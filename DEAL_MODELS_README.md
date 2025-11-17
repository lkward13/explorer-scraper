# Deal Models & Type-Safe Pipeline

This directory contains **Pydantic models** for the entire flight deals pipeline, from raw scraping to newsletter generation.

## Quick Start

### 1) Install Pydantic

```bash
pip install pydantic
```

### 2) Convert existing output

```bash
python deal_converter.py phx_full_test.json phx_weekly_payload.json
```

### 3) Use in your code

```python
from deal_models import ValidDeal, OriginWeeklyPayload
from deal_converter import parse_find_and_expand_output

# Load existing data
import json
with open("phx_full_test.json") as f:
    raw_data = json.load(f)

# Parse to type-safe models
valid_deals = parse_find_and_expand_output(raw_data)

# Access with full IDE autocomplete
for deal in valid_deals:
    print(f"{deal.destination_city}: ${deal.reference_price}")
    print(f"  {deal.discount_pct_display} off")
    print(f"  {deal.similar_dates_count} flexible dates")
    print(f"  {deal.flight_details.airline} - {deal.flight_details.duration}")
```

---

## Data Flow

```
Raw Explore Cards
    ↓
Expand via price graph
    ↓
ExpandedRoute (raw API data)
    ↓
ValidDeal (filtered + scored)
    ↓
RegionBundle / SingleDeal (grouped)
    ↓
OriginWeeklyPayload (newsletter-ready)
```

---

## Core Models

### `ValidDeal`

The canonical deal format. Every deal in your system should be a `ValidDeal`.

```python
{
  "deal_id": "phx-ppt-20251129",
  "origin": "PHX",
  "destination_airport": "PPT",
  "destination_city": "Tahiti",
  "destination_country": "PF",
  "destination_region": "oceania",
  
  "reference_price": 952,
  "usual_price_estimate": 1340,
  "discount_amount": 388,
  "discount_pct": 0.289,        # 28.9%
  "discount_pct_display": "28%",
  
  "similar_dates_count": 20,
  "first_travel_date": "2025-11-29",
  "last_travel_date": "2026-05-26",
  
  "flight_details": {
    "airline": "Alaska",
    "duration": "17h 5m",
    "stops": 1,
    "departure_time": "7:25 AM",
    "arrival_time": "9:30 PM"
  },
  
  "is_valid_deal": true,
  "is_featured_candidate": true,
  "score": 0.62,
  
  "expanded_at": "2025-11-17T12:41:12Z"
}
```

### `RegionBundle`

Multiple deals in the same region → "Europe is on sale from Phoenix"

```python
{
  "origin": "PHX",
  "destination_region": "europe",
  "region_label": "Europe",
  "title": "Europe is on sale from Phoenix",
  "subtitle": "Dublin, Paris, Barcelona 22–35% off",
  "deals": [
    # ... ValidDeal objects
  ],
  "cities_list": "Dublin, Paris, Barcelona, Rome, Amsterdam"
}
```

### `OriginWeeklyPayload`

Final output for email/blog/social generation.

```python
{
  "origin": "PHX",
  "week_of": "2025-11-17",
  "bundles": [
    # RegionBundle for Europe
    # RegionBundle for Caribbean
  ],
  "single_deals": [
    # SingleDeal for Tahiti
  ],
  "summary": {
    "total_destinations_scanned": 250,
    "valid_deals_found": 18,
    "featured_deals_picked": 5
  },
  "total_featured_deals": 5,
  "regions_on_sale": ["Europe", "Caribbean"]
}
```

---

## Deal Filtering Rules

Configured via `DealFilterConfig`:

```python
from deal_models import DealFilterConfig

config = DealFilterConfig(
    min_discount_pct=0.20,         # 20% off minimum
    min_similar_dates=5,            # 5+ flexible dates
    
    featured_min_discount_pct=0.25, # 25% for "featured"
    featured_min_similar_dates=10,  # 10+ for "featured"
    
    discount_weight=0.5,            # scoring weight
    flexibility_weight=0.5,
    
    min_deals_for_bundle=3          # 3+ deals → region bundle
)
```

### Current Rules (as of 2025-11-17)

**Base valid deal:**
- ≥ 20% off usual price
- ≥ 5 similar dates

**Featured deal:**
- ≥ 25% off usual price
- ≥ 10 similar dates

**Score formula:**
```
score = 0.5 * (discount_pct / 0.5) + 0.5 * (similar_dates / 30)
```
(capped at 50% off and 30 dates)

**Region bundle:**
- If 3+ valid deals to the same region from one origin
- Group them as "[Region] is on sale from [Origin]"

---

## Region Classification

Destinations are classified into 8 regions:

- `north_america` – US, Canada
- `central_america` – Mexico, Guatemala, Honduras, etc.
- `south_america` – Brazil, Argentina, Chile, etc.
- `caribbean` – Puerto Rico, Bahamas, Jamaica, etc.
- `europe` – UK, France, Spain, Italy, etc.
- `africa` – South Africa, Egypt, Morocco, etc.
- `south_east_asia` – Thailand, Vietnam, Singapore, etc.
- `oceania` – Australia, New Zealand, Tahiti, Fiji, etc.

Edit `COUNTRY_TO_REGION` and `AIRPORT_TO_COUNTRY` in `deal_converter.py` to add more.

---

## API / JSON Serialization

All models use Pydantic, so JSON is first-class:

```python
# Serialize to JSON
json_str = valid_deal.model_dump_json(indent=2)

# Deserialize from JSON
loaded = ValidDeal.model_validate_json(json_str)

# Convert to dict
data = valid_deal.model_dump()
```

---

## Next Steps

1. **Wire into `find_and_expand_deals.py`**
   - Instead of returning raw dicts, return `List[ValidDeal]`
   
2. **Add DB persistence**
   - Save `ValidDeal` objects to Postgres
   - Track `used_deals` with deal_id + timestamps
   
3. **Create newsletter formatter**
   - Input: `OriginWeeklyPayload`
   - Output: HTML email, blog post, social captions
   
4. **Add more airports/cities**
   - Expand `AIRPORT_TO_COUNTRY` and `CITY_TO_AIRPORT`
   - Or pull from a proper airport database

---

## Example: Newsletter Generation

```python
from deal_models import OriginWeeklyPayload

# Load weekly payload
payload = OriginWeeklyPayload.model_validate_json(open("phx_weekly.json").read())

# Generate email sections
print(f"# Flight Deals from {payload.origin}")
print(f"Week of {payload.week_of.strftime('%B %d, %Y')}")
print()

for bundle in payload.bundles:
    print(f"## {bundle.title}")
    print(f"{bundle.subtitle}")
    print()
    for deal in bundle.deals:
        print(f"- {deal.destination_city}: ${deal.reference_price} ({deal.discount_pct_display} off)")
    print()

for single in payload.single_deals:
    print(f"## {single.title}")
    deal = single.deal
    print(f"${deal.reference_price} ({deal.discount_pct_display} off, {deal.similar_dates_count} dates)")
    print(f"{deal.flight_details.airline} - {deal.flight_details.duration}")
    print()
```

---

## Files

- **`deal_models.py`** – All Pydantic models
- **`deal_converter.py`** – Convert raw JSON → typed models
- **`DEAL_MODELS_README.md`** – This file

---

## Questions?

These models are **100% compatible** with your existing JSON outputs. You can:
- Convert old data using `deal_converter.py`
- Start using models incrementally
- Keep backward compatibility with raw dicts if needed

The models just add type safety, validation, and documentation on top of what you already have.

