#!/usr/bin/env python3
"""Detailed analysis of U14 area — all wires, labels, symbols within x:120-160, y:15-45."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, 'r') as f:
    content = f.read()

# All wires in the U14 area (wider range)
wires = re.findall(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', content)
print("=== ALL WIRES in x:120-160, y:15-45 ===")
u14_wires = []
for x1, y1, x2, y2 in wires:
    x1f, y1f, x2f, y2f = float(x1), float(y1), float(x2), float(y2)
    if ((120 <= x1f <= 160 and 15 <= y1f <= 45) or 
        (120 <= x2f <= 160 and 15 <= y2f <= 45)):
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")
        u14_wires.append((x1, y1, x2, y2))

# All labels in area
labels = re.findall(r'\(label "([^"]+)" \(at ([\d.]+) ([\d.]+) (\d+)\)', content)
print("\n=== ALL LABELS in x:120-160, y:15-45 ===")
for name, x, y, rot in labels:
    xf, yf = float(x), float(y)
    if 120 <= xf <= 160 and 15 <= yf <= 45:
        print(f"  '{name}' at ({x}, {y}) rot={rot}")

# All power symbols in area
pwr_pattern = re.compile(r'\(symbol \(lib_id "power:([^"]+)"\) \(at ([\d.]+) ([\d.]+) (\d+)\)')
print("\n=== ALL POWER SYMBOLS in x:120-160, y:15-45 ===")
for m in pwr_pattern.finditer(content):
    name, x, y, rot = m.group(1), m.group(2), m.group(3), m.group(4)
    xf, yf = float(x), float(y)
    if 120 <= xf <= 160 and 15 <= yf <= 45:
        print(f"  'power:{name}' at ({x}, {y}) rot={rot}")

# Junction markers
junctions = re.findall(r'\(junction \(at ([\d.]+) ([\d.]+)\)', content)
print("\n=== JUNCTIONS in x:120-160, y:15-45 ===")
for x, y in junctions:
    xf, yf = float(x), float(y)
    if 120 <= xf <= 160 and 15 <= yf <= 45:
        print(f"  at ({x}, {y})")

# The U14 symbol itself
u14_match = re.search(r'\(symbol \(lib_id "[^"]*ADP7118[^"]*"\) \(at ([\d.]+) ([\d.]+) (\d+)\)', content)
if u14_match:
    print(f"\n=== U14 SYMBOL ===")
    print(f"  ADP7118 at ({u14_match.group(1)}, {u14_match.group(2)}) rot={u14_match.group(3)}")

# U1 symbol too
u1_match = re.search(r'\(symbol \(lib_id "[^"]*TEL5[^"]*"\) \(at ([\d.]+) ([\d.]+) (\d+)\)', content)
if u1_match:
    print(f"\n=== U1 SYMBOL ===") 
    print(f"  TEL5-2422 at ({u1_match.group(1)}, {u1_match.group(2)}) rot={u1_match.group(3)}")

# Let me also find all labels on +12V, +24V_IN line
print("\n=== ALL +12V LABELS ===")
for name, x, y, rot in labels:
    if name == '+12V':
        print(f"  '{name}' at ({x}, {y}) rot={rot}")

print("\n=== ALL +24V_IN, +24V LABELS ===")
for name, x, y, rot in labels:
    if '24V' in name:
        print(f"  '{name}' at ({x}, {y}) rot={rot}")
