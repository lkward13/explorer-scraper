#!/usr/bin/env python3
"""
Parallel worker pool for expanding flight deals.
Supports configurable number of browsers for progressive testing.
"""

import asyncio
import sys
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ParallelWorkerPool:
    """Manages a pool of browser instances for parallel deal expansion."""
    
    def __init__(
        self, 
        num_browsers: int = 2,
        proxy_list: Optional[List[dict]] = None,
        verbose: bool = True,
        use_api: bool = False
    ):
        """
        Initialize worker pool.
        
        Args:
            num_browsers: Number of concurrent browser instances
            proxy_list: Optional list of proxy configs for each browser
            verbose: Print progress information
            use_api: Use direct API calls instead of browser automation (faster, more reliable)
        """
        self.num_browsers = num_browsers
        self.proxy_list = proxy_list or []
        self.verbose = verbose
        self.use_api = use_api
        self.stats = {
            'expansions_completed': 0,
            'expansions_failed': 0,
            'start_time': None,
            'browser_times': []
        }
    
    async def process_expansions(self, expansion_queue: List[dict]) -> List[dict]:
        """
        Process all expansions in parallel across browser pool.
        
        Args:
            expansion_queue: List of dicts with keys:
                - origin: str
                - destination: str
                - start_date: str (YYYY-MM-DD)
                - end_date: str (YYYY-MM-DD)
                - price: int
        
        Returns:
            List of expansion results
        """
        self.stats['start_time'] = datetime.now()
        
        if len(expansion_queue) == 0:
            print("No expansions to process")
            return []
        
        # Split queue into chunks for each browser
        chunk_size = (len(expansion_queue) + self.num_browsers - 1) // self.num_browsers
        chunks = [
            expansion_queue[i:i+chunk_size] 
            for i in range(0, len(expansion_queue), chunk_size)
        ]
        
        # Always print execution header (for progress visibility)
        print(f"\n{'='*80}")
        print(f"PARALLEL EXECUTION: {len(expansion_queue)} expansions across {self.num_browsers} browser(s)")
        print(f"{'='*80}")
        for i, chunk in enumerate(chunks):
            print(f"  Browser {i+1}: {len(chunk)} expansions")
        print()
        
        # Process each chunk in parallel
        tasks = [
            self.process_chunk(i, chunks[i]) 
            for i in range(len(chunks))
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and handle errors
        all_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if self.verbose:
                    print(f"\n[Browser {i+1}] ERROR: {result}")
                self.stats['expansions_failed'] += len(chunks[i])
            else:
                all_results.extend(result)
        
        # Print final stats
        self._print_final_stats()
        
        return all_results
    
    async def process_chunk(self, browser_id: int, chunk: List[dict]) -> List[dict]:
        """
        Process a chunk of expansions sequentially in one browser instance.
        
        Args:
            browser_id: Browser identifier (for logging)
            chunk: List of expansion items to process
        
        Returns:
            List of results
        """
        results = []
        browser_start = datetime.now()
        
        # Import expansion method based on mode
        if self.use_api:
            from scripts.expand_dates_api import expand_deal_via_api
        else:
            from scripts.expand_dates import expand_dates
        
        # Stagger browser starts to avoid interference (each browser waits browser_id seconds)
        if browser_id > 0:
            await asyncio.sleep(browser_id * 2)  # 2 second stagger per browser
        
        for idx, item in enumerate(chunk, 1):
            try:
                if self.verbose:
                    elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                    mode_label = "API" if self.use_api else "Browser"
                    print(f"[{mode_label} {browser_id+1}] [{elapsed:.0f}s] {idx}/{len(chunk)}: "
                          f"{item['origin']} → {item['destination']} (${item['price']})")
                
                expansion_start = datetime.now()
                
                # Run expansion using selected method
                if self.use_api:
                    # API method - returns list of deals directly
                    similar_deals = await expand_deal_via_api(
                        origin=item['origin'],
                        destination=item['destination'],
                        outbound_date=item['start_date'],
                        return_date=item['end_date'],
                        original_price=item['price'],
                        verbose=True  # Enable verbose to see API details
                    )
                    result = {
                        'similar_deals': similar_deals,
                        'method': 'api'
                    }
                else:
                    # Browser method - returns dict with similar_deals
                    result = await expand_dates(
                        origin=item['origin'],
                        destination=item['destination'],
                        reference_start=item['start_date'],
                        reference_end=item['end_date'],
                        reference_price=item['price'],
                        verbose=False
                    )
                
                expansion_time = (datetime.now() - expansion_start).total_seconds()
                
                if self.verbose:
                    similar_count = len(result.get('similar_deals', []))
                    print(f"  ✓ Completed in {expansion_time:.1f}s ({similar_count} similar dates)")
                
                results.append({
                    'item': item,
                    'result': result,
                    'duration': expansion_time
                })
                
                self.stats['expansions_completed'] += 1
                self.stats['browser_times'].append(expansion_time)
                
                # Add small delay between expansions to avoid rate limiting
                if idx < len(chunk):  # Don't delay after last item
                    await asyncio.sleep(3)  # 3 second delay between expansions
                
            except Exception as e:
                if self.verbose:
                    print(f"  ✗ Error: {str(e)[:100]}")
                self.stats['expansions_failed'] += 1
                continue
        
        browser_time = (datetime.now() - browser_start).total_seconds()
        if self.verbose:
            print(f"\n[Browser {browser_id+1}] Completed {len(results)}/{len(chunk)} in {browser_time:.1f}s")
        
        return results
    
    def _print_final_stats(self):
        """Print final statistics after all expansions complete."""
        if not self.verbose:
            return
        
        total_time = (datetime.now() - self.stats['start_time']).total_seconds()
        completed = self.stats['expansions_completed']
        failed = self.stats['expansions_failed']
        total = completed + failed
        
        print(f"\n{'='*80}")
        print(f"EXECUTION COMPLETE")
        print(f"{'='*80}")
        print(f"Total expansions:     {total}")
        print(f"Successful:           {completed} ({completed/total*100:.1f}%)")
        print(f"Failed:               {failed}")
        print(f"Total runtime:        {total_time:.1f}s ({total_time/60:.1f} min)")
        
        if self.stats['browser_times']:
            avg_time = sum(self.stats['browser_times']) / len(self.stats['browser_times'])
            min_time = min(self.stats['browser_times'])
            max_time = max(self.stats['browser_times'])
            
            print(f"\nPer-expansion timing:")
            print(f"  Average:            {avg_time:.1f}s")
            print(f"  Min:                {min_time:.1f}s")
            print(f"  Max:                {max_time:.1f}s")
            print(f"  Throughput:         {completed/total_time:.2f} expansions/sec")
        
        # Extrapolation for 100 origins
        if completed > 0:
            avg_per_expansion = total_time / completed
            expansions_for_100 = 500  # 100 origins × 5 deals
            
            print(f"\nExtrapolation to 100 origins (500 expansions):")
            for browsers in [1, 2, 4, 8, 10, 12]:
                estimated = (expansions_for_100 / browsers) * avg_per_expansion
                print(f"  {browsers:2d} browsers: {estimated/60:5.1f} minutes")
        
        print(f"{'='*80}\n")


async def main():
    """Test the parallel executor with a simple example."""
    # Example test data
    test_queue = [
        {
            'origin': 'PHX',
            'destination': 'SJU',
            'start_date': '2026-01-12',
            'end_date': '2026-01-21',
            'price': 244
        }
    ]
    
    pool = ParallelWorkerPool(num_browsers=1, verbose=True)
    results = await pool.process_expansions(test_queue)
    
    print(f"\nResults: {len(results)} expansions completed")


if __name__ == '__main__':
    asyncio.run(main())

