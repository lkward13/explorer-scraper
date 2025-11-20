#!/usr/bin/env python3
"""
Test GetCalendarGraph API to see how much data it returns.
"""
import asyncio
import json
import urllib.parse
import re
from playwright.async_api import async_playwright
from datetime import datetime

async def test_graph_api():
    """Test the price graph API."""
    
    # Build request for GetCalendarGraph
    origin = 'ATL'
    destination = 'SJU'
    outbound_date = '2026-01-11'
    return_date = '2026-01-20'
    
    # Use the captured structure for GetCalendarGraph
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
        ["2026-01-04", "2026-07-04"],  # 6 month window
        None,
        [9, 9]  # Grid size
    ]
    
    inner_json_str = json.dumps(inner_structure, separators=(',', ':'))
    outer_structure = [None, inner_json_str]
    outer_json = json.dumps(outer_structure, separators=(',', ':'))
    post_body = f"f.req={urllib.parse.quote(outer_json)}&"
    
    print(f"Testing GetCalendarGraph API")
    print(f"Route: {origin} → {destination}")
    print(f"Date range in request: 2026-01-04 to 2026-07-04 (6 months)")
    print()
    
    api_url = "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGraph"
    params = {
        'f.sid': '1',
        'bl': 'boq_travel-frontend-flights-ui_20251118.02_p0',
        'hl': 'en',
        'gl': 'us',
        'soc-app': '162',
        'soc-platform': '1',
        'soc-device': '1',
        '_reqid': '1',
        'rt': 'c'
    }
    full_url = api_url + '?' + urllib.parse.urlencode(params)
    
    headers = {
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'x-same-domain': '1',
        'referer': 'https://www.google.com/travel/flights',
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
        response = await context.request.post(full_url, data=post_body, headers=headers, timeout=30000)
        
        if response.ok:
            text = await response.text()
            if text.startswith(")]}'"):
                text = text[4:]
            
            print(f"Response size: {len(text)} bytes")
            print(f"Response preview: {text[:500]}")
            print()
            
            # Find all dates in the response (handle escaped quotes)
            date_pattern = r'\\?"(\d{4}-\d{2}-\d{2})\\?"'
            matches = re.findall(date_pattern, text)
            unique_dates = sorted(set(matches))
            
            print(f"Found {len(unique_dates)} unique dates in response:")
            if unique_dates:
                print(f"  First date: {unique_dates[0]}")
                print(f"  Last date:  {unique_dates[-1]}")
                
                # Calculate span
                first = datetime.strptime(unique_dates[0], '%Y-%m-%d')
                last = datetime.strptime(unique_dates[-1], '%Y-%m-%d')
                months = (last.year - first.year) * 12 + (last.month - first.month)
                print(f"  Span: {months} months")
                
                # Show sample
                print(f"\n  Sample dates:")
                for d in unique_dates[:10]:
                    print(f"    {d}")
                if len(unique_dates) > 10:
                    print(f"    ... and {len(unique_dates) - 10} more")
        else:
            print(f"Request failed: {response.status}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_graph_api())

