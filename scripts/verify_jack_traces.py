#!/usr/bin/env python3
"""Verify J2/J15 pad positions and trace connectivity for REMOTE_IN."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    text = f.read()

# Find J2 and J15 positions
for ref in ["J2", "J15"]:
    # Find the footprint block
    pat = rf'\(footprint\s+"aurora-dsp-icepower-booster:AUDIO-SMD[^"]*"[^)]*\n\s*\(layer[^)]*\)\n\s*\(uuid[^)]*\)\n\s*\(at\s+([\d.]+)\s+([\d.]+)'
    for m in re.finditer(pat, text):
        fx, fy = float(m.group(1)), float(m.group(2))
        # Check if this is J2 or J15 by looking ahead for Reference
        block_start = m.start()
        block_snippet = text[block_start:block_start+500]
        if f'"Reference" "{ref}"' in block_snippet:
            print(f"{ref} at ({fx}, {fy})")
            # Calculate absolute pad positions
            pads = {
                "1": (4.15, -3.75),
                "2": (-4.15, 3.75),
                "3": (-1.15, 3.75),
                "4": (2.75, 3.75),
                "5": (-4.15, -3.75),
            }
            for pname, (dx, dy) in pads.items():
                ax, ay = fx + dx, fy + dy
                print(f"  Pad {pname}: ({ax:.2f}, {ay:.2f})")

# Find all REMOTE_IN traces (net 130)
print("\nREMOTE_IN traces (net 130):")
for m in re.finditer(r'\(segment\s*\n\s*\(start\s+([\d.]+)\s+([\d.]+)\)\s*\n\s*\(end\s+([\d.]+)\s+([\d.]+)\)\s*\n\s*\(width\s+[\d.]+\)\s*\n\s*\(layer\s+"([^"]+)"\)\s*\n\s*\(net\s+130\)', text):
    sx, sy = float(m.group(1)), float(m.group(2))
    ex, ey = float(m.group(3)), float(m.group(4))
    layer = m.group(5)
    print(f"  ({sx:.4f}, {sy:.4f}) -> ({ex:.4f}, {ey:.4f}) [{layer}]")

# Find REMOTE_IN vias
print("\nREMOTE_IN vias (net 130):")
for m in re.finditer(r'\(via\s*\n\s*\(at\s+([\d.]+)\s+([\d.]+)\)[^)]*\n[^)]*\n[^)]*\(net\s+130\)', text):
    vx, vy = float(m.group(1)), float(m.group(2))
    print(f"  via at ({vx:.4f}, {vy:.4f})")

# Find GND traces connecting to J2/J15 Pad4 area
print("\nGND traces near J2/J15 Pad4 (net 134):")
for m in re.finditer(r'\(segment\s*\n\s*\(start\s+([\d.]+)\s+([\d.]+)\)\s*\n\s*\(end\s+([\d.]+)\s+([\d.]+)\)\s*\n\s*\(width\s+[\d.]+\)\s*\n\s*\(layer\s+"([^"]+)"\)\s*\n\s*\(net\s+134\)', text):
    sx, sy = float(m.group(1)), float(m.group(2))
    ex, ey = float(m.group(3)), float(m.group(4))
    # Only show traces near the jack area (x < 40, y < 15)
    if (sx < 40 and sy < 15) or (ex < 40 and ey < 15):
        print(f"  ({sx:.4f}, {sy:.4f}) -> ({ex:.4f}, {ey:.4f}) [{m.group(5)}]")
