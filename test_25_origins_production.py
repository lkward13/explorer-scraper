#!/usr/bin/env python3
"""
Production-scale test: 25 origins × 9 regions × 5 deals each.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_25_origins_production():
    """Test 25 origins with full region coverage."""
    
    print("="*80)
    print("PRODUCTION SCALE TEST: 25 Origins × 9 Regions × 5 Deals")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Origins: 25 major US airports")
    print("  - Regions: All 9 regions (Caribbean, Central America, South America,")
    print("             Europe, Africa, Asia, Oceania, Middle East, North America)")
    print("  - Expansion: API mode (3 calls × 3 months = 9 months)")
    print("  - Browsers: 15 (for parallel API expansion)")
    print("  - Deals per origin: 5 (top deals across all regions)")
    print("  - Expected expansions: ~125")
    print()
    print("Estimated time:")
    print("  - Explore: ~2 minutes (25 origins × 9 regions)")
    print("  - Expansion: ~1 minute (125 deals × 1s each ÷ 15 browsers)")
    print("  - Total: ~3 minutes")
    print()
    
    # Top 25 US airports by passenger traffic (with pre-generated TFS)
    origins = [
        'ATL', 'DFW', 'DEN', 'ORD', 'LAX',
        'CLT', 'MCO', 'LAS', 'PHX', 'MIA',
        'SEA', 'IAH', 'EWR', 'SFO', 'BOS',
        'FLL', 'MSP', 'DTW', 'PHL', 'LGA',
        'BWI', 'SLC', 'SAN', 'PDX', 'AUS'
    ]
    
    # All 9 regions
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
        'name': '25 Origins × 9 Regions Production Test',
        'description': '25 origins, all regions, 9-month API expansion, 15 browsers',
        'origins': origins,
        'browsers': 15,
        'deals_per_origin': 5,
        'regions': regions,
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True  # Use 9-month API expansion
    )

if __name__ == '__main__':
    asyncio.run(test_25_origins_production())

