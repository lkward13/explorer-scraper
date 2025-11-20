#!/usr/bin/env python3
"""
Test 5 origins with 9-month API expansion and generate clickable URLs.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase
from explore_scraper.tfs_builder import build_tfs_from_airport_code
import json

async def test_with_urls():
    """Test 5 origins and generate clickable URLs."""
    
    print("="*80)
    print("5 ORIGINS TEST: With Clickable URLs")
    print("="*80)
    print()
    
    origins = ['ATL', 'DFW', 'LAX', 'ORD', 'MIA']
    
    override = {
        'name': '5 Origins with URLs',
        'description': '5 origins × Europe, 9-month API expansion, generate URLs',
        'origins': origins,
        'browsers': 5,
        'deals_per_origin': 2,
        'regions': ['europe'],
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True
    )
    
    # Load results
    print("\n" + "="*80)
    print("GENERATING CLICKABLE URLS")
    print("="*80 + "\n")
    
    # Read the most recent results
    import glob
    import os
    
    # Find most recent results file
    results_files = glob.glob("results_*.json")
    if not results_files:
        print("No results file found")
        return
    
    latest_file = max(results_files, key=os.path.getmtime)
    
    with open(latest_file, 'r') as f:
        results = json.load(f)
    
    expansions = results.get('expansions', [])
    
    if not expansions:
        print("No expansions found in results")
        return
    
    print(f"Found {len(expansions)} expanded deals\n")
    
    # Generate URLs for top 10 deals
    count = 0
    for exp in expansions:
        if count >= 10:
            break
        
        if not exp.get('similar_deals'):
            continue
        
        origin = exp['origin']
        destination = exp['destination']
        similar = exp['similar_deals']
        
        if not similar:
            continue
        
        count += 1
        
        # Sort by price
        similar.sort(key=lambda x: x['price'])
        
        print(f"{count}. {origin} → {destination} (${exp['reference_price']})")
        print(f"   Found {len(similar)} similar deals")
        print(f"   Price range: ${similar[0]['price']} - ${similar[-1]['price']}")
        print(f"\n   Top 3 cheapest dates:")
        
        for i, deal in enumerate(similar[:3]):
            # Build TFS for this specific flight
            from explore_scraper.tfs import build_round_trip_tfs
            
            tfs = build_round_trip_tfs(
                origin=origin,
                destination=destination,
                outbound_date=deal['outbound_date'],
                return_date=deal['return_date']
            )
            
            url = f"https://www.google.com/travel/flights?tfs={tfs}&hl=en&gl=us"
            
            print(f"   {i+1}. ${deal['price']} | {deal['outbound_date']} to {deal['return_date']}")
            print(f"      {url}\n")
        
        print()

if __name__ == '__main__':
    asyncio.run(test_with_urls())

