#!/bin/bash

# Test 100 origins in Docker (2× 50-origin batches)

echo "Building Docker image..."
docker build -t explorer-scraper .

echo ""
echo "Running 100-origin test (2× 50-origin batches with 10-min pause)..."
echo "This will take approximately 60-70 minutes total."
echo ""

docker run --rm \
  -e DISPLAY=:99 \
  explorer-scraper \
  python3 -u test_100_origins.py

