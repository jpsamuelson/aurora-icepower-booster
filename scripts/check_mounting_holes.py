#!/usr/bin/env python3
"""Check for mounting holes in the PCB."""
import re

with open("aurora-dsp-icepower-booster.kicad_pcb") as f:
    pcb = f.read()

# 1. Search for MountingHole footprints
print("=== Mounting Hole Footprints ===")
for m in re.finditer(r'\(footprint "([^"]*)"', pcb):
    fp = m.group(1)
    if "ount" in fp or "ole" in fp.lower() or "MH" in fp:
        # Get position
        block_start = m.start()
        at_m = re.search(r'\(at ([\d.]+) ([\d.]+)', pcb[block_start:block_start+500])
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', pcb[block_start:block_start+2000])
        if at_m:
            print(f"  {fp} @ ({at_m.group(1)}, {at_m.group(2)}) ref={ref_m.group(1) if ref_m else '?'}")

# 2. Search for H references
print("\n=== H-References ===")
for m in re.finditer(r'\(property "Reference" "(H\d+)"', pcb):
    print(f"  {m.group(1)}")

# 3. Search for np_thru_hole pads (non-plated through holes)
print("\n=== Footprints with NPTH pads ===")
# Find footprints containing np_thru_hole
fp_starts = [(m.start(), m.group(1)) for m in re.finditer(r'\(footprint "([^"]+)"', pcb)]
for i, (start, fp_name) in enumerate(fp_starts):
    end = fp_starts[i+1][0] if i+1 < len(fp_starts) else len(pcb)
    block = pcb[start:end]
    npth = re.findall(r'np_thru_hole', block)
    if npth:
        at_m = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
        pos = f"({at_m.group(1)}, {at_m.group(2)})" if at_m else "?"
        ref = ref_m.group(1) if ref_m else "?"
        print(f"  {ref}: {fp_name} @ {pos} — {len(npth)} NPTH pads")

# 4. Components near corners
print("\n=== Components near board corners ===")
corners = [(0,0,"TL"), (145.554,0,"TR"), (0,200,"BL"), (145.554,200,"BR")]
for start, fp_name in fp_starts:
    block = pcb[start:start+3000]
    at_m = re.search(r'^\(footprint "[^"]+"\s+\(layer "[^"]+"\)\s+\(uuid "[^"]+"\)\s+\(at ([\d.]+) ([\d.]+)', block)
    ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
    if at_m:
        x, y = float(at_m.group(1)), float(at_m.group(2))
        ref = ref_m.group(1) if ref_m else "?"
        for cx, cy, label in corners:
            if abs(x-cx) < 8 and abs(y-cy) < 8:
                print(f"  {label}: {ref} ({fp_name}) @ ({x}, {y})")
