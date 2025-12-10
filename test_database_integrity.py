#!/usr/bin/env python3
"""
Database Integrity Test

Deep validation of database data quality:
- NULL value checks
- Price range validation
- Date range validation
- Data consistency
- Stale data detection

Usage:
    python test_database_integrity.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).parent))

from database.config import get_connection_params
import psycopg2


def test_null_values():
    """Test 1: Check for NULL values in critical fields."""
    print("1. Checking for NULL values in critical fields...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        # Check expanded_deals table
        null_checks = [
            ("expanded_deals", "origin", "Origin airport code"),
            ("expanded_deals", "destination", "Destination airport code"),
            ("expanded_deals", "price", "Price"),
            ("expanded_deals", "outbound_date", "Outbound date"),
            ("expanded_deals", "return_date", "Return date"),
            ("route_price_insights", "origin", "Insights origin"),
            ("route_price_insights", "destination", "Insights destination"),
            ("route_price_insights", "typical_price", "Typical price"),
        ]
        
        all_good = True
        for table, column, description in null_checks:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"   ❌ {description}: {count} NULL values in {table}.{column}")
                all_good = False
            else:
                print(f"   ✅ {description}: No NULL values")
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"   ❌ NULL check failed: {e}")
        return False


def test_price_ranges():
    """Test 2: Validate price ranges are reasonable."""
    print("\n2. Validating price ranges...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        all_good = True
        
        # Check for negative prices
        cursor.execute("SELECT COUNT(*) FROM expanded_deals WHERE price < 0")
        negative_count = cursor.fetchone()[0]
        if negative_count > 0:
            print(f"   ❌ Found {negative_count} deals with negative prices")
            all_good = False
        else:
            print(f"   ✅ No negative prices")
        
        # Check for unreasonably low prices (< $50)
        cursor.execute("SELECT COUNT(*) FROM expanded_deals WHERE price < 50")
        too_low_count = cursor.fetchone()[0]
        if too_low_count > 0:
            print(f"   ⚠️  Warning: {too_low_count} deals under $50 (verify these are real)")
        else:
            print(f"   ✅ No suspiciously low prices")
        
        # Check for unreasonably high prices (> $10,000)
        cursor.execute("SELECT COUNT(*) FROM expanded_deals WHERE price > 10000")
        too_high_count = cursor.fetchone()[0]
        if too_high_count > 0:
            print(f"   ⚠️  Warning: {too_high_count} deals over $10,000 (verify these are real)")
        else:
            print(f"   ✅ No suspiciously high prices")
        
        # Check price distribution
        cursor.execute("""
            SELECT 
                MIN(price) as min_price,
                AVG(price)::INT as avg_price,
                MAX(price) as max_price
            FROM expanded_deals
        """)
        min_p, avg_p, max_p = cursor.fetchone()
        print(f"   ℹ️  Price range: ${min_p} - ${max_p} (avg: ${avg_p})")
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"   ❌ Price validation failed: {e}")
        return False


def test_date_ranges():
    """Test 3: Validate date ranges are reasonable."""
    print("\n3. Validating date ranges...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        all_good = True
        today = datetime.now().date()
        one_year_future = today + timedelta(days=365)
        
        # Check for dates in the past
        cursor.execute("""
            SELECT COUNT(*) FROM expanded_deals 
            WHERE outbound_date < CURRENT_DATE
        """)
        past_count = cursor.fetchone()[0]
        if past_count > 0:
            print(f"   ⚠️  Warning: {past_count} deals with past outbound dates (old data)")
        else:
            print(f"   ✅ No past outbound dates")
        
        # Check for dates too far in future (> 1 year)
        cursor.execute("""
            SELECT COUNT(*) FROM expanded_deals 
            WHERE outbound_date > CURRENT_DATE + INTERVAL '1 year'
        """)
        far_future_count = cursor.fetchone()[0]
        if far_future_count > 0:
            print(f"   ⚠️  Warning: {far_future_count} deals with dates > 1 year out")
        else:
            print(f"   ✅ No dates beyond 1 year")
        
        # Check for return before outbound
        cursor.execute("""
            SELECT COUNT(*) FROM expanded_deals 
            WHERE return_date < outbound_date
        """)
        invalid_dates = cursor.fetchone()[0]
        if invalid_dates > 0:
            print(f"   ❌ Found {invalid_dates} deals where return < outbound")
            all_good = False
        else:
            print(f"   ✅ All return dates after outbound dates")
        
        # Check trip duration distribution
        cursor.execute("""
            SELECT 
                MIN(return_date - outbound_date) as min_duration,
                AVG(return_date - outbound_date)::INT as avg_duration,
                MAX(return_date - outbound_date) as max_duration
            FROM expanded_deals
        """)
        min_d, avg_d, max_d = cursor.fetchone()
        print(f"   ℹ️  Trip duration: {min_d} - {max_d} days (avg: {avg_d} days)")
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"   ❌ Date validation failed: {e}")
        return False


def test_data_consistency():
    """Test 4: Check data consistency between tables."""
    print("\n4. Checking data consistency...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        all_good = True
        
        # Check if all routes in deals have insights
        cursor.execute("""
            SELECT COUNT(DISTINCT origin || '-' || destination)
            FROM expanded_deals
        """)
        total_routes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM route_price_insights")
        insights_count = cursor.fetchone()[0]
        
        print(f"   ℹ️  Total unique routes in deals: {total_routes}")
        print(f"   ℹ️  Routes with insights: {insights_count}")
        
        if insights_count < total_routes * 0.8:  # Less than 80% coverage
            print(f"   ⚠️  Warning: Only {insights_count/total_routes*100:.1f}% of routes have insights")
            print(f"      Tip: Run calculate_price_insights.py to update")
        else:
            print(f"   ✅ Good insights coverage ({insights_count/total_routes*100:.1f}%)")
        
        # Check for orphaned insights (insights without recent deals)
        cursor.execute("""
            SELECT COUNT(*)
            FROM route_price_insights rpi
            WHERE NOT EXISTS (
                SELECT 1 FROM expanded_deals ed
                WHERE ed.origin = rpi.origin 
                  AND ed.destination = rpi.destination
                  AND ed.found_at > NOW() - INTERVAL '90 days'
            )
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned > 0:
            print(f"   ℹ️  {orphaned} insights without recent deals (old routes)")
        else:
            print(f"   ✅ All insights have recent deals")
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"   ❌ Consistency check failed: {e}")
        return False


def test_stale_data():
    """Test 5: Check for stale data."""
    print("\n5. Checking for stale data...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        all_good = True
        
        # Check when insights were last updated
        cursor.execute("""
            SELECT 
                MIN(last_updated) as oldest_update,
                MAX(last_updated) as newest_update,
                COUNT(*) FILTER (WHERE last_updated < NOW() - INTERVAL '7 days') as stale_count
            FROM route_price_insights
        """)
        oldest, newest, stale_count = cursor.fetchone()
        
        if stale_count and stale_count > 0:
            print(f"   ⚠️  Warning: {stale_count} insights not updated in 7+ days")
            print(f"      Tip: Run calculate_price_insights.py daily")
        else:
            print(f"   ✅ All insights recently updated")
        
        if oldest and newest:
            print(f"   ℹ️  Insights age: {oldest.date()} to {newest.date()}")
        
        # Check when deals were last scraped
        cursor.execute("""
            SELECT MAX(found_at) as last_scrape
            FROM expanded_deals
        """)
        last_scrape = cursor.fetchone()[0]
        
        if last_scrape:
            days_ago = (datetime.now() - last_scrape).days
            print(f"   ℹ️  Last scrape: {last_scrape.date()} ({days_ago} days ago)")
            
            if days_ago > 2:
                print(f"   ⚠️  Warning: No scrapes in {days_ago} days")
                print(f"      Tip: Run daily scraper to keep data fresh")
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"   ❌ Stale data check failed: {e}")
        return False


def test_index_usage():
    """Test 6: Check if indexes exist and are being used."""
    print("\n6. Checking database indexes...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        # Check if expected indexes exist
        expected_indexes = [
            'idx_origin_dest',
            'idx_found_at',
            'idx_posted',
            'idx_route_recency',
            'idx_search_region',
            'idx_price',
            'idx_route_insights_lookup',
            'idx_route_insights_quality',
        ]
        
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
              AND tablename IN ('expanded_deals', 'route_price_insights', 'scrape_runs')
        """)
        
        existing_indexes = [row[0] for row in cursor.fetchall()]
        
        all_good = True
        for idx in expected_indexes:
            if idx in existing_indexes:
                print(f"   ✅ Index exists: {idx}")
            else:
                print(f"   ⚠️  Missing index: {idx}")
                all_good = False
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"   ❌ Index check failed: {e}")
        return False


def run_all_tests():
    """Run all database integrity tests."""
    print("=" * 80)
    print("DATABASE INTEGRITY TEST")
    print("=" * 80)
    print()
    
    tests = [
        test_null_values,
        test_price_ranges,
        test_date_ranges,
        test_data_consistency,
        test_stale_data,
        test_index_usage,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n   ❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print()
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print("✅ ALL INTEGRITY CHECKS PASSED")
        print("=" * 80)
        return True
    else:
        print(f"⚠️  {total - passed}/{total} CHECKS HAD WARNINGS OR FAILURES")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
