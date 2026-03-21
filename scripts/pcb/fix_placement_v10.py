#!/usr/bin/env python3
"""Fix v10: Final 5 errors — D1/C80 near J2/SW1, C20 near MH2."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

corrections = {
    # D1 at (38, 6) overlaps J2 at (30.47, 5.08) — move right/down
    'D1':  (48, 4, 0),       # Well clear of J2, left of DIP area
    # C80 near D1 — 4mm gap
    'C80': (52, 4, 90),      # Near D1 but outside SW1 area
    # C20 at (137, 4) overlaps MH2 at (141.73, 4) — move down
    'C20': (137, 8, 90),     # Same x, more y clearance from MH2
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
