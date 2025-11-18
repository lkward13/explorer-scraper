#!/bin/bash
origins=("DFW" "ATL" "PHX" "ORD" "OKC" "BOS" "DEN")
regions="Europe,Caribbean,South America,Africa,Oceania,Asia,Middle East"

for origin in "${origins[@]}"; do
  echo ""
  echo "=========================================="
  echo "Collecting all regions for $origin..."
  echo "=========================================="
  python scripts/collect_regions.py --origin "$origin" --regions "$regions" --delay 5 2>&1 | tail -10
  echo "Waiting 5s before next origin..."
  sleep 5
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

echo ""
echo "=========================================="
echo "If any origins have <8 regions, run:"
echo "=========================================="
for origin in "${origins[@]}"; do
  if [ -f "data/region_tfs/${origin}.json" ]; then
    regions=$(cat "data/region_tfs/${origin}.json" | python -c "import json, sys; data=json.load(sys.stdin); print(sum(1 for v in data['regions'].values() if v is not None))")
    if [ "$regions" -lt 8 ]; then
      echo "python scripts/collect_regions.py --origin $origin --regions \"Europe,Caribbean,South America,Africa,Oceania,Asia,Middle East\" --delay 5"
    fi
  fi
done
