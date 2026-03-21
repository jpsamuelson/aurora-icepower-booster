#!/usr/bin/env python3
"""Analyze latest DRC results."""
import json, sys
from collections import Counter

f = sys.argv[1] if len(sys.argv) > 1 else '/tmp/drc_p8c.json'
with open(f) as fh:
    drc = json.load(fh)

vtype = Counter()
vsev = Counter()
for v in drc.get('violations', []):
    vtype[v['type']] += 1
    vsev[v['severity']] += 1

print(f'=== DRC: {f} ===')
print(f'Violations: {sum(vtype.values())}  Unconnected: {len(drc.get("unconnected_items",[]))}')
print(f'\nBy type:')
for t, c in vtype.most_common():
    print(f'  {c:3d} {t}')
print(f'\nBy severity:')
for s, c in vsev.most_common():
    print(f'  {c:3d} {s}')

errors = [v for v in drc.get('violations', []) if v['severity'] == 'error']
if errors:
    print(f'\n=== {len(errors)} ERRORS ===')
    for v in errors:
        items = ' | '.join(
            f"{i.get('refdes','')} net={i.get('net','')} ({i.get('pos',{}).get('x',0):.1f},{i.get('pos',{}).get('y',0):.1f})"
            for i in v.get('items', [])
        )
        print(f"  {v['type']}: {v.get('description','')[:120]}")
        print(f"    {items}")
