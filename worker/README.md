# Parallel Worker System

Progressive testing framework for scaling to 100 airports with parallel browser execution.

## Quick Start - Phase 1 (Local Test)

Test locally on your machine with 2 origins and 1 browser:

```bash
python worker/test_parallel.py --phase 1
```

**What this does:**
- Scrapes PHX and DFW across 5 regions each
- Selects top 5 deals per origin (10 total)
- Expands all 10 deals sequentially in 1 browser
- Measures actual expansion time per deal
- Shows extrapolation for 100 origins with different browser counts

**Expected runtime:** ~15-20 minutes  
**Memory needed:** ~3-4 GB  
**Output:** Baseline performance metrics

## Test Phases

### Phase 1: Baseline (Run Locally)
```bash
python worker/test_parallel.py --phase 1
```
- Origins: 2 (PHX, DFW)
- Browsers: 1
- Expansions: 10
- Purpose: Establish baseline, test locally

### Phase 2: Small Parallel
```bash
python worker/test_parallel.py --phase 2
```
- Origins: 5 (PHX, DFW, LAX, ORD, JFK)
- Browsers: 2
- Expansions: 25
- Purpose: Verify parallel execution works

### Phase 3: Medium Scale
```bash
python worker/test_parallel.py --phase 3
```
- Origins: 10
- Browsers: 4
- Expansions: 50
- Purpose: Test with production-like specs (needs ~10GB RAM)

## Understanding the Output

**Key metrics to watch:**

1. **Expansion time per deal**
   - How long each individual expansion takes
   - Used to calculate how many browsers we need

2. **Extrapolation table**
   - Shows estimated runtime for 100 origins
   - Helps decide optimal browser count

3. **Success rate**
   - Should be >80%
   - If lower, indicates rate limiting or errors

**Example output:**
```
Extrapolation to 100 origins (500 expansions):
   1 browsers:  75.0 minutes
   2 browsers:  37.5 minutes
   4 browsers:  18.8 minutes
   8 browsers:   9.4 minutes
  10 browsers:   7.5 minutes
  12 browsers:   6.2 minutes
```

## Architecture

### `parallel_executor.py`
Core worker pool that manages multiple browser instances.

**Key features:**
- Configurable browser count (1-12+)
- Sequential processing per browser (stable)
- Detailed timing metrics
- Automatic extrapolation for scaling

### `test_parallel.py`
Test runner for progressive scaling tests.

**Workflow:**
1. Run Explore for N origins
2. Select top 5 deals per origin
3. Expand deals in parallel
4. Report metrics and extrapolations

## Next Steps After Phase 1

**If average expansion time is ~60-90 seconds:**
- 12 browsers will hit <60 min target ✓
- Proceed to Phase 2 locally

**If expansion time is slower (>120 seconds):**
- Need more optimization or more browsers
- Consider reducing deals per origin (5 → 3)

**If seeing rate limiting (429 errors):**
- Add proxy support (see proxy_manager.py)
- Reduce parallel browsers

## Files

- `parallel_executor.py` - Browser pool manager
- `test_parallel.py` - Progressive test runner
- `proxy_manager.py` - Proxy rotation (for later phases)
- `run_daily.py` - Production orchestrator (for deployment)

## Requirements

Same as main project:
- Python 3.8+
- Playwright
- All dependencies from main requirements.txt

## Troubleshooting

**"Browser crashed" errors:**
- Reduce num_browsers
- Add more RAM
- Check system resources with `htop` or Activity Monitor

**"No deals found":**
- Check that region TFS are collected for origin
- Run: `python scripts/collect_regions.py --origin PHX --regions all`

**Very slow expansion times (>180s):**
- Network connection issue
- Try reducing --limit in explore step
- Check if Google is rate limiting

