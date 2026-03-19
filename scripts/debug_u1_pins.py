#!/usr/bin/env python3
"""
Debug: Check exact pin connection positions for U1 TEL5-2422.
The 'at' position in lib_symbols is the CONNECTION endpoint.
Pin length extends INWARD (toward body) from that point.
"""
import re, math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, 'r') as f:
    content = f.read()

# Find TEL5-2422 in lib_symbols cache
cache_start = content.find('(lib_symbols')
cache_text = content[cache_start:]

# Find the TEL5-2422 symbol block
tel_start = cache_text.find('"TEL5-2422"')
if tel_start < 0:
    tel_start = cache_text.find('TEL5')
print(f"TEL5-2422 found at offset {tel_start}")

# Extract all pins from the cache
# Extract the full TEL5-2422 block by bracket counting
block_start = cache_text.rfind('(symbol', 0, tel_start)
depth = 0
i = block_start
while i < len(cache_text):
    if cache_text[i] == '(':
        depth += 1
    elif cache_text[i] == ')':
        depth -= 1
        if depth == 0:
            break
    i += 1
tel_block = cache_text[block_start:i+1]
print(f"TEL5-2422 block: {len(tel_block)} chars")

# Find ALL pin definitions
# Pin format: (pin TYPE STYLE (at X Y ANGLE) (length LEN) ... (name "NAME") (number "NUM"))
pin_pattern = re.compile(
    r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)\s+\(length\s+([-\d.]+)\).*?\(name\s+"([^"]+)"\).*?\(number\s+"(\d+)"\)',
    re.DOTALL
)

pins = list(pin_pattern.finditer(tel_block))
print(f"Found {len(pins)} pins\n")

# U1 symbol position
sym_x, sym_y = 80.0, 40.0
sym_rot = 0  # degrees

print("Pin layout in lib_symbols cache:")
for m in pins:
    local_x, local_y = float(m.group(1)), float(m.group(2))
    pin_angle = float(m.group(3))
    pin_len = float(m.group(4))
    name = m.group(5)
    num = m.group(6)
    
    # The pin 'at' is the connection point in local coords
    # Schematic position (no symbol rotation for rot=0):
    sch_x = sym_x + local_x
    sch_y = sym_y - local_y  # Y inverted
    
    # Pin direction (angle determines which way the pin line extends into the body)
    # 0° = pin extends RIGHT (connection on left)
    # 180° = pin extends LEFT (connection on right)
    direction = "LEFT" if pin_angle == 0 else "RIGHT" if pin_angle == 180 else f"{pin_angle}°"
    side = "left" if local_x < 0 else "right"
    
    print(f"  Pin {num:>2} ({name:>12}) local=({local_x:>7.2f}, {local_y:>6.2f}) angle={pin_angle:>3.0f}° len={pin_len}")
    print(f"         → schematic ({sch_x:.2f}, {sch_y:.2f})  [{side} side, extends {direction}]")

print("\n--- Checking if wires touch these positions ---")
wires = re.findall(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', content)

for m in pins:
    local_x, local_y = float(m.group(1)), float(m.group(2))
    name, num = m.group(5), m.group(6)
    sch_x = sym_x + local_x
    sch_y = sym_y - local_y
    
    found_wires = []
    for x1, y1, x2, y2 in wires:
        x1f, y1f, x2f, y2f = float(x1), float(y1), float(x2), float(y2)
        # Check if any wire endpoint matches this pin position
        if (abs(x1f - sch_x) < 0.01 and abs(y1f - sch_y) < 0.01):
            found_wires.append(f"start: ({x1},{y1})→({x2},{y2})")
        if (abs(x2f - sch_x) < 0.01 and abs(y2f - sch_y) < 0.01):
            found_wires.append(f"end: ({x1},{y1})→({x2},{y2})")
    
    status = "✅" if found_wires else "❌"
    print(f"  Pin {num:>2} ({name:>12}) at ({sch_x:.2f}, {sch_y:.2f}): {status} {len(found_wires)} wires")
    for w in found_wires:
        print(f"       {w}")
