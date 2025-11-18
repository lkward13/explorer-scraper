#!/bin/bash
origins=("DEN" "SEA" "BOS" "ORD" "JFK" "IAH" "SFO")
for origin in "${origins[@]}"; do
  echo ""
  echo "=========================================="
  echo "Collecting $origin..."
  echo "=========================================="
  python scripts/collect_regions.py --origin "$origin" --regions "Europe,Caribbean,Central America,South America,Africa,Oceania,Asia,Middle East" 2>&1 | tail -20
  sleep 3
done
echo ""
echo "=========================================="
echo "Collection complete! Summary:"
echo "=========================================="
for file in data/region_tfs/*.json; do 
  origin=$(basename "$file" .json)
  regions=$(cat "$file" | python -c "import json, sys; data=json.load(sys.stdin); print(sum(1 for v in data['regions'].values() if v is not None))")
  echo "$origin: $regions/8 regions"
done | sort -t: -k2 -rn
