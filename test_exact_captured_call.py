#!/usr/bin/env python3
"""Test the exact captured API call to see how much data it returns."""
import asyncio
import json
import re
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
        # Use the EXACT captured request
        url = 'https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGraph?f.sid=1&bl=boq_travel-frontend-flights-ui_20251118.02_p0&hl=en&gl=us&soc-app=162&soc-platform=1&soc-device=1&_reqid=1&rt=c'
        
        headers = {
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-same-domain': '1',
            'referer': 'https://www.google.com/travel/flights'
        }
        
        post_data = 'f.req=%5Bnull%2C%22%5Bnull%2C%5Bnull%2Cnull%2C1%2Cnull%2C%5B%5D%2C1%2C%5B1%2C0%2C0%2C0%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B%5B%5B%5B%5C%22ATL%5C%22%2C0%5D%5D%5D%2C%5B%5B%5B%5C%22SJU%5C%22%2C0%5D%5D%5D%2Cnull%2C0%2Cnull%2Cnull%2C%5C%222026-01-11%5C%22%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C3%5D%2C%5B%5B%5B%5B%5C%22SJU%5C%22%2C0%5D%5D%5D%2C%5B%5B%5B%5C%22ATL%5C%22%2C0%5D%5D%5D%2Cnull%2C0%2Cnull%2Cnull%2C%5C%222026-01-20%5C%22%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C3%5D%5D%2C%5Bnull%2Cnull%2Cnull%2C1%5D%2C%5B%5C%222026-01-04%5C%22%2C%5C%222026-03-04%5C%22%5D%2Cnull%2C%5B9%2C9%5D%5D%22%5D&'
        
        response = await context.request.post(url, data=post_data, headers=headers)
        text = await response.text()
        
        prefix = ")]}\'"
        if text.startswith(prefix):
            text = text[len(prefix):]
        
        # Find all dates
        pattern = r'["\\\\"]+(\d{4}-\d{2}-\d{2})["\\\\"]+' 
        dates = re.findall(pattern, text)
        unique_dates = sorted(set(dates))
        
        print(f'Response length: {len(text)} chars')
        print(f'Unique dates found: {len(unique_dates)}')
        if unique_dates:
            print(f'Date range: {unique_dates[0]} to {unique_dates[-1]}')
            
            # Count by month
            from collections import Counter
            months = Counter([d[:7] for d in unique_dates])
            print(f'\nDates by month:')
            for month in sorted(months.keys()):
                print(f'  {month}: {months[month]} dates')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test())

