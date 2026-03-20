#!/usr/bin/env python3
"""Parse DRC JSON and summarize."""
import json, sys
from collections import Counter

path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/drc_p1.json'
with open(path) as f:
    drc = json.load(f)

violations = drc.get('violations', [])
unconnected = drc.get('unconnected_items', [])

types = Counter()
for v in violations:
    key = f"{v.get('severity','?')}:{v.get('type','?')}"
    types[key] += 1

print(f"Violations: {len(violations)}, Unconnected: {len(unconnected)}\n")
for k, c in types.most_common():
    print(f"  {c:4d}x {k}")
