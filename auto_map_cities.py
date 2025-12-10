#!/usr/bin/env python3
"""
Auto-map city names to IATA codes by extracting from explore card data.

The data-gs field in explore cards contains base64-encoded flight data
that includes the actual IATA code Google uses for that destination.
"""
import asyncio
import base64
import re
from collections import defaultdict
from worker.test_parallel import run_explore_for_origin

async def extract_iata_mappings(num_origins=20):
    """
    Run explore and extract city→IATA mappings from the card data.
    """
    print("=" * 80)
    print("AUTO-MAPPING CITIES TO IATA CODES")
    print("=" * 80)
    print()
    print(f"Extracting IATA codes from explore data for {num_origins} origins...")
    print()
    
    origins = [
        'DFW', 'ATL', 'LAX', 'ORD', 'JFK', 'PHX', 'DEN', 'SEA', 'BOS', 'MIA',
        'SFO', 'LAS', 'MCO', 'EWR', 'CLT', 'IAH', 'FLL', 'DTW', 'PHL', 'LGA'
    ][:num_origins]
    
    # Import HTML parser to get raw data
    from explore_scraper.cli import run as explore_run
    from explore_scraper.region_tfs_generator import build_explore_url_for_region
    from selectolax.parser import HTMLParser
    
    city_to_iata = {}
    iata_confidence = defaultdict(int)  # Track how many times we see each mapping
    
    for origin in origins:
        print(f"Processing {origin}...", end=' ', flush=True)
        
        cards_found = 0
        for region in ['europe', 'caribbean', 'asia', 'south_america', 'central_america', 
                      'oceania', 'middle_east', 'africa', 'north_america']:
            try:
                url = build_explore_url_for_region(origin, region)
                
                # Get raw HTML
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    html = await page.content()
                    
                    await browser.close()
                
                # Parse cards
                tree = HTMLParser(html)
                for card in tree.css(".SwQ5Be"):
                    # Get destination name
                    dest_el = card.css_first(".cCO9qc.tdMWuf.mxXqs")
                    if not dest_el:
                        continue
                    
                    city_name = dest_el.text().strip()
                    if not city_name:
                        continue
                    
                    # Get data-gs which contains the IATA code
                    price_span = card.css_first("[data-gs]")
                    if not price_span:
                        continue
                    
                    data_gs = price_span.attributes.get("data-gs", "")
                    if not data_gs:
                        continue
                    
                    # Decode and extract IATA code
                    try:
                        decoded = base64.b64decode(data_gs).decode("utf-8", errors="ignore")
                        
                        # Look for 3-letter airport codes in the decoded data
                        # Pattern: look for /m/XXXXX or :XXX where XXX is 3 uppercase letters
                        iata_matches = re.findall(r'[:/]([A-Z]{3})(?:[:/]|$)', decoded)
                        
                        if iata_matches:
                            # Usually the destination IATA is the second code (first is origin)
                            # Take the most common non-origin code
                            for iata in iata_matches:
                                if iata != origin:  # Skip origin airport
                                    if city_name not in city_to_iata or city_to_iata[city_name] == iata:
                                        city_to_iata[city_name] = iata
                                        iata_confidence[(city_name, iata)] += 1
                                    break
                            
                            cards_found += 1
                    except Exception:
                        pass
            
            except Exception as e:
                pass
        
        print(f"✓ {cards_found} mappings")
    
    print()
    print(f"Total unique city→IATA mappings found: {len(city_to_iata)}")
    print()
    
    # Filter out IATA codes (keep only city names)
    filtered_mappings = {}
    for city, iata in city_to_iata.items():
        # Skip if city name is already an IATA code
        if len(city) == 3 and city.isupper():
            continue
        
        # Skip if mapping is suspicious (city == iata)
        if city == iata:
            continue
        
        filtered_mappings[city] = iata
    
    print("=" * 80)
    print("CITY → IATA MAPPINGS (Copy-paste ready)")
    print("=" * 80)
    print()
    
    # Sort by confidence (most common first)
    sorted_mappings = sorted(
        filtered_mappings.items(),
        key=lambda x: iata_confidence.get((x[0], x[1]), 0),
        reverse=True
    )
    
    for city, iata in sorted_mappings:
        confidence = iata_confidence.get((city, iata), 0)
        print(f"'{city}': '{iata}',  # {confidence}x")
    
    print()
    print("=" * 80)
    print(f"✅ Found {len(filtered_mappings)} city→IATA mappings")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    num_origins = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    asyncio.run(extract_iata_mappings(num_origins))

