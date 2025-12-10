#!/usr/bin/env python3
"""
Simple city-to-IATA mapper using known mappings.

For the 400 unmapped cities, I'll provide the most common ones
based on standard airport knowledge.
"""

# Top 100 most common unmapped cities with their IATA codes
COMMON_CITY_MAPPINGS = {
    # Middle East (very common)
    'Jerusalem': 'TLV',  # Tel Aviv is closest major airport
    'Tel Aviv-Yafo': 'TLV',
    'Dubai': 'DXB',
    'Abu Dhabi': 'AUH',
    'Bahrain': 'BAH',
    'Antalya': 'AYT',
    'Cappadocia': 'ASR',  # Kayseri airport
    'Salalah': 'SLL',
    'Petra': 'AMM',  # Amman is closest
    'Tehran': 'IKA',
    'Riyadh': 'RUH',
    'Kuwait City': 'KWI',
    'Erbil': 'EBL',
    'Doha': 'DOH',
    'Amman': 'AMM',
    'Sharjah': 'SHJ',
    
    # Caribbean & Central America
    'Saint Lucia': 'UVF',  # Hewanorra International
    'Barbados': 'BGI',
    'Bonaire': 'BON',
    'Curaçao': 'CUR',
    'Granada': 'GRX',  # Spain, or GND for Grenada Caribbean
    'San Salvador': 'SAL',
    'Boquete': 'DAV',  # David, Panama
    'Placencia': 'PLJ',
    'San Juan del Sur': 'MGA',  # Managua, Nicaragua
    
    # Europe
    'Paphos': 'PFO',
    'Dubrovnik': 'DBV',
    'Moscow': 'SVO',  # Sheremetyevo
    'Rovaniemi': 'RVN',
    'Santorini': 'JTR',
    'Glasgow': 'GLA',
    'Malta': 'MLA',
    'Mykonos': 'JMK',
    'Manchester': 'MAN',
    'Bordeaux': 'BOD',
    'Luxembourg': 'LUX',
    'Majorca': 'PMI',  # Palma de Mallorca
    
    # North America
    'Mexico City': 'MEX',
    'Halifax': 'YHZ',
    'Charlottetown': 'YYG',
    'Montreal': 'YUL',
    'Anchorage': 'ANC',
    'Puerto Vallarta': 'PVR',
    'Honolulu': 'HNL',
    'Québec City': 'YQB',
    'San Diego': 'SAN',
    'Washington, D.C.': 'DCA',  # or IAD for Dulles
    'New Orleans': 'MSY',
    'Toronto': 'YYZ',
    'Kauai': 'LIH',  # Lihue
    'Bozeman': 'BZN',
    'Fairbanks': 'FAI',
    
    # South America
    'Punta del Este': 'PDP',
    'Salvador': 'SSA',
    'Santa Marta': 'SMR',
    'Rio de Janeiro': 'GIG',  # Galeão
    'Salta': 'SLA',
    'Brasília': 'BSB',
    'São Paulo': 'GRU',  # Guarulhos
    'Mendoza': 'MDZ',
    'Buenos Aires': 'EZE',  # Ezeiza International
    'Cusco': 'CUZ',
    'Manaus': 'MAO',
    'Ushuaia': 'USH',
    'Valparaíso': 'SCL',  # Santiago is closest major airport
    
    # Asia
    'Bali': 'DPS',  # Denpasar
    'Phuket': 'HKT',
    'Chiang Mai': 'CNX',
    'Hanoi': 'HAN',
    'Ho Chi Minh City': 'SGN',
    'Siem Reap': 'REP',
    'Kathmandu': 'KTM',
    'Colombo': 'CMB',
    'Manila': 'MNL',
    'Cebu': 'CEB',
    'Seoul': 'ICN',  # Incheon
    'Osaka': 'KIX',  # Kansai
    'Bangkok': 'BKK',
    'Singapore': 'SIN',
    'Kuala Lumpur': 'KUL',
    'Jakarta': 'CGK',
    'Delhi': 'DEL',
    'Mumbai': 'BOM',
    'Bangalore': 'BLR',
    
    # Oceania
    'Auckland': 'AKL',
    'Christchurch': 'CHC',
    'Queenstown': 'ZQN',
    'Melbourne': 'MEL',
    'Brisbane': 'BNE',
    'Perth': 'PER',
    'Fiji': 'NAN',  # Nadi
    'Bora Bora': 'BOB',
    'Tahiti': 'PPT',
    'Rangiroa': 'RGI',
    
    # Africa
    'Marrakech': 'RAK',
    'Casablanca': 'CMN',
    'Nairobi': 'NBO',
    'Zanzibar': 'ZNZ',
    'Johannesburg': 'JNB',
    'Durban': 'DUR',
    'Victoria Falls': 'VFA',
    'Addis Ababa': 'ADD',
    'Cairo': 'CAI',
    'Luxor': 'LXR',
    'Sharm el-Sheikh': 'SSH',
}

if __name__ == "__main__":
    print("=" * 80)
    print("CITY-TO-IATA MAPPINGS (Top 100+)")
    print("=" * 80)
    print()
    print(f"Total mappings: {len(COMMON_CITY_MAPPINGS)}")
    print()
    print("# Copy-paste into CITY_TO_IATA in worker/test_parallel.py:")
    print()
    
    # Group by region for easier reading
    regions = {
        'Middle East': ['Jerusalem', 'Tel Aviv-Yafo', 'Dubai', 'Abu Dhabi', 'Bahrain', 'Antalya', 'Cappadocia', 'Salalah', 'Petra', 'Tehran', 'Riyadh', 'Kuwait City', 'Erbil', 'Doha', 'Amman', 'Sharjah'],
        'Caribbean & Central America': ['Saint Lucia', 'Barbados', 'Bonaire', 'Curaçao', 'Granada', 'San Salvador', 'Boquete', 'Placencia', 'San Juan del Sur'],
        'Europe': ['Paphos', 'Dubrovnik', 'Moscow', 'Rovaniemi', 'Santorini', 'Glasgow', 'Malta', 'Mykonos', 'Manchester', 'Bordeaux', 'Luxembourg', 'Majorca'],
        'North America': ['Mexico City', 'Halifax', 'Charlottetown', 'Montreal', 'Anchorage', 'Puerto Vallarta', 'Honolulu', 'Québec City', 'San Diego', 'Washington, D.C.', 'New Orleans', 'Toronto', 'Kauai', 'Bozeman', 'Fairbanks'],
        'South America': ['Punta del Este', 'Salvador', 'Santa Marta', 'Rio de Janeiro', 'Salta', 'Brasília', 'São Paulo', 'Mendoza', 'Buenos Aires', 'Cusco', 'Manaus', 'Ushuaia', 'Valparaíso'],
        'Asia': ['Bali', 'Phuket', 'Chiang Mai', 'Hanoi', 'Ho Chi Minh City', 'Siem Reap', 'Kathmandu', 'Colombo', 'Manila', 'Cebu', 'Seoul', 'Osaka', 'Bangkok', 'Singapore', 'Kuala Lumpur', 'Jakarta', 'Delhi', 'Mumbai', 'Bangalore'],
        'Oceania': ['Auckland', 'Christchurch', 'Queenstown', 'Melbourne', 'Brisbane', 'Perth', 'Fiji', 'Bora Bora', 'Tahiti', 'Rangiroa'],
        'Africa': ['Marrakech', 'Casablanca', 'Nairobi', 'Zanzibar', 'Johannesburg', 'Durban', 'Victoria Falls', 'Addis Ababa', 'Cairo', 'Luxor', 'Sharm el-Sheikh'],
    }
    
    for region, cities in regions.items():
        print(f"# {region}")
        for city in cities:
            if city in COMMON_CITY_MAPPINGS:
                print(f"'{city}': '{COMMON_CITY_MAPPINGS[city]}',")
        print()

