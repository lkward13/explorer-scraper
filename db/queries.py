"""
Database query helpers for saving and retrieving deals.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy import text
from db.connection import get_db_session
from deal_models import ValidDeal, ExpandedRoute


def save_deal(deal: ValidDeal) -> int:
    """
    Save a ValidDeal to the database.
    
    Returns:
        The database ID of the inserted deal
    """
    with get_db_session() as db:
        # Convert Pydantic model to dict
        deal_dict = deal.model_dump()
        
        # Convert date fields to strings for JSON
        similar_deals_json = json.dumps([
            {
                "start_date": str(d["start_date"]),
                "end_date": str(d["end_date"]),
                "price": d["price"]
            }
            for d in deal_dict.get("similar_deals", [])
        ])
        
        flight_details_json = json.dumps(deal_dict.get("flight_details") or {})
        
        # Insert query - use bindparam approach to avoid %% escaping
        from sqlalchemy import bindparam
        
        query = text("""
            INSERT INTO deals (
                deal_id,
                origin_iata,
                origin_airport_name,
                destination_airport,
                destination_city,
                destination_country,
                destination_region,
                reference_price,
                usual_price_estimate,
                discount_amount,
                discount_pct,
                similar_dates_count,
                first_travel_date,
                last_travel_date,
                deal_quality_text,
                flight_details,
                search_region,
                source,
                is_valid_deal,
                is_featured_candidate,
                score,
                expanded_at,
                threshold_used,
                similar_deals
            ) VALUES (
                :deal_id,
                :origin_iata,
                :origin_airport_name,
                :destination_airport,
                :destination_city,
                :destination_country,
                :destination_region,
                :reference_price,
                :usual_price_estimate,
                :discount_amount,
                :discount_pct,
                :similar_dates_count,
                :first_travel_date,
                :last_travel_date,
                :deal_quality_text,
                CAST(:flight_details AS jsonb),
                :search_region,
                :source,
                :is_valid_deal,
                :is_featured_candidate,
                :score,
                :expanded_at,
                :threshold_used,
                CAST(:similar_deals AS jsonb)
            )
            ON CONFLICT (deal_id) DO UPDATE SET
                reference_price = EXCLUDED.reference_price,
                usual_price_estimate = EXCLUDED.usual_price_estimate,
                discount_amount = EXCLUDED.discount_amount,
                discount_pct = EXCLUDED.discount_pct,
                similar_dates_count = EXCLUDED.similar_dates_count,
                first_travel_date = EXCLUDED.first_travel_date,
                last_travel_date = EXCLUDED.last_travel_date,
                deal_quality_text = EXCLUDED.deal_quality_text,
                flight_details = EXCLUDED.flight_details,
                is_valid_deal = EXCLUDED.is_valid_deal,
                is_featured_candidate = EXCLUDED.is_featured_candidate,
                score = EXCLUDED.score,
                expanded_at = EXCLUDED.expanded_at,
                similar_deals = EXCLUDED.similar_deals
            RETURNING id
        """)
        
        result = db.execute(query, {
            "deal_id": deal.deal_id,
            "origin_iata": deal.origin,
            "origin_airport_name": deal.origin_airport_name,
            "destination_airport": deal.destination_airport,
            "destination_city": deal.destination_city,
            "destination_country": deal.destination_country,
            "destination_region": deal.destination_region,
            "reference_price": deal.reference_price,
            "usual_price_estimate": deal.usual_price_estimate,
            "discount_amount": deal.discount_amount,
            "discount_pct": float(deal.discount_pct) if deal.discount_pct else None,
            "similar_dates_count": deal.similar_dates_count,
            "first_travel_date": deal.first_travel_date,
            "last_travel_date": deal.last_travel_date,
            "deal_quality_text": deal.deal_quality_text,
            "flight_details": flight_details_json,
            "search_region": deal.search_region,
            "source": deal.source,
            "is_valid_deal": deal.is_valid_deal,
            "is_featured_candidate": deal.is_featured_candidate,
            "score": float(deal.score),
            "expanded_at": deal.expanded_at,
            "threshold_used": float(deal.threshold_used),
            "similar_deals": similar_deals_json
        })
        
        return result.scalar()


def get_deals_for_origin(
    origin: str,
    min_score: float = 0.0,
    region: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get deals for a specific origin, sorted by score.
    """
    with get_db_session() as db:
        query_str = """
            SELECT 
                deal_id,
                origin_iata,
                destination_airport,
                destination_city,
                destination_country,
                destination_region,
                reference_price,
                usual_price_estimate,
                discount_amount,
                discount_pct,
                similar_dates_count,
                first_travel_date,
                last_travel_date,
                deal_quality_text,
                is_featured_candidate,
                score,
                expanded_at
            FROM deals
            WHERE origin_iata = :origin
              AND is_valid_deal = TRUE
              AND score >= :min_score
        """
        
        params = {"origin": origin, "min_score": min_score, "limit": limit}
        
        if region:
            query_str += " AND destination_region = :region"
            params["region"] = region
        
        query_str += " ORDER BY score DESC LIMIT :limit"
        
        result = db.execute(text(query_str), params)
        
        deals = []
        for row in result:
            deals.append({
                "deal_id": row[0],
                "origin": row[1],
                "destination_airport": row[2],
                "destination_city": row[3],
                "destination_country": row[4],
                "destination_region": row[5],
                "reference_price": row[6],
                "usual_price_estimate": row[7],
                "discount_amount": row[8],
                "discount_pct": float(row[9]) if row[9] else None,
                "similar_dates_count": row[10],
                "first_travel_date": row[11],
                "last_travel_date": row[12],
                "deal_quality_text": row[13],
                "is_featured": row[14],
                "score": float(row[15]),
                "expanded_at": row[16]
            })
        
        return deals


def is_deal_recently_used(
    origin: str,
    destination: str,
    travel_start: date,
    travel_end: date
) -> bool:
    """
    Check if a similar deal was recently published.
    """
    with get_db_session() as db:
        query = text("""
            SELECT COUNT(*) 
            FROM used_deals
            WHERE origin_iata = :origin
              AND destination_airport = :destination
              AND expires_at > CURRENT_TIMESTAMP
              AND (
                  (:travel_start, :travel_end) OVERLAPS (first_travel_date, last_travel_date)
              )
        """)
        
        result = db.execute(query, {
            "origin": origin,
            "destination": destination,
            "travel_start": travel_start,
            "travel_end": travel_end
        })
        
        count = result.scalar()
        return count > 0


def mark_deal_as_used(
    deal_id: str,
    origin: str,
    destination: str,
    destination_region: str,
    travel_start: date,
    travel_end: date,
    published_in: str = "email"
) -> int:
    """
    Mark a deal as used (published).
    """
    with get_db_session() as db:
        query = text("""
            INSERT INTO used_deals (
                deal_id,
                origin_iata,
                destination_airport,
                destination_region,
                first_travel_date,
                last_travel_date,
                published_in
            ) VALUES (
                :deal_id,
                :origin,
                :destination,
                :region,
                :travel_start,
                :travel_end,
                :published_in
            )
            RETURNING id
        """)
        
        result = db.execute(query, {
            "deal_id": deal_id,
            "origin": origin,
            "destination": destination,
            "region": destination_region,
            "travel_start": travel_start,
            "travel_end": travel_end,
            "published_in": published_in
        })
        
        return result.scalar()


def get_featured_deals_by_region(
    origin: str,
    min_deals_for_bundle: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get featured deals grouped by region.
    Only includes regions with at least min_deals_for_bundle deals.
    """
    deals = get_deals_for_origin(origin, min_score=0.0)
    
    # Group by region
    by_region = {}
    for deal in deals:
        if not deal.get("is_featured"):
            continue
        
        region = deal["destination_region"]
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(deal)
    
    # Filter regions with < min_deals
    filtered = {
        region: deals_list
        for region, deals_list in by_region.items()
        if len(deals_list) >= min_deals_for_bundle
    }
    
    # Sort each region's deals by score
    for region in filtered:
        filtered[region].sort(key=lambda d: d["score"], reverse=True)
    
    return filtered


def cleanup_expired_used_deals() -> int:
    """
    Delete expired used_deals entries.
    Returns count of deleted rows.
    """
    with get_db_session() as db:
        query = text("DELETE FROM used_deals WHERE expires_at < CURRENT_TIMESTAMP")
        result = db.execute(query)
        return result.rowcount


def get_deal_stats_for_origin(origin: str) -> Dict[str, Any]:
    """
    Get statistics for deals from an origin.
    """
    with get_db_session() as db:
        query = text("""
            SELECT 
                COUNT(*) as total_deals,
                COUNT(*) FILTER (WHERE is_featured_candidate = TRUE) as featured_count,
                COUNT(DISTINCT destination_region) as regions_count,
                AVG(discount_pct) as avg_discount,
                AVG(score) as avg_score,
                MIN(reference_price) as cheapest_price,
                MAX(discount_pct) as best_discount
            FROM deals
            WHERE origin_iata = :origin
              AND is_valid_deal = TRUE
        """)
        
        result = db.execute(query, {"origin": origin})
        row = result.fetchone()
        
        return {
            "total_deals": row[0] or 0,
            "featured_count": row[1] or 0,
            "regions_count": row[2] or 0,
            "avg_discount_pct": float(row[3]) if row[3] else 0.0,
            "avg_score": float(row[4]) if row[4] else 0.0,
            "cheapest_price": row[5] or 0,
            "best_discount_pct": float(row[6]) if row[6] else 0.0,
        }


if __name__ == "__main__":
    print("Testing database queries...")
    print()
    
    # Test getting PHX stats (should be empty for now)
    stats = get_deal_stats_for_origin("PHX")
    print("PHX stats:")
    for key, value in stats.items():
        print(f"  • {key}: {value}")

