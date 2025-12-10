#!/usr/bin/env python3
"""
Test 100 origins in four batches of 25 with 2.5-minute pauses.
More conservative approach to avoid rate limiting.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase


async def test_100_origins_four_batches():
    """Run 100 origins as 4× 25-origin batches with 2.5-min pauses."""
    
    # Load first 100 origins
    with open('data/top_150_us_airports.txt', 'r') as f:
        all_origins = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    origins_100 = all_origins[:100]
    
    # Split into 4 batches of 25
    batches = [
        origins_100[0:25],
        origins_100[25:50],
        origins_100[50:75],
        origins_100[75:100]
    ]
    
    print("=" * 80)
    print("100-ORIGIN TEST (4× 25-ORIGIN BATCHES)")
    print("=" * 80)
    print(f"Total origins: {len(origins_100)}")
    print(f"Batch size: 25 origins each")
    print(f"Number of batches: 4")
    print(f"Pause between batches: 2.5 minutes")
    print(f"Deals per origin: 5")
    print(f"Expected expansions: {len(origins_100) * 5} total")
    print("=" * 80)
    print()
    
    overall_start = datetime.now()
    batch_results = []
    pause_minutes = 10  # 10-minute pause between batches to avoid rate limiting
    
    for batch_num, batch_origins in enumerate(batches, 1):
        # ========== RUN BATCH ==========
        print("\n" + "🚀 " * 40)
        print(f"BATCH {batch_num}/4: ORIGINS {(batch_num-1)*25 + 1}-{batch_num*25}")
        print("🚀 " * 40 + "\n")
        
        batch_config = {
            'name': f'Batch {batch_num} (Origins {(batch_num-1)*25 + 1}-{batch_num*25})',
            'origins': batch_origins,
            'browsers': 8,  # 8 browsers for expansion (testing higher throughput)
            'explore_browsers': 5,  # 5 browsers for explore phase
            'deals_per_origin': 5,
            'regions': None,  # All 9 regions
            'description': f'25 origins, 5 deals each, 5 explore / 8 expansion browsers'
        }
        
        batch_result = await run_test_phase(
            phase=1,
            verbose=False,
            override_config=batch_config,
            use_api=True,
            save_to_db=True  # Save all results to PostgreSQL database
        )
        
        batch_results.append(batch_result)
        
        # ========== PAUSE (except after last batch) ==========
        if batch_num < len(batches):
            print("\n" + "⏸️  " * 40)
            print(f"PAUSING FOR {pause_minutes} MINUTES")
            print("=" * 80)
            print(f"Letting Google rate limits reset before batch {batch_num + 1}...")
            current_time = datetime.now()
            resume_time = current_time + timedelta(minutes=pause_minutes)
            print(f"Current time: {current_time.strftime('%H:%M:%S')}")
            print(f"Resume time: {resume_time.strftime('%H:%M:%S')}")
            print("⏸️  " * 40 + "\n")
            
            await asyncio.sleep(pause_minutes * 60)
    
    # ========== FINAL SUMMARY ==========
    total_time = (datetime.now() - overall_start).total_seconds()
    
    print("\n" + "=" * 80)
    print("100-ORIGIN TEST COMPLETE")
    print("=" * 80)
    
    total_cards = sum(r['cards_found'] for r in batch_results)
    total_attempted = sum(r['expansions_attempted'] for r in batch_results)
    total_succeeded = sum(r['expansions_succeeded'] for r in batch_results)
    total_valid = sum(r['valid_deals'] for r in batch_results)
    
    for i, result in enumerate(batch_results, 1):
        batch_time = result['total_time']
        print(f"\nBatch {i} ({result['config']['name']}):")
        print(f"  Time:        {batch_time:.1f}s ({batch_time/60:.1f} min)")
        print(f"  Cards:       {result['cards_found']}")
        print(f"  Expansions:  {result['expansions_succeeded']}/{result['expansions_attempted']}")
        print(f"  Valid deals: {result['valid_deals']}")
    
    print(f"\nTotal time (including pauses): {total_time:.1f}s ({total_time/60:.1f} min)")
    print()
    print(f"COMBINED RESULTS:")
    print(f"  Total cards:        {total_cards}")
    print(f"  Total expansions:   {total_succeeded}/{total_attempted}")
    print(f"  Total valid deals:  {total_valid}")
    print(f"  Success rate:       {(total_succeeded / total_attempted * 100):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_100_origins_four_batches())

