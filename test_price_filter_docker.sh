#!/bin/bash

# Test price insight filter in Docker

echo "Building Docker image..."
docker build -t explorer-scraper .

echo ""
echo "Running price filter test (3 origins, 20% discount threshold)..."
docker run --rm \
  -e DISPLAY=:99 \
  explorer-scraper \
  python3 -u test_price_filter.py

