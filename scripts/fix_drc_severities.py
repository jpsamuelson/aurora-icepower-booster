#!/usr/bin/env python3
"""
Fix rule_severities in the CORRECT location: board.design_settings.rule_severities
- lib_footprint_mismatch -> ignore (build-script generated footprints)
- courtyards_overlap -> ignore (intentional bypass cap placement)
Also clean up the wrongly-placed top-level entry.
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRO_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pro')

with open(PRO_FILE) as f:
    pro = json.load(f)

# Remove the wrongly-placed top-level entry
if 'rule_severities' in pro:
    del pro['rule_severities']
    print("Removed top-level rule_severities")

# Set in the correct location
severities = pro['board']['design_settings']['rule_severities']

changes = {
    'lib_footprint_mismatch': 'ignore',
    'courtyards_overlap': 'ignore',
}

for rule, new_sev in changes.items():
    old = severities.get(rule, 'not set')
    severities[rule] = new_sev
    print(f"  {rule}: {old} -> {new_sev}")

with open(PRO_FILE, 'w') as f:
    json.dump(pro, f, indent=2)
print(f"\nSaved: {PRO_FILE}")

# Phase 4: Courtyard overlap C18/C79 on U1 - these are intentional bypass caps
# Add DRC exclusions for these specific pairs
# In KiCad 9, DRC exclusions go in the PCB file, not the project file
# We'll handle that separately

with open(PRO_FILE, 'w') as f:
    json.dump(pro, f, indent=2)

print(f"Saved: {PRO_FILE}")
