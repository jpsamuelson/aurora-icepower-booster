#!/usr/bin/env python3
"""Get exact pad dimensions from PCB."""
import re

with open("aurora-dsp-icepower-booster.kicad_pcb") as f:
    pcb = f.read()

# Check format
print(f"PCB file lines: {pcb.count(chr(10))}")
print(f"PCB file size: {len(pcb)} bytes")

# Try to find a footprint with its pads
# First, find where R1 is
idx = pcb.find('(property "Reference" "R1"')
if idx < 0:
    print("R1 not found!")
else:
    # Show context around R1
    # Go backwards to find footprint start
    fp_start = pcb.rfind('(footprint "', 0, idx)
    print(f"\nR1 found at offset {idx}, footprint starts at {fp_start}")
    # Show 200 chars around fp_start
    snippet = pcb[fp_start:fp_start+300]
    print(f"Snippet: {snippet[:200]}...")

# Try raw pad search
print("\n--- First 5 pad matches in file ---")
pads = list(re.finditer(r'\(pad "([^"]*)" (\w+) (\w+) \(at ([\d.-]+) ([\d.-]+)', pcb))
print(f"Total pads found: {len(pads)}")
for p in pads[:5]:
    # Find size after this pad
    after = pcb[p.end():p.end()+100]
    size_m = re.search(r'\(size ([\d.]+) ([\d.]+)\)', after)
    sz = f"{size_m.group(1)}x{size_m.group(2)}" if size_m else "?"
    print(f"  Pad '{p.group(1)}' {p.group(2)} {p.group(3)} at=({p.group(4)},{p.group(5)}) size={sz}")
