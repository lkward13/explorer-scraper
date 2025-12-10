#!/usr/bin/env python3
"""
Extract price insights from Google Flights by clicking price history button.
"""
import asyncio
import re
from playwright.async_api import async_playwright

async def extract_price_insights(origin: str, destination: str, outbound_date: str, return_date: str):
    """
    Extract price insights for a specific flight.
    
    Returns:
        dict with price_status, price_range, and comparison
    """
    from explore_scraper.tfs_builder import build_round_trip_flight_url
    
    url = build_round_trip_flight_url(origin, destination, outbound_date, return_date)
    
    print(f"Loading: {origin} → {destination}, {outbound_date} to {return_date}")
    print(f"URL: {url[:80]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(5)  # Wait longer for dynamic content
        
        # First check if price insights section exists
        insights_container = page.locator('.BOyk6b, h3:has-text("Price insights")')
        if await insights_container.count() > 0:
            print("✓ Price insights section found on page")
        else:
            print("✗ Price insights section NOT found - route may not have historical data")
            # Save HTML for debugging
            html = await page.content()
            with open('no_insights_page.html', 'w') as f:
                f.write(html)
            print("Saved HTML to no_insights_page.html for inspection")
        
        # Try to click "View price history" button to expand details
        try:
            button = page.locator('button[aria-label="View price history"]')
            if await button.count() > 0:
                print("Clicking 'View price history' button...")
                await button.first.click()
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Could not click button: {e}")
        
        # Now extract price insights from the DOM
        insights = {}
        
        # Get all text
        body_text = await page.text_content('body')
        
        # Pattern 1: "Prices are currently X"
        match1 = re.search(r'Prices are currently\s+(\w+)', body_text, re.IGNORECASE)
        if match1:
            insights['price_status'] = match1.group(1).lower()  # e.g., "high", "low", "typical"
            print(f"✓ Price status: {insights['price_status']}")
        
        # Pattern 2: "usually cost between $X–$Y" or "$X-$Y"
        match2 = re.search(r'usually cost between \$(\d+)[–-]\$?(\d+)', body_text, re.IGNORECASE)
        if match2:
            insights['typical_range_low'] = int(match2.group(1))
            insights['typical_range_high'] = int(match2.group(2))
            print(f"✓ Typical range: ${insights['typical_range_low']}-${insights['typical_range_high']}")
        
        # Pattern 3: "$X is high/low/typical"
        match3 = re.search(r'\$(\d+) is (\w+)', body_text, re.IGNORECASE)
        if match3:
            insights['current_price'] = int(match3.group(1))
            insights['price_assessment'] = match3.group(2).lower()
            print(f"✓ Current price: ${insights['current_price']} is {insights['price_assessment']}")
        
        # Look in specific div class="BOyk6b" for more structured data
        try:
            insights_div = page.locator('.BOyk6b, .frOi8')
            if await insights_div.count() > 0:
                insights_text = await insights_div.first.text_content()
                print(f"✓ Full insights text: {insights_text[:200]}")
        except:
            pass
        
        await browser.close()
    
    return insights

async def main():
    print("="*80)
    print("EXTRACTING PRICE INSIGHTS FROM GOOGLE FLIGHTS")
    print("="*80)
    print()
    
    # Test with a popular route that should have insights (DFW → LHR)
    insights = await extract_price_insights(
        origin='DFW',
        destination='LHR',
        outbound_date='2026-03-15',
        return_date='2026-03-22'
    )
    
    print()
    print("="*80)
    print("EXTRACTED INSIGHTS")
    print("="*80)
    print()
    
    if insights:
        for key, value in insights.items():
            print(f"  {key}: {value}")
    else:
        print("  No insights found")
    
    print()
    print("="*80)
    print("NEXT: Integrate into expand_dates_api.py")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(main())

