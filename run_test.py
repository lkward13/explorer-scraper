#!/usr/bin/env python3
"""
Simple test runner for Railway deployment.
Runs Phase 1 test to verify Chromium headless works.
"""

import sys
import subprocess

if __name__ == "__main__":
    # Run Phase 1 test
    print("Starting Phase 1 test on Railway...")
    print("-" * 80)
    
    result = subprocess.run(
        ["python", "worker/test_parallel.py", "--phase", "1"],
        capture_output=False
    )
    
    sys.exit(result.returncode)

