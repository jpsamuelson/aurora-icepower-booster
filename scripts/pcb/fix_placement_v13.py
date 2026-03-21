#!/usr/bin/env python3
"""Fix v13: Final 2 courtyard overlaps."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

corrections = {
    # D1 at (62, 22) overlaps SW2 DIP at (55, 28.45)
    # SW2 courtyard extends downward (y decreases) from 28.45
    # Move D1 further down (= lower y, toward board top edge)
    'D1':  (62, 18, 0),      # was y=22, move to y=18 (further from SW2)

    # C16 at (137, 14) overlaps C20 at (134, 10)
    # Move C16 up more
    'C16': (140, 14, 90),    # was (137, 14), move right
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
