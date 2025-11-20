#!/usr/bin/env python3
"""
Test ONLY the API expansion (skip explore phase).
Use hardcoded deals to test if Google blocks API calls at scale.
"""
import asyncio
from worker.parallel_executor import ParallelWorkerPool

# Hardcoded test deals (from previous successful runs)
TEST_DEALS = [
    {'origin': 'ATL', 'destination': 'SJU', 'start_date': '2026-01-11', 'end_date': '2026-01-20', 'price': 171},
    {'origin': 'ATL', 'destination': 'AUA', 'start_date': '2026-01-15', 'end_date': '2026-01-22', 'price': 200},
    {'origin': 'DFW', 'destination': 'CUN', 'start_date': '2026-02-10', 'end_date': '2026-02-17', 'price': 250},
    {'origin': 'DFW', 'destination': 'GDL', 'start_date': '2026-01-20', 'end_date': '2026-01-27', 'price': 180},
    {'origin': 'LAX', 'destination': 'CUN', 'start_date': '2026-02-05', 'end_date': '2026-02-12', 'price': 280},
    {'origin': 'LAX', 'destination': 'PVR', 'start_date': '2026-01-25', 'end_date': '2026-02-01', 'price': 220},
    {'origin': 'ORD', 'destination': 'CUN', 'start_date': '2026-02-15', 'end_date': '2026-02-22', 'price': 300},
    {'origin': 'ORD', 'destination': 'MBJ', 'start_date': '2026-01-18', 'end_date': '2026-01-25', 'price': 250},
    {'origin': 'PHX', 'destination': 'CUN', 'start_date': '2026-02-08', 'end_date': '2026-02-15', 'price': 270},
    {'origin': 'PHX', 'destination': 'SJD', 'start_date': '2026-01-22', 'end_date': '2026-01-29', 'price': 240},
]

async def test_api_scale():
    """Test API expansion at increasing scales."""
    
    print("="*80)
    print("API EXPANSION SCALE TEST")
    print("="*80)
    print("\nTesting if Google blocks API calls at scale...")
    print("(Skipping explore phase - using hardcoded deals)\n")
    
    # Test 1: 3 deals, 1 browser
    print("\n" + "="*80)
    print("TEST 1: Small scale (3 deals, 1 browser, API mode)")
    print("="*80)
    
    pool1 = ParallelWorkerPool(num_browsers=1, verbose=True, use_api=True)
    results1 = await pool1.process_expansions(TEST_DEALS[:3])
    
    success1 = sum(1 for r in results1 if len(r['result'].get('similar_deals', [])) > 0)
    print(f"\n✓ Test 1: {success1}/{len(results1)} expansions found deals")
    
    if success1 == 0:
        print("⚠️  No deals found - API might be blocked or deals expired")
        return
    
    await asyncio.sleep(2)  # Brief pause between tests
    
    # Test 2: 6 deals, 3 browsers
    print("\n" + "="*80)
    print("TEST 2: Medium scale (6 deals, 3 browsers, API mode)")
    print("="*80)
    
    pool2 = ParallelWorkerPool(num_browsers=3, verbose=True, use_api=True)
    results2 = await pool2.process_expansions(TEST_DEALS[:6])
    
    success2 = sum(1 for r in results2 if len(r['result'].get('similar_deals', [])) > 0)
    print(f"\n✓ Test 2: {success2}/{len(results2)} expansions found deals")
    
    await asyncio.sleep(2)  # Brief pause between tests
    
    # Test 3: 10 deals, 5 browsers
    print("\n" + "="*80)
    print("TEST 3: Larger scale (10 deals, 5 browsers, API mode)")
    print("="*80)
    
    pool3 = ParallelWorkerPool(num_browsers=5, verbose=True, use_api=True)
    results3 = await pool3.process_expansions(TEST_DEALS[:10])
    
    success3 = sum(1 for r in results3 if len(r['result'].get('similar_deals', [])) > 0)
    print(f"\n✓ Test 3: {success3}/{len(results3)} expansions found deals")
    
    # Summary
    print("\n" + "="*80)
    print("SCALE TEST SUMMARY")
    print("="*80)
    print(f"Test 1 (3 deals):  {success1}/3 successful")
    print(f"Test 2 (6 deals):  {success2}/6 successful")
    print(f"Test 3 (10 deals): {success3}/10 successful")
    print()
    
    if success3 >= 8:
        print("✓ API method works at scale! Ready for 100+ origins.")
    elif success3 >= 5:
        print("⚠️  Some failures - might need rate limiting adjustments")
    else:
        print("✗ High failure rate - API might be getting blocked")

if __name__ == '__main__':
    asyncio.run(test_api_scale())

