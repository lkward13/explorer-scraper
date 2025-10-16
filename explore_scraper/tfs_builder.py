"""
TFS parameter builder for Google Travel Explore.

Uses protocol buffers to construct proper tfs parameters.
"""

import base64
import sys
from pathlib import Path

# Add parent directory to path to import generated protobuf
sys.path.insert(0, str(Path(__file__).parent.parent))
import flights_pb2


def build_tfs_from_airport_iata(airport_code: str) -> str:
    """
    Build a tfs parameter from an IATA airport code using protocol buffers.
    
    Args:
        airport_code: 3-letter IATA code like "JFK", "LAX", "ATL"
        
    Returns:
        URL-safe Base64-encoded tfs parameter (no padding)
        
    Constructs: "Round-trip, Economy, 1 Adult, from {ORIGIN} to anywhere"
    """
    origin_iata = airport_code.upper()
    
    # Build the Info message
    info = flights_pb2.Info()
    info.seat = flights_pb2.ECONOMY
    info.trip = flights_pb2.ROUND_TRIP
    info.passengers.append(flights_pb2.ADULT)
    
    # data[0]: from_flight = origin
    d1 = info.data.add()
    d1.from_flight.airport = origin_iata
    
    # data[1]: to_flight = origin (for "to anywhere and back")
    d2 = info.data.add()
    d2.to_flight.airport = origin_iata
    
    # Serialize to bytes
    raw = info.SerializeToString()
    
    # Base64 encode (URL-safe, no padding)
    b64 = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    
    return b64


def build_tfs_from_airport_code(airport_code: str) -> str:
    """
    Build a tfs parameter from an airport code.
    
    Args:
        airport_code: 3-letter IATA code (e.g., "LAX", "JFK", "DFW")
        
    Returns:
        URL-safe Base64-encoded tfs parameter (no padding)
    """
    return build_tfs_from_airport_iata(airport_code)


def build_explore_url_for_origin(airport_code: str, hl: str = "en", curr: str = "USD") -> str:
    """
    Build a complete Google Travel Explore URL for an origin airport.
    
    Args:
        airport_code: 3-letter IATA code
        hl: UI language (default: "en")
        curr: Currency code (default: "USD")
        
    Returns:
        Complete Google Travel Explore URL
    """
    tfs = build_tfs_from_airport_iata(airport_code)
    return f"https://www.google.com/travel/explore?tfs={tfs}&hl={hl}&tfu=GgA&curr={curr}"


# Test function
if __name__ == "__main__":
    # Test with various airports
    for code in ["DFW", "OKC", "JFK", "LAX"]:
        print(f"\n{code}:")
        tfs = build_tfs_from_airport_code(code)
        print(f"  TFS: {tfs}")
        url = build_explore_url_for_origin(code)
        print(f"  URL: {url}")

