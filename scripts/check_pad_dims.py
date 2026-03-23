#!/usr/bin/env python3
"""Get exact pad dimensions from PCB file."""
import re

with open("aurora-dsp-icepower-booster.kicad_pcb") as f:
    pcb = f.read()

fp_types = ["R_0805", "C_0805", "C_1206", "C_1210", "C_0402", "MountingHole", "SW_E-Switch"]

for fp_type in fp_types:
    m = re.search(r'\(footprint "[^"]*' + fp_type + r'[^"]*"(.{5000})', pcb, re.DOTALL)
    if m:
        block = m.group(1)
        print(f"\n{fp_type}:")
        for pm in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+) \(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\) \(size ([\d.]+) ([\d.]+)\)', block):
            print(f"  Pad '{pm.group(1)}' {pm.group(2)} {pm.group(3)} at=({pm.group(4)},{pm.group(5)}) size=({pm.group(7)}x{pm.group(8)})")
    else:
        print(f"\n{fp_type}: not found")
