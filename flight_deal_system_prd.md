# **Flight Deal System — Full PRD (Product Requirements Document)**  
### **Version 1.0 — Generated for Cursor Implementation**

---

# **0. Overview**

This system identifies, evaluates, and enriches cheap flight deals by combining three components:

1. **RADAR:** Google Explore scrapes → detect cheap prices.
2. **MEMORY / BASELINE:** Store all daily prices from Google Flights price-graph RPC → compute “typical” prices for each route/month/trip_length.
3. **SPOTLIGHT:** For routes detected as cheap, fetch full price graph → evaluate deal quality → find similar dates → generate enriched “deal objects.”

The key advantage of this design:

- No HTML scraping  
- No dependency on Google Price Insights  
- Scalable  
- Statistically reliable  
- Expands in accuracy over time

---

# **1. Goals**

### **Primary Goals**
- Identify cheap routes daily using Google Explore.
- Determine if a route is *actually* a good deal relative to historical norms.
- Fetch 11-month price-graph data via RPC and store **every daily data point**.
- Build internal baselines from historical data.
- Produce enriched deal objects containing:
  - deal price  
  - typical price  
  - “$X cheaper than usual”  
  - discount %  
  - bucket classification (low, typical, high)  
  - similar dates (±$X)

---

# **2. Architecture Summary**

### **Three-Stage System**

## **Stage 1 — RADAR (Google Explore)**
- Scrape Explore for each ORIGIN × REGION pair.
- Store all Explore results.
- Pick **top N cheapest** results per origin-region to create **deal candidates**.

---

## **Stage 2 — MEMORY / BASELINE (Historical graph storage)**

### **Price Graph RPC**
- For a given `(origin, destination, trip_length)`:
  - Fetch **~330 daily prices** for the next ~11 months.
  - Store **all daily `(date, price)` points** in a Postgres table.

### **Baseline Engine**
- Nightly job groups historical graph data by:
  - route (origin, destination)
  - trip_length  
  - month_of_year  
- Computes:
  - median price  
  - p25 and p75  
  - sample_count  
- Stores this in a `route_baselines` table.

---

## **Stage 3 — SPOTLIGHT (Deal enrichment)**

When Explore finds a cheap price:

1. Look up baseline for that route/month/trip_length.
2. If Explore price is ≥25% below typical → mark as deal.
3. Fetch the price graph for that route.
4. Compute:
   - local typical (±30-day window using median)
   - discount amount and %
   - classification bucket
   - similar available dates from graph
5. Insert enriched deal into `deals` table.

---

# **3. Database Schema**

## **3.1 explore_results**

Stores raw Explore radar hits.

```sql
CREATE TABLE explore_results (
    id              SERIAL PRIMARY KEY,
    origin          VARCHAR(3) NOT NULL,
    destination     VARCHAR(3) NOT NULL,
    region          VARCHAR(32),
    price           INTEGER NOT NULL,
    depart_date     DATE,
    return_date     DATE,
    trip_length     INTEGER,
    observed_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_explore_results_origin_region
    ON explore_results (origin, region, observed_at);
```

---

## **3.2 route_prices**

Stores *every* daily price from a graph scrape.

```sql
CREATE TABLE route_prices (
    id              SERIAL PRIMARY KEY,
    origin          VARCHAR(3) NOT NULL,
    destination     VARCHAR(3) NOT NULL,
    trip_length     INTEGER NOT NULL,
    depart_date     DATE NOT NULL,
    price           INTEGER NOT NULL,
    observed_at     TIMESTAMP NOT NULL,
    source          VARCHAR(16) NOT NULL
);

CREATE INDEX idx_route_prices_route_date
    ON route_prices (origin, destination, trip_length, depart_date);

CREATE INDEX idx_route_prices_route_observed
    ON route_prices (origin, destination, trip_length, observed_at);
```

---

## **3.3 route_baselines**

Stores typical prices for each route/month/trip_length.

```sql
CREATE TABLE route_baselines (
    id              SERIAL PRIMARY KEY,
    origin          VARCHAR(3) NOT NULL,
    destination     VARCHAR(3) NOT NULL,
    trip_length     INTEGER NOT NULL,
    month_of_year   INTEGER NOT NULL CHECK (month_of_year BETWEEN 1 AND 12),
    median_price    INTEGER NOT NULL,
    p25_price       INTEGER,
    p75_price       INTEGER,
    sample_count    INTEGER NOT NULL,
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (origin, destination, trip_length, month_of_year)
);

CREATE INDEX idx_route_baselines_route_month
    ON route_baselines (origin, destination, trip_length, month_of_year);
```

---

## **3.4 deals**

Stores enriched deals ready for email/web/push delivery.

```sql
CREATE TABLE deals (
    id                  SERIAL PRIMARY KEY,
    origin              VARCHAR(3) NOT NULL,
    destination         VARCHAR(3) NOT NULL,
    trip_length         INTEGER NOT NULL,
    depart_date         DATE NOT NULL,
    return_date         DATE NOT NULL,
    current_price       INTEGER NOT NULL,
    baseline_price      INTEGER,
    discount_amount     INTEGER,
    discount_pct        REAL,
    bucket              VARCHAR(16),
    similar_dates_json  JSONB,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deals_route_depart
    ON deals (origin, destination, depart_date);
```

---

# **4. Daily Pipeline (Cron)**

## **Step 1 — Scrape Explore (RADAR)**

### Config:

```
ORIGINS = 100 airports
REGIONS = 9
TOP_N_PER_ORIGIN_REGION = 5
```

### Flow:

- For each origin-region:
  - Call Explore
  - Insert results into `explore_results`
  - Select cheapest N → deal candidates

Approximately ~4,500 candidates/day.

---

## **Step 2 — Deal Detection (Compare vs Baseline)**

Given a candidate from Explore:

1. Extract:
   - origin, destination  
   - depart_date, return_date  
   - price  
   - trip_length  
   - month_of_year  

2. Lookup baseline:

```
SELECT * FROM route_baselines
WHERE origin = ?
AND destination = ?
AND trip_length = ?
AND month_of_year = ?;
```

3. If baseline exists AND sample_count >= MIN_BASELINE_SAMPLES:

```
discount_amount = baseline_price - explore_price
discount_pct = discount_amount / baseline_price

If discount_pct >= MIN_DEAL_DISCOUNT_PCT (0.25): 
    enqueue for graph scrape
```

4. If baseline does NOT exist:
   - Optionally skip OR apply fallback absolute thresholds.

---

# **5. Deal Enrichment (Graph + Similar Dates)**

For each candidate that passes detection:

### Step 1 — Fetch graph RPC  
Fetch ~330 daily price points for 11 months.

### Step 2 — Store all daily points  
Insert into `route_prices`.

### Step 3 — Compute local typical price  

Using ±30-day window:

```python
comparison_prices = [p.price for p in points
                     if abs((p.date - deal_date).days) <= 30]
typical_price = median(comparison_prices)
```

### Step 4 — Compute discount

```python
discount_amount = typical_price - deal_price
discount_pct = discount_amount / typical_price
```

### Step 5 — Classify deal

```python
>= 35%  → very_low
>= 20%  → low
>= 5%   → typical
< 5%    → high (not a good deal)
```

### Step 6 — Identify similar dates

Find dates with price ≤ deal_price + $75:

```python
similar_dates = [
  {depart_date, return_date, price}
]
```

### Step 7 — Insert into `deals`

This is your final deal object.

---

# **6. Nightly Job — Build Baselines**

Runs daily or several times a week.

### Query:

```sql
SELECT origin, destination, trip_length,
       EXTRACT(MONTH FROM depart_date) AS month_of_year,
       PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) AS p25,
       PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price) AS median,
       PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) AS p75,
       COUNT(*) AS sample_count
FROM route_prices
WHERE observed_at >= NOW() - INTERVAL '365 days'
GROUP BY origin, destination, trip_length, EXTRACT(MONTH FROM depart_date);
```

### Upsert into `route_baselines`.

This improves accuracy over time.

---

# **7. Rotational Graph Scrapes (Optional, Enhances Accuracy)**

To avoid gaps:

- Keep list of all `(origin, dest, trip_length)` routes.
- Each night scrape **500–2000 routes** not graphed recently.
- Insert their graph data into `route_prices`.

This builds a complete memory without hammering 35k graph calls/day.

---

# **8. Price Insights (Google HTML)**

**NOT** used in core pipeline.  
CAPTCHA risk is too high.

`scripts/check_price_insight_fast.py` should be:

- optional calibration tool  
- run only on 5–20 deals/day manually  
- not integrated into automated workflow

We compute our own:

- “low / typical / high”
- “$X cheaper than usual”

from `route_prices` and `route_baselines`.

---

# **9. Config Values (Defaults)**

```python
MIN_DEAL_DISCOUNT_PCT = 0.25
MIN_BASELINE_SAMPLES = 30
COMPARISON_WINDOW_DAYS = 30
SIMILAR_DATE_MAX_DELTA_DOLLARS = 75
BASELINE_LOOKBACK_DAYS = 365
TOP_N_PER_ORIGIN_REGION = 5
```

---

# **10. Required Modules**

Cursor should implement:

```text
config.py
db.py
explore_scraper.py
graph_scraper.py
deal_detection.py
deal_builder.py
baseline.py
scheduler.py
main.py
```

Each module’s responsibilities are clearly defined in sections above.

---

# **11. Expected Output (Deals)**

Each deal object contains:

- origin, destination  
- depart_date, return_date  
- current price  
- typical price  
- discount amount  
- discount percentage  
- bucket classification  
- similar dates list  
- created_at  

This is sufficient for:

- Email alerts  
- Website display  
- Push notifications  
- Deal ranking  
- Machine learning models (later)

---

# **12. System Behavior Over Time**

### Week 1:
- Explore detects cheap routes.
- Graph scrapes enrich deals.
- Baselines begin forming.

### Weeks 2–4:
- Baselines become stable and meaningful.
- Deal classification becomes much more accurate.

### Months 2–3:
- System becomes comparable to Going.com in deal accuracy.

---

# **13. What This System *Avoids***

- HTML scraping  
- CAPTCHA walls  
- Reliance on Google’s price insight endpoint  
- Excessive RPC traffic (we only graph what matters)  
- Needing months of data before launching (you can launch within days)

---

# **14. Launch Plan (Minimal Viable Pipeline)**

### Day 1–3:
- Implement Explore → Candidate flow.
- Implement graph scraper + store daily points.
- Generate first few deals with logic above.

### Day 4–14:
- Implement nightly baseline builder.
- Deals begin including “cheaper than usual” reliably.

### End of Week 2:
- Launch publicly.

---

# **15. End State**

A fully autonomous system that:

- Detects deals daily  
- Enriches them  
- Scores them  
- Stores long-term price data  
- Gets smarter with time  
- Scales to 100×350 routes  
- Avoids CAPTCHAs  
- Does not rely on Google’s private insights
