# Cron Job Setup for Automated Daily Scraping

## Overview

Currently, you have **NO cron job set up**. Everything is manual. Let's automate it!

## What You Need to Automate

### Daily Workflow:
1. **Scrape** 100 origins (2-4 hours)
2. **Calculate** price insights (30 seconds)
3. **Select** deals using simple thresholds
4. **Send** email digest
5. **Mark** deals as sent (prevents duplicates)

## Recommended Schedule

### Option 1: Daily Morning Scrape (Recommended)
```bash
# Run at 2 AM every day
0 2 * * * cd /Users/lukeward/Documents/Coding\ Projects/Explorer\ Scraper && ./run_100_origins.sh >> /tmp/scrape.log 2>&1

# Send email at 7 AM (after scrape completes)
0 7 * * * cd /Users/lukeward/Documents/Coding\ Projects/Explorer\ Scraper && python3 send_test_email.py --num-deals 50 >> /tmp/email.log 2>&1
```

**Why this works:**
- Scrape runs overnight (2-6 AM)
- Email sent at 7 AM with fresh data
- You wake up to new deals

### Option 2: Evening Scrape
```bash
# Run at 8 PM every day
0 20 * * * cd /Users/lukeward/Documents/Coding\ Projects/Explorer\ Scraper && ./run_100_origins.sh >> /tmp/scrape.log 2>&1

# Send email at midnight (after scrape completes)
0 0 * * * cd /Users/lukeward/Documents/Coding\ Projects/Explorer\ Scraper && python3 send_test_email.py --num-deals 50 >> /tmp/email.log 2>&1
```

### Option 3: All-in-One Pipeline
```bash
# Run complete pipeline at 2 AM
0 2 * * * cd /Users/lukeward/Documents/Coding\ Projects/Explorer\ Scraper && ./run_daily_pipeline.sh >> /tmp/pipeline.log 2>&1
```

**Note:** `run_daily_pipeline.sh` currently uses quality scoring. You'll need to update it to use simple selection first.

## How to Set Up Cron Job

### Step 1: Create the Cron Script

I'll create a dedicated script for you:

```bash
#!/bin/bash
# daily_scrape_and_email.sh
# Complete daily workflow

cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"

# Load environment variables
export $(cat .env | xargs)

echo "=========================================="
echo "Daily Flight Deal Pipeline"
echo "Started: $(date)"
echo "=========================================="

# Step 1: Run 100-origin scrape
echo ""
echo "[1/3] Running 100-origin scrape..."
./run_100_origins.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Scrape failed"
    exit 1
fi

# Step 2: Calculate price insights (for future use)
echo ""
echo "[2/3] Calculating price insights..."
python3 scripts/calculate_price_insights.py --verbose

# Step 3: Send email with simple selection
echo ""
echo "[3/3] Sending email digest..."
python3 send_test_email.py --num-deals 50

echo ""
echo "=========================================="
echo "Pipeline complete: $(date)"
echo "=========================================="
```

### Step 2: Make It Executable

```bash
chmod +x daily_scrape_and_email.sh
```

### Step 3: Test It Manually First

```bash
./daily_scrape_and_email.sh
```

Make sure it works before automating!

### Step 4: Add to Crontab

```bash
# Open crontab editor
crontab -e

# Add this line (runs at 2 AM daily)
0 2 * * * /Users/lukeward/Documents/Coding\ Projects/Explorer\ Scraper/daily_scrape_and_email.sh >> /tmp/flight_deals.log 2>&1
```

### Step 5: Verify Cron Job

```bash
# List your cron jobs
crontab -l

# Check if cron is running (macOS)
sudo launchctl list | grep cron
```

## Cron Schedule Syntax

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Examples:

```bash
# Every day at 2 AM
0 2 * * *

# Every day at 2 AM and 2 PM
0 2,14 * * *

# Every Monday at 3 AM
0 3 * * 1

# Every 6 hours
0 */6 * * *

# Weekdays only at 7 AM
0 7 * * 1-5
```

## Important: macOS Considerations

### 1. Full Disk Access
macOS may block cron from accessing files. Grant access:
1. System Preferences → Security & Privacy
2. Privacy → Full Disk Access
3. Add `/usr/sbin/cron`

### 2. Docker Must Be Running
Your scraper uses Docker. Ensure Docker Desktop:
- Starts automatically on boot
- Or start it in your cron script:

```bash
# Check if Docker is running, start if not
if ! docker info > /dev/null 2>&1; then
    open -a Docker
    sleep 30  # Wait for Docker to start
fi
```

### 3. Environment Variables
Cron has minimal environment. Your script must:
- `cd` to the correct directory
- Load `.env` file explicitly
- Use absolute paths

## Monitoring Your Cron Job

### Check Logs
```bash
# View today's log
tail -f /tmp/flight_deals.log

# View last 100 lines
tail -n 100 /tmp/flight_deals.log

# Search for errors
grep -i error /tmp/flight_deals.log
```

### Email Notifications on Failure
Add this to your cron script:

```bash
#!/bin/bash
# At the top of daily_scrape_and_email.sh

# Email on failure
trap 'echo "Pipeline failed at $(date)" | mail -s "Flight Scraper Failed" your@email.com' ERR
```

### Check Cron Execution
```bash
# macOS: Check system logs
log show --predicate 'process == "cron"' --last 1d

# Or check if script ran
ls -lh /tmp/flight_deals.log
```

## Recommended Setup (Start Here)

### 1. Create the Daily Script

```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"
cat > daily_scrape_and_email.sh << 'EOF'
#!/bin/bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"
export $(grep -v '^#' .env | xargs)

echo "=========================================="
echo "Daily Flight Deal Pipeline - $(date)"
echo "=========================================="

# Run scrape
echo "[1/2] Running scrape..."
./run_100_origins.sh

# Send email
echo "[2/2] Sending email..."
python3 send_test_email.py --num-deals 50

echo "Complete: $(date)"
EOF

chmod +x daily_scrape_and_email.sh
```

### 2. Test It
```bash
./daily_scrape_and_email.sh
```

### 3. Schedule It
```bash
crontab -e
# Add: 0 2 * * * /Users/lukeward/Documents/Coding\ Projects/Explorer\ Scraper/daily_scrape_and_email.sh >> /tmp/flight_deals.log 2>&1
```

### 4. Verify
```bash
# Check it's scheduled
crontab -l

# Next morning, check the log
tail -n 50 /tmp/flight_deals.log
```

## Alternative: launchd (macOS Native)

Instead of cron, macOS prefers `launchd`. Here's how:

### Create Launch Agent
```bash
cat > ~/Library/LaunchAgents/com.flightdeals.scraper.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.flightdeals.scraper</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/lukeward/Documents/Coding Projects/Explorer Scraper/daily_scrape_and_email.sh</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/tmp/flight_deals.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/flight_deals_error.log</string>
</dict>
</plist>
EOF
```

### Load It
```bash
launchctl load ~/Library/LaunchAgents/com.flightdeals.scraper.plist

# Check status
launchctl list | grep flightdeals

# Unload (to stop)
launchctl unload ~/Library/LaunchAgents/com.flightdeals.scraper.plist
```

## Current Status

❌ **No automation set up**
- You're running everything manually
- Need to remember to scrape daily
- Missing data collection opportunities

✅ **What you have:**
- `run_100_origins.sh` - Ready to automate
- `send_test_email.py` - Ready to automate
- `.env` with credentials

🎯 **Next step:** Set up the cron job!

## Quick Start Command

Want me to create the script for you? Just run:

```bash
cd "/Users/lukeward/Documents/Coding Projects/Explorer Scraper"
# I can create the daily script if you want
```

Let me know if you want me to create the automation script!


