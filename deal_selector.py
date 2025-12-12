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
    
    # Regional price thresholds (what's considered a "good deal")
    REGION_THRESHOLDS = {
        'caribbean': 350,
        'central_america': 350,
        'south_america': 600,
        'europe': 600,
        'middle_east': 850,
        'africa': 850,
        'asia': 850,
        'oceania': 950,
        'pacific': 950,
    }
    
    def __init__(self, connection_string: str):
        """
        Initialize with database connection.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.conn = psycopg2.connect(connection_string)
    
    def _calculate_deal_quality_score(self, deal: Dict) -> Dict:
        """
        Calculate deal quality score using our price insights.
        
        Args:
            deal: Deal dictionary with origin, destination, price
            
        Returns:
            {
                'score': 0-100,  # Higher = better deal
                'quality': 'excellent' | 'great' | 'good' | 'fair' | 'unknown',
                'insight': 'X% below typical price',
                'confidence': 'high' | 'medium' | 'low',
                'typical_price': int,
                'discount_pct': float
            }
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get price insights for this route
        cursor.execute("""
            SELECT typical_price, low_price_threshold, min_price_seen, 
                   sample_size, data_quality
            FROM route_price_insights
            WHERE origin = %s AND destination = %s
        """, (deal['origin'], deal['destination']))
        
        insights = cursor.fetchone()
        cursor.close()
        
        if not insights:
            # No historical data yet - use basic heuristics
            return {
                'score': 50,
                'quality': 'unknown',
                'insight': 'New route - no historical data yet',
                'confidence': 'low',
                'typical_price': None,
                'discount_pct': 0
            }
        
        price = deal['price']
        typical = insights['typical_price']
        low_threshold = insights['low_price_threshold']
        min_seen = insights['min_price_seen']
        data_quality = insights['data_quality']
        
        # Calculate how good this deal is
        discount_pct = ((typical - price) / typical * 100) if typical > 0 else 0
        
        # Score calculation (0-100)
        if price <= min_seen:
            score = 100  # Best price ever!
            quality = 'excellent'
            insight = f'Best price ever! {int(discount_pct)}% below typical'
        elif price <= low_threshold:
            # Great deal - between best ever and 25th percentile
            score = 85 + (low_threshold - price) / (low_threshold - min_seen) * 15
            quality = 'great'
            insight = f'{int(discount_pct)}% below typical price'
        elif price <= typical:
            # Good deal - between 25th percentile and median
            score = 60 + (typical - price) / (typical - low_threshold) * 25
            quality = 'good'
            insight = f'{int(discount_pct)}% below typical price'
        else:
            # Fair or poor - above median
            score = max(0, 60 - (price - typical) / typical * 100)
            quality = 'fair'
            insight = f'{int(abs(discount_pct))}% above typical price'
        
        return {
            'score': round(score, 1),
            'quality': quality,
            'insight': insight,
            'confidence': data_quality,  # 'high', 'medium', or 'low'
            'typical_price': typical,
            'discount_pct': round(discount_pct, 1)
        }
    
    def select_daily_deals_with_scoring(
        self,
        origins: Optional[List[str]] = None,
        max_price: int = 600,
        min_quality_score: int = 60,
        dedup_days: int = 21,
        limit_per_origin: int = 10
    ) -> List[Dict]:
        """
        Select deals with quality scoring based on price insights.
        
        Args:
            origins: List of origin airports (None = all origins)
            max_price: Maximum price threshold
            min_quality_score: Only include deals scoring >= this (0-100)
            dedup_days: Don't send same route within X days
            limit_per_origin: Max destinations to consider per origin
            
        Returns:
            List of deals sorted by quality score (best first), each with:
            {
                'origin': 'DFW',
                'destination': 'BCN',
                'price': 450,
                'quality': {
                    'score': 92.5,
                    'quality': 'great',
                    'insight': '32% below typical price',
                    'confidence': 'high',
                    'typical_price': 660,
                    'discount_pct': 31.8
                },
                ... other deal fields ...
            }
        """
        # Get unposted deals
        deals_by_origin = self._get_unposted_deals(
            origins=origins,
            max_price=max_price,
            dedup_days=dedup_days,
            limit_per_origin=limit_per_origin
        )
        
        # Score each deal
        scored_deals = []
        for origin, deals in deals_by_origin.items():
            for deal in deals:
                quality = self._calculate_deal_quality_score(deal)
                
                # Only include deals meeting quality threshold
                if quality['score'] >= min_quality_score:
                    deal['quality'] = quality
                    scored_deals.append(deal)
        
        # Sort by quality score (best first)
        scored_deals.sort(key=lambda x: x['quality']['score'], reverse=True)
        
        return scored_deals
    
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
    
    def select_deals_simple(
        self,
        origins: Optional[List[str]] = None,
        cooldown_days: int = 7,
        limit: int = 50,
        max_price_override: Optional[int] = None
    ) -> List[Dict]:
        """
        Simple price-based deal selection using regional thresholds.
        No historical data required - just industry-standard "good deal" prices.
        
        Args:
            origins: List of origin airports (None = all origins)
            cooldown_days: Don't send same route within X days
            limit: Maximum number of deals to return
            max_price_override: Override all regional thresholds with this price
            
        Returns:
            List of deals sorted by price (cheapest first)
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get recently sent routes
        recently_sent = set(self.get_recently_sent_routes(days=cooldown_days))
        
        # Build query
        query = """
            SELECT DISTINCT ON (origin, destination)
                *
            FROM expanded_deals
            WHERE found_at >= NOW() - INTERVAL '48 hours'
        """
        params = []
        
        if origins:
            query += " AND origin = ANY(%s)"
            params.append(origins)
        
        query += " ORDER BY origin, destination, price ASC"
        
        cursor.execute(query, params)
        all_deals = cursor.fetchall()
        cursor.close()
        
        # Filter by regional thresholds and cooldown
        good_deals = []
        for deal in all_deals:
            # Skip recently sent routes
            route = (deal['origin'], deal['destination'])
            if route in recently_sent:
                continue
            
            # Check price threshold
            region = deal.get('search_region', '').lower()
            
            if max_price_override:
                threshold = max_price_override
            else:
                threshold = self.REGION_THRESHOLDS.get(region, 600)  # Default to Europe threshold
            
            if deal['price'] <= threshold:
                good_deals.append(dict(deal))
        
        # Sort by price (cheapest first) and limit
        good_deals.sort(key=lambda x: x['price'])
        return good_deals[:limit]
    
    def mark_deals_as_sent(
        self,
        deals: List[Dict],
        recipient_email: Optional[str] = None
    ) -> int:
        """
        Mark deals as sent in the sent_deals tracking table.
        
        Args:
            deals: List of deal dictionaries
            recipient_email: Email address of recipient (optional)
            
        Returns:
            Number of deals marked as sent
        """
        cursor = self.conn.cursor()
        count = 0
        
        for deal in deals:
            cursor.execute("""
                INSERT INTO sent_deals 
                (origin, destination, price, outbound_date, return_date, recipient_email, deal_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                deal['origin'],
                deal['destination'],
                deal['price'],
                deal['outbound_date'],
                deal['return_date'],
                recipient_email,
                deal.get('id')
            ))
            count += 1
        
        self.conn.commit()
        cursor.close()
        return count
    
    def get_recently_sent_routes(self, days: int = 7) -> List[tuple]:
        """
        Get routes that have been sent in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of (origin, destination) tuples
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT origin, destination
            FROM sent_deals
            WHERE sent_at >= NOW() - INTERVAL '%s days'
        """, (days,))
        
        routes = [(row[0], row[1]) for row in cursor.fetchall()]
        cursor.close()
        return routes
    
    def select_deals_with_cooldown(
        self,
        origins: Optional[List[str]] = None,
        max_price: int = 600,
        min_quality_score: int = 70,
        cooldown_days: int = 7,
        limit: int = 50
    ) -> List[Dict]:
        """
        Select deals with quality scoring AND cooldown logic.
        Prevents sending the same route too frequently.
        
        Args:
            origins: List of origin airports (None = all origins)
            max_price: Maximum price threshold
            min_quality_score: Only include deals scoring >= this (0-100)
            cooldown_days: Don't send same route within X days
            limit: Maximum number of deals to return
            
        Returns:
            List of deals sorted by quality score (best first)
        """
        # Get recently sent routes
        recently_sent = set(self.get_recently_sent_routes(days=cooldown_days))
        
        # Get all deals with quality scoring
        all_deals = self.select_daily_deals_with_scoring(
            origins=origins,
            max_price=max_price,
            min_quality_score=min_quality_score,
            dedup_days=21,
            limit_per_origin=10
        )
        
        # Filter out recently sent routes
        filtered_deals = []
        for deal in all_deals:
            route = (deal['origin'], deal['destination'])
            if route not in recently_sent:
                filtered_deals.append(deal)
        
        # Return top N deals
        return filtered_deals[:limit]
    
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

