#!/usr/bin/env python3
"""Test requesting 9 months like the screenshot shows."""
import asyncio
import json
import urllib.parse
import re
from playwright.async_api import async_playwright

async def test_wide_range():
    origin = 'ATL'
    destination = 'SJU'
    outbound_date = '2026-01-11'
    return_date = '2026-01-20'
    
    # Try requesting 9 months like the screenshot shows
    start_range = '2026-01-04'
    end_range = '2026-10-04'  # 9 months
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
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
        post_body = f'f.req={urllib.parse.quote(outer_json)}&'
        
        url = 'https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGraph?f.sid=1&bl=boq_travel-frontend-flights-ui_20251118.02_p0&hl=en&gl=us&soc-app=162&soc-platform=1&soc-device=1&_reqid=1&rt=c'
        
        headers = {
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-same-domain': '1',
            'referer': 'https://www.google.com/travel/flights'
        }
        
        response = await context.request.post(url, data=post_body, headers=headers)
        text = await response.text()
        
        prefix = ")]}\'"
        if text.startswith(prefix):
            text = text[len(prefix):]
        
        print(f'Status: {response.status}')
        print(f'Response length: {len(text)} chars')
        
        # Check if it's an error
        if 'ErrorResponse' in text:
            print('✗ Error response - Google rejected the 9-month range')
            print(f'Response: {text[:500]}')
        else:
            pattern = r'["\\\\"]+(\d{4}-\d{2}-\d{2})["\\\\"]+' 
            dates = re.findall(pattern, text)
            unique_dates = sorted(set(dates))
            print(f'✓ Unique dates: {len(unique_dates)}')
            if unique_dates:
                print(f'  Range: {unique_dates[0]} to {unique_dates[-1]}')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_wide_range())

