#!/usr/bin/env python3
"""
Capture both GetCalendarGrid (date grid) and GetCalendarGraph (price graph) API calls.
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def capture_both():
    """Capture both calendar APIs."""
    
    url = "https://www.google.com/travel/flights?tfs=GhoSCjIwMjYtMDEtMTFqBRIDQVRMcgUSA1NKVRoaEgoyMDI2LTAxLTIwagUSA1NKVXIFEgNBVExCAQFIAZgBAQ&hl=en&gl=us"
    
    print("Testing: ATL → SJU")
    print(f"URL: {url}\n")
    
    captured = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        async def handle_request(request):
            if 'GetCalendar' in request.url:
                captured.append({
                    'url': request.url,
                    'method': request.method,
                    'post_data': request.post_data,
                })
                api_name = 'Grid' if 'Grid' in request.url else 'Graph'
                print(f"🎯 Captured: GetCalendar{api_name}")
        
        page.on('request', handle_request)
        
        print("Navigating...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        
        print("\nClicking 'Price graph'...")
        try:
            await page.click('text="Price graph"', timeout=5000)
            await page.wait_for_timeout(5000)
            print("✓ Clicked Price graph")
        except Exception as e:
            print(f"✗ Could not click: {e}")
        
        print("\nClicking 'Date grid'...")
        try:
            await page.click('text="Date grid"', timeout=5000)
            await page.wait_for_timeout(5000)
            print("✓ Clicked Date grid")
        except Exception as e:
            print(f"✗ Could not click: {e}")
        
        await browser.close()
    
    print(f"\n{'='*80}")
    print(f"Captured {len(captured)} API calls")
    print('='*80)
    
    for i, req in enumerate(captured, 1):
        api_type = 'Grid' if 'Grid' in req['url'] else 'Graph'
        print(f"\n{i}. GetCalendar{api_type}")
        print(f"   URL: {req['url'][:80]}...")
        print(f"   POST data length: {len(req['post_data'])} bytes")
        
        # Decode and show structure
        import urllib.parse
        params = urllib.parse.parse_qs(req['post_data'])
        if 'f.req' in params:
            f_req = urllib.parse.unquote(params['f.req'][0])
            print(f"   f.req preview: {f_req[:150]}...")
    
    # Save both
    with open('both_calendar_apis.json', 'w') as f:
        json.dump(captured, f, indent=2)
    print(f"\n✓ Saved to: both_calendar_apis.json")

if __name__ == '__main__':
    asyncio.run(capture_both())

