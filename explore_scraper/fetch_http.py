# explore_scraper/fetch_http.py
import re
import httpx
from typing import Optional

_PRICE_RE = re.compile(rb"(\$|USD)\s?\d{2,5}")
_EXPLORE_HINT_RE = re.compile(
    rb"(About these results|Explore nearby|role=\"main\")", re.I
)


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


async def fetch_html_stream(
    url: str, proxy: Optional[str], timeout: float = 12.0, max_bytes: int = 500000
) -> str:
    """Fetch HTML from URL. Note: httpx automatically decompresses gzip/brotli."""
    limits = httpx.Limits(max_keepalive_connections=4, max_connections=4)
    client_kwargs = {
        "http2": True,
        "headers": _headers(),
        "limits": limits,
        "timeout": timeout,
        "follow_redirects": True,
    }
    if proxy:
        client_kwargs["proxy"] = proxy
    
    async with httpx.AsyncClient(**client_kwargs) as client:
        # Use regular get() to let httpx handle decompression properly
        response = await client.get(url)
        response.raise_for_status()
        return response.text

