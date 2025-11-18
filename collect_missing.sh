#!/bin/bash
echo "Collecting missing regions..."
echo ""

python scripts/collect_regions.py --origin ATL --regions "Europe,South America" 2>&1 | tail -5
sleep 2

python scripts/collect_regions.py --origin PHX --regions "Asia,Middle East" 2>&1 | tail -5
sleep 2

python scripts/collect_regions.py --origin ORD --regions "Caribbean,Oceania,Africa" 2>&1 | tail -5
sleep 2

python scripts/collect_regions.py --origin OKC --regions "Oceania,Asia" 2>&1 | tail -5
sleep 2

python scripts/collect_regions.py --origin BOS --regions "South America,Asia,Middle East" 2>&1 | tail -5
sleep 2

python scripts/collect_regions.py --origin DEN --regions "Caribbean,Africa" 2>&1 | tail -5

echo ""
echo "=========================================="
echo "Collection complete! Final status:"
echo "=========================================="
for origin in DFW ATL PHX ORD OKC BOS DEN; do
  regions=$(cat "data/region_tfs/${origin}.json" | python -c "import json, sys; data=json.load(sys.stdin); print(sum(1 for v in data['regions'].values() if v is not None))")
  echo "$origin: $regions/8 regions"
done
