from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import json
import os
from typing import Dict, List, Optional, Union
from src.exceptions import CarouselNotFoundError, ListNameNotFoundError

class GoogleCarouselExtractor:
    """Extracts carousel data from Google search results pages."""
    
    CAROUSEL_SELECTORS = [
        'g-scrolling-carousel',
        'div[jsname="yRioIc"]'
    ]
    
    LIST_NAME_SELECTORS = [
        'span.kxbc',
        'span.Wkr6U.z4P7Tc'
    ]
    
    NAME_SELECTORS = [
        '.kltat',
        '.jEmWnc'
    ]
    
    EXTENSION_SELECTORS = [
        '.ellip.klmeta',
        '.b7VT4c'
    ]

    def __init__(self, html_path: str):
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the Chrome WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Convert file path to file URL
        abs_path = os.path.abspath(html_path)
        file_url = f'file://{abs_path}'
        
        # Load the page
        self.driver.get(file_url)
        
        # Wait for content to load
        self._wait_for_carousel()
        
        # Get the rendered HTML
        rendered_html = self.driver.page_source
        
        # Parse with BeautifulSoup
        self.soup = BeautifulSoup(rendered_html, 'html.parser')

    def __del__(self):
        """Cleanup the WebDriver when done."""
        if hasattr(self, 'driver'):
            self.driver.quit()
        
    def _wait_for_carousel(self):
        """Wait for the Javascript code to finish running."""
        WebDriverWait(self.driver, 20).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
    
    def _find_carousel(self) -> BeautifulSoup:
        """Find the carousel element in the page."""
        for selector in self.CAROUSEL_SELECTORS:
            carousel = self.soup.select(selector)
            if carousel:
                return carousel[0]
        raise CarouselNotFoundError("No carousel found in the HTML content")

    def _find_list_name(self) -> str:
        """Extract the list name from the page."""
        for selector in self.LIST_NAME_SELECTORS:
            elements = self.soup.select(selector)
            if len(elements) >= 2:
                return elements[1].text.lower()
        raise ListNameNotFoundError("Could not find list name in the HTML content")

    def _parse_item(self, item: BeautifulSoup) -> Dict[str, Union[str, List[str], None]]:
        """Parse a single carousel item."""
        img = item.find('img')
        image = img['src'] if img and img.has_attr('src') else None
        
        link = 'https://www.google.com' + item['href']
        
        # find name
        i = 0
        for selector in self.NAME_SELECTORS:
            name = item.select_one(selector)
            if name:
                break
            i += 1
        name = name.text.strip()
        
        # check if extension do not exists
        if not item.select_one(self.EXTENSION_SELECTORS[i]):
            return {
                'name': name,
                'link': link,
                'image': image
            }

        extension = item.select_one(self.EXTENSION_SELECTORS[i]).text.strip()
        
        return {
            'name': name,
            'extensions': [extension],
            'link': link,
            'image': image
        }

    def extract(self) -> Dict[str, List[Dict]]:
        """Extract carousel data from the HTML content."""
        carousel = self._find_carousel()
        list_name = self._find_list_name()
        
        items = []
        for item in carousel.find_all('a'):
            items.append(self._parse_item(item))

        return {list_name: items}


def extract_from_file(file_path: str, pretty: bool = True) -> str:
    """Extract carousel data from an HTML file."""
    extractor = GoogleCarouselExtractor(file_path)
    data = extractor.extract()
    
    return data

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        try:
            data_dict = extract_from_file(sys.argv[1])
            
            if len(sys.argv) == 2:
                print(json.dumps(data_dict, indent=4))
                sys.exit(1)
            
            with open(sys.argv[2], 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
            
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        print('Please provide the HTML file path', file=sys.stderr)
        sys.exit(1)