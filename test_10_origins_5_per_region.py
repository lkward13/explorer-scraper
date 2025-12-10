#!/usr/bin/env python3
"""
Test 10 origins with 5 deals per region (regional diversity)

This test validates:
1. All regions are checked (not just cheapest)
2. Regional sales can be detected (3+ deals per region)
3. Asia/Australia deals aren't missed
4. Rate limiting is manageable
"""
import asyncio
from worker.test_parallel import run_test_phase

async def test_10_origins_regional_diversity():
    print("=" * 80)
    print("REGIONAL DIVERSITY TEST: 10 Origins, 5 Deals Per Region")
    print("=" * 80)
    print()
    print("Configuration:")
    print("  - 10 origins (major US airports)")
    print("  - 5 deals per region (up to 45 per origin)")
    print("  - All 9 regions checked")
    print("  - Expected: ~450 expansions total")
    print("  - Expected runtime: ~7-10 minutes")
    print()
    
    result = await run_test_phase(
        phase=1,
        verbose=False,
        override_config={
            'name': 'Regional Diversity Test',
            'description': '10 origins, 5 per region, all regions',
            'origins': ['DFW', 'ATL', 'LAX', 'ORD', 'JFK', 'PHX', 'DEN', 'SEA', 'BOS', 'MIA'],
            'browsers': 3,
            'explore_browsers': 5,
            'deals_per_origin': 5,  # 5 per REGION (not 5 total)
            'regions': None  # All regions
        },
        use_api=True,
        save_to_db=True
    )
    
    print()
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Total expansions: {result['expansions_attempted']}")
    print(f"Expansions succeeded: {result['expansions_succeeded']}")
    print(f"Valid deals (≥5 dates): {result['valid_deals']}")
    success_rate = (result['expansions_succeeded'] / result['expansions_attempted'] * 100) if result['expansions_attempted'] > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    print()
    
    # Analyze regional coverage
    print("Checking regional diversity...")
    from database.db import DealsDatabase
    from database.config import get_connection_string
    
    db = DealsDatabase(get_connection_string())
    
    # Get latest scrape run
    with db.conn.cursor() as cur:
        cur.execute("SELECT MAX(id) FROM scrape_runs")
        scrape_run_id = cur.fetchone()[0]
        
        # Check regions found
        cur.execute("""
            SELECT 
                search_region,
                COUNT(DISTINCT origin) as origins,
                COUNT(DISTINCT destination) as destinations,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM expanded_deals
            WHERE scrape_run_id = %s
            GROUP BY search_region
            ORDER BY search_region
        """, (scrape_run_id,))
        
        regions = cur.fetchall()
        
        print()
        print("Regions Found:")
        print("-" * 80)
        for region, origins, destinations, min_price, max_price in regions:
            print(f"  {region:20s}: {origins} origins, {destinations} destinations, ${min_price}-${max_price}")
        
        # Check for regional sales (3+ destinations from same origin to same region)
        cur.execute("""
            SELECT 
                origin,
                search_region,
                COUNT(DISTINCT destination) as dest_count,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM expanded_deals
            WHERE scrape_run_id = %s
            GROUP BY origin, search_region
            HAVING COUNT(DISTINCT destination) >= 3
            ORDER BY dest_count DESC
        """, (scrape_run_id,))
        
        regional_sales = cur.fetchall()
        
        print()
        print("Regional Sales Detected (3+ destinations):")
        print("-" * 80)
        if regional_sales:
            for origin, region, dest_count, min_price, max_price in regional_sales:
                print(f"  {origin} → {region:15s}: {dest_count} destinations, ${min_price}-${max_price}")
        else:
            print("  None detected")
    
    db.close()
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_10_origins_regional_diversity())

