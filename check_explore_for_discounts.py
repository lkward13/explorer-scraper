#!/usr/bin/env python3
"""
Check if discount data is in the Explore page HTML (without clicking cards).
"""
import asyncio
from playwright.async_api import async_playwright
from explore_scraper.region_tfs_generator import build_explore_url_for_region


async def main():
    url = build_explore_url_for_region("PHX", "europe")
    
    print("Loading explore page...")
    print(f"URL: {url[:80]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)
        
        html = await page.content()
        
        # Save HTML
        with open('explore_page_full.html', 'w') as f:
            f.write(html)
        print("✓ Saved HTML to: explore_page_full.html")
        
        # Check for discount patterns
        patterns_to_check = [
            'cheaper than usual',
            'lower than usual',
            'currently low',
            'currently high',
            'currently typical',
            'Prices are'
        ]
        
        print("\nSearching for discount patterns in Explore page HTML:")
        print("-" * 80)
        
        for pattern in patterns_to_check:
            if pattern.lower() in html.lower():
                print(f"✓ Found: '{pattern}'")
                # Show context
                idx = html.lower().find(pattern.lower())
                context_start = max(0, idx - 100)
                context_end = min(len(html), idx + len(pattern) + 100)
                context = html[context_start:context_end]
                print(f"  Context: ...{context[:200]}...")
                print()
            else:
                print(f"✗ Not found: '{pattern}'")
        
        await browser.close()
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("Review explore_page_full.html to see if discount data is embedded")
    print("If not found: Discount data only appears AFTER clicking each card")


if __name__ == '__main__':
    asyncio.run(main())

