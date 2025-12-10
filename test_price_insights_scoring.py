#!/usr/bin/env python3
"""
Test the price insights quality scoring system.

Shows how deals are scored based on historical data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.config import get_connection_string
from deal_selector import DealSelector


def test_scoring():
    """Test quality scoring with real deals."""
    
    selector = DealSelector(get_connection_string())
    
    print("=" * 80)
    print("PRICE INSIGHTS QUALITY SCORING TEST")
    print("=" * 80)
    print()
    
    # Get top scored deals
    print("Getting deals with quality scoring (min score: 60)...")
    scored_deals = selector.select_daily_deals_with_scoring(
        max_price=1000,
        min_quality_score=60,
        limit_per_origin=5
    )
    
    print(f"Found {len(scored_deals)} deals meeting quality threshold")
    print()
    
    # Show top 20 deals
    print("=" * 80)
    print("TOP 20 DEALS BY QUALITY SCORE")
    print("=" * 80)
    print()
    
    for i, deal in enumerate(scored_deals[:20], 1):
        quality = deal['quality']
        
        # Quality badge
        if quality['quality'] == 'excellent':
            badge = "🏆 EXCELLENT"
        elif quality['quality'] == 'great':
            badge = "⭐ GREAT"
        elif quality['quality'] == 'good':
            badge = "✅ GOOD"
        else:
            badge = "📊 FAIR"
        
        # Confidence indicator
        conf_emoji = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴'
        }.get(quality['confidence'], '⚪')
        
        print(f"{i:2}. {badge:15} | Score: {quality['score']:5.1f} | {conf_emoji} {quality['confidence']:6}")
        print(f"    {deal['origin']} → {deal['destination_city']:20} ${deal['price']:4}")
        print(f"    {quality['insight']}")
        if quality['typical_price']:
            print(f"    Typical: ${quality['typical_price']} | This deal: ${deal['price']}")
        print()
    
    # Show distribution by quality
    print("=" * 80)
    print("DEAL DISTRIBUTION BY QUALITY")
    print("=" * 80)
    print()
    
    by_quality = {}
    for deal in scored_deals:
        q = deal['quality']['quality']
        by_quality[q] = by_quality.get(q, 0) + 1
    
    for quality in ['excellent', 'great', 'good', 'fair', 'unknown']:
        count = by_quality.get(quality, 0)
        if count > 0:
            bar = '█' * (count // 10)
            print(f"  {quality.upper():10} | {count:4} deals | {bar}")
    print()
    
    # Show distribution by confidence
    print("=" * 80)
    print("CONFIDENCE DISTRIBUTION")
    print("=" * 80)
    print()
    
    by_confidence = {}
    for deal in scored_deals:
        conf = deal['quality']['confidence']
        by_confidence[conf] = by_confidence.get(conf, 0) + 1
    
    for conf in ['high', 'medium', 'low']:
        count = by_confidence.get(conf, 0)
        if count > 0:
            pct = count / len(scored_deals) * 100
            bar = '█' * int(pct / 2)
            print(f"  {conf.upper():6} | {count:4} deals ({pct:5.1f}%) | {bar}")
    print()
    
    # Show some examples of each quality level
    print("=" * 80)
    print("EXAMPLES BY QUALITY LEVEL")
    print("=" * 80)
    print()
    
    for quality_level in ['excellent', 'great', 'good']:
        examples = [d for d in scored_deals if d['quality']['quality'] == quality_level][:3]
        if examples:
            print(f"\n{quality_level.upper()} Examples:")
            print("-" * 60)
            for deal in examples:
                q = deal['quality']
                print(f"  {deal['origin']} → {deal['destination']} | "
                      f"${deal['price']} (typical: ${q['typical_price']}) | "
                      f"Score: {q['score']:.1f}")
    
    print()


if __name__ == "__main__":
    test_scoring()

