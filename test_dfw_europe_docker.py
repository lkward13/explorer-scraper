#!/usr/bin/env python3
"""
Test DFW → Europe with 9-month API expansion in Docker.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_dfw_europe():
    """Test DFW → Europe with API expansion."""
    
    print("="*80)
    print("DFW → EUROPE TEST (9-month API expansion)")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Origin: DFW")
    print("  - Region: Europe")
    print("  - Expansion: API mode (3 calls × 3 months = 9 months)")
    print("  - Browsers: 3 (for parallel API expansion)")
    print("  - Deals: Top 5 from explore phase")
    print()
    
    override = {
        'name': 'DFW → Europe (API expansion)',
        'description': 'Test 9-month API expansion with real European destinations',
        'origins': ['DFW'],
        'browsers': 3,
        'deals_per_origin': 5,
        'regions': ['europe'],
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True  # Use API expansion
    )

if __name__ == '__main__':
    asyncio.run(test_dfw_europe())

