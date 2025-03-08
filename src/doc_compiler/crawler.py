import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options


class WebCrawler:
    def __init__(self, entry_url: str, max_depth: int):
        """Initialize the crawler with entry URL and maximum depth."""
        self.entry_url = entry_url
        self.max_depth = max_depth
        self.visited_urls = set()
        self.base_domain = urlparse(entry_url).netloc
        self.setup_selenium()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def setup_selenium(self):
        """Initialize Selenium WebDriver with Chrome in headless mode."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize Selenium: {e}")
            self.driver = None

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled based on domain."""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.base_domain
        except Exception:
            return False

    def get_page_content(
        self, url: str
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Fetch page content using requests first, fall back to Selenium if needed.
        Returns: (title, content, list of links)
        """
        try:
            # First try with requests
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return self._extract_content(soup, url)
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch {url} with requests: {e}")
            if self.driver:
                try:
                    self.driver.get(url)
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    return self._extract_content(soup, url)
                except WebDriverException as e:
                    self.logger.error(f"Selenium also failed for {url}: {e}")
            return None, None, []

    def _extract_content(
        self, soup: BeautifulSoup, url: str
    ) -> Tuple[str, str, List[str]]:
        """Extract title, main content, and links from BeautifulSoup object."""
        # Remove unwanted elements
        for element in soup.select("nav, footer, header, script, style"):
            element.decompose()

        # Extract title
        title = soup.title.string if soup.title else url

        # Extract main content
        content = " ".join(
            p.get_text().strip()
            for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
        )

        # Extract links
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(url, href)
            if self.is_valid_url(absolute_url):
                links.append(absolute_url)

        return title, content, links

    def crawl(self) -> List[Dict[str, str]]:
        """
        Crawl the website starting from entry_url up to max_depth.
        Returns a list of dictionaries containing page title, URL, and content.
        """
        pages = []
        to_visit = [(self.entry_url, 0)]  # (url, depth)

        while to_visit:
            url, depth = to_visit.pop(0)

            if depth > self.max_depth or url in self.visited_urls:
                continue

            self.visited_urls.add(url)
            self.logger.info(f"Crawling {url} at depth {depth}")

            title, content, links = self.get_page_content(url)
            if title and content:
                pages.append({"url": url, "title": title, "content": content})

                # Add new links to visit
                if depth < self.max_depth:
                    for link in links:
                        if link not in self.visited_urls:
                            to_visit.append((link, depth + 1))

        if self.driver:
            self.driver.quit()

        return pages
