#!/usr/bin/env python3
"""
Final production test: 10 origins × 9 regions × 5 deals each.
This is a realistic scale that avoids rate limiting.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_10_origins():
    """Test 10 major origins - realistic production scale."""
    
    print("="*80)
    print("FINAL PRODUCTION TEST: 10 Origins × 9 Regions × 5 Deals")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Origins: 10 major US airports")
    print("  - Regions: All 9 regions")
    print("  - Expansion: API mode (9-month coverage)")
    print("  - Browsers: 10 (for parallel API expansion)")
    print("  - Deals per origin: 5 (top 5 cheapest)")
    print("  - Expected expansions: ~50")
    print()
    print("Estimated time:")
    print("  - Explore: ~3-4 minutes (90 page loads)")
    print("  - Expansion: ~30-60 seconds (50 deals)")
    print("  - Total: ~4-5 minutes")
    print()
    
    # Top 10 major hubs
    origins = [
        'ATL',  # Atlanta - #1 busiest
        'DFW',  # Dallas/Fort Worth - #2
        'DEN',  # Denver - #3
        'ORD',  # Chicago O'Hare - #4
        'LAX',  # Los Angeles - #5
        'JFK',  # New York JFK - major international
        'SFO',  # San Francisco - West Coast hub
        'MIA',  # Miami - Latin America hub
        'SEA',  # Seattle - Pacific hub
        'BOS',  # Boston - Northeast hub
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
        'name': '10 Origins Final Test',
        'description': '10 major hubs, all regions, 9-month API expansion',
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
    asyncio.run(test_10_origins())

