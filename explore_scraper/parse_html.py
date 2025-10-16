# explore_scraper/parse_html.py
import re
import base64
from selectolax.parser import HTMLParser
from typing import List, Dict, Any


def parse_cards_from_html(html: str) -> List[Dict[str, Any]]:
    """
    Parse destination cards from Google Travel Explore HTML.
    
    Returns list of dicts with fields:
    - destination: destination name
    - min_price: price as integer
    - currency: currency code (USD, EUR, etc.)
    - start_date: start date YYYY-MM-DD (optional)
    - end_date: end date YYYY-MM-DD (optional)
    - duration: flight duration string (optional)
    """
    tree = HTMLParser(html)
    cards = []
    
    # Find all destination cards
    for card in tree.css(".SwQ5Be"):
        # Extract destination name
        dest_el = card.css_first(".cCO9qc.tdMWuf.mxXqs")
        if not dest_el:
            continue
        
        destination = dest_el.text().strip()
        if not destination:
            continue
        
        # Extract price and dates from data-gs
        price_span = card.css_first("[data-gs]")
        if not price_span:
            continue
        
        data_gs = price_span.attributes.get("data-gs", "")
        aria_label = price_span.attributes.get("aria-label", "")
        
        # Parse price from aria-label (e.g., "249 US dollars")
        price_match = re.search(r"(\d+)\s+US dollars", aria_label)
        if not price_match:
            continue
        
        min_price = int(price_match.group(1))
        
        # Parse dates from data-gs (it's base64 encoded)
        # Decode base64 first, then extract dates
        start_date = None
        end_date = None
        try:
            decoded_gs = base64.b64decode(data_gs).decode("utf-8", errors="ignore")
            date_match = re.search(r":(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})", decoded_gs)
            if date_match:
                start_date = date_match.group(1)
                end_date = date_match.group(2)
        except Exception:
            pass
        
        # Extract flight duration from aria-label
        duration_span = card.css_first('.ogfYpf span[role="text"]')
        duration = None
        if duration_span:
            duration = duration_span.attributes.get("aria-label")
        
        cards.append(
            {
                "destination": destination,
                "min_price": min_price,
                "currency": "USD",
                "start_date": start_date,
                "end_date": end_date,
                "duration": duration,
            }
        )
    
    return cards

