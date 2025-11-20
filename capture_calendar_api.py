#!/usr/bin/env python3
"""
Capture the calendar API request by monitoring network traffic.
This will help us identify the exact XHR/Fetch call that returns date grid data.
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def capture_api_call():
    """Capture the calendar API request details."""
    
    # Test with a known working route
    origin = 'ATL'
    destination = 'SJU'
    start_date = '2026-01-11'
    end_date = '2026-01-20'
    
    from scripts.expand_dates import build_flights_url
    url = build_flights_url(origin, destination, start_date, end_date)
    
    print(f"Testing: {origin} → {destination}")
    print(f"URL: {url}\n")
    
    captured_requests = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Capture ALL requests
        async def handle_request(request):
            # Look for FlightsFrontendUi or calendar-related requests
            if any(keyword in request.url for keyword in [
                'FlightsFrontendUi',
                'calendar',
                'GetCalendarGraph',
                'DateGrid',
                'PriceGraph'
            ]):
                captured_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': request.post_data,
                    'resource_type': request.resource_type
                })
                print(f"\n{'='*80}")
                print(f"CAPTURED REQUEST:")
                print(f"  URL: {request.url[:100]}...")
                print(f"  Method: {request.method}")
                print(f"  Type: {request.resource_type}")
                if request.post_data:
                    print(f"  Body length: {len(request.post_data)} bytes")
        
        page.on('request', handle_request)
        
        # Navigate and click date grid
        print("Navigating to flights page...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        
        print("Clicking 'Date grid' button...")
        try:
            await page.click('text="Date grid"', timeout=5000)
            await page.wait_for_timeout(5000)  # Wait for API calls
            print("Date grid clicked, waiting for API calls...")
        except Exception as e:
            print(f"Could not click Date grid: {e}")
            print("Trying 'Price graph' instead...")
            try:
                await page.click('text="Price graph"', timeout=5000)
                await page.wait_for_timeout(5000)
                print("Price graph clicked, waiting for API calls...")
            except Exception as e2:
                print(f"Could not click Price graph either: {e2}")
        
        await page.wait_for_timeout(3000)  # Extra wait for any delayed requests
        
        await browser.close()
    
    # Save captured requests
    print(f"\n{'='*80}")
    print(f"SUMMARY: Captured {len(captured_requests)} relevant requests")
    print('='*80)
    
    if captured_requests:
        with open('captured_api_requests.json', 'w') as f:
            json.dump(captured_requests, f, indent=2)
        print("\nSaved to: captured_api_requests.json")
        
        # Print details of most promising request
        for i, req in enumerate(captured_requests):
            print(f"\nRequest {i+1}:")
            print(f"  URL: {req['url']}")
            print(f"  Method: {req['method']}")
            if req['post_data']:
                print(f"  Has POST data: Yes ({len(req['post_data'])} bytes)")
            print(f"  Headers: {len(req['headers'])} headers")
    else:
        print("\n⚠️  No calendar API requests captured!")
        print("The date grid/price graph might not have loaded properly.")

if __name__ == '__main__':
    asyncio.run(capture_api_call())

