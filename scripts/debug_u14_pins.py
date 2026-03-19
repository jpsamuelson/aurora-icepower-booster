#!/usr/bin/env python3
"""Debug U14 ADP7118ARDZ pins — extract from lib_symbols cache."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, 'r') as f:
    content = f.read()

cache_start = content.find('(lib_symbols')
cache_text = content[cache_start:]

# Find ADP7118 block
idx = cache_text.find('ADP7118')
print(f"ADP7118 at offset {idx}")

block_start = cache_text.rfind('(symbol', 0, idx)
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
block = cache_text[block_start:i+1]
print(f"Block: {len(block)} chars")

# Print raw pin data
print("\n--- All (pin lines ---")
for m in re.finditer(r'\(pin\s', block):
    snippet = block[m.start():m.start()+250]
    # Find end of this pin  
    d = 0
    for j, ch in enumerate(snippet):
        if ch == '(': d += 1
        elif ch == ')':
            d -= 1
            if d == 0:
                snippet = snippet[:j+1]
                break
    print(f"  {snippet}")

# U14 at (140, 30), rot 0°
sym_x, sym_y = 140.0, 30.0
print(f"\n--- Schematic pin positions (symbol at {sym_x}, {sym_y}) ---")
for m in re.finditer(r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)\s+\(length\s+([-\d.]+)\)', block):
    lx, ly, angle, length = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    # Get name and number
    rest = block[m.start():m.start()+300]
    name_m = re.search(r'\(name "([^"]+)"', rest)
    num_m = re.search(r'\(number "([^"]+)"', rest)
    name = name_m.group(1) if name_m else "?"
    num = num_m.group(1) if num_m else "?"
    
    sch_x = sym_x + lx
    sch_y = sym_y - ly
    side = "left" if lx < 0 else "right"
    print(f"  Pin {num:>2} ({name:>10}) local=({lx:>7.2f}, {ly:>6.2f}) → sch=({sch_x:.2f}, {sch_y:.2f}) [{side}]")

# Now check which wires touch each pin
print("\n--- Wire connections ---")
wires = re.findall(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', content)
for m in re.finditer(r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', block):
    lx, ly, angle = float(m.group(1)), float(m.group(2)), float(m.group(3))
    rest = block[m.start():m.start()+300]
    name_m = re.search(r'\(name "([^"]+)"', rest)
    num_m = re.search(r'\(number "([^"]+)"', rest)
    name = name_m.group(1) if name_m else "?"
    num = num_m.group(1) if num_m else "?"
    
    sch_x = sym_x + lx
    sch_y = sym_y - ly
    
    found = []
    for x1, y1, x2, y2 in wires:
        x1f, y1f, x2f, y2f = float(x1), float(y1), float(x2), float(y2)
        if (abs(x1f - sch_x) < 0.01 and abs(y1f - sch_y) < 0.01):
            found.append(f"start of ({x1},{y1})→({x2},{y2})")
        if (abs(x2f - sch_x) < 0.01 and abs(y2f - sch_y) < 0.01):
            found.append(f"end of ({x1},{y1})→({x2},{y2})")
    
    status = "✅" if found else "❌ NONE"
    print(f"  Pin {num:>2} ({name:>10}) at ({sch_x:.2f}, {sch_y:.2f}): {status}")
    for f in found:
        print(f"       {f}")
