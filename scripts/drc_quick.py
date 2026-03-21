#!/usr/bin/env python3
"""Quick DRC summary."""
import json
with open('/tmp/drc_v3.json') as f:
    data = json.load(f)
counts = {}
for v in data.get('violations', []):
    t = v.get('type', 'unknown')
    s = v.get('severity', 'unknown')
    key = f'{s}:{t}'
    counts[key] = counts.get(key, 0) + 1
for k in sorted(counts.keys()):
    print(f'  {counts[k]:4d}  {k}')
print(f'  Unconnected: {len(data.get("unconnected_items", []))}')
