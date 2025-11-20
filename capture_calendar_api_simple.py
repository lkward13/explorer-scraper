#!/usr/bin/env python3
"""
Capture the GetCalendarGrid API request by monitoring network traffic.
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def capture_api_call():
    """Capture the calendar API request details."""
    
    # Test URL
    url = "https://www.google.com/travel/flights?tfs=GhoSCjIwMjYtMDEtMTFqBRIDQVRMcgUSA1NKVRoaEgoyMDI2LTAxLTIwagUSA1NKVXIFEgNBVExCAQFIAZgBAQ&hl=en&gl=us"
    
    print(f"Testing: ATL → SJU")
    print(f"URL: {url}\n")
    
    captured_requests = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Capture ALL requests
        async def handle_request(request):
            # Look for GetCalendarGrid
            if 'GetCalendarGrid' in request.url or 'GetCalendarGraph' in request.url:
                captured_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                    'resource_type': request.resource_type
                })
                print(f"\n{'='*80}")
                print(f"🎯 CAPTURED: {request.url[:80]}...")
                print(f"   Method: {request.method}")
                print(f"   Body: {len(request.post_data) if request.post_data else 0} bytes")
        
        page.on('request', handle_request)
        
        # Navigate and click date grid
        print("Navigating to flights page...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        
        print("Clicking 'Date grid' button...")
        try:
            await page.click('text="Date grid"', timeout=5000)
            await page.wait_for_timeout(5000)  # Wait for API calls
            print("✓ Date grid clicked")
        except Exception as e:
            print(f"✗ Could not click Date grid: {e}")
        
        await page.wait_for_timeout(3000)
        
        await browser.close()
    
    # Save captured requests
    print(f"\n{'='*80}")
    print(f"SUMMARY: Captured {len(captured_requests)} calendar API requests")
    print('='*80)
    
    if captured_requests:
        with open('captured_calendar_api.json', 'w') as f:
            json.dump(captured_requests, f, indent=2)
        print("\n✓ Saved to: captured_calendar_api.json")
        
        # Print details
        for i, req in enumerate(captured_requests):
            print(f"\n📋 Request {i+1}:")
            print(f"   URL: {req['url']}")
            print(f"   Method: {req['method']}")
            if req['post_data']:
                print(f"   POST data length: {len(req['post_data'])} bytes")
                print(f"   POST data preview: {req['post_data'][:200]}...")
    else:
        print("\n⚠️  No calendar API requests captured!")

if __name__ == '__main__':
    asyncio.run(capture_api_call())

