# Scaling to 100 Airports: Implementation Plan

## Current Status (2025-11-17)

✅ **Core pipeline working end-to-end:**
- Multi-region search (8 regions)
- Date expansion via price graph API
- Deal quality extraction ($X cheaper than usual)
- Flight details (airline, duration, stops, times)
- Type-safe models (Pydantic)
- Newsletter-ready output

## Goal

Find and publish **3–6 high-quality deals per week** from each of **~100 US airports**.

---

## Deal Rules (Agreed Upon)

### What counts as a "valid deal"

Per route (origin → destination):

1. **Discount requirement**: ≥ **20% off** usual price
   - Computed: `discount_pct = deal_quality_amount / (reference_price + deal_quality_amount)`
   - Example: Tahiti $952 vs usual $1340 → 28.9% off ✅

2. **Flexibility requirement**: ≥ **5 similar dates** within ±10% of reference price
   - Ensures deal is actually bookable, not just one weird date

3. **No hard price caps per region**
   - Focus on % off, not absolute prices
   - A $1,132 flight that's 30% off beats a $200 flight that's 15% off

### Deal scoring

```python
score = 0.5 * (discount_pct / 0.5) + 0.5 * (flex_count / 30)
```

- Cap discount at 50% off → normalized to 1.0
- Cap flex at 30 dates → normalized to 1.0
- Equal weight to discount % and flexibility

### Featured deals (newsletter-worthy)

- ≥ **25% off**
- ≥ **10 similar dates**

### Region bundles ("Europe on sale from PHX")

- When **3+ valid deals** to the same region from one origin
- Group into a bundle for email/social

---

## Regions (8 total)

All destinations classified into:

1. **North America** – US, Canada
2. **Central America** – Mexico, Guatemala, Honduras, Costa Rica, etc.
3. **South America** – Brazil, Argentina, Chile, Colombia, Peru, etc.
4. **Caribbean** – Puerto Rico, Jamaica, Bahamas, Aruba, etc.
5. **Europe** – UK, France, Spain, Italy, Germany, etc.
6. **Africa** – South Africa, Egypt, Morocco, Kenya, etc.
7. **South East Asia** – Thailand, Vietnam, Singapore, Malaysia, etc.
8. **Oceania** – Australia, New Zealand, Tahiti, Fiji, etc.

---

## Daily Workflow (Per Origin)

### Step 1: Explore scraping (all regions)

```python
for region in ALL_REGIONS:
    cards = explore_scraper(origin=origin, region=region)
    # Returns list of destination cards with prices
```

**Per region per origin**: keep top **3 cheapest** under a safety cap (to avoid expanding 200+ routes)

Example caps (can tune):
- North America: $350
- Central America: $600
- Caribbean: $600
- South America: $700
- Europe: $750
- Africa: $850
- South East Asia: $900
- Oceania: $1100

**Result**: ~10–15 expansion candidates per origin per day

### Step 2: Expand via price graph

```python
for candidate in expansion_candidates:
    expansion = expand_dates(
        origin=candidate.origin,
        destination=candidate.destination_iata,
        reference_price=candidate.min_price,
        reference_start=candidate.start_date,
        reference_end=candidate.end_date
    )
    # Returns: similar_deals, deal_quality_amount, flight_details
```

Run in **batches of 2** (Playwright stability)

### Step 3: Filter & score

```python
for expansion in expansions:
    # Compute discount %
    discount_pct = deal_quality_amount / usual_price
    
    # Apply filters
    if discount_pct < 0.20 or similar_dates < 5:
        skip()
    
    # Score
    score = compute_score(discount_pct, similar_dates)
    
    # Save as ValidDeal
    save_to_db(valid_deal)
```

**Result**: 0–5 valid deals per origin per day stored in DB

### Step 4: Weekly selection (for publishing)

Per origin per week:
1. Load all valid deals from the past 7 days
2. Remove recently used deals (35-day window)
3. Group by region
4. Create bundles (3+ deals in region)
5. Score and rank
6. Pick top **3–6** (bundles + singles)

**Output**: `OriginWeeklyPayload` JSON → email/blog/social

---

## Daily Volume Estimates

### Per origin per day:
- Explore scrape: ~200–300 cards across 8 regions
- Expansion candidates: ~10–15 routes
- Valid deals found: ~0–5 (depends on market)

### Across 100 origins per day:
- Expansions: ~1,000–1,500 per day
- Valid deals: ~100–500 per day
- **Published weekly**: ~300–600 per week (3–6 per origin)

---

## Tech Stack for 100 Origins

### Data storage
- **PostgreSQL** with tables:
  - `origins`: IATA, name, tier, status
  - `raw_explore_cards`: scraped cards (audit trail)
  - `deals`: ValidDeal objects (canonical)
  - `used_deals`: deal_id + last_sent_at (35-day tracking)

### Job orchestration
- **Celery** or **Arq** (Python async task queue)
- **Redis** as broker
- **Cron** to enqueue jobs

Example cron:
```bash
# Every hour, enqueue 10 origins
0 * * * * python enqueue_origins.py --batch-size 10
```

### Worker pool
- **2–4 Playwright instances** per machine
- Each instance handles expansions serially (batch size 2)
- Scale horizontally: add more machines as needed

### API / Web layer
- **FastAPI** (Python)
- Endpoints:
  - `GET /deals/{origin}` → latest deals
  - `GET /weekly/{origin}` → OriginWeeklyPayload
  - `POST /admin/enqueue/{origin}` → manual trigger

---

## File Structure

```
Explorer Scraper/
├── deal_models.py              # Pydantic models
├── deal_converter.py           # JSON → models
├── deal_filters.py             # Filtering logic (NEW)
├── deal_scorer.py              # Scoring logic (NEW)
├── region_classifier.py        # Region mapping (NEW)
│
├── explore_scraper/            # Existing
│   ├── cli.py
│   ├── tfs_builder.py
│   └── ...
│
├── scripts/
│   ├── expand_dates.py         # Existing
│   ├── find_and_expand_deals.py  # Existing
│   ├── collect_regions.py      # Existing
│   ├── enqueue_origins.py      # NEW - cron entrypoint
│   └── process_origin.py       # NEW - worker task
│
├── db/
│   ├── models.py               # SQLAlchemy models (NEW)
│   ├── queries.py              # DB helpers (NEW)
│   └── schema.sql              # DB schema (NEW)
│
└── newsletter/
    ├── generator.py            # HTML email (NEW)
    ├── social.py               # Social posts (NEW)
    └── templates/              # Email templates (NEW)
```

---

## Next Implementation Steps

### Phase 1: Core infrastructure (Week 1–2)
1. ✅ Type-safe models (done!)
2. Set up PostgreSQL + schema
3. Refactor `find_and_expand_deals.py` to use models
4. Add `deal_filters.py` with % off logic
5. Add `region_classifier.py` with 8-region taxonomy

### Phase 2: Job orchestration (Week 3–4)
1. Set up Celery/Arq + Redis
2. Create `enqueue_origins.py` (cron entrypoint)
3. Create `process_origin.py` (worker task)
4. Add DB persistence for ValidDeals
5. Add used_deals tracking

### Phase 3: Multi-origin (Week 5–6)
1. Collect region TFS for top 20 airports
2. Test with 20 origins running daily
3. Tune batch sizes, timeouts, error handling
4. Add monitoring (Sentry, Datadog, etc.)

### Phase 4: Newsletter generation (Week 7–8)
1. Create email templates
2. Create `newsletter/generator.py`
3. Create `newsletter/social.py`
4. Test with real subscribers (small list)

### Phase 5: Scale to 100 (Week 9–10)
1. Collect region TFS for all 100 airports
2. Tune infrastructure (add machines if needed)
3. Add more city → IATA mappings
4. Launch!

---

## Monitoring & Alerts

### Key metrics to track:
- Expansions per day per origin
- Valid deals found per day per origin
- Deal quality distribution (avg % off, avg flex)
- Playwright failures / timeouts
- Used deals preventing duplicates
- Email open rates (by region, by origin)

### Alerts:
- No valid deals found for an origin in 3 days
- Expansion success rate < 80%
- Deal quality drops (avg % off < 15%)
- Worker queue depth > 1000

---

## Cost Estimates (Speculative)

### Compute (AWS/GCP/similar):
- 3–5 machines (4 CPU, 8GB RAM each)
- ~$300–500/month

### Database:
- Postgres (managed): ~$50–100/month

### Monitoring:
- Sentry / Datadog: ~$50–100/month

### Email (10K subscribers):
- SendGrid / Mailgun: ~$50–100/month

**Total**: ~$500–800/month for 100 airports at full scale

---

## Questions to Answer Before Scaling

1. **Origin selection**: Which 100 airports?
   - Tier 1 (20–30): JFK, LAX, ORD, DFW, etc.
   - Tier 2 (70–80): BNA, RDU, OKC, etc.

2. **Publishing cadence**: Weekly? 2×/week?
   - Weekly = simpler, more curated
   - 2×/week = more deals, more frequent

3. **Email segmentation**: One email per origin? Or multi-origin?
   - Per-origin = personalized ("Deals from your airport")
   - Multi-origin = "Best deals nationwide"

4. **Budget airline stance**: Include or exclude ULCCs?
   - Currently: include but label clearly
   - Option: exclude Spirit/Frontier entirely

5. **Used deals window**: 35 days? Longer/shorter?
   - 35 days = conservative (good for quality)
   - 21 days = more deals (risk of staleness)

---

## Status: Ready for Phase 1

The core pipeline is **production-ready** for single-origin daily runs.

Next: DB setup + job orchestration to scale horizontally.
