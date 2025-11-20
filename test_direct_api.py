#!/usr/bin/env python3
"""
Test calling the GetCalendarGrid API directly without browser automation.
"""
import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

# Decode the captured POST data
captured_post_data = "f.req=%5Bnull%2C%22%5Bnull%2C%5Bnull%2Cnull%2C1%2Cnull%2C%5B%5D%2C1%2C%5B1%2C0%2C0%2C0%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B%5B%5B%5B%5C%22ATL%5C%22%2C0%5D%5D%5D%2C%5B%5B%5B%5C%22SJU%5C%22%2C0%5D%5D%5D%2Cnull%2C0%2Cnull%2Cnull%2C%5C%222026-01-11%5C%22%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C3%5D%2C%5B%5B%5B%5B%5C%22SJU%5C%22%2C0%5D%5D%5D%2C%5B%5B%5B%5C%22ATL%5C%22%2C0%5D%5D%5D%2Cnull%2C0%2Cnull%2Cnull%2C%5C%222026-01-20%5C%22%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C3%5D%5D%2Cnull%2Cnull%2Cnull%2C1%5D%2C%5B%5C%222026-01-08%5C%22%2C%5C%222026-01-14%5C%22%5D%2C%5B%5C%222026-01-17%5C%22%2C%5C%222026-01-23%5C%22%5D%5D%22%5D&"

decoded = urllib.parse.unquote(captured_post_data)
print("Decoded POST data:")
print(decoded)
print("\n" + "="*80 + "\n")

# Parse the f.req parameter
params = urllib.parse.parse_qs(captured_post_data)
f_req = params.get('f.req', [''])[0]
f_req_decoded = urllib.parse.unquote(f_req)
print("f.req decoded:")
print(f_req_decoded)
print("\n" + "="*80 + "\n")

# Try to parse as JSON
try:
    f_req_json = json.loads(f_req_decoded)
    print("f.req as JSON:")
    print(json.dumps(f_req_json, indent=2))
except Exception as e:
    print(f"Could not parse as JSON: {e}")

print("\n" + "="*80 + "\n")

# Now let's test calling the API directly
async def test_direct_api_call():
    """Test calling the GetCalendarGrid API directly using Playwright's request context."""
    
    print("Testing direct API call...")
    
    # Build the request
    api_url = "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGrid"
    
    # Query parameters
    params = {
        'f.sid': '-3556833754367434112',  # This might need to be dynamic
        'bl': 'boq_travel-frontend-flights-ui_20251118.02_p0',
        'hl': 'en',
        'gl': 'us',
        'soc-app': '162',
        'soc-platform': '1',
        'soc-device': '1',
        '_reqid': '272427',
        'rt': 'c'
    }
    
    full_url = api_url + '?' + urllib.parse.urlencode(params)
    
    # Headers (from captured request)
    headers = {
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'x-same-domain': '1',
        'referer': 'https://www.google.com/travel/flights?tfs=GhoSCjIwMjYtMDEtMTFqBRIDQVRMcgUSA1NKVRoaEgoyMDI2LTAxLTIwagUSA1NKVXIFEgNBVExCAQFIAZgBAQ&hl=en&gl=us',
    }
    
    # POST body
    post_body = captured_post_data
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
        # Make the API call using context.request
        try:
            response = await context.request.post(
                full_url,
                data=post_body,
                headers=headers
            )
            
            print(f"Status: {response.status}")
            print(f"Headers: {response.headers}")
            
            if response.ok:
                text = await response.text()
                print(f"\nResponse (first 500 chars):")
                print(text[:500])
                
                # Try to parse as JSON
                try:
                    # Google's response might be wrapped in )]}' for security
                    if text.startswith(")]}'"):
                        text = text[4:]
                    data = json.loads(text)
                    print(f"\n✓ Successfully parsed JSON response!")
                    print(f"Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                except Exception as e:
                    print(f"\nCould not parse as JSON: {e}")
            else:
                print(f"✗ Request failed: {response.status}")
                print(await response.text())
                
        except Exception as e:
            print(f"✗ Error making request: {e}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_direct_api_call())

