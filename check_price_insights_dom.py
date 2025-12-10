#!/usr/bin/env python3
"""
Check if price insights are available in the DOM without needing to click.
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    print("="*80)
    print("CHECKING FOR PRICE INSIGHTS IN DOM")
    print("="*80)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to a flights search (OKC -> BCN)
        url = "https://www.google.com/travel/flights/search?tfs=CBwQAhojEgoyMDI1LTEyLTE3agcIARIDT0tDcgcIARIDQkNOGwEBSAGYAQE&hl=en&gl=us"
        print(f"Loading: {url}")
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        print("✓ Page loaded")
        print()
        
        # Wait a bit for dynamic content
        await asyncio.sleep(3)
        
        # Look for price insight text
        print("Looking for price insights in the DOM...")
        print("-"*80)
        
        # Check for common price insight phrases
        phrases = [
            "currently typical",
            "currently low",
            "currently high",
            "cheaper than usual",
            "lower than usual",
            "higher than usual",
            "Prices are",
            "price history",
        ]
        
        for phrase in phrases:
            try:
                # Check if phrase exists anywhere on page
                elements = await page.locator(f"text=/{phrase}/i").all()
                if elements:
                    print(f"✓ Found '{phrase}' ({len(elements)} instances)")
                    
                    # Get the text content and context
                    for i, elem in enumerate(elements[:3], 1):
                        try:
                            text = await elem.text_content()
                            print(f"  [{i}] Text: {text[:100]}")
                            
                            # Get parent to see context
                            parent = elem.locator('..')
                            parent_text = await parent.text_content()
                            print(f"      Context: {parent_text[:150]}")
                        except:
                            pass
                else:
                    print(f"✗ Not found: '{phrase}'")
            except:
                print(f"✗ Error checking: '{phrase}'")
        
        print()
        print("="*80)
        print("LOOKING FOR SPECIFIC ELEMENTS")
        print("="*80)
        print()
        
        # Look for price insight section/container
        selectors = [
            '[class*="price"][class*="insight" i]',
            '[class*="price"][class*="history" i]',
            '[class*="typical" i]',
            '[aria-label*="price" i]',
            'button:has-text("price history")',
            'button:has-text("View price history")',
        ]
        
        for selector in selectors:
            try:
                elements = await page.locator(selector).all()
                if elements:
                    print(f"✓ Found selector: {selector} ({len(elements)} matches)")
                    for i, elem in enumerate(elements[:2], 1):
                        text = await elem.text_content()
                        print(f"  [{i}] {text[:100]}")
                else:
                    print(f"✗ Not found: {selector}")
            except Exception as e:
                print(f"✗ Error with selector '{selector}': {str(e)[:50]}")
        
        print()
        print("="*80)
        print("EXTRACTING FULL PAGE TEXT")
        print("="*80)
        print()
        
        # Get all text and search for patterns
        body_text = await page.text_content('body')
        
        # Search for specific patterns
        import re
        
        # Pattern 1: "Prices are currently X"
        pattern1 = re.search(r'Prices are currently (\w+)', body_text, re.IGNORECASE)
        if pattern1:
            print(f"✓ Price status: {pattern1.group(0)}")
        
        # Pattern 2: "$X cheaper than usual"
        pattern2 = re.search(r'\$(\d+) cheaper than usual', body_text, re.IGNORECASE)
        if pattern2:
            print(f"✓ Discount: {pattern2.group(0)}")
        
        # Pattern 3: "X% cheaper"
        pattern3 = re.search(r'(\d+)% cheaper', body_text, re.IGNORECASE)
        if pattern3:
            print(f"✓ Percentage: {pattern3.group(0)}")
        
        # Save page HTML for inspection
        html = await page.content()
        with open('flights_page.html', 'w') as f:
            f.write(html)
        print()
        print("✓ Saved full HTML to: flights_page.html")
        
        # Now try clicking "View price history" if it exists
        print()
        print("="*80)
        print("TRYING TO CLICK PRICE HISTORY")
        print("="*80)
        print()
        
        try:
            # Look for the button
            button = page.locator('button:has-text("View price history"), button:has-text("price history")')
            if await button.count() > 0:
                print("✓ Found 'View price history' button")
                await button.first.click()
                print("✓ Clicked button")
                
                # Wait for any modal/panel to appear
                await asyncio.sleep(2)
                
                # Check for new content
                new_text = await page.text_content('body')
                
                # Look for additional insights
                pattern4 = re.search(r'\$(\d+)[-–]?\$?(\d+)? (cheaper|more expensive)', new_text, re.IGNORECASE)
                if pattern4:
                    print(f"✓ After click: {pattern4.group(0)}")
                
                # Save HTML after click
                html_after = await page.content()
                with open('flights_page_after_click.html', 'w') as f:
                    f.write(html_after)
                print("✓ Saved HTML after click to: flights_page_after_click.html")
            else:
                print("✗ 'View price history' button not found")
        except Exception as e:
            print(f"✗ Error clicking button: {e}")
        
        print()
        print("Keeping browser open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)
        
        await browser.close()
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print("Files created:")
    print("  - flights_page.html (before click)")
    print("  - flights_page_after_click.html (after clicking price history)")
    print()
    print("Next: Review these files to find where price insights are stored")

if __name__ == '__main__':
    asyncio.run(main())

