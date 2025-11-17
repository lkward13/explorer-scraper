#!/usr/bin/env python3
"""
Convert raw find_and_expand_deals output to human-readable newsletter format.

Usage:
    python scripts/format_deals.py results.json
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from deal_models import ExpandedRoute, ValidDeal, RegionBundle, OriginWeeklyPayload, DatePrice, FlightDetails
from deal_converter import classify_region, get_airport_country
from deal_filters import expansion_to_valid_deal, DealFilterConfig
from datetime import date, datetime


def parse_expanded_route(expansion_dict: dict) -> ExpandedRoute:
    """Convert raw expansion dict to ExpandedRoute model."""
    
    def parse_date_str(d):
        if isinstance(d, str):
            return date.fromisoformat(d)
        return d
    
    similar_deals = [
        DatePrice(
            start_date=parse_date_str(d['start_date']),
            end_date=parse_date_str(d['end_date']),
            price=d['price'],
            url=d.get('url')
        )
        for d in expansion_dict.get('similar_deals', [])
    ]
    
    all_dates = [
        DatePrice(
            start_date=parse_date_str(d['start_date']),
            end_date=parse_date_str(d['end_date']),
            price=d['price'],
            url=d.get('url')
        )
        for d in expansion_dict.get('all_dates', [])
    ]
    
    flight_details_dict = expansion_dict.get('flight_details') or {}
    flight_details = FlightDetails(**flight_details_dict) if flight_details_dict else FlightDetails()
    
    return ExpandedRoute(
        origin=expansion_dict['origin'],
        destination=expansion_dict['destination'],
        actual_destination=expansion_dict.get('actual_destination'),
        reference_price=expansion_dict['reference_price'],
        reference_start=parse_date_str(expansion_dict['reference_start']),
        reference_end=parse_date_str(expansion_dict['reference_end']),
        threshold=expansion_dict.get('threshold', 0.10),
        price_range=expansion_dict.get('price_range', {}),
        similar_deals=similar_deals,
        all_dates=all_dates,
        deal_quality=expansion_dict.get('deal_quality'),
        deal_quality_amount=expansion_dict.get('deal_quality_amount'),
        flight_details=flight_details,
        raw_responses=expansion_dict.get('raw_responses', [])
    )


def format_deal_summary(deal: ValidDeal) -> str:
    """Format a single deal for display."""
    lines = []
    lines.append(f"  📍 {deal.destination_city} ({deal.destination_airport})")
    lines.append(f"     ${deal.reference_price} (usually ${deal.usual_price_estimate}) - {deal.discount_pct_display} off")
    lines.append(f"     ✈️  {deal.flight_details.airline} - {deal.flight_details.duration} - {deal.flight_details.stops} stop{'s' if deal.flight_details.stops != 1 else ''}")
    lines.append(f"     📅 {deal.similar_dates_count} flexible dates: {deal.first_travel_date} to {deal.last_travel_date}")
    lines.append(f"     ⭐ Score: {deal.score:.2f} {'🔥 FEATURED' if deal.is_featured_candidate else ''}")
    return "\n".join(lines)


def process_raw_results(results_file: str):
    """Process raw results and convert to ValidDeals."""
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    origin = data['origin']
    valid_deals = []
    
    print(f"")
    print(f"{'='*80}")
    print(f"DEALS FROM {origin}")
    print(f"{'='*80}")
    print(f"")
    
    config = DealFilterConfig()
    
    for deal_data in data.get('expanded_deals', []):
        # Parse expansion
        expansion_dict = deal_data.get('expansion_dict') or deal_data.get('expansion')
        explore_deal = deal_data['explore_deal']
        
        # Parse to ExpandedRoute model
        try:
            expansion = parse_expanded_route(expansion_dict)
        except Exception as e:
            print(f"[warn] Failed to parse {explore_deal['destination']}: {e}", file=sys.stderr)
            continue
        
        # Get destination info
        dest_airport = expansion.actual_destination or expansion.destination
        dest_city = explore_deal['destination']
        dest_country = get_airport_country(dest_airport) or "XX"
        dest_region = classify_region(dest_airport, dest_country)
        search_region = explore_deal.get('search_region', dest_region)
        
        # Convert to ValidDeal
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
    
    # Group by region
    deals_by_region = {}
    for deal in valid_deals:
        region = deal.destination_region
        if region not in deals_by_region:
            deals_by_region[region] = []
        deals_by_region[region].append(deal)
    
    # Sort deals within each region by score
    for region in deals_by_region:
        deals_by_region[region].sort(key=lambda d: d.score, reverse=True)
    
    # Display by region
    for region, deals in sorted(deals_by_region.items()):
        region_label = region.replace('_', ' ').title()
        print(f"")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  {region_label.upper()} ({len(deals)} deals)")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"")
        
        for deal in deals:
            print(format_deal_summary(deal))
            print("")
    
    # Summary
    print("")
    print(f"{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"  Total valid deals: {len(valid_deals)}")
    print(f"  Regions with deals: {len(deals_by_region)}")
    print(f"  Featured candidates: {sum(1 for d in valid_deals if d.is_featured_candidate)}")
    print(f"  Average discount: {int(sum(d.discount_pct for d in valid_deals) / len(valid_deals) * 100)}%")
    print(f"  Average flexibility: {int(sum(d.similar_dates_count for d in valid_deals) / len(valid_deals))} dates")
    print(f"")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/format_deals.py results.json")
        sys.exit(1)
    
    process_raw_results(sys.argv[1])

