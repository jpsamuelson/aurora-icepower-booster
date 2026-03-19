#!/usr/bin/env python3
"""Find wire at (140, 37.62) — the dangling wire endpoint."""
import re, math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

print("Wires near (140, 37.62):")
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    for wx, wy in [(x1, y1), (x2, y2)]:
        if abs(wx - 140.0) < 2 and abs(wy - 37.62) < 2:
            length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            print(f"  ({x1},{y1})->({x2},{y2}), L={length:.4f}mm")
            break

# Also check what symbols/pins are at or near (140, 37.62)
print("\nSymbols near (140, 37.62):")
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    x, y = float(m.group(2)), float(m.group(3))
    if abs(x - 140.0) < 5 and abs(y - 37.62) < 5:
        start = m.start()
        chunk = text[start:start+1500]
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
        ref = ref_m.group(1) if ref_m else "?"
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', chunk)
        val = val_m.group(1) if val_m else "?"
        print(f"  {ref} ({val}) at ({x}, {y}), rot={m.group(4)}")

# U14 GND pin is at (140.0, 40.0 - (30.0 - 40.0))... no
# U14 at (140, 30). Looking at cache: there's a sub-unit with Pin 1 (GND) at local (0, 7.62) -> sch (140, 30 - 7.62) = (140, 22.38)
# Hmm that doesn't match 37.62

# Actually (140, 37.62) could be related to the #PWR010 at (140, 40). 
# GND pin of power:GND is at symbol position. #PWR010 at (140, 40).
# But 37.62 is 2.38 above 40.

print("\nU14 pin near y=37.62:")
print("  U14 center at (140, 30)")
print("  None of the ADP7118 pins are at y=37.62")
print()

# The wire at (140, 37.62) is a leftover / orphan wire in the U14 area
# It's near #PWR010 (GND at 140, 40). 
# Let me check the wire UUID
uuid = "c4a53c4d-ceb6-4f4c-be69-3f14d041bca2"
idx = text.find(uuid)
if idx >= 0:
    # Find the wire block containing this UUID
    start = text.rfind('(wire', max(0, idx-200), idx)
    end = text.find('))', idx) + 2
    raw = text[start:end]
    print(f"Raw wire block:\n  {raw}")
