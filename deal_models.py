"""
Type-safe data models for the flight deals pipeline.
Uses Pydantic for validation, JSON serialization, and type hints.
"""

from typing import Optional, List, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, computed_field


# ============================================================================
# Core flight & deal data
# ============================================================================

class FlightDetails(BaseModel):
    """Flight routing details for a specific itinerary."""
    airline: Optional[str] = None
    duration: Optional[str] = None  # e.g. "17h 5m"
    stops: Optional[int] = None
    departure_time: Optional[str] = None  # e.g. "4:15 PM"
    arrival_time: Optional[str] = None    # e.g. "11:35 AM"


class DatePrice(BaseModel):
    """A single date combination with price."""
    start_date: date
    end_date: date
    price: int
    url: Optional[str] = None  # Google Flights URL for this specific date combo


# ============================================================================
# Raw Explore card (from Google Travel Explore)
# ============================================================================

class ExploreCard(BaseModel):
    """Raw destination card from Explore scraper."""
    origin: str
    destination: str              # city/place name
    min_price: int
    currency: str = "USD"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[str] = None
    search_region: str            # e.g. "europe", "caribbean"


# ============================================================================
# Expanded route (after price graph scraping via expand_dates)
# ============================================================================

class ExpandedRoute(BaseModel):
    """Full result from expand_dates price graph scraping."""
    origin: str
    destination: str              # IATA code
    actual_destination: Optional[str] = None  # resolved IATA if different

    reference_price: int
    reference_start: date
    reference_end: date
    threshold: float = 0.10

    price_range: dict             # {"min": int, "max": int}

    similar_deals: List[DatePrice]
    all_dates: List[DatePrice]    # all parsed date/price combos

    deal_quality: Optional[str] = None              # "$388 cheaper than usual"
    deal_quality_amount: Optional[int] = None       # 388

    flight_details: FlightDetails

    raw_responses: List[dict] = Field(default_factory=list)  # API metadata


# ============================================================================
# Normalized valid deal (canonical format for DB/storage)
# ============================================================================

class ValidDeal(BaseModel):
    """
    Canonical deal record after filtering, scoring, and normalization.
    This is what you store in DB and use for all downstream processing.
    """
    deal_id: str                  # unique: "phx-dub-20260201-20260208"

    # Origin
    origin: str                   # IATA
    origin_airport_name: Optional[str] = None

    # Destination
    destination_airport: str      # IATA
    destination_city: str
    destination_country: str      # ISO-2 code (e.g. "IE")
    destination_region: str       # "europe", "caribbean", etc.

    # Pricing
    reference_price: int
    usual_price_estimate: Optional[int] = None    # reference + discount_amount
    discount_amount: Optional[int] = None         # $ saved
    discount_pct: Optional[float] = None          # 0.0–1.0 (e.g. 0.289 = 28.9%)

    # Flexibility
    similar_dates_count: int
    first_travel_date: date
    last_travel_date: date

    # Display
    deal_quality_text: Optional[str] = None       # "$220 cheaper than usual"

    # Flight details
    flight_details: FlightDetails

    # Metadata
    search_region: str                            # which Explore region found it
    source: str = "google_flights_price_graph"

    # Deal evaluation
    is_valid_deal: bool = True
    is_featured_candidate: bool = False           # passes higher bar
    score: float                                  # composite score (0–1)

    # Timestamps & audit
    expanded_at: datetime
    threshold_used: float = 0.10

    @computed_field
    @property
    def discount_pct_display(self) -> Optional[str]:
        """Human-readable discount percentage (e.g. '29%')."""
        if self.discount_pct is not None:
            return f"{int(self.discount_pct * 100)}%"
        return None


# ============================================================================
# Region bundle (grouped deals for "Europe on sale" type sections)
# ============================================================================

class RegionBundle(BaseModel):
    """
    A grouped set of deals for a single origin → region.
    Used for "Europe is on sale from Phoenix" type sections.
    """
    origin: str
    origin_airport_name: Optional[str] = None

    destination_region: str       # e.g. "europe"
    region_label: str             # e.g. "Europe"

    bundle_type: Literal["region_sale"] = "region_sale"

    title: str                    # "Europe is on sale from Phoenix"
    subtitle: str                 # "4 cities 22–35% off with 8–20 dates each"

    deals: List[ValidDeal]

    stats: dict = Field(default_factory=dict)  # {"deals_in_bundle": 4, "average_discount_pct": 0.31, ...}

    @computed_field
    @property
    def cities_list(self) -> str:
        """Comma-separated list of cities (e.g. 'Dublin, Paris, Barcelona')."""
        return ", ".join([d.destination_city for d in self.deals[:5]])  # cap at 5 for display


class SingleDeal(BaseModel):
    """
    A standalone hero deal (not part of a region bundle).
    Used for exceptional individual deals like Tahiti.
    """
    bundle_type: Literal["single"] = "single"
    title: str                    # "Tahiti for under $1,000 from Phoenix"
    deal: ValidDeal


# ============================================================================
# Origin weekly payload (for email/blog/social content generation)
# ============================================================================

class OriginWeeklyPayload(BaseModel):
    """
    Final payload for one origin for a given week.
    This is what the email/blog/social formatter consumes.
    """
    origin: str
    origin_airport_name: Optional[str] = None

    week_of: date                 # Monday of the week

    bundles: List[RegionBundle] = Field(default_factory=list)
    single_deals: List[SingleDeal] = Field(default_factory=list)

    summary: dict = Field(default_factory=dict)  # stats like total_destinations_scanned, etc.

    @computed_field
    @property
    def total_featured_deals(self) -> int:
        """Total number of featured deals (bundles + singles)."""
        bundle_count = sum(len(b.deals) for b in self.bundles)
        single_count = len(self.single_deals)
        return bundle_count + single_count

    @computed_field
    @property
    def regions_on_sale(self) -> List[str]:
        """List of regions that have bundles."""
        return [b.region_label for b in self.bundles]


# ============================================================================
# Helpers for route metadata (used during expansion)
# ============================================================================

class RouteMetadata(BaseModel):
    """
    Metadata about a route used during deal evaluation.
    Not stored directly, but used for scoring/filtering.
    """
    origin: str
    destination_airport: str
    destination_city: str
    destination_country: str
    destination_region: str       # computed from airport/country

    is_domestic: bool = False
    is_international: bool = True
    is_longhaul: bool = False     # Europe/Asia/Oceania/Africa

    # For future use
    airline_category: Optional[str] = None  # "LEGACY", "LCC", "ULCC"


# ============================================================================
# Deal filter configuration (for programmatic threshold tuning)
# ============================================================================

class DealFilterConfig(BaseModel):
    """Configuration for deal filtering and scoring."""
    min_discount_pct: float = 0.20        # 20% off minimum
    min_similar_dates: int = 5            # 5+ flexible dates

    featured_min_discount_pct: float = 0.25   # 25% off for "featured"
    featured_min_similar_dates: int = 10      # 10+ dates for "featured"

    # Scoring weights
    discount_weight: float = 0.5
    flexibility_weight: float = 0.5

    # Bundle thresholds
    min_deals_for_bundle: int = 3         # 3+ deals in region → bundle


# ============================================================================
# Example usage functions (for documentation)
# ============================================================================

def example_usage():
    """Show how these models fit together."""

    # 1) Raw expanded route from expand_dates
    expanded = ExpandedRoute(
        origin="PHX",
        destination="DUB",
        reference_price=433,
        reference_start=date(2026, 2, 1),
        reference_end=date(2026, 2, 8),
        similar_deals=[
            DatePrice(start_date=date(2026, 2, 1), end_date=date(2026, 2, 8), price=433),
            DatePrice(start_date=date(2026, 2, 3), end_date=date(2026, 2, 10), price=440),
        ],
        all_dates=[],
        deal_quality="$220 cheaper than usual",
        deal_quality_amount=220,
        flight_details=FlightDetails(
            airline="United",
            duration="13h 20m",
            stops=1,
            departure_time="4:15 PM",
            arrival_time="11:35 AM"
        )
    )

    # 2) Normalize to ValidDeal
    usual_price = expanded.reference_price + (expanded.deal_quality_amount or 0)
    discount_pct = (expanded.deal_quality_amount / usual_price) if usual_price > 0 else 0

    valid_deal = ValidDeal(
        deal_id="phx-dub-20260201",
        origin="PHX",
        destination_airport="DUB",
        destination_city="Dublin",
        destination_country="IE",
        destination_region="europe",
        reference_price=expanded.reference_price,
        usual_price_estimate=usual_price,
        discount_amount=expanded.deal_quality_amount,
        discount_pct=discount_pct,
        similar_dates_count=len(expanded.similar_deals),
        first_travel_date=min(d.start_date for d in expanded.similar_deals),
        last_travel_date=max(d.end_date for d in expanded.similar_deals),
        deal_quality_text=expanded.deal_quality,
        flight_details=expanded.flight_details,
        search_region="europe",
        score=0.84,
        expanded_at=datetime.now()
    )

    # 3) Create a region bundle
    bundle = RegionBundle(
        origin="PHX",
        destination_region="europe",
        region_label="Europe",
        title="Europe is on sale from Phoenix",
        subtitle="Dublin, Paris, Barcelona 22–35% off",
        deals=[valid_deal],  # would have more in practice
        stats={"deals_in_bundle": 1, "average_discount_pct": 0.337}
    )

    # 4) Create weekly payload
    payload = OriginWeeklyPayload(
        origin="PHX",
        week_of=date(2025, 11, 17),
        bundles=[bundle],
        single_deals=[],
        summary={
            "total_destinations_scanned": 250,
            "valid_deals_found": 18,
            "featured_deals_picked": 5
        }
    )

    # Serialize to JSON for API/storage
    json_output = payload.model_dump_json(indent=2)
    print(json_output)

    # Deserialize from JSON
    loaded = OriginWeeklyPayload.model_validate_json(json_output)
    print(f"Loaded {loaded.total_featured_deals} deals")


if __name__ == "__main__":
    example_usage()

