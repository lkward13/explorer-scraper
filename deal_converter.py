"""
Helper functions for converting deals and classifying regions.
"""

from typing import Optional

# IATA → Country mapping (ISO 2-letter codes)
AIRPORT_COUNTRIES = {
    # North America
    "LAX": "US", "JFK": "US", "ORD": "US", "DFW": "US", "DEN": "US",
    "ATL": "US", "SFO": "US", "SEA": "US", "LAS": "US", "PHX": "US",
    "IAH": "US", "MIA": "US", "BOS": "US", "MSP": "US", "DTW": "US",
    "PHL": "US", "LGA": "US", "BWI": "US", "SLC": "US", "SAN": "US",
    "TPA": "US", "PDX": "US", "STL": "US", "HNL": "US", "ANC": "US",
    "YYZ": "CA", "YVR": "CA", "YUL": "CA", "YYC": "CA",
    
    # Central America & Mexico
    "MEX": "MX", "CUN": "MX", "GDL": "MX", "MTY": "MX", "TIJ": "MX",
    "PTY": "PA", "SJO": "CR", "GUA": "GT", "SAL": "SV", "MGA": "NI",
    "SAP": "HN", "LIR": "CR", "BZE": "BZ",
    
    # Caribbean
    "SJU": "PR", "CUR": "CW", "AUA": "AW", "MBJ": "JM", "PUJ": "DO",
    "NAS": "BS", "BGI": "BB", "GND": "GD", "UVF": "LC", "POS": "TT",
    
    # South America
    "GIG": "BR", "GRU": "BR", "BSB": "BR", "CWB": "BR", "SSA": "BR",
    "EZE": "AR", "AEP": "AR", "SCL": "CL", "LIM": "PE", "BOG": "CO",
    "UIO": "EC", "MVD": "UY", "ASU": "PY", "GYE": "EC", "MDE": "CO",
    
    # Europe
    "LHR": "GB", "LGW": "GB", "CDG": "FR", "ORY": "FR", "AMS": "NL",
    "FRA": "DE", "MUC": "DE", "MAD": "ES", "BCN": "ES", "FCO": "IT",
    "MXP": "IT", "DUB": "IE", "ZRH": "CH", "VIE": "AT", "BRU": "BE",
    "CPH": "DK", "ARN": "SE", "OSL": "NO", "HEL": "FI", "LIS": "PT",
    "ATH": "GR", "IST": "TR", "WAW": "PL", "PRG": "CZ", "BUD": "HU",
    "OTP": "RO", "SOF": "BG", "KEF": "IS", "SNN": "IE", "ORK": "IE",
    
    # Africa
    "JNB": "ZA", "CPT": "ZA", "CAI": "EG", "CMN": "MA", "NBO": "KE",
    "ADD": "ET", "LOS": "NG", "ACC": "GH", "DAR": "TZ",
    
    # South East Asia
    "BKK": "TH", "SIN": "SG", "HKG": "HK", "NRT": "JP", "HND": "JP",
    "KIX": "JP", "ICN": "KR", "PVG": "CN", "PEK": "CN", "DEL": "IN",
    "BOM": "IN", "MNL": "PH", "CGK": "ID", "KUL": "MY", "HAN": "VN",
    "SGN": "VN", "TPE": "TW",
    
    # Oceania
    "SYD": "AU", "MEL": "AU", "BNE": "AU", "PER": "AU", "AKL": "NZ",
    "CHC": "NZ", "PPT": "PF", "NAN": "FJ", "RAR": "CK", "APW": "WS",
    
    # Middle East
    "DXB": "AE", "AUH": "AE", "DOH": "QA", "BAH": "BH", "AMM": "JO",
    "TLV": "IL", "RUH": "SA", "JED": "SA",
}

# Country → Region mapping
REGION_MAP = {
    # North America
    "US": "north_america",
    "CA": "north_america",
    
    # Central America & Mexico
    "MX": "central_america",
    "GT": "central_america",
    "BZ": "central_america",
    "SV": "central_america",
    "HN": "central_america",
    "NI": "central_america",
    "CR": "central_america",
    "PA": "central_america",
    
    # Caribbean
    "PR": "caribbean",
    "CU": "caribbean",
    "JM": "caribbean",
    "HT": "caribbean",
    "DO": "caribbean",
    "BS": "caribbean",
    "TT": "caribbean",
    "BB": "caribbean",
    "LC": "caribbean",
    "GD": "caribbean",
    "VC": "caribbean",
    "AG": "caribbean",
    "DM": "caribbean",
    "KN": "caribbean",
    "AW": "caribbean",
    "CW": "caribbean",
    "BQ": "caribbean",
    "SX": "caribbean",
    "MF": "caribbean",
    "GP": "caribbean",
    "MQ": "caribbean",
    "VG": "caribbean",
    "VI": "caribbean",
    "KY": "caribbean",
    "TC": "caribbean",
    
    # South America
    "CO": "south_america",
    "VE": "south_america",
    "GY": "south_america",
    "SR": "south_america",
    "GF": "south_america",
    "BR": "south_america",
    "EC": "south_america",
    "PE": "south_america",
    "BO": "south_america",
    "PY": "south_america",
    "CL": "south_america",
    "AR": "south_america",
    "UY": "south_america",
    
    # Europe
    "GB": "europe",
    "IE": "europe",
    "FR": "europe",
    "ES": "europe",
    "PT": "europe",
    "IT": "europe",
    "DE": "europe",
    "NL": "europe",
    "BE": "europe",
    "LU": "europe",
    "CH": "europe",
    "AT": "europe",
    "DK": "europe",
    "NO": "europe",
    "SE": "europe",
    "FI": "europe",
    "IS": "europe",
    "PL": "europe",
    "CZ": "europe",
    "SK": "europe",
    "HU": "europe",
    "RO": "europe",
    "BG": "europe",
    "GR": "europe",
    "HR": "europe",
    "SI": "europe",
    "EE": "europe",
    "LV": "europe",
    "LT": "europe",
    "MT": "europe",
    "CY": "europe",
    "RS": "europe",
    "BA": "europe",
    "MK": "europe",
    "AL": "europe",
    "ME": "europe",
    "XK": "europe",
    "MD": "europe",
    "UA": "europe",
    "BY": "europe",
    "TR": "europe",
    
    # Africa
    "EG": "africa",
    "LY": "africa",
    "TN": "africa",
    "DZ": "africa",
    "MA": "africa",
    "MR": "africa",
    "ML": "africa",
    "NE": "africa",
    "TD": "africa",
    "SD": "africa",
    "ER": "africa",
    "DJ": "africa",
    "ET": "africa",
    "SO": "africa",
    "KE": "africa",
    "UG": "africa",
    "RW": "africa",
    "BI": "africa",
    "TZ": "africa",
    "MZ": "africa",
    "MW": "africa",
    "ZM": "africa",
    "ZW": "africa",
    "BW": "africa",
    "NA": "africa",
    "ZA": "africa",
    "LS": "africa",
    "SZ": "africa",
    "AO": "africa",
    "CD": "africa",
    "CF": "africa",
    "CG": "africa",
    "GA": "africa",
    "GQ": "africa",
    "ST": "africa",
    "CM": "africa",
    "NG": "africa",
    "BJ": "africa",
    "TG": "africa",
    "GH": "africa",
    "CI": "africa",
    "LR": "africa",
    "SL": "africa",
    "GN": "africa",
    "GW": "africa",
    "GM": "africa",
    "SN": "africa",
    "CV": "africa",
    
    # South East Asia
    "CN": "south_east_asia",
    "JP": "south_east_asia",
    "KR": "south_east_asia",
    "TW": "south_east_asia",
    "HK": "south_east_asia",
    "MO": "south_east_asia",
    "MN": "south_east_asia",
    "KP": "south_east_asia",
    "TH": "south_east_asia",
    "VN": "south_east_asia",
    "LA": "south_east_asia",
    "KH": "south_east_asia",
    "MM": "south_east_asia",
    "MY": "south_east_asia",
    "SG": "south_east_asia",
    "BN": "south_east_asia",
    "ID": "south_east_asia",
    "TL": "south_east_asia",
    "PH": "south_east_asia",
    "IN": "south_east_asia",
    "PK": "south_east_asia",
    "BD": "south_east_asia",
    "LK": "south_east_asia",
    "NP": "south_east_asia",
    "BT": "south_east_asia",
    "MV": "south_east_asia",
    
    # Oceania
    "AU": "oceania",
    "NZ": "oceania",
    "PG": "oceania",
    "FJ": "oceania",
    "NC": "oceania",
    "SB": "oceania",
    "VU": "oceania",
    "WS": "oceania",
    "TO": "oceania",
    "KI": "oceania",
    "TV": "oceania",
    "NR": "oceania",
    "PW": "oceania",
    "FM": "oceania",
    "MH": "oceania",
    "PF": "oceania",  # French Polynesia (Tahiti)
    "CK": "oceania",  # Cook Islands
    
    # Middle East
    "SA": "middle_east",
    "YE": "middle_east",
    "OM": "middle_east",
    "AE": "middle_east",
    "QA": "middle_east",
    "BH": "middle_east",
    "KW": "middle_east",
    "IQ": "middle_east",
    "SY": "middle_east",
    "JO": "middle_east",
    "LB": "middle_east",
    "IL": "middle_east",
    "PS": "middle_east",
    "IR": "middle_east",
    "AM": "middle_east",
    "AZ": "middle_east",
    "GE": "middle_east",
}


def get_airport_country(iata_code: str) -> Optional[str]:
    """Get the country code for an airport IATA code."""
    return AIRPORT_COUNTRIES.get(iata_code.upper())


def classify_region(iata_code: str, country_code: Optional[str] = None) -> str:
    """
    Classify an airport into a region.
    
    Args:
        iata_code: IATA airport code
        country_code: Optional country code (will look up if not provided)
    
    Returns:
        Region name (e.g., "europe", "caribbean", etc.)
    """
    if country_code is None:
        country_code = get_airport_country(iata_code)
    
    if country_code is None:
        return "unknown"
    
    return REGION_MAP.get(country_code.upper(), "unknown")


if __name__ == "__main__":
    # Test
    test_airports = ["DUB", "PPT", "MEX", "GRU", "SIN", "JNB", "DXB"]
    
    for iata in test_airports:
        country = get_airport_country(iata)
        region = classify_region(iata, country)
        print(f"{iata} → {country} → {region}")
