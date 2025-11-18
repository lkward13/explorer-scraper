#!/bin/bash
origins=("DFW" "ATL" "PHX" "ORD" "OKC" "BOS" "DEN")
regions="Europe,Asia,Africa,South America,Central America,Caribbean,Oceania,Middle East"

echo "=========================================="
echo "Collecting 8 regions per origin:"
echo "1. Europe"
echo "2. Asia"
echo "3. Africa"
echo "4. South America"
echo "5. Central America"
echo "6. Caribbean"
echo "7. Oceania"
echo "8. Middle East"
echo "=========================================="

for origin in "${origins[@]}"; do
  echo ""
  echo "=========================================="
  echo "Collecting all 8 regions for $origin..."
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
    count=$(cat "data/region_tfs/${origin}.json" | python -c "import json, sys; data=json.load(sys.stdin); print(sum(1 for v in data['regions'].values() if v is not None))")
    echo "$origin: $count/9 regions (8 main + 'anywhere')"
  else
    echo "$origin: FILE NOT FOUND"
  fi
done
