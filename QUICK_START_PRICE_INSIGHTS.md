# Quick Start: Price Insights System

## TL;DR

Your flight scraper now has **built-in price intelligence**. It analyzes historical data to score deal quality (0-100) and identify truly exceptional deals.

## Daily Usage (3 Commands)

```bash
# 1. Run scraper (as usual)
docker run ... test_100_origins_v2.py

# 2. Calculate insights (NEW - run after scrape)
python scripts/calculate_price_insights.py

# 3. Get best deals (NEW - with quality scores)
python test_price_insights_scoring.py
```

## Current Stats

- ✅ **2,403 routes** with price insights
- ✅ **2,202 routes** with high confidence (30+ samples)
- ✅ **490 deals** scored as "excellent" (best price ever)
- ✅ **86%** of deals have high confidence scores

## What Changed

### Before (Still Works)
```python
from deal_selector import DealSelector

selector = DealSelector(conn_string)
deals = selector.select_daily_deals()  # Old method
```

### After (New & Improved)
```python
from deal_selector import DealSelector

selector = DealSelector(conn_string)
deals = selector.select_daily_deals_with_scoring(
    min_quality_score=75  # Only great+ deals
)

# Each deal now has quality info:
for deal in deals[:5]:
    print(f"{deal['origin']} → {deal['destination']}: ${deal['price']}")
    print(f"Quality: {deal['quality']['quality']} (Score: {deal['quality']['score']})")
    print(f"Insight: {deal['quality']['insight']}")
```

## Quality Levels

| Badge | Score | Meaning |
|-------|-------|---------|
| 🏆 **Excellent** | 90-100 | Best price ever or near-record low |
| ⭐ **Great** | 75-89 | Significantly below typical |
| ✅ **Good** | 60-74 | Below typical price |
| 📊 **Fair** | 40-59 | Around typical price |

## Confidence Levels

| Icon | Level | Samples | Reliability |
|------|-------|---------|-------------|
| 🟢 | High | 30+ | Very reliable |
| 🟡 | Medium | 14-29 | Reliable |
| 🔴 | Low | 7-13 | Less reliable |

## Example Output

```
🏆 EXCELLENT | Score: 100.0 | 🟢 high confidence
DFW → Barcelona: $430
Best price ever! 10% below typical
Typical: $480 | This deal: $430
```

## Automation (Cron)

```bash
# Add to crontab (crontab -e)
0 6 * * * cd /path/to/Explorer\ Scraper && docker run ... >> /tmp/scrape.log 2>&1
0 8 * * * cd /path/to/Explorer\ Scraper && python3 scripts/calculate_price_insights.py >> /tmp/insights.log 2>&1
```

## Quick Checks

```bash
# How many routes tracked?
psql -h localhost -U lukeward -d flight_deals -c "SELECT COUNT(*) FROM route_price_insights;"

# Show top deals
python test_price_insights_scoring.py | head -30

# Recalculate insights
python scripts/calculate_price_insights.py --verbose
```

## Files to Know

| File | Purpose |
|------|---------|
| `scripts/calculate_price_insights.py` | Calculate insights from historical data |
| `test_price_insights_scoring.py` | Test script showing top deals |
| `PRICE_INSIGHTS_GUIDE.md` | Full documentation |
| `IMPLEMENTATION_COMPLETE.md` | Implementation summary |

## Need Help?

1. **Check logs:** `tail -20 /tmp/insights.log`
2. **Verify data:** `python scripts/calculate_price_insights.py --verbose`
3. **Read docs:** `PRICE_INSIGHTS_GUIDE.md`
4. **Test scoring:** `python test_price_insights_scoring.py`

## What's Next?

After 2-4 weeks of daily scraping:
- More routes with high confidence
- Better seasonal pattern detection
- Price trend analysis
- Automated email alerts

---

**Status:** ✅ Ready to use  
**Backwards Compatible:** ✅ Yes (old methods still work)  
**Production Ready:** ✅ Yes

