#!/usr/bin/env python3
"""
Test 100 origins in two batches of 50 with a pause in between.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase


async def test_100_origins_two_batches():
    """Run 100 origins as 2× 50-origin batches with a pause."""
    
    # Load first 100 origins (skip comment lines starting with #)
    with open('data/top_150_us_airports.txt', 'r') as f:
        all_origins = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    origins_100 = all_origins[:100]
    batch1 = origins_100[:50]
    batch2 = origins_100[50:100]
    
    print("=" * 80)
    print("100-ORIGIN TEST (2× 50-ORIGIN BATCHES)")
    print("=" * 80)
    print(f"Total origins: {len(origins_100)}")
    print(f"Batch 1: {len(batch1)} origins")
    print(f"Batch 2: {len(batch2)} origins")
    print(f"Deals per origin: 5")
    print(f"Expected expansions: {len(origins_100) * 5} total")
    print("=" * 80)
    print()
    
    overall_start = datetime.now()
    
    # ========== BATCH 1 ==========
    print("\n" + "🚀 " * 40)
    print("BATCH 1: ORIGINS 1-50")
    print("🚀 " * 40 + "\n")
    
    batch1_config = {
        'name': 'Batch 1 (Origins 1-50)',
        'origins': batch1,
        'browsers': 5,
        'deals_per_origin': 5,
        'regions': None,  # All 9 regions
        'description': '50 origins, 5 deals each, 5 browsers'
    }
    
    batch1_result = await run_test_phase(
        phase=1,
        verbose=False,
        override_config=batch1_config,
        use_api=True
    )
    
    batch1_time = batch1_result['total_time']
    
    # ========== PAUSE ==========
    pause_minutes = 10
    print("\n" + "⏸️  " * 40)
    print(f"PAUSING FOR {pause_minutes} MINUTES")
    print("=" * 80)
    print("Letting Google rate limits reset before batch 2...")
    current_time = datetime.now()
    resume_time = current_time + timedelta(minutes=pause_minutes)
    print(f"Current time: {current_time.strftime('%H:%M:%S')}")
    print(f"Resume time: {resume_time.strftime('%H:%M:%S')}")
    print("⏸️  " * 40 + "\n")
    
    await asyncio.sleep(pause_minutes * 60)
    
    # ========== BATCH 2 ==========
    print("\n" + "🚀 " * 40)
    print("BATCH 2: ORIGINS 51-100")
    print("🚀 " * 40 + "\n")
    
    batch2_config = {
        'name': 'Batch 2 (Origins 51-100)',
        'origins': batch2,
        'browsers': 5,
        'deals_per_origin': 5,
        'regions': None,  # All 9 regions
        'description': '50 origins, 5 deals each, 5 browsers'
    }
    
    batch2_result = await run_test_phase(
        phase=1,
        verbose=False,
        override_config=batch2_config,
        use_api=True
    )
    
    batch2_time = batch2_result['total_time']
    
    # ========== FINAL SUMMARY ==========
    total_time = (datetime.now() - overall_start).total_seconds()
    
    print("\n" + "=" * 80)
    print("100-ORIGIN TEST COMPLETE")
    print("=" * 80)
    print(f"Batch 1 time:         {batch1_time:.1f}s ({batch1_time/60:.1f} min)")
    print(f"Pause time:           {pause_minutes * 60}s ({pause_minutes} min)")
    print(f"Batch 2 time:         {batch2_time:.1f}s ({batch2_time/60:.1f} min)")
    print(f"Total time:           {total_time:.1f}s ({total_time/60:.1f} min)")
    print()
    print(f"Batch 1 results:")
    print(f"  Cards found:        {batch1_result['cards_found']}")
    print(f"  Expansions:         {batch1_result['expansions_succeeded']}/{batch1_result['expansions_attempted']}")
    print(f"  Valid deals:        {batch1_result['valid_deals']}")
    print()
    print(f"Batch 2 results:")
    print(f"  Cards found:        {batch2_result['cards_found']}")
    print(f"  Expansions:         {batch2_result['expansions_succeeded']}/{batch2_result['expansions_attempted']}")
    print(f"  Valid deals:        {batch2_result['valid_deals']}")
    print()
    print(f"COMBINED RESULTS:")
    print(f"  Total cards:        {batch1_result['cards_found'] + batch2_result['cards_found']}")
    print(f"  Total expansions:   {batch1_result['expansions_succeeded'] + batch2_result['expansions_succeeded']}/{batch1_result['expansions_attempted'] + batch2_result['expansions_attempted']}")
    print(f"  Total valid deals:  {batch1_result['valid_deals'] + batch2_result['valid_deals']}")
    print(f"  Success rate:       {((batch1_result['expansions_succeeded'] + batch2_result['expansions_succeeded']) / (batch1_result['expansions_attempted'] + batch2_result['expansions_attempted']) * 100):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_100_origins_two_batches())

