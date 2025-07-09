#!/usr/bin/env python3
"""
Debug script to examine the actual HTML content from LawnFawn search results.
This will help us understand why our selectors aren't working.
"""

import asyncio
import os
from app.services.firecrawl_client import get_firecrawl_client
from bs4 import BeautifulSoup

async def debug_lawnfawn_html():
    """Debug LawnFawn search HTML content."""
    
    # Initialize Firecrawl client
    client = get_firecrawl_client()
    
    # Test URL from the screenshots
    search_url = "https://www.lawnfawn.com/search?options%5Bprefix%5D=last&q=1142&filter.p.product_type="
    
    print(f"🔍 Scraping: {search_url}")
    
    # Scrape with longer wait time for JavaScript
    response = await client.scrape_page(
        search_url,
        waitFor=5000,  # Wait 5 seconds for JavaScript
        includeTags=["a", "div", "span", "img", "h1", "h2", "h3", "p"],
        excludeTags=["script", "style"]
    )
    
    print(f"✅ Success: {response.success}")
    print(f"📄 Content length: {len(response.content)}")
    print(f"💰 Credits used: {response.credits_used}")
    
    if response.success:
        # Save raw content for inspection
        with open("debug_lawnfawn_raw.html", "w", encoding="utf-8") as f:
            f.write(response.content)
        print("💾 Saved raw HTML to: debug_lawnfawn_raw.html")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("\n🔍 ANALYZING HTML STRUCTURE:")
        
        # Look for all links
        all_links = soup.find_all('a', href=True)
        print(f"📎 Total links found: {len(all_links)}")
        
        # Look for product-related links
        product_links = []
        for link in all_links:
            href = link.get('href', '')
            if '/products/' in href:
                product_links.append({
                    'href': href,
                    'classes': link.get('class', []),
                    'text': link.get_text(strip=True)[:50],
                    'aria_label': link.get('aria-label', ''),
                    'data_attrs': {k: v for k, v in link.attrs.items() if k.startswith('data-')}
                })
        
        print(f"🎯 Product links found: {len(product_links)}")
        
        for i, link in enumerate(product_links):
            print(f"\n  Link {i+1}:")
            print(f"    href: {link['href']}")
            print(f"    classes: {link['classes']}")
            print(f"    text: {link['text']}")
            print(f"    aria-label: {link['aria_label']}")
            print(f"    data-attrs: {link['data_attrs']}")
        
        # Test our selectors
        print("\n🧪 TESTING SELECTORS:")
        
        selectors_to_test = [
            'a.js-prod-link',
            'a.media.block.relative',
            'a[href*="/products/"]',
            '.product-item a',
            '.product-link',
            '.grid-product__link',
            'a[class*="js-prod"]',
            'a[class*="prod-link"]',
            'a[class*="media"]'
        ]
        
        for selector in selectors_to_test:
            matches = soup.select(selector)
            print(f"  {selector}: {len(matches)} matches")
            if matches:
                for match in matches[:2]:  # Show first 2 matches
                    print(f"    → {match.get('href', 'NO_HREF')} | classes: {match.get('class', [])}")
        
        # Look for specific text content
        print("\n📝 SEARCHING FOR SPECIFIC CONTENT:")
        content_lower = response.content.lower()
        
        search_terms = [
            'stitched rectangle frames',
            'js-prod-link',
            'media block relative',
            '/products/stitched-rectangle-frames',
            'lf1142'
        ]
        
        for term in search_terms:
            found = term in content_lower
            print(f"  '{term}': {'✅ FOUND' if found else '❌ NOT FOUND'}")
        
        # Look for any divs or elements that might contain product info
        print("\n🏗️ LOOKING FOR PRODUCT CONTAINERS:")
        
        product_containers = soup.find_all(['div', 'article', 'section'], 
                                         class_=lambda x: x and any(keyword in ' '.join(x).lower() 
                                                                   for keyword in ['product', 'item', 'card', 'result']))
        
        print(f"📦 Product containers found: {len(product_containers)}")
        
        for i, container in enumerate(product_containers[:3]):  # Show first 3
            print(f"\n  Container {i+1}:")
            print(f"    tag: {container.name}")
            print(f"    classes: {container.get('class', [])}")
            
            # Look for links within this container
            container_links = container.find_all('a', href=True)
            for link in container_links:
                href = link.get('href', '')
                if '/products/' in href or 'stitched' in href.lower():
                    print(f"    → LINK: {href} | classes: {link.get('class', [])}")
    
    else:
        print(f"❌ Failed to scrape: {response.error_message}")

if __name__ == "__main__":
    # Set API key
    if not os.getenv('FIRECRAWL_API_KEY'):
        print("❌ Please set FIRECRAWL_API_KEY environment variable")
        exit(1)
    
    asyncio.run(debug_lawnfawn_html())
