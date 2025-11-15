# ExploreScrape - Google Travel Flight Deal Finder

A two-stage pipeline to discover and expand cheap flight deals:
1. **Explore Scraper**: Find 60+ cheap destinations from your airport
2. **Date Expander**: For each deal, find all similar-priced dates across 10+ months

## Quick Start

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
protoc --python_out=. flights.proto
playwright install chromium

# Step 1: Find cheap deals from DFW
python -m explore_scraper.cli --origin DFW --use-browser --out deals.json

# Step 2: Expand a specific deal to find flexible dates
python scripts/expand_dates.py \
  --origin DFW \
  --destination SEA \
  --start 2025-12-08 \
  --end 2025-12-15 \
  --price 66 \
  --threshold 0.10 \
  --out expanded.json
```

---

## Part 1: Explore Scraper

Finds cheap flight deals from your origin airport to various destinations.

### Usage

```bash
# Search from any airport (uses IATA code)
python -m explore_scraper.cli --origin JFK --use-browser --out results.json

# With proxy
python -m explore_scraper.cli --origin LAX --use-browser --proxy "http://IP:PORT"

# Parse saved HTML (offline)
python -m explore_scraper.cli --html-file explore.html --out results.json
```

### Output Format

Returns 60+ destination deals:

```json
[
  {
    "destination": "Miami",
    "min_price": 45,
    "currency": "USD",
    "start_date": "2025-12-04",
    "end_date": "2025-12-11",
    "duration": "2 hours 30 minutes"
  },
  {
    "destination": "Seattle",
    "min_price": 66,
    "currency": "USD",
    "start_date": "2025-12-08",
    "end_date": "2025-12-15",
    "duration": "4 hours 15 minutes"
  }
]
```

**Fields:**
- `destination`: City/location name
- `min_price`: Lowest price found (integer)
- `currency`: Currency code (USD, EUR, etc.)
- `start_date`: Departure date (YYYY-MM-DD, may be null)
- `end_date`: Return date (YYYY-MM-DD, may be null)
- `duration`: Flight time (string, may be null)

---

## Part 2: Date Expander

Takes a single deal from Explore and finds ALL similar-priced dates across 10+ months.

### How It Works

1. Navigates to Google Flights with the specific route and dates
2. Opens the price graph calendar view
3. Paginates through 12 months by clicking "Scroll forward"
4. Intercepts GetCalendarGraph API responses
5. Parses 300+ date/price combinations
6. Filters by price threshold (default ±10%)

### Usage

```bash
# Expand a deal with ±10% price threshold
python scripts/expand_dates.py \
  --origin DFW \
  --destination LHR \
  --start 2025-12-10 \
  --end 2025-12-18 \
  --price 450 \
  --threshold 0.10 \
  --out expanded.json

# Wider threshold (±25%)
python scripts/expand_dates.py \
  --origin OKC \
  --destination SEA \
  --start 2025-12-06 \
  --end 2025-12-13 \
  --price 149 \
  --threshold 0.25 \
  --out expanded.json
```

### Output Format

Returns both ALL dates and filtered similar deals:

```json
{
  "origin": "DFW",
  "destination": "SEA",
  "reference_price": 66,
  "reference_start": "2025-12-08",
  "reference_end": "2025-12-15",
  "threshold": 0.10,
  "price_range": {
    "min": 59,
    "max": 72
  },
  "all_dates": [
    {
      "start_date": "2025-12-01",
      "end_date": "2025-12-08",
      "price": 66
    },
    {
      "start_date": "2025-12-05",
      "end_date": "2025-12-12",
      "price": 94
    }
    // ... 300+ more combinations
  ],
  "similar_deals": [
    {
      "start_date": "2025-12-08",
      "end_date": "2025-12-15",
      "price": 66
    }
    // Only deals within ±10% threshold
  ]
}
```

**Key Fields:**
- `all_dates`: Complete dataset (300+ combinations, 10+ months, full price range)
- `similar_deals`: Filtered results within threshold
- `threshold`: Percentage used for filtering (0.10 = ±10%)
- `price_range`: Min/max prices for the threshold filter

**Data Coverage:**
- **Date range**: Typically Nov 2025 → Oct 2026 (10-11 months)
- **Total combinations**: 300-350 date pairs
- **Price range**: Full spectrum (e.g., $66-$445)

---

## Full Workflow Example

```bash
# 1. Find all cheap deals from DFW
python -m explore_scraper.cli --origin DFW --use-browser --out dfw_deals.json

# Output: 64 destinations found
# {destination: "Seattle", min_price: 66, start_date: "2025-12-08", ...}

# 2. Pick an interesting deal and expand it
python scripts/expand_dates.py \
  --origin DFW \
  --destination SEA \
  --start 2025-12-08 \
  --end 2025-12-15 \
  --price 66 \
  --threshold 0.10 \
  --out seattle_expanded.json

# Output: 306 total dates, 1 within ±10%
# (In this case, $66 is an exceptional deal with no similar prices)

# 3. Try another deal with more flexibility
python scripts/expand_dates.py \
  --origin DFW \
  --destination MIA \
  --start 2025-12-04 \
  --end 2025-12-11 \
  --price 45 \
  --threshold 0.15 \
  --out miami_expanded.json
```

---

## Technical Details

### How Explore Scraper Works

1. **URL Generation**: Uses Protocol Buffers to construct Google Travel Explore URLs from IATA codes
2. **Browser Automation**: Playwright launches Chromium and navigates to the Explore page
3. **Wait for Render**: Waits for JavaScript to render destination cards (`.SwQ5Be` selector)
4. **Parse HTML**: Extracts destination names, prices, dates from rendered DOM
5. **Base64 Decode**: Decodes embedded flight data from `data-gs` attributes
6. **Output JSON**: Returns structured data for all destinations

**Key Technologies:**
- `playwright`: Browser automation
- `selectolax`: Fast HTML parsing
- `protobuf`: TFS parameter generation
- `httpx`: HTTP/2 support (legacy mode)

### How Date Expander Works

1. **URL Generation**: Uses Protocol Buffers to construct Google Flights URLs with specific dates
2. **Browser Navigation**: Opens the flights page with pre-filled origin, destination, dates
3. **Network Interception**: Captures all HTTP responses, especially GetCalendarGraph API calls
4. **Price Graph Automation**:
   - Clicks "Price graph" button
   - Waits for initial data load
   - Clicks "Scroll forward" button 12 times
   - Waits for new API response after each click (10s timeout)
5. **Response Parsing**: Extracts date/price pairs from JSON-like API responses using regex
6. **Deduplication**: Removes duplicate (start_date, end_date, price) combinations
7. **Filtering**: Applies threshold to find similar deals
8. **Output**: Returns both complete dataset and filtered results

**Key Technologies:**
- `playwright`: Browser automation + network interception
- `protobuf`: Flight URL generation
- `regex`: Parse escaped JSON in API responses
- `asyncio`: Async/await for browser operations

**API Response Format:**
```
[\"2025-12-06\",\"2025-12-13\",[[null,149],\"encoded_data\"],1]
Format: [outbound_date, inbound_date, [[null, price], ...], trip_length]
```

---

## Project Structure

```
explore_scraper/
├── __init__.py          # Package initialization
├── cli.py               # Explore scraper CLI
├── tfs.py               # URL parsing/building utilities
├── tfs_builder.py       # Protobuf TFS generation
├── fetch_http.py        # HTTP fetching (legacy)
├── fetch_browser.py     # Playwright automation
└── parse_html.py        # HTML parsing for Explore cards

scripts/
└── expand_dates.py      # Date expander script

flights.proto            # Protocol Buffer definition
flights_pb2.py           # Generated protobuf code (via protoc)

data/
└── top_150_us_airports.txt  # Reference airport list
```

---

## Current Status

### ✅ Working Features

**Explore Scraper:**
- Airport code-based searches (any IATA code worldwide)
- Programmatic TFS generation via Protocol Buffers
- Playwright browser automation
- Extracts: destination, price, currency, dates, duration
- Base64 decoding of embedded flight data
- Proxy support (HTTP/SOCKS)
- HTML file parsing (offline mode)
- Error handling for 0 results

**Date Expander:**
- Protobuf-based Google Flights URL generation
- Price graph automation (click, scroll, paginate)
- Network interception for GetCalendarGraph API
- Parses 300+ date combinations across 10+ months
- Deduplication logic
- Threshold-based filtering (±10%, ±25%, etc.)
- Returns both complete dataset and filtered results
- Verbose logging for debugging

### ⚠️ Known Limitations

- **Browser required**: Both scripts need Playwright (Google uses JavaScript SPAs)
- **Sandbox issues**: macOS/Linux may need `--required_permissions: ['all']` in AI tools
- **API data range**: Google provides 10-11 months of pricing data (not infinite)
- **Exceptional deals**: Very cheap prices may have few/no similar alternatives
- **Duration field**: Sometimes null in Explore results (Google's data availability)

### 🚧 Next Steps

**Immediate:**
- [ ] Combine scripts into single automated pipeline
- [ ] Add deal selection criteria (domestic vs international, price thresholds)
- [ ] Filter deals by flexibility (require 5-10 similar dates, not just 1-2)
- [ ] Add "recently used" tracking to avoid repeat destinations

**Future Enhancements:**
- [ ] Multi-origin batch mode (scrape top 150 US airports)
- [ ] Database storage for historical price tracking
- [ ] Email/Slack notifications for good deals
- [ ] Web UI for browsing deals
- [ ] Airline preference filtering
- [ ] Layover duration preferences
- [ ] Image URLs and coordinates extraction

---

## Troubleshooting

**"Parsed 0 cards" error:**
- Make sure you're using `--use-browser` flag
- Check that Playwright Chromium is installed: `playwright install chromium`

**Currency dialog opens during pagination:**
- Script automatically detects and closes with Escape key
- If persistent, check button selectors in `expand_dates.py`

**"No new GetCalendarGraph detected":**
- Price graph may have reached the end of available data
- Google typically provides 10-11 months from current date
- Check verbose logs to see how many months were successfully loaded

**Timeout errors:**
- Increase `--timeout` parameter (default: 30s)
- Check internet connection
- Try with `--proxy` if behind firewall

---

## Git Checkpoint

Current version: `v1.0-working-separate-scripts`

To revert to this checkpoint:
```bash
git checkout v1.0-working-separate-scripts
```

To see all checkpoints:
```bash
git tag -l
```

---

## License

MIT
