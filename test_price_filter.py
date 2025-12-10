#!/usr/bin/env python3
"""
Test the price insight filter with 3 origins.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def main():
    print("=" * 80)
    print("TESTING PRICE INSIGHT FILTER (3 ORIGINS)")
    print("=" * 80)
    print()
    print("Flow:")
    print("  1. Explore 3 origins (PHX, DFW, LAX)")
    print("  2. Select top 5 deals per origin (15 total)")
    print("  3. Check price status (filter to 'low' only)")
    print("  4. Expand remaining deals")
    print()
    print("=" * 80)
    print()
    
    # Custom config for 3-origin test
    test_config = {
        'name': 'Price Filter Test',
        'origins': ['PHX', 'DFW', 'LAX'],
        'browsers': 5,  # 5 browsers for expansion
        'deals_per_origin': 5,  # Check 5 deals per origin
        'regions': None,  # All 9 regions
        'description': '3 origins, 5 deals each, "low" status filter'
    }
    
    result = await run_test_phase(
        phase=1,  # Use phase 1 slot
        verbose=True,
        override_config=test_config,
        use_api=True,  # Use API expansion
        save_to_db=False  # Don't save to DB for now
    )
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"Explore time:         {result['explore_time']:.1f}s")
    print(f"Price insight time:   {result['insight_time']:.1f}s")
    print(f"Expansion time:       {result['expansion_time']:.1f}s")
    print(f"Total time:           {result['total_time']:.1f}s")
    print()
    print(f"Cards found:          {result['cards_found']}")
    print(f"Deals selected:       {result['deals_selected']}")
    print(f"Deals with 'low' status: {result['deals_filtered']}")
    print(f"Expansions succeeded: {result['expansions_succeeded']}")
    print(f"Valid deals (≥5 dates): {result['valid_deals']}")
    print()
    
    if result['deals_filtered'] > 0:
        filter_rate = (result['deals_filtered'] / result['deals_selected']) * 100
        print(f"Filter pass rate:     {filter_rate:.1f}% ({result['deals_filtered']}/{result['deals_selected']})")
    
    if result['expansions_succeeded'] > 0:
        expansion_rate = (result['expansions_succeeded'] / result['deals_filtered']) * 100
        print(f"Expansion success:    {expansion_rate:.1f}% ({result['expansions_succeeded']}/{result['deals_filtered']})")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())

