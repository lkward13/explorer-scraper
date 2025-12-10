#!/usr/bin/env python3
"""
Check for price insights by loading a flights search URL directly.
Works in Docker with Xvfb.
"""
import asyncio
import re
from playwright.async_api import async_playwright

async def main():
    print("="*80)
    print("CHECKING PRICE INSIGHTS IN FLIGHT SEARCH RESULTS")
    print("="*80)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Use a pre-built URL for OKC → BCN (from your screenshot)
        url = "https://www.google.com/travel/flights/search?tfs=CBwQAhojEgoyMDI1LTEyLTE3agcIARIDT0tDcgcIARIDQkNOGgwIAxIIL20vMDFmNjJyBwgBEgNPS0MyARFIAZgBAQ&hl=en&gl=us"
        
        print(f"Loading: OKC → BCN, Dec 17, 2025")
        print(f"URL: {url[:80]}...")
        print()
        
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        print("✓ Page loaded")
        await asyncio.sleep(5)  # Wait for any dynamic content
        
        # Get all page text
        body_text = await page.text_content('body')
        
        print()
        print("="*80)
        print("SEARCHING FOR PRICE INSIGHTS")
        print("="*80)
        print()
        
        # Search for all price insight patterns
        patterns = {
            'Price status (typical)': r'Prices are currently typical',
            'Price status (low)': r'Prices are currently low',
            'Price status (high)': r'Prices are currently high',
            'Cheaper (dollar)': r'\$(\d+) cheaper than usual',
            'More expensive (dollar)': r'\$(\d+) more expensive than usual',
            'Cheaper (percent)': r'(\d+)% cheaper than usual',
            'More expensive (percent)': r'(\d+)% more expensive than usual',
            'Lower prices': r'lower than usual',
            'Higher prices': r'higher than usual',
        }
        
        found_insights = []
        
        for name, pattern in patterns.items():
            matches = re.findall(pattern, body_text, re.IGNORECASE)
            if matches:
                print(f"✓ {name}:")
                if isinstance(matches[0], tuple):
                    # Extract from regex groups
                    for match in matches[:3]:
                        print(f"    {match}")
                else:
                    # Direct string match
                    for match in matches[:3]:
                        print(f"    {match}")
                found_insights.append(name)
            else:
                print(f"✗ {name}: Not found")
        
        # Save HTML for inspection
        html = await page.content()
        with open('price_insights_page.html', 'w') as f:
            f.write(html)
        
        print()
        print(f"✓ Saved HTML to: price_insights_page.html")
        
        # Also save just the text content for easier grepping
        with open('price_insights_text.txt', 'w') as f:
            f.write(body_text)
        print(f"✓ Saved text to: price_insights_text.txt")
        
        # Look for the specific element/section containing price insights
        print()
        print("="*80)
        print("LOOKING FOR PRICE INSIGHT ELEMENTS")
        print("="*80)
        print()
        
        # Try to find elements with price-related text
        try:
            # Look for any element containing "currently"
            elements = await page.locator('text=/currently/i').all()
            print(f"Elements with 'currently': {len(elements)}")
            for i, elem in enumerate(elements[:5], 1):
                try:
                    text = await elem.text_content()
                    print(f"  [{i}] {text[:150]}")
                except:
                    pass
        except Exception as e:
            print(f"Error: {e}")
        
        print()
        print("="*80)
        print("GREP FOR KEY PHRASES IN TEXT")
        print("="*80)
        print()
        
        # Manual grep through the text
        key_phrases = [
            "Prices are",
            "currently typical",
            "currently low",
            "currently high",
            "cheaper than",
            "more expensive than",
        ]
        
        for phrase in key_phrases:
            if phrase.lower() in body_text.lower():
                # Find the context
                idx = body_text.lower().find(phrase.lower())
                context_start = max(0, idx - 50)
                context_end = min(len(body_text), idx + len(phrase) + 100)
                context = body_text[context_start:context_end]
                print(f"✓ Found: '{phrase}'")
                print(f"   Context: ...{context}...")
                print()
            else:
                print(f"✗ Not found: '{phrase}'")
        
        await browser.close()
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    
    if found_insights:
        print(f"✓ Found {len(found_insights)} types of price insights:")
        for insight in found_insights:
            print(f"  - {insight}")
    else:
        print("✗ No price insights found in the page")
        print()
        print("This could mean:")
        print("  1. Price insights are not shown for this route")
        print("  2. They're loaded dynamically after page load")
        print("  3. They're in a different format/location")
    
    print()
    print("Next steps:")
    print("  1. Review price_insights_page.html")
    print("  2. Search for 'typical', 'cheaper', 'usual' in the HTML")
    print("  3. If found, identify the DOM structure to extract it")

if __name__ == '__main__':
    asyncio.run(main())

