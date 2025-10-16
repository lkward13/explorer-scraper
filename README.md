# ExploreScrape - Lightweight Google Travel Explore Scraper

Extracts destination cards (name, price, dates, flight duration) from Google Travel Explore pages.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
protoc --python_out=. flights.proto  # Generate protocol buffer code
playwright install chromium
```

## Usage

### By airport code (recommended)

Works with **any** IATA airport code - uses protocol buffers to generate proper Google Travel URLs:

```bash
# Search from JFK
python -m explore_scraper.cli --origin JFK --use-browser

# Search from LAX, save to file
python -m explore_scraper.cli --origin LAX --use-browser --out results.json

# Search from DFW
python -m explore_scraper.cli --origin DFW --use-browser

# With proxy
python -m explore_scraper.cli --origin ORD --use-browser --proxy "http://IP:PORT"
```

**Supports all IATA codes** - no manual collection or mapping needed!

### By full URL (alternative)

If you have a specific Google Travel Explore URL:

```bash
python -m explore_scraper.cli \
  --tfs-url "https://www.google.com/travel/explore?tfs=CBwQ..." \
  --use-browser
```

### Parse saved HTML file (offline)

Parse a previously saved HTML file:

```bash
python -m explore_scraper.cli --html-file explore.html --out results.json
```

## Output

Prints JSON array of destination cards:

```json
[
  {
    "destination": "Tampa",
    "min_price": 249,
    "currency": "USD",
    "start_date": "2025-11-08",
    "end_date": "2025-11-15",
    "duration": "1 hour 30 minutes"
  },
  {
    "destination": "Denver",
    "min_price": 39,
    "currency": "USD",
    "start_date": "2025-11-06",
    "end_date": "2025-11-12",
    "duration": null
  }
]
```

### Data Fields

Each destination card contains:

- **`destination`** (string): Name of the destination (city, national park, etc.)
- **`min_price`** (integer): Lowest price found for flights, in the specified currency
- **`currency`** (string): Currency code (e.g., "USD") - determined by `--gl` parameter
- **`start_date`** (string | null): Trip start date in YYYY-MM-DD format, extracted from base64-encoded data
- **`end_date`** (string | null): Trip end date in YYYY-MM-DD format, extracted from base64-encoded data
- **`duration`** (string | null): Flight duration (e.g., "2 hours 30 minutes") - only present for some destinations

**Notes:**
- Typical query returns 60+ destinations
- Date ranges and duration may be `null` if not available in the source data
- Flight duration appears more commonly for national parks and remote destinations

## Features

- **Automated browser scraping** with Playwright (renders JavaScript)
- **Parse saved HTML files** as alternative
- Extracts: destination, price, currency, date range, flight duration
- Base64 decodes embedded flight data
- Error handling for 0 results
- Optional proxy support

## Limitations

- **Requires browser for live scraping**: Google Travel Explore is a JavaScript SPA
- **macOS/Linux users**: Chromium requires system directory access (works fine in normal terminal, AI tools may need sandbox bypass)
- Direct HTTP scraping (without `--use-browser`) returns empty results

## Project Structure

```
explore_scraper/
├── __init__.py          # Package initialization
├── cli.py               # Command-line interface and main orchestration
├── tfs.py               # URL parsing and building (extracts tfs parameters)
├── tfs_builder.py       # Programmatic TFS generation from airport codes (protobuf)
├── fetch_http.py        # Direct HTTP fetching (legacy, returns empty for JS pages)
├── fetch_browser.py     # Playwright browser automation (recommended)
└── parse_html.py        # HTML parsing logic (extracts cards from rendered HTML)

flights.proto            # Protocol Buffer definition for Google Flights data
flights_pb2.py           # Generated Python code from flights.proto (via protoc)

data/
└── top_150_us_airports.txt  # Reference list of top 150 US airport codes
```

## Current Status

**✅ Working:**
- **Airport code-based searches** (`--origin JFK`) - supports **any** IATA code worldwide
- **Programmatic TFS parameter generation** using Protocol Buffers (no manual collection needed)
- **Playwright-based browser automation** (`--use-browser`) for JavaScript rendering
- **Full data extraction**: destination, price, currency, dates, duration
- **Base64 decoding** of embedded flight data
- **Proxy support** for both HTTP and SOCKS
- **HTML file parsing** fallback for offline analysis
- **Error handling** for 0 results and network failures

**⚠️ Known Issues:**
- Direct HTTP fetch without browser returns empty (by design - page requires JavaScript)
- Flight duration field is sometimes null (depends on Google's data availability)
- Browser automation requires sandbox bypass on macOS/Linux (AI tools may need permissions)

**🔮 Future Enhancements:**
- Add image URLs extraction
- Extract coordinates/map data
- Parse airline information if available
- Add retry logic for network failures
- Support for multiple currencies
- Batch mode: scrape multiple airports at once
- Caching layer for repeated queries

