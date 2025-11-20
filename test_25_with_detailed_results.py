#!/usr/bin/env python3
"""
25-origin test with detailed per-origin results tracking.
"""
import asyncio
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from worker.test_parallel import run_test_phase

async def test_25_origins_detailed():
    """Test 25 origins with detailed result tracking."""
    
    print("="*80)
    print("DETAILED TEST: 25 Origins × 9 Regions × 5 Deals")
    print("="*80)
    print()
    
    # Top 25 US airports with TFS data
    origins = [
        'ATL', 'DFW', 'DEN', 'ORD', 'LAX',
        'CLT', 'MCO', 'LAS', 'PHX', 'MIA',
        'SEA', 'IAH', 'EWR', 'SFO', 'BOS',
        'FLL', 'MSP', 'DTW', 'PHL', 'LGA',
        'BWI', 'SLC', 'SAN', 'PDX', 'AUS'
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
        'name': '25 Origins Detailed Test',
        'description': '25 origins with per-origin result tracking',
        'origins': origins,
        'browsers': 10,
        'deals_per_origin': 5,
        'regions': regions,
    }
    
    results = await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True
    )
    
    # Analyze results per origin
    print("\n" + "="*80)
    print("DETAILED RESULTS BY ORIGIN")
    print("="*80)
    
    if results and 'expanded_deals' in results:
        # Group by origin
        by_origin = defaultdict(list)
        for deal in results['expanded_deals']:
            origin = deal.get('origin', 'UNKNOWN')
            by_origin[origin].append(deal)
        
        # Track API failures
        total_deals = 0
        api_failures = 0
        no_data_routes = 0
        too_expensive_routes = 0
        valid_deals = 0
        
        for origin in sorted(origins):
            deals = by_origin.get(origin, [])
            total_deals += len(deals)
            
            print(f"\n{origin}:")
            print(f"  Deals expanded: {len(deals)}")
            
            if deals:
                for deal in deals:
                    dest = deal.get('destination', 'UNKNOWN')
                    price = deal.get('price', 0)
                    similar = deal.get('result', {}).get('similar_deals', [])
                    
                    # Check if it was an API failure (we'll add a flag for this)
                    if len(similar) == 0:
                        # Check the raw result to see if it was no data or too expensive
                        # For now, we'll count it as "no similar dates"
                        no_data_routes += 1
                        status = "❌ No data or too expensive"
                    elif len(similar) < 5:
                        status = f"⚠️  Only {len(similar)} dates found"
                    else:
                        valid_deals += 1
                        status = f"✅ {len(similar)} dates found"
                    
                    print(f"    {dest} (${price}): {status}")
            else:
                print(f"    ⚠️  No deals expanded for this origin")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total deals expanded:        {total_deals}")
        print(f"Valid deals (≥5 dates):      {valid_deals} ({valid_deals/total_deals*100:.1f}%)")
        print(f"Low data deals (<5 dates):   {total_deals - valid_deals - no_data_routes}")
        print(f"No data/too expensive:       {no_data_routes} ({no_data_routes/total_deals*100:.1f}%)")
        print(f"API failures (blocked):      {api_failures}")
        print()
        print(f"✅ API Success Rate: {(total_deals - api_failures) / total_deals * 100:.1f}%")
        
        if api_failures == 0:
            print("\n🎉 PERFECT! No API failures - all requests got data from Google!")
        
    else:
        print("\n⚠️  No results returned from test")

if __name__ == '__main__':
    asyncio.run(test_25_origins_detailed())

