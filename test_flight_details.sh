#!/bin/bash

echo "=== Testing Flight Details Extraction ==="
echo ""

# Test 1: OKC to Dublin (international, 1 stop)
echo "Test 1: OKC → Dublin (Nov 24 - Dec 3)"
python scripts/expand_dates.py --origin OKC --destination DUB --start 2025-11-24 --end 2025-12-03 --price 428 --threshold 0.10 --out test1.json 2>&1 | grep "Flight:"
echo ""

# Test 2: DFW to NYC (domestic, likely nonstop)
echo "Test 2: DFW → NYC (Dec 1 - Dec 8)"
python scripts/expand_dates.py --origin DFW --destination JFK --start 2025-12-01 --end 2025-12-08 --price 200 --threshold 0.10 --out test2.json 2>&1 | grep "Flight:"
echo ""

# Test 3: LAX to Tokyo (long international)
echo "Test 3: LAX → Tokyo (Jan 15 - Jan 25, 2026)"
python scripts/expand_dates.py --origin LAX --destination NRT --start 2026-01-15 --end 2026-01-25 --price 600 --threshold 0.10 --out test3.json 2>&1 | grep "Flight:"
echo ""

# Test 4: MIA to Cancun (short international)
echo "Test 4: MIA → Cancun (Dec 10 - Dec 17)"
python scripts/expand_dates.py --origin MIA --destination CUN --start 2025-12-10 --end 2025-12-17 --price 250 --threshold 0.10 --out test4.json 2>&1 | grep "Flight:"
echo ""

# Test 5: SEA to London (long international)
echo "Test 5: SEA → London (Feb 1 - Feb 10, 2026)"
python scripts/expand_dates.py --origin SEA --destination LHR --start 2026-02-01 --end 2026-02-10 --price 500 --threshold 0.10 --out test5.json 2>&1 | grep "Flight:"
echo ""

echo "=== Summary ==="
echo ""
echo "Test 1 (OKC→DUB):"
cat test1.json | jq -c '.flight_details'
echo ""
echo "Test 2 (DFW→JFK):"
cat test2.json | jq -c '.flight_details'
echo ""
echo "Test 3 (LAX→NRT):"
cat test3.json | jq -c '.flight_details'
echo ""
echo "Test 4 (MIA→CUN):"
cat test4.json | jq -c '.flight_details'
echo ""
echo "Test 5 (SEA→LHR):"
cat test5.json | jq -c '.flight_details'

