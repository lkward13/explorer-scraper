#!/usr/bin/env python3
"""Show actual deals found from API expansion."""
import asyncio
from scripts.expand_dates_api import expand_deal_via_api

# Test deals from recent run
TEST_DEALS = [
    {'origin': 'ATL', 'destination': 'SJU', 'start_date': '2026-01-11', 'end_date': '2026-01-20', 'price': 195},
    {'origin': 'DFW', 'destination': 'SJU', 'start_date': '2026-01-15', 'end_date': '2026-01-22', 'price': 206},
    {'origin': 'LAX', 'destination': 'SJU', 'start_date': '2026-01-18', 'end_date': '2026-01-25', 'price': 231},
    {'origin': 'ORD', 'destination': 'SJU', 'start_date': '2026-01-12', 'end_date': '2026-01-19', 'price': 159},
    {'origin': 'PHX', 'destination': 'SJU', 'start_date': '2026-01-20', 'end_date': '2026-01-27', 'price': 236},
]

async def main():
    print("="*80)
    print("DEALS FOUND VIA API EXPANSION")
    print("="*80)
    
    for i, deal in enumerate(TEST_DEALS, 1):
        print(f"\n{i}. {deal['origin']} → {deal['destination']} (${deal['price']})")
        print(f"   Original dates: {deal['start_date']} to {deal['end_date']}")
        
        # Expand via API
        similar_deals = await expand_deal_via_api(
            origin=deal['origin'],
            destination=deal['destination'],
            outbound_date=deal['start_date'],
            return_date=deal['end_date'],
            original_price=deal['price'],
            verbose=False
        )
        
        print(f"   Found {len(similar_deals)} similar deals:")
        
        if similar_deals:
            # Show first 10 deals
            for j, sd in enumerate(similar_deals[:10], 1):
                savings = deal['price'] - sd['price']
                savings_str = f"(save ${savings})" if savings > 0 else f"(+${-savings})"
                print(f"     {j:2d}. {sd['outbound_date']} to {sd['return_date']}: ${sd['price']:3d} {savings_str}")
            
            if len(similar_deals) > 10:
                print(f"     ... and {len(similar_deals) - 10} more")
            
            # Show price range
            prices = [sd['price'] for sd in similar_deals]
            print(f"\n   Price range: ${min(prices)} - ${max(prices)}")
            print(f"   Average: ${sum(prices) // len(prices)}")
        else:
            print("     (No similar deals within 15% price threshold)")

if __name__ == '__main__':
    asyncio.run(main())

