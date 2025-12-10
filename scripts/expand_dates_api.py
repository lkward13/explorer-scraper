#!/usr/bin/env python3
"""
Advanced API-based date expansion using GetCalendarGraph.
Uses the Price Graph API to fetch ~12 months of data in just 2 requests.
"""
import asyncio
import json
import urllib.parse
import re
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, BrowserContext

async def fetch_calendar_graph(
    context: BrowserContext,
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    start_range: str,
    end_range: str
) -> List[Dict]:
    """
    Fetch price graph data for a specific date range.
    """
    # Build request body
    inner_structure = [
        None,
        [
            None, None, 1, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None,
            [
                # Outbound
                [
                    [[[origin, 0]]],
                    [[[destination, 0]]],
                    None, 0, None, None, outbound_date,
                    None, None, None, None, None, None, None, 3
                ],
                # Return
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
        if not response.ok:
            return None  # Signal API failure
        
        text = await response.text()
        if text.startswith(")]}'"):
            text = text[4:]
        
        # Parse response for dates and prices
        # Format: ["YYYY-MM-DD","YYYY-MM-DD",[[null,PRICE]
        # Note: Dates might be escaped in the JSON string
        deals = []
        
        # Use regex to find date pairs and prices
        # Matches: ["2026-01-04","2026-01-13",[[null,189]
        # Handles potentially escaped quotes
        pattern = r'\[\\?"(\d{4}-\d{2}-\d{2})\\?",\\?"(\d{4}-\d{2}-\d{2})\\?",\[\[null,(\d+)\]'
        matches = re.findall(pattern, text)
        
        for out_d, ret_d, price in matches:
            deals.append({
                'outbound_date': out_d,
                'return_date': ret_d,
                'price': int(price)
            })
            
        return deals  # Return empty list if no matches (legitimate 0)
        
    except Exception:
        return None  # Signal API failure

async def expand_deal_via_api(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    original_price: int,
    price_threshold: float = 1.15,
    context: Optional[BrowserContext] = None,
    verbose: bool = False
) -> List[Dict]:
    """
    Expand a deal using Google's Price Graph API (4 calls for ~11 months from TODAY).
    """
    if verbose:
        print(f"[API] Expanding {origin}→{destination} (Graph API, 4 calls for 11 months from today)")
    
    should_close = False
    if context is None:
        p = await async_playwright().start()
        browser = await p.chromium.launch()
        context = await browser.new_context()
        should_close = True
    
    try:
        # Start from TODAY (not from the deal's date) and go 11 months out
        # This ensures we get all available flights in the booking window
        today = datetime.now()
        
        # Range 1: 0-3 months from today
        range1_start = today.strftime('%Y-%m-%d')
        range1_end = (today + timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Range 2: 3-6 months from today
        range2_start = (today + timedelta(days=91)).strftime('%Y-%m-%d')
        range2_end = (today + timedelta(days=180)).strftime('%Y-%m-%d')
        
        # Range 3: 6-9 months from today
        range3_start = (today + timedelta(days=181)).strftime('%Y-%m-%d')
        range3_end = (today + timedelta(days=270)).strftime('%Y-%m-%d')
        
        # Range 4: 9-11 months from today
        range4_start = (today + timedelta(days=271)).strftime('%Y-%m-%d')
        range4_end = (today + timedelta(days=330)).strftime('%Y-%m-%d')  # ~11 months
        
        # Make 4 parallel API calls
        # Add random jitter (0.5-2s) between API calls to avoid rate limiting
        async def fetch_with_jitter(delay_ms, *args):
            await asyncio.sleep(delay_ms / 1000.0)
            return await fetch_calendar_graph(*args)
        
        # Stagger the 4 API calls with random delays
        jitters = [0, random.uniform(500, 2000), random.uniform(500, 2000), random.uniform(500, 2000)]
        
        task1 = fetch_with_jitter(jitters[0], context, origin, destination, outbound_date, return_date, range1_start, range1_end)
        task2 = fetch_with_jitter(jitters[1], context, origin, destination, outbound_date, return_date, range2_start, range2_end)
        task3 = fetch_with_jitter(jitters[2], context, origin, destination, outbound_date, return_date, range3_start, range3_end)
        task4 = fetch_with_jitter(jitters[3], context, origin, destination, outbound_date, return_date, range4_start, range4_end)
        
        results = await asyncio.gather(task1, task2, task3, task4)
        
        # Check if any API calls failed (returned None)
        if None in results:
            if verbose:
                print(f"[API] ✗ API call failed (blocked or error)")
            return []  # Return empty list to signal failure
        
        # Combine all deals
        all_deals = results[0] + results[1] + results[2] + results[3]
        
        # Deduplicate
        unique_deals = {}
        for deal in all_deals:
            key = f"{deal['outbound_date']}_{deal['return_date']}"
            unique_deals[key] = deal
        
        deals = list(unique_deals.values())
        
        if verbose:
            print(f"[API] Found {len(deals)} total date combinations")
        
        # Filter by price
        max_price = original_price * price_threshold
        good_deals = [d for d in deals if d['price'] <= max_price]
        
        if verbose:
            if len(deals) > 0 and len(good_deals) == 0:
                print(f"[API] ✓ API returned {len(deals)} dates, but 0 within ${max_price:.0f} (all too expensive)")
            else:
                print(f"[API] ✓ Found {len(good_deals)} deals within ${max_price:.0f}")
            
        return good_deals
        
    finally:
        if should_close:
            await context.close()
            await browser.close()
            await p.stop()

if __name__ == '__main__':
    # Test run
    async def test():
        deals = await expand_deal_via_api(
            'ATL', 'SJU', '2026-01-11', '2026-01-20', 195, verbose=True
        )
        if deals:
            print(f"\nTop 5 deals:")
            for d in sorted(deals, key=lambda x: x['price'])[:5]:
                print(f"  {d['outbound_date']} to {d['return_date']}: ${d['price']}")
            
            # Show date span
            dates = [d['outbound_date'] for d in deals]
            print(f"\nDate span: {min(dates)} to {max(dates)}")
            
    asyncio.run(test())
