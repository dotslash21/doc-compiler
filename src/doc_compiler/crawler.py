import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WebCrawler:
    def __init__(self, entry_url: str, max_depth: int):
        """Initialize the crawler with entry URL and maximum depth."""
        self.entry_url = entry_url
        self.max_depth = max_depth
        self.visited_urls = set()
        parsed_entry = urlparse(entry_url)
        self.base_domain = parsed_entry.netloc
        # Store base path from entry URL to restrict crawling
        self.base_path = parsed_entry.path
        # If path doesn't end with '/', append it to ensure we're checking the directory
        if not self.base_path.endswith("/"):
            self.base_path += "/"
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

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments, trailing slashes, and lowercasing."""
        # Remove fragment identifier
        url_without_fragment, _ = urldefrag(url)

        # Normalize trailing slashes and case
        parsed = urlparse(url_without_fragment)
        normalized_path = parsed.path.lower().rstrip("/")

        # Rebuild URL without fragment and with normalized path
        normalized = parsed._replace(path=normalized_path, fragment="").geturl()
        return normalized

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled based on domain, scheme, and path."""
        try:
            parsed = urlparse(url)

            # Check URL scheme
            if parsed.scheme not in ("http", "https"):
                return False

            # Check if URL is under the same base path
            url_path = parsed.path
            if not url_path.startswith(self.base_path):
                self.logger.debug(f"URL {url} is outside base path {self.base_path}")
                return False

            return True
        except Exception as e:
            self.logger.warning(f"Invalid URL: {url}, error: {e}")
            return False

    def get_page_content(
        self, url: str
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Fetch page content using requests first, fall back to Selenium if needed.
        Returns: (title, content, list of links)
        """
        try:
            # First try with trafilatura for direct content extraction
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                extracted_text = trafilatura.extract(
                    downloaded, include_links=True, output_format="markdown"
                )
                if extracted_text:
                    # Extract title separately with requests
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    title = soup.title.string.strip() if soup.title else "Untitled Page"
                    return title, extracted_text, self._extract_links(soup, url)

            # Fall back to requests + BeautifulSoup approach
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return self._extract_content(soup, url)
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch {url} with requests: {e}")
            if self.driver:
                try:
                    self.driver.get(url)
                    # Wait for page to load with timeout
                    wait = WebDriverWait(self.driver, 15)
                    # Wait for body to be present
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                    # Try with trafilatura first
                    extracted_text = trafilatura.extract(
                        self.driver.page_source,
                        include_links=True,
                        output_format="markdown",
                    )
                    if extracted_text:
                        title = self.driver.title or "Untitled Page"
                        soup = BeautifulSoup(self.driver.page_source, "html.parser")
                        return title, extracted_text, self._extract_links(soup, url)

                    # Fall back to regular parsing
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    return self._extract_content(soup, url)
                except (WebDriverException, TimeoutException) as e:
                    self.logger.error(f"Selenium also failed for {url}: {e}")
            return None, None, []

    def _extract_links(self, soup: BeautifulSoup, url: str) -> List[str]:
        """Extract links from BeautifulSoup object."""
        links = []
        current_url_normalized = self.normalize_url(url)

        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Filter out javascript, mailto, tel links
            if href.startswith(("javascript:", "mailto:", "tel:")):
                continue

            absolute_url = urljoin(url, href)
            normalized_url = self.normalize_url(absolute_url)

            # Skip self-references (links to the same page)
            if normalized_url == current_url_normalized:
                continue

            if self.is_valid_url(normalized_url):
                links.append(normalized_url)

        return links

    def _extract_content(
        self, soup: BeautifulSoup, url: str
    ) -> Tuple[str, str, List[str]]:
        """Extract title, main content, and links from BeautifulSoup object."""
        # Remove unwanted elements
        for element in soup.select("nav, footer, header, script, style"):
            element.decompose()

        # Extract title - improved fallback
        title = "Untitled Page"
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.select_one("h1"):
            title = soup.select_one("h1").get_text().strip()

        # Try trafilatura first for main content extraction
        html_content = str(soup)
        extracted_text = trafilatura.extract(
            html_content, include_links=False, output_format="markdown"
        )

        # If trafilatura was successful, use its output
        if extracted_text:
            content = extracted_text
        else:
            # Fall back to original extraction method
            content_elements = []
            for tag in soup.find_all(
                [
                    "p",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                    "li",
                    "div.content",
                    "article",
                ]
            ):
                text = tag.get_text().strip()
                if text:  # Only include non-empty elements
                    content_elements.append(text)

            content = " ".join(content_elements)

            # If content is still empty, try to get the whole body text
            if not content and soup.body:
                content = soup.body.get_text().strip()

        # Extract links
        links = self._extract_links(soup, url)

        return title, content, links

    def crawl(self) -> List[Dict[str, str]]:
        """
        Crawl the website starting from entry_url up to max_depth.
        Returns a list of dictionaries containing page title, URL, and content.
        """
        pages = []
        to_visit = [(self.entry_url, 0)]  # (url, depth)
        normalized_visited = set()  # Set of normalized URLs

        while to_visit:
            url, depth = to_visit.pop(0)
            normalized_url = self.normalize_url(url)

            if depth > self.max_depth or normalized_url in normalized_visited:
                continue

            normalized_visited.add(normalized_url)
            self.visited_urls.add(url)
            self.logger.info(f"Crawling {url} at depth {depth}")

            title, content, links = self.get_page_content(url)
            if title and content:
                pages.append({"url": url, "title": title, "content": content})

                # Add new links to visit
                if depth < self.max_depth:
                    for link in links:
                        link_normalized = self.normalize_url(link)
                        if link_normalized not in normalized_visited:
                            to_visit.append((link, depth + 1))

        if self.driver:
            self.driver.quit()

        return pages
