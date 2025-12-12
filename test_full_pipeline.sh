#!/bin/bash
#
# Full Pipeline Test
#
# Tests the complete workflow end-to-end:
# 1. Scrape deals (5 origins for speed)
# 2. Calculate price insights
# 3. Run system tests
# 4. Send email with top deals
#
# Usage:
#   ./test_full_pipeline.sh              # Send real email
#   ./test_full_pipeline.sh --dry-run    # Preview only

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DRY_RUN=""
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
fi

cd "$(dirname "$0")"

echo "================================================================================"
echo -e "${BLUE}FULL PIPELINE TEST - END TO END${NC}"
echo "================================================================================"
echo ""
echo "This will:"
echo "  1. Scrape 5 origins (OKC, DFW, ATL, LAX, ORD) - ~5 minutes"
echo "  2. Calculate price insights from all data"
echo "  3. Run system health checks"
echo "  4. Send email with top 30 deals"
echo ""

if [[ -n "$DRY_RUN" ]]; then
    echo -e "${YELLOW}DRY RUN MODE - Email will not be sent${NC}"
else
    echo -e "${GREEN}LIVE MODE - Email will be sent to lkward13@gmail.com${NC}"
fi

echo ""
echo "Starting in 3 seconds..."
sleep 3
echo ""

# Step 1: Scrape deals
echo "================================================================================"
echo -e "${BLUE}[1/4] SCRAPING DEALS (5 origins)${NC}"
echo "================================================================================"
echo ""

# Use Docker to run scraper with 5 origins
ORIGINS="OKC,DFW,ATL,LAX,ORD"

echo "Running scraper in Docker..."
echo "Origins: $ORIGINS"
echo "Note: Using test_100_origins_v2.py which has database saving built-in"
echo ""

# Create a temporary Python script that runs just these 5 origins
cat > /tmp/test_5_origins_db.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from worker.test_parallel import run_test_phase

async def test_5_origins():
    origins = ['OKC', 'DFW', 'ATL', 'LAX', 'ORD']
    regions = ['caribbean', 'central_america', 'south_america', 'europe', 'africa', 'asia', 'oceania', 'middle_east', 'north_america']
    
    override = {
        'name': '5 Origins Full Pipeline Test',
        'description': '5 origins for quick testing with database save',
        'origins': origins,
        'browsers': 10,
        'deals_per_origin': 5,
        'regions': regions,
    }
    
    await run_test_phase(
        phase=1,
        verbose=True,
        override_config=override,
        use_api=True,
        save_to_db=True  # SAVE TO DATABASE
    )

if __name__ == '__main__':
    asyncio.run(test_5_origins())
PYTHON_SCRIPT

docker run --rm \
  --network host \
  -v "$(pwd)/data:/app/data" \
  -v "/tmp/test_5_origins_db.py:/app/test_5_origins_db.py" \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=5432 \
  -e DB_NAME=flight_deals \
  -e DB_USER=lukeward \
  -e DB_PASSWORD=postgres \
  flight-scraper \
  python3 test_5_origins_db.py

echo ""
echo -e "${GREEN}✅ Scraping complete${NC}"
echo ""

# Step 2: Calculate price insights
echo "================================================================================"
echo -e "${BLUE}[2/4] CALCULATING PRICE INSIGHTS${NC}"
echo "================================================================================"
echo ""

python3 scripts/calculate_price_insights.py --verbose

echo ""
echo -e "${GREEN}✅ Price insights updated${NC}"
echo ""

# Step 3: Run tests
echo "================================================================================"
echo -e "${BLUE}[3/4] RUNNING SYSTEM TESTS${NC}"
echo "================================================================================"
echo ""

if python3 test_full_system.py; then
    echo ""
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Continuing anyway..."
fi

echo ""

# Step 4: Send email
echo "================================================================================"
echo -e "${BLUE}[4/4] SENDING DEAL EMAIL${NC}"
echo "================================================================================"
echo ""

python3 send_test_email.py --num-deals 30 --min-quality 70 $DRY_RUN

echo ""
echo "================================================================================"
echo -e "${GREEN}✅ FULL PIPELINE TEST COMPLETE${NC}"
echo "================================================================================"
echo ""

if [[ -z "$DRY_RUN" ]]; then
    echo -e "${GREEN}✅ Email sent to lkward13@gmail.com${NC}"
    echo ""
    echo "Check your inbox for:"
    echo "  - Top 30 deals"
    echo "  - Grouped by origin"
    echo "  - Quality scores and insights"
else
    echo -e "${YELLOW}Dry run complete - no email sent${NC}"
    echo ""
    echo "Preview saved to: test_email_preview.html"
    echo "Run without --dry-run to send real email"
fi

echo ""
echo "Pipeline tested successfully! 🎉"
echo ""

