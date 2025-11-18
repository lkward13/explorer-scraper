#!/usr/bin/env python3
"""
Collect TFS parameters for different destination regions using Playwright.

Usage:
    python scripts/collect_regions.py --origin LAX
    python scripts/collect_regions.py --origin ATL --regions "Europe,Asia"
    python scripts/collect_regions.py --origin JFK --out data/region_tfs/JFK.json
"""

import re
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional, Dict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# Standard regions available in Google Travel Explore
DEFAULT_REGIONS = [
    "North America",
    "Central America",
    "South America",
    "Caribbean",
    "Europe",
    "Africa",
    "Asia",
    "Oceania",
    "Middle East",
]


async def get_tfs_for_region(
    page,  # Reuse existing page
    origin: str,
    region: str,
    verbose: bool = False,
    timeout: int = 30000
) -> Optional[str]:
    """
    Automate browser to get TFS parameter for origin → region.
    
    Strategy:
    1. Build URL with origin already set using our protobuf TFS
    2. Navigate to that URL (origin pre-filled)
    3. Only automate the destination field
    4. Extract the new TFS from URL
    
    Args:
        page: Playwright page object (reused across calls)
        origin: IATA airport code (e.g., "LAX", "JFK")
        region: Destination region (e.g., "Europe", "Asia")
        verbose: Print debug info
        timeout: Timeout for page operations in ms
        
    Returns:
        TFS parameter string or None if failed
    """
    # Import our TFS builder
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from explore_scraper.tfs_builder import build_explore_url_for_origin
    
    try:
        # Start with origin already set in URL
        start_url = build_explore_url_for_origin(origin)
        if verbose:
            print(f"[{origin}→{region}] Navigating with origin pre-set...", file=sys.stderr)
            print(f"[{origin}→{region}] URL: {start_url}", file=sys.stderr)
        
        if verbose:
            print(f"[{origin}→{region}] Starting page.goto()...", file=sys.stderr)
        await page.goto(start_url, wait_until="networkidle", timeout=timeout)
        if verbose:
            print(f"[{origin}→{region}] Page loaded, waiting 3s...", file=sys.stderr)
        await page.wait_for_timeout(3000)  # Let page fully load
        
        if verbose:
            print(f"[{origin}→{region}] Setting destination to: {region}", file=sys.stderr)
        
        # Find the destination input (origin is already set)
        # Try clicking the "Where to?" field
        dest_found = False
        
        # Method 1: Look for empty destination field
        try:
            # Wait for page to be ready
            await page.wait_for_selector('input[type="text"]', timeout=5000)
            
            # Find all text inputs
            inputs = await page.query_selector_all('input[type="text"]')
            
            # Look for the one that's for destination (usually the second one, or has placeholder)
            for inp in inputs:
                placeholder = await inp.get_attribute('placeholder')
                aria_label = await inp.get_attribute('aria-label')
                value = await inp.get_attribute('value')
                
                # Check if this looks like a destination field
                if placeholder and 'where to' in placeholder.lower():
                    dest_input = inp
                    dest_found = True
                    break
                elif aria_label and 'where to' in aria_label.lower():
                    dest_input = inp
                    dest_found = True
                    break
                elif aria_label and 'destination' in aria_label.lower():
                    dest_input = inp
                    dest_found = True
                    break
            
            if not dest_found and len(inputs) >= 2:
                # Fallback: assume second input is destination
                dest_input = inputs[1]
                dest_found = True
                if verbose:
                    print(f"[{origin}→{region}] Using second input field as destination", file=sys.stderr)
                    
        except Exception as e:
            if verbose:
                print(f"[{origin}→{region}] Error finding destination field: {e}", file=sys.stderr)
        
        if not dest_found:
            if verbose:
                print(f"[{origin}→{region}] ❌ Destination field not found", file=sys.stderr)
            return None
        
        # Click and type region
        await dest_input.click()
        await page.wait_for_timeout(500)
        await page.keyboard.type(region, delay=100)
        await page.wait_for_timeout(2500)
        
        # Press Enter to use the typed region name (not autocomplete)
        # This ensures "Africa" doesn't become "South Africa", etc.
        if verbose:
            print(f"[{origin}→{region}] Pressing Enter to confirm region", file=sys.stderr)
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(3000)  # Wait for URL to update
        
        current_url = page.url
        if verbose:
            print(f"[{origin}→{region}] Current URL: {current_url[:100]}...", file=sys.stderr)
        
        # Extract TFS from URL
        match = re.search(r'tfs=([^&]+)', current_url)
        if match:
            tfs = match.group(1)
            if verbose:
                print(f"[{origin}→{region}] ✅ Extracted TFS: {tfs[:50]}...", file=sys.stderr)
            return tfs
        else:
            if verbose:
                print(f"[{origin}→{region}] ❌ TFS parameter not found in URL", file=sys.stderr)
            return None
    
    except PlaywrightTimeoutError as e:
        if verbose:
            print(f"[{origin}→{region}] ❌ Timeout: {e}", file=sys.stderr)
        return None
    except Exception as e:
        if verbose:
            print(f"[{origin}→{region}] ❌ Error: {e}", file=sys.stderr)
        return None


async def collect_regions_for_origin(
    origin: str,
    regions: list[str],
    verbose: bool = False,
    delay: int = 2
) -> Dict[str, Optional[str]]:
    """
    Collect TFS parameters for all regions from a given origin.
    Launches a single browser and reuses it for all regions.
    
    Args:
        origin: IATA airport code
        regions: List of region names
        verbose: Print debug info
        delay: Delay between requests in seconds
        
    Returns:
        Dictionary mapping region name to TFS parameter
    """
    results = {}
    
    # Launch a single browser for all regions
    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False  # Run with visible browser to avoid detection
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        
        try:
            for i, region in enumerate(regions, 1):
                print(f"\n{'#'*60}")
                print(f"Region {i}/{len(regions)}: {origin} → {region}")
                print(f"{'#'*60}")
                tfs = await get_tfs_for_region(page, origin, region, verbose=verbose)
                results[region.lower().replace(" ", "_")] = tfs
                
                if i < len(regions) and tfs:
                    print(f"⏳ Waiting {delay}s before next region...")
                    await asyncio.sleep(delay)
        finally:
            await browser.close()
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Collect Google Travel TFS parameters for different destination regions",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--origin",
        required=True,
        help="Origin airport IATA code (e.g., LAX, JFK, ATL)"
    )
    parser.add_argument(
        "--regions",
        help=f"Comma-separated regions (default: all standard regions)"
    )
    parser.add_argument(
        "--out",
        help="Output JSON file (default: data/region_tfs/<ORIGIN>.json)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=2,
        help="Delay between regions in seconds (default: 2)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Parse regions
    if args.regions:
        regions = [r.strip() for r in args.regions.split(",")]
    else:
        regions = DEFAULT_REGIONS
    
    # Set output path
    if args.out:
        output_path = Path(args.out)
    else:
        output_dir = Path("data/region_tfs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.origin.upper()}.json"
    
    print(f"Collecting TFS parameters for {args.origin.upper()}")
    print(f"Regions: {', '.join(regions)}")
    print(f"Output: {output_path}")
    
    # Collect TFS for each region
    results = asyncio.run(
        collect_regions_for_origin(
            args.origin,
            regions,
            verbose=args.verbose,
            delay=args.delay
        )
    )
    
    # Load existing data if file exists, otherwise create new structure
    if output_path.exists():
        with open(output_path, "r") as f:
            output = json.load(f)
        # Merge new results with existing regions
        output["regions"].update(results)
    else:
        # Build new output structure
        output = {
            "origin": args.origin.upper(),
            "regions": results,
            "collected_at": None,  # Could add timestamp
        }
    
    # Add the default "anywhere" TFS using our protobuf builder
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from explore_scraper.tfs_builder import build_tfs_from_airport_code
    output["regions"]["anywhere"] = build_tfs_from_airport_code(args.origin)
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved to {output_path}")
    
    # Summary
    success = sum(1 for v in results.values() if v is not None)
    total = len(results)
    print(f"\nResults: {success}/{total} regions collected successfully")
    
    if success < total:
        print("\n⚠️ Some regions failed. Run with --verbose to debug.")
        sys.exit(1)


if __name__ == "__main__":
    main()

