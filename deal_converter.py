"""
Converters to transform raw JSON outputs into typed deal models.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path
import json

from deal_models import (
    FlightDetails, DatePrice, ExpandedRoute, ValidDeal,
    RouteMetadata, DealFilterConfig, RegionBundle, SingleDeal,
    OriginWeeklyPayload
)


# ============================================================================
# Region classification helpers
# ============================================================================

# Simple country → region mapping (expand as needed)
COUNTRY_TO_REGION = {
    "US": "north_america",
    "CA": "north_america",
    "MX": "central_america",
    "GT": "central_america",
    "BZ": "central_america",
    "SV": "central_america",
    "HN": "central_america",
    "NI": "central_america",
    "CR": "central_america",
    "PA": "central_america",
    "BR": "south_america",
    "AR": "south_america",
    "CL": "south_america",
    "CO": "south_america",
    "PE": "south_america",
    "EC": "south_america",
    "VE": "south_america",
    "UY": "south_america",
    "PY": "south_america",
    "BO": "south_america",
    "GY": "south_america",
    "SR": "south_america",
    "GF": "south_america",
    "BS": "caribbean",
    "JM": "caribbean",
    "CU": "caribbean",
    "DO": "caribbean",
    "PR": "caribbean",
    "TT": "caribbean",
    "BB": "caribbean",
    "AW": "caribbean",
    "KY": "caribbean",
    "VG": "caribbean",
    "GB": "europe",
    "FR": "europe",
    "DE": "europe",
    "ES": "europe",
    "IT": "europe",
    "PT": "europe",
    "NL": "europe",
    "BE": "europe",
    "CH": "europe",
    "AT": "europe",
    "SE": "europe",
    "NO": "europe",
    "DK": "europe",
    "FI": "europe",
    "IE": "europe",
    "PL": "europe",
    "CZ": "europe",
    "GR": "europe",
    "IS": "europe",
    "ZA": "africa",
    "EG": "africa",
    "MA": "africa",
    "KE": "africa",
    "TZ": "africa",
    "TH": "south_east_asia",
    "VN": "south_east_asia",
    "SG": "south_east_asia",
    "MY": "south_east_asia",
    "ID": "south_east_asia",
    "PH": "south_east_asia",
    "AU": "oceania",
    "NZ": "oceania",
    "PF": "oceania",  # French Polynesia (Tahiti)
    "FJ": "oceania",
}

# Airport → country mapping (simplified - in production use a full DB)
AIRPORT_TO_COUNTRY = {
    "DUB": "IE", "CDG": "FR", "LHR": "GB", "BCN": "ES", "FCO": "IT",
    "AMS": "NL", "MAD": "ES", "MUC": "DE", "ZRH": "CH", "VIE": "AT",
    "JNB": "ZA", "CPT": "ZA", "CAI": "EG", "CMN": "MA",
    "PPT": "PF", "AKL": "NZ", "SYD": "AU", "MEL": "AU",
    "BKK": "TH", "SGN": "VN", "SIN": "SG", "KUL": "MY",
    "SJU": "PR", "CUN": "MX", "NAS": "BS", "AUA": "AW",
    "GRU": "BR", "EZE": "AR", "SCL": "CL", "BOG": "CO",
    "LIM": "PE", "GYE": "EC", "UIO": "EC", "CCS": "VE",
    "SAP": "HN",  # San Pedro Sula
}

# City name → IATA + country (for when we only have city names)
CITY_TO_AIRPORT = {
    "Dublin": ("DUB", "IE"),
    "Paris": ("CDG", "FR"),
    "London": ("LHR", "GB"),
    "Barcelona": ("BCN", "ES"),
    "Rome": ("FCO", "IT"),
    "Amsterdam": ("AMS", "NL"),
    "Madrid": ("MAD", "ES"),
    "Johannesburg": ("JNB", "ZA"),
    "Tahiti": ("PPT", "PF"),
    "San Juan": ("SJU", "PR"),
}


def classify_destination_region(airport_code: str, city_name: str) -> tuple[str, str, str]:
    """
    Classify destination into region.
    Returns: (region, country_code, airport_code)
    """
    # Try airport code lookup
    country = AIRPORT_TO_COUNTRY.get(airport_code)
    if not country:
        # Try city name lookup
        if city_name in CITY_TO_AIRPORT:
            airport_code, country = CITY_TO_AIRPORT[city_name]
    
    if not country:
        # Fallback
        return "other", "XX", airport_code
    
    region = COUNTRY_TO_REGION.get(country, "other")
    return region, country, airport_code


# ============================================================================
# Convert raw expansion JSON to ExpandedRoute
# ============================================================================

def parse_expanded_route(raw: Dict[str, Any]) -> ExpandedRoute:
    """Convert raw expand_dates output to ExpandedRoute model."""
    
    # Parse dates
    similar_deals = [
        DatePrice(
            start_date=date.fromisoformat(d["start_date"]),
            end_date=date.fromisoformat(d["end_date"]),
            price=d["price"]
        )
        for d in raw.get("similar_deals", [])
    ]
    
    all_dates = [
        DatePrice(
            start_date=date.fromisoformat(d["start_date"]),
            end_date=date.fromisoformat(d["end_date"]),
            price=d["price"]
        )
        for d in raw.get("all_dates", [])
    ]
    
    # Parse flight details
    fd_raw = raw.get("flight_details", {})
    flight_details = FlightDetails(
        airline=fd_raw.get("airline"),
        duration=fd_raw.get("duration"),
        stops=fd_raw.get("stops"),
        departure_time=fd_raw.get("departure_time"),
        arrival_time=fd_raw.get("arrival_time")
    )
    
    return ExpandedRoute(
        origin=raw["origin"],
        destination=raw["destination"],
        actual_destination=raw.get("actual_destination"),
        reference_price=raw["reference_price"],
        reference_start=date.fromisoformat(raw["reference_start"]),
        reference_end=date.fromisoformat(raw["reference_end"]),
        threshold=raw.get("threshold", 0.10),
        price_range=raw.get("price_range", {}),
        similar_deals=similar_deals,
        all_dates=all_dates,
        deal_quality=raw.get("deal_quality"),
        deal_quality_amount=raw.get("deal_quality_amount"),
        flight_details=flight_details,
        raw_responses=raw.get("raw_responses", [])
    )


# ============================================================================
# Convert ExpandedRoute to ValidDeal
# ============================================================================

def expanded_route_to_valid_deal(
    expanded: ExpandedRoute,
    explore_dest_name: str,
    search_region: str,
    config: DealFilterConfig = DealFilterConfig()
) -> Optional[ValidDeal]:
    """
    Convert an ExpandedRoute to ValidDeal, applying filters and scoring.
    Returns None if deal doesn't meet minimum thresholds.
    """
    
    # Compute discount metrics
    discount_amount = expanded.deal_quality_amount or 0
    ref_price = expanded.reference_price
    usual_price = ref_price + discount_amount if discount_amount > 0 else None
    
    if not usual_price or usual_price == 0:
        return None  # Can't compute discount %
    
    discount_pct = discount_amount / usual_price
    flex_count = len(expanded.similar_deals)
    
    # Apply base filters
    if flex_count < config.min_similar_dates:
        return None
    
    if discount_pct < config.min_discount_pct:
        return None
    
    # Classify destination
    region, country, airport = classify_destination_region(
        expanded.actual_destination or expanded.destination,
        explore_dest_name
    )
    
    # Compute score
    pct_score = min(discount_pct, 0.5) / 0.5  # cap at 50% off
    flex_score = min(flex_count, 30) / 30.0   # cap at 30 dates
    score = (config.discount_weight * pct_score + 
             config.flexibility_weight * flex_score)
    
    # Check if featured
    is_featured = (
        discount_pct >= config.featured_min_discount_pct and
        flex_count >= config.featured_min_similar_dates
    )
    
    # Generate deal ID
    deal_id = f"{expanded.origin.lower()}-{airport.lower()}-{expanded.reference_start.strftime('%Y%m%d')}"
    
    # Get date range
    first_date = min(d.start_date for d in expanded.similar_deals)
    last_date = max(d.end_date for d in expanded.similar_deals)
    
    return ValidDeal(
        deal_id=deal_id,
        origin=expanded.origin,
        destination_airport=airport,
        destination_city=explore_dest_name,
        destination_country=country,
        destination_region=region,
        reference_price=ref_price,
        usual_price_estimate=usual_price,
        discount_amount=discount_amount,
        discount_pct=discount_pct,
        similar_dates_count=flex_count,
        first_travel_date=first_date,
        last_travel_date=last_date,
        deal_quality_text=expanded.deal_quality,
        flight_details=expanded.flight_details,
        search_region=search_region,
        is_valid_deal=True,
        is_featured_candidate=is_featured,
        score=score,
        expanded_at=datetime.now(),
        threshold_used=expanded.threshold
    )


# ============================================================================
# Convert raw find_and_expand_deals output to ValidDeals
# ============================================================================

def parse_find_and_expand_output(
    raw_json: Dict[str, Any],
    config: DealFilterConfig = DealFilterConfig()
) -> List[ValidDeal]:
    """
    Parse the output from find_and_expand_deals.py into ValidDeal objects.
    """
    valid_deals = []
    
    for deal_data in raw_json.get("expanded_deals", []):
        explore_deal = deal_data["explore_deal"]
        expansion = deal_data["expansion"]
        
        # Convert expansion to ExpandedRoute first
        expanded = ExpandedRoute(
            origin=expansion["origin"],
            destination=expansion["destination"],
            actual_destination=expansion.get("actual_destination"),
            reference_price=expansion["reference_price"],
            reference_start=date.fromisoformat(expansion["reference_start"]),
            reference_end=date.fromisoformat(expansion["reference_end"]),
            threshold=expansion.get("threshold", 0.10),
            price_range=expansion.get("price_range", {}),
            similar_deals=[
                DatePrice(
                    start_date=date.fromisoformat(d["start_date"]),
                    end_date=date.fromisoformat(d["end_date"]),
                    price=d["price"]
                )
                for d in expansion.get("similar_deals", [])
            ],
            all_dates=[],  # Not needed for ValidDeal
            deal_quality=expansion.get("deal_quality"),
            deal_quality_amount=expansion.get("deal_quality_amount"),
            flight_details=FlightDetails(**expansion.get("flight_details", {})),
            raw_responses=expansion.get("raw_responses", [])
        )
        
        # Convert to ValidDeal
        valid_deal = expanded_route_to_valid_deal(
            expanded=expanded,
            explore_dest_name=explore_deal["destination"],
            search_region=explore_deal["search_region"],
            config=config
        )
        
        if valid_deal:
            valid_deals.append(valid_deal)
    
    return valid_deals


# ============================================================================
# Group ValidDeals into region bundles and singles
# ============================================================================

def create_weekly_payload(
    origin: str,
    valid_deals: List[ValidDeal],
    week_of: date,
    config: DealFilterConfig = DealFilterConfig()
) -> OriginWeeklyPayload:
    """Group valid deals into bundles and singles for weekly output."""
    
    from collections import defaultdict
    
    # Group by region
    by_region = defaultdict(list)
    for deal in valid_deals:
        by_region[deal.destination_region].append(deal)
    
    bundles = []
    singles = []
    
    for region, deals in by_region.items():
        deals_sorted = sorted(deals, key=lambda d: d.score, reverse=True)
        
        if len(deals_sorted) >= config.min_deals_for_bundle:
            # Create bundle
            min_pct = min(d.discount_pct for d in deals_sorted if d.discount_pct)
            max_pct = max(d.discount_pct for d in deals_sorted if d.discount_pct)
            
            bundle = RegionBundle(
                origin=origin,
                destination_region=region,
                region_label=region.replace("_", " ").title(),
                title=f"{region.replace('_', ' ').title()} is on sale from {origin}",
                subtitle=f"{len(deals_sorted)} cities {int(min_pct*100)}–{int(max_pct*100)}% off",
                deals=deals_sorted[:5],  # top 5 for the bundle
                stats={
                    "deals_in_bundle": len(deals_sorted),
                    "average_discount_pct": sum(d.discount_pct for d in deals_sorted if d.discount_pct) / len(deals_sorted),
                    "average_similar_dates": sum(d.similar_dates_count for d in deals_sorted) / len(deals_sorted)
                }
            )
            bundles.append(bundle)
        else:
            # Treat as singles
            for deal in deals_sorted:
                single = SingleDeal(
                    title=f"{deal.destination_city} from {origin} – {deal.discount_pct_display} off",
                    deal=deal
                )
                singles.append(single)
    
    # Sort bundles by average score
    bundles = sorted(bundles, key=lambda b: sum(d.score for d in b.deals) / len(b.deals), reverse=True)
    
    # Sort singles by score
    singles = sorted(singles, key=lambda s: s.deal.score, reverse=True)
    
    return OriginWeeklyPayload(
        origin=origin,
        week_of=week_of,
        bundles=bundles,
        single_deals=singles,
        summary={
            "total_destinations_scanned": len(valid_deals),
            "valid_deals_found": len(valid_deals),
            "featured_deals_picked": sum(len(b.deals) for b in bundles) + len(singles),
            "min_discount_pct": config.min_discount_pct,
            "min_similar_dates": config.min_similar_dates
        }
    )


# ============================================================================
# Example usage / CLI
# ============================================================================

def convert_existing_output(input_file: str, output_file: str):
    """Convert existing find_and_expand_deals output to new format."""
    
    with open(input_file) as f:
        raw_data = json.load(f)
    
    # Parse to ValidDeals
    valid_deals = parse_find_and_expand_output(raw_data)
    
    # Create weekly payload
    origin = raw_data.get("origin", "UNKNOWN")
    payload = create_weekly_payload(
        origin=origin,
        valid_deals=valid_deals,
        week_of=date.today()
    )
    
    # Save
    with open(output_file, "w") as f:
        f.write(payload.model_dump_json(indent=2))
    
    print(f"✅ Converted {len(valid_deals)} deals")
    print(f"   Bundles: {len(payload.bundles)}")
    print(f"   Singles: {len(payload.single_deals)}")
    print(f"   Output: {output_file}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 3:
        convert_existing_output(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python deal_converter.py input.json output.json")
        print("\nExample:")
        print("  python deal_converter.py phx_full_test.json phx_weekly_payload.json")

