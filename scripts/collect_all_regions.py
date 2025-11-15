#!/usr/bin/env python3
"""
Collect region TFS parameters for multiple origins.

This is a one-time setup script to collect region-specific TFS parameters
for various origins (DFW, LAX, JFK, etc.) so we can search by region.

Usage:
    python scripts/collect_all_regions.py --origins DFW,LAX,JFK,ORD
    python scripts/collect_all_regions.py --origins-file data/top_150_us_airports.txt --limit 10
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.collect_regions import collect_regions_for_origin, DEFAULT_REGIONS
from datetime import datetime


async def collect_for_multiple_origins(
    origins: list[str],
    regions: list[str],
    verbose: bool = False,
    delay: int = 2
):
    """Collect region TFS for multiple origins."""
    
    print(f"Collecting regions for {len(origins)} origins")
    print(f"Regions: {', '.join(regions)}")
    print(f"Output: data/region_tfs/{{ORIGIN}}.json\n")
    
    for i, origin in enumerate(origins, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(origins)}] Collecting: {origin}")
        print(f"{'='*60}")
        
        # Collect regions for this origin
        results = await collect_regions_for_origin(
            origin=origin,
            regions=regions,
            verbose=verbose,
            delay=delay
        )
        
        # Save to file
        output_dir = Path("data/region_tfs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{origin.upper()}.json"
        
        output_data = {
            "origin": origin.upper(),
            "regions": results,
            "collected_at": datetime.now().isoformat()
        }
        
        import json
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n✅ Saved to {output_path}")
        
        # Check for failures
        failed = [r for r, tfs in results.items() if tfs is None]
        if failed:
            print(f"⚠️  Failed regions: {', '.join(failed)}")
        
        # Delay between origins
        if i < len(origins):
            print(f"\n⏳ Waiting {delay}s before next origin...")
            await asyncio.sleep(delay)
    
    print(f"\n{'='*60}")
    print(f"✅ Completed {len(origins)} origins")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Collect region TFS for multiple origins"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--origins",
        type=str,
        help="Comma-separated list of origin IATA codes (e.g., DFW,LAX,JFK)"
    )
    group.add_argument(
        "--origins-file",
        type=str,
        help="File with one origin per line (e.g., data/top_150_us_airports.txt)"
    )
    
    parser.add_argument(
        "--regions",
        type=str,
        default=','.join(DEFAULT_REGIONS),
        help=f"Comma-separated regions (default: {', '.join(DEFAULT_REGIONS)})"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of origins to process"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=2,
        help="Delay between origins in seconds (default: 2)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Parse origins
    if args.origins:
        origins = [o.strip().upper() for o in args.origins.split(',')]
    else:
        with open(args.origins_file, 'r') as f:
            origins = [line.strip().upper() for line in f if line.strip()]
    
    # Apply limit
    if args.limit:
        origins = origins[:args.limit]
    
    # Parse regions
    regions = [r.strip() for r in args.regions.split(',')]
    
    # Run collection
    asyncio.run(
        collect_for_multiple_origins(
            origins=origins,
            regions=regions,
            verbose=args.verbose,
            delay=args.delay
        )
    )


if __name__ == "__main__":
    main()

