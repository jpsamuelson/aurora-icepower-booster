#!/usr/bin/env python3
"""Debug C22 connectivity: find position, pin locations, and nearby wires."""
import re, math

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

# Find C22 symbol instance
pos = 0
c22_block = None
while True:
    idx = t.find('(symbol (lib_id "Device:C")', pos)
    if idx == -1:
        break
    block = extract_balanced(t, idx)
    if block and '"C22"' in block:
        c22_block = block
        break
    pos = idx + 1

if not c22_block:
    print("C22 not found!")
    exit(1)

# Get C22 position and rotation
at_m = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?\)', c22_block)
cx, cy = float(at_m.group(1)), float(at_m.group(2))
rot = float(at_m.group(3)) if at_m.group(3) else 0
print(f"C22 position: ({cx}, {cy}), rotation: {rot}°")

# Device:C pin positions (from lib_symbols cache)
# Pin 1: local (0, 1.016) — typically top
# Pin 2: local (0, -1.016) — typically bottom
# But let me find the actual pin positions from the cache
cache_m = re.search(r'\(symbol "Device:C"', t)
if cache_m:
    cache_block = extract_balanced(t, cache_m.start())
    # Find pins in sub-symbols (C_1_1)
    for pm in re.finditer(r'\(pin\s+(\w+)\s+\w+\s*\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+\d+)?\)', cache_block):
        pin_type = pm.group(1)
        px, py = float(pm.group(2)), float(pm.group(3))
        num_m = re.search(r'\(number\s+"(\d+)"', cache_block[pm.start():pm.start()+200])
        num = num_m.group(1) if num_m else '?'
        
        # Calculate schematic position
        rad = math.radians(rot)
        sx = cx + px * math.cos(rad) - py * math.sin(rad)
        # KiCad Y-axis: schematic_y = symbol_y - rotated_y
        sy = cy - (px * math.sin(rad) + py * math.cos(rad))
        
        print(f"  Pin {num} ({pin_type}): local ({px}, {py}) → schematic ({sx:.2f}, {sy:.2f})")

# Find wires near C22
print(f"\n--- Wires near C22 (x={cx-10:.0f}-{cx+10:.0f}, y={cy-10:.0f}-{cy+10:.0f}) ---")
for m in re.finditer(r'\(wire\s*\(pts\s*\(xy\s+([\d.]+)\s+([\d.]+)\)\s*\(xy\s+([\d.]+)\s+([\d.]+)\)\)', t):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    if (cx-10 < x1 < cx+10 or cx-10 < x2 < cx+10) and (cy-10 < y1 < cy+10 or cy-10 < y2 < cy+10):
        print(f"  Wire ({x1},{y1})→({x2},{y2})")

# Find GND/#PWR symbols near C22
print(f"\n--- Power symbols near C22 ---")
for m in re.finditer(r'\(symbol\s*\(lib_id\s+"power:(GND|VCC|PWR_FLAG)"', t):
    block = extract_balanced(t, m.start())
    at_m2 = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)', block)
    if at_m2:
        px, py = float(at_m2.group(1)), float(at_m2.group(2))
        if abs(px - cx) < 10 and abs(py - cy) < 10:
            ref_m = re.search(r'"Reference"\s+"([^"]+)"', block)
            ref = ref_m.group(1) if ref_m else '?'
            print(f"  {ref} ({m.group(1)}) at ({px}, {py})")

# Also check for V+ net label near C22
print(f"\n--- Net labels near C22 ---")
for m in re.finditer(r'\(net_label\s+"([^"]+)"\s*\(at\s+([\d.]+)\s+([\d.]+)', t):
    lx, ly = float(m.group(2)), float(m.group(3))
    if abs(lx - cx) < 15 and abs(ly - cy) < 15:
        print(f"  Label '{m.group(1)}' at ({lx}, {ly})")

# Also search for hierarchical/global labels
for m in re.finditer(r'\((?:hierarchical_label|global_label|label)\s+"([^"]+)"\s*\(at\s+([\d.]+)\s+([\d.]+)', t):
    lx, ly = float(m.group(2)), float(m.group(3))
    if abs(lx - cx) < 15 and abs(ly - cy) < 15:
        print(f"  Label '{m.group(1)}' at ({lx}, {ly})")
