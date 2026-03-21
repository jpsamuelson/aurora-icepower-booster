#!/usr/bin/env python3
"""Fix v12: D1/C80 near J1 below courtyard, C20 away from MH2."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

corrections = {
    # D1/C80: Place below J1 courtyard (y≈20), near power input
    # J1 at (70.87, 10.83), courtyard ends at ~y=17
    'D1':  (62, 22, 0),      # Below J1, away from SW areas
    'C80': (68, 22, 90),     # 6mm from D1, good clearance

    # C20 at (137, 4) → MH2 at (141.73, 4). Move left+down
    'C20': (134, 10, 90),    # x=134, y=10 — clear of MH2 (141.73, 4)
}

with open(PCB) as f:
    content = f.read()

for ref, (x, y, rot) in corrections.items():
    pat = rf'(\(property "Reference" "{re.escape(ref)}")'
    m = re.search(pat, content)
    fp_start = content.rfind('(footprint "', 0, m.start())
    region = content[fp_start:m.start()]
    at_m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)', region)
    abs_s = fp_start + at_m.start()
    abs_e = fp_start + at_m.end()
    new_at = f'(at {x} {y} {rot})' if rot else f'(at {x} {y})'
    content = content[:abs_s] + new_at + content[abs_e:]
    print(f"  {ref}: → ({x}, {y})")

with open(PCB, 'w') as f:
    f.write(content)
print("Done.")
