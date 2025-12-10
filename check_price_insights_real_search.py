#!/usr/bin/env python3
"""
Do a real flight search and check for price insights in the results.
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    print("="*80)
    print("CHECKING PRICE INSIGHTS WITH REAL SEARCH")
    print("="*80)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Go to Google Flights
        print("Loading Google Flights...")
        await page.goto("https://www.google.com/travel/flights", timeout=60000)
        await asyncio.sleep(2)
        
        # Fill in search form
        print("Filling search form: OKC → BCN, Dec 17-24, 2025")
        
        # Origin
        await page.fill('input[placeholder*="Where from" i]', 'OKC')
        await asyncio.sleep(1)
        await page.keyboard.press('Enter')
        await asyncio.sleep(1)
        
        # Destination
        await page.fill('input[placeholder*="Where to" i]', 'BCN')
        await asyncio.sleep(1)
        await page.keyboard.press('Enter')
        await asyncio.sleep(1)
        
        # Click departure date
        await page.click('input[placeholder*="Departure" i]')
        await asyncio.sleep(1)
        
        # Type date or select from calendar (let's try typing)
        # Actually, let's just click search and it will use default dates
        
        # Click search/explore button
        print("Clicking search...")
        await page.click('button:has-text("Explore"), button:has-text("Search")')
        
        # Wait for results to load
        print("Waiting for results...")
        await page.wait_for_selector('text=/Top departing flights|Best flights/i', timeout=30000)
        await asyncio.sleep(3)
        
        print("✓ Results loaded")
        print()
        
        # Now look for price insights
        print("="*80)
        print("LOOKING FOR PRICE INSIGHTS")
        print("="*80)
        print()
        
        # Get all text
        body_text = await page.text_content('body')
        
        # Search for price insight phrases
        import re
        
        patterns = {
            'Price status': r'Prices are currently (typical|low|high)',
            'Cheaper amount': r'\$(\d+) cheaper than usual',
            'More expensive': r'\$(\d+) more expensive than usual',
            'Percentage': r'(\d+)% (cheaper|more expensive)',
        }
        
        for name, pattern in patterns.items():
            match = re.search(pattern, body_text, re.IGNORECASE)
            if match:
                print(f"✓ {name}: {match.group(0)}")
            else:
                print(f"✗ {name}: Not found")
        
        # Look for "View price history" button
        print()
        print("Looking for price history button...")
        try:
            button = await page.locator('text=/View price history|price history/i').first
            if button:
                print("✓ Found price history button")
                button_text = await button.text_content()
                print(f"  Text: {button_text}")
                
                # Try to click it
                print("  Clicking...")
                await button.click()
                await asyncio.sleep(2)
                
                # Check for new content
                new_text = await page.text_content('body')
                
                # Look for additional insights after clicking
                print()
                print("After clicking price history:")
                
                for name, pattern in patterns.items():
                    match = re.search(pattern, new_text, re.IGNORECASE)
                    if match:
                        print(f"  ✓ {name}: {match.group(0)}")
        except Exception as e:
            print(f"✗ Error with price history button: {str(e)[:100]}")
        
        # Save HTML
        print()
        html = await page.content()
        with open('flights_search_results.html', 'w') as f:
            f.write(html)
        print("✓ Saved HTML to: flights_search_results.html")
        
        # Take a screenshot
        await page.screenshot(path='flights_search_results.png', full_page=True)
        print("✓ Saved screenshot to: flights_search_results.png")
        
        print()
        print("Keeping browser open for 15 seconds for inspection...")
        await asyncio.sleep(15)
        
        await browser.close()
    
    print()
    print("="*80)
    print("DONE")
    print("="*80)
    print()
    print("Review:")
    print("  - flights_search_results.html (full page HTML)")
    print("  - flights_search_results.png (screenshot)")

if __name__ == '__main__':
    asyncio.run(main())

