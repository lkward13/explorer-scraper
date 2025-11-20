#!/usr/bin/env python3
"""Test a single expansion with verbose logging to diagnose timeouts."""
import asyncio
import json
import sys
from worker.test_parallel import run_explore_for_origin
from scripts.expand_dates import expand_dates


async def main():
    """Run single expansion test for ATL -> Antigua Guatemala."""
    origin = 'ATL'
    dest_name = 'Antigua Guatemala'
    region = 'central_america'
    
    print(f"\n{'='*80}")
    print(f"Testing: {origin} -> {dest_name} ({region})")
    print(f"{'='*80}\n")
    
    # Get explore data
    print("Step 1: Running explore to find the deal card...")
    cards = await run_explore_for_origin(origin, regions=[region], verbose=False)
    print(f"  Found {len(cards)} total cards from {origin} in {region}")
    
    # Find the specific destination
    matches = [c for c in cards if dest_name in str(c.get('destination', ''))]
    if not matches:
        print(f"  ERROR: No matching cards found for '{dest_name}'")
        return
    
    card = matches[0]
    print(f"  Found card for {dest_name}:")
    print(f"    Price: ${card['min_price']}")
    print(f"    Dates: {card['start_date']} to {card['end_date']}")
    print(f"    Region: {card.get('search_region', 'unknown')}")
    
    # Run expansion with verbose
    print(f"\nStep 2: Running expansion with verbose=True...")
    print(f"  (Watch for 'GetCalendarGraph' responses, interstitial detection, etc.)\n")
    
    result = await expand_dates(
        origin=origin,
        destination=card['destination'],
        reference_start=card['start_date'],
        reference_end=card['end_date'],
        reference_price=card['min_price'],
        verbose=True,
    )
    
    print(f"\n{'='*80}")
    print(f"RESULT: {len(result.get('similar_deals', []))} similar deals found")
    print(f"{'='*80}")
    
    if result.get('similar_deals'):
        print("\nSample deals:")
        for deal in result['similar_deals'][:3]:
            print(f"  {deal['start_date']} to {deal['end_date']}: ${deal['price']}")


if __name__ == '__main__':
    asyncio.run(main())

