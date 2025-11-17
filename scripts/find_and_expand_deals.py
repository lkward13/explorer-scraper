#!/usr/bin/env python3
"""
Combined script: Find cheap deals and expand them to find flexible dates.

Workflow:
1. Run Explore scraper to find cheap destinations
2. For each deal, run date expander to find similar-priced dates
3. Filter deals by flexibility (require minimum number of similar dates)
4. Output comprehensive results with all flexible options

Usage:
    python scripts/find_and_expand_deals.py --origin DFW --threshold 0.10 --min-similar-deals 5
    python scripts/find_and_expand_deals.py --origin LAX --threshold 0.15 --limit 10
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from explore_scraper.cli import run as explore_run
from scripts.expand_dates import expand_dates


# Load city → IATA code mapping
CITY_TO_IATA_FILE = Path(__file__).parent.parent / "data" / "city_to_iata.json"
CITY_TO_IATA = {}

try:
    with open(CITY_TO_IATA_FILE, 'r') as f:
        CITY_TO_IATA = json.load(f)
except FileNotFoundError:
    print(f"Warning: City→IATA mapping file not found: {CITY_TO_IATA_FILE}", file=sys.stderr)


async def find_and_expand_deals(
    origin: str,
    regions: Optional[List[str]] = None,
    threshold: float = 0.10,
    min_similar_deals: int = 5,
    limit: Optional[int] = None,
    verbose: bool = False,
    proxy: Optional[str] = None,
    used_deals_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find cheap deals and expand each to find flexible dates.
    
    Args:
        origin: Origin airport IATA code
        regions: List of regions to search (e.g., ["Europe", "Asia"]) - None = anywhere
        threshold: Price threshold for similar deals (0.10 = ±10%)
        min_similar_deals: Minimum number of similar dates required to keep a deal
        limit: Maximum number of deals to expand (None = all)
        verbose: Print detailed progress
        proxy: Optional proxy string
        used_deals_file: JSON file tracking previously used deals
        
    Returns:
        Dict with explore_deals and expanded_deals
    """
    # Default regions if none specified
    if regions is None:
        regions = ["anywhere", "Europe", "Asia", "Africa", "South America", "Oceania", "Caribbean", "Middle East"]
    
    if verbose:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Finding and expanding deals from {origin}", file=sys.stderr)
        print(f"Regions: {', '.join(regions)}", file=sys.stderr)
        print(f"Threshold: ±{threshold*100:.0f}%", file=sys.stderr)
        print(f"Min similar deals required: {min_similar_deals}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
    
    # Step 1: Find cheap deals using Explore scraper across all regions
    all_explore_deals = []
    
    for i, region in enumerate(regions, 1):
        if verbose:
            print(f"[1/{len(regions)+1}] Running Explore scraper for {origin} → {region}...", file=sys.stderr)
        
        try:
            region_deals = await explore_run(
                tfs_url=None,
                tfs_blob=None,
                origin_airport=origin,
                region=None if region == "anywhere" else region,
                html_file=None,
                enhanced_mode=False,
                use_browser=True,
                hl="en",
                gl="us",
                proxy=proxy,
                max_bytes=16000,
                timeout=30.0,
                verbose=False,  # Don't spam logs for each region
            )
            
            # Tag each deal with its region
            for deal in region_deals:
                deal['search_region'] = region
            
            all_explore_deals.extend(region_deals)
            
            if verbose:
                print(f"[✓] Found {len(region_deals)} destinations in {region}", file=sys.stderr)
        
        except Exception as e:
            if verbose:
                print(f"[✗] Error searching {region}: {e}", file=sys.stderr)
            continue
    
    # Deduplicate destinations (same destination may appear in multiple regions)
    seen_destinations = {}
    explore_deals = []
    
    for deal in all_explore_deals:
        dest = deal['destination']
        if dest not in seen_destinations:
            seen_destinations[dest] = deal
            explore_deals.append(deal)
        else:
            # Keep the cheaper price if duplicate
            if deal.get('min_price', float('inf')) < seen_destinations[dest].get('min_price', float('inf')):
                seen_destinations[dest] = deal
                # Replace in list
                explore_deals = [d for d in explore_deals if d['destination'] != dest]
                explore_deals.append(deal)
    
    if verbose:
        print(f"\n[✓] Total: {len(explore_deals)} unique destinations (deduplicated from {len(all_explore_deals)})", file=sys.stderr)
    
    # Filter out deals without dates (can't expand them)
    valid_deals = [
        d for d in explore_deals 
        if d.get('start_date') and d.get('end_date') and d.get('min_price')
    ]
    
    if verbose:
        print(f"[✓] {len(valid_deals)} deals have valid dates for expansion", file=sys.stderr)
    
    if not valid_deals:
        return {
            'origin': origin,
            'explore_deals': explore_deals,
            'expanded_deals': [],
            'summary': {
                'total_destinations': len(explore_deals),
                'deals_with_dates': 0,
                'deals_expanded': 0,
                'deals_with_flexibility': 0
            }
        }
    
    # Group deals by region and take cheapest from each for variety
    deals_by_region = {}
    for deal in valid_deals:
        region = deal.get('search_region', 'unknown')
        if region not in deals_by_region:
            deals_by_region[region] = []
        deals_by_region[region].append(deal)
    
    # Sort each region by price
    for region in deals_by_region:
        deals_by_region[region].sort(key=lambda x: x.get('min_price', 999999))
    
    # Determine how many to take from each region
    if limit:
        per_region = max(1, limit // len(deals_by_region))
    else:
        per_region = 10  # Default: top 10 cheapest from each region
    
    # Take top N cheapest from each region
    deals_to_expand = []
    for region, region_deals in deals_by_region.items():
        deals_to_expand.extend(region_deals[:per_region])
    
    if verbose:
        print(f"\n[info] Taking top {per_region} cheapest deals from each of {len(deals_by_region)} regions", file=sys.stderr)
        for region, region_deals in sorted(deals_by_region.items(), key=lambda x: x[0]):
            cheapest = region_deals[0].get('min_price') if region_deals else 0
            print(f"  {region}: {len(region_deals)} deals (cheapest: ${cheapest})", file=sys.stderr)
        print(f"\n[2/2] Expanding {len(deals_to_expand)} deals...", file=sys.stderr)
    
    # Step 2: Expand deals in batches (parallel processing)
    expanded_deals = []
    max_good_deals = 10  # Stop after finding this many good deals
    batch_size = 2  # Process 2 deals at a time (each opens a browser)
    
    async def expand_single_deal(deal, deal_num, total_deals):
        """Expand a single deal and return result if it passes threshold."""
        destination = deal['destination']
        price = deal['min_price']
        start_date = deal['start_date']
        end_date = deal['end_date']
        
        try:
            # Map city name to IATA code
            dest_code = CITY_TO_IATA.get(destination)
            
            if not dest_code:
                if verbose:
                    print(f"[{deal_num}/{total_deals}] {destination} - no IATA mapping", file=sys.stderr)
                return None
            
            if verbose:
                print(f"[{deal_num}/{total_deals}] Expanding: {origin} → {destination} (${price})", file=sys.stderr)
            
            # Expand the deal to find flexible dates
            expansion = await expand_dates(
                origin=origin,
                destination=dest_code,
                reference_start=start_date,
                reference_end=end_date,
                reference_price=price,
                threshold=threshold,
                verbose=False  # Don't spam logs
            )
            
            # Check if deal has enough flexibility
            similar_count = len(expansion['similar_deals'])
            
            if similar_count >= min_similar_deals:
                if verbose:
                    print(f"[✓] {destination}: {similar_count} similar dates - KEEPING", file=sys.stderr)
                return {
                    'explore_deal': deal,
                    'expansion': expansion,
                    'similar_deals_count': similar_count
                }
            else:
                if verbose:
                    print(f"[✗] {destination}: {similar_count} similar dates - SKIPPING", file=sys.stderr)
                return None
                
        except Exception as e:
            if verbose:
                print(f"[✗] {destination}: Error - {str(e)[:50]}", file=sys.stderr)
            return None
    
    # Process deals in batches
    for batch_start in range(0, len(deals_to_expand), batch_size):
        # Early stopping if we found enough
        if len(expanded_deals) >= max_good_deals:
            if verbose:
                print(f"\n[✓] Found {len(expanded_deals)} flexible deals - stopping early", file=sys.stderr)
            break
        
        batch_end = min(batch_start + batch_size, len(deals_to_expand))
        batch = deals_to_expand[batch_start:batch_end]
        
        if verbose:
            print(f"\n--- Batch {batch_start//batch_size + 1} ({batch_start+1}-{batch_end} of {len(deals_to_expand)}) ---", file=sys.stderr)
        
        # Expand all deals in batch concurrently
        tasks = [
            expand_single_deal(deal, batch_start + i + 1, len(deals_to_expand))
            for i, deal in enumerate(batch)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful expansions
        for result in results:
            if result and not isinstance(result, Exception):
                expanded_deals.append(result)
    
    if verbose:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Summary:", file=sys.stderr)
        print(f"  Total destinations found: {len(explore_deals)}", file=sys.stderr)
        print(f"  Deals with valid dates: {len(valid_deals)}", file=sys.stderr)
        print(f"  Deals expanded: {len(deals_to_expand)}", file=sys.stderr)
        print(f"  Deals with sufficient flexibility: {len(expanded_deals)}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
    
    return {
        'origin': origin,
        'threshold': threshold,
        'min_similar_deals': min_similar_deals,
        'explore_deals': explore_deals,
        'expanded_deals': expanded_deals,
        'summary': {
            'total_destinations': len(explore_deals),
            'deals_with_dates': len(valid_deals),
            'deals_expanded': len(deals_to_expand),
            'deals_with_flexibility': len(expanded_deals)
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Find cheap deals and expand to find flexible dates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find deals from DFW, require 5+ similar dates
  %(prog)s --origin DFW --min-similar-deals 5

  # Wider threshold, expand only top 10 deals
  %(prog)s --origin LAX --threshold 0.15 --limit 10

  # Verbose output
  %(prog)s --origin ORD --verbose
        """
    )
    
    parser.add_argument("--origin", required=True, help="Origin airport IATA code")
    parser.add_argument("--regions", type=str, help="Comma-separated regions to search (default: all regions)")
    parser.add_argument("--threshold", type=float, default=0.10, help="Price threshold for similar deals (default: 0.10 = ±10%%)")
    parser.add_argument("--min-similar-deals", type=int, default=5, help="Minimum similar dates required to keep a deal (default: 5)")
    parser.add_argument("--limit", type=int, help="Max number of deals to expand (default: all)")
    parser.add_argument("--out", help="Output JSON file (default: stdout)")
    parser.add_argument("--proxy", help="HTTP/SOCKS proxy")
    parser.add_argument("--used-deals-file", help="JSON file tracking previously used deals")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Parse regions if provided
    regions_list = None
    if args.regions:
        regions_list = [r.strip() for r in args.regions.split(',')]
    
    # Run the combined workflow
    result = asyncio.run(
        find_and_expand_deals(
            origin=args.origin,
            regions=regions_list,
            threshold=args.threshold,
            min_similar_deals=args.min_similar_deals,
            limit=args.limit,
            verbose=args.verbose,
            proxy=args.proxy,
            used_deals_file=args.used_deals_file
        )
    )
    
    # Output results
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Saved to {args.out}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

