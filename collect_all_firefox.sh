#!/bin/bash
origins=("DFW" "ATL" "PHX" "ORD" "OKC" "BOS" "DEN")
regions="Europe,Caribbean,South America,Africa,Oceania,Asia,Middle East"

for origin in "${origins[@]}"; do
  echo ""
  echo "=========================================="
  echo "Collecting all regions for $origin..."
  echo "=========================================="
  python scripts/collect_regions.py --origin "$origin" --regions "$regions" --delay 5
  echo "Waiting 10s before next origin..."
  sleep 10
done

echo ""
echo "=========================================="
echo "Final Summary:"
echo "=========================================="
for origin in "${origins[@]}"; do
  if [ -f "data/region_tfs/${origin}.json" ]; then
    regions=$(cat "data/region_tfs/${origin}.json" | python -c "import json, sys; data=json.load(sys.stdin); print(sum(1 for v in data['regions'].values() if v is not None))")
    echo "$origin: $regions/8 regions"
  else
    echo "$origin: FILE NOT FOUND"
  fi
done
