#!/usr/bin/env python3
"""
Test the new 11-month expansion from TODAY.
This should catch more availability than the old 9-month from deal date.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_11_month():
    """Test 5 origins with 11-month expansion from today."""
    
    print("="*80)
    print("11-MONTH EXPANSION TEST (from TODAY)")
    print("="*80)
    print()
    print("Changes:")
    print("  - Old: 9 months from deal's date (e.g., March 2026 + 9 months)")
    print("  - New: 11 months from TODAY")
    print()
    print("Expected improvement:")
    print("  - More availability (searching from today, not future date)")
    print("  - Longer booking window (11 vs 9 months)")
    print("  - Fewer '0 date combinations' for seasonal routes")
    print()
    
    origins = ['LAX', 'PHX', 'SFO', 'DEN', 'SEA']
    regions = ['europe']
    
    override = {
        'name': '11-Month Expansion Test',
        'description': '5 origins, Europe only, 11 months from today',
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
    print("TEST COMPLETE")
    print("="*80)
    print()
    print("Check if routes that had '0 date combinations' before now have data!")

if __name__ == '__main__':
    asyncio.run(test_11_month())

