#!/usr/bin/env python3
"""Analyze remaining silk warnings in detail."""
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/drc_p3.json'
with open(path) as f:
    drc = json.load(f)

violations = drc.get('violations', [])
for v in violations:
    typ = v.get('type', '?')
    sev = v.get('severity', '?')
    items = v.get('items', [])
    descs = []
    for i in items:
        d = i.get('description', '')
        pos = i.get('pos', {})
        pos_str = f" @ ({pos.get('x',0):.1f}, {pos.get('y',0):.1f})" if pos else ""
        descs.append(f"{d}{pos_str}")
    print(f"{sev}:{typ}")
    for d in descs:
        print(f"  {d}")
    print()
