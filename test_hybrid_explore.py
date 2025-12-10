#!/usr/bin/env python3
"""
Test the hybrid explore: Fast TFS + selective discount enhancement.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from explore_scraper.fetch_browser_hybrid import fetch_and_enhance_cards
from explore_scraper.region_tfs_generator import build_explore_url_for_region


async def main():
    print("="*80)
    print("TESTING HYBRID EXPLORE (Fast TFS + Discount Enhancement)")
    print("="*80)
    print()
    
    # Test with PHX → Europe
    origin = "PHX"
    region = "europe"
    
    print(f"Origin: {origin}")
    print(f"Region: {region}")
    print()
    
    url = build_explore_url_for_region(origin, region)
    print(f"URL: {url[:80]}...")
    print()
    
    print("-"*80)
    
    cards = await fetch_and_enhance_cards(
        url,
        headless=True,
        timeout=60.0,
        verbose=True
    )
    
    print()
    print("="*80)
    print("RESULTS")
    print("="*80)
    print()
    
    if not cards:
        print("✗ No cards found")
        return
    
    print(f"✓ Found {len(cards)} cards")
    print()
    
    # Show cards with discounts
    cards_with_discount = [c for c in cards if c.get('deal_quality_amount')]
    print(f"Cards with discount data: {len(cards_with_discount)}/{len(cards)}")
    print()
    
    if cards_with_discount:
        print("Top deals (by discount %):")
        print("-"*80)
        sorted_cards = sorted(cards_with_discount, key=lambda x: x.get('discount_percent', 0), reverse=True)
        for i, card in enumerate(sorted_cards[:10], 1):
            print(f"{i}. {card['destination']} ({card.get('airport_code', '???')}): ${card['min_price']}")
            print(f"   Savings: ${card['deal_quality_amount']} ({card['discount_percent']}% off)")
            print(f"   Status: {card.get('deal_quality', 'N/A')}")
            print()
    
    # Show cards meeting 20% threshold
    good_deals = [c for c in cards_with_discount if c.get('discount_percent', 0) >= 20]
    print("="*80)
    print(f"DEALS MEETING 20% THRESHOLD: {len(good_deals)}")
    print("="*80)
    print()
    
    if good_deals:
        for card in good_deals:
            print(f"✓ {card['destination']} ({card.get('airport_code', '???')}): ${card['min_price']} - {card['discount_percent']}% off")
    else:
        print("No deals meet the 20% threshold")
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total cards: {len(cards)}")
    print(f"With discount data: {len(cards_with_discount)}")
    print(f"Meeting 20% threshold: {len(good_deals)}")
    print()
    print("Next: Integrate into parallel_executor to filter cards before expansion")


if __name__ == '__main__':
    asyncio.run(main())

