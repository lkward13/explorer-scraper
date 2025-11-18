#!/bin/bash
origins=("DFW" "ATL" "PHX" "ORD" "OKC" "BOS" "DEN")
regions="North America,Central America,South America,Caribbean,Europe,Africa,Asia,Oceania,Middle East"

echo "=========================================="
echo "Collecting 9 regions per origin:"
echo "1. North America"
echo "2. Central America"
echo "3. South America"
echo "4. Caribbean"
echo "5. Europe"
echo "6. Africa"
echo "7. Asia"
echo "8. Oceania"
echo "9. Middle East"
echo "=========================================="

for origin in "${origins[@]}"; do
  echo ""
  echo "=========================================="
  echo "Collecting all 9 regions for $origin..."
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
    count=$(cat "data/region_tfs/${origin}.json" | python -c "import json, sys; data=json.load(sys.stdin); print(sum(1 for v in data['regions'].values() if v is not None and v != data['regions'].get('anywhere')))")
    echo "$origin: $count/9 regions"
  else
    echo "$origin: FILE NOT FOUND"
  fi
done
