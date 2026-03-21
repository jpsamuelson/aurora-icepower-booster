#!/usr/bin/env python3
"""Analyze DRC results."""
import json
from collections import Counter

with open('/tmp/drc_p8b.json') as f:
    drc = json.load(f)

vtype = Counter()
vsev = Counter()
for v in drc.get('violations', []):
    vtype[v['type']] += 1
    vsev[v['severity']] += 1

print('=== Violations by type ===')
for t, c in vtype.most_common():
    print(f'  {c:3d} {t}')
print(f'\n=== By severity ===')
for s, c in vsev.most_common():
    print(f'  {c:3d} {s}')

print(f'\n=== ERRORS ===')
for v in drc.get('violations', []):
    if v['severity'] == 'error':
        items_str = ' | '.join(
            f"{i.get('refdes','')} net={i.get('net','')} ({i.get('pos',{}).get('x',0):.1f},{i.get('pos',{}).get('y',0):.1f})"
            for i in v.get('items', [])
        )
        print(f"  {v['type']}: {v.get('description','')[:100]}")
        print(f"    {items_str}")

print(f'\n=== Unconnected ({len(drc.get("unconnected_items",[]))}) ===')
for u in drc.get('unconnected_items', []):
    items = u.get('items', [])
    if items:
        nets = [i.get('net', '') for i in items]
        pos = [(i.get('pos',{}).get('x',0), i.get('pos',{}).get('y',0)) for i in items]
        print(f'  nets={nets} pos={pos}')
