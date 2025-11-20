#!/usr/bin/env python3
"""
Capture API calls when clicking a deal card to see if deal quality data comes from an API.
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def capture_deal_quality_api():
    """Capture network requests when clicking a deal card."""
    
    # DFW → Europe explore URL
    tfs = "GhNqBRIDREZXcgoSCC9tLzAyajl6GhNqChIIL20vMDJqOXpyBRIDREZXQgEBSAGYAQE"
    url = f"https://www.google.com/travel/explore?tfs={tfs}&hl=en&gl=us&tfu=GgA"
    
    captured_requests = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture all XHR/Fetch requests
        async def handle_request(request):
            if request.resource_type in ["xhr", "fetch"]:
                post_data = None
                if request.method == "POST":
                    try:
                        post_data = request.post_data
                    except:
                        post_data = "<binary or gzipped data>"
                
                captured_requests.append({
                    "url": request.url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                    "post_data": post_data
                })
                print(f"📡 {request.method} {request.url[:100]}...")
        
        page.on("request", handle_request)
        
        print(f"Navigating to Explore page...")
        await page.goto(url, wait_until="networkidle")
        
        print(f"Waiting for cards...")
        await page.wait_for_selector(".SwQ5Be", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Get first card
        cards = await page.query_selector_all(".SwQ5Be")
        print(f"Found {len(cards)} cards")
        
        if cards:
            print(f"\nClicking first card...")
            
            # Clear captured requests
            captured_requests.clear()
            
            # Click and wait
            await cards[0].click()
            await page.wait_for_timeout(5000)
            
            print(f"\n{'='*80}")
            print(f"CAPTURED {len(captured_requests)} API CALLS AFTER CLICKING CARD:")
            print(f"{'='*80}\n")
            
            for i, req in enumerate(captured_requests):
                print(f"{i+1}. {req['method']} {req['url']}")
                if "FlightsFrontend" in req['url'] or "travel" in req['url']:
                    print(f"   ⭐ Likely relevant!")
            
            # Save to file
            with open("deal_quality_api_calls.json", "w") as f:
                json.dump(captured_requests, f, indent=2)
            
            print(f"\n✓ Saved to: deal_quality_api_calls.json")
            
            # Wait to see the page
            print(f"\nWaiting 10s to inspect page...")
            await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(capture_deal_quality_api())

