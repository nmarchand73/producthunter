#!/usr/bin/env python3
"""
Debug script to analyze ProductHunt HTML structure.
"""

import requests
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def analyze_producthunt_structure():
    """Analyze ProductHunt page structure to improve selectors."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'ProductHunt Daily Recap CLI Tool v1.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    session.verify = False
    
    try:
        print("🔍 Fetching ProductHunt homepage...")
        response = session.get("https://www.producthunt.com/", timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"✅ Page loaded successfully ({len(response.content)} bytes)")
        
        # Look for common patterns
        print("\n📊 Analyzing page structure...")
        
        # Find all divs with data attributes
        data_divs = soup.find_all('div', attrs=lambda x: x and isinstance(x, dict) and any(k.startswith('data-') for k in x.keys()) if x else False)
        print(f"   - Divs with data attributes: {len(data_divs)}")
        
        # Find all links to posts
        post_links = soup.find_all('a', href=lambda x: x and '/posts/' in x if x else False)
        print(f"   - Links to posts: {len(post_links)}")
        
        # Print first few post links for analysis
        print("\n🔗 Sample post links:")
        for i, link in enumerate(post_links[:5]):
            href = link.get('href', '')
            text = link.get_text(strip=True)[:50]
            print(f"   {i+1}. {href} -> '{text}'")
        
        # Look for vote elements
        vote_elements = soup.find_all(string=lambda x: x and x.strip().isdigit() if x else False)
        print(f"\n📊 Potential vote numbers found: {len([v for v in vote_elements if int(v.strip()) > 0])}")
        
        # Look for common class patterns
        all_divs = soup.find_all('div')
        class_patterns = {}
        for div in all_divs[:100]:  # Sample first 100 divs
            classes = div.get('class', [])
            for cls in classes:
                if any(keyword in cls.lower() for keyword in ['post', 'product', 'item', 'card']):
                    class_patterns[cls] = class_patterns.get(cls, 0) + 1
        
        print(f"\n🎯 Relevant CSS classes found:")
        for cls, count in sorted(class_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   - .{cls}: {count} occurrences")
            
        # Save a sample of the HTML for manual inspection
        print(f"\n💾 Saving sample HTML for manual analysis...")
        with open('producthunt_sample.html', 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()[:10000]))  # First 10KB
        
        print("✅ Analysis complete! Check 'producthunt_sample.html' for detailed structure")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    analyze_producthunt_structure()
