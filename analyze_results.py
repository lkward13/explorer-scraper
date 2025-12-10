#!/usr/bin/env python3
"""
Analyze results of the regional diversity test.
Focuses on:
1. Success rate of mapped cities
2. Regional distribution of VALID deals
3. Comparison with previous runs
"""
import psycopg2
from database.config import get_connection_string

def analyze_results():
    conn = psycopg2.connect(get_connection_string())
    cur = conn.cursor()
    
    # Get latest scrape run
    cur.execute("SELECT MAX(id) FROM scrape_runs")
    run_id = cur.fetchone()[0]
    
    print("=" * 80)
    print(f"ANALYSIS FOR RUN #{run_id}")
    print("=" * 80)
    print()
    
    # 1. Overall Stats
    cur.execute("""
        SELECT 
            COUNT(*) as total_deals,
            COUNT(DISTINCT origin) as origins,
            COUNT(DISTINCT destination) as destinations,
            COUNT(DISTINCT search_region) as regions
        FROM expanded_deals
        WHERE scrape_run_id = %s
    """, (run_id,))
    total, origins, dests, regions = cur.fetchone()
    print(f"Total Options Found: {total}")
    print(f"Origins: {origins}")
    print(f"Destinations: {dests}")
    print(f"Regions: {regions}")
    print()
    
    # 2. Valid Deals by Region
    print("VALID DEALS BY REGION:")
    print("-" * 80)
    cur.execute("""
        SELECT 
            search_region,
            COUNT(DISTINCT destination) as unique_routes,
            MIN(price) as min_price,
            MAX(price) as max_price,
            COUNT(*) as total_options
        FROM expanded_deals
        WHERE scrape_run_id = %s
        GROUP BY search_region
        ORDER BY unique_routes DESC
    """, (run_id,))
    
    for region, routes, min_p, max_p, options in cur.fetchall():
        print(f"{region.title():20s}: {routes:3d} routes (${min_p}-${max_p}) - {options} options")
    print()
    
    # 3. Rare Regions Check
    print("CHECKING RARE REGIONS:")
    print("-" * 80)
    rare_regions = ['asia', 'oceania', 'africa', 'middle_east']
    found_any = False
    for region in rare_regions:
        cur.execute("""
            SELECT origin, destination, price, destination_city
            FROM expanded_deals
            WHERE scrape_run_id = %s AND search_region = %s
            ORDER BY price ASC
            LIMIT 3
        """, (run_id, region))
        deals = cur.fetchall()
        if deals:
            found_any = True
            print(f"{region.title()}:")
            for origin, dest, price, city in deals:
                print(f"  ✓ {origin} → {dest} ({city}): ${price}")
        else:
            print(f"{region.title()}: No deals found")
    print()
    
    # 4. Success Rate of Mapped Cities
    print("MAPPED VS UNMAPPED (Inferred):")
    print("-" * 80)
    # We can check if destination is 3 chars (mapped) or longer (unmapped)
    cur.execute("""
        SELECT 
            LENGTH(destination) as dest_len,
            COUNT(DISTINCT destination) as count
        FROM expanded_deals
        WHERE scrape_run_id = %s
        GROUP BY dest_len
    """, (run_id,))
    
    for length, count in cur.fetchall():
        if length == 3:
            print(f"IATA Codes (Mapped): {count} destinations")
        else:
            print(f"City Names (Unmapped/Failed): {count} destinations")

if __name__ == "__main__":
    analyze_results()

