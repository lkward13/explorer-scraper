#!/usr/bin/env python3
"""
Debug why GetCalendarGraph isn't returning 12 months of data.
"""
import asyncio
import json
import urllib.parse
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

async def test_graph_ranges():
    """Test different date ranges to see what the API returns."""
    
    origin = "ATL"
    destination = "SJU"
    outbound_date = "2026-01-11"
    return_date = "2026-01-20"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
        # Test multiple ranges
        test_cases = [
            ("Range 1: First 6 months", "2026-01-11", "2026-07-11"),
            ("Range 2: Second 6 months", "2026-07-12", "2027-01-11"),
            ("Range 3: First 3 months", "2026-01-11", "2026-04-11"),
            ("Range 4: Months 4-6", "2026-04-12", "2026-07-11"),
        ]
        
        for label, start_range, end_range in test_cases:
            print(f"\n{'='*80}")
            print(f"{label}: {start_range} to {end_range}")
            print(f"{'='*80}")
            
            # Build request
            inner_structure = [
                None,
                [
                    None, None, 1, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None,
                    [
                        [
                            [[[origin, 0]]],
                            [[[destination, 0]]],
                            None, 0, None, None, outbound_date,
                            None, None, None, None, None, None, None, 3
                        ],
                        [
                            [[[destination, 0]]],
                            [[[origin, 0]]],
                            None, 0, None, None, return_date,
                            None, None, None, None, None, None, None, 3
                        ]
                    ],
                    None, None, None, 1
                ],
                [start_range, end_range],
                None,
                [9, 9]
            ]
            
            outer_json = json.dumps([None, json.dumps(inner_structure, separators=(',', ':'))], separators=(',', ':'))
            post_body = f"f.req={urllib.parse.quote(outer_json)}&"
            
            url = "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGraph?f.sid=1&bl=boq_travel-frontend-flights-ui_20251118.02_p0&hl=en&gl=us&soc-app=162&soc-platform=1&soc-device=1&_reqid=1&rt=c"
            
            headers = {
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                'x-same-domain': '1',
                'referer': 'https://www.google.com/travel/flights'
            }
            
            try:
                response = await context.request.post(url, data=post_body, headers=headers, timeout=30000)
                
                print(f"Status: {response.status}")
                
                if not response.ok:
                    print(f"✗ Failed with status {response.status}")
                    text = await response.text()
                    print(f"Response: {text[:200]}")
                    continue
                
                text = await response.text()
                if text.startswith(")]}'"):
                    text = text[4:]
                
                # Count dates
                pattern = r'\[\\?"(\d{4}-\d{2}-\d{2})\\?",\\?"(\d{4}-\d{2}-\d{2})\\?",\[\[null,(\d+)\]'
                matches = re.findall(pattern, text)
                
                if matches:
                    dates = [m[0] for m in matches]
                    prices = [int(m[2]) for m in matches]
                    print(f"✓ Found {len(matches)} date combinations")
                    print(f"  Date range: {min(dates)} to {max(dates)}")
                    print(f"  Price range: ${min(prices)} - ${max(prices)}")
                    
                    # Show first 3 and last 3
                    print(f"\n  First 3:")
                    for i, (out, ret, price) in enumerate(matches[:3]):
                        print(f"    {i+1}. {out} to {ret}: ${price}")
                    
                    if len(matches) > 6:
                        print(f"  ...")
                        print(f"  Last 3:")
                        for i, (out, ret, price) in enumerate(matches[-3:]):
                            print(f"    {len(matches)-2+i}. {out} to {ret}: ${price}")
                else:
                    print(f"✗ No date combinations found")
                    print(f"Response length: {len(text)} chars")
                    print(f"Response preview: {text[:500]}")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
        await context.close()
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_graph_ranges())

