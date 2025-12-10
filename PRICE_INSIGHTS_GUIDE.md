# Price Insights System Guide

## Overview

The price insights system analyzes historical deal data to calculate statistical insights for each route (origin → destination pair). These insights are used to score deal quality and identify truly exceptional deals.

## System Components

### 1. Database Table: `route_price_insights`

Stores calculated insights for each route:

```sql
route_price_insights
├── origin (DFW, ATL, PHX...)
├── destination (BCN, LHR, CDG...)
├── typical_price (median - best indicator of "normal")
├── low_price_threshold (25th percentile - good deals)
├── high_price_threshold (75th percentile - expensive)
├── min_price_seen (best price ever)
├── max_price_seen (worst price ever)
├── avg_price (mean price)
├── sample_size (number of data points)
├── first_seen (when tracking started)
├── last_updated (when insights were recalculated)
├── data_quality (high/medium/low based on sample size)
└── days_tracked (how many days of data)
```

### 2. Calculation Script: `scripts/calculate_price_insights.py`

Analyzes historical data and updates insights table.

**Usage:**
```bash
# Default: 7+ samples, 90 days lookback
python scripts/calculate_price_insights.py --verbose

# Custom parameters
python scripts/calculate_price_insights.py --min-samples 10 --days 60

# Quiet mode (for cron)
python scripts/calculate_price_insights.py
```

**What it does:**
- Queries all deals from last 90 days
- Calculates statistical measures (median, percentiles, min, max, avg)
- Updates `route_price_insights` table
- Assigns data quality based on sample size:
  - **High:** 30+ samples
  - **Medium:** 14-29 samples
  - **Low:** 7-13 samples

### 3. Quality Scoring: `deal_selector.py`

Scores deals based on price insights.

**Quality Levels:**
- 🏆 **Excellent (90-100):** Best price ever or near-record low
- ⭐ **Great (75-89):** Significantly below typical (below 25th percentile)
- ✅ **Good (60-74):** Below typical price (below median)
- 📊 **Fair (40-59):** Around typical price
- ❓ **Unknown:** No historical data yet

**Scoring Formula:**
```python
if price <= min_seen:
    score = 100  # Best ever!
elif price <= low_threshold:
    score = 85-100  # Great deal
elif price <= typical:
    score = 60-85  # Good deal
else:
    score = 0-60  # Fair or poor
```

## Daily Workflow

### Current System (Still Works)
```bash
# 1. Run daily scrape (100 origins)
docker run ... test_100_origins_v2.py

# 2. Deals stored in expanded_deals table
# 3. Use old deal_selector.select_daily_deals() method
```

### New System (With Price Insights)
```bash
# 1. Run daily scrape (100 origins)
docker run ... test_100_origins_v2.py

# 2. Calculate price insights
python scripts/calculate_price_insights.py

# 3. Get scored deals
python -c "
from database.config import get_connection_string
from deal_selector import DealSelector

selector = DealSelector(get_connection_string())
deals = selector.select_daily_deals_with_scoring(
    min_quality_score=75,  # Only great+ deals
    max_price=800
)

for deal in deals[:10]:
    q = deal['quality']
    print(f\"{deal['origin']} → {deal['destination']}: ${deal['price']} (Score: {q['score']:.1f})\")
"
```

## Automation Setup

### Option 1: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add these lines:
# Run scraper daily at 6 AM
0 6 * * * cd /path/to/Explorer\ Scraper && docker run ... test_100_origins_v2.py >> /tmp/scrape.log 2>&1

# Calculate insights at 8 AM (after scrape completes)
0 8 * * * cd /path/to/Explorer\ Scraper && python3 scripts/calculate_price_insights.py >> /tmp/insights.log 2>&1

# Send email at 9 AM (after insights calculated)
0 9 * * * cd /path/to/Explorer\ Scraper && python3 send_daily_deals.py >> /tmp/email.log 2>&1
```

### Option 2: systemd Timer (Linux)

Create `/etc/systemd/system/flight-insights.service`:
```ini
[Unit]
Description=Calculate Flight Price Insights
After=network.target

[Service]
Type=oneshot
User=yourusername
WorkingDirectory=/path/to/Explorer Scraper
ExecStart=/usr/bin/python3 scripts/calculate_price_insights.py
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/flight-insights.timer`:
```ini
[Unit]
Description=Daily Flight Price Insights Calculation

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable flight-insights.timer
sudo systemctl start flight-insights.timer
```

### Option 3: Python Script with Schedule

```python
import schedule
import time
import subprocess

def run_scraper():
    subprocess.run(["docker", "run", "..."])

def calculate_insights():
    subprocess.run(["python3", "scripts/calculate_price_insights.py"])

def send_emails():
    subprocess.run(["python3", "send_daily_deals.py"])

schedule.every().day.at("06:00").do(run_scraper)
schedule.every().day.at("08:00").do(calculate_insights)
schedule.every().day.at("09:00").do(send_emails)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Testing & Validation

### Test Insights Calculation
```bash
# Verbose output with statistics
python scripts/calculate_price_insights.py --verbose

# Check results
psql -h localhost -U lukeward -d flight_deals -c "
SELECT 
    data_quality,
    COUNT(*) as routes,
    AVG(sample_size)::INT as avg_samples
FROM route_price_insights
GROUP BY data_quality
ORDER BY data_quality;
"
```

### Test Quality Scoring
```bash
# Run test script
python test_price_insights_scoring.py

# Check top deals
python -c "
from database.config import get_connection_string
from deal_selector import DealSelector

selector = DealSelector(get_connection_string())
deals = selector.select_daily_deals_with_scoring(min_quality_score=90)

print(f'Found {len(deals)} excellent deals')
for deal in deals[:5]:
    q = deal['quality']
    print(f\"{deal['origin']} → {deal['destination']}: ${deal['price']} ({q['insight']})\")
"
```

### Verify Data Quality
```bash
# Check routes with low confidence
psql -h localhost -U lukeward -d flight_deals -c "
SELECT origin, destination, sample_size, data_quality
FROM route_price_insights
WHERE data_quality = 'low'
ORDER BY sample_size DESC
LIMIT 10;
"
```

## Monitoring & Maintenance

### Daily Checks
1. **Insights calculation succeeded:**
   ```bash
   tail -20 /tmp/insights.log
   ```

2. **Number of routes tracked:**
   ```bash
   psql -h localhost -U lukeward -d flight_deals -c "SELECT COUNT(*) FROM route_price_insights;"
   ```

3. **Data quality distribution:**
   ```bash
   python scripts/calculate_price_insights.py --verbose | grep "Summary"
   ```

### Weekly Maintenance
1. **Check for stale insights:**
   ```sql
   SELECT COUNT(*) 
   FROM route_price_insights 
   WHERE last_updated < NOW() - INTERVAL '7 days';
   ```

2. **Identify routes needing more data:**
   ```sql
   SELECT origin, destination, sample_size, days_tracked
   FROM route_price_insights
   WHERE data_quality = 'low'
   ORDER BY sample_size ASC
   LIMIT 20;
   ```

### Monthly Analysis
1. **Price trends:**
   ```sql
   -- Routes getting cheaper
   SELECT origin, destination, typical_price, min_price_seen,
          (typical_price - min_price_seen) as potential_savings
   FROM route_price_insights
   WHERE typical_price > min_price_seen * 1.2  -- 20%+ savings possible
   ORDER BY potential_savings DESC
   LIMIT 20;
   ```

2. **Best value routes:**
   ```sql
   SELECT origin, destination, typical_price, sample_size
   FROM route_price_insights
   WHERE typical_price < 400  -- Cheap routes
     AND data_quality = 'high'  -- High confidence
   ORDER BY typical_price ASC
   LIMIT 20;
   ```

## Troubleshooting

### Issue: No insights calculated
**Cause:** Not enough historical data (< 7 samples per route)  
**Solution:** Wait for more scrapes, or lower `--min-samples` threshold

### Issue: All deals show "unknown" quality
**Cause:** Insights table empty or not calculated  
**Solution:** Run `python scripts/calculate_price_insights.py --verbose`

### Issue: Insights seem incorrect
**Cause:** Outliers in data or insufficient samples  
**Solution:** Check data quality, increase `--min-samples`, or manually inspect route

### Issue: Calculation script fails
**Cause:** Database connection issue  
**Solution:** Check `.env` file, verify PostgreSQL is running

## Future Enhancements

### Phase 1 (Current) ✅
- [x] Basic statistical insights (median, percentiles)
- [x] Quality scoring system
- [x] Data quality indicators
- [x] Daily calculation script

### Phase 2 (Next 2-4 weeks)
- [ ] Seasonal pattern detection
- [ ] Price trend analysis (getting cheaper/expensive)
- [ ] Price drop alerts (>20% drop from recent average)
- [ ] Email templates with quality badges

### Phase 3 (Month 2+)
- [ ] Machine learning price predictions
- [ ] Optimal booking time recommendations
- [ ] Route popularity scoring
- [ ] Personalized deal recommendations

## API Reference

### `DealSelector.select_daily_deals_with_scoring()`

```python
selector = DealSelector(connection_string)
deals = selector.select_daily_deals_with_scoring(
    origins=['DFW', 'ATL'],      # Optional: filter by origins
    max_price=800,                # Maximum price threshold
    min_quality_score=70,         # Only deals scoring >= 70
    dedup_days=21,                # Don't repeat same route within 21 days
    limit_per_origin=10           # Max deals per origin
)

# Returns list of deals sorted by quality score:
# [
#   {
#     'origin': 'DFW',
#     'destination': 'BCN',
#     'price': 450,
#     'quality': {
#       'score': 92.5,
#       'quality': 'great',
#       'insight': '32% below typical price',
#       'confidence': 'high',
#       'typical_price': 660,
#       'discount_pct': 31.8
#     },
#     ... other fields ...
#   }
# ]
```

### `calculate_price_insights()`

```python
from scripts.calculate_price_insights import calculate_insights

rows_updated = calculate_insights(
    min_samples=7,       # Minimum data points required
    lookback_days=90,    # Days of history to analyze
    verbose=True         # Print statistics
)
```

## Support

For issues or questions:
1. Check logs: `/tmp/insights.log`
2. Verify database: `psql -h localhost -U lukeward -d flight_deals`
3. Test manually: `python scripts/calculate_price_insights.py --verbose`
4. Review this guide: `PRICE_INSIGHTS_GUIDE.md`

