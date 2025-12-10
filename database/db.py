"""
Database CRUD operations for flight deals.
"""
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class DealsDatabase:
    """Database interface for storing and querying flight deals."""
    
    def __init__(self, connection_string: str = None, **connection_params):
        """
        Initialize database connection.
        
        Args:
            connection_string: PostgreSQL connection string (e.g., "postgresql://user:pass@host:port/db")
            **connection_params: Alternative connection params (host, port, database, user, password)
        """
        if connection_string:
            self.conn = psycopg2.connect(connection_string)
        else:
            self.conn = psycopg2.connect(**connection_params)
        self.conn.autocommit = False
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        self.close()
    
    def insert_expanded_deals(self, deals: List[Dict]) -> int:
        """
        Insert expanded deals into database.
        NOTE: No UNIQUE constraint - allows duplicates for historical tracking.
        
        Args:
            deals: List of deal dicts with keys:
                - origin (str)
                - destination (str)
                - destination_city (str, optional)
                - outbound_date (str or date)
                - return_date (str or date)
                - price (int)
                - reference_price (int)
                - search_region (str, optional)
                - duration (str, optional)
                - similar_date_count (int)
                - google_flights_url (str, optional)
        
        Returns:
            Number of deals successfully inserted
        """
        if not deals:
            return 0
        
        insert_sql = """
            INSERT INTO expanded_deals 
                (scrape_run_id, origin, destination, destination_city, outbound_date, return_date, 
                 price, reference_price, search_region, duration, 
                 similar_date_count, google_flights_url)
            VALUES 
                (%(scrape_run_id)s, %(origin)s, %(destination)s, %(destination_city)s, %(outbound_date)s, 
                 %(return_date)s, %(price)s, %(reference_price)s, %(search_region)s, 
                 %(duration)s, %(similar_date_count)s, %(google_flights_url)s)
        """
        
        with self.conn.cursor() as cur:
            # Execute batch insert (no conflict handling - allows duplicates)
            execute_batch(cur, insert_sql, deals)
            # execute_batch doesn't update rowcount, so return the number of deals
            inserted_count = len(deals)
            self.conn.commit()
        
        return inserted_count
    
    def mark_as_posted(self, deal_ids: List[int]) -> int:
        """
        Mark deals as posted.
        
        Args:
            deal_ids: List of deal IDs to mark as posted
        
        Returns:
            Number of deals marked as posted
        """
        if not deal_ids:
            return 0
        
        update_sql = """
            UPDATE expanded_deals 
            SET posted = TRUE, posted_at = NOW()
            WHERE id = ANY(%s) AND posted = FALSE
        """
        
        with self.conn.cursor() as cur:
            cur.execute(update_sql, (deal_ids,))
            updated_count = cur.rowcount
            self.conn.commit()
        
        return updated_count
    
    def get_unposted_deals(self, limit: int = 100) -> List[Dict]:
        """
        Get deals that haven't been posted yet.
        
        Args:
            limit: Maximum number of deals to return
        
        Returns:
            List of deal dicts
        """
        select_sql = """
            SELECT id, origin, destination, outbound_date, return_date, price,
                   reference_price, similar_date_count, found_at
            FROM expanded_deals
            WHERE posted = FALSE
            ORDER BY found_at DESC
            LIMIT %s
        """
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(select_sql, (limit,))
            results = cur.fetchall()
        
        return [dict(row) for row in results]
    
    def check_route_posted_recently(self, origin: str, destination: str, days: int = 21) -> bool:
        """
        Check if a route (origin-destination pair) was posted in the last N days.
        Used for deduplication - don't post same route too frequently.
        
        Args:
            origin: Origin airport code (e.g., "DFW")
            destination: Destination airport code (e.g., "LHR")
            days: Number of days to look back (default 21 = 3 weeks)
        
        Returns:
            True if route was posted recently, False otherwise
        """
        check_sql = """
            SELECT EXISTS(
                SELECT 1 
                FROM expanded_deals
                WHERE origin = %s 
                  AND destination = %s
                  AND posted = TRUE
                  AND posted_at > NOW() - INTERVAL '%s days'
            )
        """
        
        with self.conn.cursor() as cur:
            cur.execute(check_sql, (origin, destination, days))
            exists = cur.fetchone()[0]
        
        return exists
    
    def get_deals_by_route(self, origin: str, destination: str, posted_only: bool = False) -> List[Dict]:
        """
        Get all deals for a specific route.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            posted_only: If True, only return posted deals
        
        Returns:
            List of deal dicts
        """
        select_sql = """
            SELECT id, origin, destination, outbound_date, return_date, price,
                   reference_price, similar_date_count, found_at, posted, posted_at
            FROM expanded_deals
            WHERE origin = %s AND destination = %s
        """
        
        if posted_only:
            select_sql += " AND posted = TRUE"
        
        select_sql += " ORDER BY found_at DESC"
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(select_sql, (origin, destination))
            results = cur.fetchall()
        
        return [dict(row) for row in results]
    
    def create_scrape_run(self, origins_count: int) -> int:
        """
        Create a new scrape run record.
        
        Args:
            origins_count: Number of origins being scraped
        
        Returns:
            The ID of the newly created scrape run
        """
        insert_sql = """
            INSERT INTO scrape_runs (origins_count, status)
            VALUES (%s, 'running')
            RETURNING id
        """
        
        with self.conn.cursor() as cur:
            cur.execute(insert_sql, (origins_count,))
            run_id = cur.fetchone()[0]
            self.conn.commit()
        
        return run_id
    
    def complete_scrape_run(self, run_id: int, stats: Dict, status: str = 'completed') -> None:
        """
        Mark a scrape run as complete and update its statistics.
        
        Args:
            run_id: ID of the scrape run
            stats: Dictionary with keys:
                - cards_found (int)
                - expansions_attempted (int)
                - expansions_succeeded (int)
                - valid_deals (int)
            status: Status to set (default 'completed', can be 'failed')
        """
        update_sql = """
            UPDATE scrape_runs
            SET completed_at = NOW(),
                cards_found = %s,
                expansions_attempted = %s,
                expansions_succeeded = %s,
                valid_deals = %s,
                status = %s
            WHERE id = %s
        """
        
        with self.conn.cursor() as cur:
            cur.execute(update_sql, (
                stats.get('cards_found', 0),
                stats.get('expansions_attempted', 0),
                stats.get('expansions_succeeded', 0),
                stats.get('valid_deals', 0),
                status,
                run_id
            ))
            self.conn.commit()
    
    def get_recent_scrape_runs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent scrape run history.
        
        Args:
            limit: Number of runs to return
        
        Returns:
            List of scrape run dicts
        """
        select_sql = """
            SELECT id, started_at, completed_at, origins_count, 
                   cards_found, expansions_attempted, expansions_succeeded, 
                   valid_deals, status
            FROM scrape_runs
            ORDER BY started_at DESC
            LIMIT %s
        """
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(select_sql, (limit,))
            results = cur.fetchall()
        
        return [dict(row) for row in results]
    
    def get_stats(self) -> Dict:
        """
        Get overall database statistics.
        
        Returns:
            Dict with statistics about stored deals
        """
        stats_sql = """
            SELECT 
                COUNT(*) as total_deals,
                COUNT(*) FILTER (WHERE posted = TRUE) as posted_deals,
                COUNT(*) FILTER (WHERE posted = FALSE) as unposted_deals,
                COUNT(DISTINCT origin) as unique_origins,
                COUNT(DISTINCT destination) as unique_destinations,
                COUNT(DISTINCT (origin, destination)) as unique_routes,
                MIN(found_at) as first_deal_date,
                MAX(found_at) as latest_deal_date,
                AVG(price) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM expanded_deals
        """
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(stats_sql)
            result = cur.fetchone()
        
        return dict(result) if result else {}

