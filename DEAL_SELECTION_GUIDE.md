# Deal Selection & Email System Guide

## Overview

The system now has smart deal selection with cooldown tracking to prevent sending duplicate deals too frequently.

## Key Features

### 1. **Simplified Email Format**
- Clean, mobile-friendly design
- Shows: Destination, Price, Book button
- Removed: Quality labels, confidence scores, "best price ever" messaging
- Grouped by origin airport

### 2. **Quality Scoring (Behind the Scenes)**
- Every deal gets a 0-100 quality score based on historical price data
- Only deals scoring ≥70 are considered
- Scoring factors:
  - How price compares to historical median
  - How price compares to historical best
  - Data confidence (sample size)

### 3. **Cooldown System**
- Tracks which routes have been sent in `sent_deals` table
- Prevents sending the same route within X days (default: 7 days)
- Example: If you send OKC→BCN today, it won't appear again for 7 days

### 4. **Deal Selection Logic**

```python
# Basic selection (with quality scoring)
deals = selector.select_daily_deals_with_scoring(
    origins=['OKC', 'DFW'],
    max_price=600,
    min_quality_score=70,
    limit_per_origin=10
)

# With cooldown (prevents duplicates)
deals = selector.select_deals_with_cooldown(
    origins=['OKC', 'DFW'],
    max_price=600,
    min_quality_score=70,
    cooldown_days=7,  # Don't send same route within 7 days
    limit=50          # Max total deals to return
)
```

## Database Tables

### `sent_deals`
Tracks every deal that's been sent:
- `origin`, `destination` - Route
- `price`, `outbound_date`, `return_date` - Deal details
- `sent_at` - When it was sent
- `recipient_email` - Who received it

### `route_price_insights`
Historical price statistics for each route:
- `typical_price` - Median price
- `low_price_threshold` - 25th percentile (good deal)
- `min_price_seen` - Best price ever
- `sample_size` - How many data points
- `data_quality` - high/medium/low confidence

## Workflow

### Daily Pipeline

1. **Scrape** (100 origins, ~2-4 hours)
   ```bash
   ./run_100_origins.sh
   ```

2. **Calculate Insights** (updates price statistics)
   ```bash
   python3 scripts/calculate_price_insights.py --verbose
   ```

3. **Select Deals** (with cooldown)
   ```python
   selector = DealSelector(conn_string)
   deals = selector.select_deals_with_cooldown(
       min_quality_score=70,
       cooldown_days=7,
       limit=50
   )
   ```

4. **Send Email**
   ```python
   builder = EmailBuilder()
   email = builder.build_digest_email(deals, "Today's Flight Deals")
   # ... send via SMTP ...
   ```

5. **Mark as Sent** (prevents duplicates)
   ```python
   selector.mark_deals_as_sent(deals, recipient_email="user@example.com")
   ```

## Controlling Email Frequency

### Option 1: Minimum Quality Threshold
Only send deals scoring ≥ X:
```python
deals = selector.select_deals_with_cooldown(
    min_quality_score=80,  # Only excellent deals
    limit=50
)
```

If no deals meet the threshold, **don't send an email that day**.

### Option 2: Minimum Deal Count
Only send if you have at least X good deals:
```python
deals = selector.select_deals_with_cooldown(
    min_quality_score=70,
    limit=50
)

if len(deals) >= 10:  # Only send if we have 10+ deals
    # Send email
    selector.mark_deals_as_sent(deals)
else:
    print("Not enough deals today, skipping email")
```

### Option 3: Cooldown Period
Increase cooldown to reduce frequency:
```python
deals = selector.select_deals_with_cooldown(
    cooldown_days=14,  # Wait 2 weeks before sending same route again
    limit=50
)
```

## Example: Smart Daily Email Script

```python
#!/usr/bin/env python3
from deal_selector import DealSelector
from email_builder import EmailBuilder
from database.config import get_connection_string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
MIN_QUALITY_SCORE = 75      # Only great deals
MIN_DEALS_TO_SEND = 15      # Need at least 15 deals
COOLDOWN_DAYS = 7           # 1 week between same route
MAX_DEALS = 50              # Max deals per email

# Select deals
selector = DealSelector(get_connection_string())
deals = selector.select_deals_with_cooldown(
    min_quality_score=MIN_QUALITY_SCORE,
    cooldown_days=COOLDOWN_DAYS,
    limit=MAX_DEALS
)

# Check if we have enough deals
if len(deals) < MIN_DEALS_TO_SEND:
    print(f"Only {len(deals)} deals found, need {MIN_DEALS_TO_SEND}. Skipping email today.")
    selector.close()
    exit(0)

# Build and send email
builder = EmailBuilder()
email = builder.build_digest_email(deals, "Today's Top Flight Deals")

# ... SMTP sending code ...

# Mark as sent
selector.mark_deals_as_sent(deals, recipient_email="user@example.com")
selector.close()

print(f"✅ Sent {len(deals)} deals")
```

## Key Methods

### `DealSelector.select_deals_with_cooldown()`
Smart selection with duplicate prevention:
- Filters by quality score
- Excludes recently sent routes
- Returns top N deals

### `DealSelector.mark_deals_as_sent()`
Records deals in `sent_deals` table:
- Tracks when sent
- Tracks who received it
- Used by cooldown logic

### `DealSelector.get_recently_sent_routes()`
Returns routes sent in last N days:
- Used internally by cooldown logic
- Can be called directly to check history

## Tips

1. **Start Conservative**: Use high quality thresholds (75-80) and longer cooldowns (10-14 days)

2. **Monitor Deal Volume**: Track how many deals meet your criteria each day

3. **Adjust Seasonally**: Lower thresholds during slow travel seasons, raise during peak

4. **Per-User Preferences**: Store user preferences (origins, cooldown, quality threshold) in a users table

5. **A/B Testing**: Try different thresholds and measure click-through rates

## Next Steps

- Add user preference system (origins, cooldown period, quality threshold)
- Track email open rates and click-through rates
- Add unsubscribe functionality
- Implement per-user cooldowns (different users can get same deal)
- Add deal categories (weekend trips, long hauls, budget deals)



