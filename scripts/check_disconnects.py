#!/usr/bin/env python3
"""Check for real (non-zone) disconnects in DRC results."""
import json

with open("/tmp/drc_final.json") as f:
    d = json.load(f)

print("=== REAL DISCONNECTS (non-zone) ===")
real = 0
zone = 0
for u in d.get("unconnected_items", []):
    items = u.get("items", [])
    is_zone = all("zone" in i.get("description", "").lower() for i in items)
    if is_zone:
        zone += 1
    else:
        real += 1
        desc = u.get("description", "")
        print(f"\n  {desc}")
        for i in items:
            pos = i.get("pos", {})
            print(f"    {i['description']} @({pos.get('x','?')},{pos.get('y','?')})")

print(f"\nZone disconnects: {zone}")
print(f"Real disconnects: {real}")

print("\n=== VIOLATION TYPES ===")
from collections import Counter
types = Counter(v["type"] for v in d.get("violations", []))
for t, c in types.most_common():
    print(f"  {c}x {t}")

print("\n=== SHORTS ===")
for v in d.get("violations", []):
    if v["type"] == "shorting_items":
        print(f"  {v['description']}")
