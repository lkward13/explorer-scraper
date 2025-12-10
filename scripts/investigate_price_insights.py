#!/usr/bin/env python3
"""
Investigate where price insights come from:
1. Check initial page load <script> tags for embedded JSON
2. Monitor ALL network requests when price insights appear
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright


async def investigate_price_insights():
    """Load a Google Flights search and capture everything."""
    
    # Test route: JFK → Barcelona (known to have price insights)
    url = "https://www.google.com/travel/flights/search?tfs=CBwQAhooagwIAhIIL20vMDJfMjg6DEoISi9tLzAxNWZyEgoyMDI1LTAzLTE1GigKDAgCEggvbS8wMV9mcjIMSghKL20vMDJfMjgSCjIwMjUtMDMtMjJAAUgBcAGCAQsI____________AUABSAGYAQE&hl=en&gl=us"
    
    print("=" * 80)
    print("INVESTIGATING PRICE INSIGHTS")
    print("=" * 80)
    print(f"URL: {url}")
    print()
    
    async with async_playwright() as p:
        # Launch browser with stealth
        browser = await p.chromium.launch(
            headless=False,  # Visible so we can see what's happening
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Track all network requests
        network_log = []
        
        async def log_request(request):
            network_log.append({
                'type': 'request',
                'method': request.method,
                'url': request.url,
                'resource_type': request.resource_type
            })
        
        async def log_response(response):
            url = response.url
            # Only log interesting responses
            if any(keyword in url for keyword in ['rpc', 'api', 'GetCalendar', 'GetExplore', 'insight', 'price', 'typical']):
                try:
                    body = await response.text()
                    network_log.append({
                        'type': 'response',
                        'method': response.request.method,
                        'url': url,
                        'status': response.status,
                        'content_type': response.headers.get('content-type', ''),
                        'body_preview': body[:500] if body else None,
                        'body_length': len(body) if body else 0
                    })
                except:
                    pass
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        print("Loading page...")
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        print("✓ Page loaded")
        print()
        
        # ========== PART 1: Check initial page HTML for embedded JSON ==========
        print("=" * 80)
        print("PART 1: CHECKING INITIAL PAGE <SCRIPT> TAGS FOR EMBEDDED DATA")
        print("=" * 80)
        
        # Get all script tags
        scripts = await page.query_selector_all('script')
        print(f"Found {len(scripts)} <script> tags")
        print()
        
        for i, script in enumerate(scripts):
            content = await script.inner_text()
            if not content or len(content) < 100:
                continue
            
            # Look for price insight keywords
            if any(keyword in content.lower() for keyword in ['insight', 'typical', 'cheaper', 'expensive', 'usual']):
                print(f"Script {i+1}: Contains price insight keywords!")
                print(f"Length: {len(content)} chars")
                print(f"Preview: {content[:300]}...")
                print()
                
                # Try to extract JSON
                # Common patterns: var data = {...}, window.WIZ_global_data = {...}
                json_patterns = [
                    r'var\s+\w+\s*=\s*(\{.*?\});',
                    r'window\.\w+\s*=\s*(\{.*?\});',
                    r'=\s*(\{.*?\});',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            # Check if this JSON contains price insights
                            data_str = json.dumps(data).lower()
                            if 'insight' in data_str or 'typical' in data_str:
                                print(f"  → Found JSON with price insight data!")
                                print(f"  → Keys: {list(data.keys())[:10]}")
                                
                                # Save to file for inspection
                                with open('/tmp/price_insight_json.json', 'w') as f:
                                    json.dump(data, f, indent=2)
                                print(f"  → Saved to /tmp/price_insight_json.json")
                                print()
                        except:
                            pass
        
        # ========== PART 2: Wait for price insights to appear and check network ==========
        print("=" * 80)
        print("PART 2: WAITING FOR PRICE INSIGHTS TO LOAD")
        print("=" * 80)
        
        # Wait for price insights element
        try:
            print("Waiting for price insights element...")
            await page.wait_for_selector('.frOi8, .BOyk6b, [class*="insight"]', timeout=30000)
            print("✓ Price insights element found!")
            print()
        except:
            print("⚠ Price insights element not found (might be CAPTCHA or no insights for this route)")
            print()
        
        # Check if price insights are visible
        insight_text = await page.evaluate('''() => {
            const elements = document.querySelectorAll('.frOi8, .BOyk6b, .NtS4zd');
            return Array.from(elements).map(el => el.textContent).join(' | ');
        }''')
        
        if insight_text:
            print("Price Insights Found in DOM:")
            print(f"  {insight_text}")
            print()
        
        # ========== PART 3: Analyze network log ==========
        print("=" * 80)
        print("PART 3: NETWORK REQUESTS ANALYSIS")
        print("=" * 80)
        
        print(f"Total requests captured: {len([r for r in network_log if r['type'] == 'request'])}")
        print(f"Interesting responses: {len([r for r in network_log if r['type'] == 'response'])}")
        print()
        
        # Filter for RPC/API calls
        rpc_calls = [r for r in network_log if r['type'] == 'response' and 'rpc' in r['url'].lower()]
        
        if rpc_calls:
            print("RPC/API Calls Found:")
            for call in rpc_calls:
                print(f"\n  URL: {call['url']}")
                print(f"  Method: {call['method']}")
                print(f"  Status: {call['status']}")
                print(f"  Content-Type: {call['content_type']}")
                print(f"  Body Length: {call['body_length']} bytes")
                if call.get('body_preview'):
                    print(f"  Preview: {call['body_preview']}")
        else:
            print("No RPC calls found")
        
        # Save full network log
        with open('/tmp/network_log.json', 'w') as f:
            json.dump(network_log, f, indent=2)
        print()
        print("✓ Full network log saved to /tmp/network_log.json")
        
        # Keep browser open for manual inspection
        print()
        print("=" * 80)
        print("Browser will stay open for 30 seconds for manual inspection...")
        print("Check the page for price insights and inspect network tab")
        print("=" * 80)
        await asyncio.sleep(30)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(investigate_price_insights())


