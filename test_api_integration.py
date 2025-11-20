#!/usr/bin/env python3
"""
Test API-based expansion integration with the full scraper.
Start small to see if Google blocks us at scale.
"""
import asyncio
from pathlib import Path
from worker.test_parallel import run_test_phase

async def main():
    """Run progressive API tests."""
    
    print("="*80)
    print("API EXPANSION INTEGRATION TEST")
    print("="*80)
    print("\nTesting if Google blocks API calls at scale...")
    print()
    
    # Test 1: 2 origins, 2 browsers, API mode
    print("\n" + "="*80)
    print("TEST 1: Small scale (2 origins, 5 expansions, API mode)")
    print("="*80)
    
    test1_config = {
        'name': 'API Test: 2 origins, 2 browsers',
        'description': '2 origins × 1 region × 2 browsers (API mode)',
        'origins': ['ATL', 'DFW'],
        'browsers': 2,
        'deals_per_origin': 3,
        'regions': ['caribbean'],  # Just 1 region for speed
        'use_api': True  # ← Enable API mode
    }
    
    result1 = await run_test_phase(3, verbose=True, override_config=test1_config)
    
    if result1:
        print("\n✓ Test 1 complete!")
        input("\nPress Enter to continue to Test 2 (or Ctrl+C to stop)...")
    
    # Test 2: 5 origins, 5 browsers, API mode
    print("\n" + "="*80)
    print("TEST 2: Medium scale (5 origins, 15 expansions, API mode)")
    print("="*80)
    
    test2_config = {
        'name': 'API Test: 5 origins, 5 browsers',
        'description': '5 origins × 1 region × 5 browsers (API mode)',
        'origins': ['ATL', 'DFW', 'LAX', 'ORD', 'PHX'],
        'browsers': 5,
        'deals_per_origin': 3,
        'regions': ['caribbean'],
        'use_api': True
    }
    
    result2 = await run_test_phase(3, verbose=True, override_config=test2_config)
    
    if result2:
        print("\n✓ Test 2 complete!")
        input("\nPress Enter to continue to Test 3 (or Ctrl+C to stop)...")
    
    # Test 3: 10 origins, 10 browsers, API mode
    print("\n" + "="*80)
    print("TEST 3: Larger scale (10 origins, 30 expansions, API mode)")
    print("="*80)
    
    test3_config = {
        'name': 'API Test: 10 origins, 10 browsers',
        'description': '10 origins × 1 region × 10 browsers (API mode)',
        'origins': ['ATL', 'DFW', 'LAX', 'ORD', 'PHX', 'DEN', 'SEA', 'BOS', 'MIA', 'JFK'],
        'browsers': 10,
        'deals_per_origin': 3,
        'regions': ['caribbean'],
        'use_api': True
    }
    
    result3 = await run_test_phase(3, verbose=True, override_config=test3_config)
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETE!")
    print("="*80)
    print("\nIf all tests succeeded without blocks, we can scale to 100+ origins!")

if __name__ == '__main__':
    asyncio.run(main())

