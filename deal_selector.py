#!/usr/bin/env python3
"""
Deal Selection Logic for Daily Email Notifications

Strategies:
1. Individual deals: Best deal per origin
2. Regional sales: Detect when multiple destinations in same region are on sale
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class DealSelector:
    """Select and categorize flight deals for email notifications."""
    
    def __init__(self, connection_string: str):
        """
        Initialize with database connection.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.conn = psycopg2.connect(connection_string)
    
    def select_daily_deals(
        self,
        origins: Optional[List[str]] = None,
        max_price: int = 600,
        min_destinations_for_regional: int = 3,
        dedup_days: int = 21,
        limit_per_origin: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Select deals for daily email, categorized by type.
        
        Args:
            origins: List of origin airports (None = all origins)
            max_price: Maximum price threshold
            min_destinations_for_regional: Min destinations to trigger "regional sale"
            dedup_days: Don't send same route within X days
            limit_per_origin: Max destinations to consider per origin
            
        Returns:
            {
                'individual': [deal1, deal2, ...],  # Single destination deals
                'regional': [regional_deal1, ...]   # Multi-destination regional sales
            }
        """
        # Get unposted deals for each origin
        deals_by_origin = self._get_unposted_deals(
            origins=origins,
            max_price=max_price,
            dedup_days=dedup_days,
            limit_per_origin=limit_per_origin
        )
        
        individual_deals = []
        regional_deals = []
        
        for origin, deals in deals_by_origin.items():
            if not deals:
                continue
            
            # Sort all deals by price
            sorted_deals = sorted(deals, key=lambda x: x['price'])
            best_deal = sorted_deals[0]
            best_price = best_deal['price']
            
            # Group deals by region
            by_region = defaultdict(list)
            for deal in deals:
                region = deal['search_region']
                if region:  # Only group if region is known
                    by_region[region].append(deal)
            
            # Strategy: Check if we should group or send individually
            # Rule 1: If best deal is significantly cheaper ($50+), always send it individually
            # Rule 2: If a region has 3+ destinations with similar prices, group them
            # Rule 3: Otherwise, send top deals individually
            
            best_deal_sent = False
            
            # Check each region for "sale" pattern
            for region, region_deals in by_region.items():
                if len(region_deals) >= min_destinations_for_regional:
                    # Check if prices are similar (within 35% range)
                    # Absolute $100 check is too strict for expensive regions like Asia ($600 vs $800)
                    region_prices = [d['price'] for d in region_deals]
                    min_p = min(region_prices)
                    max_p = max(region_prices)
                    
                    # Calculate relative spread
                    # e.g., $300 to $400 is (100/300) = 33% -> OK
                    # e.g., $600 to $800 is (200/600) = 33% -> OK
                    # e.g., $300 to $500 is (200/300) = 66% -> Too wide
                    relative_spread = (max_p - min_p) / min_p if min_p > 0 else 0
                    
                    if relative_spread <= 0.35:  # 35% spread allowed
                        # REGIONAL SALE DETECTED!
                        regional_deals.append(self._create_regional_deal(origin, region, region_deals))
                        
                        # Mark best deal as sent if it's in this region
                        if best_deal in region_deals:
                            best_deal_sent = True
                    else:
                        # Prices too varied - send individually
                        individual_deals.extend(region_deals)
                        if best_deal in region_deals:
                            best_deal_sent = True
                else:
                    # Not enough destinations - treat as individual deals
                    individual_deals.extend(region_deals)
                    if best_deal in region_deals:
                        best_deal_sent = True
            
            # Add deals with no region as individual
            no_region = [d for d in deals if not d['search_region']]
            individual_deals.extend(no_region)
            if best_deal in no_region:
                best_deal_sent = True
            
            # Rule: Always highlight the best deal if it's exceptional
            # If best deal is $50+ cheaper than the next cheapest AND not already sent
            if not best_deal_sent and len(sorted_deals) > 1:
                second_best_price = sorted_deals[1]['price']
                if second_best_price - best_price >= 50:
                    # Best deal is significantly better - send it individually
                    individual_deals.insert(0, best_deal)  # Add to front
        
        return {
            'individual': individual_deals,
            'regional': regional_deals
        }
    
    def _get_unposted_deals(
        self,
        origins: Optional[List[str]],
        max_price: int,
        dedup_days: int,
        limit_per_origin: int
    ) -> Dict[str, List[Dict]]:
        """
        Get unposted deals grouped by origin.
        
        Returns:
            {
                'DFW': [deal1, deal2, ...],
                'ATL': [deal1, deal2, ...],
                ...
            }
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build query
            origin_filter = ""
            params = [max_price]
            
            if origins:
                placeholders = ','.join(['%s'] * len(origins))
                origin_filter = f"AND origin IN ({placeholders})"
                params.extend(origins)
            
            params.append(dedup_days)  # Add dedup_days at the end
            
            query = f"""
                WITH ranked_deals AS (
                    SELECT 
                        origin,
                        destination,
                        destination_city,
                        search_region,
                        price,
                        outbound_date,
                        return_date,
                        google_flights_url,
                        similar_date_count,
                        ROW_NUMBER() OVER (
                            PARTITION BY origin, destination 
                            ORDER BY price ASC
                        ) as rn
                    FROM expanded_deals
                    WHERE 
                        posted = FALSE
                        AND price <= %s
                        {origin_filter}
                        -- Not posted in last X days
                        AND NOT EXISTS (
                            SELECT 1 
                            FROM expanded_deals e2
                            WHERE e2.origin = expanded_deals.origin
                            AND e2.destination = expanded_deals.destination
                            AND e2.posted = TRUE
                            AND e2.posted_at > NOW() - INTERVAL '%s days'
                        )
                )
                SELECT 
                    origin,
                    destination,
                    destination_city,
                    search_region,
                    price,
                    outbound_date,
                    return_date,
                    google_flights_url,
                    similar_date_count
                FROM ranked_deals
                WHERE rn = 1  -- Best price per route
                ORDER BY origin, price ASC
            """
            
            cur.execute(query, params)
            all_deals = cur.fetchall()
        
        # Group by origin and limit per origin
        by_origin = defaultdict(list)
        for deal in all_deals:
            origin = deal['origin']
            if len(by_origin[origin]) < limit_per_origin:
                by_origin[origin].append(dict(deal))
        
        return dict(by_origin)
    
    def _create_regional_deal(
        self,
        origin: str,
        region: str,
        deals: List[Dict]
    ) -> Dict:
        """
        Create a regional sale deal from multiple destination deals.
        
        Args:
            origin: Origin airport code
            region: Region name (e.g., 'europe', 'caribbean')
            deals: List of deals in this region
            
        Returns:
            {
                'type': 'regional',
                'origin': 'DFW',
                'region': 'europe',
                'region_display': 'Europe',
                'destination_count': 5,
                'min_price': 347,
                'max_price': 425,
                'destinations': [
                    {'destination': 'BCN', 'city': 'Barcelona', 'price': 347, ...},
                    {'destination': 'LIS', 'city': 'Lisbon', 'price': 355, ...},
                    ...
                ]
            }
        """
        # Sort by price
        sorted_deals = sorted(deals, key=lambda x: x['price'])
        
        return {
            'type': 'regional',
            'origin': origin,
            'region': region,
            'region_display': region.title(),  # 'europe' -> 'Europe'
            'destination_count': len(sorted_deals),
            'min_price': sorted_deals[0]['price'],
            'max_price': sorted_deals[-1]['price'],
            'destinations': sorted_deals
        }
    
    def mark_as_posted(self, deal_ids: List[int]) -> int:
        """
        Mark deals as posted.
        
        Args:
            deal_ids: List of deal IDs to mark
            
        Returns:
            Number of deals marked
        """
        if not deal_ids:
            return 0
        
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE expanded_deals
                SET posted = TRUE, posted_at = NOW()
                WHERE id = ANY(%s) AND posted = FALSE
            """, (deal_ids,))
            
            count = cur.rowcount
            self.conn.commit()
        
        return count
    
    def get_deal_ids_from_selection(self, deals: Dict[str, List[Dict]]) -> List[int]:
        """
        Extract all deal IDs from a selection result.
        
        Args:
            deals: Result from select_daily_deals()
            
        Returns:
            List of deal IDs to mark as posted
        """
        deal_ids = []
        
        # Individual deals - need to fetch IDs
        for deal in deals['individual']:
            deal_ids.extend(self._get_deal_ids_for_route(
                deal['origin'],
                deal['destination'],
                deal['outbound_date'],
                deal['return_date']
            ))
        
        # Regional deals - need to fetch IDs for all destinations
        for regional in deals['regional']:
            for dest_deal in regional['destinations']:
                deal_ids.extend(self._get_deal_ids_for_route(
                    regional['origin'],
                    dest_deal['destination'],
                    dest_deal['outbound_date'],
                    dest_deal['return_date']
                ))
        
        return deal_ids
    
    def _get_deal_ids_for_route(
        self,
        origin: str,
        destination: str,
        outbound_date: str,
        return_date: str
    ) -> List[int]:
        """Get all deal IDs for a specific route/date combo."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id
                FROM expanded_deals
                WHERE origin = %s
                AND destination = %s
                AND outbound_date = %s
                AND return_date = %s
                AND posted = FALSE
            """, (origin, destination, outbound_date, return_date))
            
            return [row[0] for row in cur.fetchall()]
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# Example usage
if __name__ == "__main__":
    from database.config import get_connection_string
    
    selector = DealSelector(get_connection_string())
    
    # Test with 5 origins
    deals = selector.select_daily_deals(
        origins=['DFW', 'ATL', 'LAX', 'ORD', 'JFK'],
        max_price=600,
        min_destinations_for_regional=3,
        limit_per_origin=5
    )
    
    print(f"\n{'='*80}")
    print(f"DEAL SELECTION RESULTS")
    print(f"{'='*80}")
    
    print(f"\nIndividual Deals: {len(deals['individual'])}")
    for deal in deals['individual']:
        print(f"  {deal['origin']} → {deal['destination']} (${deal['price']})")
    
    print(f"\nRegional Sales: {len(deals['regional'])}")
    for regional in deals['regional']:
        print(f"  {regional['origin']} → {regional['region_display']}: "
              f"{regional['destination_count']} destinations "
              f"(${regional['min_price']}-${regional['max_price']})")
        for dest in regional['destinations'][:3]:  # Show first 3
            print(f"    - {dest['destination']}: ${dest['price']}")
    
    selector.close()

