#!/usr/bin/env python3
"""
Quality Scoring System Test

Focused tests on the quality scoring system:
- Score calculation accuracy
- Quality level assignment
- Confidence level assignment
- Edge cases
- Consistency checks

Usage:
    python test_quality_scoring.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.config import get_connection_string, get_connection_params
from deal_selector import DealSelector
import psycopg2


def test_score_calculation():
    """Test 1: Verify score calculations are accurate."""
    print("1. Testing score calculation accuracy...")
    try:
        selector = DealSelector(get_connection_string())
        
        # Get a deal with insights
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        # Find a route with insights
        cursor.execute("""
            SELECT ed.origin, ed.destination, ed.price,
                   rpi.typical_price, rpi.low_price_threshold, rpi.min_price_seen
            FROM expanded_deals ed
            JOIN route_price_insights rpi 
              ON ed.origin = rpi.origin AND ed.destination = rpi.destination
            WHERE rpi.data_quality = 'high'
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if not result:
            print("   ⚠️  No deals with insights found (run scraper first)")
            cursor.close()
            conn.close()
            return True
        
        origin, dest, price, typical, low_threshold, min_seen = result
        
        # Create a test deal
        test_deal = {
            'origin': origin,
            'destination': dest,
            'price': price
        }
        
        # Calculate quality
        quality = selector._calculate_deal_quality_score(test_deal)
        
        # Verify score is in valid range
        if not (0 <= quality['score'] <= 100):
            print(f"   ❌ Invalid score: {quality['score']} (should be 0-100)")
            cursor.close()
            conn.close()
            return False
        
        print(f"   ✅ Score in valid range: {quality['score']:.1f}")
        
        # Verify score logic
        if price <= min_seen:
            expected_quality = 'excellent'
            if quality['quality'] != expected_quality:
                print(f"   ❌ Price <= min_seen but quality is {quality['quality']} (expected: {expected_quality})")
                cursor.close()
                conn.close()
                return False
            print(f"   ✅ Best price logic correct")
        elif price <= low_threshold:
            if quality['quality'] not in ['excellent', 'great']:
                print(f"   ❌ Price <= low_threshold but quality is {quality['quality']}")
                cursor.close()
                conn.close()
                return False
            print(f"   ✅ Great deal logic correct")
        elif price <= typical:
            if quality['quality'] not in ['excellent', 'great', 'good']:
                print(f"   ❌ Price <= typical but quality is {quality['quality']}")
                cursor.close()
                conn.close()
                return False
            print(f"   ✅ Good deal logic correct")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Score calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_levels():
    """Test 2: Verify quality level assignments."""
    print("\n2. Testing quality level assignments...")
    try:
        selector = DealSelector(get_connection_string())
        deals = selector.select_daily_deals_with_scoring(
            min_quality_score=0,  # Get all deals
            max_price=10000
        )
        
        if not deals:
            print("   ⚠️  No deals found (run scraper first)")
            return True
        
        # Count quality levels
        quality_counts = {}
        for deal in deals:
            quality = deal['quality']['quality']
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        valid_qualities = ['excellent', 'great', 'good', 'fair', 'unknown']
        all_good = True
        
        for quality, count in quality_counts.items():
            if quality not in valid_qualities:
                print(f"   ❌ Invalid quality level: {quality}")
                all_good = False
            else:
                print(f"   ✅ {quality}: {count} deals")
        
        # Check if we have some distribution (not all one quality)
        if len(quality_counts) == 1 and list(quality_counts.keys())[0] == 'excellent':
            print(f"   ⚠️  Warning: All deals are 'excellent' - verify scoring logic")
        
        return all_good
    except Exception as e:
        print(f"   ❌ Quality level test failed: {e}")
        return False


def test_confidence_levels():
    """Test 3: Verify confidence level assignments."""
    print("\n3. Testing confidence level assignments...")
    try:
        selector = DealSelector(get_connection_string())
        deals = selector.select_daily_deals_with_scoring(
            min_quality_score=0,
            max_price=10000
        )
        
        if not deals:
            print("   ⚠️  No deals found (run scraper first)")
            return True
        
        # Count confidence levels
        confidence_counts = {}
        for deal in deals:
            confidence = deal['quality']['confidence']
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        valid_confidences = ['high', 'medium', 'low']
        all_good = True
        
        for confidence, count in confidence_counts.items():
            if confidence not in valid_confidences:
                print(f"   ❌ Invalid confidence level: {confidence}")
                all_good = False
            else:
                percentage = count / len(deals) * 100
                print(f"   ✅ {confidence}: {count} deals ({percentage:.1f}%)")
        
        # Check if most are high confidence
        high_count = confidence_counts.get('high', 0)
        high_percentage = high_count / len(deals) * 100 if deals else 0
        
        if high_percentage < 70:
            print(f"   ⚠️  Warning: Only {high_percentage:.1f}% high confidence (target: 70%+)")
        else:
            print(f"   ✅ Good confidence distribution")
        
        return all_good
    except Exception as e:
        print(f"   ❌ Confidence level test failed: {e}")
        return False


def test_edge_cases():
    """Test 4: Test edge cases and error handling."""
    print("\n4. Testing edge cases...")
    try:
        selector = DealSelector(get_connection_string())
        
        all_good = True
        
        # Test 1: No deals with impossible criteria
        deals = selector.select_daily_deals_with_scoring(
            min_quality_score=101,  # Impossible
            max_price=1
        )
        if len(deals) != 0:
            print(f"   ❌ Expected 0 deals with impossible criteria, got {len(deals)}")
            all_good = False
        else:
            print(f"   ✅ Impossible criteria returns empty list")
        
        # Test 2: Fake origins
        deals = selector.select_daily_deals_with_scoring(
            origins=['XXX', 'YYY'],
            min_quality_score=0
        )
        if len(deals) != 0:
            print(f"   ❌ Expected 0 deals with fake origins, got {len(deals)}")
            all_good = False
        else:
            print(f"   ✅ Fake origins returns empty list")
        
        # Test 3: Very low quality threshold (should return many)
        deals = selector.select_daily_deals_with_scoring(
            min_quality_score=0,
            max_price=10000
        )
        if len(deals) == 0:
            print(f"   ⚠️  Warning: No deals even with min_quality_score=0")
        else:
            print(f"   ✅ Low threshold returns {len(deals)} deals")
        
        # Test 4: Deal without insights (should handle gracefully)
        conn = psycopg2.connect(**get_connection_params())
        cursor = conn.cursor()
        
        # Find a deal without insights
        cursor.execute("""
            SELECT ed.origin, ed.destination, ed.price
            FROM expanded_deals ed
            WHERE NOT EXISTS (
                SELECT 1 FROM route_price_insights rpi
                WHERE rpi.origin = ed.origin AND rpi.destination = ed.destination
            )
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            origin, dest, price = result
            test_deal = {'origin': origin, 'destination': dest, 'price': price}
            quality = selector._calculate_deal_quality_score(test_deal)
            
            if quality['quality'] != 'unknown':
                print(f"   ❌ Deal without insights should be 'unknown', got '{quality['quality']}'")
                all_good = False
            else:
                print(f"   ✅ Deal without insights handled correctly")
        else:
            print(f"   ℹ️  All deals have insights (good!)")
        
        cursor.close()
        conn.close()
        
        return all_good
    except Exception as e:
        print(f"   ❌ Edge case test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_consistency():
    """Test 5: Check consistency of scoring."""
    print("\n5. Testing scoring consistency...")
    try:
        selector = DealSelector(get_connection_string())
        
        # Get deals twice and verify scores are consistent
        deals1 = selector.select_daily_deals_with_scoring(
            min_quality_score=70,
            max_price=800
        )
        
        deals2 = selector.select_daily_deals_with_scoring(
            min_quality_score=70,
            max_price=800
        )
        
        if len(deals1) != len(deals2):
            print(f"   ❌ Inconsistent results: {len(deals1)} vs {len(deals2)} deals")
            return False
        
        print(f"   ✅ Consistent deal count: {len(deals1)} deals")
        
        # Check if scores are identical for same deals
        if deals1 and deals2:
            # Compare first deal
            d1 = deals1[0]
            d2 = deals2[0]
            
            if d1['origin'] == d2['origin'] and d1['destination'] == d2['destination']:
                if d1['quality']['score'] != d2['quality']['score']:
                    print(f"   ❌ Inconsistent scores for same deal")
                    return False
                else:
                    print(f"   ✅ Scores are consistent")
        
        # Check that higher scores come first (sorting works)
        if len(deals1) > 1:
            for i in range(len(deals1) - 1):
                if deals1[i]['quality']['score'] < deals1[i+1]['quality']['score']:
                    print(f"   ❌ Deals not sorted by score")
                    return False
            print(f"   ✅ Deals properly sorted by score")
        
        return True
    except Exception as e:
        print(f"   ❌ Consistency test failed: {e}")
        return False


def run_all_tests():
    """Run all quality scoring tests."""
    print("=" * 80)
    print("QUALITY SCORING SYSTEM TEST")
    print("=" * 80)
    print()
    
    tests = [
        test_score_calculation,
        test_quality_levels,
        test_confidence_levels,
        test_edge_cases,
        test_consistency,
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
        print("✅ ALL SCORING TESTS PASSED")
        print("=" * 80)
        return True
    else:
        print(f"❌ {total - passed}/{total} TESTS FAILED")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
