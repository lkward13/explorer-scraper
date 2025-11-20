#!/usr/bin/env python3
"""
Production test: 50 origins × 9 regions × 5 deals each.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_50_origins():
    """Test 50 origins - half of the full 103 airport list."""
    
    print("="*80)
    print("PRODUCTION TEST: 50 Origins × 9 Regions × 5 Deals")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Origins: 50 major US airports")
    print("  - Regions: All 9 regions")
    print("  - Expansion: API mode (9-month coverage)")
    print("  - Browsers: 10 (for parallel API expansion)")
    print("  - Deals per origin: 5 (top 5 cheapest)")
    print("  - Expected expansions: ~250")
    print()
    print("Estimated time:")
    print("  - Explore: ~15-18 minutes (450 page loads)")
    print("  - Expansion: ~2-3 minutes (250 deals)")
    print("  - Total: ~18-21 minutes")
    print()
    
    # First 50 airports with pre-generated TFS data
    origins = [
        'ABQ', 'ALB', 'ANC', 'ATL', 'AUS',
        'AVL', 'BDL', 'BHM', 'BNA', 'BOI',
        'BOS', 'BTR', 'BUF', 'BWI', 'CAK',
        'CHO', 'CHS', 'CID', 'CLE', 'CLT',
        'CMH', 'COS', 'CVG', 'DAL', 'DAY',
        'DEN', 'DFW', 'DSM', 'DTW', 'ELP',
        'EWR', 'FAR', 'FAT', 'FLL', 'FSD',
        'GEG', 'GPT', 'GRR', 'GSP', 'HOU',
        'HSV', 'IAD', 'IAH', 'ICT', 'IND',
        'JAX', 'JFK', 'LAS', 'LAX', 'LBB'
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
        'name': '50 Origins Production Test',
        'description': '50 origins, all regions, 9-month API expansion, 10 browsers',
        'origins': origins,
        'browsers': 10,
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
    asyncio.run(test_50_origins())

