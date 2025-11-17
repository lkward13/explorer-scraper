"""
Enhanced browser-based fetching that clicks cards to extract detailed deal info.

This module:
1. Loads the Explore page
2. Clicks each destination card
3. Extracts the actual airport code from the Flights page URL
4. Extracts deal quality ("$X cheaper than usual")
5. Returns enhanced card data
"""

import re
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def fetch_enhanced_cards(
    url: str,
    proxy: Optional[str] = None,
    timeout: float = 30.0,
    headless: bool = True,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Fetch enhanced destination card data by clicking each card.
    
    Returns list of dicts with fields:
    - destination: destination name
    - min_price: price as integer
    - currency: currency code
    - start_date: start date YYYY-MM-DD
    - end_date: end date YYYY-MM-DD
    - duration: flight duration string
    - airport_code: actual IATA code (e.g., "FLG" for Grand Canyon)
    - deal_quality: savings info (e.g., "$267 cheaper than usual")
    - deal_quality_amount: dollar amount saved (e.g., 267)
    """
    async with async_playwright() as p:
        launch_kwargs = {
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        }
        
        if proxy:
            launch_kwargs["proxy"] = {"server": proxy}
        
        browser = await p.chromium.launch(**launch_kwargs)
        
        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            
            page = await context.new_page()
            page.set_default_timeout(timeout * 1000)
            
            # Navigate to Explore page
            await page.goto(url, wait_until="networkidle")
            
            # Wait for cards to load
            try:
                await page.wait_for_selector(".SwQ5Be", timeout=timeout * 1000)
            except PlaywrightTimeoutError:
                if verbose:
                    print("[warn] No cards found on page", flush=True)
                return []
            
            await page.wait_for_timeout(2000)
            
            # Get all card elements
            cards = await page.query_selector_all(".SwQ5Be")
            
            if verbose:
                print(f"[info] Found {len(cards)} cards to process", flush=True)
            
            enhanced_cards = []
            
            for idx, card in enumerate(cards):
                try:
                    # Extract basic info from the card
                    dest_el = await card.query_selector(".cCO9qc.tdMWuf.mxXqs")
                    if not dest_el:
                        continue
                    
                    destination = (await dest_el.text_content()).strip()
                    
                    # Extract price
                    price_span = await card.query_selector("[data-gs]")
                    if not price_span:
                        continue
                    
                    aria_label = await price_span.get_attribute("aria-label")
                    price_match = re.search(r"(\d+)\s+US dollars", aria_label or "")
                    if not price_match:
                        continue
                    
                    min_price = int(price_match.group(1))
                    
                    # Extract dates from data-gs
                    import base64
                    data_gs = await price_span.get_attribute("data-gs")
                    start_date = None
                    end_date = None
                    try:
                        decoded_gs = base64.b64decode(data_gs).decode("utf-8", errors="ignore")
                        date_match = re.search(r":(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})", decoded_gs)
                        if date_match:
                            start_date = date_match.group(1)
                            end_date = date_match.group(2)
                    except Exception:
                        pass
                    
                    # Extract duration
                    duration_span = await card.query_selector('.ogfYpf span[role="text"]')
                    duration = None
                    if duration_span:
                        duration = await duration_span.get_attribute("aria-label")
                    
                    if verbose:
                        print(f"[{idx+1}/{len(cards)}] Clicking: {destination} (${min_price})", flush=True)
                    
                    # Click the card and wait for navigation
                    airport_code = None
                    deal_quality = None
                    deal_quality_amount = None
                    
                    try:
                        # Click and wait for navigation to complete
                        async with page.expect_navigation(timeout=10000):
                            await card.click()
                        
                        # Wait for page to load
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        await page.wait_for_timeout(2000)
                        
                        # Extract airport code from URL
                        current_url = page.url
                        
                        # Look for destination airport in URL (e.g., /flights/MIA-LAX)
                        url_match = re.search(r'/flights/[A-Z]{3}-([A-Z]{3})', current_url)
                        if url_match:
                            airport_code = url_match.group(1)
                        
                        # Extract deal quality - look for the price comparison text
                        try:
                            # Wait for the price info to load
                            await page.wait_for_selector("text=/cheaper|lower|usual/i", timeout=3000)
                            
                            # Get all text content and search for deal info
                            page_text = await page.text_content("body")
                            
                            # Look for patterns like "$267 cheaper than usual" or "Prices are currently low — $267 cheaper"
                            patterns = [
                                r'\$(\d+)\s+cheaper\s+than\s+usual',
                                r'\$(\d+)\s+cheaper',
                                r'\$(\d+)\s+lower\s+than\s+usual',
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, page_text, re.IGNORECASE)
                                if match:
                                    deal_quality_amount = int(match.group(1))
                                    # Get surrounding context
                                    start = max(0, match.start() - 50)
                                    end = min(len(page_text), match.end() + 50)
                                    deal_quality = page_text[start:end].strip()
                                    break
                        except Exception as e:
                            if verbose:
                                print(f"  ⚠ Could not find deal quality: {e}", flush=True)
                        
                        if verbose and airport_code:
                            print(f"  → Airport: {airport_code}", flush=True)
                        if verbose and deal_quality_amount:
                            print(f"  → Savings: ${deal_quality_amount}", flush=True)
                        
                    except Exception as e:
                        if verbose:
                            print(f"  ✗ Error clicking card: {e}", flush=True)
                    
                    enhanced_cards.append({
                        "destination": destination,
                        "min_price": min_price,
                        "currency": "USD",
                        "start_date": start_date,
                        "end_date": end_date,
                        "duration": duration,
                        "airport_code": airport_code,
                        "deal_quality": deal_quality,
                        "deal_quality_amount": deal_quality_amount,
                    })
                    
                    # Go back to Explore page
                    try:
                        await page.go_back(wait_until="networkidle", timeout=10000)
                        await page.wait_for_timeout(1500)
                        
                        # Re-query cards since DOM changed
                        cards = await page.query_selector_all(".SwQ5Be")
                    except Exception as e:
                        if verbose:
                            print(f"  ✗ Error going back: {e}", flush=True)
                        break
                    
                except Exception as e:
                    if verbose:
                        print(f"  ✗ Error processing card: {e}", flush=True)
                    # Try to go back if we're stuck
                    try:
                        await page.go_back()
                        await page.wait_for_timeout(1000)
                    except:
                        pass
                    continue
            
            await context.close()
            return enhanced_cards
            
        finally:
            await browser.close()

