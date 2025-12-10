# explore_scraper/cli.py
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional
from .tfs import extract_tfs_from_url, build_explore_url
from .tfs_builder import build_tfs_from_airport_code
from .fetch_http import fetch_html_stream
from .fetch_browser import fetch_html_browser
from .fetch_browser_enhanced import fetch_enhanced_cards
from .parse_html import parse_cards_from_html


async def run(
    tfs_url: Optional[str],
    tfs_blob: Optional[str],
    origin_airport: Optional[str],
    region: Optional[str],
    html_file: Optional[str],
    use_browser: bool,
    enhanced_mode: bool,
    hl: str,
    gl: str,
    proxy: Optional[str],
    max_bytes: int,
    timeout: float,
    verbose: bool,
):
    """Main scraper logic."""
    # If HTML file is provided, parse it directly
    if html_file:
        if verbose:
            print(f"[info] Parsing HTML file: {html_file}", file=sys.stderr)
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html = f.read()
            cards = parse_cards_from_html(html)
            
            if not cards:
                print("[error] No destination cards found in HTML file", file=sys.stderr)
                sys.exit(1)
            
            return cards
        except Exception as e:
            print(f"[error] Failed to parse HTML file: {e}", file=sys.stderr)
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    # Determine the TFS parameter source
    param_count = sum([bool(tfs_url), bool(tfs_blob), bool(origin_airport)])
    if param_count == 0:
        raise SystemExit("Provide one of: --origin, --tfs-url, --tfs, or --html-file")
    if param_count > 1:
        raise SystemExit("Provide exactly one of: --origin, --tfs-url, --tfs, or --html-file")

    # Get TFS parameter from appropriate source
    if origin_airport:
        # Check if region-specific TFS exists
        if region:
            region_file = Path(f"data/region_tfs/{origin_airport.upper()}.json")
            if region_file.exists():
                try:
                    with open(region_file, 'r') as f:
                        region_data = json.load(f)
                    
                    region_key = region.lower().replace(" ", "_")
                    if region_key in region_data["regions"]:
                        tfs = region_data["regions"][region_key]
                        
                        # Check if TFS is null (collection failed)
                        if tfs is None:
                            print(f"[error] Region '{region}' TFS is null (collection failed)", file=sys.stderr)
                            print(f"[info] Run: python scripts/collect_regions.py --origin {origin_airport} --regions \"{region}\"", file=sys.stderr)
                            sys.exit(1)
                        
                        if verbose:
                            print(f"[info] Using cached TFS for {origin_airport} → {region}", file=sys.stderr)
                    else:
                        print(f"[error] Region '{region}' not found in {region_file}", file=sys.stderr)
                        print(f"[info] Available regions: {', '.join(region_data['regions'].keys())}", file=sys.stderr)
                        sys.exit(1)
                except Exception as e:
                    print(f"[error] Failed to load region TFS: {e}", file=sys.stderr)
                    if verbose:
                        import traceback
                        traceback.print_exc()
                    sys.exit(1)
            else:
                print(f"[error] No region data found for {origin_airport}", file=sys.stderr)
                print(f"[info] Run: python scripts/collect_regions.py --origin {origin_airport}", file=sys.stderr)
                sys.exit(1)
        else:
            # Build TFS programmatically using protocol buffers (anywhere)
            if verbose:
                print(f"[info] Building TFS for origin: {origin_airport} (anywhere)", file=sys.stderr)
            try:
                tfs = build_tfs_from_airport_code(origin_airport)
            except Exception as e:
                print(f"[error] Failed to build TFS: {e}", file=sys.stderr)
                if verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
    elif tfs_url:
        tfs = extract_tfs_from_url(tfs_url)
    else:
        tfs = tfs_blob

    url = build_explore_url(tfs, hl=hl, gl=gl)

    if verbose:
        print(f"[info] URL: {url}", file=sys.stderr)
        if use_browser:
            print(f"[info] Using Playwright browser automation", file=sys.stderr)
        else:
            print(f"[warn] Using direct HTTP fetch (may not work - use --use-browser if you get 0 results)", file=sys.stderr)
        if proxy:
            print(f"[info] Proxy: {proxy}", file=sys.stderr)

    try:
        # Choose fetch method
        if enhanced_mode:
            # Enhanced mode: click cards to get airport codes and deal quality
            if verbose:
                print(f"[info] Using enhanced mode (clicking cards for details)", file=sys.stderr)
            cards = await fetch_enhanced_cards(url, proxy=proxy, timeout=timeout, headless=True, verbose=verbose)
        elif use_browser:
            html = await fetch_html_browser(url, proxy=proxy, timeout=timeout)
            cards = parse_cards_from_html(html)
        else:
            html = await fetch_html_stream(url, proxy=proxy, timeout=timeout, max_bytes=max_bytes)
            cards = parse_cards_from_html(html)
        
        if not cards:
            error_msg = "No destination cards found in response"
            if not use_browser and not enhanced_mode:
                error_msg += " (try using --use-browser to enable JavaScript rendering)"
            raise RuntimeError(error_msg)
        
        return cards
    except Exception as e:
        # Re-raise the exception so it can be handled by the caller
        raise


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser(
        description="Google Travel Explore scraper (JSON)",
        epilog="Examples:\n"
               "  %(prog)s --origin JFK --use-browser\n"
               "  %(prog)s --origin LAX --use-browser --out results.json\n"
               "  %(prog)s --html-file explore.html",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input source (mutually exclusive)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--origin", type=str, metavar="CODE", help="Airport code (e.g., JFK, LAX, ORD) - recommended")
    g.add_argument("--tfs-url", type=str, help="Full Explore URL containing tfs=...")
    g.add_argument("--tfs", type=str, help="Raw tfs blob")
    g.add_argument("--html-file", type=str, help="Parse a saved HTML file (for JS-rendered pages)")
    
    # Region filter (optional, only works with --origin)
    p.add_argument("--region", type=str, help="Destination region (e.g., 'Europe', 'Asia') - requires pre-collected data")
    
    # Options
    p.add_argument("--use-browser", action="store_true", help="Use Playwright to render JavaScript (required for live scraping)")
    p.add_argument("--enhanced", action="store_true", help="Enhanced mode: click cards to extract airport codes and deal quality (slower but more accurate)")
    p.add_argument("--hl", type=str, default="en", help="Language code (default: en)")
    p.add_argument("--gl", type=str, default="us", help="Region code (default: us)")
    p.add_argument("--proxy", type=str, default=None, help="HTTP/SOCKS proxy (format: http://host:port)")
    p.add_argument("--max-bytes", type=int, default=16000, help="Max bytes to fetch (default: 16000)")
    p.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds (default: 30)")
    p.add_argument("--out", type=str, default=None, help="Output JSON file (default: stdout)")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = p.parse_args()
    
    # Validate --region only works with --origin
    if args.region and not args.origin:
        print("[error] --region requires --origin to be specified", file=sys.stderr)
        sys.exit(1)
    
    cards = asyncio.run(
        run(
            tfs_url=args.tfs_url,
            tfs_blob=args.tfs,
            origin_airport=args.origin,
            region=args.region,
            html_file=args.html_file,
            use_browser=args.use_browser,
            enhanced_mode=args.enhanced,
            hl=args.hl,
            gl=args.gl,
            proxy=args.proxy,
            max_bytes=args.max_bytes,
            timeout=args.timeout,
            verbose=args.verbose,
        )
    )

    if args.out:
        with open(args.out, "w") as f:
            json.dump(cards, f, indent=2)
    else:
        print(json.dumps(cards, indent=2))


if __name__ == "__main__":
    main()

