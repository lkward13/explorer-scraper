#!/usr/bin/env python3
"""
Check if deal quality data is in the initial GetExploreDestinations response.
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def check_explore_response():
    """Capture the GetExploreDestinations response to see if it has deal quality."""
    
    tfs = "GhNqBRIDREZXcgoSCC9tLzAyajl6GhNqChIIL20vMDJqOXpyBRIDREZXQgEBSAGYAQE"
    url = f"https://www.google.com/travel/explore?tfs={tfs}&hl=en&gl=us&tfu=GgA"
    
    explore_response = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture GetExploreDestinations response
        async def handle_response(response):
            nonlocal explore_response
            if "GetExploreDestinations" in response.url and response.status == 200:
                print(f"✓ Captured GetExploreDestinations response")
                try:
                    text = await response.text()
                    explore_response = text
                except Exception as e:
                    print(f"Error reading response: {e}")
        
        page.on("response", handle_response)
        
        print(f"Loading Explore page...")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        await browser.close()
    
    if explore_response:
        # Remove )]}' prefix
        if explore_response.startswith(")]}'"):
            explore_response = explore_response[4:]
        
        # Save to file
        with open("explore_destinations_response.txt", "w") as f:
            f.write(explore_response)
        
        print(f"\n✓ Saved response to: explore_destinations_response.txt")
        print(f"Response length: {len(explore_response)} chars")
        
        # Check for "cheaper" keyword
        if "cheaper" in explore_response.lower():
            print(f"✅ Found 'cheaper' in response - deal quality data IS included!")
            
            # Count occurrences
            import re
            cheaper_matches = re.findall(r'\$\d+\s+cheaper', explore_response, re.IGNORECASE)
            print(f"   Found {len(cheaper_matches)} 'cheaper' mentions")
            if cheaper_matches:
                print(f"   Examples: {cheaper_matches[:3]}")
        else:
            print(f"❌ No 'cheaper' found - deal quality NOT in initial response")
            print(f"   (Would need separate GetExploreDestinationFlightDetails calls)")
        
        # Show first 1000 chars
        print(f"\nFirst 1000 chars of response:")
        print(explore_response[:1000])
    else:
        print("✗ Failed to capture GetExploreDestinations response")

if __name__ == '__main__':
    asyncio.run(check_explore_response())

