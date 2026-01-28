import requests
from bs4 import BeautifulSoup
import html2text
from typing import Optional

class WebScraper:
    """Service to scrape and extract content from websites"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a URL

        Args:
            url: The website URL to scrape

        Returns:
            Extracted text content or None if failed
        """
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Fetch the page
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Get text using html2text for better formatting
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.ignore_emphasis = False
            text = h.handle(str(soup))

            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)

            return clean_text

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to process content: {str(e)}")

    def get_page_metadata(self, url: str) -> dict:
        """Extract metadata from the page (title, description, etc.)"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            metadata = {
                'title': soup.title.string if soup.title else '',
                'description': '',
                'url': url
            }

            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metadata['description'] = meta_desc.get('content')

            return metadata

        except Exception:
            return {'title': '', 'description': '', 'url': url}
