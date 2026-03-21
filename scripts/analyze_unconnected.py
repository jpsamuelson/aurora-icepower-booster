#!/usr/bin/env python3
"""Analyze the 13 unconnected items in detail."""
import json

with open('/tmp/drc_p5h.json') as f:
    drc = json.load(f)

print("=== UNCONNECTED ITEMS ===")
for i, v in enumerate(drc.get('unconnected', []), 1):
    items = v.get('items', [])
    desc = v.get('description', '')
    print(f"\n{i}. {desc}")
    for item in items:
        d = item.get('description', '')
        pos = item.get('pos', {})
        x, y = pos.get('x', 0), pos.get('y', 0)
        print(f"   {d} @ ({x:.2f}, {y:.2f})")
