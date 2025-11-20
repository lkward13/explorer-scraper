# ExploreScrape - Production Flight Deal Scraper

**🚀 Production-ready flight deal finder using Google Flights API**

A scalable pipeline to discover and expand flight deals across multiple origins:
1. **Explore Scraper**: Find 300-400 destinations per origin across 9 regions
2. **API-based Expansion**: Find all similar-priced dates for 11 months (bypasses UI automation)
3. **Parallel Execution**: Process 25-50 origins simultaneously with 5 concurrent browsers

## ✨ Current Capabilities (v2.0)

- **✅ 50 origins tested** (25-origin batches to avoid rate limits)
- **✅ 100% API success rate** (250/250 expansions completed)
- **✅ 58.4% valid deal rate** (146/250 deals with ≥5 flexible dates)
- **✅ 11-month coverage** from today (vs 9 months from deal date)
- **✅ No bot detection** (API calls bypass all UI anti-scraping)
- **✅ 18,600+ destinations found** in a single 50-origin run

## Quick Start (Docker)

```bash
# Build image
docker build -t explorer-scraper .

# Run 25-origin test (recommended starting point)
docker run --rm explorer-scraper start_with_xvfb.sh python -u test_25_origins_11_month.py

# Run 50-origin test (2× 25-origin batches with 10-min pause)
docker run --rm explorer-scraper start_with_xvfb.sh python -u test_50_origins_two_batches.py
```

**What you get:**
- 25 origins × 9 regions = 9,600+ destination cards
- 125 deals expanded (5 per origin)
- ~58 valid deals with 5+ flexible dates
- Total time: ~15 minutes for 25 origins

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

## Architecture (v2.0)

### Two-Phase Pipeline

**Phase 1: Explore (Browser-based)**
- Uses pre-generated TFS (Travel Flight Search) parameters for 9 regions
- Playwright loads Google Flights Explore pages
- Scrapes 300-400 destination cards per origin
- 5 concurrent browsers processing batches of 5 origins
- ~13 minutes for 25 origins (225 page loads)

**Phase 2: Expansion (API-based)**
- Directly calls `GetCalendarGraph` API (bypasses UI entirely)
- 4 parallel API calls per deal covering 11 months from today
- Each call covers ~3 months (330+ date combinations total)
- 5 concurrent "browsers" (really just API clients)
- ~3-5 minutes for 125 expansions
- **100% success rate** - no bot detection

### Key Technical Achievements

✅ **API Expansion (GetCalendarGraph)**
- Discovered and reverse-engineered Google's internal calendar API
- Supports 11-month date range from TODAY (vs 9 months from deal date)
- Returns 330+ date combinations per deal
- 0.4-30s per expansion (avg 5-14s depending on route popularity)
- Completely bypasses UI automation, button clicks, selectors

✅ **Programmatic TFS Generation**
- Pre-generated region TFS for 100+ US airports  
- Stored in `data/region_tfs/*.json`
- No browser collection needed
- Instant URL generation for any origin/region combo

✅ **Robust Retry Logic**
- Explore: Retries once after 10s if "No destination cards found"
- Expansion: N/A (API calls don't fail due to bot detection)
- Connection errors: 2 retries with 5s delays

✅ **Rate Limit Handling**
- 25-origin batches avoid Google rate limiting (450 page loads)
- 50+ origins: Use 2× 25-origin batches with 10-min pause
- Sequential region scraping within each origin (9 pages)
- 3-second stagger between browser launches in each batch

### Performance Benchmarks

**25 Origins (Tested & Reliable)**
- Explore: 9,600+ cards in 13 min (100% success)
- Expansion: 125 deals in 3-5 min (100% API success)
- Valid deals: 58/125 (46.4%) with ≥5 flexible dates
- Total: ~15-18 minutes

**50 Origins (2× 25-origin batches)**
- Batch 1: 18 min (9,755 cards, 58 valid deals)
- Pause: 10 min
- Batch 2: 24 min (8,837 cards, 88 valid deals)
- Total: 52 min (18,592 cards, 146 valid deals, 58.4% rate)

**Estimated 100 Origins**
- 4× 25-origin batches = ~110 minutes
- Or 2× 50-origin runs (parallel servers) = ~55 minutes
- ~290 valid deals expected

### Current Limitations

✅ **Solved:**
- ~~Bot detection during expansion~~ (API bypass)
- ~~Inconsistent date ranges~~ (11 months from today)
- ~~Slow expansion~~ (API is 20-150x faster than UI)
- ~~Rate limiting on expansion~~ (API has higher limits)

⚠️ **Active:**
- **Explore rate limiting**: 25-origin batches required (450 page loads max)
- **Browser dependency**: Explore still needs Playwright (API doesn't have explore equivalent)
- **Deal details**: Currently no "cheaper than usual" data (would require separate API)

🚧 **Deferred (v3.0):**
- Database storage & deal deduplication
- Deal quality API (`GetExploreDestinationFlightDetails`)
- Multi-server deployment for 100+ origins
- Web UI for browsing results
- Price alerts & notifications

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

## Technical Deep Dive

### How API Expansion Works

**Discovery Process:**
1. Used Chrome DevTools to capture network requests during manual price graph interaction
2. Identified `GetCalendarGraph` endpoint returning date/price JSON
3. Reverse-engineered the POST body structure (nested arrays with origin, destination, dates, grid size)
4. Tested different date ranges: found 6-month hard limit per API call
5. Solution: Make 4 parallel calls covering 3 months each = 11 total months

**API Request Format:**
```python
POST https://www.google.com/_/FlightsFrontendUi/data/...GetCalendarGraph
Body: f.req=[null,"[[null,[null,null,1,null,[],1,[1,0,0,0],null,null,null,null,null,null,
  [[[[\"DFW\",0]]],[[\"LHR\",0]]],null,0,null,null,\"2025-12-10\",null,null,null,null,null,null,null,3],
  [[[\"LHR\",0]]],[[\"DFW\",0]]],null,0,null,null,\"2025-12-18\",null,null,null,null,null,null,null,3]]
  ,null,null,null,1],[\"2025-11-20\",\"2026-02-20\"],null,[9,9]]"]
```

**Key Parameters:**
- `[9,9]`: Grid size (9x9 = 81 date combinations per call)
- Date range: Start/end dates for the 3-month window
- Origin/destination: IATA codes
- Reference dates: The original deal's outbound/return dates

**Response Parsing:**
```python
# Raw response (escaped JSON in string):
')]}\n[["wrb.fr","GetCalendarGraph",...["2026-01-04","2026-01-13",[[null,189]...

# Regex extraction:
pattern = r'\[\\?"(\d{4}-\d{2}-\d{2})\\?",\\?"(\d{4}-\d{2}-\d{2})\\?",\[\[null,(\d+)\]'
# Yields: [('2026-01-04', '2026-01-13', '189'), ...]
```

### Why 11 Months from TODAY?

**Problem with "9 months from deal date":**
- Explore finds deals departing in March 2026
- Expansion searched March-December 2026
- But airlines only release schedules 6-9 months out
- Result: 67/125 routes had "0 date combinations" (no availability yet)

**Solution: 11 months from TODAY:**
- Always search from current date forward
- Captures all available booking windows
- Reduced "no availability" from 72 to 63 routes (12.5% improvement)
- Increased valid deals from 53 to 58 (9.4% improvement)

### Retry Logic Details

**Explore Phase:**
```python
# If explore returns 0 cards:
if len(cards) == 0 and retry_count < max_retries:
    await asyncio.sleep(10)  # Wait for rate limit reset
    return await scrape_region(region, retry_count + 1, max_retries)
# Falls back to 0 cards after 1 retry
```

**Why this works:**
- "No destination cards found" = Google rate limiting (not a failure)
- 10-second wait lets rate limit window reset
- 1 retry is enough (2nd failure = truly no data)
- Prevents hanging on persistently blocked routes

**Expansion Phase:**
- No retries needed (API doesn't get blocked)
- Returns `None` on HTTP error, `[]` on no data
- Distinguishes between failure and legitimate "no dates available"

---

## File Structure

```
explore_scraper/
├── cli.py                    # Explore scraper entry point
├── tfs_builder.py            # Programmatic TFS generation
├── fetch_browser.py          # Playwright automation
└── parse_html.py             # HTML parsing

scripts/
├── expand_dates_api.py       # API-based expansion (NEW!)
└── expand_dates.py           # UI-based expansion (legacy)

worker/
├── test_parallel.py          # Test orchestration & batching
└── parallel_executor.py      # Parallel expansion executor

data/
├── region_tfs/               # Pre-generated TFS for 100+ airports
│   ├── ATL.json
│   ├── DFW.json
│   └── ...
└── top_100_airports.txt      # Reference airport list

test_25_origins_11_month.py   # Recommended test script
test_50_origins_two_batches.py # 50-origin test with pause
```

---

## Git Checkpoints

**Current version:** `v2.0-api-expansion-production`

**Major milestones:**
- `v1.0-working-separate-scripts` - Initial UI-based expansion
- `v1.5-programmatic-tfs` - Pre-generated region TFS
- `v2.0-api-expansion-production` - API-based expansion, 50-origin scale

To see all checkpoints:
```bash
git log --oneline --graph
```

---

## License

MIT
