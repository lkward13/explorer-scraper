#!/usr/bin/env python3
"""
Additional city mappings for Tier 2 cities (Found 10-20x)
"""

ADDITIONAL_MAPPINGS = {
    # Caribbean & Central America
    'Roatán': 'RTB',
    'Puerto Plata': 'POP',
    'Montego Bay': 'MBJ',
    'Ocho Rios': 'MBJ',  # Use Montego Bay
    'Negril': 'MBJ',     # Use Montego Bay
    'Providenciales': 'PLS',
    'Freeport': 'FPO',
    'Nassau': 'NAS',
    'Antigua': 'ANU',    # Antigua & Barbuda
    'Nosara': 'NOB',     # Or LIR
    'Puntarenas': 'SJO', # Use San Jose
    'Dominical': 'SJO',
    'Parque Nacional Volcán Arenal': 'SJO',
    'Parque Nacional Tortuguero': 'SJO',
    'Parque Nacional Volcán Tenorio': 'LIR',
    'Copan Ruinas': 'SAP', # San Pedro Sula is closest major airport
    'Quetzaltenango': 'GUA', # Guatemala City
    'León': 'MGA',       # Managua
    'San Juan del Sur': 'MGA',
    
    # South America
    'Machu Picchu': 'CUZ', # Use Cusco
    'Historic Sanctuary of Machu Picchu': 'CUZ',
    'Ollantaytambo': 'CUZ',
    'Parque Nacional Natural Tayrona': 'SMR', # Santa Marta
    'Puerto Viejo de Talamanca': 'SJO',
    
    # Asia
    'Kyoto': 'KIX',      # Use Osaka
    'Beijing': 'PEK',
    'Da Nang': 'DAD',
    'Kochi': 'COK',
    'Bengaluru': 'BLR',
    'Agra': 'DEL',       # Use Delhi (closest major international)
    'Jaipur': 'JAI',
    'Goa': 'GOI',
    
    # Middle East & Africa
    'Giza': 'CAI',       # Use Cairo
    'Bosphorus': 'IST',  # Istanbul
    'Dead Sea': 'AMM',   # Amman
    'Pretoria': 'JNB',   # Johannesburg
    'Pilanesberg National Park': 'JNB',
    'Cradle of Humankind': 'JNB',
    'Gansbaai': 'CPT',   # Cape Town
    'Knysna': 'GRJ',     # George Airport
    
    # Europe
    'Mykonos': 'JMK',
    'Luxembourg': 'LUX',
    'Bordeaux': 'BOD',
    'Manchester': 'MAN',
    'Glasgow': 'GLA',
    'Kazan': 'KZN',
    'Terceira Island': 'TER',
    'Pico Island': 'PIX',
    'Longyearbyen': 'LYR',
    'Gudauri': 'TBS',    # Tbilisi
    
    # North America
    "Peggy's Cove": 'YHZ', # Halifax
    'Denali National Park and Preserve': 'FAI', # Fairbanks
    'Hawaiʻi Volcanoes National Park': 'ITO',   # Hilo
    'Haleiwa': 'HNL',    # Honolulu
}

if __name__ == "__main__":
    print("=" * 80)
    print("ADDITIONAL CITY MAPPINGS (Tier 2)")
    print("=" * 80)
    print()
    print("# Add these to CITY_TO_IATA in worker/test_parallel.py:")
    print()
    
    for city, code in ADDITIONAL_MAPPINGS.items():
        print(f"'{city}': '{code}',")

