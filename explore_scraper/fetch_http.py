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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "Cache-Control": "max-age=0",
        "Cookie": "CONSENT=YES+US.en+V14+BX; SOCS=CAISHAgBEhJnd3NfMjAyNDExMTktMF9SQzIaAmVuIAEaBgiA3rW4Bg",
        "Referer": "https://www.google.com/",
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

