#!/usr/bin/env python3
"""Find V+ network connections near U14/C22 area to determine correct routing for C22 Pin 1."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    t = f.read()

def extract_balanced(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

# Find U14 and its pins
print("=== U14 ADP7118ARDZ ===")
pos = 0
while True:
    idx = t.find('(symbol (lib_id "aurora-dsp-icepower-booster:ADP7118ARDZ")', pos)
    if idx == -1:
        idx = t.find('(symbol (lib_id "ADP7118ARDZ")', pos)
        if idx == -1:
            break
    block = extract_balanced(t, idx)
    if block and '"U14"' in block:
        at_m = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?\)', block)
        print(f"  Position: ({at_m.group(1)}, {at_m.group(2)}), Rot: {at_m.group(3) or 0}")
        break
    pos = idx + 1

# Find ALL power symbols in U14/C22 area (x=120-165, y=25-50)
print("\n=== Power symbols in U14 area ===")
for m in re.finditer(r'\(symbol\s*\(lib_id\s+"power:(\w+)"', t):
    block = extract_balanced(t, m.start())
    at_m = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)', block)
    if at_m:
        px, py = float(at_m.group(1)), float(at_m.group(2))
        if 120 < px < 165 and 25 < py < 50:
            ref_m = re.search(r'"Reference"\s+"([^"]+)"', block)
            ref = ref_m.group(1) if ref_m else '?'
            print(f"  {ref} ({m.group(1)}) at ({px}, {py})")

# Find ALL labels in the area
print("\n=== All labels in U14 area ===")
for label_type in ['label', 'global_label', 'hierarchical_label', 'net_label']:
    for m in re.finditer(rf'\({label_type}\s+"([^"]+)"\s*\(at\s+([\d.]+)\s+([\d.]+)', t):
        lx, ly = float(m.group(2)), float(m.group(3))
        if 120 < lx < 165 and 25 < ly < 50:
            print(f"  {label_type}: '{m.group(1)}' at ({lx}, {ly})")

# Find ALL wires in the area
print("\n=== All wires in U14 area (x=130-155, y=25-45) ===")
for m in re.finditer(r'\(wire\s*\(pts\s*\(xy\s+([\d.]+)\s+([\d.]+)\)\s*\(xy\s+([\d.]+)\s+([\d.]+)\)\)', t):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    if (130 < x1 < 155 or 130 < x2 < 155) and (25 < y1 < 45 or 25 < y2 < 45):
        print(f"  Wire ({x1},{y1})→({x2},{y2})")
