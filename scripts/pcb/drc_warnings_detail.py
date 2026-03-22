#!/usr/bin/env python3
"""Detaillierte DRC-Warning-Analyse: alle Kategorien mit konkreten Positionen/Refs."""
import json
from collections import defaultdict

DRC = '/tmp/aurora-drc-routed.json'
with open(DRC) as f:
    data = json.load(f)

violations = data.get('violations', [])
unconnected = data.get('unconnected_items', [])

# ── 1. Gruppieren nach Typ ──
by_type = defaultdict(list)
for v in violations:
    by_type[v.get('type','?')].append(v)

for vtype, items in sorted(by_type.items()):
    sev = items[0].get('severity', '?')
    print(f"\n{'='*70}")
    print(f"  {vtype} ({len(items)}x, severity={sev})")
    print(f"{'='*70}")
    for i, v in enumerate(items):
        descs = [it.get('description','?') for it in v.get('items',[])]
        positions = [(it.get('pos',{}).get('x',0), it.get('pos',{}).get('y',0)) for it in v.get('items',[])]
        for j, (d, p) in enumerate(zip(descs, positions)):
            marker = "  → " if j > 0 else f"  [{i+1:3d}] "
            print(f"{marker}{d}  @ ({p[0]:.2f}, {p[1]:.2f})")

# ── 2. Unconnected ──
print(f"\n{'='*70}")
print(f"  UNCONNECTED ({len(unconnected)}x)")
print(f"{'='*70}")
for i, u in enumerate(unconnected):
    descs = [it.get('description','?') for it in u.get('items',[])]
    positions = [(it.get('pos',{}).get('x',0), it.get('pos',{}).get('y',0)) for it in u.get('items',[])]
    for j, (d, p) in enumerate(zip(descs, positions)):
        marker = "  → " if j > 0 else f"  [{i+1:3d}] "
        print(f"{marker}{d}  @ ({p[0]:.2f}, {p[1]:.2f})")
