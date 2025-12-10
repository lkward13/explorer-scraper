"""
Fast price insight checker using fast-flights library + HTML parsing.
"""
import sys
import os
import re
from pathlib import Path

# Add flights-main to path
flights_main_path = Path(__file__).parent.parent / "flights-main"
sys.path.insert(0, str(flights_main_path))

# Change to flights-main directory for primp to work properly
original_dir = os.getcwd()
os.chdir(str(flights_main_path))

from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter
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
    
    # Method 1: Look for "Prices are currently X" text
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


def check_price_insight(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    fetch_mode: str = "common",
    verbose: bool = False
) -> dict:
    """
    Check price insight for a specific flight using fast-flights + HTML parsing.
    
    Args:
        origin: Origin airport code (e.g., 'PHX')
        destination: Destination airport code (e.g., 'FCO')
        outbound_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD)
        fetch_mode: 'common', 'fallback', 'local', etc.
        verbose: Print details
    
    Returns:
        {
            'current_price': 'low' | 'typical' | 'high' | None,
            'price': int,  # cheapest price found
            'discount_amount': int or None,  # e.g., 378
            'discount_text': str or None,    # e.g., "$378 cheaper than usual"
            'typical_range_low': int or None,
            'typical_range_high': int or None,
            'discount_percent': float or None,  # calculated percentage
            'success': bool
        }
    """
    try:
        # Create filter
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
        
        # Build URL to get HTML
        tfs_b64 = filter_obj.as_b64().decode('utf-8')
        url = f"https://www.google.com/travel/flights?tfs={tfs_b64}&hl=en"
        
        # Fetch HTML using primp
        from primp import Client
        client = Client(impersonate="chrome_126", verify=False)
        response = client.get(url)
        html = response.text
        
        # Parse price insights from HTML
        insight_data = parse_price_insight_from_html(html, verbose=verbose)
        
        # Also get flights from fast-flights for current price
        result = get_flights_from_filter(filter_obj, mode=fetch_mode)
        
        # Extract price and status
        current_price = getattr(result, 'current_price', None)
        flights = getattr(result, 'flights', [])
        
        price = None
        if flights:
            # Get cheapest flight (remove $ and commas)
            prices = []
            for f in flights:
                if hasattr(f, 'price') and f.price:
                    price_str = str(f.price).replace('$', '').replace(',', '')
                    try:
                        prices.append(int(price_str))
                    except ValueError:
                        pass
            if prices:
                price = min(prices)
        
        # Calculate discount percentage if we have both prices
        discount_percent = None
        if insight_data.get('discount_amount') and price:
            usual_price = price + insight_data['discount_amount']
            discount_percent = round((insight_data['discount_amount'] / usual_price) * 100, 1)
        
        if verbose:
            status = insight_data.get('status') or current_price
            status_emoji = "🟢" if status == "low" else "🟡" if status == "typical" else "🔴" if status == "high" else "⚪"
            if insight_data.get('discount_amount'):
                print(f"  {status_emoji} {origin}→{destination}: ${price} (${insight_data['discount_amount']} cheaper, {discount_percent}% off)")
            else:
                print(f"  {status_emoji} {origin}→{destination}: {status or 'N/A'}, ${price or 'N/A'}")
        
        return {
            'current_price': insight_data.get('status') or current_price,
            'price': price,
            'discount_amount': insight_data.get('discount_amount'),
            'discount_text': insight_data.get('discount_text'),
            'typical_range_low': insight_data.get('typical_range_low'),
            'typical_range_high': insight_data.get('typical_range_high'),
            'discount_percent': discount_percent,
            'success': (insight_data.get('status') or current_price) is not None
        }
        
    except Exception as e:
        if verbose:
            print(f"  ✗ {origin}→{destination}: Error - {e}")
        return {
            'current_price': None,
            'price': None,
            'discount_amount': None,
            'discount_text': None,
            'typical_range_low': None,
            'typical_range_high': None,
            'discount_percent': None,
            'success': False,
            'error': str(e)
        }


def check_deals_batch(deals: list, fetch_mode: str = "common", verbose: bool = False) -> list:
    """
    Check price insights for a batch of deals (synchronous).
    
    Args:
        deals: List of deal dicts with origin, destination, start_date, end_date
        fetch_mode: fast-flights fetch mode
        verbose: Print progress
    
    Returns:
        List of deals with price_insight added
    """
    enhanced_deals = []
    
    for idx, deal in enumerate(deals):
        if verbose:
            print(f"[{idx+1}/{len(deals)}] Checking {deal['origin']}→{deal.get('destination', deal.get('airport_code', '???'))}")
        
        # Determine destination airport code
        dest_code = deal.get('airport_code') or deal.get('destination')
        
        if not dest_code or len(dest_code) != 3:
            if verbose:
                print(f"  ⚠ Skipping: No valid destination code")
            enhanced_deals.append(deal)
            continue
        
        insight = check_price_insight(
            origin=deal['origin'],
            destination=dest_code,
            outbound_date=deal.get('start_date'),
            return_date=deal.get('end_date'),
            fetch_mode=fetch_mode,
            verbose=verbose
        )
        
        enhanced_deal = {**deal, **insight}
        enhanced_deals.append(enhanced_deal)
    
    return enhanced_deals


if __name__ == "__main__":
    # Test
    print("Testing fast-flights price insight checker...")
    print("=" * 80)
    
    # Test with a route we know from earlier (Lisbon was 76% off = should be "low")
    test_deal = {
        'origin': 'PHX',
        'destination': 'Lisbon',
        'airport_code': 'LIS',
        'start_date': '2026-03-01',  # Approximate date from explore
        'end_date': '2026-03-08',
        'min_price': 495
    }
    
    result = check_price_insight(
        origin=test_deal['origin'],
        destination=test_deal['airport_code'],
        outbound_date=test_deal['start_date'],
        return_date=test_deal['end_date'],
        fetch_mode="common",  # Use common mode
        verbose=True
    )
    
    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    print(f"  Status: {result['current_price']}")
    print(f"  Current price: ${result['price']}")
    if result.get('discount_amount'):
        print(f"  Discount: ${result['discount_amount']} cheaper than usual ({result['discount_percent']}% off)")
    if result.get('typical_range_low') and result.get('typical_range_high'):
        print(f"  Typical range: ${result['typical_range_low']}-${result['typical_range_high']}")
    print(f"  Success: {result['success']}")
    
    # Restore original directory
    os.chdir(original_dir)

