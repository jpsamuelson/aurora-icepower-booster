#!/usr/bin/env python3
"""Analyze DRC violations from JSON to plan fixes."""
import json, re

with open('/tmp/drc_nosuppress.json') as f:
    data = json.load(f)

# Analyze silk_overlap
print('=== silk_overlap (38) ===')
refs_overlap = {}
for v in data['violations']:
    if v['type'] == 'silk_overlap':
        for it in v.get('items', []):
            d = it.get('description', '')
            m = re.search(r'of (\w+)', d)
            if m:
                refs_overlap[m.group(1)] = refs_overlap.get(m.group(1), 0) + 1
for r in sorted(refs_overlap.keys()):
    print(f'  {r}: {refs_overlap[r]}')

# Analyze silk_edge_clearance
print('\n=== silk_edge_clearance (17) ===')
for v in data['violations']:
    if v['type'] == 'silk_edge_clearance':
        for it in v.get('items', []):
            print(f'  {it.get("description","")[:150]}')

# Analyze silk_over_copper
print('\n=== silk_over_copper (10) ===')
for v in data['violations']:
    if v['type'] == 'silk_over_copper':
        items = v.get('items', [])
        descs = [it.get('description','')[:120] for it in items]
        print(f'  {" | ".join(descs)}')

# Analyze courtyard overlaps
print('\n=== courtyards_overlap (2) ===')
for v in data['violations']:
    if v['type'] == 'courtyards_overlap':
        items = v.get('items', [])
        descs = [it.get('description','')[:120] for it in items]
        print(f'  {" | ".join(descs)}')
