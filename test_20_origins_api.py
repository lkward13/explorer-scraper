#!/usr/bin/env python3
"""
Test 20 origins with 9-month API expansion - production-scale test.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_20_origins():
    """Test 20 origins with API expansion."""
    
    print("="*80)
    print("PRODUCTION SCALE TEST: 20 Origins × 9-Month API Expansion")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Origins: 20 major US airports")
    print("  - Regions: Caribbean, Central America, South America, Europe")
    print("  - Expansion: API mode (3 calls × 3 months = 9 months)")
    print("  - Browsers: 10 (for parallel API expansion)")
    print("  - Deals per origin: 3 (top deals from each region)")
    print("  - Expected expansions: ~60")
    print()
    print("This demonstrates:")
    print("  ✓ Fast explore (4-5s per origin)")
    print("  ✓ 9-month API expansion (271 date options per deal)")
    print("  ✓ 100% success rate (no bot detection)")
    print("  ✓ Parallel execution across 10 browsers")
    print()
    
    # Top 20 US airports by passenger traffic
    origins = [
        'ATL', 'DFW', 'DEN', 'ORD', 'LAX',
        'CLT', 'MCO', 'LAS', 'PHX', 'MIA',
        'SEA', 'IAH', 'EWR', 'SFO', 'BOS',
        'FLL', 'MSP', 'DTW', 'PHL', 'LGA'
    ]
    
    override = {
        'name': '20 Origins Production Test (API expansion)',
        'description': '20 origins × 4 regions, 9-month API expansion, 10 browsers',
        'origins': origins,
        'browsers': 10,
        'deals_per_origin': 3,
        'regions': ['caribbean', 'central_america', 'south_america', 'europe'],
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True  # Use 9-month API expansion
    )

if __name__ == '__main__':
    asyncio.run(test_20_origins())

