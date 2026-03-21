#!/usr/bin/env python3
"""Remove ALL severity ignore overrides from .kicad_pro, restoring defaults."""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRO_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pro')

with open(PRO_FILE) as f:
    pro = json.load(f)

rs = pro['board']['design_settings']['rule_severities']

# Find and fix all ignores
fixed = []
for k, v in rs.items():
    if v == 'ignore':
        fixed.append(k)
        # Restore to KiCad defaults
        defaults = {
            'courtyards_overlap': 'error',
            'footprint_filters_mismatch': 'warning',
            'footprint_type_mismatch': 'error',
            'lib_footprint_mismatch': 'warning',
            'missing_courtyard': 'warning',
            'npth_inside_courtyard': 'warning',
            'pth_inside_courtyard': 'warning',
            'silk_edge_clearance': 'warning',
            'silk_over_copper': 'warning',
            'silk_overlap': 'warning',
        }
        rs[k] = defaults.get(k, 'warning')

print(f"Restored {len(fixed)} rules from 'ignore' to default:")
for k in fixed:
    print(f"  {k}: ignore → {rs[k]}")

with open(PRO_FILE, 'w') as f:
    json.dump(pro, f, indent=2)
    f.write('\n')
print(f"\nSaved {PRO_FILE}")
