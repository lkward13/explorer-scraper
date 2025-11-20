#!/usr/bin/env python3
"""
Show detailed deals from DFW → Europe with 9-month expansion.
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from explore_scraper.cli import run as explore_run
from scripts.expand_dates_api import expand_deal_via_api

# City to IATA mapping
CITY_TO_IATA = {
    'Dublin': 'DUB', 'Barcelona': 'BCN', 'Madrid': 'MAD', 'Lisbon': 'LIS',
    'Helsinki': 'HEL', 'Amsterdam': 'AMS', 'Zürich': 'ZRH', 'Stockholm': 'ARN',
    'Paris': 'CDG', 'London': 'LHR', 'Rome': 'FCO', 'Athens': 'ATH',
    'Berlin': 'BER', 'Prague': 'PRG', 'Vienna': 'VIE', 'Budapest': 'BUD',
    'Copenhagen': 'CPH', 'Oslo': 'OSL', 'Brussels': 'BRU', 'Milan': 'MXP',
    'Warsaw': 'WAW', 'Istanbul': 'IST', 'Edinburgh': 'EDI', 'Munich': 'MUC'
}

async def show_dfw_europe_deals():
    print("="*80)
    print("DFW → EUROPE DEALS (9-month API expansion)")
    print("="*80)
    print()
    
    # Load region TFS
    region_file = Path("data/region_tfs/DFW.json")
    with open(region_file, 'r') as f:
        region_data = json.load(f)
    
    tfs = region_data["regions"]["europe"]
    url = f"https://www.google.com/travel/explore?tfs={tfs}&hl=en&gl=us&tfu=GgA"
    
    print(f"[1/2] Exploring deals from DFW to Europe...")
    print(f"URL: {url[:100]}...")
    print()
    
    # Fetch with browser (ENHANCED MODE for deal quality)
    # This clicks each card to extract "cheaper than usual" data
    cards = await explore_run(
        tfs_url=None,
        tfs_blob=None,
        origin_airport='DFW',
        region='europe',
        html_file=None,
        use_browser=True,
        enhanced_mode=True,  # Extract "cheaper than usual" data (slower but comprehensive)
        hl='en',
        gl='us',
        proxy=None,
        max_bytes=100_000_000,
        timeout=120.0,
        verbose=True  # Show progress
    )
    
    print(f"✓ Found {len(cards)} deals from DFW to Europe")
    print()
    
    # Sort by price and take top 5
    cards.sort(key=lambda x: x.get('min_price', 9999))
    top_cards = cards[:5]
    
    print("="*80)
    print("TOP 5 DEALS:")
    print("="*80)
    
    for i, card in enumerate(top_cards):
        dest_name = card.get('destination', 'Unknown')
        dest_iata = CITY_TO_IATA.get(dest_name, dest_name)
        price = card.get('min_price')
        start_date = card.get('start_date')
        end_date = card.get('end_date')
        deal_quality = card.get('deal_quality')
        deal_quality_amount = card.get('deal_quality_amount')
        
        print(f"\n{i+1}. DFW → {dest_iata} ({dest_name})")
        print(f"   Original: ${price} | {start_date} to {end_date}")
        if deal_quality:
            usual_price = price + deal_quality_amount
            discount_pct = int((deal_quality_amount / usual_price) * 100) if usual_price > 0 else 0
            print(f"   💰 {deal_quality} (usually ${usual_price}) — {discount_pct}% off")
        print(f"   {'─'*76}")
        
        # Expand this deal
        expanded = await expand_deal_via_api(
            origin='DFW',
            destination=dest_iata,
            outbound_date=start_date,
            return_date=end_date,
            original_price=price,
            price_threshold=1.15,
            verbose=False
        )
        
        if expanded:
            # Sort by price
            expanded.sort(key=lambda x: x['price'])
            
            # Show stats
            prices = [d['price'] for d in expanded]
            dates = [d['outbound_date'] for d in expanded]
            
            print(f"   ✓ Found {len(expanded)} similar deals (within 15% of ${price})")
            print(f"   Price range: ${min(prices)} - ${max(prices)} | Avg: ${sum(prices)/len(prices):.0f}")
            print(f"   Date range: {min(dates)} to {max(dates)}")
            
            # Count months
            from collections import Counter
            months = Counter([d[:7] for d in dates])
            print(f"   Months covered: {len(months)} ({', '.join(sorted(months.keys())[:3])}...)")
            
            # Show top 5 cheapest
            print(f"\n   Top 5 cheapest dates:")
            for j, exp_deal in enumerate(expanded[:5]):
                savings = price - exp_deal['price']
                savings_str = f"(save ${savings})" if savings > 0 else f"(+${abs(savings)})"
                print(f"     {j+1}. ${exp_deal['price']:>3} {savings_str:>12} | {exp_deal['outbound_date']} to {exp_deal['return_date']}")
        else:
            print(f"   ✗ No similar deals found within price threshold")
    
    print()
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(show_dfw_europe_deals())

