#!/usr/bin/env python3
"""Full analysis of all 13 unconnected items."""
import json

with open('/tmp/drc_reroute.json') as f:
    drc = json.load(f)

signal_uc = []
zone_uc = []

for i, v in enumerate(drc.get('unconnected_items', []), 1):
    items = v.get('items', [])
    descs = []
    is_zone = False
    for item in items:
        d = item.get('description', '')
        pos = item.get('pos', {})
        x, y = pos.get('x', 0), pos.get('y', 0)
        descs.append(f"{d} @ ({x:.1f}, {y:.1f})")
        if 'Zone' in d:
            is_zone = True
    
    entry = f"{i}. {' <-> '.join(descs)}"
    if is_zone:
        zone_uc.append(entry)
    else:
        signal_uc.append(entry)

print(f"=== SIGNAL UNCONNECTED ({len(signal_uc)}) ===")
for s in signal_uc:
    print(s)

print(f"\n=== ZONE FRAGMENTS ({len(zone_uc)}) ===")
for z in zone_uc:
    print(z)
