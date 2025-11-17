# URL Storage Feature

## What We Built

Added Google Flights URL generation and storage for every date combination found during deal expansion.

## Changes Made

### 1. Data Model (`deal_models.py`)
```python
class DatePrice(BaseModel):
    start_date: date
    end_date: date
    price: int
    url: Optional[str] = None  # ← NEW: Google Flights URL
```

### 2. URL Generation (`expand_dates.py`)
- Uses existing `build_flights_url()` function with protobuf encoding
- Generates unique URL for each date combination
- URLs are created after parsing price graph data, before filtering

```python
for date_combo in unique_dates:
    date_combo['url'] = build_flights_url(
        origin=origin,
        destination=actual_destination or destination,
        start_date=date_combo['start_date'],
        end_date=date_combo['end_date']
    )
```

### 3. Pipeline Integration
- Updated `find_and_expand_deals.py` to parse URLs
- Updated `format_deals.py` to handle URLs
- URLs stored in database via existing JSONB `similar_deals` field

## Database Storage

No schema changes needed! URLs are stored in existing `deals.similar_deals` JSONB column:

```json
{
  "similar_deals": [
    {
      "start_date": "2026-01-12",
      "end_date": "2026-01-21",
      "price": 244,
      "url": "https://www.google.com/travel/flights?tfs=..."
    }
  ]
}
```

## URL Format

Each URL:
- Pre-fills Google Flights with specific dates
- Uses protobuf-encoded `tfs` parameter
- Format: `https://www.google.com/travel/flights?tfs={base64}&hl=en&gl=us`

## Example Output

```
PHX → San Juan from $244

Available dates (click to book):
  • 2026-01-12 to 2026-01-21 - $244
    https://www.google.com/travel/flights?tfs=GhoSCjIwMjYtMDEtMTJqBRIDUEhYcgUSA1NKVRoaEgoyMDI2LTAxLTIxagUSA1NKVXIFEgNQSFhCAQFIAZgBAQ&hl=en&gl=us
    
  • 2026-02-01 to 2026-02-10 - $259
    https://www.google.com/travel/flights?tfs=GhoSCjIwMjYtMDItMDFqBRIDUEhYcgUSA1NKVRoaEgoyMDI2LTAyLTEwagUSA1NKVXIFEgNQSFhCAQFIAZgBAQ&hl=en&gl=us
```

## Usage

### In Python
```python
from deal_models import ValidDeal

# Access URLs from ValidDeal
for deal in valid_deals:
    for date_price in deal.similar_deals:
        print(f"{date_price.start_date} - ${date_price.price}")
        print(f"Book: {date_price.url}")
```

### In Newsletter/Website
```html
<ul>
  {% for date in deal.similar_dates %}
    <li>
      <a href="{{ date.url }}">
        {{ date.start_date }} to {{ date.end_date }} - ${{ date.price }}
      </a>
    </li>
  {% endfor %}
</ul>
```

## Files Changed

- `deal_models.py` - Added `url` field to DatePrice
- `scripts/expand_dates.py` - Generate URLs for all date combos
- `scripts/find_and_expand_deals.py` - Parse URLs from expansion dict
- `scripts/format_deals.py` - Parse URLs from expansion dict
- `scripts/demo_urls.py` - NEW: Demo script showing URL display

## Testing

Verified with PHX → San Juan:
- ✅ URLs generated for all 12 similar date combinations
- ✅ Each URL unique and correctly encoded
- ✅ URLs preserved through entire pipeline
- ✅ URLs stored in JSON output
- ✅ URLs accessible via Pydantic models

## Next Steps

When building the newsletter/website frontend:
1. Fetch deals from database
2. Parse `similar_deals` JSONB
3. Create clickable date links using `url` field
4. Style like cheapflightsfrom.us example
