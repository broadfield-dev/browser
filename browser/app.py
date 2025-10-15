import os
#os.system("playwright install")
import re
import urllib.parse
import asyncio
from typing import Dict, Optional
from itertools import cycle

import gradio as gr
from bs4 import BeautifulSoup, NavigableString
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

class CredentialRevolver:
    def __init__(self, proxy_string: str):
        self.proxies = self._parse_proxies(proxy_string)
        self.proxy_cycler = cycle(self.proxies) if self.proxies else None

    def _parse_proxies(self, proxy_string: str):
        proxies = []
        if not proxy_string: return proxies
        for line in proxy_string.strip().splitlines():
            try:
                parsed = urllib.parse.urlparse(f"//{line.strip()}")
                if not parsed.hostname or not parsed.port: continue
                server = f"http://{parsed.hostname}:{parsed.port}"
                proxy_dict = {"server": server}
                if parsed.username: proxy_dict["username"] = urllib.parse.unquote(parsed.username)
                if parsed.password: proxy_dict["password"] = urllib.parse.unquote(parsed.password)
                proxies.append(proxy_dict)
            except Exception: pass
        return proxies

    def get_next(self) -> Optional[Dict]:
        return next(self.proxy_cycler) if self.proxy_cycler else None

    def count(self) -> int:
        return len(self.proxies)

PLAYWRIGHT_STATE: Dict = {}
REVOLVER = CredentialRevolver(os.getenv("PROXY_LIST", ""))

SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={query}&hl=en",
    "DuckDuckGo": "https://duckduckgo.com/html/?q={query}",
    "Bing": "https://www.bing.com/search?q={query}",
    "Brave": "https://search.brave.com/search?q={query}",
    "Ecosia": "https://www.ecosia.org/search?q={query}",
    "Yahoo": "https://search.yahoo.com/search?p={query}",
    "Startpage": "https://www.startpage.com/sp/search?q={query}",
    "Qwant": "https://www.qwant.com/?q={query}",
    "Swisscows": "https://swisscows.com/web?query={query}",
    "You.com": "https://you.com/search?q={query}",
    "SearXNG": "https://searx.be/search?q={query}",
    "MetaGer": "https://metager.org/meta/meta.ger-en?eingabe={query}",
    "Yandex": "https://yandex.com/search/?text={query}",
    "Baidu": "https://www.baidu.com/s?wd={query}",
    "Perplexity": "https://www.perplexity.ai/search?q={query}",
}

class HTML_TO_MARKDOWN_CONVERTER:
    def __init__(self, soup: BeautifulSoup, base_url: str):
        self.soup = soup
        self.base_url = base_url

    def _cleanup_html(self):
        selectors_to_remove = ['nav', 'footer', 'header', 'aside', 'form', 'script', 'style', 'svg', 'button', 'input', 'textarea', '[role="navigation"]', '[role="search"]', '[id*="comment"]', '[class*="comment-"]', '[id*="sidebar"]', '[class*="sidebar"]', '[id*="related"]', '[class*="related"]', '[id*="share"]', '[class*="share"]', '[id*="social"]', '[class*="social"]', '[id*="cookie"]', '[class*="cookie"]', '[aria-hidden="true"]']
        for selector in selectors_to_remove:
            for element in self.soup.select(selector):
                element.decompose()

    def convert(self):
        self._cleanup_html()
        content_node = self.soup.find('main') or self.soup.find('article') or self.soup.find('body')
        if not content_node: return ""
        md = self._process_node(content_node)
        return re.sub(r'\n{3,}', '\n\n', md).strip()

    def _process_node(self, element):
        if isinstance(element, NavigableString): return re.sub(r'\s+', ' ', element.strip())
        if element.name is None or not element.name: return ''
        inner_md = " ".join(self._process_node(child) for child in element.children).strip()
        if element.name in ['p', 'div', 'section']: return f"\n\n{inner_md}\n\n"
        if element.name == 'h1': return f"\n\n# {inner_md}\n\n"
        if element.name == 'h2': return f"\n\n## {inner_md}\n\n"
        if element.name == 'h3': return f"\n\n### {inner_md}\n\n"
        if element.name in ['h4', 'h5', 'h6']: return f"\n\n#### {inner_md}\n\n"
        if element.name == 'li': return f"* {inner_md}\n"
        if element.name in ['ul', 'ol']: return f"\n{inner_md}\n"
        if element.name == 'blockquote': return f"> {inner_md.replace(chr(10), chr(10) + '> ')}\n\n"
        if element.name == 'hr': return "\n\n---\n\n"
        if element.name == 'table':
            header = " | ".join(f"**{th.get_text(strip=True)}**" for th in element.select('thead th, tr th'))
            separator = " | ".join(['---'] * len(header.split('|')))
            rows = [" | ".join(td.get_text(strip=True) for td in tr.find_all('td')) for tr in element.select('tbody tr')]
            return f"\n\n{header}\n{separator}\n" + "\n".join(rows) + "\n\n"
        if element.name == 'pre': return f"\n```\n{element.get_text(strip=True)}\n```\n\n"
        if element.name == 'code': return f"`{inner_md}`"
        if element.name in ['strong', 'b']: return f"**{inner_md}**"
        if element.name in ['em', 'i']: return f"*{inner_md}*"
        if element.name == 'a':
            href = element.get('href', '')
            full_href = urllib.parse.urljoin(self.base_url, href)
            return f"[{inner_md}]({full_href})"
        if element.name == 'img':
            src = element.get('src', '')
            alt = element.get('alt', 'Image').strip()
            full_src = urllib.parse.urljoin(self.base_url, src)
            return f"\n\n![{alt}]({full_src})\n\n"
        return inner_md

async def perform_web_browse(action: str, query: str, browser_name: str, search_engine_name: str):
    browser_key = browser_name.lower()
    if "playwright" not in PLAYWRIGHT_STATE:
        PLAYWRIGHT_STATE["playwright"] = await async_playwright().start()

    if browser_key not in PLAYWRIGHT_STATE:
        try:
            p = PLAYWRIGHT_STATE["playwright"]
            if browser_key == 'firefox': browser_instance = await p.firefox.launch(headless=True)
            elif browser_key == 'chromium': browser_instance = await p.chromium.launch(headless=True)
            elif browser_key == 'webkit': browser_instance = await p.webkit.launch(headless=True)
            else: raise ValueError(f"Invalid browser name: {browser_name}")
            PLAYWRIGHT_STATE[browser_key] = browser_instance
        except Exception as e:
            return {"status": "error", "query": query, "error_message": f"Failed to launch '{browser_key}'. Error: {str(e).splitlines()[0]}"}
    
    browser_instance = PLAYWRIGHT_STATE[browser_key]

    if action == "Scrape URL":
        if not query.startswith(('http://', 'https://')):
            url = f"http://{query}"
        else:
            url = query
    else: # action == "Search"
        url_template = SEARCH_ENGINES.get(search_engine_name)
        if not url_template:
            return {"status": "error", "query": query, "error_message": f"Invalid search engine: '{search_engine_name}'."}
        url = url_template.format(query=urllib.parse.quote_plus(query))

    proxy_config = REVOLVER.get_next()
    proxy_server_used = proxy_config["server"] if proxy_config else "Direct Connection"
    
    context_args = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36', 'java_script_enabled': True, 'ignore_https_errors': True, 'bypass_csp': True, 'accept_downloads': False}
    if proxy_config: context_args['proxy'] = proxy_config

    context = await browser_instance.new_context(**context_args)
    page = await context.new_page()

    try:
        response = await page.goto(url, wait_until='domcontentloaded', timeout=25000)
        
        html_content = await page.content()

        if any(phrase in html_content for phrase in ["unusual traffic", "CAPTCHA", "are you human", "not a robot"]):
            raise Exception(f"Anti-bot measure detected on {page.url}. Try another search engine or proxy.")

        final_url, title = page.url, await page.title() or "No Title"
        soup = BeautifulSoup(html_content, 'lxml')
        converter = HTML_TO_MARKDOWN_CONVERTER(soup, base_url=final_url)
        markdown_text = converter.convert()
        status_code = response.status if response else 0

        return {"status": "success", "query": query, "action": action, "final_url": final_url, "page_title": title, "http_status": status_code, "proxy_used": proxy_server_used, "markdown_content": markdown_text}
    except Exception as e:
        error_message = str(e).splitlines()[0]
        if "Timeout" in error_message:
            return {"status": "error", "query": query, "proxy_used": proxy_server_used, "error_message": f"Navigation Timeout: The page for '{query}' took too long to load."}
        return {"status": "error", "query": query, "proxy_used": proxy_server_used, "error_message": error_message}
    finally:
        if 'page' in locals() and not page.is_closed(): await page.close()
        if 'context' in locals(): await context.close()

with gr.Blocks(title="Web Browse API", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Web Browse API")
    gr.Markdown(f"This interface exposes a stateless API endpoint (`/api/web_browse`) to fetch and parse web content. {REVOLVER.count()} proxies loaded.")
    
    action_input = gr.Radio(label="Action", choices=["Search", "Scrape URL"], value="Search")
    query_input = gr.Textbox(label="Query or URL", placeholder="e.g., 'best cat food' or 'www.wikipedia.org'")
    
    with gr.Row():
        browser_input = gr.Dropdown(label="Browser", choices=["firefox", "chromium", "webkit"], value="firefox", scale=1)
        search_engine_input = gr.Dropdown(label="Search Engine (if action is Search)", choices=sorted(list(SEARCH_ENGINES.keys())), value="DuckDuckGo", scale=2)
    
    submit_button = gr.Button("Browse", variant="primary")
    output_json = gr.JSON(label="API Result")
    
    submit_button.click(fn=perform_web_browse, inputs=[action_input, query_input, browser_input, search_engine_input], outputs=output_json, api_name="web_browse")

if __name__ == "__main__":
    demo.launch(mcp_server=True)
