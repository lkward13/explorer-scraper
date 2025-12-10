"""
Hybrid browser-based fetching: Fast TFS load + selective enhancement.

This module:
1. Loads the Explore page via TFS (fast)
2. Clicks specific cards to get discount data
3. Returns enhanced card data

Much faster than clicking every card.
"""

import re
import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


async def enhance_cards_with_discounts(
    page: Page,
    cards: List[Dict[str, Any]],
    timeout: float = 15.0,
    verbose: bool = False,
    delay_between_clicks: tuple = (2, 4),
) -> List[Dict[str, Any]]:
    """
    Takes a list of cards from fast explore and clicks each one to get discount data.
    
    Args:
        page: Already-loaded Playwright page on the Explore page
        cards: List of cards from parse_html.py (destination, min_price, etc.)
        timeout: Timeout per card click
        verbose: Print progress
        delay_between_clicks: (min, max) seconds to wait between clicks (human-like)
    
    Returns:
        Enhanced cards with deal_quality and deal_quality_amount added
    """
    import random
    
    # Wait for cards to be visible
    try:
        await page.wait_for_selector(".SwQ5Be", timeout=5000)
    except PlaywrightTimeoutError:
        if verbose:
            print("[warn] No cards found on page for enhancement", flush=True)
        return cards
    
    await page.wait_for_timeout(2000)  # Increased initial wait
    
    # Get all card elements
    card_elements = await page.query_selector_all(".SwQ5Be")
    
    if verbose:
        print(f"[info] Enhancing {len(cards)} cards with discount data...", flush=True)
    
    enhanced_cards = []
    
    for idx, card_data in enumerate(cards):
        if idx >= len(card_elements):
            # More cards in data than elements (shouldn't happen, but be safe)
            enhanced_cards.append(card_data)
            continue
        
        card_element = card_elements[idx]
        
        try:
            if verbose:
                print(f"[{idx+1}/{len(cards)}] Checking: {card_data['destination']} (${card_data['min_price']})", flush=True)
            
            deal_quality = None
            deal_quality_amount = None
            airport_code = None
            
            try:
                # Click and wait for navigation
                async with page.expect_navigation(timeout=timeout * 1000):
                    await card_element.click()
                
                # Wait for page to load
                await page.wait_for_load_state("networkidle", timeout=timeout * 1000)
                await page.wait_for_timeout(1500)
                
                # Extract airport code from URL (e.g., /flights/PHX-FCO or /search?tfs=...)
                current_url = page.url
                # Try flight URL pattern first
                url_match = re.search(r'/flights/[A-Z]{3}-([A-Z]{3})', current_url)
                if url_match:
                    airport_code = url_match.group(1)
                else:
                    # Try TFS pattern (destination is second airport in serialized data)
                    # This is less reliable, so only use as fallback
                    pass
                
                # Extract deal quality - look for price comparison text
                try:
                    # Wait for price info (but don't fail if not found)
                    await page.wait_for_selector("text=/cheaper|lower|usual|typical|high|low/i", timeout=3000)
                    
                    # Get all text content
                    page_text = await page.text_content("body")
                    
                    # Look for discount patterns
                    patterns = [
                        r'\$(\d+)\s+cheaper\s+than\s+usual',
                        r'\$(\d+)\s+cheaper',
                        r'\$(\d+)\s+lower\s+than\s+usual',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            deal_quality_amount = int(match.group(1))
                            # Extract just the key phrase, cleaned up
                            deal_quality = f"${deal_quality_amount} cheaper than usual"
                            break
                    
                    # Also check for "Prices are currently X" status
                    status_match = re.search(r'Prices are currently\s+(low|high|typical)', page_text, re.IGNORECASE)
                    if status_match and not deal_quality:
                        deal_quality = f"Prices are currently {status_match.group(1).lower()}"
                    
                except PlaywrightTimeoutError:
                    # No price insights for this route
                    if verbose:
                        print(f"  ⚠ No price insights available", flush=True)
                except Exception as e:
                    if verbose:
                        print(f"  ⚠ Could not extract discount: {e}", flush=True)
                
                if verbose and airport_code:
                    print(f"  → Airport: {airport_code}", flush=True)
                if verbose and deal_quality_amount:
                    print(f"  → Savings: ${deal_quality_amount} ({int(deal_quality_amount / card_data['min_price'] * 100)}% off)", flush=True)
                elif verbose and deal_quality:
                    print(f"  → Status: {deal_quality}", flush=True)
                else:
                    if verbose:
                        print(f"  → No discount data", flush=True)
                
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error clicking card: {e}", flush=True)
            
            # Add enhancement data to card
            enhanced_card = {**card_data}
            if airport_code:
                enhanced_card['airport_code'] = airport_code
            if deal_quality:
                enhanced_card['deal_quality'] = deal_quality
            if deal_quality_amount:
                enhanced_card['deal_quality_amount'] = deal_quality_amount
                # Calculate discount percentage
                enhanced_card['discount_percent'] = round(deal_quality_amount / card_data['min_price'] * 100, 1)
            
            enhanced_cards.append(enhanced_card)
            
            # Go back to Explore page
            try:
                await page.go_back(wait_until="networkidle", timeout=timeout * 1000)
                
                # Human-like delay before next click
                delay = random.uniform(delay_between_clicks[0], delay_between_clicks[1])
                await page.wait_for_timeout(int(delay * 1000))
                
                # Re-query card elements since DOM changed
                card_elements = await page.query_selector_all(".SwQ5Be")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error going back: {e}", flush=True)
                # If we can't go back, just add remaining cards without enhancement
                enhanced_cards.extend(cards[idx + 1:])
                break
            
        except Exception as e:
            if verbose:
                print(f"  ✗ Error processing card: {e}", flush=True)
            # Add card without enhancement
            enhanced_cards.append(card_data)
            # Try to recover
            try:
                await page.go_back()
                await page.wait_for_timeout(1000)
            except:
                pass
    
    return enhanced_cards


async def fetch_and_enhance_cards(
    url: str,
    proxy: Optional[str] = None,
    timeout: float = 30.0,
    headless: bool = True,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Fast TFS load + selective discount enhancement.
    
    Returns list of dicts with fields:
    - destination: destination name
    - min_price: price as integer
    - currency: currency code
    - start_date: start date YYYY-MM-DD
    - end_date: end date YYYY-MM-DD
    - duration: flight duration string
    - airport_code: actual IATA code (if found)
    - deal_quality: savings info (e.g., "$267 cheaper than usual")
    - deal_quality_amount: dollar amount saved (e.g., 267)
    - discount_percent: discount percentage (e.g., 24.5)
    """
    from playwright.async_api import async_playwright
    from explore_scraper.parse_html import parse_cards_from_html
    import sys
    from pathlib import Path
    
    # Add parent directory to path to import browser_stealth
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from browser_stealth import get_stealth_context_options, get_stealth_launch_args, apply_stealth_to_page
    
    async with async_playwright() as p:
        # Get stealth launch args
        launch_kwargs = {
            "headless": headless,
            "args": get_stealth_launch_args()
        }
        
        if proxy:
            launch_kwargs["proxy"] = {"server": proxy}
        
        # Use system Chrome on macOS, Playwright's Chromium elsewhere
        import platform
        if platform.system() == "Darwin":  # macOS
            launch_kwargs['headless'] = False
            browser = await p.chromium.launch(channel='chrome', **launch_kwargs)
        else:  # Linux/Docker
            browser = await p.chromium.launch(**launch_kwargs)
        
        try:
            # Get stealth context options
            context_options = get_stealth_context_options()
            if proxy:
                context_options["proxy"] = {"server": proxy}
            
            context = await browser.new_context(**context_options)
            
            page = await context.new_page()
            page.set_default_timeout(timeout * 1000)
            
            # Apply stealth JavaScript
            await apply_stealth_to_page(page)
            
            # Step 1: Fast TFS load
            if verbose:
                print(f"[1/2] Loading explore page (TFS)...", flush=True)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            except Exception as e:
                if verbose:
                    print(f"[warn] Page load timeout/error, trying to continue: {e}", flush=True)
                # Try to wait for cards anyway
                pass
            
            await page.wait_for_timeout(3000)
            
            # Parse cards from HTML (fast)
            html = await page.content()
            cards = parse_cards_from_html(html)
            
            if verbose:
                print(f"  → Found {len(cards)} cards", flush=True)
            
            if not cards:
                await context.close()
                return []
            
            # Step 2: Enhance with discounts
            if verbose:
                print(f"[2/2] Clicking cards for discount data...", flush=True)
            
            enhanced_cards = await enhance_cards_with_discounts(
                page, cards, timeout=timeout, verbose=verbose
            )
            
            await context.close()
            return enhanced_cards
            
        finally:
            await browser.close()

