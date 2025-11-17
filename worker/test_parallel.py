#!/usr/bin/env python3
"""
Test parallel execution at different scales.

Usage:
    python worker/test_parallel.py --phase 1  # 2 origins, 1 browser (local test)
    python worker/test_parallel.py --phase 2  # 5 origins, 2 browsers
    python worker/test_parallel.py --phase 3  # 10 origins, 4 browsers
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from worker.parallel_executor import ParallelWorkerPool
from explore_scraper.cli import run as explore_run

# Test configurations for each phase
PHASES = {
    1: {
        'name': 'Baseline (local test)',
        'origins': ['PHX', 'DFW'],
        'browsers': 1,
        'deals_per_origin': 5,
        'description': 'Test locally to establish baseline performance'
    },
    2: {
        'name': 'Small parallel',
        'origins': ['PHX', 'DFW', 'LAX', 'ORD', 'JFK'],
        'browsers': 2,
        'deals_per_origin': 5,
        'description': 'Verify 2 browsers work in parallel'
    },
    3: {
        'name': 'Medium scale',
        'origins': ['PHX', 'DFW', 'LAX', 'ORD', 'JFK', 'ATL', 'DEN', 'SEA', 'MIA', 'BOS'],
        'browsers': 4,
        'deals_per_origin': 5,
        'description': 'Test with 4 browsers (~10GB RAM needed)'
    },
}


async def run_explore_for_origin(origin: str, regions: List[str] = None, verbose: bool = False) -> List[dict]:
    """
    Run Explore scraper for a single origin across all regions.
    
    Args:
        origin: Airport code (e.g., 'PHX')
        regions: List of regions to search, or None for default regions
        verbose: Print progress
    
    Returns:
        List of deal cards
    """
    if regions is None:
        regions = ['europe', 'caribbean', 'central-america', 'south_america', 'oceania']
    
    all_cards = []
    
    for region in regions:
        if verbose:
            print(f"  Exploring {origin} → {region}...")
        
        try:
            result = explore_run(
                origin=origin,
                regions=[region],
                verbose=False,
                output_format='json'
            )
            
            # Parse result
            if isinstance(result, str):
                result = json.loads(result)
            
            cards = result.get('deals', [])
            
            # Add origin and search_region to each card
            for card in cards:
                card['origin'] = origin
                card['search_region'] = region
            
            all_cards.extend(cards)
            
            if verbose:
                print(f"    Found {len(cards)} cards")
        
        except Exception as e:
            if verbose:
                print(f"    Error: {str(e)[:100]}")
            continue
    
    return all_cards


def select_top_deals_per_origin(cards: List[dict], deals_per_origin: int) -> List[dict]:
    """
    Select top N deals per origin.
    
    Args:
        cards: List of deal cards from Explore
        deals_per_origin: Number of deals to select per origin
    
    Returns:
        Selected deals ready for expansion
    """
    # Group by origin
    by_origin = {}
    for card in cards:
        origin = card.get('origin')
        if origin not in by_origin:
            by_origin[origin] = []
        by_origin[origin].append(card)
    
    # Select top N per origin
    selected = []
    for origin, origin_cards in by_origin.items():
        # Sort by price, take top N
        sorted_cards = sorted(origin_cards, key=lambda x: x.get('min_price', 9999))
        top_cards = sorted_cards[:deals_per_origin]
        
        # Convert to expansion format
        for card in top_cards:
            selected.append({
                'origin': origin,
                'destination': card.get('destination'),
                'start_date': card.get('start_date'),
                'end_date': card.get('end_date'),
                'price': card.get('min_price'),
                'search_region': card.get('search_region')
            })
    
    return selected


async def run_test_phase(phase: int, verbose: bool = True):
    """
    Run a specific test phase.
    
    Args:
        phase: Phase number (1-3)
        verbose: Print detailed progress
    
    Returns:
        Test results
    """
    if phase not in PHASES:
        print(f"Invalid phase: {phase}. Must be 1-3.")
        return None
    
    config = PHASES[phase]
    
    print(f"\n{'='*80}")
    print(f"PHASE {phase}: {config['name']}")
    print(f"{'='*80}")
    print(f"Description:      {config['description']}")
    print(f"Origins:          {len(config['origins'])} ({', '.join(config['origins'])})")
    print(f"Browsers:         {config['browsers']}")
    print(f"Deals per origin: {config['deals_per_origin']}")
    print(f"Expected deals:   {len(config['origins']) * config['deals_per_origin']}")
    print(f"{'='*80}\n")
    
    overall_start = datetime.now()
    
    # STEP 1: Run Explore for all origins
    print(f"STEP 1: Explore Scraping")
    print(f"-" * 80)
    explore_start = datetime.now()
    
    all_cards = []
    for origin in config['origins']:
        print(f"\nExploring {origin}...")
        cards = await run_explore_for_origin(origin, verbose=verbose)
        all_cards.extend(cards)
        print(f"  Total so far: {len(all_cards)} cards")
    
    explore_time = (datetime.now() - explore_start).total_seconds()
    print(f"\n✓ Explore complete: {len(all_cards)} cards in {explore_time:.1f}s ({explore_time/60:.1f} min)")
    
    # STEP 2: Select top deals
    print(f"\nSTEP 2: Deal Selection")
    print(f"-" * 80)
    
    expansion_candidates = select_top_deals_per_origin(
        all_cards,
        deals_per_origin=config['deals_per_origin']
    )
    
    print(f"Selected {len(expansion_candidates)} deals for expansion:")
    by_origin = {}
    for candidate in expansion_candidates:
        origin = candidate['origin']
        by_origin[origin] = by_origin.get(origin, 0) + 1
    
    for origin, count in sorted(by_origin.items()):
        print(f"  {origin}: {count} deals")
    
    # STEP 3: Parallel expansion
    print(f"\nSTEP 3: Parallel Expansion")
    print(f"-" * 80)
    
    expansion_start = datetime.now()
    
    worker_pool = ParallelWorkerPool(
        num_browsers=config['browsers'],
        verbose=verbose
    )
    
    results = await worker_pool.process_expansions(expansion_candidates)
    
    expansion_time = (datetime.now() - expansion_start).total_seconds()
    
    # STEP 4: Summary
    total_time = (datetime.now() - overall_start).total_seconds()
    
    print(f"\n{'='*80}")
    print(f"PHASE {phase} SUMMARY")
    print(f"{'='*80}")
    print(f"Explore time:         {explore_time:.1f}s ({explore_time/60:.1f} min)")
    print(f"Expansion time:       {expansion_time:.1f}s ({expansion_time/60:.1f} min)")
    print(f"Total time:           {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"\nExpansions attempted: {len(expansion_candidates)}")
    print(f"Expansions succeeded: {len(results)}")
    print(f"Success rate:         {len(results)/len(expansion_candidates)*100:.1f}%")
    
    # Valid deals (after filtering)
    valid_deals = []
    for result in results:
        expansion = result.get('result', {})
        similar_count = len(expansion.get('similar_deals', []))
        if similar_count >= 5:  # Minimum threshold
            valid_deals.append(result)
    
    print(f"\nValid deals (≥5 dates): {len(valid_deals)}")
    print(f"{'='*80}\n")
    
    return {
        'phase': phase,
        'config': config,
        'explore_time': explore_time,
        'expansion_time': expansion_time,
        'total_time': total_time,
        'cards_found': len(all_cards),
        'expansions_attempted': len(expansion_candidates),
        'expansions_succeeded': len(results),
        'valid_deals': len(valid_deals)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Test parallel execution at different scales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python worker/test_parallel.py --phase 1    # Test locally (2 origins, 1 browser)
  python worker/test_parallel.py --phase 2    # Small parallel (5 origins, 2 browsers)
  python worker/test_parallel.py --phase 3    # Medium scale (10 origins, 4 browsers)
        """
    )
    
    parser.add_argument(
        '--phase',
        type=int,
        required=True,
        choices=[1, 2, 3],
        help='Test phase to run (1=baseline, 2=small parallel, 3=medium scale)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce verbosity'
    )
    
    args = parser.parse_args()
    
    # Run the test
    result = asyncio.run(run_test_phase(args.phase, verbose=not args.quiet))
    
    if result:
        print("\n✅ Test complete!")
        print(f"\nNext steps:")
        if args.phase < 3:
            print(f"  Run phase {args.phase + 1}: python worker/test_parallel.py --phase {args.phase + 1}")
        else:
            print("  All local phases complete! Ready for server deployment.")


if __name__ == '__main__':
    main()

