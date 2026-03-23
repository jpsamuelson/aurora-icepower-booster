#!/usr/bin/env python3
"""Detailed breakdown of all remaining DRC issues with fix instructions."""
import json
from collections import defaultdict

with open("/tmp/drc_current.json") as f:
    d = json.load(f)

violations = d.get("violations", [])
unconnected = d.get("unconnected_items", [])

by_type = defaultdict(list)
for v in violations:
    by_type[v["type"]].append(v)

# === isolated_copper ===
iso = by_type.get("isolated_copper", [])
iso_fcu = sum(1 for v in iso if any("F.Cu" in i.get("description","") for i in v.get("items",[])))
iso_bcu = sum(1 for v in iso if any("B.Cu" in i.get("description","") for i in v.get("items",[])))
print(f"=== isolated_copper: {len(iso)} ({iso_fcu} F.Cu, {iso_bcu} B.Cu) ===")

# === silk_edge_clearance ===
silk = by_type.get("silk_edge_clearance", [])
silk_refs = defaultdict(int)
for v in silk:
    for i in v.get("items", []):
        desc = i.get("description", "")
        import re
        ref = re.search(r'of (\w+) on', desc)
        if ref:
            silk_refs[ref.group(1)] += 1
print(f"\n=== silk_edge_clearance: {len(silk)} ===")
for ref, count in sorted(silk_refs.items()):
    print(f"  {ref}: {count}x")

# === text_thickness ===
tt = by_type.get("text_thickness", [])
print(f"\n=== text_thickness: {len(tt)} ===")
for v in tt:
    for i in v.get("items", []):
        print(f"  {i.get('description', '')[:100]}")

# === unconnected ===
zone_zone = 0
pad_zone = 0
other = 0
pad_zone_details = []

for u in unconnected:
    items = u.get("items", [])
    descs = [i.get("description", "").lower() for i in items]
    
    if all("zone" in d for d in descs):
        zone_zone += 1
    elif any("pad" in d for d in descs) and any("zone" in d for d in descs):
        pad_zone += 1
        pad_zone_details.append(items)
    else:
        other += 1
        print(f"\n  OTHER: {u.get('description','')}")
        for i in items:
            pos = i.get("pos", {})
            print(f"    {i['description']} @({pos.get('x','?')},{pos.get('y','?')})")

print(f"\n=== unconnected: {len(unconnected)} ===")
print(f"  Zone↔Zone: {zone_zone}")
print(f"  Pad↔Zone: {pad_zone}")
print(f"  Other: {other}")

for items in pad_zone_details:
    for i in items:
        pos = i.get("pos", {})
        desc = i.get("description", "")
        if "pad" in desc.lower():
            print(f"  Pad disconnect: {desc} @({pos.get('x','?')},{pos.get('y','?')})")
