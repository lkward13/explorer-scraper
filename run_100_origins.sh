#!/bin/bash
#
# Run 100 Origins Scrape
#
# This will scrape all 100 major US airports to build comprehensive price insights.
# Expected time: 2-4 hours
# Expected deals: ~240,000 deals
#
# Usage:
#   ./run_100_origins.sh

set -e

cd "$(dirname "$0")"

echo "================================================================================"
echo "100-ORIGIN SCRAPE - COMPREHENSIVE DATA COLLECTION"
echo "================================================================================"
echo ""
echo "This will scrape 100 US airports in 4 batches of 25:"
echo "  - Batch 1: Origins 1-25"
echo "  - Batch 2: Origins 26-50"
echo "  - Batch 3: Origins 51-75"
echo "  - Batch 4: Origins 76-100"
echo ""
echo "Configuration:"
echo "  - 10-minute pause between batches"
echo "  - 5 deals per origin (top 5 cheapest)"
echo "  - All 9 regions"
echo "  - Saves to database automatically"
echo ""
echo "Expected results:"
echo "  - ~240,000 deals"
echo "  - ~2,400 unique routes"
echo "  - 2-4 hours total time"
echo ""
echo "After completion:"
echo "  - Run: python3 scripts/calculate_price_insights.py"
echo "  - Then: python3 send_test_email.py"
echo ""
echo "Starting in 3 seconds..."
sleep 3
echo ""

# Run in Docker
docker run --rm \
  --network host \
  -v "$(pwd)/data:/app/data" \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=5432 \
  -e DB_NAME=flight_deals \
  -e DB_USER=lukeward \
  -e DB_PASSWORD=postgres \
  flight-scraper \
  python3 test_100_origins_v2.py

echo ""
echo "================================================================================"
echo "✅ SCRAPE COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Calculate price insights:"
echo "     python3 scripts/calculate_price_insights.py --verbose"
echo ""
echo "  2. Check data quality:"
echo "     python3 test_full_system.py"
echo ""
echo "  3. Send test email:"
echo "     python3 send_test_email.py --num-deals 50"
echo ""

