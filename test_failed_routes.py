#!/usr/bin/env python3
"""Test 10 routes that consistently fail to see if calendar data actually loads."""
import asyncio
import sys
from playwright.async_api import async_playwright
from scripts.expand_dates import expand_dates

# Routes that consistently get 0 similar dates
FAILED_ROUTES = [
    ('ATL', 'MIA', '2026-01-11', '2026-01-20', 58, 'Miami'),
    ('LAX', 'LAS', '2026-01-11', '2026-01-20', 50, 'Las Vegas'),
    ('ATL', 'ANTIGUA GUATEMALA', '2026-02-21', '2026-02-28', 195, 'Antigua Guatemala'),
    ('LAX', 'COPAN RUINAS', '2026-01-11', '2026-01-20', 228, 'Copan Ruinas'),
    ('LAX', 'AUA', '2026-01-11', '2026-01-20', 306, 'Aruba'),
    ('DEN', 'SAN JOSE', '2026-01-11', '2026-01-20', 200, 'San Jose CR'),
    ('PHX', 'CUENCA', '2026-01-11', '2026-01-20', 250, 'Cuenca Ecuador'),
    ('MCO', 'BRIGHTON', '2026-01-11', '2026-01-20', 300, 'Brighton UK'),
    ('DEN', 'CARTAGENA', '2026-01-11', '2026-01-20', 220, 'Cartagena Colombia'),
    ('PHX', 'KRAKOW', '2026-01-11', '2026-01-20', 400, 'Krakow Poland'),
]

async def test_route(origin, dest, start, end, price, name):
    """Test a single route to see if expansion finds data."""
    print(f"\n{'='*80}", flush=True)
    print(f"Testing: {origin} → {name} (${price})", flush=True)
    print(f"Dates: {start} to {end}", flush=True)
    print('='*80, flush=True)
    
    try:
        result = await expand_dates(
            origin=origin,
            destination=dest,
            reference_start=start,
            reference_end=end,
            reference_price=price,
            verbose=False  # Keep it quiet
        )
        
        similar_count = len(result.get('similar_deals', []))
        print(f"  Result: {similar_count} similar dates found", flush=True)
        
        if similar_count > 0:
            print(f"  ✅ SUCCESS - Found calendar data!", flush=True)
        else:
            print(f"  ❌ FAILED - No calendar data", flush=True)
        
        return similar_count > 0
        
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)[:100]}", flush=True)
        return False

async def main():
    print("\n" + "="*80, flush=True)
    print("TESTING 10 CONSISTENTLY FAILING ROUTES", flush=True)
    print("="*80, flush=True)
    
    successes = 0
    failures = 0
    
    for origin, dest, start, end, price, name in FAILED_ROUTES:
        success = await test_route(origin, dest, start, end, price, name)
        if success:
            successes += 1
        else:
            failures += 1
        
        # Small delay between tests
        await asyncio.sleep(3)
    
    print("\n" + "="*80, flush=True)
    print("SUMMARY", flush=True)
    print("="*80, flush=True)
    print(f"Successes: {successes}/{len(FAILED_ROUTES)}", flush=True)
    print(f"Failures:  {failures}/{len(FAILED_ROUTES)}", flush=True)
    print(f"Success rate: {(successes/len(FAILED_ROUTES)*100):.1f}%", flush=True)

if __name__ == '__main__':
    asyncio.run(main())

