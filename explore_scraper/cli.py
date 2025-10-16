# explore_scraper/cli.py
import sys
import json
import asyncio
import argparse
from typing import Optional
from .tfs import extract_tfs_from_url, build_explore_url
from .fetch_http import fetch_html_stream
from .fetch_browser import fetch_html_browser
from .parse_html import parse_cards_from_html


async def run(
    tfs_url: Optional[str],
    tfs_blob: Optional[str],
    html_file: Optional[str],
    use_browser: bool,
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
    
    # Otherwise, fetch from URL
    if not (tfs_url or tfs_blob) or (tfs_url and tfs_blob):
        raise SystemExit("Provide exactly one of --tfs-url, --tfs, or --html-file")

    if tfs_url:
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
        if use_browser:
            html = await fetch_html_browser(url, proxy=proxy, timeout=timeout)
        else:
            html = await fetch_html_stream(url, proxy=proxy, timeout=timeout, max_bytes=max_bytes)
        
        cards = parse_cards_from_html(html)
        
        if not cards:
            print("[error] No destination cards found in response", file=sys.stderr)
            if not use_browser:
                print("[info] Try using --use-browser to enable JavaScript rendering", file=sys.stderr)
            sys.exit(1)
        
        return cards
    except Exception as e:
        print(f"[error] Scraping failed: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser(description="Google Travel Explore scraper (JSON)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tfs-url", type=str, help="Full Explore URL containing tfs=...")
    g.add_argument("--tfs", type=str, help="Raw tfs blob")
    g.add_argument("--html-file", type=str, help="Parse a saved HTML file (for JS-rendered pages)")
    p.add_argument("--use-browser", action="store_true", help="Use Playwright to render JavaScript (required for live scraping)")
    p.add_argument("--hl", type=str, default="en")
    p.add_argument("--gl", type=str, default="us")
    p.add_argument("--proxy", type=str, default=None, help="HTTP/SOCKS proxy (format: http://host:port)")
    p.add_argument("--max-bytes", type=int, default=16000)
    p.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds (default: 30)")
    p.add_argument("--out", type=str, default=None)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    cards = asyncio.run(
        run(
            tfs_url=args.tfs_url,
            tfs_blob=args.tfs,
            html_file=args.html_file,
            use_browser=args.use_browser,
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

