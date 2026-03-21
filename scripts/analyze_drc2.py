#!/usr/bin/env python3
"""Analyze DRC violations from latest run."""
import json, re

with open('/tmp/drc_final2.json') as f:
    data = json.load(f)

counts = {}
for v in data.get('violations', []):
    t = v.get('type', 'unknown')
    s = v.get('severity', 'unknown')
    key = f'{s}:{t}'
    counts[key] = counts.get(key, 0) + 1
print("=== Summary ===")
for k in sorted(counts.keys()):
    print(f'  {counts[k]:4d}  {k}')
print(f'  Unconnected: {len(data.get("unconnected_items", []))}')

# Details for each category
for vtype in ['courtyards_overlap', 'silk_edge_clearance', 'silk_over_copper', 'silk_overlap']:
    vs = [v for v in data['violations'] if v['type'] == vtype]
    if vs:
        print(f'\n=== {vtype} ({len(vs)}) ===')
        for v in vs[:10]:
            items = v.get('items', [])
            descs = [it.get('description', '')[:120] for it in items]
            pos_strs = []
            for it in items:
                pos = it.get('pos', {})
                if pos:
                    pos_strs.append(f"({pos.get('x',0):.1f}, {pos.get('y',0):.1f})")
            print(f'  {" | ".join(descs)}  {" ".join(pos_strs)}')
        if len(vs) > 10:
            print(f'  ... +{len(vs)-10} more')
