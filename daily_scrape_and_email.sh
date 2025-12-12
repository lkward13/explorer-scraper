#!/bin/bash
#
# Daily Flight Deal Automation
# 
# This script runs automatically via cron to:
# 1. Scrape 100 origins for flight deals
# 2. Select top 25 deals using regional thresholds
# 3. Send email digest
# 4. Mark deals as sent (prevents duplicates)
#
# Schedule: Run daily at 2 AM
# Cron: 0 2 * * * /path/to/daily_scrape_and_email.sh >> /tmp/flight_deals.log 2>&1

set -e  # Exit on error

# Configuration
SCRIPT_DIR="/Users/lukeward/Documents/Coding Projects/Explorer Scraper"
NUM_DEALS=25              # Send top 25 deals (focused, not overwhelming)
MIN_DEALS_REQUIRED=10     # Only send email if we have at least 10 deals
COOLDOWN_DAYS=7           # Don't repeat same route within 7 days

# Change to script directory
cd "$SCRIPT_DIR"

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "=========================================="
echo "Daily Flight Deal Pipeline"
echo "Started: $(date)"
echo "=========================================="

# Check if Docker is running (required for scraper)
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Step 1: Run 100-origin scrape (2-4 hours)
echo ""
echo "[1/3] Running 100-origin scrape..."
echo "  This will take 2-4 hours..."
./run_100_origins.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Scrape failed"
    exit 1
fi
echo "  ✅ Scrape complete"

# Step 2: Calculate price insights (for future use when we have 14+ days of data)
echo ""
echo "[2/3] Calculating price insights..."
python3 scripts/calculate_price_insights.py --verbose
echo "  ✅ Insights calculated"

# Step 3: Check how many deals we have
echo ""
echo "[3/3] Selecting and sending deals..."
DEAL_COUNT=$(python3 -c "
from deal_selector import DealSelector
from database.config import get_connection_string
selector = DealSelector(get_connection_string())
deals = selector.select_deals_simple(cooldown_days=$COOLDOWN_DAYS, limit=$NUM_DEALS)
print(len(deals))
selector.close()
")

echo "  Found $DEAL_COUNT deals meeting criteria"

# Only send email if we have enough deals
if [ "$DEAL_COUNT" -lt "$MIN_DEALS_REQUIRED" ]; then
    echo "  ⚠️  Only $DEAL_COUNT deals found (need $MIN_DEALS_REQUIRED minimum)"
    echo "  Skipping email today - not enough quality deals"
    echo ""
    echo "=========================================="
    echo "Pipeline complete (no email sent): $(date)"
    echo "=========================================="
    exit 0
fi

# Send email
echo "  Sending email with $DEAL_COUNT deals..."
python3 send_test_email.py --num-deals $NUM_DEALS

if [ $? -eq 0 ]; then
    echo "  ✅ Email sent successfully"
else
    echo "  ❌ Email failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Pipeline complete: $(date)"
echo "Sent $DEAL_COUNT deals to $RECIPIENT_EMAIL"
echo "=========================================="


