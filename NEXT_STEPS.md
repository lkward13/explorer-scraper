# Next Steps - Flight Deal Finder

## Current Status ✅

### Working Features
1. **Explore Scraper** - Finds 60+ cheap destinations from any origin
2. **Date Expander** - Expands each deal to find 300+ date combinations across 10+ months
3. **Combined Script** - Automates full workflow with flexibility filtering
4. **City→IATA Mapping** - 100+ cities mapped for automatic expansion
5. **Regional Search Support** - `--region` flag exists (Europe, Asia, etc.)

### Git Checkpoints
- `v1.0-working-separate-scripts` - Individual scripts working
- `v1.1-combined-script` - Combined automation working

---

## Immediate Enhancements Needed

### 1. Multi-Region Search Workflow ⚠️ IN PROGRESS

**Problem:** Explore shows deals based on map viewport. Need to search multiple regions for variety.

**Solution:** Use `--region` flag with pre-collected TFS parameters.

**Status:**
- ✅ `--region` flag exists in Explore scraper
- ✅ `scripts/collect_regions.py` exists for collecting region TFS
- ⚠️ Only LAX regions collected so far
- ❌ Combined script doesn't use regions yet

**Action Items:**
```bash
# 1. Collect regions for key origins (one-time setup)
python scripts/collect_all_regions.py --origins DFW,LAX,JFK,ORD,ATL

# 2. Update combined script to loop through regions
# - Search "anywhere" first
# - Then search each region: Europe, Asia, Africa, South America, Oceania, Caribbean, Middle East
# - Combine all results

# 3. Test workflow
python scripts/find_and_expand_deals.py \
  --origin DFW \
  --regions Europe,Asia,Caribbean \
  --min-similar-deals 5
```

**Code Changes Needed:**
- [ ] Update `find_and_expand_deals.py` to accept `--regions` argument
- [ ] Loop through each region and call `explore_run()` with `region=` parameter
- [ ] Combine results from all regions
- [ ] De-duplicate destinations across regions

---

### 2. Used Deals Tracking 📝 TODO

**Problem:** Need to avoid showing the same deals repeatedly in newsletter/site.

**Solution:** Track used deals in a JSON file with timestamps.

**Data Structure:**
```json
{
  "used_deals": [
    {
      "origin": "DFW",
      "destination": "LHR",
      "destination_iata": "LHR",
      "price": 450,
      "dates": ["2025-12-10", "2025-12-18"],
      "used_date": "2025-11-15",
      "newsletter_id": "2025-11-15-weekly"
    }
  ]
}
```

**Logic:**
- Before expanding a deal, check if `(origin, destination_iata)` was used in last N days (e.g., 60 days)
- Skip deals used recently
- After publishing, add deal to used_deals.json

**Code Changes Needed:**
- [ ] Create `data/used_deals.json` structure
- [ ] Add `load_used_deals()` function
- [ ] Add `is_deal_recently_used()` check (60-day window)
- [ ] Add `mark_deal_as_used()` function
- [ ] Add `--used-deals-file` argument to combined script
- [ ] Filter deals before expansion

---

### 3. Budget Airline Handling ✈️ TODO

**Problem:** Budget airlines (Spirit, Frontier, Allegiant, etc.) may have hidden fees. Need to flag or filter them.

**Solution:** Detect budget airlines and either:
- Option A: Skip them entirely
- Option B: Flag them and include a non-budget alternative
- Option C: Only include if deal is exceptional (>30% cheaper)

**Budget Airlines List:**
- Spirit Airlines
- Frontier Airlines
- Allegiant Air
- Sun Country
- Avelo Airlines
- Breeze Airways

**Note:** Explore scraper doesn't currently extract airline info. Need to either:
1. Extract airline from Explore HTML (if available)
2. Get airline from Google Flights during expansion
3. Use a heuristic (very low domestic prices = likely budget)

**Code Changes Needed:**
- [ ] Research if airline info is in Explore HTML
- [ ] If not, extract during date expansion from Google Flights
- [ ] Add budget airline detection
- [ ] Add `--allow-budget` / `--budget-threshold` flags
- [ ] Filter or flag budget deals

---

### 4. Flexibility Requirements ✅ DONE

**Current:** `min_similar_deals` parameter (default: 5)

**User Preference:** At least 5 similar dates required

**Status:** ✅ Already implemented and working

---

## Recommended Implementation Order

### Phase 1: Multi-Region Support (Next)
1. Create `scripts/collect_all_regions.py` ✅ DONE
2. Collect regions for top 5-10 US airports
3. Update `find_and_expand_deals.py` to loop through regions
4. Test with DFW → [Europe, Asia, Caribbean]
5. Commit: "Add multi-region search support"

### Phase 2: Used Deals Tracking
1. Design `used_deals.json` structure
2. Implement load/save/check functions
3. Add 60-day recency filter
4. Test tracking workflow
5. Commit: "Add used deals tracking"

### Phase 3: Budget Airline Detection
1. Research airline data availability
2. Implement detection logic
3. Add filtering options
4. Test with Spirit/Frontier routes
5. Commit: "Add budget airline detection"

### Phase 4: Production Pipeline
1. Create `scripts/generate_newsletter_deals.py`
2. Combine all filters and logic
3. Output formatted for newsletter/site
4. Add scheduling/automation
5. Commit: "Add production deal generation"

---

## Testing Plan

### Test Case 1: Multi-Region Search
```bash
# Collect regions for DFW (one-time)
python scripts/collect_regions.py --origin DFW

# Run multi-region search
python scripts/find_and_expand_deals.py \
  --origin DFW \
  --regions Europe,Asia,Caribbean \
  --min-similar-deals 5 \
  --limit 20 \
  --out dfw_multi_region.json

# Expected: Mix of domestic + international deals
# Should have deals to Europe, Asia, Caribbean
```

### Test Case 2: Used Deals Filter
```bash
# First run - no filters
python scripts/find_and_expand_deals.py --origin DFW --out run1.json

# Mark some deals as used
python scripts/mark_deals_used.py --input run1.json --deals 0,1,2

# Second run - should skip marked deals
python scripts/find_and_expand_deals.py \
  --origin DFW \
  --used-deals-file data/used_deals.json \
  --out run2.json

# Expected: run2.json should not include deals 0,1,2 from run1.json
```

### Test Case 3: Budget Airline Filter
```bash
# Allow budget airlines
python scripts/find_and_expand_deals.py \
  --origin DFW \
  --allow-budget \
  --out with_budget.json

# Exclude budget airlines
python scripts/find_and_expand_deals.py \
  --origin DFW \
  --no-budget \
  --out no_budget.json

# Compare: no_budget.json should have fewer/different deals
```

---

## Questions for Discussion

1. **Region Priority:** Should we search all regions every time, or rotate through them?
   - Option A: All regions, every run (more deals, longer runtime)
   - Option B: Rotate regions weekly (faster, ensures variety over time)

2. **Used Deals Window:** How long before we can reuse a destination?
   - Suggested: 60 days
   - Alternative: 90 days, or based on newsletter frequency

3. **Budget Airlines:** What's the threshold for "insanely cheap"?
   - Suggested: >30% cheaper than non-budget alternative
   - Or: Absolute price < $50 domestic, < $300 international

4. **Deal Volume:** How many deals do you want per newsletter/post?
   - This affects `--limit` parameter
   - Suggested: 10-20 deals per publication

5. **Origins:** Should we rotate origins, or always use same ones?
   - Option A: Fixed list (DFW, LAX, JFK, ORD, ATL)
   - Option B: Rotate through top 20-50 US airports
   - Option C: Let users filter by their home airport on site

---

## Files to Create/Modify

### New Files Needed:
- [ ] `scripts/collect_all_regions.py` ✅ CREATED
- [ ] `scripts/mark_deals_used.py`
- [ ] `scripts/generate_newsletter_deals.py`
- [ ] `data/used_deals.json`
- [ ] `data/budget_airlines.json`

### Files to Modify:
- [ ] `scripts/find_and_expand_deals.py` - Add regions, used deals, budget filter
- [ ] `README.md` - Document new features
- [ ] `NEXT_STEPS.md` - Update as features complete

---

## Current Limitations to Address

1. **Airline Info:** Explore doesn't show airline, may need to get from Flights expansion
2. **Layover Info:** Not currently extracted, may need for quality filtering
3. **Non-stop Preference:** Some users may want non-stop only
4. **Seasonal Deals:** No seasonal awareness yet (e.g., summer Europe, winter Caribbean)
5. **Price History:** No tracking of whether price is historically good
6. **Availability:** No check if seats are actually bookable at that price

---

## Long-term Enhancements (Future)

- **Database:** Move from JSON files to proper database (SQLite/Postgres)
- **Web Scraping Schedule:** Cron job to run daily/weekly
- **API:** REST API for deal queries
- **Web UI:** Browse deals by origin, destination, date flexibility
- **Price Alerts:** Email when specific routes drop below threshold
- **Historical Analysis:** Track price trends over time
- **ML Price Prediction:** Predict if price will go up/down
- **Multi-origin:** Find deals from any of user's nearby airports

---

## Ready to Implement

**Next immediate task:** Multi-region support

Let me know if you want to proceed with Phase 1, or if you'd like to discuss any of the questions above first!

