#!/usr/bin/env python3
"""
Run test and show results with clickable URLs inline.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from explore_scraper.cli import run as explore_run
from scripts.expand_dates_api import expand_deal_via_api
import json
import base64

# City to IATA mapping
CITY_TO_IATA = {
    'Dublin': 'DUB', 'Barcelona': 'BCN', 'Madrid': 'MAD', 'Lisbon': 'LIS',
    'Helsinki': 'HEL', 'Amsterdam': 'AMS', 'Zürich': 'ZRH', 'Stockholm': 'ARN',
    'Paris': 'CDG', 'London': 'LHR', 'Rome': 'FCO', 'Athens': 'ATH',
    'Berlin': 'BER', 'Prague': 'PRG', 'Vienna': 'VIE', 'Budapest': 'BUD',
    'Copenhagen': 'CPH', 'Oslo': 'OSL', 'Brussels': 'BRU', 'Milan': 'MXP',
    'Warsaw': 'WAW', 'Istanbul': 'IST', 'Edinburgh': 'EDI', 'Munich': 'MUC'
}

async def show_results():
    print("="*80)
    print("LIVE TEST: ATL → Europe with Clickable URLs")
    print("="*80)
    print()
    
    # Load region TFS
    region_file = Path("data/region_tfs/ATL.json")
    with open(region_file, 'r') as f:
        region_data = json.load(f)
    
    tfs = region_data["regions"]["europe"]
    
    print(f"[1/3] Exploring deals from ATL to Europe...")
    
    # Fetch with browser
    cards = await explore_run(
        tfs_url=None,
        tfs_blob=None,
        origin_airport='ATL',
        region='europe',
        html_file=None,
        use_browser=True,
        enhanced_mode=False,
        hl='en',
        gl='us',
        proxy=None,
        max_bytes=100_000_000,
        timeout=120.0,
        verbose=False
    )
    
    print(f"✓ Found {len(cards)} deals\n")
    
    # Sort by price and take top 3
    cards.sort(key=lambda x: x.get('min_price', 9999))
    top_cards = cards[:3]
    
    print(f"[2/3] Expanding top 3 deals (9-month API)...\n")
    
    all_results = []
    
    for i, card in enumerate(top_cards):
        dest_name = card.get('destination', 'Unknown')
        dest_iata = CITY_TO_IATA.get(dest_name, dest_name)
        price = card.get('min_price')
        start_date = card.get('start_date')
        end_date = card.get('end_date')
        
        print(f"  {i+1}. ATL → {dest_iata} ({dest_name}) - ${price}")
        
        # Expand
        expanded = await expand_deal_via_api(
            origin='ATL',
            destination=dest_iata,
            outbound_date=start_date,
            return_date=end_date,
            original_price=price,
            price_threshold=1.15,
            verbose=False
        )
        
        if expanded:
            expanded.sort(key=lambda x: x['price'])
            print(f"     ✓ Found {len(expanded)} similar deals\n")
            
            all_results.append({
                'origin': 'ATL',
                'destination': dest_iata,
                'destination_name': dest_name,
                'reference_price': price,
                'reference_start': start_date,
                'reference_end': end_date,
                'similar_deals': expanded
            })
        else:
            print(f"     ✗ No similar deals\n")
    
    # Show results with URLs
    print("="*80)
    print("[3/3] CLICKABLE URLS FOR TOP DEALS")
    print("="*80)
    print()
    
    for i, result in enumerate(all_results):
        similar = result['similar_deals']
        
        print(f"{i+1}. {result['origin']} → {result['destination']} ({result['destination_name']})")
        print(f"   Original: ${result['reference_price']} | {result['reference_start']} to {result['reference_end']}")
        print(f"   Found {len(similar)} similar deals")
        print()
        
        # Show top 5 with URLs
        print(f"   Top 5 cheapest dates:")
        for j, deal in enumerate(similar[:5]):
            # Build simple search URL (Google will find the flights)
            url = f"https://www.google.com/travel/flights?q=flights+from+{result['origin']}+to+{result['destination']}+on+{deal['outbound_date']}+return+{deal['return_date']}&hl=en&gl=us"
            
            savings = result['reference_price'] - deal['price']
            savings_str = f"(save ${savings})" if savings > 0 else f"(+${abs(savings)})"
            
            print(f"   {j+1}. ${deal['price']:>3} {savings_str:>12} | {deal['outbound_date']} to {deal['return_date']}")
            print(f"      🔗 {url}")
            print()
        
        print()

if __name__ == '__main__':
    asyncio.run(show_results())

