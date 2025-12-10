"""
Price insight checker using Playwright for reliable HTML loading.
"""
import asyncio
import re
import time
from typing import Optional
from selectolax.lexbor import LexborHTMLParser


def parse_price_insight_from_html(html: str, verbose: bool = False) -> dict:
    """
    Parse price insight data from Google Flights HTML.
    
    Returns:
        {
            'status': 'low' | 'typical' | 'high' | None,
            'discount_amount': int or None,  # e.g., 378 from "$378 cheaper"
            'discount_text': str or None,    # e.g., "$378 cheaper than usual"
            'typical_range_low': int or None,  # e.g., 670
            'typical_range_high': int or None, # e.g., 2000
        }
    """
    parser = LexborHTMLParser(html)
    result = {
        'status': None,
        'discount_amount': None,
        'discount_text': None,
        'typical_range_low': None,
        'typical_range_high': None,
    }
    
    # Get all text
    text = parser.body.text()
    
    # Find status (low/typical/high)
    status_match = re.search(r'Prices are currently\s+(low|typical|high)', text, re.IGNORECASE)
    if status_match:
        result['status'] = status_match.group(1).lower()
    
    # Find discount amount ("$378 cheaper than usual")
    discount_patterns = [
        r'\$(\d+)\s+cheaper\s+than\s+usual',
        r'\$(\d+)\s+lower\s+than\s+usual',
        r'—\s*\$(\d+)\s+cheaper',
    ]
    for pattern in discount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['discount_amount'] = int(match.group(1))
            # Extract the full text around it
            start = max(0, match.start() - 10)
            end = min(len(text), match.end() + 20)
            result['discount_text'] = text[start:end].strip()
            break
    
    # Find typical price range ("usually cost between $670–2,000" or "$670-$2,000")
    range_patterns = [
        r'usually cost between \$(\d+)[–-]\$?(\d+)',
        r'usually cost between \$(\d+)[–-](\d+)',
        r'\$(\d+)[–-]\$(\d+)',
    ]
    for pattern in range_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['typical_range_low'] = int(match.group(1).replace(',', ''))
            result['typical_range_high'] = int(match.group(2).replace(',', ''))
            break
    
    if verbose and result['status']:
        print(f"    Status: {result['status']}")
        if result['discount_amount']:
            print(f"    Discount: ${result['discount_amount']}")
        if result['typical_range_low'] and result['typical_range_high']:
            print(f"    Typical range: ${result['typical_range_low']}-${result['typical_range_high']}")
    
    return result


async def check_price_insight_playwright(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    verbose: bool = False,
    timeout: int = 15000
) -> dict:
    """
    Check price insight using Playwright for reliable JavaScript rendering.
    
    Args:
        origin: Origin airport code (e.g., 'PHX')
        destination: Destination airport code (e.g., 'FCO')
        outbound_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD)
        verbose: Print details
        timeout: Timeout in milliseconds
    
    Returns:
        {
            'current_price': 'low' | 'typical' | 'high' | None,
            'price': int,  # cheapest price found
            'discount_amount': int or None,
            'discount_text': str or None,
            'typical_range_low': int or None,
            'typical_range_high': int or None,
            'discount_percent': float or None,
            'success': bool,
            'load_time': float  # seconds
        }
    """
    from playwright.async_api import async_playwright
    import sys
    from pathlib import Path
    
    # Add flights-main to path for TFS generation
    sys.path.insert(0, str(Path(__file__).parent.parent / "flights-main"))
    from fast_flights import FlightData, Passengers, create_filter
    
    start_time = time.time()
    
    try:
        # Create filter to build URL
        filter_obj = create_filter(
            flight_data=[
                FlightData(
                    date=outbound_date,
                    from_airport=origin,
                    to_airport=destination
                ),
                FlightData(
                    date=return_date,
                    from_airport=destination,
                    to_airport=origin
                ),
            ],
            trip="round-trip",
            seat="economy",
            passengers=Passengers(
                adults=1,
                children=0,
                infants_in_seat=0,
                infants_on_lap=0
            )
        )
        
        # Build URL
        tfs_b64 = filter_obj.as_b64().decode('utf-8')
        url = f"https://www.google.com/travel/flights?tfs={tfs_b64}&hl=en"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Load page
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            
            # Wait for price insights to load (or timeout gracefully)
            try:
                await page.wait_for_selector('text=/Prices are currently/i', timeout=5000)
            except:
                # Price insights might not be available for this route
                pass
            
            # Get HTML
            html = await page.content()
            
            # Parse price insights
            insight_data = parse_price_insight_from_html(html, verbose=verbose)
            
            # Extract cheapest price from page
            price = None
            try:
                # Look for price elements
                price_elements = await page.query_selector_all('[role="text"]')
                prices = []
                for elem in price_elements:
                    text = await elem.text_content()
                    if text and '$' in text:
                        price_match = re.search(r'\$(\d+)', text)
                        if price_match:
                            prices.append(int(price_match.group(1)))
                
                if prices:
                    price = min(prices)
            except:
                pass
            
            await browser.close()
        
        load_time = time.time() - start_time
        
        # Calculate discount percentage
        discount_percent = None
        if insight_data.get('discount_amount') and price:
            usual_price = price + insight_data['discount_amount']
            discount_percent = round((insight_data['discount_amount'] / usual_price) * 100, 1)
        
        if verbose:
            status = insight_data.get('status')
            status_emoji = "🟢" if status == "low" else "🟡" if status == "typical" else "🔴" if status == "high" else "⚪"
            if insight_data.get('discount_amount'):
                print(f"  {status_emoji} {origin}→{destination}: ${price} (${insight_data['discount_amount']} cheaper, {discount_percent}% off) [{load_time:.1f}s]")
            else:
                print(f"  {status_emoji} {origin}→{destination}: {status or 'N/A'}, ${price or 'N/A'} [{load_time:.1f}s]")
        
        return {
            'current_price': insight_data.get('status'),
            'price': price,
            'discount_amount': insight_data.get('discount_amount'),
            'discount_text': insight_data.get('discount_text'),
            'typical_range_low': insight_data.get('typical_range_low'),
            'typical_range_high': insight_data.get('typical_range_high'),
            'discount_percent': discount_percent,
            'success': insight_data.get('status') is not None,
            'load_time': load_time
        }
        
    except Exception as e:
        load_time = time.time() - start_time
        if verbose:
            print(f"  ✗ {origin}→{destination}: Error - {e} [{load_time:.1f}s]")
        return {
            'current_price': None,
            'price': None,
            'discount_amount': None,
            'discount_text': None,
            'typical_range_low': None,
            'typical_range_high': None,
            'discount_percent': None,
            'success': False,
            'load_time': load_time,
            'error': str(e)
        }


async def main():
    print("=" * 80)
    print("TESTING PLAYWRIGHT PRICE INSIGHT CHECKER")
    print("=" * 80)
    print()
    
    # Test multiple routes to benchmark speed and reliability
    test_routes = [
        ("PHX", "LIS", "2026-03-01", "2026-03-08", "Lisbon (should be low)"),
        ("PHX", "FCO", "2026-03-15", "2026-03-22", "Rome (should be typical)"),
        ("PHX", "ATH", "2026-03-10", "2026-03-17", "Athens (should be low)"),
        ("LAX", "JFK", "2025-12-20", "2025-12-27", "LAX-JFK (holiday, should be high)"),
    ]
    
    results = []
    total_start = time.time()
    
    for origin, dest, out_date, ret_date, description in test_routes:
        print(f"\nTesting: {description}")
        print("-" * 80)
        result = await check_price_insight_playwright(
            origin, dest, out_date, ret_date, verbose=True
        )
        results.append(result)
    
    total_time = time.time() - total_start
    
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print(f"Total routes tested: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}/{len(results)}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per route: {total_time/len(results):.1f}s")
    print(f"Success rate: {sum(1 for r in results if r['success'])/len(results)*100:.0f}%")
    
    # Show discount data found
    with_discounts = [r for r in results if r.get('discount_amount')]
    print(f"\nRoutes with discount data: {len(with_discounts)}/{len(results)}")
    for i, r in enumerate(with_discounts, 1):
        print(f"  {i}. ${r['discount_amount']} cheaper ({r['discount_percent']}% off)")
    
    print("\n" + "=" * 80)
    print("SCALABILITY ASSESSMENT")
    print("=" * 80)
    avg_time = total_time / len(results)
    print(f"At {avg_time:.1f}s per route:")
    print(f"  - 10 routes = {avg_time * 10:.0f}s (~{avg_time * 10 / 60:.1f} min)")
    print(f"  - 50 routes = {avg_time * 50:.0f}s (~{avg_time * 50 / 60:.1f} min)")
    print(f"  - 100 routes = {avg_time * 100:.0f}s (~{avg_time * 100 / 60:.1f} min)")
    
    print("\nWith 5 parallel browsers:")
    print(f"  - 50 routes = ~{avg_time * 50 / 5 / 60:.1f} min")
    print(f"  - 100 routes = ~{avg_time * 100 / 5 / 60:.1f} min")


if __name__ == "__main__":
    asyncio.run(main())

