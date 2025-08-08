"""
ProductHunt Category Scraper

This module scrapes all categories and subcategories from ProductHunt
and creates a comprehensive mapping between URL-style names and display names.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Tuple, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductHuntCategoryScraper:
    """Scraper for ProductHunt categories and subcategories."""
    
    def __init__(self):
        self.base_url = "https://www.producthunt.com"
        self.categories_url = f"{self.base_url}/categories"
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Store for categories
        self.categories = {}
        self.category_hierarchy = {}
        
    def extract_category_from_url(self, url: str) -> str:
        """Extract category name from URL."""
        parsed = urlparse(url)
        if '/categories/' in parsed.path:
            category = parsed.path.split('/categories/')[-1]
            # Remove any query parameters or fragments
            return category.split('?')[0].split('#')[0]
        return ""
    
    def normalize_category_name(self, name: str) -> str:
        """Convert display name to URL-style name."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        normalized = re.sub(r'[^\w\s-]', '', name.lower())
        normalized = re.sub(r'\s+', '-', normalized.strip())
        normalized = re.sub(r'-+', '-', normalized)  # Remove multiple hyphens
        return normalized.strip('-')
    
    def get_page_content(self, url: str) -> BeautifulSoup:
        """Get page content with error handling."""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Add small delay to be respectful
            time.sleep(1)
            
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def scrape_main_categories(self) -> Dict[str, Dict]:
        """Scrape main categories from the categories page."""
        soup = self.get_page_content(self.categories_url)
        if not soup:
            return {}
        
        categories = {}
        
        # Look for category links - ProductHunt uses various structures
        category_links = soup.find_all('a', href=lambda x: x and '/categories/' in x)
        
        # Also look for section headers that might contain category names
        sections = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        # Extract from links
        for link in category_links:
            href = link.get('href', '')
            if '/categories/' in href and href != '/categories':
                category_url_name = self.extract_category_from_url(href)
                if category_url_name:
                    # Get display name from link text or nearby text
                    display_name = link.get_text(strip=True)
                    if display_name:
                        categories[category_url_name] = {
                            'display_name': display_name,
                            'url_name': category_url_name,
                            'url': urljoin(self.base_url, href),
                            'type': 'main_category',
                            'subcategories': []
                        }
        
        # Also try to find categories from structured content
        # Look for patterns like category grids or lists
        content_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(
            term in str(x).lower() for term in ['category', 'grid', 'list', 'section']
        ))
        
        for section in content_sections:
            links = section.find_all('a', href=lambda x: x and '/categories/' in x)
            for link in links:
                href = link.get('href', '')
                category_url_name = self.extract_category_from_url(href)
                if category_url_name and category_url_name not in categories:
                    display_name = link.get_text(strip=True)
                    if display_name:
                        categories[category_url_name] = {
                            'display_name': display_name,
                            'url_name': category_url_name,
                            'url': urljoin(self.base_url, href),
                            'type': 'main_category',
                            'subcategories': []
                        }
        
        logger.info(f"Found {len(categories)} main categories")
        return categories
    
    def scrape_category_details(self, category_info: Dict) -> Dict:
        """Scrape detailed information from a category page."""
        soup = self.get_page_content(category_info['url'])
        if not soup:
            return category_info
        
        # Look for subcategories or related categories
        subcategory_links = soup.find_all('a', href=lambda x: x and '/categories/' in x)
        subcategories = []
        
        for link in subcategory_links:
            href = link.get('href', '')
            subcat_url_name = self.extract_category_from_url(href)
            if subcat_url_name and subcat_url_name != category_info['url_name']:
                display_name = link.get_text(strip=True)
                if display_name:
                    subcategories.append({
                        'display_name': display_name,
                        'url_name': subcat_url_name,
                        'url': urljoin(self.base_url, href)
                    })
        
        # Get category description if available
        description_selectors = [
            'meta[name="description"]',
            '.category-description',
            '.description',
            'p'
        ]
        
        description = ""
        for selector in description_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                if selector.startswith('meta'):
                    description = desc_element.get('content', '')
                else:
                    description = desc_element.get_text(strip=True)
                if description:
                    break
        
        category_info['description'] = description[:500] if description else ""
        category_info['subcategories'] = subcategories
        
        logger.info(f"Scraped details for {category_info['display_name']}: {len(subcategories)} subcategories")
        return category_info
    
    def discover_additional_categories(self) -> Set[str]:
        """Discover additional categories from product pages and other sources."""
        additional_urls = set()
        
        # Try common category patterns
        common_categories = [
            'engineering-development', 'design-creative', 'work-productivity',
            'marketing-sales', 'finance', 'health-fitness', 'travel',
            'social-community', 'ai-software', 'chrome-extensions',
            'productivity-tools', 'developer-tools', 'design-tools',
            'business-tools', 'mobile-apps', 'web-apps'
        ]
        
        for cat in common_categories:
            url = f"{self.base_url}/categories/{cat}"
            additional_urls.add(url)
        
        return additional_urls
    
    def create_comprehensive_mapping(self) -> Dict:
        """Create comprehensive category mapping."""
        # Start with main categories
        categories = self.scrape_main_categories()
        
        # Add some manual mappings for common categories we know exist
        known_mappings = {
            'engineering-development': 'Engineering & Development',
            'design-creative': 'Design & Creative',
            'work-productivity': 'Work & Productivity',
            'marketing-sales': 'Marketing & Sales',
            'social-community': 'Social & Community',
            'health-fitness': 'Health & Fitness',
            'ai-software': 'AI',
            'chrome-extensions': 'Chrome Extensions',
            'developer-tools': 'Developer Tools',
            'productivity-tools': 'Productivity Tools',
            'design-tools': 'Design Tools',
            'business-tools': 'Business Tools',
            'mobile-apps': 'Mobile Apps',
            'web-apps': 'Web Apps',
            'finance': 'Finance',
            'travel': 'Travel',
            'ecommerce': 'Ecommerce',
            'platforms': 'Platforms',
            'physical-products': 'Physical Products',
            'web3': 'Web3',
            'family': 'Family',
            'lifestyle': 'Lifestyle',
            'product-add-ons': 'Product add-ons'
        }
        
        # Add known mappings to categories
        for url_name, display_name in known_mappings.items():
            if url_name not in categories:
                categories[url_name] = {
                    'display_name': display_name,
                    'url_name': url_name,
                    'url': f"{self.base_url}/categories/{url_name}",
                    'type': 'main_category',
                    'subcategories': [],
                    'description': f"Category for {display_name} products"
                }
        
        # Try to scrape details for each category
        detailed_categories = {}
        for url_name, category_info in categories.items():
            try:
                detailed_info = self.scrape_category_details(category_info)
                detailed_categories[url_name] = detailed_info
            except Exception as e:
                logger.error(f"Error scraping details for {url_name}: {e}")
                detailed_categories[url_name] = category_info
        
        return detailed_categories
    
    def create_reverse_mapping(self, categories: Dict) -> Dict:
        """Create mapping from display names to URL names."""
        reverse_mapping = {}
        
        for url_name, category_info in categories.items():
            display_name = category_info['display_name']
            reverse_mapping[display_name.lower()] = url_name
            
            # Also add variations
            normalized = self.normalize_category_name(display_name)
            if normalized != url_name:
                reverse_mapping[normalized] = url_name
            
            # Add subcategories to reverse mapping
            for subcat in category_info.get('subcategories', []):
                sub_display = subcat['display_name']
                sub_url = subcat['url_name']
                reverse_mapping[sub_display.lower()] = sub_url
                reverse_mapping[self.normalize_category_name(sub_display)] = sub_url
        
        return reverse_mapping
    
    def save_categories_data(self, categories: Dict, output_file: str):
        """Save categories data to JSON file."""
        # Create comprehensive data structure
        categories_data = {
            'metadata': {
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_categories': len(categories),
                'source_url': self.categories_url,
                'scraper_version': '1.0'
            },
            'categories': categories,
            'url_to_display_mapping': {
                url_name: info['display_name'] 
                for url_name, info in categories.items()
            },
            'display_to_url_mapping': self.create_reverse_mapping(categories),
            'category_list': list(categories.keys()),
            'display_names': [info['display_name'] for info in categories.values()]
        }
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(categories_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(categories)} categories to {output_file}")
        return categories_data

def main():
    """Main function to run the category scraper."""
    scraper = ProductHuntCategoryScraper()
    
    # Create output file path
    output_file = "data/producthunt_categories.json"
    
    try:
        # Scrape categories
        logger.info("Starting ProductHunt category scraping...")
        categories = scraper.create_comprehensive_mapping()
        
        # Save data
        categories_data = scraper.save_categories_data(categories, output_file)
        
        # Print summary
        print(f"\n=== ProductHunt Category Scraping Complete ===")
        print(f"Total categories found: {len(categories)}")
        print(f"Output file: {output_file}")
        print(f"\nSample categories:")
        for i, (url_name, info) in enumerate(list(categories.items())[:10]):
            print(f"  {url_name} -> {info['display_name']}")
            if i >= 9:
                print(f"  ... and {len(categories) - 10} more")
                break
        
        return categories_data
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise

if __name__ == "__main__":
    main()
