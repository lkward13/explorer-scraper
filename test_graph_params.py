#!/usr/bin/env python3
"""
Test different grid parameters to see if we can get more months.
"""
import asyncio
import json
import urllib.parse
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

async def test_grid_sizes():
    """Test different grid size parameters."""
    
    origin = "ATL"
    destination = "SJU"
    outbound_date = "2026-01-11"
    return_date = "2026-01-20"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
        # Test different grid sizes
        # The UI might use a larger grid to get more data
        test_cases = [
            ("Grid [9, 9]", [9, 9]),
            ("Grid [12, 12]", [12, 12]),
            ("Grid [15, 15]", [15, 15]),
            ("Grid [20, 20]", [20, 20]),
            ("Grid [30, 30]", [30, 30]),
        ]
        
        # Use a wide date range
        start_range = "2026-01-11"
        end_range = "2026-10-11"  # 9 months like the screenshot
        
        for label, grid_size in test_cases:
            print(f"\n{'='*80}")
            print(f"{label}")
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
                grid_size  # Try different grid sizes
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
                
                if not response.ok:
                    print(f"✗ Failed with status {response.status}")
                    continue
                
                text = await response.text()
                if text.startswith(")]}'"):
                    text = text[4:]
                
                # Count dates
                pattern = r'\[\\?"(\d{4}-\d{2}-\d{2})\\?",\\?"(\d{4}-\d{2}-\d{2})\\?",\[\[null,(\d+)\]'
                matches = re.findall(pattern, text)
                
                if matches:
                    dates = [m[0] for m in matches]
                    print(f"✓ Found {len(matches)} date combinations")
                    print(f"  Date range: {min(dates)} to {max(dates)}")
                    
                    # Count months
                    from collections import Counter
                    months = Counter([d[:7] for d in dates])
                    print(f"  Months covered: {len(months)}")
                    for month in sorted(months.keys()):
                        print(f"    {month}: {months[month]} dates")
                else:
                    print(f"✗ No date combinations found")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
        await context.close()
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_grid_sizes())

