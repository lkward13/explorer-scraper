#!/bin/bash
# Run full API workflow test in Docker

echo "Building Docker image..."
docker build -t explorer-scraper . -q

echo "Running full workflow test (Explore + API expansion)..."
docker run --rm explorer-scraper start_with_xvfb.sh python -u test_full_api_workflow.py

