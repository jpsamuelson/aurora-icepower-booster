#!/usr/bin/env python3
"""Analyze silk DRC violations in detail."""
import json

with open('/tmp/drc_p5h.json') as f:
    drc = json.load(f)

# Silk over copper — manufacturing concern
print("=== SILK OVER COPPER (23) ===")
for v in drc.get('violations', []):
    if v['type'] == 'silk_over_copper':
        items = v.get('items', [])
        desc = v.get('description', '')
        refs = []
        for item in items:
            r = item.get('description', '')
            pos = item.get('pos', {})
            refs.append(f"  {r} @ ({pos.get('x',0):.2f}, {pos.get('y',0):.2f})")
        print(f"{desc}")
        for r in refs:
            print(r)
        print()

# Silk overlap — cosmetic but let's see
print("\n=== SILK OVERLAP (53) — first 20 ===")
for i, v in enumerate(drc.get('violations', [])):
    if v['type'] == 'silk_overlap' and i < 60:
        items = v.get('items', [])
        refs = [item.get('description', '') for item in items]
        print(f"  {' vs '.join(refs)}")

# Silk edge clearance
print("\n=== SILK EDGE CLEARANCE (2) ===")
for v in drc.get('violations', []):
    if v['type'] == 'silk_edge_clearance':
        items = v.get('items', [])
        refs = [item.get('description', '') for item in items]
        print(f"  {' | '.join(refs)}")

# Unconnected
print("\n=== UNCONNECTED (13) ===")
for v in drc.get('unconnected', []):
    items = v.get('items', [])
    refs = [item.get('description', '') for item in items]
    print(f"  {' <-> '.join(refs)}")
