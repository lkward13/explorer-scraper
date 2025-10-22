#!/usr/bin/env python3
"""
Expand Explore deals by finding all similar-priced date combinations.

Takes a flight deal (origin, destination, dates, price) and uses Google Flights
price graph to find all date combinations within a price threshold.

Usage:
    python scripts/expand_dates.py --origin OKC --destination SEA --start 2025-12-04 --end 2025-12-10 --price 48
    python scripts/expand_dates.py --origin DFW --destination LHR --start 2025-12-10 --end 2025-12-18 --price 450 --threshold 0.15
"""

import re
import sys
import json
import asyncio
import argparse
from typing import Optional, List, Dict, Any
from pathlib import Path
from playwright.async_api import async_playwright


def build_flights_url(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    trip_type: str = "roundtrip"
) -> str:
    """
    Build Google Flights URL for specific route and dates using protobuf.
    
    Args:
        origin: Origin airport code (e.g., "OKC")
        destination: Destination airport code (e.g., "SEA")
        start_date: Departure date YYYY-MM-DD
        end_date: Return date YYYY-MM-DD
        trip_type: "roundtrip" or "oneway"
    
    Returns:
        Google Flights URL with pre-filled origin, destination, and dates
    """
    import base64
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import flights_pb2
    
    # Build protobuf message
    info = flights_pb2.Info()
    info.seat = flights_pb2.ECONOMY
    info.passengers.append(flights_pb2.ADULT)
    
    if trip_type == "roundtrip":
        info.trip = flights_pb2.ROUND_TRIP
        
        # Outbound flight: from origin on start_date
        d1 = info.data.add()
        d1.date = start_date
        d1.from_flight.airport = origin.upper()
        d1.to_flight.airport = destination.upper()
        
        # Return flight: from destination on end_date
        d2 = info.data.add()
        d2.date = end_date
        d2.from_flight.airport = destination.upper()
        d2.to_flight.airport = origin.upper()
    else:
        info.trip = flights_pb2.ONE_WAY
        
        # One-way flight
        d1 = info.data.add()
        d1.date = start_date
        d1.from_flight.airport = origin.upper()
        d1.to_flight.airport = destination.upper()
    
    # Serialize and encode
    raw = info.SerializeToString()
    tfs = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    
    # Build URL
    url = f"https://www.google.com/travel/flights?tfs={tfs}&hl=en&gl=us"
    return url


async def scrape_price_graph_data(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    verbose: bool = False,
    timeout: int = 30000
) -> Optional[List[Dict[str, Any]]]:
    """
    Scrape price data from Google Flights price graph using network interception.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        start_date: Reference departure date
        end_date: Reference return date
        verbose: Print debug info
        timeout: Timeout in milliseconds
        
    Returns:
        List of date/price combinations or None if failed
    """
    url = build_flights_url(origin, destination, start_date, end_date)
    
    if verbose:
        print(f"[info] Navigating to: {url}", file=sys.stderr)
    
    price_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Keep visible for debugging
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        
        # Set up network interception - capture ALL responses, especially after clicks
        async def handle_response(response):
            # Capture all responses from google.com
            if 'google.com' in response.url and response.status == 200:
                try:
                    # Try to get response body
                    body = await response.body()
                    body_text = body.decode('utf-8', errors='ignore')
                    
                    # Highlight GetCalendarGraph calls specifically
                    if 'GetCalendarGraph' in response.url:
                        if verbose:
                            print(f"[info] *** GetCalendarGraph: {response.url[:100]}... ({len(body)} bytes)", file=sys.stderr)
                    elif verbose:
                        print(f"[info] Intercepted: {response.url[:80]}... ({len(body)} bytes)", file=sys.stderr)
                    
                    # Store all responses for inspection
                    price_data.append({
                        'url': response.url,
                        'body': body_text,
                        'status': response.status,
                        'size': len(body)
                    })
                except Exception as e:
                    if verbose:
                        print(f"[warn] Failed to read response: {e}", file=sys.stderr)
        
        page.on('response', handle_response)
        
        try:
            # Navigate to flights page (dates already in URL via protobuf)
            await page.goto(url, wait_until="networkidle", timeout=timeout)
            await page.wait_for_timeout(5000)  # Let page fully load with results
            
            # Save screenshot for debugging
            if verbose:
                await page.screenshot(path="debug_flights_initial.png")
                print(f"[debug] Saved screenshot: debug_flights_initial.png", file=sys.stderr)
                print(f"[info] Page loaded with results, looking for 'Price graph' button...", file=sys.stderr)
            
            # Look for "Price graph" button/link and click it
            # This should be visible on the page since dates are already set
            price_graph_clicked = False
            price_graph_selectors = [
                'button:has-text("Price graph")',
                'a:has-text("Price graph")',
                '[role="tab"]:has-text("Price graph")',
                'text="Price graph"',
                '[aria-label*="Price graph"]',
            ]
            
            for selector in price_graph_selectors:
                try:
                    if verbose:
                        print(f"[debug] Trying selector: {selector}", file=sys.stderr)
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        if verbose:
                            print(f"[info] Found 'Price graph' with selector: {selector}", file=sys.stderr)
                        await element.click()
                        price_graph_clicked = True
                        if verbose:
                            print(f"[info] Clicked 'Price graph'", file=sys.stderr)
                        await page.wait_for_timeout(3000)  # Wait for graph data to load
                        break
                except Exception as e:
                    if verbose:
                        print(f"[debug] Selector '{selector}' failed: {e}", file=sys.stderr)
                    continue
            
            if not price_graph_clicked:
                if verbose:
                    print(f"[warn] Could not find/click 'Price graph' button", file=sys.stderr)
                    await page.screenshot(path="debug_flights_no_graph.png")
                    print(f"[debug] Saved screenshot: debug_flights_no_graph.png", file=sys.stderr)
            else:
                # Now paginate through future months (up to 12 months)
                if verbose:
                    print(f"[info] Paginating through price graph data...", file=sys.stderr)
                    print(f"[info] Waiting for price graph to fully load...", file=sys.stderr)
                
                # Wait longer for price graph to fully render
                await page.wait_for_timeout(3000)
                
                # Track how many GetCalendarGraph calls we've seen so far
                def count_graph_calls():
                    return sum(1 for r in price_data if 'GetCalendarGraph' in r.get('url',''))

                # Keep clicking until we can't click anymore (up to 12 months)
                for month_num in range(12):
                    if verbose:
                        print(f"[info] Loading month {month_num + 2}...", file=sys.stderr)
                    
                    # Find and click the "next month" button (right arrow on price graph)
                    # The button has class VfPpkd-LgbsSe - get the LAST one (right arrow)
                    next_button_selectors = [
                        # Target the specific button class and get the last one (right arrow)
                        'button.VfPpkd-LgbsSe.b9hyVd >> nth=-1',
                        'button.VfPpkd-LgbsSe.MQasIc >> nth=-1',
                        'button.VfPpkd-LgbsSe >> nth=-1',
                        # Within the dialog
                        'div[role="dialog"] button.VfPpkd-LgbsSe >> nth=-1',
                        # Fallback
                        'button:has(svg) >> nth=-1',
                    ]
                    
                    clicked_next = False
                    retry_count = 0
                    max_retries = 3
                    
                    while not clicked_next and retry_count < max_retries:
                        for selector in next_button_selectors:
                            try:
                                # Wait a bit before each attempt
                                if retry_count > 0:
                                    await page.wait_for_timeout(1000)
                                
                                next_btn = await page.wait_for_selector(selector, timeout=4000)
                                if next_btn:
                                    # Check if button is visible and enabled
                                    is_visible = await next_btn.is_visible()
                                    is_enabled = await next_btn.is_enabled()
                                    
                                    if is_visible and is_enabled:
                                        # Count current graph calls, then click and wait for a new one
                                        before = count_graph_calls()
                                        await next_btn.click()
                                        clicked_next = True
                                        if verbose:
                                            print(f"[info]   Clicked 'Next month' button (attempt {retry_count + 1})", file=sys.stderr)
                                        # Wait up to ~10s for a NEW GetCalendarGraph to arrive
                                        for _ in range(20):
                                            await page.wait_for_timeout(500)
                                            after = count_graph_calls()
                                            if after > before:
                                                if verbose:
                                                    print(f"[info]   Detected new GetCalendarGraph response", file=sys.stderr)
                                                break
                                        else:
                                            if verbose:
                                                print(f"[warn]   No new GetCalendarGraph detected within 10s after click", file=sys.stderr)
                                        break
                            except Exception as e:
                                if verbose and retry_count == 0:
                                    print(f"[debug]   Selector '{selector}' failed: {str(e)[:50]}", file=sys.stderr)
                                continue
                        
                        if not clicked_next:
                            retry_count += 1
                            if retry_count < max_retries:
                                if verbose:
                                    print(f"[debug]   Retry {retry_count}/{max_retries}...", file=sys.stderr)
                    
                    if not clicked_next:
                        if verbose:
                            print(f"[warn] Could not find 'Next month' button after {max_retries} attempts, stopping pagination", file=sys.stderr)
                            # Save screenshot for debugging
                            await page.screenshot(path=f"debug_no_next_button_month_{month_num + 2}.png")
                            print(f"[debug] Saved screenshot: debug_no_next_button_month_{month_num + 2}.png", file=sys.stderr)
                        break
            
            # Wait longer for any final network requests to complete
            if verbose:
                print(f"[info] Waiting for final network requests to complete...", file=sys.stderr)
            await page.wait_for_timeout(5000)  # Wait 5 seconds for stragglers
            
            if verbose:
                print(f"[info] Captured {len(price_data)} network responses", file=sys.stderr)
                # Save responses to files for inspection
                for i, resp in enumerate(price_data):
                    filename = f"debug_response_{i}.txt"
                    with open(filename, 'w') as f:
                        f.write(f"URL: {resp['url']}\n")
                        f.write(f"Size: {resp['size']} bytes\n")
                        f.write("="*80 + "\n")
                        f.write(resp['body'])
                    print(f"[debug] Saved response to: {filename}", file=sys.stderr)
            
        except Exception as e:
            if verbose:
                print(f"[error] Error during scraping: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
        finally:
            await browser.close()
    
    return price_data


def parse_price_data(responses: List[Dict[str, Any]], verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Parse intercepted network responses to extract date/price data.
    
    The Google Flights price graph response contains arrays like:
    ["2025-12-06","2025-12-13",[[null,149],"encoded_data"],1]
    Format: [outbound_date, inbound_date, [[null, price], ...], trip_length]
    
    Args:
        responses: List of intercepted network responses
        verbose: Print debug info
        
    Returns:
        List of dicts with 'start_date', 'end_date', 'price'
    """
    parsed_dates = []
    
    if verbose:
        print(f"[debug] Parsing {len(responses)} responses", file=sys.stderr)
    
    for i, resp in enumerate(responses):
        body = resp['body']
        url = resp['url']
        
        if verbose:
            print(f"[debug] Response {i}: {url[:80]}...", file=sys.stderr)
        
        # Look for the FlightsFrontendUi data endpoint (has the price graph data)
        if 'FlightsFrontendUi/data' not in url:
            if verbose:
                print(f"[debug]   -> Skipping (not FlightsFrontendUi/data)", file=sys.stderr)
            continue
        
        if verbose:
            print(f"[debug]   -> Parsing FlightsFrontendUi response", file=sys.stderr)
        
        # Parse the response - it's a JSON-like structure with escaped quotes/brackets
        # Pattern: [\"YYYY-MM-DD\",\"YYYY-MM-DD\",[[null,PRICE],...],...]
        # The response has escaped characters: \" and \[
        pattern = r'\[\\"(\d{4}-\d{2}-\d{2})\\",\\"(\d{4}-\d{2}-\d{2})\\",\[\[null,(\d+)\]'
        matches = re.findall(pattern, body)
        
        if verbose:
            # Also count total date strings to see if we're missing any
            all_dates = re.findall(r'(\d{4}-\d{2}-\d{2})', body)
            print(f"[debug] Found {len(matches)} date/price pairs in response (total dates in response: {len(all_dates)})", file=sys.stderr)
        
        for match in matches:
            start_date, end_date, price = match
            parsed_dates.append({
                'start_date': start_date,
                'end_date': end_date,
                'price': int(price)
            })
    
    if verbose:
        print(f"[info] Parsed {len(parsed_dates)} date/price combinations", file=sys.stderr)
    
    return parsed_dates


async def expand_dates(
    origin: str,
    destination: str,
    reference_start: str,
    reference_end: str,
    reference_price: int,
    threshold: float = 0.10,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Find all date combinations within price threshold of reference deal.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        reference_start: Reference departure date (YYYY-MM-DD)
        reference_end: Reference return date (YYYY-MM-DD)
        reference_price: Reference price in USD
        threshold: Price threshold as decimal (0.10 = ±10%)
        verbose: Print debug info
        
    Returns:
        Dict with reference deal and list of similar deals
    """
    if verbose:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Expanding dates for: {origin} → {destination}", file=sys.stderr)
        print(f"Reference: {reference_start} to {reference_end} @ ${reference_price}", file=sys.stderr)
        print(f"Threshold: ±{threshold*100:.0f}%", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
    
    # Calculate price range
    min_price = int(reference_price * (1 - threshold))
    max_price = int(reference_price * (1 + threshold))
    
    if verbose:
        print(f"[info] Looking for prices between ${min_price} and ${max_price}", file=sys.stderr)
    
    # Scrape price graph data
    responses = await scrape_price_graph_data(
        origin, destination, reference_start, reference_end, verbose=verbose
    )
    
    if not responses:
        if verbose:
            print(f"[warn] No network data captured", file=sys.stderr)
        return {
            'origin': origin,
            'destination': destination,
            'reference_price': reference_price,
            'reference_start': reference_start,
            'reference_end': reference_end,
            'price_range': {'min': min_price, 'max': max_price},
            'similar_deals': [],
            'raw_responses': []
        }
    
    # Parse the responses
    all_dates = parse_price_data(responses, verbose=verbose)
    
    # Filter by price threshold
    similar_deals = [
        d for d in all_dates 
        if min_price <= d.get('price', 0) <= max_price
    ]
    
    if verbose:
        print(f"\n[info] Found {len(similar_deals)} deals within price range", file=sys.stderr)
    
    return {
        'origin': origin,
        'destination': destination,
        'reference_price': reference_price,
        'reference_start': reference_start,
        'reference_end': reference_end,
        'price_range': {'min': min_price, 'max': max_price},
        'similar_deals': similar_deals,
        'raw_responses': [{'url': r['url'], 'size': len(r['body'])} for r in responses]
    }


def main():
    parser = argparse.ArgumentParser(
        description="Expand Explore deal by finding all similar-priced dates",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--origin", required=True, help="Origin airport code (e.g., OKC)")
    parser.add_argument("--destination", required=True, help="Destination airport code (e.g., SEA)")
    parser.add_argument("--start", required=True, help="Reference start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Reference end date (YYYY-MM-DD)")
    parser.add_argument("--price", type=int, required=True, help="Reference price in USD")
    parser.add_argument("--threshold", type=float, default=0.10, help="Price threshold (default: 0.10 = ±10%%)")
    parser.add_argument("--out", help="Output JSON file (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Run the expansion
    result = asyncio.run(
        expand_dates(
            origin=args.origin,
            destination=args.destination,
            reference_start=args.start,
            reference_end=args.end,
            reference_price=args.price,
            threshold=args.threshold,
            verbose=args.verbose
        )
    )
    
    # Output results
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Saved to {args.out}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

