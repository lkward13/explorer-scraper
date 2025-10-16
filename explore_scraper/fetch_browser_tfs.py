"""
Get TFS parameter from Google by automating airport selection.
This is extracted from the collector script for on-demand use.
"""

import re
from playwright.async_api import async_playwright


async def get_tfs_for_airport(airport_code: str, verbose: bool = False) -> str | None:
    """
    Get the TFS parameter for an airport by automating Google Travel Explore.
    
    Args:
        airport_code: 3-letter IATA code (e.g., "JFK", "LAX")
        verbose: Whether to print progress
        
    Returns:
        TFS parameter string, or None if failed
    """
    if verbose:
        print(f"  Automating airport selection for {airport_code}...", end=" ", flush=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to Google Travel Explore
            await page.goto("https://www.google.com/travel/explore", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(3000)
            
            # Find the origin input
            origin_input = await page.query_selector('input[aria-label*="Where from"]') or \
                          await page.query_selector('input[placeholder*="Where from"]') or \
                          await page.query_selector('div[role="combobox"] input[type="text"]')
            
            if not origin_input:
                all_inputs = await page.query_selector_all('input[type="text"]')
                if len(all_inputs) > 0:
                    origin_input = all_inputs[0]
            
            if not origin_input:
                if verbose:
                    print("❌ Input not found")
                await browser.close()
                return None
            
            # Click and type the airport code
            await origin_input.click()
            await page.wait_for_timeout(300)
            
            # Select all and replace
            await page.keyboard.press('Meta+A')
            await page.wait_for_timeout(200)
            await page.keyboard.type(airport_code.upper(), delay=100)
            await page.wait_for_timeout(2000)
            
            # Check for autocomplete options
            all_options = await page.query_selector_all('[role="option"]')
            if len(all_options) == 0:
                if verbose:
                    print("❌ No options")
                await browser.close()
                return None
            
            # Press Arrow Down and Enter to select
            await page.keyboard.press('ArrowDown')
            await page.wait_for_timeout(300)
            await page.keyboard.press('Enter')
            
            # Wait for URL update
            await page.wait_for_timeout(4000)
            
            # Extract TFS from URL
            current_url = page.url
            match = re.search(r'tfs=([^&]+)', current_url)
            
            if match:
                from urllib.parse import unquote
                tfs = unquote(match.group(1))
                if verbose:
                    print(f"✅ Got TFS")
                await browser.close()
                return tfs
            else:
                if verbose:
                    print("❌ No TFS in URL")
                await browser.close()
                return None
                
        except Exception as e:
            if verbose:
                print(f"❌ Error: {str(e)[:50]}")
            await browser.close()
            return None

