# explore_scraper/tfs.py
from urllib.parse import urlparse, parse_qs, urlencode

EXPLORE_BASE = "https://www.google.com/travel/explore"


def extract_tfs_from_url(url: str) -> str:
    """Extract the tfs parameter from a Google Travel Explore URL."""
    q = parse_qs(urlparse(url).query)
    tfs = q.get("tfs", [None])[0]
    if not tfs:
        raise ValueError("No tfs param found in URL")
    return tfs


def build_explore_url(tfs: str, hl: str = "en", gl: str = "us") -> str:
    """Build a complete Explore URL with tfs, language, and region parameters."""
    params = {"tfs": tfs, "hl": hl, "gl": gl, "tfu": "GgA"}
    return f"{EXPLORE_BASE}?{urlencode(params)}"

