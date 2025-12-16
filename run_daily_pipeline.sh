#!/bin/bash
#
# Daily Flight Deal Pipeline
#
# This script runs the complete daily workflow:
# 1. Scrape deals from Google Flights
# 2. Calculate price insights
# 3. Select top deals with quality scoring
# 4. Send digest email
#
# Usage:
#   ./run_daily_pipeline.sh
#   ./run_daily_pipeline.sh --dry-run    # Test without sending email
#   ./run_daily_pipeline.sh --skip-scrape # Skip scraping, just email existing deals

set -e  # Exit on error

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=false
SKIP_SCRAPE=false
NUM_DEALS=50
MIN_QUALITY=70

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-scrape)
            SKIP_SCRAPE=true
            shift
            ;;
        --num-deals)
            NUM_DEALS="$2"
            shift 2
            ;;
        --min-quality)
            MIN_QUALITY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--skip-scrape] [--num-deals N] [--min-quality N]"
            exit 1
            ;;
    esac
done

# Change to script directory
cd "$(dirname "$0")"

echo "================================================================================"
echo -e "${BLUE}DAILY FLIGHT DEAL PIPELINE${NC}"
echo "================================================================================"
echo ""
echo "Configuration:"
echo "  Dry Run: $DRY_RUN"
echo "  Skip Scrape: $SKIP_SCRAPE"
echo "  Number of Deals: $NUM_DEALS"
echo "  Min Quality Score: $MIN_QUALITY"
echo ""

# Step 1: Scrape deals (optional)
if [ "$SKIP_SCRAPE" = false ]; then
    echo "================================================================================"
    echo -e "${BLUE}[1/4] SCRAPING FLIGHT DEALS${NC}"
    echo "================================================================================"
    echo ""
    
    # Check if Docker is available
    if command -v docker &> /dev/null; then
        echo "Running 100-origin scrape in Docker..."
        echo "Expected duration: ~3.5-4 hours"
        echo ""
        
        docker run --rm \
          -e DISPLAY=:99 \
          -e DB_HOST=host.docker.internal \
          -e DB_PORT=5432 \
          -e DB_NAME=flight_deals \
          -e DB_USER="${DB_USER}" \
          -e DB_PASSWORD="${DB_PASSWORD}" \
          explorer-scraper python3 -u test_100_origins_v2.py
        
        echo ""
        echo "✅ Scrape complete!"
    else
        echo -e "${YELLOW}⚠️  Docker not found, skipping scrape${NC}"
    fi
    echo ""
else
    echo "================================================================================"
    echo -e "${YELLOW}[1/4] SKIPPING SCRAPE (using existing data)${NC}"
    echo "================================================================================"
    echo ""
fi

# Step 2: Calculate price insights
echo "================================================================================"
echo -e "${BLUE}[2/4] CALCULATING PRICE INSIGHTS${NC}"
echo "================================================================================"
echo ""

python3 scripts/calculate_price_insights.py --verbose

echo ""

# Step 3: Run tests (optional, quick health check)
echo "================================================================================"
echo -e "${BLUE}[3/4] RUNNING HEALTH CHECK${NC}"
echo "================================================================================"
echo ""

python3 test_full_system.py

echo ""

# Step 4: Send email
echo "================================================================================"
echo -e "${BLUE}[4/4] SENDING DEAL EMAIL${NC}"
echo "================================================================================"
echo ""

if [ "$DRY_RUN" = true ]; then
    python3 send_test_email.py --num-deals "$NUM_DEALS" --min-quality "$MIN_QUALITY" --dry-run
else
    # Use SendGrid if API key is available (for DigitalOcean where SMTP is blocked)
    if [ -n "$SENDGRID_API_KEY" ]; then
        python3 send_daily_deals_sendgrid.py --num-deals "$NUM_DEALS" --min-quality "$MIN_QUALITY"
    else
        python3 send_test_email.py --num-deals "$NUM_DEALS" --min-quality "$MIN_QUALITY"
    fi
fi

echo ""
echo "================================================================================"
echo -e "${GREEN}✅ PIPELINE COMPLETE${NC}"
echo "================================================================================"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo -e "${GREEN}Email sent successfully!${NC}"
    echo "Check your inbox for the daily deals digest."
else
    echo -e "${YELLOW}Dry run complete - no email sent.${NC}"
    echo "Preview saved to: test_email_preview.html"
fi

echo ""
echo "Next run: Tomorrow at the same time"
echo "To automate: Add this script to crontab"
echo "  crontab -e"
echo "  0 8 * * * cd $(pwd) && ./run_daily_pipeline.sh >> /tmp/flight_deals.log 2>&1"
echo ""



