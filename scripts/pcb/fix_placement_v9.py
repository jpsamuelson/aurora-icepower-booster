#!/usr/bin/env python3
"""Fix v9: Final PSU position fixes for remaining 18 DRC errors."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

corrections = {
    # U14 caps: move further from U14 at (128, 8)
    'C16': (137, 12, 90),    # was (132, 12) — pad-to-pad short with U14
    'C20': (137, 4, 90),     # was (132, 4) — pad short with U14

    # D1/C80: move far from J1 at (70.87, 10.83) — J1 courtyard is huge
    # Place near J2 area at (30.47, 5.08) — enough room there
    'D1':  (38, 6, 0),       # was (62, 5) — still in J1 courtyard
    'C80': (42, 6, 90),      # was (66, 5) — still in J1 courtyard

    # C23 ↔ C15: too close at y=28,30. Move C23 further
    'C23': (85, 30, 90),     # was (80, 30) — 5mm from C15 at (80, 28)

    # C17 ↔ U1: C17 at (82, 12) marginally inside U1 courtyard
    'C17': (78, 12, 90),     # Move left, well outside U1 courtyard (x=83)
}

with open(PCB) as f:
    content = f.read()

for ref, (x, y, rot) in corrections.items():
    pat = rf'(\(property "Reference" "{re.escape(ref)}")'
    m = re.search(pat, content)
    if not m:
        print(f"NOT FOUND: {ref}")
        continue
    pos = m.start()
    fp_start = content.rfind('(footprint "', 0, pos)
    region = content[fp_start:pos]
    at_m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)', region)
    abs_s = fp_start + at_m.start()
    abs_e = fp_start + at_m.end()
    new_at = f'(at {x} {y} {rot})' if rot else f'(at {x} {y})'
    content = content[:abs_s] + new_at + content[abs_e:]
    print(f"  {ref}: → ({x}, {y})")

with open(PCB, 'w') as f:
    f.write(content)
print("Done.")
