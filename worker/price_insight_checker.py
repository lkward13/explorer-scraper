"""
Price insight checker for filtering deals by price status.
Uses fast-flights library to get "low" / "typical" / "high" status.
"""
import asyncio
import time
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path


async def check_price_status_fast(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str
) -> dict:
    """
    Check price status using fast-flights (HTTP only, no browser).
    
    Args:
        origin: Origin airport code (e.g., 'PHX')
        destination: Destination airport code (e.g., 'FCO')
        start_date: Departure date (YYYY-MM-DD)
        end_date: Return date (YYYY-MM-DD)
    
    Returns:
        {
            'status': 'low' | 'typical' | 'high' | None,
            'success': bool,
            'load_time': float  # seconds
        }
    """
    start_time = time.time()
    
    try:
        # Import fast-flights locally to avoid protobuf conflicts
        flights_main_path = str(Path(__file__).parent.parent / "flights-main")
        if flights_main_path not in sys.path:
            sys.path.insert(0, flights_main_path)
        
        from fast_flights import FlightData, Passengers, create_filter, get_flights
        
        # Create flight filter
        filter_obj = create_filter(
            flight_data=[
                FlightData(
                    date=start_date,
                    from_airport=origin,
                    to_airport=destination
                ),
                FlightData(
                    date=end_date,
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
        
        # Get flights (this makes the HTTP request)
        result = get_flights(filter_obj)
        
        load_time = time.time() - start_time
        
        # Check if we got any flights
        if not result or len(result) == 0:
            return {
                'status': None,
                'success': False,
                'load_time': load_time,
                'error': 'No flights found'
            }
        
        # Get the cheapest flight's price status
        cheapest = result[0]  # Results are sorted by price
        status = cheapest.current_price if hasattr(cheapest, 'current_price') else None
        
        return {
            'status': status,
            'success': status is not None,
            'load_time': load_time
        }
        
    except Exception as e:
        load_time = time.time() - start_time
        return {
            'status': None,
            'success': False,
            'load_time': load_time,
            'error': str(e)
        }


async def check_price_insights_parallel(
    deals: List[Dict[str, Any]],
    max_parallel: int = 10,
    status_filter: str = "low",
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Check price status for multiple deals in parallel and filter by status.
    Uses fast-flights (HTTP only) to avoid bot detection.
    
    Args:
        deals: List of deal dicts with origin, destination, start_date, end_date, price
        max_parallel: Maximum number of parallel requests (default 10, fast-flights is HTTP only)
        status_filter: Status to filter for: "low" (default), "typical", or "high"
        verbose: Print progress
    
    Returns:
        List of deals that match the status filter, with price status data added
    """
    if verbose:
        print(f"\nChecking price status for {len(deals)} deals (filter: {status_filter})...")
    
    # Create semaphore to limit parallel requests
    semaphore = asyncio.Semaphore(max_parallel)
    
    async def check_with_semaphore(deal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with semaphore:
            status_data = await check_price_status_fast(
                origin=deal['origin'],
                destination=deal['destination'],
                start_date=deal['start_date'],
                end_date=deal['end_date']
            )
            
            # Add status data to deal
            deal['price_status'] = status_data
            
            # Check if meets filter
            status = status_data.get('status')
            meets_filter = status == status_filter
            
            if verbose:
                status_emoji = "🟢" if status == "low" else "🟡" if status == "typical" else "🔴" if status == "high" else "⚪"
                
                if meets_filter:
                    print(f"  ✓ {status_emoji} {deal['origin']}→{deal['destination']}: ${deal['price']} "
                          f"({status}) [{status_data['load_time']:.1f}s]")
                elif status:
                    print(f"  ✗ {status_emoji} {deal['origin']}→{deal['destination']}: ${deal['price']} "
                          f"({status} - not {status_filter}) [{status_data['load_time']:.1f}s]")
                else:
                    error = status_data.get('error', 'Unknown')
                    print(f"  ⚪ {deal['origin']}→{deal['destination']}: No status data ({error}) [{status_data['load_time']:.1f}s]")
            
            return deal if meets_filter else None
    
    # Check all deals in parallel
    start_time = time.time()
    results = await asyncio.gather(*[check_with_semaphore(deal) for deal in deals])
    total_time = time.time() - start_time
    
    # Filter out None results (deals that didn't meet filter)
    filtered_deals = [d for d in results if d is not None]
    
    if verbose:
        print(f"\n✓ Price status check complete: {len(filtered_deals)}/{len(deals)} deals are '{status_filter}'")
        print(f"  Total time: {total_time:.1f}s ({total_time/len(deals):.1f}s per deal)")
    
    return filtered_deals

