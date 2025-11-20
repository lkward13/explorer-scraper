#!/usr/bin/env python3
"""
Test DFW to Europe - full workflow with real deals.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from explore_scraper.cli import run as explore_run
from scripts.expand_dates_api import expand_deal_via_api

async def test_dfw_europe():
    print("="*80)
    print("TESTING: DFW → Europe")
    print("="*80)
    
    # Step 1: Explore deals from DFW to Europe
    print("\n[1/2] Exploring deals from DFW to Europe...")
    print("-"*80)
    
    # Use the CLI explore function (browser mode for sandbox compatibility)
    cards = await explore_run(
        tfs_url=None,
        tfs_blob=None,
        origin_airport='DFW',
        region='europe',
        html_file=None,
        use_browser=True,  # Use browser (works in sandbox)
        enhanced_mode=False,
        hl='en',
        gl='us',
        proxy=None,
        max_bytes=100_000_000,
        timeout=120.0,
        verbose=True
    )
    
    if not cards:
        print("\n✗ No deals found from DFW to Europe")
        return
    
    print(f"\n✓ Found {len(cards)} deals from DFW to Europe")
    
    # City to IATA mapping
    CITY_TO_IATA = {
        'Dublin': 'DUB', 'Barcelona': 'BCN', 'Madrid': 'MAD', 'Lisbon': 'LIS',
        'Helsinki': 'HEL', 'Amsterdam': 'AMS', 'Zürich': 'ZRH', 'Stockholm': 'ARN',
        'Paris': 'CDG', 'London': 'LHR', 'Rome': 'FCO', 'Athens': 'ATH',
        'Berlin': 'BER', 'Prague': 'PRG', 'Vienna': 'VIE', 'Budapest': 'BUD',
        'Copenhagen': 'CPH', 'Oslo': 'OSL', 'Brussels': 'BRU', 'Milan': 'MXP'
    }
    
    # Convert cards to deals
    deals = []
    for card in cards[:10]:  # Top 10
        dest_name = card.get('destination', 'Unknown')
        dest_iata = CITY_TO_IATA.get(dest_name, dest_name)
        
        deals.append({
            'origin': 'DFW',
            'destination': dest_iata,
            'destination_name': dest_name,
            'start_date': card.get('start_date'),
            'end_date': card.get('end_date'),
            'price': card.get('min_price')
        })
    
    print("\nTop 10 deals:")
    for i, deal in enumerate(deals):
        print(f"  {i+1}. {deal['origin']} → {deal['destination']} ({deal['destination_name']})")
        print(f"     ${deal['price']} | {deal['start_date']} to {deal['end_date']}")
    
    # Step 2: Expand the top 3 deals
    print("\n" + "="*80)
    print("[2/2] Expanding top 3 deals to find flexible dates (9 months)...")
    print("="*80)
    
    for i, deal in enumerate(deals[:3]):
        print(f"\n{'─'*80}")
        print(f"Deal {i+1}: {deal['origin']} → {deal['destination']} ({deal['destination_name']})")
        print(f"Original: ${deal['price']} | {deal['start_date']} to {deal['end_date']}")
        print(f"{'─'*80}")
        
        # Expand this deal
        expanded = await expand_deal_via_api(
            origin=deal['origin'],
            destination=deal['destination'],
            outbound_date=deal['start_date'],
            return_date=deal['end_date'],
            original_price=deal['price'],
            price_threshold=1.15,
            verbose=False
        )
        
        if expanded:
            # Sort by price
            expanded.sort(key=lambda x: x['price'])
            
            print(f"\n✓ Found {len(expanded)} similar deals (within 15% of ${deal['price']})")
            
            # Show price range
            prices = [d['price'] for d in expanded]
            print(f"  Price range: ${min(prices)} - ${max(prices)}")
            print(f"  Average: ${sum(prices) / len(prices):.0f}")
            
            # Show date range
            dates = [d['outbound_date'] for d in expanded]
            print(f"  Date range: {min(dates)} to {max(dates)}")
            
            # Count months
            from collections import Counter
            months = Counter([d[:7] for d in dates])
            print(f"  Months covered: {len(months)}")
            
            # Show top 10 cheapest
            print(f"\n  Top 10 cheapest dates:")
            for j, exp_deal in enumerate(expanded[:10]):
                savings = deal['price'] - exp_deal['price']
                savings_str = f"(save ${savings})" if savings > 0 else f"(+${abs(savings)})" if savings < 0 else "(same)"
                print(f"    {j+1}. ${exp_deal['price']} {savings_str} | {exp_deal['outbound_date']} to {exp_deal['return_date']}")
        else:
            print(f"\n✗ No similar deals found within price threshold")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(test_dfw_europe())

