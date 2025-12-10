#!/bin/bash

# Build and run Playwright price insight test in Docker

echo "Building Docker image..."
docker build -t explorer-scraper .

echo ""
echo "Running Playwright price insight test..."
docker run --rm \
  -e DISPLAY=:99 \
  explorer-scraper \
  python3 scripts/check_price_insight_playwright.py

