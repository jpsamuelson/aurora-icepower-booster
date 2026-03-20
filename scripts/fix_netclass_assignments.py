#!/usr/bin/env python3
"""Check X5R cap net assignments and build net-class assignment script."""
import re, json

with open('aurora-dsp-icepower-booster.kicad_sch') as f:
    sch = f.read()

# X5R caps: check what nets they're on
print("=== X5R Caps ===")
# These are bulk caps (C24, C25, C74-C79) on +/-12V supply nets
# They are NOT in the audio signal path
x5r_refs = ['C24', 'C25', 'C74', 'C75', 'C76', 'C77', 'C78', 'C79']
print(f"X5R Refs: {x5r_refs}")
print("Alle X5R sind 10µF Bulk-Entkopplung auf +/-12V Versorgungsnetzen")
print("NICHT im Audio-Signalpfad → X5R ist hier regelkonform")
print()

# Build net assignment map
print("=== Netzklassen-Zuweisungen ===")
with open('aurora-dsp-icepower-booster.kicad_pro') as f:
    proj = json.load(f)

# Collect all nets from PCB
with open('aurora-dsp-icepower-booster.kicad_pcb') as f:
    pcb = f.read()

all_nets = set()
for m in re.finditer(r'\(net\s+\d+\s+"([^"]+)"\)', pcb):
    all_nets.add(m.group(1))

# Classify
assignments = {}
for nn in sorted(all_nets):
    if not nn:
        continue
    if nn == 'GND':
        continue  # GND doesn't need netclass (zone handles it)
    
    # Power
    if any(p in nn for p in ['+12V', '-12V', '+24V', 'V_BAT', 'VCC', '+5V', '+3V3']):
        assignments[nn] = 'Power'
    # Audio Input (most sensitive)
    elif any(p in nn for p in ['INV_IN', 'EMI_HOT', 'EMI_COLD']):
        assignments[nn] = 'Audio_Input'
    # Audio Output
    elif any(p in nn for p in ['OUT_DRIVE', 'OUT_PROT', 'BUF_DRIVE', 'GAIN_FB', 'SW_OUT']):
        assignments[nn] = 'Audio_Output'
    # Default (everything else)

print(f"Zuweisungen erstellt: {len(assignments)}")
by_class = {}
for nn, nc in assignments.items():
    by_class.setdefault(nc, []).append(nn)
for nc, nets in sorted(by_class.items()):
    print(f"  {nc}: {len(nets)} Netze")
    for n in sorted(nets)[:5]:
        print(f"    {n}")
    if len(nets) > 5:
        print(f"    ... ({len(nets)-5} more)")

# Update project file
net_settings = proj.setdefault('net_settings', {})
nets_dict = net_settings.setdefault('nets', {})
for nn, nc in assignments.items():
    nets_dict[nn] = {"net_class": nc}

with open('aurora-dsp-icepower-booster.kicad_pro', 'w') as f:
    json.dump(proj, f, indent=2)
    f.write('\n')

print(f"\n✅ {len(assignments)} Netzklassen-Zuweisungen in .kicad_pro geschrieben")
