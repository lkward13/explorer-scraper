#!/usr/bin/env python3
"""
Generate TFS parameters for all regions programmatically (no browser needed).
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from explore_scraper.region_tfs_generator import generate_all_regions_for_origin


def generate_and_save_tfs(origins: list[str], output_dir: Path):
    """
    Generate TFS for all regions for given origins and save to JSON.
    
    Args:
        origins: List of IATA airport codes
        output_dir: Directory to save JSON files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for origin in origins:
        origin_upper = origin.upper()
        print(f"\nGenerating TFS for {origin_upper}...")
        
        # Generate all regions
        regions = generate_all_regions_for_origin(origin_upper)
        
        # Create output structure
        output = {
            "origin": origin_upper,
            "regions": regions,
            "collected_at": datetime.now().isoformat(),
            "method": "programmatic"
        }
        
        # Save to file
        output_path = output_dir / f"{origin_upper}.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"  ✓ Saved to {output_path}")
        print(f"  ✓ Generated {len(regions)} regions")


if __name__ == "__main__":
    # Test with 10 origins
    test_origins = [
        "DFW", "ATL", "PHX", "ORD", "OKC", 
        "BOS", "DEN", "LAX", "JFK", "MIA"
    ]
    
    output_dir = Path(__file__).parent.parent / "data" / "region_tfs"
    
    print("=" * 60)
    print("Generating TFS parameters programmatically")
    print("=" * 60)
    print(f"Origins: {', '.join(test_origins)}")
    print(f"Output: {output_dir}")
    
    generate_and_save_tfs(test_origins, output_dir)
    
    print("\n" + "=" * 60)
    print("✅ Complete! All TFS parameters generated.")
    print("=" * 60)

