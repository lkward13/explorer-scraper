#!/usr/bin/env python3
"""
Full 25-origin test with 11-month expansion from TODAY, using 5 browsers.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_25_origins_11_month():
    """Test 25 origins with 11-month expansion from today, 5 browsers."""
    
    print("="*80)
    print("PRODUCTION TEST: 25 Origins × 9 Regions × 5 Deals (11-Month Expansion)")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Origins: 25 major US airports")
    print("  - Regions: All 9 regions")
    print("  - Expansion: API mode (11-month from TODAY)")
    print("  - Browsers: 5 (for both explore and expansion)")
    print("  - Deals per origin: 5 (top 5 cheapest)")
    print("  - Expected expansions: ~125")
    print()
    print("Key change:")
    print("  - OLD: 9 months from deal's date (e.g., March 2026 + 9 months)")
    print("  - NEW: 11 months from TODAY")
    print("  - Expected: More availability, fewer '0 date combinations'")
    print()
    print("Estimated time:")
    print("  - Explore: ~8-10 minutes (225 page loads, batches of 5)")
    print("  - Expansion: ~3-4 minutes (125 deals, 5 browsers)")
    print("  - Total: ~12-14 minutes")
    print()
    
    # Top 25 US airports with TFS data
    origins = [
        'ATL', 'DFW', 'DEN', 'ORD', 'LAX',
        'CLT', 'MCO', 'LAS', 'PHX', 'MIA',
        'SEA', 'IAH', 'EWR', 'SFO', 'BOS',
        'FLL', 'MSP', 'DTW', 'PHL', 'LGA',
        'BWI', 'SLC', 'SAN', 'PDX', 'AUS'
    ]
    
    regions = [
        'caribbean',
        'central_america',
        'south_america',
        'europe',
        'africa',
        'asia',
        'oceania',
        'middle_east',
        'north_america'
    ]
    
    override = {
        'name': '25 Origins 11-Month Test',
        'description': '25 origins, all regions, 11-month API expansion from today, 5 browsers',
        'origins': origins,
        'browsers': 5,
        'deals_per_origin': 5,
        'regions': regions,
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True
    )
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    print()
    print("Check results:")
    print("  - Did we get more dates for popular routes?")
    print("  - Did '0 date combinations' decrease?")
    print("  - Still 100% API success rate?")
    print()

if __name__ == '__main__':
    asyncio.run(test_25_origins_11_month())

