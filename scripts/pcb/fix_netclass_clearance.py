#!/usr/bin/env python3
"""
Fix netclass clearances to match DRU rules so Freerouting respects them.
- Power clearance: 0.2 → 0.25 (match power_clearance DRU)
- Add HV netclass: clearance 0.5mm (for +24V_IN)
- Move +24V patterns from Power to HV
"""
import json, os

PRO = 'aurora-dsp-icepower-booster.kicad_pro'

with open(PRO) as f:
    pro = json.load(f)

ns = pro['net_settings']
classes = ns['classes']

# 1. Fix Power clearance: 0.2 → 0.25
for cls in classes:
    if cls['name'] == 'Power':
        old = cls['clearance']
        cls['clearance'] = 0.25
        print(f"Power.clearance: {old} → {cls['clearance']}")
        break

# 2. Add HV netclass if not present
hv_exists = any(c['name'] == 'HV' for c in classes)
if not hv_exists:
    hv_class = {
        "bus_width": 12.0,
        "clearance": 0.5,
        "color": "",
        "line_style": 0,
        "micro_via_diameter": 0.3,
        "micro_via_drill": 0.1,
        "name": "HV",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "track_width": 0.5,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6.0
    }
    classes.append(hv_class)
    print(f"Added HV netclass: clearance=0.5, track_width=0.5")
else:
    for cls in classes:
        if cls['name'] == 'HV':
            cls['clearance'] = 0.5
            print(f"HV.clearance set to 0.5")

# 3. Update patterns: move +24V* from Power to HV
patterns = ns.get('netclass_patterns', [])
updated = 0
for p in patterns:
    if p['pattern'] in ('+24V_IN', '+24V*'):
        old_cls = p['netclass']
        p['netclass'] = 'HV'
        print(f"Pattern '{p['pattern']}': {old_cls} → HV")
        updated += 1

if updated == 0:
    # Add pattern if missing
    patterns.append({'netclass': 'HV', 'pattern': '+24V_IN'})
    print("Added pattern +24V_IN → HV")

# Write back
with open(PRO, 'w') as f:
    json.dump(pro, f, indent=2)
    f.write('\n')

print(f"\n✅ Updated {PRO}")
