#!/usr/bin/env python3
"""Analyze unconnected items from DRC JSON by exploring the structure."""
import json

with open('/tmp/drc_p5h.json') as f:
    drc = json.load(f)

# Print top-level keys
print("Top-level keys:", list(drc.keys()))

# Check each key for unconnected info
for key in drc.keys():
    if key == 'violations':
        continue
    val = drc[key]
    if isinstance(val, list) and len(val) > 0:
        print(f"\n{key}: {len(val)} items")
        for item in val[:3]:
            print(f"  {json.dumps(item, indent=2)[:500]}")
    elif isinstance(val, dict):
        print(f"\n{key}: {json.dumps(val, indent=2)[:300]}")
    else:
        print(f"\n{key}: {val}")

# Also check violations for unconnected type
uc_count = 0
for v in drc.get('violations', []):
    if 'unconnected' in v.get('type', '').lower():
        uc_count += 1
        items = v.get('items', [])
        for item in items:
            print(f"  UC: {item.get('description','')} @ ({item.get('pos',{}).get('x',0):.1f}, {item.get('pos',{}).get('y',0):.1f})")
if uc_count == 0:
    print("\nNo violations with 'unconnected' type found in violations list")
    # Maybe under different key
    print("\nSearching all violations for net-related issues:")
    for v in drc.get('violations', []):
        t = v.get('type', '')
        if t not in ('silk_over_copper', 'silk_overlap', 'silk_edge_clearance'):
            print(f"  Type: {t}")
            for item in v.get('items', []):
                print(f"    {item.get('description', '')}")
