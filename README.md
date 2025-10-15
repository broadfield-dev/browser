# Browser API: Search and Scrape the Web

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Browser API is a powerful and easy-to-use Python package for web automation. It allows you to programmatically perform web searches using a variety of search engines and scrape the content of any URL, returning clean, readable Markdown.

Built with Gradio and Playwright, it can be run as a standalone web UI, a REST API, or be imported directly into your Python projects.

## Features

-   **Dual Action:** Perform web searches or scrape specific URLs.
-   **Multi-Browser Support:** Use Chromium, Firefox, or WebKit for your tasks.
-   **Extensive Search Engine List:** Supports over a dozen search engines, including Google, DuckDuckGo, and Perplexity.
-   **Intelligent Scraping:** Cleans HTML and converts the main content to Markdown.
-   **Flexible Usage:** Can be used as a Python library, a command-line tool, or a web API.

## Installation

There are two steps to install the package and its dependencies.

**Step 1: Install the Python Package**

Install the package directly from GitHub using `pip`. This will also install all necessary Python dependencies like `playwright`, `gradio`, and `beautifulsoup4`.

```bash
pip install git+https://github.com/broadfield-dev/browser.git
```

**Step 2: Install Browser Binaries**

After the package is installed, you must download the browser binaries that Playwright uses for automation.

```bash
playwright install
```

This command only needs to be run once after the initial installation.

## How to Use

Browser API can be used in two primary ways: as a Python library in your own code or as a standalone server with a web UI.

### 1. Using as a Python Library

Import the `perform_web_browse` function to integrate web search and scraping directly into your application. It's an `async` function, so you'll need to use it in an asynchronous context.

**Example: Search and Scrape**

```python
import asyncio
from browser.app import perform_web_browse

async def main():
    # --- Example 1: Perform a web search ---
    print("Performing a search for 'latest AI research'...")
    search_result = await perform_web_browse(
        action="Search",
        query="latest AI research",
        browser_name="chromium",
        search_engine_name="Google"
    )

    if search_result.get("status") == "success":
        print("Search successful!")
        # print(search_result["markdown_content"]) # Uncomment to see the full markdown
    else:
        print(f"Search failed: {search_result.get('error_message')}")

    print("-" * 50)

    # --- Example 2: Scrape a specific URL ---
    print("Scraping Wikipedia page for 'Web scraping'...")
    scrape_result = await perform_web_browse(
        action="Scrape URL",
        query="https://en.wikipedia.org/wiki/Web_scraping",
        browser_name="firefox",
        search_engine_name=None # Not needed for scraping
    )

    if scrape_result.get("status") == "success":
        print("Scraping successful!")
        print(f"Page Title: {scrape_result['page_title']}")
        # print(scrape_result["markdown_content"]) # Uncomment to see the full markdown
    else:
        print(f"Scraping failed: {scrape_result.get('error_message')}")


if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Running the Gradio Web UI and API Server

The package includes a Gradio-based web interface for easy interaction and exposes a REST API endpoint. To launch it, simply run the following command in your terminal:

```bash
browser-api
```

This will start a local web server. Open the URL provided in the terminal (usually `http://127.0.0.1:7860`) in your browser to use the web UI.

#### Using the REST API

Once the server is running, you can send `POST` requests to the `/api/web_browse` endpoint.

**Example: `curl` Request to Search**

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{
  "action": "Search",
  "query": "latest AI research",
  "browser_name": "chromium",
  "search_engine_name": "Google"
}' \
http://127.0.0.1:7860/api/web_browse
```

**Example: `curl` Request to Scrape a URL**

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{
  "action": "Scrape URL",
  "query": "https://en.wikipedia.org/wiki/Web_scraping",
  "browser_name": "firefox"
}' \
http://127.0.0.1:7860/api/web_browse
```

## Platform Compatibility

-   **Windows, macOS, and Linux:** The Python code is fully cross-platform.
-   **Linux System Dependencies:** The `packages.txt` file in this repository lists system libraries required for Playwright's browsers to run on Debian-based Linux systems. If you are deploying on such a system, you will need to ensure these packages are installed. On Windows and macOS, these dependencies are not needed.

## Supported Search Engines

You can use any of the following search engines with the `"Search"` action:

-   Google
-   DuckDuckGo
-   Bing
-   Brave
-   Ecosia
-   Yahoo
-   Startpage
-   Qwant
-   Swisscows
-   You.com
-   SearXNG
-   MetaGer
-   Yandex
-   Baidu
-   Perplexity
