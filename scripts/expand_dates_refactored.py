#!/usr/bin/env python3
"""
Refactored expand_dates with browser pooling support.

Key change: scrape_price_graph_data now accepts an optional page parameter
for browser reuse in parallel execution.
"""

# This is a partial refactor showing the key changes needed.
# The full implementation would replace expand_dates.py

async def _do_scraping(page, url, origin, destination, verbose, timeout):
    """
    Core scraping logic extracted to work with any page.
    This is called by both the standalone and pooled versions.
    """
    price_data = []
    dom_scraped_data = []
    actual_destination = None
    deal_quality = None
    deal_quality_amount = None
    flight_details = None
    
    # Set up network interception
    async def handle_response(response):
        if 'google.com' in response.url and response.status == 200:
            try:
                body = await response.body()
                body_text = body.decode('utf-8', errors='ignore')
                
                if 'GetCalendarGraph' in response.url:
                    if verbose:
                        print(f"[info] *** GetCalendarGraph: {response.url[:100]}... ({len(body)} bytes)", file=sys.stderr)
                elif verbose:
                    print(f"[info] Intercepted: {response.url[:80]}... ({len(body)} bytes)", file=sys.stderr)
                
                price_data.append({
                    'url': response.url,
                    'body': body_text,
                    'status': response.status,
                    'size': len(body)
                })
            except Exception as e:
                if verbose:
                    print(f"[warn] Failed to read response: {e}", file=sys.stderr)
    
    # Register handler
    page.on('response', handle_response)
    
    try:
        # Navigate and scrape (all the existing logic from lines 268-545)
        await page.goto(url, wait_until="networkidle", timeout=timeout)
        # ... rest of scraping logic ...
        
    finally:
        # Remove handler to avoid memory leaks when reusing page
        page.remove_listener('response', handle_response)
    
    return {
        'api_responses': price_data,
        'dom_scraped': dom_scraped_data,
        'actual_destination': actual_destination,
        'deal_quality': deal_quality,
        'deal_quality_amount': deal_quality_amount,
        'flight_details': flight_details
    }


async def scrape_price_graph_data(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    verbose: bool = False,
    timeout: int = 30000,
    page = None  # NEW: Optional page for browser pooling
) -> Optional[List[Dict[str, Any]]]:
    """
    Scrape price data from Google Flights price graph.
    
    Args:
        page: Optional Playwright page to reuse (for browser pooling)
              If None, launches its own browser
    """
    url = build_flights_url(origin, destination, start_date, end_date)
    
    if page is None:
        # Standalone mode: launch own browser
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=[...])
            context = await browser.new_context(...)
            page = await context.new_page()
            
            try:
                result = await _do_scraping(page, url, origin, destination, verbose, timeout)
                return result
            finally:
                await browser.close()
    else:
        # Pooled mode: reuse provided page
        return await _do_scraping(page, url, origin, destination, verbose, timeout)




