#!/usr/bin/env python3
"""Analyze errors from manual route."""
import json

with open('/tmp/drc_v2.json') as f:
    drc = json.load(f)

for v in drc.get('violations', []):
    sev = v.get('severity', '')
    vtype = v.get('type', '')
    if sev == 'error':
        print(f"\n{sev}: {vtype}")
        print(f"  {v.get('description', '')}")
        for item in v.get('items', []):
            d = item.get('description', '')
            pos = item.get('pos', {})
            x, y = pos.get('x', 0), pos.get('y', 0)
            print(f"    {d} @ ({x:.2f}, {y:.2f})")
