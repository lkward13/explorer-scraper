"""
Deal filtering and scoring logic.
Implements the % off + flexibility rules defined in SCALING_TO_100_AIRPORTS.md
"""

from typing import Optional
from deal_models import ExpandedRoute, ValidDeal, DealFilterConfig, RouteMetadata
from datetime import datetime, date


def compute_deal_metrics(expansion: ExpandedRoute) -> dict:
    """
    Compute core metrics from an ExpandedRoute.
    Returns dict with: discount_amount, usual_price, discount_pct, flex_count
    """
    discount_amount = expansion.deal_quality_amount or 0
    ref_price = expansion.reference_price
    usual_price = ref_price + discount_amount if discount_amount > 0 else None
    
    discount_pct = (discount_amount / usual_price) if usual_price and usual_price > 0 else 0
    flex_count = len(expansion.similar_deals)
    
    return {
        "discount_amount": discount_amount,
        "usual_price": usual_price,
        "discount_pct": discount_pct,
        "flex_count": flex_count
    }


def is_valid_deal(expansion: ExpandedRoute, config: DealFilterConfig) -> bool:
    """
    Determine if an expansion meets the minimum requirements to be a valid deal.
    
    Rules:
    - discount_pct >= config.min_discount_pct (default: 20%)
    - flex_count >= config.min_similar_dates (default: 5)
    """
    metrics = compute_deal_metrics(expansion)
    
    if metrics["flex_count"] < config.min_similar_dates:
        return False
    
    if metrics["discount_pct"] < config.min_discount_pct:
        return False
    
    return True


def is_featured_deal(expansion: ExpandedRoute, config: DealFilterConfig) -> bool:
    """
    Determine if a deal meets the higher bar for being "featured" 
    (email/homepage/social worthy).
    
    Rules:
    - discount_pct >= config.featured_min_discount_pct (default: 25%)
    - flex_count >= config.featured_min_similar_dates (default: 10)
    """
    metrics = compute_deal_metrics(expansion)
    
    if metrics["flex_count"] < config.featured_min_similar_dates:
        return False
    
    if metrics["discount_pct"] < config.featured_min_discount_pct:
        return False
    
    return True


def compute_deal_score(expansion: ExpandedRoute, config: DealFilterConfig) -> float:
    """
    Compute a normalized score (0-1) for a deal based on discount % and flexibility.
    
    Formula:
        score = discount_weight * (discount_pct / 0.5) + flexibility_weight * (flex_count / 30)
    
    - Discount capped at 50% off
    - Flexibility capped at 30 dates
    - Default weights: 50/50
    """
    metrics = compute_deal_metrics(expansion)
    
    # Normalize discount_pct (cap at 50% off)
    pct_score = min(metrics["discount_pct"], 0.5) / 0.5
    
    # Normalize flex_count (cap at 30 dates)
    flex_score = min(metrics["flex_count"], 30) / 30.0
    
    # Weighted average
    score = (config.discount_weight * pct_score + 
             config.flexibility_weight * flex_score)
    
    return score


def expansion_to_valid_deal(
    expansion: ExpandedRoute,
    explore_dest_name: str,
    destination_airport: str,
    destination_city: str,
    destination_country: str,
    destination_region: str,
    search_region: str,
    config: DealFilterConfig = DealFilterConfig()
) -> Optional[ValidDeal]:
    """
    Convert an ExpandedRoute to a ValidDeal if it passes filters.
    Returns None if deal doesn't meet minimum thresholds.
    
    Args:
        expansion: The raw expansion data
        explore_dest_name: Original destination name from Explore card
        destination_airport: IATA code (resolved)
        destination_city: City name
        destination_country: ISO-2 country code
        destination_region: One of the 8 regions
        search_region: Which Explore region found it
        config: Filtering/scoring configuration
    """
    # Check if valid
    if not is_valid_deal(expansion, config):
        return None
    
    # Compute metrics
    metrics = compute_deal_metrics(expansion)
    
    # Check featured status
    featured = is_featured_deal(expansion, config)
    
    # Compute score
    score = compute_deal_score(expansion, config)
    
    # Generate deal ID
    deal_id = f"{expansion.origin.lower()}-{destination_airport.lower()}-{expansion.reference_start.strftime('%Y%m%d')}"
    
    # Get date range
    if expansion.similar_deals:
        first_date = min(d.start_date for d in expansion.similar_deals)
        last_date = max(d.end_date for d in expansion.similar_deals)
    else:
        first_date = expansion.reference_start
        last_date = expansion.reference_end
    
    return ValidDeal(
        deal_id=deal_id,
        origin=expansion.origin,
        destination_airport=destination_airport,
        destination_city=destination_city,
        destination_country=destination_country,
        destination_region=destination_region,
        reference_price=expansion.reference_price,
        usual_price_estimate=metrics["usual_price"],
        discount_amount=metrics["discount_amount"],
        discount_pct=metrics["discount_pct"],
        similar_dates_count=metrics["flex_count"],
        first_travel_date=first_date,
        last_travel_date=last_date,
        deal_quality_text=expansion.deal_quality,
        flight_details=expansion.flight_details,
        search_region=search_region,
        is_valid_deal=True,
        is_featured_candidate=featured,
        score=score,
        expanded_at=datetime.now(),
        threshold_used=expansion.threshold
    )


# ============================================================================
# Convenience functions for batch processing
# ============================================================================

def filter_and_score_expansions(
    expansions: list,
    config: DealFilterConfig = DealFilterConfig(),
    verbose: bool = False
) -> list:
    """
    Filter a list of expansion results and return only valid deals with scores.
    
    Args:
        expansions: List of dicts with keys: 'expansion', 'explore_deal', 'route_meta'
        config: Filtering configuration
        verbose: Print filtering decisions
    
    Returns:
        List of ValidDeal objects
    """
    valid_deals = []
    
    for item in expansions:
        expansion = item.get("expansion")
        explore_deal = item.get("explore_deal", {})
        route_meta = item.get("route_meta", {})
        
        if not expansion:
            continue
        
        # Convert raw dict to ExpandedRoute if needed
        if isinstance(expansion, dict):
            from deal_converter import parse_expanded_route
            try:
                expansion = parse_expanded_route(expansion)
            except Exception as e:
                if verbose:
                    print(f"[warn] Failed to parse expansion: {e}")
                continue
        
        # Get destination info
        dest_airport = route_meta.get("destination_airport") or expansion.actual_destination or expansion.destination
        dest_city = route_meta.get("destination_city") or explore_deal.get("destination", dest_airport)
        dest_country = route_meta.get("destination_country", "XX")
        dest_region = route_meta.get("destination_region", "other")
        search_region = explore_deal.get("search_region", dest_region)
        
        # Try to convert
        valid_deal = expansion_to_valid_deal(
            expansion=expansion,
            explore_dest_name=dest_city,
            destination_airport=dest_airport,
            destination_city=dest_city,
            destination_country=dest_country,
            destination_region=dest_region,
            search_region=search_region,
            config=config
        )
        
        if valid_deal:
            valid_deals.append(valid_deal)
            if verbose:
                print(f"✓ {valid_deal.destination_city}: {valid_deal.discount_pct_display} off, "
                      f"{valid_deal.similar_dates_count} dates, score={valid_deal.score:.2f}")
        elif verbose:
            metrics = compute_deal_metrics(expansion)
            print(f"✗ {dest_city}: {int(metrics['discount_pct']*100)}% off, "
                  f"{metrics['flex_count']} dates (below threshold)")
    
    return valid_deals


# ============================================================================
# Example usage / testing
# ============================================================================

if __name__ == "__main__":
    # Example: test with mock data
    from deal_models import ExpandedRoute, FlightDetails, DatePrice
    
    config = DealFilterConfig()
    print(f"Filters: {config.min_discount_pct*100}% off, {config.min_similar_dates}+ dates")
    print()
    
    # Test case 1: Good deal (Tahiti)
    tahiti = ExpandedRoute(
        origin="PHX",
        destination="PPT",
        reference_price=952,
        reference_start=date(2025, 11, 29),
        reference_end=date(2025, 12, 10),
        similar_deals=[DatePrice(start_date=date(2025, 11, 29), end_date=date(2025, 12, 10), price=952) for _ in range(20)],
        all_dates=[],
        deal_quality="$388 cheaper than usual",
        deal_quality_amount=388,
        flight_details=FlightDetails(airline="Alaska", duration="17h 5m", stops=1),
        price_range={}
    )
    
    deal = expansion_to_valid_deal(
        tahiti, "Tahiti", "PPT", "Tahiti", "PF", "oceania", "oceania", config
    )
    
    if deal:
        print(f"✅ Tahiti: {deal.discount_pct_display} off, score={deal.score:.2f}, featured={deal.is_featured_candidate}")
    else:
        print("❌ Tahiti: rejected")
    
    # Test case 2: Below threshold
    weak = ExpandedRoute(
        origin="PHX",
        destination="SEA",
        reference_price=100,
        reference_start=date(2025, 12, 1),
        reference_end=date(2025, 12, 5),
        similar_deals=[DatePrice(start_date=date(2025, 12, 1), end_date=date(2025, 12, 5), price=100)],  # only 1
        all_dates=[],
        deal_quality="$15 cheaper than usual",
        deal_quality_amount=15,  # only 13% off
        flight_details=FlightDetails(airline="Alaska", duration="2h 30m", stops=0),
        price_range={}
    )
    
    deal2 = expansion_to_valid_deal(
        weak, "Seattle", "SEA", "Seattle", "US", "north_america", "anywhere", config
    )
    
    if deal2:
        print(f"✅ Seattle: {deal2.discount_pct_display} off, score={deal2.score:.2f}")
    else:
        metrics = compute_deal_metrics(weak)
        print(f"❌ Seattle: {int(metrics['discount_pct']*100)}% off, {metrics['flex_count']} dates (rejected)")
