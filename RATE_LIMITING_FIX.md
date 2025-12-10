# Rate Limiting Fix - 100-Origin Test v2

**Date:** November 24, 2025  
**Status:** Running  
**Expected Duration:** 2.5-3 hours

---

## 🔍 Problem Identified

The previous 100-origin test showed **progressive slowdown** across batches:

| Batch | Time | Per-Expansion | Slowdown |
|-------|------|---------------|----------|
| 1 | 16.5 min | 7.9s | Baseline |
| 2 | 20.6 min | 9.9s | +25% |
| 3 | 29.5 min | 14.2s | +80% |
| 4 | 53.9 min | 25.9s | +228% ⚠️ |

**Root Cause:** Google API rate limiting accumulates across the session, even with 5-minute pauses between batches.

---

## 🛠️ Solutions Implemented

### 1. Increased Pause Time
- **Before:** 5 minutes between batches
- **After:** 10 minutes between batches
- **Impact:** Gives Google's rate limiters more time to reset

### 2. Reduced Concurrent API Calls
- **Before:** 5 browsers for expansion (5 simultaneous API calls)
- **After:** 3 browsers for expansion (3 simultaneous API calls)
- **Impact:** 40% reduction in concurrent load on Google's API
- **Note:** Explore phase still uses 5 browsers (unaffected)

### 3. Added Random Jitter
- **Implementation:** 0.5-2 second random delay between the 4 API calls per expansion
- **Location:** `scripts/expand_dates_api.py`
- **Impact:** Makes requests appear more "human-like" and spreads load over time

```python
# Stagger the 4 API calls with random delays
jitters = [0, random.uniform(500, 2000), random.uniform(500, 2000), random.uniform(500, 2000)]

task1 = fetch_with_jitter(jitters[0], context, origin, destination, ...)
task2 = fetch_with_jitter(jitters[1], context, origin, destination, ...)
task3 = fetch_with_jitter(jitters[2], context, origin, destination, ...)
task4 = fetch_with_jitter(jitters[3], context, origin, destination, ...)
```

---

## 📊 Expected Performance

### Time Estimates (per batch)
With 3 browsers instead of 5, expansion phase will be ~1.67x slower per batch:
- **Batch 1:** ~20-25 minutes (was 16.5 min)
- **Batch 2:** ~25-30 minutes (was 20.6 min)
- **Batch 3:** ~30-35 minutes (was 29.5 min)
- **Batch 4:** ~30-35 minutes (was 53.9 min) ⚠️ **Should be much better!**

### Total Time
- **Previous test:** 135.5 minutes (2h 15min)
- **Expected:** 150-180 minutes (2.5-3 hours)
- **Trade-off:** +15-45 minutes for consistent performance and 100% reliability

---

## 🎯 Success Criteria

1. **Batch 4 should NOT be 2-3x slower than Batch 1**
2. **All 500 expansions should succeed (100% rate)**
3. **Per-expansion time should remain consistent across batches** (~10-15s)
4. **Database should save all ~21,000 flight options**

---

## 📝 Files Modified

### Configuration
- `test_100_origins_v2.py`
  - Changed `pause_minutes` from 5 to 10
  - Changed `browsers` from 5 to 3
  - Added `explore_browsers: 5` config

### Core Logic
- `worker/test_parallel.py`
  - Added support for separate `explore_browsers` vs `browsers` (expansion)
  - Updated logging to show both browser counts

### API Calls
- `scripts/expand_dates_api.py`
  - Added `import random`
  - Implemented `fetch_with_jitter()` wrapper function
  - Added 0.5-2s random delays between the 4 API calls per expansion

---

## 🔬 Monitoring

To check progress during the test:

```bash
# Check current status
tail -50 test_100_origins_final.log

# Monitor batch completion
grep "BATCH [0-9]/4" test_100_origins_final.log

# Check for rate limiting issues
grep -i "rate limit\|timeout\|failed" test_100_origins_final.log

# See expansion timing
grep "Expansion time:" test_100_origins_final.log
```

---

## 📈 Results (To Be Updated)

### Batch Performance
| Batch | Time | Per-Expansion | vs. Previous |
|-------|------|---------------|--------------|
| 1 | TBD | TBD | TBD |
| 2 | TBD | TBD | TBD |
| 3 | TBD | TBD | TBD |
| 4 | TBD | TBD | **Should be much better!** |

### Overall Metrics
- **Total Time:** TBD
- **Success Rate:** TBD
- **Valid Deals:** TBD
- **Database Entries:** TBD

---

## 🚀 Next Steps After Completion

1. **Analyze Results:** Compare Batch 4 timing to Batch 1
2. **Verify Database:** Check all deals were saved correctly
3. **Fine-tune:** If still seeing slowdown, consider:
   - Increasing pause to 15 minutes
   - Reducing to 2 browsers for expansion
   - Adding per-browser jitter (not just per-API-call)
4. **Production Deployment:** Once stable, deploy to cloud infrastructure

