#!/usr/bin/env python3
"""
Full System Integration Test

Tests all components of the flight deal scraper system:
- Database connectivity
- Price insights calculation
- Deal selection (old and new methods)
- Data quality
- Performance

Usage:
    python test_full_system.py
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.config import get_connection_string, get_connection_params
from deal_selector import DealSelector
import psycopg2


def test_database_connection():
    """Test 1: Database connection."""
    print("1. Testing database connection...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            print("   ✅ Database connection successful")
            return True
        else:
            print("   ❌ Database connection returned unexpected result")
            return False
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False


def test_tables_exist():
    """Test 2: Check all required tables exist and have data."""
    print("\n2. Checking database tables...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        tables = ['expanded_deals', 'scrape_runs', 'route_price_insights']
        all_good = True
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count:,} rows")
            
            if table == 'expanded_deals' and count == 0:
                print(f"      ⚠️  Warning: No deals in database (run scraper first)")
                all_good = False
            elif table == 'route_price_insights' and count == 0:
                print(f"      ⚠️  Warning: No insights calculated (run calculate_price_insights.py)")
                all_good = False
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"   ❌ Table check failed: {e}")
        return False


def test_insights_calculation():
    """Test 3: Test insights calculation."""
    print("\n3. Testing insights calculation...")
    try:
        from scripts.calculate_price_insights import calculate_insights
        
        start_time = time.time()
        rows = calculate_insights(min_samples=7, lookback_days=90, verbose=False)
        elapsed = time.time() - start_time
        
        print(f"   ✅ Updated {rows:,} routes in {elapsed:.2f} seconds")
        
        if elapsed > 10:
            print(f"      ⚠️  Warning: Calculation took longer than expected (> 10s)")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Insights calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_old_deal_selection():
    """Test 4: Test old deal selection method."""
    print("\n4. Testing old deal selection method...")
    try:
        selector = DealSelector(get_connection_string())
        deals = selector.select_daily_deals(
            max_price=600,
            limit_per_origin=5
        )
        
        # Check structure
        if not isinstance(deals, dict):
            print(f"   ❌ Expected dict, got {type(deals)}")
            return False
        
        if 'individual' not in deals or 'regional' not in deals:
            print(f"   ❌ Missing required keys (individual, regional)")
            return False
        
        individual_count = len(deals['individual'])
        regional_count = len(deals['regional'])
        
        print(f"   ✅ Individual deals: {individual_count}")
        print(f"   ✅ Regional sales: {regional_count}")
        
        if individual_count == 0 and regional_count == 0:
            print(f"      ⚠️  Warning: No deals returned (check max_price threshold)")
        
        return True
    except Exception as e:
        print(f"   ❌ Old method failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_new_deal_selection():
    """Test 5: Test new deal selection with scoring."""
    print("\n5. Testing new deal selection with scoring...")
    try:
        selector = DealSelector(get_connection_string())
        deals = selector.select_daily_deals_with_scoring(
            min_quality_score=60,
            max_price=800
        )
        
        # Check structure
        if not isinstance(deals, list):
            print(f"   ❌ Expected list, got {type(deals)}")
            return False
        
        print(f"   ✅ Found {len(deals)} scored deals")
        
        if len(deals) == 0:
            print(f"      ⚠️  Warning: No deals returned (try lowering min_quality_score)")
            return True  # Not a failure, just no deals meet criteria
        
        # Check first deal has quality info
        first_deal = deals[0]
        
        required_keys = ['quality']
        for key in required_keys:
            if key not in first_deal:
                print(f"   ❌ Missing required key: {key}")
                return False
        
        quality = first_deal['quality']
        required_quality_keys = ['score', 'quality', 'insight', 'confidence']
        for key in required_quality_keys:
            if key not in quality:
                print(f"   ❌ Missing quality key: {key}")
                return False
        
        # Validate score range
        score = quality['score']
        if not (0 <= score <= 100):
            print(f"   ❌ Invalid score: {score} (should be 0-100)")
            return False
        
        # Validate quality level
        valid_qualities = ['excellent', 'great', 'good', 'fair', 'unknown']
        if quality['quality'] not in valid_qualities:
            print(f"   ❌ Invalid quality level: {quality['quality']}")
            return False
        
        # Validate confidence
        valid_confidences = ['high', 'medium', 'low']
        if quality['confidence'] not in valid_confidences:
            print(f"   ❌ Invalid confidence: {quality['confidence']}")
            return False
        
        print(f"   ✅ Quality scoring working")
        print(f"      Top deal: {first_deal['origin']} → {first_deal['destination']}")
        print(f"      Score: {score:.1f}")
        print(f"      Quality: {quality['quality']}")
        
        return True
    except Exception as e:
        print(f"   ❌ New method failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_quality():
    """Test 6: Check data quality distribution."""
    print("\n6. Checking data quality distribution...")
    try:
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data_quality, COUNT(*) 
            FROM route_price_insights 
            GROUP BY data_quality
            ORDER BY 
                CASE data_quality 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END
        """)
        
        results = cursor.fetchall()
        total = sum(count for _, count in results)
        
        if total == 0:
            print(f"   ⚠️  No insights data (run calculate_price_insights.py first)")
            cursor.close()
            conn.close()
            return True  # Not a failure, just no data yet
        
        high_count = 0
        for quality, count in results:
            percentage = (count / total * 100) if total > 0 else 0
            print(f"   ✅ {quality}: {count:,} routes ({percentage:.1f}%)")
            if quality == 'high':
                high_count = count
        
        # Check if at least 70% are high confidence
        high_percentage = (high_count / total * 100) if total > 0 else 0
        if high_percentage < 70:
            print(f"      ⚠️  Warning: Only {high_percentage:.1f}% high confidence (target: 70%+)")
            print(f"      Tip: Run more daily scrapes to increase confidence")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Data quality check failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 80)
    print("FULL SYSTEM INTEGRATION TEST")
    print("=" * 80)
    print()
    
    tests = [
        test_database_connection,
        test_tables_exist,
        test_insights_calculation,
        test_old_deal_selection,
        test_new_deal_selection,
        test_data_quality
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
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        return True
    else:
        print(f"❌ {total - passed}/{total} TESTS FAILED")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
