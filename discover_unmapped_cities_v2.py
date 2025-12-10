#!/usr/bin/env python3
"""
Discover unmapped cities from explore results.

Uses the existing test_parallel infrastructure to run explore,
then analyzes the results to find unmapped cities.
"""
import asyncio
import sys
from collections import defaultdict
from worker.test_parallel import run_test_phase

# Current mapping (will check against this)
CITY_TO_IATA = {
    # Western Europe
    'Dublin': 'DUB', 'Barcelona': 'BCN', 'Madrid': 'MAD', 'Lisbon': 'LIS',
    'Helsinki': 'HEL', 'Amsterdam': 'AMS', 'Zürich': 'ZRH', 'Stockholm': 'ARN',
    'Paris': 'CDG', 'London': 'LHR', 'Rome': 'FCO', 'Athens': 'ATH',
    'Milan': 'MXP', 'Porto': 'OPO', 'Nice': 'NCE', 'Edinburgh': 'EDI',
    'Geneva': 'GVA', 'Lyon': 'LYS', 'Toulouse': 'TLS', 'Bologna': 'BLQ',
    'Palermo': 'PMO', 'Catania': 'CTA', 'Seville': 'SVQ', 'Bilbao': 'BIO',
    'Valencia': 'VLC', 'Malaga': 'AGP', 'Reykjavik': 'KEF', 'Reykjavík': 'KEF',
    'Larnaca': 'LCA', 'Limassol': 'LCA', 'Nicosia': 'LCA', 'Ayia Napa': 'LCA',
    
    # Eastern Europe
    'Kraków': 'KRK', 'Florence': 'FLR', 'Naples': 'NAP', 'Venice': 'VCE',
    'Prague': 'PRG', 'Budapest': 'BUD', 'Vienna': 'VIE', 'Warsaw': 'WAW',
    'Copenhagen': 'CPH', 'Oslo': 'OSL', 'Brussels': 'BRU',
    'Frankfurt': 'FRA', 'Munich': 'MUC', 'Berlin': 'BER',
    
    # Caribbean & Central America
    'San Juan': 'SJU', 'Aruba': 'AUA', 'Cayman Islands': 'GCM', 'Anguilla': 'AXA',
    'El Yunque National Forest': 'SJU',
    'Cancun': 'CUN', 'Cancún': 'CUN',
    'Punta Cana': 'PUJ', 'La Romana': 'LRM',
    'Sint Maarten': 'SXM',
    
    # Central America
    'Guatemala City': 'GUA', 'Antigua Guatemala': 'GUA',
    'Lake Atitlán': 'GUA', 'Semuc Champey': 'GUA', 'Panajachel': 'GUA',
    
    # South America
    'Bogotá': 'BOG', 'Cartagena': 'CTG',
    'Cuenca': 'CUE', 'Guayaquil': 'GYE',
    'Monteverde': 'SJO',
    
    # Asia & Oceania
    'Tokyo': 'NRT', 'Sydney': 'SYD',
    'Hong Kong': 'HKG',
    'Taipei City': 'TPE', 'Taipei': 'TPE',
    'Hyderabad': 'HYD',
    
    # Africa
    'Cape Town': 'CPT',
    'Stellenbosch': 'CPT', 'Hermanus': 'CPT', 'Franschhoek': 'CPT', 'Paarl': 'CPT',
    
    # French Polynesia
    'Tahiti': 'PPT', "Mo'orea": 'MOZ', 'Bora Bora': 'BOB',
    'Raiatea': 'RFP', "Taha'a": 'RFP', 'Huahine-Iti': 'HUH',
    
    # Special regions
    'Amalfi': 'NAP',
}

async def discover_unmapped_cities(num_origins=20):
    """
    Run explore and discover all unmapped cities.
    
    Args:
        num_origins: Number of origins to test (more = more complete list)
    """
    print("=" * 80)
    print("UNMAPPED CITY DISCOVERY")
    print("=" * 80)
    print()
    print(f"Running explore on {num_origins} origins to discover unmapped cities...")
    print("This will take ~5 minutes (explore only, no expansion)")
    print()
    
    # Use top US airports for diversity
    origins = [
        'DFW', 'ATL', 'LAX', 'ORD', 'JFK', 'PHX', 'DEN', 'SEA', 'BOS', 'MIA',
        'SFO', 'LAS', 'MCO', 'EWR', 'CLT', 'IAH', 'FLL', 'DTW', 'PHL', 'LGA'
    ][:num_origins]
    
    # Import the explore function from test_parallel
    from worker.test_parallel import run_explore_for_origin
    
    all_cards = []
    for origin in origins:
        print(f"Exploring {origin}...", end=' ', flush=True)
        try:
            cards = await run_explore_for_origin(origin, regions=None, verbose=False)
            all_cards.extend(cards)
            print(f"✓ {len(cards)} cards")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print()
    print(f"Total cards collected: {len(all_cards)}")
    print()
    
    # Analyze destinations
    unmapped_by_region = defaultdict(set)
    destination_counts = defaultdict(int)
    
    for card in all_cards:
        dest = card.get('destination', '')
        region = card.get('search_region', 'unknown')
        
        # Check if it's unmapped
        is_iata = len(dest) == 3 and dest.isupper()
        is_mapped = dest in CITY_TO_IATA
        
        if not is_iata and not is_mapped and dest:
            unmapped_by_region[region].add(dest)
            destination_counts[dest] += 1
    
    # Output results
    print("=" * 80)
    print("UNMAPPED CITIES BY REGION")
    print("=" * 80)
    print()
    
    total_unmapped = sum(len(cities) for cities in unmapped_by_region.values())
    print(f"Found {total_unmapped} unmapped cities across {len(unmapped_by_region)} regions")
    print()
    
    for region in sorted(unmapped_by_region.keys()):
        cities = sorted(unmapped_by_region[region], key=lambda c: destination_counts[c], reverse=True)
        print(f"\n{region.upper()} ({len(cities)} cities):")
        print("-" * 80)
        for city in cities[:20]:  # Show top 20 per region
            count = destination_counts[city]
            print(f"  '{city}': '???',  # Found {count}x")
        if len(cities) > 20:
            print(f"  ... and {len(cities) - 20} more")
    
    print()
    print("=" * 80)
    print("COPY-PASTE READY FORMAT (Top 50 most common)")
    print("=" * 80)
    print()
    
    # Sort all cities by frequency
    all_cities = [(city, count, region) for region, cities in unmapped_by_region.items() 
                  for city in cities for count in [destination_counts[city]]]
    all_cities.sort(key=lambda x: x[1], reverse=True)
    
    print("# Add these to CITY_TO_IATA in worker/test_parallel.py:")
    print()
    
    current_region = None
    for i, (city, count, region) in enumerate(all_cities[:50]):
        if region != current_region:
            print(f"\n# {region.title()} ({count}x occurrences)")
            current_region = region
        print(f"'{city}': '???',  # {count}x")

if __name__ == "__main__":
    num_origins = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    asyncio.run(discover_unmapped_cities(num_origins))

