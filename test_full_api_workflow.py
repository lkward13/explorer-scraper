#!/usr/bin/env python3
"""
Test full workflow: Explore (browser) + Expansion (API).
Small scale to verify integration works end-to-end.
"""
import asyncio
from pathlib import Path
from worker.test_parallel import run_test_phase

async def main():
    """Run full workflow test with API expansion."""
    
    print("="*80)
    print("FULL WORKFLOW TEST: Explore (Browser) + Expansion (API)")
    print("="*80)
    print("\nThis will:")
    print("1. Run explore scraping (browser automation)")
    print("2. Select top deals")
    print("3. Expand using API (fast, no browser)")
    print()
    
    # Small test: 2 origins, 1 region, API expansion
    test_config = {
        'name': 'Full Workflow: 2 origins, API expansion',
        'description': '2 origins × 1 region, explore via browser, expand via API',
        'origins': ['ATL', 'DFW'],
        'browsers': 2,
        'deals_per_origin': 3,
        'regions': ['caribbean'],  # Just 1 region for speed
        'use_api': True  # ← Use API for expansion
    }
    
    print("Starting test...")
    print(f"Origins: {', '.join(test_config['origins'])}")
    print(f"Region: {test_config['regions'][0]}")
    print(f"Expansion method: API")
    print()
    
    result = await run_test_phase(3, verbose=True, override_config=test_config)
    
    if result:
        print("\n" + "="*80)
        print("✓ FULL WORKFLOW TEST COMPLETE!")
        print("="*80)
        print("\nAPI expansion works with real explore data!")
        print("Ready to scale to 100+ origins.")
    else:
        print("\n✗ Test failed")

if __name__ == '__main__':
    asyncio.run(main())

