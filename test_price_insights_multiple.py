#!/usr/bin/env python3
"""
Test price insights on multiple routes to verify all parsing works.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.check_price_insight_fast import check_price_insight

def test_route(origin, destination, outbound, return_date, expected_status=None):
    print(f"\nTesting: {origin} → {destination}")
    print("-" * 80)
    result = check_price_insight(origin, destination, outbound, return_date, verbose=True)
    
    if expected_status and result['current_price'] != expected_status:
        print(f"  ⚠️  Expected {expected_status}, got {result['current_price']}")
    
    return result

if __name__ == "__main__":
    print("=" * 80)
    print("TESTING PRICE INSIGHTS ON MULTIPLE ROUTES")
    print("=" * 80)
    
    # Test 1: Lisbon (should be "low" with discount)
    test_route("PHX", "LIS", "2026-03-01", "2026-03-08", expected_status="low")
    
    # Test 2: Rome (should be "typical")
    test_route("PHX", "FCO", "2026-03-15", "2026-03-22", expected_status="typical")
    
    # Test 3: A route with "high" pricing
    test_route("LAX", "JFK", "2025-12-20", "2025-12-27", expected_status="high")
    
    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)

