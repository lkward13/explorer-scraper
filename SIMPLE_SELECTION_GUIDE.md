# Simple Price-Based Deal Selection

## Overview

The system now uses **simple regional price thresholds** instead of historical data scoring. This works immediately without needing 2-3 weeks of data collection.

## How It Works

Instead of comparing to historical prices, we use industry-standard "good deal" thresholds:

```python
REGION_THRESHOLDS = {
    'caribbean': 350,           # MBJ, SJU, GCM, AUA, etc.
    'central_america': 350,     # SJO, SAL, PTY, etc.
    'south_america': 600,       # BOG, LIM, GRU, etc.
    'europe': 600,              # BCN, LHR, CDG, DUB, etc.
    'middle_east': 850,         # DXB, DOH, TLV, etc.
    'africa': 850,              # CPT, JNB, NBO, etc.
    'asia': 850,                # NRT, BKK, HKG, SIN, etc.
    'oceania': 950,             # SYD, AKL, etc.
    'pacific': 950,             # PPT, NAN, etc.
}
```

### Selection Logic

1. Get all deals from last 48 hours
2. Filter by regional threshold (e.g., Europe < $600)
3. Exclude routes sent in last 7 days (cooldown)
4. Sort by price (cheapest first)
5. Return top N deals

## Usage

### Send Test Email

```bash
# Send 30 deals
python3 send_test_email.py --num-deals 30

# Preview without sending
python3 send_test_email.py --num-deals 30 --dry-run
```

### In Your Code

```python
from deal_selector import DealSelector
from database.config import get_connection_string

selector = DealSelector(get_connection_string())

# Get deals using simple thresholds
deals = selector.select_deals_simple(
    origins=['OKC', 'DFW'],  # Optional: specific origins
    cooldown_days=7,          # Don't repeat routes within 7 days
    limit=50                  # Max deals to return
)

# Send email...
# Then mark as sent
selector.mark_deals_as_sent(deals, recipient_email="user@example.com")
selector.close()
```

## Advantages

✅ **Works immediately** - No historical data needed
✅ **Simple & reliable** - Based on industry knowledge
✅ **Transparent** - Clear thresholds, easy to understand
✅ **Adjustable** - Change thresholds anytime

## When to Switch to Quality Scoring

After **14-21 days** of daily scrapes:
- You'll have reliable historical data
- Can switch to `select_deals_with_cooldown()` (quality scoring)
- More sophisticated: compares to route-specific history
- Better for finding truly exceptional deals

## Current Thresholds Explained

### Caribbean ($350)
- Short flights (2-4 hours)
- Competitive market
- $350 = good deal, $250 = great deal

### Europe ($600)
- Transatlantic flights (7-9 hours)
- Major hubs (LHR, CDG, BCN)
- $600 = good deal, $400 = great deal

### Asia ($850)
- Long-haul (12-16 hours)
- Premium market
- $850 = good deal, $600 = great deal

### Pacific ($950)
- Ultra long-haul (15+ hours)
- Limited competition
- $950 = good deal, $700 = great deal

## Adjusting Thresholds

Edit `deal_selector.py`:

```python
REGION_THRESHOLDS = {
    'caribbean': 300,  # More selective (only cheaper deals)
    'europe': 700,     # Less selective (more deals qualify)
    # ...
}
```

Or override in code:

```python
deals = selector.select_deals_simple(
    max_price_override=500  # Ignore regions, use $500 for everything
)
```

## Cooldown System

The cooldown prevents sending the same route too frequently:

```python
# 7-day cooldown (default)
deals = selector.select_deals_simple(cooldown_days=7)

# 14-day cooldown (less frequent)
deals = selector.select_deals_simple(cooldown_days=14)

# No cooldown (for testing)
deals = selector.select_deals_simple(cooldown_days=0)
```

Cooldown is tracked in the `sent_deals` table:
- Records every route sent
- Tracks when it was sent
- Automatically filters out recently sent routes

## Daily Pipeline

```bash
# 1. Run daily scrape (2-4 hours)
./run_100_origins.sh

# 2. Send email with simple selection
python3 send_test_email.py --num-deals 50

# That's it! No need to calculate price insights yet.
```

## Transition Plan

**Weeks 1-2:** Use simple selection (current system)
- Build historical database
- Send emails with simple thresholds
- Monitor which deals perform well

**Week 3+:** Switch to quality scoring
- Run: `python3 scripts/calculate_price_insights.py`
- Update email script to use `select_deals_with_cooldown()`
- More sophisticated deal detection

## Tips

1. **Start conservative**: Use lower thresholds to send only great deals
2. **Monitor volume**: Track how many deals meet criteria each day
3. **Adjust seasonally**: Lower thresholds in slow seasons, raise in peak
4. **Test different values**: A/B test thresholds to find sweet spot
5. **Track clicks**: See which price points get most engagement

## Example: Production Email Script

```python
#!/usr/bin/env python3
from deal_selector import DealSelector
from email_builder import EmailBuilder
from send_daily_deals import EmailSender
from database.config import get_connection_string
import os

# Configuration
MIN_DEALS_TO_SEND = 20  # Only send if we have 20+ deals
MAX_DEALS = 50          # Max deals per email
COOLDOWN_DAYS = 7       # 1 week between same route

# Select deals
selector = DealSelector(get_connection_string())
deals = selector.select_deals_simple(
    cooldown_days=COOLDOWN_DAYS,
    limit=MAX_DEALS
)

# Check if we have enough
if len(deals) < MIN_DEALS_TO_SEND:
    print(f"Only {len(deals)} deals found, need {MIN_DEALS_TO_SEND}. Skipping email today.")
    selector.close()
    exit(0)

# Build email
builder = EmailBuilder()
email = builder.build_digest_email(deals, "Today's Top Flight Deals")

# Send email
sender = EmailSender(
    os.getenv('SMTP_HOST'),
    int(os.getenv('SMTP_PORT')),
    os.getenv('SMTP_USER'),
    os.getenv('SMTP_PASS')
)
sender.send_email(
    to=os.getenv('RECIPIENT_EMAIL'),
    subject=email['subject'],
    html=email['html'],
    text=email['text'],
    from_email=os.getenv('SMTP_USER')
)

# Mark as sent
selector.mark_deals_as_sent(deals, recipient_email=os.getenv('RECIPIENT_EMAIL'))
selector.close()

print(f"✅ Sent {len(deals)} deals")
```


