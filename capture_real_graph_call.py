#!/usr/bin/env python3
"""
Capture the REAL GetCalendarGraph API call from the browser.
"""
import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

async def capture_graph_api():
    """Capture what the browser actually sends."""
    
    origin = "ATL"
    destination = "SJU"
    outbound_date = "2026-01-11"
    return_date = "2026-01-20"
    
    # Use a simple URL (Google will handle it)
    url = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}+on+{outbound_date}+return+{return_date}&hl=en&gl=us"
    
    captured_requests = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture network requests
        async def handle_request(request):
            if "GetCalendarGraph" in request.url and request.method == "POST":
                post_data = request.post_data
                if post_data:
                    captured_requests.append({
                        "url": request.url,
                        "method": request.method,
                        "headers": dict(request.headers),
                        "post_data": post_data,
                    })
                    print(f"\n🎯 CAPTURED GetCalendarGraph!")
                    print(f"   URL: {request.url[:100]}...")
                    print(f"   Body length: {len(post_data)} bytes")
        
        page.on("request", handle_request)
        
        print(f"Navigating to: {url[:100]}...")
        await page.goto(url, timeout=60000, wait_until='networkidle')
        
        print("Waiting for page to load...")
        await page.wait_for_timeout(3000)
        
        # Click Price graph
        print("Clicking 'Price graph'...")
        try:
            await page.click('text="Price graph"', timeout=10000)
            print("✓ Price graph clicked")
            
            # Wait for initial API call
            await page.wait_for_timeout(3000)
            
            print(f"Captured {len(captured_requests)} API call(s) so far...")
            
            # Try scrolling the graph to trigger more API calls
            print("Scrolling graph to the right...")
            try:
                # Click the right arrow multiple times
                for i in range(5):
                    await page.click('button[aria-label*="Next"]', timeout=5000)
                    await page.wait_for_timeout(1000)
                    print(f"  Scroll {i+1}/5 - Total API calls: {len(captured_requests)}")
            except Exception as e:
                print(f"  Could not scroll: {e}")
            
            # Wait a bit more
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"✗ Could not click Price graph: {e}")
        
        # Save captured data
        if captured_requests:
            with open("real_graph_api_call.json", "w") as f:
                json.dump(captured_requests, f, indent=2)
            print(f"\n✓ Saved to: real_graph_api_call.json")
            
            # Decode the POST data
            for req in captured_requests:
                post_data = req['post_data']
                parsed = urllib.parse.parse_qs(post_data)
                if 'f.req' in parsed:
                    f_req = parsed['f.req'][0]
                    decoded = urllib.parse.unquote(f_req)
                    print(f"\nDecoded f.req:")
                    print(json.dumps(json.loads(decoded), indent=2))
        else:
            print("\n✗ No GetCalendarGraph API call captured")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(capture_graph_api())

