from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="browser",
    version="0.1.0",
    author="broadfield-dev",
    description="A web browser API for searching and scraping web content.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/broadfield-dev/browser",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "browser-api=browser.app:demo.launch",
        ],
    },
)
