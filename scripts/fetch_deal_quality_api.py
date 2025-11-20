#!/usr/bin/env python3
"""
Fetch deal quality ("$X cheaper than usual") via GetExploreDestinationFlightDetails API.
"""
import asyncio
import json
import urllib.parse
import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, BrowserContext

async def fetch_deal_quality(
    context: BrowserContext,
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    session_id: str = "1"
) -> Optional[Dict]:
    """
    Fetch deal quality for a specific destination.
    
    Returns:
        dict with 'deal_quality' and 'deal_quality_amount' or None
    """
    
    # Build the request body
    # The session token format from the card click: "CjRIRjdyN3RvTGNUZTBBQmFEeFFCRy0tLS0tLS0tLS1va2t2MkFBQUFBR2tlaDBBTGRGZXdBEh1ERlctTElTOjIwMjUtMTItMDFfMjAyNS0xMi0wORoLCMXwAhACGgNVU0Q4KXDF8AI="
    # This is base64 encoded, but we can construct a simpler request
    
    # The inner structure appears to be: [null, "session_token", origin-dest:dates, currency info]
    # Let's try a simplified version
    route_string = f"{origin}-{destination}:{start_date}_{end_date}"
    
    inner_structure = [
        [None, route_string],
        [None, None, None, "USD"]
    ]
    
    f_req_value = json.dumps([None, json.dumps(inner_structure, separators=(',', ':'))], separators=(',', ':'))
    post_body = f"f.req={urllib.parse.quote(f_req_value)}&"
    
    url = f"https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetExploreDestinationFlightDetails?f.sid={session_id}&bl=boq_travel-frontend-flights-ui_20251118.02_p0&hl=en&gl=us&soc-app=162&soc-platform=1&soc-device=1&_reqid=1&rt=c"
    
    headers = {
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'x-same-domain': '1',
        'referer': 'https://www.google.com/travel/explore'
    }
    
    try:
        response = await context.request.post(url, data=post_body, headers=headers, timeout=10000)
        
        if not response.ok:
            return None
        
        text = await response.text()
        if text.startswith(")]}'"):
            text = text[4:]
        
        # Look for "cheaper than usual" patterns
        # Patterns: "$267 cheaper than usual", "Prices are currently low — $267 cheaper"
        patterns = [
            r'\$(\d+)\s+cheaper\s+than\s+usual',
            r'\$(\d+)\s+cheaper',
            r'(\d+)%\s+cheaper\s+than\s+usual',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                
                # Check if it's a percentage or dollar amount
                if '%' in pattern:
                    return {
                        'deal_quality': f"{amount_str}% cheaper than usual",
                        'deal_quality_amount': None  # Can't convert % to $
                    }
                else:
                    return {
                        'deal_quality': f"${amount_str} cheaper than usual",
                        'deal_quality_amount': int(amount_str)
                    }
        
        # No deal quality found
        return None
        
    except Exception as e:
        return None


async def fetch_deal_quality_batch(
    cards: List[Dict],
    verbose: bool = False
) -> List[Dict]:
    """
    Fetch deal quality for multiple cards in parallel.
    
    Args:
        cards: List of card dicts with origin, destination, start_date, end_date
        verbose: Print progress
    
    Returns:
        Updated cards with deal_quality and deal_quality_amount fields
    """
    if not cards:
        return cards
    
    if verbose:
        print(f"[deal_quality] Fetching for {len(cards)} destinations...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Fetch all in parallel
        tasks = []
        for card in cards:
            origin = card.get('origin', 'DFW')
            destination = card.get('airport_code') or card.get('destination', 'Unknown')
            start_date = card.get('start_date')
            end_date = card.get('end_date')
            
            if start_date and end_date:
                tasks.append(fetch_deal_quality(context, origin, destination, start_date, end_date))
            else:
                tasks.append(asyncio.sleep(0))  # Placeholder
        
        results = await asyncio.gather(*tasks)
        
        # Update cards with results
        for i, result in enumerate(results):
            if result:
                cards[i]['deal_quality'] = result.get('deal_quality')
                cards[i]['deal_quality_amount'] = result.get('deal_quality_amount')
                
                if verbose:
                    dest = cards[i].get('destination', 'Unknown')
                    print(f"  ✓ {dest}: {result.get('deal_quality')}")
        
        await context.close()
        await browser.close()
    
    if verbose:
        found_count = sum(1 for c in cards if c.get('deal_quality'))
        print(f"[deal_quality] Found quality data for {found_count}/{len(cards)} destinations")
    
    return cards


if __name__ == '__main__':
    # Test
    async def test():
        test_cards = [
            {'origin': 'DFW', 'destination': 'LIS', 'start_date': '2025-12-01', 'end_date': '2025-12-09', 'min_price': 472},
            {'origin': 'DFW', 'destination': 'MXP', 'start_date': '2025-12-01', 'end_date': '2025-12-09', 'min_price': 486},
            {'origin': 'DFW', 'destination': 'ATH', 'start_date': '2026-01-11', 'end_date': '2026-01-19', 'min_price': 496},
        ]
        
        updated = await fetch_deal_quality_batch(test_cards, verbose=True)
        
        print("\nResults:")
        for card in updated:
            print(f"  {card['destination']}: {card.get('deal_quality', 'No data')}")
    
    asyncio.run(test())

