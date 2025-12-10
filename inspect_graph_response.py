#!/usr/bin/env python3
"""
Capture and inspect GetCalendarGraph API response to look for price insights.
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright

async def capture_graph_response():
    """Capture a real GetCalendarGraph response and inspect it."""
    
    print("Capturing GetCalendarGraph API response...")
    print("Looking for price insights like 'cheaper than usual'\n")
    
    captured_responses = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Intercept network responses
        async def handle_response(response):
            if 'GetCalendarGraph' in response.url:
                try:
                    text = await response.text()
                    captured_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'text': text
                    })
                    print(f"✓ Captured GetCalendarGraph response ({len(text)} bytes)")
                except:
                    pass
        
        context.on('response', handle_response)
        
        page = await context.new_page()
        
        # Navigate to a flights page
        print("Navigating to Google Flights...")
        url = "https://www.google.com/travel/flights/search?tfs=CBwQAhooagwIAhIIL20vMDJ3enZyEgoyMDI2LTAxLTE1cgwIAxIIL20vMDRqcGwyKGoMCAISCC9tLzA0anBsMhIKMjAyNi0wMS0yMnIMCAMSCC9tLzAyd3p2cgEBSAGYAQE&hl=en&gl=us"
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        print("Waiting for price graph to load...")
        await asyncio.sleep(3)
        
        # Try to click price graph button
        try:
            await page.click('button[aria-label*="price" i], button[aria-label*="graph" i]', timeout=5000)
            print("Clicked price graph button")
            await asyncio.sleep(3)
        except:
            print("Could not find price graph button, but that's ok")
        
        await browser.close()
    
    if not captured_responses:
        print("\n✗ No GetCalendarGraph responses captured")
        return
    
    print(f"\n{'='*80}")
    print(f"ANALYZING {len(captured_responses)} RESPONSE(S)")
    print(f"{'='*80}\n")
    
    for idx, resp in enumerate(captured_responses, 1):
        text = resp['text']
        
        # Remove the safety prefix
        if text.startswith(")]}'"):
            text = text[4:]
        
        print(f"Response {idx}:")
        print(f"  Length: {len(text)} chars")
        print(f"  Status: {resp['status']}")
        
        # Look for price-related keywords
        keywords = [
            'cheaper',
            'usual',
            'typical',
            'average',
            'low',
            'high',
            'price',
            'insight',
            'deal',
            'discount',
            'save',
            'savings'
        ]
        
        found_keywords = []
        for keyword in keywords:
            if re.search(keyword, text, re.IGNORECASE):
                # Count occurrences
                count = len(re.findall(keyword, text, re.IGNORECASE))
                found_keywords.append(f"{keyword} ({count}x)")
        
        if found_keywords:
            print(f"  Keywords found: {', '.join(found_keywords)}")
        else:
            print(f"  Keywords found: None")
        
        # Look for specific patterns
        patterns = {
            'Dollar amounts': r'\$\d+',
            'Percentages': r'\d+%',
            'Cheaper phrases': r'cheaper than usual|cheaper|lower than|better than',
            'Price ranges': r'\$\d+[-–]\$\d+',
        }
        
        print(f"\n  Pattern analysis:")
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                sample = matches[:5]  # First 5 matches
                print(f"    {name}: {len(matches)} matches - {sample}")
            else:
                print(f"    {name}: No matches")
        
        # Save full response for manual inspection
        filename = f"graph_response_{idx}.json"
        with open(filename, 'w') as f:
            f.write(text)
        print(f"\n  Full response saved to: {filename}")
        
        # Try to parse the structure
        print(f"\n  Attempting to parse structure...")
        try:
            # Try to find the main data array
            # Format is usually: )]}'\n[["wrb.fr","GetCalendarGraph",...]]
            json_match = re.search(r'\[\[.*\]\]', text)
            if json_match:
                data = json.loads(json_match.group(0))
                print(f"    ✓ Parsed as JSON array with {len(data)} top-level elements")
                
                # Navigate the structure
                if len(data) > 0 and len(data[0]) > 2:
                    payload = data[0][2]
                    print(f"    Payload type: {type(payload)}")
                    if isinstance(payload, str):
                        print(f"    Payload is string (likely escaped JSON): {len(payload)} chars")
                        # Try to parse the escaped JSON
                        try:
                            inner = json.loads(payload)
                            print(f"    ✓ Parsed inner JSON: {type(inner)}")
                            if isinstance(inner, list):
                                print(f"       List with {len(inner)} elements")
                                # Save parsed structure
                                with open(f"graph_response_{idx}_parsed.json", 'w') as f:
                                    json.dump(inner, f, indent=2)
                                print(f"       Saved parsed structure to: graph_response_{idx}_parsed.json")
                        except:
                            print(f"    ✗ Could not parse inner JSON")
                    elif isinstance(payload, list):
                        print(f"    Payload is list with {len(payload)} elements")
        except Exception as e:
            print(f"    ✗ Could not parse: {e}")
        
        print(f"\n{'-'*80}\n")
    
    print(f"{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"\nNext steps:")
    print(f"  1. Review the saved JSON files")
    print(f"  2. Look for price insight data in the structure")
    print(f"  3. If found, update expand_dates_api.py to extract it")
    print(f"\nFiles created:")
    for idx in range(1, len(captured_responses) + 1):
        print(f"  - graph_response_{idx}.json (raw)")
        print(f"  - graph_response_{idx}_parsed.json (parsed, if successful)")

if __name__ == '__main__':
    asyncio.run(capture_graph_response())

