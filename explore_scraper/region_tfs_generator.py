"""
Generate TFS parameters for all regions programmatically.
No browser automation needed - uses hardcoded Google Knowledge Graph IDs.
"""

import base64
import sys
from pathlib import Path

# Add parent directory to path to import generated protobuf
sys.path.insert(0, str(Path(__file__).parent.parent))
import flights_pb2


# Google Knowledge Graph IDs for regions (extracted from collected TFS)
REGION_KG_IDS = {
    "north_america": "/m/059g4",
    "central_america": "/m/01tzh",
    "south_america": "/m/06n3y",
    "caribbean": "/m/0261m",
    "europe": "/m/02j9z",
    "africa": "/m/0hzlz",
    "asia": "/m/0j0k",
    "oceania": "/m/02wzv",
    "middle_east": "/m/04wsz",
}


def build_tfs_for_region(origin_iata: str, region_kg_id: str) -> str:
    """
    Build a TFS parameter for origin → region using protocol buffers.
    
    Args:
        origin_iata: 3-letter IATA code (e.g., "DFW", "LAX")
        region_kg_id: Google Knowledge Graph ID (e.g., "/m/02j9z" for Europe)
        
    Returns:
        URL-safe Base64-encoded TFS parameter (no padding)
    """
    origin = origin_iata.upper()
    
    # Build the Info message
    info = flights_pb2.Info()
    info.seat = flights_pb2.ECONOMY
    info.trip = flights_pb2.ROUND_TRIP
    info.passengers.append(flights_pb2.ADULT)
    
    # data[0]: from_flight = origin, to_flight = region
    d1 = info.data.add()
    d1.from_flight.airport = origin
    d1.to_flight.airport = region_kg_id
    
    # data[1]: from_flight = region, to_flight = origin (return trip)
    d2 = info.data.add()
    d2.from_flight.airport = region_kg_id
    d2.to_flight.airport = origin
    
    # Serialize to bytes
    raw = info.SerializeToString()
    
    # Base64 encode (URL-safe, no padding)
    b64 = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    
    return b64


def generate_all_regions_for_origin(origin_iata: str) -> dict:
    """
    Generate TFS parameters for all 9 regions for a given origin.
    
    Args:
        origin_iata: 3-letter IATA code
        
    Returns:
        Dictionary mapping region name to TFS parameter
    """
    results = {}
    
    for region_name, kg_id in REGION_KG_IDS.items():
        tfs = build_tfs_for_region(origin_iata, kg_id)
        results[region_name] = tfs
    
    # Also add "anywhere" TFS (origin to anywhere and back)
    info = flights_pb2.Info()
    info.seat = flights_pb2.ECONOMY
    info.trip = flights_pb2.ROUND_TRIP
    info.passengers.append(flights_pb2.ADULT)
    
    d1 = info.data.add()
    d1.from_flight.airport = origin_iata.upper()
    
    d2 = info.data.add()
    d2.to_flight.airport = origin_iata.upper()
    
    raw = info.SerializeToString()
    results["anywhere"] = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    
    return results


def build_explore_url_for_region(origin_iata: str, region_name: str, hl: str = "en", curr: str = "USD") -> str:
    """
    Build a complete Google Travel Explore URL for origin → region.
    
    Args:
        origin_iata: 3-letter IATA code
        region_name: Region name (e.g., "europe", "asia")
        hl: UI language (default: "en")
        curr: Currency code (default: "USD")
        
    Returns:
        Complete Google Travel Explore URL
    """
    region_name_lower = region_name.lower().replace(" ", "_")
    
    if region_name_lower not in REGION_KG_IDS:
        raise ValueError(f"Unknown region: {region_name}. Valid regions: {list(REGION_KG_IDS.keys())}")
    
    kg_id = REGION_KG_IDS[region_name_lower]
    tfs = build_tfs_for_region(origin_iata, kg_id)
    
    return f"https://www.google.com/travel/explore?tfs={tfs}&hl={hl}&tfu=GgA&curr={curr}"


if __name__ == "__main__":
    # Test with DFW
    print("Testing programmatic TFS generation for DFW:")
    print("=" * 60)
    
    regions = generate_all_regions_for_origin("DFW")
    
    for region_name, tfs in regions.items():
        print(f"\n{region_name}:")
        print(f"  TFS: {tfs[:60]}...")
        
    # Compare with collected TFS for Europe
    print("\n" + "=" * 60)
    print("Comparing with collected TFS for DFW → Europe:")
    print(f"Generated: {regions['europe'][:60]}...")
    print(f"Collected: CBwQAxoXagcIARIDREZXcgwIBBIIL20vMDJqOXoaF2oMCAQSCC9tLzAyaj...")

