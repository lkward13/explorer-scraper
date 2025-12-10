#!/usr/bin/env python3
"""
Test parallel execution at different scales.

Usage:
    python worker/test_parallel.py --phase 1  # 2 origins, 1 browser (local test)
    python worker/test_parallel.py --phase 2  # 5 origins, 2 browsers
    python worker/test_parallel.py --phase 3  # 10 origins, 4 browsers
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from worker.parallel_executor import ParallelWorkerPool
from explore_scraper.cli import run as explore_run

# Test configurations for each phase
PHASES = {
    1: {
        'name': 'Baseline (local test)',
        'origins': ['PHX'],
        'browsers': 1,
        'deals_per_origin': 2,
        'regions': ['europe'],  # Just 1 region for speed
        'description': 'Debug test: 1 origin, 1 region, 1 browser, 2 expansions (first verbose)'
    },
    2: {
        'name': 'Small parallel',
        'origins': ['PHX', 'DFW'],
        'browsers': 2,
        'deals_per_origin': 2,
        'regions': ['europe'],  # Just 1 region for speed
        'description': 'Test 2 browsers in parallel: 2 origins, 1 region, 2 expansions per browser'
    },
    3: {
        'name': 'Full workflow test',
        'origins': ['PHX', 'DFW', 'LAX', 'ORD'],
        'browsers': 10,  # More browsers, fewer expansions each
        'deals_per_origin': 5,
        'regions': ['central_america', 'south_america', 'caribbean', 'europe', 'africa', 'asia', 'oceania', 'middle_east'],  # All except North America
        'description': 'Test 10 browsers: 4 origins, 8 regions (no North America), 2 expansions per browser'
    },
    4: {
        'name': 'Production scale test',
        'origins': ['DFW', 'ATL', 'PHX', 'ORD', 'OKC', 'BOS', 'DEN'],
        'browsers': 7,
        'deals_per_origin': 5,
        'description': 'Test at 7% of production scale: 7 origins, 7 browsers, 35 expansions'
    },
    5: {
        'name': 'Large scale test',
        'origins': ['DFW', 'ATL', 'PHX', 'ORD', 'OKC', 'BOS', 'DEN', 'LAX', 'JFK', 'MIA', 
                    'SEA', 'LAS', 'MCO', 'EWR', 'SFO', 'IAH', 'MSP', 'DTW', 'PHL', 'CLT',
                    'SAN', 'TPA', 'PDX', 'STL'],
        'browsers': 7,
        'deals_per_origin': 5,
        'description': 'Test at 24% of production scale: 24 origins, 7 browsers (staggered start), all 9 regions, 120 expansions'
    },
}


async def run_explore_for_origin(origin: str, regions: List[str] = None, verbose: bool = False) -> List[dict]:
    """
    Run Explore scraper for a single origin across all regions IN PARALLEL.
    
    Args:
        origin: Airport code (e.g., 'PHX')
        regions: List of regions to search, or None for default regions
        verbose: Print progress
    
    Returns:
        List of deal cards
    """
    if regions is None:
        regions = ['north_america', 'central_america', 'south_america', 'caribbean', 
                   'europe', 'africa', 'asia', 'oceania', 'middle_east']
    
    async def scrape_region(region: str, retry_count: int = 0, max_retries: int = 1):
        """Scrape a single region with retry logic."""
        try:
            # Import the programmatic TFS generator
            from explore_scraper.region_tfs_generator import build_explore_url_for_region
            
            # Build TFS URL programmatically (no pre-collected data needed)
            tfs_url = build_explore_url_for_region(origin, region)
            
            result = await explore_run(
                tfs_url=tfs_url,
                tfs_blob=None,
                origin_airport=None,  # Not needed when using tfs_url
                region=None,  # Not needed when using tfs_url
                html_file=None,
                use_browser=True,  # Browser required (HTTP consistently blocked)
                enhanced_mode=False,
                hl='en',
                gl='us',
                proxy=None,
                max_bytes=100_000_000,
                timeout=120.0,
                verbose=False
            )
            
            # Result is a list of cards
            cards = result if isinstance(result, list) else []
            
            # If we got 0 cards and haven't retried yet, try once more (likely rate limited)
            if len(cards) == 0 and retry_count < max_retries:
                if verbose:
                    print(f"  ⟳ {origin} → {region}: Got 0 cards, retrying ({retry_count + 1}/{max_retries})")
                await asyncio.sleep(10)  # Wait 10 seconds to let rate limit reset
                return await scrape_region(region, retry_count + 1, max_retries)
            
            # Add origin and search_region to each card
            for card in cards:
                if isinstance(card, dict):
                    card['origin'] = origin
                    card['search_region'] = region
            
            return cards
        
        except Exception as e:
            error_msg = str(e)
            
            # Special handling for rate limiting (no cards found)
            if 'No destination cards found' in error_msg:
                if retry_count < max_retries:
                    print(f"  ⟳ {origin} → {region}: Rate limited, waiting 60s before retry...")
                    await asyncio.sleep(60)  # Wait 1 minute to let rate limit reset
                    return await scrape_region(region, retry_count + 1, max_retries)
                else:
                    print(f"  ✗ {origin} → {region}: Rate limited (max retries reached)")
                    return []
            
            # Retry on connection/network errors
            if retry_count < max_retries and any(err in error_msg for err in ['ERR_SOCKET', 'net::ERR', 'timeout', 'Connection', 'closed']):
                if verbose:
                    print(f"  ⟳ {origin} → {region}: Retry {retry_count + 1}/{max_retries} ({error_msg[:30]})")
                await asyncio.sleep(5)  # Wait 5 seconds before retry
                return await scrape_region(region, retry_count + 1, max_retries)
            
            if verbose:
                print(f"  ✗ {origin} → {region}: {error_msg[:50]}")
            return []
    
    # Scrape regions SEQUENTIALLY to avoid too many browsers at once
    # (Origins are still parallel, but regions within each origin are sequential)
    all_cards = []
    for region in regions:
        cards = await scrape_region(region)
        all_cards.extend(cards)
        if verbose:
            print(f"  ✓ {origin} → {region}: {len(cards)} cards")
    
    return all_cards


def select_top_deals_per_origin(cards: List[dict], deals_per_origin: int, region_filter: str = None) -> List[dict]:
    """
    Select top N deals per region per origin, with regional diversity.
    
    Strategy: Take top deals_per_origin from EACH region to ensure we check
    Asia/Australia/etc even if Europe/Caribbean are cheaper overall.
    
    This means if deals_per_origin=5 and we have 9 regions, we'll expand
    up to 45 deals per origin (5 × 9 regions).
    
    Args:
        cards: List of deal cards from Explore
        deals_per_origin: Number of deals to select PER REGION (not total)
        region_filter: Optional region to filter by (e.g., 'europe')
    
    Returns:
        Selected deals ready for expansion
    """
    # City to IATA mapping for common destinations
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
        'Paphos': 'PFO', 'Dubrovnik': 'DBV', 'Moscow': 'SVO', 'Rovaniemi': 'RVN',
        'Santorini': 'JTR', 'Glasgow': 'GLA', 'Malta': 'MLA', 'Mykonos': 'JMK',
        'Manchester': 'MAN', 'Bordeaux': 'BOD', 'Luxembourg': 'LUX', 'Majorca': 'PMI',
        
        # Eastern Europe
        'Kraków': 'KRK', 'Florence': 'FLR', 'Naples': 'NAP', 'Venice': 'VCE',
        'Prague': 'PRG', 'Budapest': 'BUD', 'Vienna': 'VIE', 'Warsaw': 'WAW',
        'Copenhagen': 'CPH', 'Oslo': 'OSL', 'Brussels': 'BRU',
        'Frankfurt': 'FRA', 'Munich': 'MUC', 'Berlin': 'BER',
        
        # Caribbean & Central America
        'San Juan': 'SJU', 'Aruba': 'AUA', 'Cayman Islands': 'GCM', 'Anguilla': 'AXA',
        'El Yunque National Forest': 'SJU',  # Use San Juan for El Yunque
        'Cancun': 'CUN', 'Cancún': 'CUN',
        'Punta Cana': 'PUJ', 'La Romana': 'LRM',
        'Sint Maarten': 'SXM',
        'Saint Lucia': 'UVF', 'Barbados': 'BGI', 'Bonaire': 'BON', 'Curaçao': 'CUR',
        'Granada': 'GRX', 'San Salvador': 'SAL', 'Boquete': 'DAV',
        'Placencia': 'PLJ', 'San Juan del Sur': 'MGA',
        
        # Central America
        'Guatemala City': 'GUA', 'Antigua Guatemala': 'GUA',
        'Lake Atitlán': 'GUA', 'Semuc Champey': 'GUA', 'Panajachel': 'GUA',
        
        # South America
        'Bogotá': 'BOG', 'Cartagena': 'CTG',
        'Cuenca': 'CUE', 'Guayaquil': 'GYE',
        'Monteverde': 'SJO',  # Costa Rica - use San Jose
        'Punta del Este': 'PDP', 'Salvador': 'SSA', 'Santa Marta': 'SMR',
        'Rio de Janeiro': 'GIG', 'Salta': 'SLA', 'Brasília': 'BSB',
        'São Paulo': 'GRU', 'Mendoza': 'MDZ', 'Buenos Aires': 'EZE',
        'Cusco': 'CUZ', 'Manaus': 'MAO', 'Ushuaia': 'USH', 'Valparaíso': 'SCL',
        
        # Asia
        'Tokyo': 'NRT', 'Sydney': 'SYD',
        'Hong Kong': 'HKG',
        'Taipei City': 'TPE', 'Taipei': 'TPE',
        'Hyderabad': 'HYD',
        'Jerusalem': 'TLV', 'Tel Aviv-Yafo': 'TLV', 'Dubai': 'DXB', 'Abu Dhabi': 'AUH',
        'Bahrain': 'BAH', 'Antalya': 'AYT', 'Cappadocia': 'ASR', 'Salalah': 'SLL',
        'Petra': 'AMM', 'Tehran': 'IKA', 'Riyadh': 'RUH', 'Kuwait City': 'KWI',
        'Erbil': 'EBL', 'Doha': 'DOH', 'Amman': 'AMM', 'Sharjah': 'SHJ',
        'Bali': 'DPS', 'Phuket': 'HKT', 'Chiang Mai': 'CNX', 'Hanoi': 'HAN',
        'Ho Chi Minh City': 'SGN', 'Siem Reap': 'REP', 'Kathmandu': 'KTM',
        'Colombo': 'CMB', 'Manila': 'MNL', 'Cebu': 'CEB', 'Seoul': 'ICN',
        'Osaka': 'KIX', 'Bangkok': 'BKK', 'Singapore': 'SIN', 'Kuala Lumpur': 'KUL',
        'Jakarta': 'CGK', 'Delhi': 'DEL', 'Mumbai': 'BOM', 'Bangalore': 'BLR',
        
        # Oceania
        'Auckland': 'AKL', 'Christchurch': 'CHC', 'Queenstown': 'ZQN',
        'Melbourne': 'MEL', 'Brisbane': 'BNE', 'Perth': 'PER', 'Fiji': 'NAN',
        'Rangiroa': 'RGI',
        
        # Africa
        'Cape Town': 'CPT',
        'Stellenbosch': 'CPT', 'Hermanus': 'CPT', 'Franschhoek': 'CPT', 'Paarl': 'CPT',
        'Marrakech': 'RAK', 'Casablanca': 'CMN', 'Nairobi': 'NBO', 'Zanzibar': 'ZNZ',
        'Johannesburg': 'JNB', 'Durban': 'DUR', 'Victoria Falls': 'VFA',
        'Addis Ababa': 'ADD', 'Cairo': 'CAI', 'Luxor': 'LXR', 'Sharm el-Sheikh': 'SSH',
        
        # French Polynesia
        'Tahiti': 'PPT', "Mo'orea": 'MOZ', 'Bora Bora': 'BOB',
        'Raiatea': 'RFP', "Taha'a": 'RFP', 'Huahine-Iti': 'HUH',
        
        # North America
        'Mexico City': 'MEX', 'Halifax': 'YHZ', 'Charlottetown': 'YYG',
        'Montreal': 'YUL', 'Anchorage': 'ANC', 'Puerto Vallarta': 'PVR',
        'Honolulu': 'HNL', 'Québec City': 'YQB', 'San Diego': 'SAN',
        'Washington, D.C.': 'DCA', 'New Orleans': 'MSY', 'Toronto': 'YYZ',
        'Kauai': 'LIH', 'Bozeman': 'BZN', 'Fairbanks': 'FAI',
        "Peggy's Cove": 'YHZ', 'Denali National Park and Preserve': 'FAI',
        'Hawaiʻi Volcanoes National Park': 'ITO', 'Haleiwa': 'HNL',
        
        # Additional Caribbean/Central America
        'Roatán': 'RTB', 'Puerto Plata': 'POP', 'Montego Bay': 'MBJ',
        'Ocho Rios': 'MBJ', 'Negril': 'MBJ', 'Providenciales': 'PLS',
        'Freeport': 'FPO', 'Nassau': 'NAS', 'Antigua': 'ANU',
        'Nosara': 'NOB', 'Puntarenas': 'SJO', 'Dominical': 'SJO',
        'Parque Nacional Volcán Arenal': 'SJO', 'Parque Nacional Tortuguero': 'SJO',
        'Parque Nacional Volcán Tenorio': 'LIR', 'Copan Ruinas': 'SAP',
        'Quetzaltenango': 'GUA', 'León': 'MGA', 'San Juan del Sur': 'MGA',
        
        # Additional South America
        'Machu Picchu': 'CUZ', 'Historic Sanctuary of Machu Picchu': 'CUZ',
        'Ollantaytambo': 'CUZ', 'Parque Nacional Natural Tayrona': 'SMR',
        'Puerto Viejo de Talamanca': 'SJO',
        
        # Additional Asia
        'Kyoto': 'KIX', 'Beijing': 'PEK', 'Da Nang': 'DAD', 'Kochi': 'COK',
        'Bengaluru': 'BLR', 'Agra': 'DEL', 'Jaipur': 'JAI', 'Goa': 'GOI',
        
        # Additional Europe
        'Mykonos': 'JMK', 'Luxembourg': 'LUX', 'Bordeaux': 'BOD',
        'Manchester': 'MAN', 'Glasgow': 'GLA', 'Kazan': 'KZN',
        'Terceira Island': 'TER', 'Pico Island': 'PIX', 'Longyearbyen': 'LYR',
        'Gudauri': 'TBS',
        
        # Additional Middle East/Africa
        'Giza': 'CAI', 'Bosphorus': 'IST', 'Dead Sea': 'AMM',
        'Pretoria': 'JNB', 'Pilanesberg National Park': 'JNB',
        'Cradle of Humankind': 'JNB', 'Gansbaai': 'CPT', 'Knysna': 'GRJ',
        
        # Special regions
        'Amalfi': 'NAP',  # Amalfi Coast uses Naples airport
    }
    
    # Filter by region if specified
    if region_filter:
        cards = [c for c in cards if c.get('search_region') == region_filter]
    
    # Group by origin
    by_origin = {}
    for card in cards:
        origin = card.get('origin')
        if origin not in by_origin:
            by_origin[origin] = []
        by_origin[origin].append(card)
    
    # Select top N per region per origin (ensures regional diversity)
    selected = []
    for origin, origin_cards in by_origin.items():
        # Group by region first to ensure diversity
        by_region = {}
        for card in origin_cards:
            region = card.get('search_region', 'unknown')
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(card)
        
        # Take top deals_per_origin from EACH region
        # This means we'll expand up to (deals_per_origin × num_regions) deals per origin
        origin_selected = []
        for region, region_cards in by_region.items():
            # Sort by price and take top N from this region
            region_sorted = sorted(region_cards, key=lambda x: x.get('min_price', 9999))
            origin_selected.extend(region_sorted[:deals_per_origin])
        
        # Sort final selection by price (for logging/display purposes)
        sorted_cards = sorted(origin_selected, key=lambda x: x.get('min_price', 9999))
        # DON'T limit to deals_per_origin here - we want ALL selected deals from all regions!
        
        # Convert to expansion format
        for card in sorted_cards:
            dest_name = card.get('destination')
            dest_iata = CITY_TO_IATA.get(dest_name, dest_name)  # Fallback to name if not in map
            
            # Track if this is a city name (not in mapping and not already an IATA code)
            is_unmapped_city = (dest_name != dest_iata and dest_name not in CITY_TO_IATA and len(dest_name) > 3)
            
            selected.append({
                'origin': origin,
                'destination': dest_iata,
                'destination_name': dest_name,  # Keep original name for logging
                'start_date': card.get('start_date'),
                'end_date': card.get('end_date'),
                'price': card.get('min_price'),
                'search_region': card.get('search_region'),
                'is_unmapped_city': is_unmapped_city
            })
    
    return selected


async def run_test_phase(phase: int, verbose: bool = True, override_config: dict = None, use_api: bool = False, save_to_db: bool = False):
    """
    Run a specific test phase.
    
    Args:
        phase: Phase number (1-3)
        verbose: Print detailed progress
        override_config: Optional config dict to override phase defaults
        use_api: Whether to use API-based expansion
        save_to_db: Whether to save results to PostgreSQL database
    
    Returns:
        Test results
    """
    if phase not in PHASES:
        print(f"Invalid phase: {phase}. Must be 1-3.")
        return None
    
    config = override_config if override_config else PHASES[phase]
    
    # Support separate browser counts for explore vs expansion
    explore_browsers = config.get('explore_browsers', config['browsers'])
    expansion_browsers = config['browsers']
    
    print(f"\n{'='*80}")
    print(f"PHASE {phase}: {config['name']}")
    print(f"{'='*80}")
    print(f"Description:      {config['description']}")
    print(f"Origins:          {len(config['origins'])} ({', '.join(config['origins'])})")
    print(f"Explore browsers: {explore_browsers}")
    print(f"Expansion browsers: {expansion_browsers}")
    print(f"Deals per origin: {config['deals_per_origin']}")
    print(f"Expected deals:   {len(config['origins']) * config['deals_per_origin']}")
    print(f"{'='*80}\n")
    
    overall_start = datetime.now()
    
    # Database setup (if enabled)
    db = None
    run_id = None
    if save_to_db:
        try:
            from database.db import DealsDatabase
            from database.config import get_connection_string
            db = DealsDatabase(get_connection_string())
            run_id = db.create_scrape_run(len(config['origins']))
            if verbose:
                print(f"[DB] Created scrape run #{run_id}")
        except Exception as e:
            print(f"[DB] Warning: Could not connect to database: {e}")
            print(f"[DB] Continuing without database storage...")
            db = None
    
    # STEP 1: Run Explore for all origins (BATCHED PARALLEL with staggered starts)
    print(f"STEP 1: Explore Scraping (Batched Parallel)")
    print(f"-" * 80)
    explore_start = datetime.now()
    
    regions_to_scrape = config.get('regions', None)  # Use config regions if specified
    
    # Batch origins to avoid overwhelming the system (smaller batches = faster completion)
    BATCH_SIZE = 5  # Process 5 origins at a time (with retry logic for failures)
    origins = config['origins']
    all_cards = []
    
    for batch_num in range(0, len(origins), BATCH_SIZE):
        batch = origins[batch_num:batch_num + BATCH_SIZE]
        batch_name = f"Batch {batch_num//BATCH_SIZE + 1}/{(len(origins) + BATCH_SIZE - 1)//BATCH_SIZE}"
        
        print(f"\n{batch_name}: Exploring {len(batch)} origins in parallel...")
        
        # Stagger browser starts to avoid connection issues
        async def run_with_stagger(origin, delay):
            if delay > 0:
                await asyncio.sleep(delay)
            return await run_explore_for_origin(origin, regions=regions_to_scrape, verbose=False)
        
        # Run batch in parallel with 3-second stagger between each origin
        batch_tasks = [
            run_with_stagger(origin, i * 3)
            for i, origin in enumerate(batch)
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(batch_results):
            origin = batch[i]
            if isinstance(result, Exception):
                print(f"  ✗ {origin}: Failed - {str(result)[:50]}")
                # Retry failed origin once with delay
                try:
                    print(f"     Waiting 30s before retry...")
                    await asyncio.sleep(30)  # Give rate limits time to reset
                    print(f"     Retrying {origin}...")
                    retry_result = await run_explore_for_origin(origin, regions=regions_to_scrape, verbose=False)
                    all_cards.extend(retry_result)
                    print(f"     ✓ {origin}: {len(retry_result)} cards (retry succeeded)")
                except Exception as e:
                    print(f"     ✗ {origin}: Retry failed - {str(e)[:50]}")
            else:
                all_cards.extend(result)
                print(f"  ✓ {origin}: {len(result)} cards")
        
        # Add delay between batches to avoid rate limiting
        if batch_num + BATCH_SIZE < len(origins):  # Not the last batch
            print(f"  ⏸️  Waiting 15 seconds before next batch...")
            await asyncio.sleep(15)
    
    explore_time = (datetime.now() - explore_start).total_seconds()
    print(f"\n✓ Explore complete: {len(all_cards)} cards in {explore_time:.1f}s ({explore_time/60:.1f} min)")
    
    # STEP 2: Select top deals
    print(f"\nSTEP 2: Deal Selection")
    print(f"-" * 80)
    
    # Scrape all regions (no filtering)
    region_filter = None
    
    expansion_candidates = select_top_deals_per_origin(
        all_cards,
        deals_per_origin=config['deals_per_origin'],
        region_filter=region_filter
    )
    
    print(f"Selected {len(expansion_candidates)} deals for expansion:")
    by_origin = {}
    for candidate in expansion_candidates:
        origin = candidate['origin']
        by_origin[origin] = by_origin.get(origin, 0) + 1
    
    for origin, count in sorted(by_origin.items()):
        print(f"  {origin}: {count} deals")
    
    # STEP 3: Parallel expansion
    print(f"\nSTEP 3: Parallel Expansion")
    print(f"-" * 80)
    
    expansion_start = datetime.now()
    
    # Check if we should use API mode (parameter overrides config)
    use_api_mode = use_api if use_api else config.get('use_api', False)
    
    worker_pool = ParallelWorkerPool(
        num_browsers=expansion_browsers,  # Use expansion_browsers for expansion phase
        verbose=verbose,
        use_api=use_api_mode
    )
    
    results = await worker_pool.process_expansions(expansion_candidates)
    
    expansion_time = (datetime.now() - expansion_start).total_seconds()
    
    # Log unmapped cities that returned 0 results
    unmapped_cities_with_zero_results = []
    for candidate in expansion_candidates:
        if candidate.get('is_unmapped_city'):
            # Check if this expansion returned 0 results
            matching_result = next((r for r in results if r['origin'] == candidate['origin'] and r['destination'] == candidate['destination']), None)
            if matching_result and len(matching_result.get('similar_dates', [])) == 0:
                unmapped_cities_with_zero_results.append({
                    'city_name': candidate['destination_name'],
                    'used_code': candidate['destination'],
                    'route': f"{candidate['origin']}→{candidate['destination_name']}"
                })
    
    if unmapped_cities_with_zero_results:
        print(f"\n⚠️  UNMAPPED CITIES WITH 0 RESULTS (need IATA codes):")
        seen = set()
        for item in unmapped_cities_with_zero_results:
            if item['city_name'] not in seen:
                print(f"  '{item['city_name']}': '???',  # Example route: {item['route']}")
                seen.add(item['city_name'])
    
    # STEP 4: Summary
    total_time = (datetime.now() - overall_start).total_seconds()
    
    print(f"\n{'='*80}")
    print(f"PHASE {phase} SUMMARY")
    print(f"{'='*80}")
    print(f"Explore time:         {explore_time:.1f}s ({explore_time/60:.1f} min)")
    print(f"Expansion time:       {expansion_time:.1f}s ({expansion_time/60:.1f} min)")
    print(f"Total time:           {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"\nExpansions attempted: {len(expansion_candidates)}")
    print(f"Expansions succeeded: {len(results)}")
    if len(expansion_candidates) > 0:
        print(f"Success rate:         {len(results)/len(expansion_candidates)*100:.1f}%")
    else:
        print(f"Success rate:         N/A (no expansions attempted)")
    
    # Valid deals (after filtering)
    valid_deals = []
    for result in results:
        expansion = result.get('result', {})
        similar_count = len(expansion.get('similar_deals', []))
        if similar_count >= 5:  # Minimum threshold
            valid_deals.append(result)
    
    print(f"\nValid deals (≥5 dates): {len(valid_deals)}")
    print(f"{'='*80}\n")
    
    # STEP 5: Save to database (if enabled)
    if db and run_id:
        print(f"STEP 5: Saving to Database")
        print(f"-" * 80)
        
        try:
            # Import URL builder
            from explore_scraper.tfs_builder import build_round_trip_flight_url
            
            # Transform results to database format
            deals_to_insert = []
            for result in results:
                item = result['item']
                similar_deals = result['result'].get('similar_deals', [])
                
                # Only save valid deals (≥5 similar dates)
                if len(similar_deals) >= 5:
                    # Save ALL similar dates (not just one)
                    for deal in similar_deals:
                        # Generate Google Flights URL for this specific date combo
                        url = build_round_trip_flight_url(
                            origin=item['origin'],
                            destination=item['destination'],
                            outbound_date=deal['outbound_date'],
                            return_date=deal['return_date']
                        )
                        
                        deals_to_insert.append({
                            'origin': item['origin'],
                            'destination': item['destination'],
                            'destination_city': item.get('destination_name'),  # Use original city name
                            'outbound_date': deal['outbound_date'],
                            'return_date': deal['return_date'],
                            'price': deal['price'],
                            'reference_price': item['price'],
                            'search_region': item.get('search_region'),
                            'duration': None,  # Not available in expansion phase
                            'similar_date_count': len(similar_deals),
                            'google_flights_url': url,
                            'scrape_run_id': run_id
                        })
            
            # Insert deals
            if deals_to_insert:
                inserted = db.insert_expanded_deals(deals_to_insert)
                print(f"✓ Inserted {inserted} deals ({len(valid_deals)} routes × avg {inserted//len(valid_deals) if valid_deals else 0} dates each)")
            else:
                print(f"No valid deals to insert")
            
            # Update scrape run stats
            db.complete_scrape_run(run_id, {
                'cards_found': len(all_cards),
                'expansions_attempted': len(expansion_candidates),
                'expansions_succeeded': len(results),
                'valid_deals': len(valid_deals)
            })
            
            # Show database stats
            stats = db.get_stats()
            print(f"\n📊 Database Statistics:")
            print(f"  Total deals: {stats.get('total_deals', 0)}")
            print(f"  Unposted deals: {stats.get('unposted_deals', 0)}")
            print(f"  Unique routes: {stats.get('unique_routes', 0)}")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"[DB] Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            if run_id:
                try:
                    db.complete_scrape_run(run_id, {
                        'cards_found': len(all_cards),
                        'expansions_attempted': len(expansion_candidates),
                        'expansions_succeeded': len(results),
                        'valid_deals': 0
                    })
                except:
                    pass
    
    return {
        'phase': phase,
        'config': config,
        'explore_time': explore_time,
        'expansion_time': expansion_time,
        'total_time': total_time,
        'cards_found': len(all_cards),
        'expansions_attempted': len(expansion_candidates),
        'expansions_succeeded': len(results),
        'valid_deals': len(valid_deals),
        'expanded_deals': results  # Add full results for detailed analysis
    }


def main():
    parser = argparse.ArgumentParser(
        description="Test parallel execution at different scales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python worker/test_parallel.py --phase 1    # Test locally (2 origins, 1 browser)
  python worker/test_parallel.py --phase 2    # Small parallel (5 origins, 2 browsers)
  python worker/test_parallel.py --phase 3    # Medium scale (10 origins, 4 browsers)
        """
    )
    
    parser.add_argument(
        '--phase',
        type=int,
        required=True,
        choices=[1, 2, 3, 4, 5],
        help='Test phase to run (1=baseline, 2=small parallel, 3=full workflow, 4=production scale)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce verbosity'
    )
    
    parser.add_argument(
        '--origins',
        type=int,
        help='Override number of origins to test'
    )
    
    parser.add_argument(
        '--deals-per-origin',
        type=int,
        help='Override deals per origin to expand'
    )
    
    args = parser.parse_args()
    
    # Override phase config if specified
    if args.origins or args.deals_per_origin:
        base_config = PHASES[args.phase].copy()
        if args.origins:
            base_config['origins'] = base_config['origins'][:args.origins]
        if args.deals_per_origin:
            base_config['deals_per_origin'] = args.deals_per_origin
        
        result = asyncio.run(run_test_phase(
            args.phase,
            verbose=not args.quiet,
            override_config=base_config
        ))
    else:
        result = asyncio.run(run_test_phase(args.phase, verbose=not args.quiet))
    
    if result:
        print("\n✅ Test complete!")
        print(f"\nNext steps:")
        if args.phase < 3:
            print(f"  Run phase {args.phase + 1}: python worker/test_parallel.py --phase {args.phase + 1}")
        else:
            print("  All local phases complete! Ready for server deployment.")


if __name__ == '__main__':
    main()

