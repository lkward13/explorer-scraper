#!/usr/bin/env python3
"""
Make an actual GetCalendarGraph API call and inspect the response for price insights.
"""
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scripts.expand_dates_api import fetch_calendar_graph
from playwright.async_api import async_playwright

async def main():
    print("="*80)
    print("INSPECTING GetCalendarGraph API RESPONSE")
    print("="*80)
    print()
    print("Making API call: DFW → LHR, Jan 15-22, 2026")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Make the API call
        deals = await fetch_calendar_graph(
            context=context,
            origin='DFW',
            destination='LHR',
            outbound_date='2026-01-15',
            return_date='2026-01-22',
            start_range='2025-11-20',
            end_range='2026-02-20'
        )
        
        await browser.close()
    
    if deals is None:
        print("✗ API call failed")
        return
    
    print(f"✓ API call succeeded, returned {len(deals)} date combinations")
    print()
    
    # The fetch_calendar_graph function parses the response
    # But we need to see the RAW response to find price insights
    # Let me modify it to capture the raw text
    
    print("Re-running with raw response capture...")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Make the API call manually to get raw response
        import urllib.parse
        
        origin = 'DFW'
        destination = 'LHR'
        outbound_date = '2026-01-15'
        return_date = '2026-01-22'
        start_range = '2025-11-20'
        end_range = '2026-02-20'
        
        inner_structure = [
            None,
            [
                None, None, 1, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None,
                [
                    [
                        [[[origin, 0]]],
                        [[[destination, 0]]],
                        None, 0, None, None, outbound_date,
                        None, None, None, None, None, None, None, 3
                    ],
                    [
                        [[[destination, 0]]],
                        [[[origin, 0]]],
                        None, 0, None, None, return_date,
                        None, None, None, None, None, None, None, 3
                    ]
                ],
                None, None, None, 1
            ],
            [start_range, end_range],
            None,
            [9, 9]
        ]
        
        outer_json = json.dumps([None, json.dumps(inner_structure, separators=(',', ':'))], separators=(',', ':'))
        post_body = f"f.req={urllib.parse.quote(outer_json)}&"
        
        url = "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGraph?f.sid=1&bl=boq_travel-frontend-flights-ui_20251118.02_p0&hl=en&gl=us&soc-app=162&soc-platform=1&soc-device=1&_reqid=1&rt=c"
        
        headers = {
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-same-domain': '1',
            'referer': 'https://www.google.com/travel/flights'
        }
        
        response = await context.request.post(url, data=post_body, headers=headers, timeout=30000)
        text = await response.text()
        
        await browser.close()
    
    if text.startswith(")]}'"):
        text = text[4:]
    
    print(f"Raw response length: {len(text)} chars")
    print()
    
    # Save to file
    with open('graph_response_raw.txt', 'w') as f:
        f.write(text)
    print("✓ Saved raw response to: graph_response_raw.txt")
    
    # Look for price insight keywords
    print()
    print("="*80)
    print("KEYWORD ANALYSIS")
    print("="*80)
    print()
    
    keywords = {
        'cheaper': r'cheaper',
        'usual': r'usual',
        'typical': r'typical',
        'average': r'average',
        'low': r'\blow\b',
        'high': r'\bhigh\b',
        'insight': r'insight',
        'discount': r'discount',
        'save': r'save',
        'savings': r'savings',
        'percent': r'\d+%',
        'dollar': r'\$\d+',
    }
    
    for name, pattern in keywords.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"  {name}: {len(matches)} matches")
            if len(matches) <= 10:
                print(f"    Examples: {matches[:5]}")
        else:
            print(f"  {name}: No matches")
    
    # Look for specific phrases
    print()
    print("="*80)
    print("PHRASE SEARCH")
    print("="*80)
    print()
    
    phrases = [
        'cheaper than usual',
        'lower than usual',
        'higher than usual',
        'typical price',
        'price insight',
        'currently low',
        'currently high',
    ]
    
    for phrase in phrases:
        if re.search(phrase, text, re.IGNORECASE):
            print(f"  ✓ Found: '{phrase}'")
            # Show context
            matches = list(re.finditer(phrase, text, re.IGNORECASE))
            for match in matches[:3]:
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                print(f"     Context: ...{context}...")
        else:
            print(f"  ✗ Not found: '{phrase}'")
    
    # Try to parse the JSON structure
    print()
    print("="*80)
    print("STRUCTURE ANALYSIS")
    print("="*80)
    print()
    
    try:
        # The response format is: [["wrb.fr","GetCalendarGraph","{...}",...]]
        data = json.loads(text)
        print(f"✓ Parsed as JSON with {len(data)} top-level elements")
        
        if len(data) > 0:
            first_elem = data[0]
            print(f"  First element has {len(first_elem)} sub-elements")
            
            if len(first_elem) > 2:
                payload_str = first_elem[2]
                print(f"  Payload (element [2]) type: {type(payload_str)}")
                print(f"  Payload length: {len(payload_str) if isinstance(payload_str, str) else 'N/A'}")
                
                # Try to parse the payload
                if isinstance(payload_str, str):
                    try:
                        payload = json.loads(payload_str)
                        print(f"  ✓ Parsed payload as JSON")
                        
                        # Save parsed payload
                        with open('graph_response_parsed.json', 'w') as f:
                            json.dump(payload, f, indent=2)
                        print(f"  ✓ Saved parsed payload to: graph_response_parsed.json")
                        
                        # Analyze structure
                        if isinstance(payload, list):
                            print(f"\n  Payload is a list with {len(payload)} elements")
                            for i, elem in enumerate(payload[:5]):
                                print(f"    [{i}]: {type(elem)} - {str(elem)[:100]}")
                    except Exception as e:
                        print(f"  ✗ Could not parse payload: {e}")
    except Exception as e:
        print(f"✗ Could not parse response: {e}")
    
    print()
    print("="*80)
    print("NEXT STEPS")
    print("="*80)
    print()
    print("1. Review graph_response_raw.txt and graph_response_parsed.json")
    print("2. Look for price insight fields in the structure")
    print("3. If found, update expand_dates_api.py to extract them")
    print()

if __name__ == '__main__':
    asyncio.run(main())

