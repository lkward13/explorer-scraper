
# ExploreScrape — Lightweight Google Travel Explore Scraper (PRD)

## 1) Executive Summary
**ExploreScrape** is a small, single-purpose scraper that extracts destination cards (e.g., _Seattle – $179_) from **Google Travel Explore** pages that are driven by **TFS** parameters. The v1 goal is **manual runs** that output **JSON** (stdout/file). No database, no scheduler. We keep an optional Playwright fallback for resilience, but default to a fast HTML bootstrap parse (no JavaScript).

- Input: A full `https://www.google.com/travel/explore?tfs=...` URL or a raw `tfs` blob.
- Output: JSON array of `{ destination, min_price, currency }` (+ extra fields when available).
- Scale: Hundreds to a few thousand scrapes/day (no heavy orchestration).
- Deployment: Run locally or on a Hetzner box. Python 3.11+.

---

## 2) Requirements
### Functional
1. Accept `--tfs-url` (or `--tfs` blob) and optional `--hl`, `--gl` (default `en`, `us`).
2. Fetch HTML via HTTP/2, optionally with a proxy (`--proxy http://user:pass@host:port`).
3. Parse bootstrapped data from `AF_initDataCallback` scripts.
4. If HTML path yields insufficient cards, optionally **fallback** to Playwright to capture the `/_/TravelFrontendUi/data/batchexecute` RPC and parse JSON.
5. Print **JSON** to stdout or save to `--out` file.
6. Exit non-zero on hard failures; otherwise code 0.
7. Keep average transfer size low by streaming and early-aborting.

### Non-Functional
- **Simplicity**: a single package with a CLI entry point.
- **Resilience**: cookies set to skip consent; subresources blocked in PW fallback.
- **Performance**: HTML path streams and stops after a price token (plus 2KB grace).

---

## 3) CLI UX
```
python -m explore_scraper.cli   --tfs-url "https://www.google.com/travel/explore?tfs=CBwQ...&tfu=GgA"   --proxy "http://user:pass@IP:PORT"   --max-bytes 16000   --fallback-pw   --out results.json
```
Arguments:
- `--tfs-url` (string) OR `--tfs` (string). Exactly one required.
- `--hl` (default: `en`), `--gl` (default: `us`).
- `--proxy` (optional) for HTTP path.
- `--fallback-pw` (flag) enable PW fallback; `--pw-proxy` optional.
- `--max-bytes` (int, default 16000).
- `--out` (path) optional; if omitted, prints JSON to stdout.
- `--timeout` (seconds, default 12).
- `--verbose` (flag).

---

## 4) Directory Layout
```
explore_scraper/
  __init__.py
  tfs.py                 # URL helpers (build, normalize, extract blob)
  fetch_http.py          # httpx HTTP/2 streaming fetch with early-abort
  parse_bootstrap.py     # parse AF_initDataCallback from HTML
  fallback_pw.py         # optional Playwright RPC capture & parser
  cli.py                 # command-line interface
requirements.txt
README.md
```

---

## 5) Implementation Details & Code Stubs

### 5.1 `explore_scraper/tfs.py`
```python
# explore_scraper/tfs.py
from urllib.parse import urlparse, parse_qs, urlencode

EXPLORE_BASE = "https://www.google.com/travel/explore"

def extract_tfs_from_url(url: str) -> str:
    q = parse_qs(urlparse(url).query)
    tfs = q.get("tfs", [None])[0]
    if not tfs:
        raise ValueError("No tfs param found in URL")
    return tfs

def build_explore_url(tfs: str, hl: str = "en", gl: str = "us") -> str:
    params = {"tfs": tfs, "hl": hl, "gl": gl, "tfu": "GgA"}
    return f"{EXPLORE_BASE}?{urlencode(params)}"
```

### 5.2 `explore_scraper/fetch_http.py`
```python
# explore_scraper/fetch_http.py
import re
import httpx
from typing import Optional

_PRICE_RE = re.compile(rb"(\$|USD|€|£)\s?\d{2,5}")
_EXPLORE_HINT_RE = re.compile(rb"(AF_initDataCallback|About these results|Explore nearby|role=\"main\")", re.I)

def _headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Save-Data": "on",
        "Cookie": "CONSENT=PENDING+987; SOCS=CAI",
    }

async def fetch_html_stream(url: str, proxy: Optional[str], timeout: float = 12.0, max_bytes: int = 16000) -> str:
    limits = httpx.Limits(max_keepalive_connections=4, max_connections=4)
    async with httpx.AsyncClient(http2=True, headers=_headers(), limits=limits, timeout=timeout,
                                 follow_redirects=True, proxies=proxy or None) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            buf = bytearray()
            seen = False
            found_at = -1
            async for chunk in r.aiter_bytes():
                buf += chunk
                if not seen and _EXPLORE_HINT_RE.search(chunk):
                    seen = True
                if found_at < 0 and _PRICE_RE.search(chunk):
                    found_at = len(buf)
                if found_at > 0 and len(buf) >= found_at + 2048:
                    break
                if len(buf) >= max_bytes:
                    break
            return buf.decode(errors="ignore")
```

### 5.3 `explore_scraper/parse_bootstrap.py`
```python
# explore_scraper/parse_bootstrap.py
import json, re
from selectolax.parser import HTMLParser
from typing import List, Dict, Any

_AF_RE = re.compile(r"AF_initDataCallback\((\{.*?\})\);", re.S)
_DATA_RE = re.compile(r"data\s*:\s*(\[[\s\S]*?\])\s*,\s*sideChannel", re.S)
_PRICE_RE = re.compile(r"(?:\$|USD|€|£)\s?(\d{2,5})")

def _extract_arrays(html: str) -> List[list]:
    arrays: List[list] = []
    for s in HTMLParser(html).css("script"):
        t = s.text() or ""
        m = _AF_RE.search(t)
        if not m: continue
        dm = _DATA_RE.search(m.group(1))
        if not dm: continue
        try:
            arrays.append(json.loads(dm.group(1)))
        except Exception:
            pass
    return arrays

def parse_cards_from_html(html: str) -> List[Dict[str, Any]]:
    arrays = _extract_arrays(html)
    out: Dict[str, Dict[str, Any]] = {}

    def walk(x):
        if isinstance(x, list):
            dest, price = None, None
            for el in x:
                if isinstance(el, str):
                    if not dest and 2 <= len(el) <= 64 and el[0].isupper():
                        dest = el
                    if price is None:
                        m = _PRICE_RE.search(el)
                        if m: price = int(m.group(1))
            if dest and price is not None:
                cur = out.get(dest)
                if (not cur) or (price < cur["min_price"]):
                    out[dest] = {"destination": dest, "min_price": price, "currency": "$"}
            for el in x:
                walk(el)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)

    for arr in arrays:
        walk(arr)
    return list(out.values())
```

### 5.4 `explore_scraper/fallback_pw.py`
```python
# explore_scraper/fallback_pw.py
import json
from typing import Optional, Tuple, List, Dict, Any
from playwright.async_api import async_playwright

_XSSI = ")]}'"

async def fetch_rpc(url: str, proxy_url: Optional[str]) -> Tuple[str, List[Dict[str, Any]]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, proxy={"server": proxy_url} if proxy_url else None)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36",
            locale="en-US",
            extra_http_headers={"Save-Data":"on","Accept-Language":"en-US,en;q=0.9"},
        )
        page = await ctx.new_page()
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in
                         {"image","media","font","stylesheet","websocket","other"} else route.continue_())
        captured = {"body": None}
        async def on_response(res):
            if "/_/TravelFrontendUi/data/batchexecute" in res.url and "rpcids=" in res.url:
                try:
                    captured["body"] = await res.text()
                except: pass
        page.on("response", on_response)
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        for _ in range(10):
            if captured["body"]: break
            await page.wait_for_timeout(300)
        body = captured["body"] or ""
        await ctx.close(); await browser.close()

        if body.startswith(_XSSI):
            body = body[len(_XSSI):]

        calls: List[Dict[str, Any]] = []
        try:
            outer = json.loads(body)
            def walk(x):
                if isinstance(x, list):
                    for it in x: walk(it)
                elif isinstance(x, str) and x and x[0] in "[{":
                    try: calls.append(json.loads(x))
                    except: pass
            walk(outer)
        except: pass
        return body, calls

def parse_rpc_cards(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    import re
    PRICE_RE = re.compile(r"(?:\$|USD|€|£)\s?(\d{2,5})")
    out = {}
    def walk(x):
        if isinstance(x, list):
            dest, price = None, None
            for el in x:
                if isinstance(el, str):
                    if not dest and 2 <= len(el) <= 64 and el[0].isupper():
                        dest = el
                    if price is None:
                        m = PRICE_RE.search(el)
                        if m: price = int(m.group(1))
            if dest and price is not None:
                cur = out.get(dest)
                if (not cur) or (price < cur["min_price"]):
                    out[dest] = {"destination": dest, "min_price": price, "currency": "$"}
            for el in x: walk(el)
        elif isinstance(x, dict):
            for v in x.values(): walk(v)
    for c in calls: walk(c)
    return list(out.values())
```

### 5.5 `explore_scraper/cli.py`
```python
# explore_scraper/cli.py
import sys, json, asyncio, argparse
from typing import Optional
from .tfs import extract_tfs_from_url, build_explore_url
from .fetch_http import fetch_html_stream
from .parse_bootstrap import parse_cards_from_html
from .fallback_pw import fetch_rpc, parse_rpc_cards

async def run(
    tfs_url: Optional[str],
    tfs_blob: Optional[str],
    hl: str,
    gl: str,
    proxy: Optional[str],
    pw_proxy: Optional[str],
    max_bytes: int,
    timeout: float,
    fallback_pw: bool,
    verbose: bool,
):
    if not (tfs_url or tfs_blob) or (tfs_url and tfs_blob):
        raise SystemExit("Provide exactly one of --tfs-url or --tfs")

    if tfs_url:
        tfs = extract_tfs_from_url(tfs_url)
    else:
        tfs = tfs_blob

    url = build_explore_url(tfs, hl=hl, gl=gl)

    if verbose:
        print(f"[info] URL: {url}", file=sys.stderr)
        if proxy: print(f"[info] HTTP proxy: {proxy}", file=sys.stderr)

    try:
        html = await fetch_html_stream(url, proxy=proxy, timeout=timeout, max_bytes=max_bytes)
        cards = parse_cards_from_html(html)
        if cards:
            return cards
    except Exception as e:
        if verbose: print(f"[warn] HTML path failed: {e}", file=sys.stderr)

    if not fallback_pw:
        return []

    if verbose:
        print("[info] Falling back to Playwright RPC capture...", file=sys.stderr)
        if pw_proxy: print(f"[info] PW proxy: {pw_proxy}", file=sys.stderr)

    raw, calls = await fetch_rpc(url, proxy_url=pw_proxy)
    cards = parse_rpc_cards(calls)
    return cards

def main():
    p = argparse.ArgumentParser(description="Google Travel Explore scraper (JSON)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tfs-url", type=str, help="Full Explore URL containing tfs=...")
    g.add_argument("--tfs", type=str, help="Raw tfs blob")
    p.add_argument("--hl", type=str, default="en")
    p.add_argument("--gl", type=str, default="us")
    p.add_argument("--proxy", type=str, default=None, help="HTTP proxy for HTML fetch")
    p.add_argument("--pw-proxy", type=str, default=None, help="Proxy for Playwright fallback")
    p.add_argument("--fallback-pw", action="store_true", help="Enable Playwright RPC fallback")
    p.add_argument("--max-bytes", type=int, default=16000)
    p.add_argument("--timeout", type=float, default=12.0)
    p.add_argument("--out", type=str, default=None)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    cards = asyncio.run(run(
        tfs_url=args.tfs_url,
        tfs_blob=args.tfs,
        hl=args.hl,
        gl=args.gl,
        proxy=args.proxy,
        pw_proxy=args.pw_proxy,
        max_bytes=args.max_bytes,
        timeout=args.timeout,
        fallback_pw=args.fallback_pw,
        verbose=args.verbose,
    ))

    if args.out:
        with open(args.out, "w") as f:
            json.dump(cards, f, indent=2)
    else:
        print(json.dumps(cards, indent=2))

if __name__ == "__main__":
    main()
```

### 5.6 `explore_scraper/__init__.py`
```python
# explore_scraper/__init__.py
__all__ = ["tfs", "fetch_http", "parse_bootstrap", "fallback_pw"]
```

### 5.7 `requirements.txt`
```
httpx>=0.27.0
selectolax>=0.3.21
playwright>=1.46.0
```

### 5.8 `README.md`
```
# ExploreScrape (Lightweight Explore Scraper)

## Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

## Run
python -m explore_scraper.cli --tfs-url "https://www.google.com/travel/explore?tfs=CBwQ...&tfu=GgA" --verbose

## With proxy
python -m explore_scraper.cli --tfs-url "..." --proxy "http://user:pass@IP:PORT"

## With fallback to Playwright
python -m explore_scraper.cli --tfs-url "..." --fallback-pw --pw-proxy "http://user:pass@host:port"

## Output
- prints JSON to stdout or --out results.json
```

---

## 6) Acceptance Criteria
- Given a valid Explore TFS URL, the tool prints a non-empty JSON array of destination-price cards.
- When HTML path fails or yields 0 cards, PW fallback (if enabled) returns cards.
- Average transfer size remains small (HTML path early-aborts around 10–15 KB typical).
- CLI exits 0 on success, non-zero on unrecoverable errors.

---

## 7) Future
- Batch mode (`--urls-file`).
- Cron integration.
- Currency normalization & enrichment.
- Basic API for website integration.
