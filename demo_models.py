"""
Demo: Using the type-safe deal models
"""

from deal_models import OriginWeeklyPayload

# Load the weekly payload we just created
payload = OriginWeeklyPayload.model_validate_json(open("phx_weekly_payload.json").read())

print("=" * 80)
print(f"FLIGHT DEALS FROM {payload.origin}")
print(f"Week of {payload.week_of}")
print("=" * 80)
print()

# Summary stats
print(f"📊 This week's stats:")
print(f"   • Scanned: {payload.summary['total_destinations_scanned']} destinations")
print(f"   • Valid deals: {payload.summary['valid_deals_found']}")
print(f"   • Featured: {payload.total_featured_deals}")
print(f"   • Regions on sale: {', '.join(payload.regions_on_sale) or 'None'}")
print()

# Region bundles
if payload.bundles:
    print("🌍 REGION SALES")
    print("-" * 80)
    for bundle in payload.bundles:
        print(f"\n{bundle.title}")
        print(f"{bundle.subtitle}")
        print(f"\nCities: {bundle.cities_list}")
        print("\nDeals:")
        for deal in bundle.deals:
            print(f"  • {deal.destination_city}: ${deal.reference_price}")
            print(f"    {deal.discount_pct_display} off ({deal.similar_dates_count} dates)")
            print(f"    {deal.flight_details.airline} - {deal.flight_details.duration}")
    print()

# Single deals
if payload.single_deals:
    print("✈️  FEATURED DEALS")
    print("-" * 80)
    for single in payload.single_deals:
        deal = single.deal
        print(f"\n{single.title}")
        print(f"  Price: ${deal.reference_price} (usually ${deal.usual_price_estimate})")
        print(f"  Savings: ${deal.discount_amount} ({deal.discount_pct_display} off)")
        print(f"  Dates: {deal.similar_dates_count} options from {deal.first_travel_date} to {deal.last_travel_date}")
        print(f"  Flight: {deal.flight_details.airline} - {deal.flight_details.duration} - {deal.flight_details.stops} stop{'s' if deal.flight_details.stops != 1 else ''}")
        print(f"  Times: {deal.flight_details.departure_time} → {deal.flight_details.arrival_time}")
        print(f"  Score: {deal.score:.2f} (featured: {deal.is_featured_candidate})")

print()
print("=" * 80)

# Type-safe access (IDE autocomplete works!)
print(f"\n💡 The type system prevents bugs:")
print(f"   • payload.origin is a string: '{payload.origin}'")
print(f"   • payload.week_of is a date: {payload.week_of} (type: {type(payload.week_of).__name__})")
print(f"   • payload.total_featured_deals is computed: {payload.total_featured_deals}")
