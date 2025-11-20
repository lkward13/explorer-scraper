#!/usr/bin/env python3
"""
Quick test to see detailed API logging for "0 similar dates" cases.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_api_logging():
    """Test 3 origins to see API logging details."""
    
    print("="*80)
    print("API LOGGING TEST: 3 Origins to check '0 similar dates' cases")
    print("="*80)
    print()
    
    origins = ['ATL', 'DFW', 'LAX']
    regions = ['europe']  # Just Europe for speed
    
    override = {
        'name': 'API Logging Test',
        'description': 'Test API logging to see if 0 dates = no data or too expensive',
        'origins': origins,
        'browsers': 3,
        'deals_per_origin': 3,
        'regions': regions,
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True
    )

if __name__ == '__main__':
    asyncio.run(test_api_logging())

