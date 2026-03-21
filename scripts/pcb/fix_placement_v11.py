#!/usr/bin/env python3
"""Fix v11: Final corrections for C16/C20, D1/C80 positions."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

# Check where SW1 is first
with open(PCB) as f:
    content = f.read()

m = re.search(r'(\(property "Reference" "SW1")', content)
if m:
    fp_start = content.rfind('(footprint "', 0, m.start())
    region = content[fp_start:m.start()]
    at_m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)', region)
    if at_m:
        print(f"SW1 at: ({at_m.group(1)}, {at_m.group(2)}, {at_m.group(3) or '0'})")

corrections = {
    # C16/C20 overlap at x=137 — increase y separation
    'C16': (137, 14, 90),    # was y=12, now y=14
    'C20': (137, 4, 90),     # was y=8, now y=4 (moved apart)

    # D1/C80 near SW1 — move to completely different area (y=30, below U1 zone)
    'D1':  (46, 30, 0),      # Far from SW1 and J1/J2
    'C80': (50, 30, 90),     # Near D1 but well separated
}

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
