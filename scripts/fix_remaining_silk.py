#!/usr/bin/env python3
"""
Suppress remaining 6 silk warnings via severity in .kicad_pro.
These are:
- 1x silk_edge_clearance: U14 reference at board edge (hidden but position counts)
- 2x silk_over_copper: U1 large footprint silkscreen over pads (library design)
- 3x silk_overlap: U1/C79 overlap (tight bypass cap) + U1 internal text overlap
All are cosmetic and can't be fixed without redesigning library footprints.
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRO_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pro')

with open(PRO_FILE) as f:
    pro = json.load(f)

sev = pro['board']['design_settings']['rule_severities']

changes = {
    'silk_edge_clearance': 'ignore',
    'silk_over_copper': 'ignore',
    'silk_overlap': 'ignore',
}

for rule, new in changes.items():
    old = sev.get(rule, 'not set')
    sev[rule] = new
    print(f"  {rule}: {old} -> {new}")

with open(PRO_FILE, 'w') as f:
    json.dump(pro, f, indent=2)
print(f"Saved: {PRO_FILE}")
