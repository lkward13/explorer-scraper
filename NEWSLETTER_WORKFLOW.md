# Email Newsletter Workflow

## Overview

This document describes how to use the flight deal scraper to generate and send weekly email newsletters.

## Workflow Steps

### 1. Find Deals (Weekly)

Run the deal finder for each origin airport you're tracking:

```bash
# Find deals from Phoenix
python scripts/find_and_expand_deals.py \
  --origin PHX \
  --min-similar-deals 5 \
  --limit 20 \
  --out deals/phx_$(date +%Y%m%d).json \
  --verbose

# Find deals from Dallas
python scripts/find_and_expand_deals.py \
  --origin DFW \
  --min-similar-deals 5 \
  --limit 20 \
  --out deals/dfw_$(date +%Y%m%d).json \
  --verbose
```

**Parameters:**
- `--min-similar-deals 5`: Only include deals with 5+ flexible date options
- `--limit 20`: Expand top 20 cheapest deals (filters to ~5-10 flexible deals)
- `--out`: Save results to dated JSON file

### 2. Generate Newsletter HTML

Convert the deals JSON to an HTML email:

```bash
python scripts/generate_newsletter.py \
  --deals deals/phx_20241117.json \
  --origin PHX \
  --origin-name "Phoenix" \
  --out newsletters/phx_20241117.html
```

### 3. Review Newsletter

Open the HTML file in a browser to preview:

```bash
open newsletters/phx_20241117.html
```

Check:
- ✅ All deals have complete flight details
- ✅ Prices look reasonable
- ✅ Flexible date counts are accurate
- ✅ Links work correctly

### 4. Send via Email Service

Use your email service provider's API to send the newsletter:

#### Option A: Mailchimp

```python
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

client = MailchimpMarketing.Client()
client.set_config({
    "api_key": "YOUR_API_KEY",
    "server": "us1"
})

# Read newsletter HTML
with open("newsletters/phx_20241117.html") as f:
    html_content = f.read()

# Create campaign
campaign = client.campaigns.create({
    "type": "regular",
    "recipients": {"list_id": "YOUR_LIST_ID"},
    "settings": {
        "subject_line": "✈️ This Week's Best Flight Deals from Phoenix",
        "from_name": "Flight Deals",
        "reply_to": "deals@example.com"
    }
})

# Set content
client.campaigns.set_content(campaign["id"], {
    "html": html_content
})

# Send
client.campaigns.send(campaign["id"])
```

#### Option B: SendGrid

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Read newsletter HTML
with open("newsletters/phx_20241117.html") as f:
    html_content = f.read()

message = Mail(
    from_email='deals@example.com',
    to_emails='subscriber@example.com',
    subject='✈️ This Week's Best Flight Deals from Phoenix',
    html_content=html_content
)

sg = SendGridAPIClient('YOUR_API_KEY')
response = sg.send(message)
```

#### Option C: AWS SES

```python
import boto3

ses = boto3.client('ses', region_name='us-east-1')

# Read newsletter HTML
with open("newsletters/phx_20241117.html") as f:
    html_content = f.read()

response = ses.send_email(
    Source='deals@example.com',
    Destination={'ToAddresses': ['subscriber@example.com']},
    Message={
        'Subject': {'Data': '✈️ This Week's Best Flight Deals from Phoenix'},
        'Body': {'Html': {'Data': html_content}}
    }
)
```

## Newsletter Content Strategy

### What to Include

**Always Include:**
- ✅ Deals with 5+ flexible date options
- ✅ Complete flight details (airline, times, stops)
- ✅ Price range for flexibility
- ✅ Direct link to Google Flights

**Optionally Include:**
- 💰 Deal quality ("$X cheaper than usual") when available
- 🌍 Mix of domestic and international destinations
- 🎯 Highlight "best value" deals (high savings + flexibility)

### What to Exclude

**Never Include:**
- ❌ Deals with <5 flexible dates (not truly flexible)
- ❌ Deals without complete flight details
- ❌ Duplicate destinations (keep cheapest only)
- ❌ Recently sent deals (within 35 days)

### Frequency Recommendations

**Weekly Newsletter:**
- Send: Every Monday morning (8 AM local time)
- Content: Top 5-10 flexible deals from that origin
- Lookout: 6 months ahead

**Daily Digest (Optional):**
- Send: Every morning
- Content: Top 3 "hot deals" (high savings + flexibility)
- Lookout: 3 months ahead

## Tracking Used Deals

To avoid sending the same deals repeatedly:

```bash
# Track used deals
python scripts/find_and_expand_deals.py \
  --origin PHX \
  --min-similar-deals 5 \
  --used-deals-file data/used_deals.json \
  --out deals/phx_$(date +%Y%m%d).json
```

The `used_deals.json` file tracks:
- Destination + date range
- Last sent date
- 35-day cooldown period

## Automation with Cron

Add to crontab for weekly automation:

```bash
# Run every Monday at 6 AM
0 6 * * 1 cd /path/to/explorer-scraper && python scripts/find_and_expand_deals.py --origin PHX --min-similar-deals 5 --out deals/phx_$(date +\%Y\%m\%d).json

# Generate newsletter at 7 AM
0 7 * * 1 cd /path/to/explorer-scraper && python scripts/generate_newsletter.py --deals deals/phx_$(date +\%Y\%m\%d).json --origin PHX --origin-name "Phoenix" --out newsletters/phx_$(date +\%Y\%m\%d).html

# Send newsletter at 8 AM (custom script)
0 8 * * 1 cd /path/to/explorer-scraper && python scripts/send_newsletter.py --html newsletters/phx_$(date +\%Y\%m\%d).html
```

## Multi-Origin Setup

For tracking multiple cities:

```bash
#!/bin/bash
# weekly_deals.sh

ORIGINS=("PHX:Phoenix" "DFW:Dallas" "LAX:Los Angeles" "ORD:Chicago" "JFK:New York")
DATE=$(date +%Y%m%d)

for origin_pair in "${ORIGINS[@]}"; do
    IFS=':' read -r code name <<< "$origin_pair"
    
    echo "Processing $name ($code)..."
    
    # Find deals
    python scripts/find_and_expand_deals.py \
        --origin $code \
        --min-similar-deals 5 \
        --limit 20 \
        --out deals/${code}_${DATE}.json \
        --used-deals-file data/used_deals_${code}.json
    
    # Generate newsletter
    python scripts/generate_newsletter.py \
        --deals deals/${code}_${DATE}.json \
        --origin $code \
        --origin-name "$name" \
        --out newsletters/${code}_${DATE}.html
    
    echo "✅ $name newsletter ready"
done
```

## Email Service Recommendations

| Service | Pros | Cons | Best For |
|---------|------|------|----------|
| **Mailchimp** | Easy to use, good templates, analytics | Expensive at scale | Small lists (<2k) |
| **SendGrid** | Reliable, good deliverability | More technical | Medium lists (2k-50k) |
| **AWS SES** | Very cheap, scalable | Requires AWS setup | Large lists (50k+) |
| **Postmark** | Best deliverability | More expensive | High-value subscribers |

## Metrics to Track

**Engagement:**
- Open rate (target: >25%)
- Click-through rate (target: >5%)
- Unsubscribe rate (target: <0.5%)

**Deal Quality:**
- Average savings per deal
- Average flexibility (similar dates)
- Conversion rate (clicks → bookings)

**Operational:**
- Scraping success rate
- Deals found per origin
- Processing time

## Legal Requirements

**CAN-SPAM Compliance:**
- ✅ Include physical address
- ✅ Clear unsubscribe link
- ✅ Honor opt-outs within 10 days
- ✅ Accurate "From" name and subject

**GDPR Compliance (if EU subscribers):**
- ✅ Get explicit consent
- ✅ Allow data export
- ✅ Allow data deletion
- ✅ Privacy policy link

## Example Newsletter Schedule

**Monday Morning (8 AM):**
- Subject: "✈️ This Week's Best Flight Deals from Phoenix"
- Content: 5-10 flexible deals
- Focus: Mix of domestic + international

**Thursday Afternoon (2 PM):**
- Subject: "🔥 Weekend Flash Deals from Phoenix"
- Content: 3-5 short-haul deals
- Focus: Quick weekend getaways

## Troubleshooting

**No deals found:**
- Lower `--min-similar-deals` to 3
- Increase `--limit` to 30
- Check if region collection is working

**Missing flight details:**
- Flight details extraction may have failed
- Check logs for errors
- Manually verify on Google Flights

**High unsubscribe rate:**
- Reduce frequency
- Improve deal quality (higher savings)
- Better targeting (region preferences)

## Future Enhancements

- [ ] Personalized newsletters (subscriber preferences)
- [ ] Price alerts (specific destinations)
- [ ] Mobile app notifications
- [ ] SMS alerts for hot deals
- [ ] Social media posting
- [ ] Deal history tracking
- [ ] A/B testing subject lines

