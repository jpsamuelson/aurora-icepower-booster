#!/usr/bin/env python3
"""Deep DRC analysis — categorize every violation with full details."""
import json
from collections import defaultdict

with open("/tmp/drc_deep.json") as f:
    d = json.load(f)

violations = d.get("violations", [])
unconnected = d.get("unconnected_items", [])

print(f"{'='*70}")
print(f"DRC DEEP ANALYSIS — {len(violations)} Violations, {len(unconnected)} Unconnected")
print(f"{'='*70}")

# Group by type
by_type = defaultdict(list)
for v in violations:
    by_type[v.get("type", "unknown")].append(v)

for vtype in sorted(by_type.keys(), key=lambda t: -len(by_type[t])):
    items = by_type[vtype]
    sev = items[0].get("severity", "?")
    print(f"\n{'─'*70}")
    print(f"[{sev.upper()}] {vtype} — {len(items)}x")
    print(f"{'─'*70}")
    
    for i, v in enumerate(items):
        desc = v.get("description", "").strip()
        vitems = v.get("items", [])
        
        # Compact output
        item_strs = []
        for it in vitems:
            idesc = it.get("description", "")
            pos = it.get("pos", {})
            x = pos.get("x", "?")
            y = pos.get("y", "?")
            item_strs.append(f"{idesc} @({x},{y})")
        
        print(f"  {i+1}. {desc}")
        for s in item_strs:
            print(f"     └─ {s}")

# Unconnected items analysis
print(f"\n{'='*70}")
print(f"UNCONNECTED ITEMS — {len(unconnected)}")
print(f"{'='*70}")

zone_disconnects = 0
real_disconnects = []

for u in unconnected:
    desc = u.get("description", "")
    items = u.get("items", [])
    is_zone = all("zone" in it.get("description", "").lower() for it in items)
    
    if is_zone:
        zone_disconnects += 1
    else:
        item_strs = []
        for it in items:
            idesc = it.get("description", "")
            pos = it.get("pos", {})
            x = pos.get("x", "?")
            y = pos.get("y", "?")
            item_strs.append(f"{idesc} @({x},{y})")
        real_disconnects.append((desc, item_strs))

print(f"\n  Zone-to-Zone disconnects (stale fill): {zone_disconnects}")
print(f"  Real signal disconnects: {len(real_disconnects)}")

for desc, items in real_disconnects:
    print(f"\n  ⚠ {desc}")
    for s in items:
        print(f"     └─ {s}")

# Summary with actionability
print(f"\n{'='*70}")
print(f"SUMMARY & ACTION ITEMS")
print(f"{'='*70}")

categories = {
    "KRITISCH (muss behoben werden)": [],
    "ZONE REFILL (löst sich in KiCad)": [],
    "KOSMETISCH (akzeptabel)": [],
    "BEKANNT (Designentscheidung)": [],
}

for vtype, items in by_type.items():
    count = len(items)
    if vtype in ("shorting_items",):
        categories["KRITISCH (muss behoben werden)"].append(f"{count}x {vtype}")
    elif vtype in ("isolated_copper",):
        categories["ZONE REFILL (löst sich in KiCad)"].append(f"{count}x {vtype}")
    elif vtype in ("clearance",) and any("power_clearance" in v.get("description","") for v in items):
        categories["ZONE REFILL (löst sich in KiCad)"].append(f"{count}x {vtype} (stale zone vs new traces)")
    elif vtype in ("silk_edge_clearance",):
        categories["BEKANNT (Designentscheidung)"].append(f"{count}x {vtype} (XLR Silkscreen-Extensions)")
    elif vtype in ("text_thickness", "missing_courtyard", "solder_mask_bridge"):
        categories["KOSMETISCH (akzeptabel)"].append(f"{count}x {vtype}")
    elif vtype in ("hole_clearance",):
        # Analyze if these are real issues
        categories["KRITISCH (muss behoben werden)"].append(f"{count}x {vtype}")
    else:
        categories["KOSMETISCH (akzeptabel)"].append(f"{count}x {vtype}")

if zone_disconnects > 0:
    categories["ZONE REFILL (löst sich in KiCad)"].append(f"{zone_disconnects}x zone-to-zone unconnected")
if real_disconnects:
    categories["KRITISCH (muss behoben werden)"].append(f"{len(real_disconnects)}x real signal disconnects")

for cat, items in categories.items():
    if items:
        print(f"\n  {cat}:")
        for item in items:
            print(f"    • {item}")
