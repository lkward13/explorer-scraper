#!/usr/bin/env python3
"""
Calculate price insights from historical deal data.

This script analyzes all deals in the database and calculates statistical
insights for each route (origin → destination pair).

Usage:
    python scripts/calculate_price_insights.py
    python scripts/calculate_price_insights.py --min-samples 10
    python scripts/calculate_price_insights.py --days 60 --verbose

Run this daily (via cron) after scraping completes to keep insights fresh.
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.config import get_connection_params
import psycopg2


def calculate_insights(
    min_samples: int = 7,
    lookback_days: int = 90,
    verbose: bool = False
):
    """
    Calculate price insights for all routes with sufficient data.
    
    Args:
        min_samples: Minimum number of data points required (default: 7)
        lookback_days: How many days of history to analyze (default: 90)
        verbose: Print detailed progress
    """
    conn = psycopg2.connect(**get_connection_params())
    cursor = conn.cursor()
    
    if verbose:
        print(f"Calculating price insights...")
        print(f"  Lookback period: {lookback_days} days")
        print(f"  Minimum samples: {min_samples}")
        print()
    
    # Calculate insights for all routes with sufficient data
    query = """
    WITH route_stats AS (
        SELECT 
            origin,
            destination,
            COUNT(*) as sample_size,
            MIN(found_at) as first_seen,
            MAX(found_at) as last_seen,
            
            -- Statistical measures
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) as p25,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price) as median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) as p75,
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            
            -- Time tracking
            EXTRACT(DAY FROM (MAX(found_at) - MIN(found_at)))::INTEGER as days_tracked
        FROM expanded_deals
        WHERE found_at > NOW() - INTERVAL '%s days'
        GROUP BY origin, destination
        HAVING COUNT(*) >= %s
    )
    INSERT INTO route_price_insights (
        origin, destination, 
        typical_price, low_price_threshold, high_price_threshold,
        min_price_seen, max_price_seen, avg_price,
        sample_size, first_seen, last_updated,
        data_quality, days_tracked
    )
    SELECT 
        origin, destination,
        ROUND(median)::INTEGER as typical_price,
        ROUND(p25)::INTEGER as low_price_threshold,
        ROUND(p75)::INTEGER as high_price_threshold,
        min_price, max_price,
        ROUND(avg_price)::INTEGER as avg_price,
        sample_size, first_seen, NOW() as last_updated,
        
        -- Data quality based on sample size
        CASE 
            WHEN sample_size >= 30 THEN 'high'
            WHEN sample_size >= 14 THEN 'medium'
            ELSE 'low'
        END as data_quality,
        
        days_tracked
    FROM route_stats
    ON CONFLICT (origin, destination) 
    DO UPDATE SET
        typical_price = EXCLUDED.typical_price,
        low_price_threshold = EXCLUDED.low_price_threshold,
        high_price_threshold = EXCLUDED.high_price_threshold,
        min_price_seen = LEAST(route_price_insights.min_price_seen, EXCLUDED.min_price_seen),
        max_price_seen = GREATEST(route_price_insights.max_price_seen, EXCLUDED.max_price_seen),
        avg_price = EXCLUDED.avg_price,
        sample_size = EXCLUDED.sample_size,
        last_updated = NOW(),
        data_quality = EXCLUDED.data_quality,
        days_tracked = EXCLUDED.days_tracked;
    """ % (lookback_days, min_samples)
    
    cursor.execute(query)
    rows_affected = cursor.rowcount
    conn.commit()
    
    if verbose:
        print(f"✓ Updated price insights for {rows_affected} routes")
        print()
        
        # Show summary statistics
        cursor.execute("""
            SELECT 
                data_quality,
                COUNT(*) as route_count,
                AVG(sample_size)::INTEGER as avg_samples,
                AVG(days_tracked)::INTEGER as avg_days
            FROM route_price_insights
            GROUP BY data_quality
            ORDER BY 
                CASE data_quality 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END;
        """)
        
        print("Summary by data quality:")
        print("-" * 60)
        for row in cursor.fetchall():
            quality, count, avg_samples, avg_days = row
            print(f"  {quality.upper():8} | {count:4} routes | "
                  f"avg {avg_samples:3} samples | {avg_days:3} days tracked")
        print()
        
        # Show some example insights
        cursor.execute("""
            SELECT origin, destination, typical_price, low_price_threshold,
                   min_price_seen, sample_size, data_quality
            FROM route_price_insights
            ORDER BY sample_size DESC
            LIMIT 10;
        """)
        
        print("Top 10 most-tracked routes:")
        print("-" * 80)
        print(f"{'Route':15} {'Typical':>8} {'Good Deal':>10} {'Best Ever':>10} "
              f"{'Samples':>8} {'Quality':>8}")
        print("-" * 80)
        for row in cursor.fetchall():
            origin, dest, typical, low, min_seen, samples, quality = row
            route = f"{origin} → {dest}"
            print(f"{route:15} ${typical:7} ${low:9} ${min_seen:9} "
                  f"{samples:8} {quality:>8}")
        print()
    
    cursor.close()
    conn.close()
    
    return rows_affected


def main():
    parser = argparse.ArgumentParser(
        description="Calculate price insights from historical deal data"
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=7,
        help='Minimum number of data points required (default: 7)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='How many days of history to analyze (default: 90)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress and statistics'
    )
    
    args = parser.parse_args()
    
    try:
        rows = calculate_insights(
            min_samples=args.min_samples,
            lookback_days=args.days,
            verbose=args.verbose
        )
        
        if not args.verbose:
            print(f"✓ Updated {rows} routes")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

