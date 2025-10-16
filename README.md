# ExploreScrape - Lightweight Google Travel Explore Scraper

Extracts destination cards (name, price, dates, flight duration) from Google Travel Explore pages.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Automated browser scraping (recommended)

Uses Playwright to automate a real browser and extract fully-rendered data:

```bash
# Live scraping with Playwright
python -m explore_scraper.cli \
  --tfs-url "https://www.google.com/travel/explore?tfs=CBwQ..." \
  --use-browser \
  --verbose

# Save to file
python -m explore_scraper.cli \
  --tfs-url "https://www.google.com/travel/explore?tfs=CBwQ..." \
  --use-browser \
  --out results.json

# With proxy
python -m explore_scraper.cli \
  --tfs-url "..." \
  --use-browser \
  --proxy "http://user:pass@IP:PORT"
```

### Parse saved HTML file (alternative)

If you prefer to save HTML manually:

```bash
python -m explore_scraper.cli --html-file explore.html --out results.json
```

**How to save HTML from browser:**
1. Navigate to Google Travel Explore URL in Chrome/Firefox
2. Wait for map and destinations to load
3. Right-click → "Save Page As" → "Webpage, Complete"
4. Use the saved HTML file with the scraper

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
├── fetch_http.py        # Direct HTTP fetching (legacy, returns empty for JS pages)
├── fetch_browser.py     # Playwright browser automation (recommended)
└── parse_html.py        # HTML parsing logic (extracts cards from rendered HTML)
```

## Current Status (Checkpoint)

**✅ Working:**
- Playwright-based browser automation (`--use-browser`)
- Full data extraction: destination, price, currency, dates, duration
- Base64 decoding of embedded flight data
- Proxy support
- HTML file parsing fallback
- Error handling for 0 results

**⚠️ Known Issues:**
- Direct HTTP fetch without browser returns empty (by design - page requires JS)
- Flight duration field is sometimes null (depends on Google's data)

**🔮 Future Enhancements:**
- Add image URLs extraction
- Extract coordinates/map data
- Parse airline information if available
- Add retry logic for network failures
- Support for multiple currencies

