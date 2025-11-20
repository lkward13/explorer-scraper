#!/usr/bin/env python3
"""Test if URLs load correctly for failing vs successful routes."""
import asyncio
import sys
from playwright.async_api import async_playwright

async def test_url(url, label):
    print(f"\n{'='*80}", flush=True)
    print(f"Testing: {label}", flush=True)
    print(f"URL: {url[:80]}...", flush=True)
    print('='*80, flush=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("  Navigating...", flush=True)
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Check what's on the page
        page_text = await page.text_content("body")
        
        # Look for key indicators
        has_flights = "Top departing flights" in page_text or "Best departing flights" in page_text
        has_price_graph = "Price graph" in page_text
        has_date_grid = "Date grid" in page_text
        has_search_form = "Where to?" in page_text
        
        print(f"  Has flights results: {has_flights}", flush=True)
        print(f"  Has 'Price graph' button: {has_price_graph}", flush=True)
        print(f"  Has 'Date grid' button: {has_date_grid}", flush=True)
        print(f"  Shows search form (blank page): {has_search_form}", flush=True)
        
        # Get the final URL after any redirects
        final_url = page.url
        if final_url != url:
            print(f"  Redirected to: {final_url[:80]}...", flush=True)
        
        await browser.close()
        return has_flights, has_price_graph

async def main():
    # Test failing route
    print("\n\nTEST 1: FAILING ROUTE", flush=True)
    failing_url = "https://www.google.com/travel/flights?tfs=GhoSCjIwMjYtMDEtMTFqBRIDQVRMcgUSA01JQRoaEgoyMDI2LTAxLTIwagUSA01JQXIFEgNBVExCAQFIAZgBAQ&hl=en&gl=us"
    await test_url(failing_url, "ATL → MIA")
    
    # Test successful route
    print("\n\nTEST 2: SUCCESSFUL ROUTE", flush=True)
    success_url = "https://www.google.com/travel/flights?tfs=GhoSCjIwMjYtMDEtMTFqBRIDQVRMcgUSA1NKVRoaEgoyMDI2LTAxLTIwagUSA1NKVXIFEgNBVExCAQFIAZgBAQ&hl=en&gl=us"
    await test_url(success_url, "ATL → SJU")
    
    print("\n\nDONE", flush=True)

if __name__ == '__main__':
    asyncio.run(main())

