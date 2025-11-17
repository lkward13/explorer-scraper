#!/usr/bin/env python3
"""
Demo script to show how to access and display URLs for each date combination.
This simulates what would appear on cheapflightsfrom.us
"""

import json
import sys

def demo_url_display(results_file: str):
    """Show how URLs can be used for links like cheapflightsfrom.us"""
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print("\n" + "="*80)
    print(f"DEALS FROM {data['origin']} (with clickable date links)")
    print("="*80 + "\n")
    
    for deal_idx, deal in enumerate(data.get('expanded_deals', []), 1):
        explore = deal['explore_deal']
        expansion = deal.get('expansion', {})
        
        dest = explore['destination']
        price = explore['min_price']
        
        print(f"{deal_idx}. {data['origin']} → {dest} from ${price}")
        print(f"   Score: {deal.get('score', 0):.2f}")
        print(f"   Available dates (click to book):\n")
        
        # Show first 10 date combinations with URLs
        similar_deals = expansion.get('similar_deals', [])
        for i, date_combo in enumerate(similar_deals[:10], 1):
            start = date_combo['start_date']
            end = date_combo['end_date']
            price = date_combo['price']
            url = date_combo.get('url', 'No URL')
            
            # Format like cheapflightsfrom.us would
            print(f"     • {start} to {end} - ${price}")
            print(f"       {url}")
            print()
        
        if len(similar_deals) > 10:
            print(f"     ... and {len(similar_deals) - 10} more dates\n")
        
        print("-" * 80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/demo_urls.py results.json")
        sys.exit(1)
    
    demo_url_display(sys.argv[1])

