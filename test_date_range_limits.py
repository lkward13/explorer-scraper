#!/usr/bin/env python3
"""Test GetCalendarGraph API date range limits."""
import asyncio
from playwright.async_api import async_playwright
import json
import urllib.parse
from datetime import datetime, timedelta

async def test_range(months):
    """Test a specific month range."""
    origin, dest = 'ATL', 'SJU'
    start_date = '2026-01-11'
    
    # Calculate end date
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = start + timedelta(days=months*30)
    end_date = end.strftime('%Y-%m-%d')
    
    # Correctly formatted inner structure
    inner = [
        None,
        [
            None, None, 1, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None,
            [
                [
                    [[[origin, 0]]],
                    [[[dest, 0]]],
                    None, 0, None, None, start_date,
                    None, None, None, None, None, None, None, 3
                ],
                [
                    [[[dest, 0]]],
                    [[[origin, 0]]],
                    None, 0, None, None, start_date,
                    None, None, None, None, None, None, None, 3
                ]
            ],
            None, None, None, 1
        ],
        [start_date, end_date],
        None,
        [9, 9]
    ]
    
    outer = [None, json.dumps(inner, separators=(',', ':'))]
    post_body = f'f.req={urllib.parse.quote(json.dumps(outer, separators=(",", ":")))}&'
    
    url = 'https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGraph?f.sid=1&bl=boq_travel-frontend-flights-ui_20251118.02_p0&hl=en&gl=us&soc-app=162&soc-platform=1&soc-device=1&_reqid=1&rt=c'
    headers = {
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'x-same-domain': '1',
        'referer': 'https://www.google.com/travel/flights'
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        response = await context.request.post(url, data=post_body, headers=headers, timeout=30000)
        text = await response.text()
        
        is_error = 'ErrorResponse' in text
        size = len(text)
        
        print(f'{months:2d} months ({start_date} to {end_date}): {"ERROR" if is_error else "OK":5s} - {size:6d} bytes')
        
        await browser.close()
        return not is_error

async def main():
    print('Testing GetCalendarGraph date range limits:')
    print('='*70)
    
    for months in [3, 6, 9, 12, 15, 18]:
        success = await test_range(months)
        if not success and months > 6:
            print(f'\n✗ Limit reached at {months} months')
            print(f'✓ Maximum supported: {months-3} months')
            # Try exactly 7, 8, 9 to pinpoint
            if months == 9:
                print('\nPinpointing limit between 6 and 9 months...')
                await test_range(7)
                await test_range(8)
            break
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
