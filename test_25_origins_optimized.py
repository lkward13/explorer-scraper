#!/usr/bin/env python3
"""
Optimized test: 25 origins × 9 regions × 5 deals each.
Uses fewer browsers for explore, more for expansion.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_25_origins_optimized():
    """Test 25 origins with optimized browser allocation."""
    
    print("="*80)
    print("OPTIMIZED TEST: 25 Origins × 9 Regions × 5 Deals")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Origins: 25 major US airports")
    print("  - Regions: All 9 regions")
    print("  - Expansion: API mode (9-month coverage)")
    print("  - Browsers: 10 (optimal for API parallelism)")
    print("  - Deals per origin: 5 (top 5 cheapest across all regions)")
    print("  - Expected expansions: ~125")
    print()
    print("Optimizations:")
    print("  ✓ Reduced browser count (10 vs 15) for less resource contention")
    print("  ✓ Batching explore in smaller groups for faster completion")
    print("  ✓ API expansion is pure HTTP (no actual browsers)")
    print()
    print("Estimated time:")
    print("  - Explore: ~2-3 minutes")
    print("  - Expansion: ~1-2 minutes")
    print("  - Total: ~3-5 minutes")
    print()
    
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
        'name': '25 Origins Optimized Test',
        'description': '25 origins, 9 regions, 9-month API, 10 browsers (optimized)',
        'origins': origins,
        'browsers': 10,  # Reduced from 15
        'deals_per_origin': 5,
        'regions': regions,
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True
    )

if __name__ == '__main__':
    asyncio.run(test_25_origins_optimized())

