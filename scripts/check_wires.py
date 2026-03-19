#!/usr/bin/env python3
"""Check actual wires and labels near U1 and U14 in the schematic."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, 'r') as f:
    content = f.read()

print(f"Schematic size: {len(content)} chars")

# Extract all wires
wires = re.findall(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', content)
print(f"\nTotal wires: {len(wires)}")

# U1 at (80.0, 40.0) — look for wires near x=69..91, y=30..50
print("\n=== WIRES NEAR U1 (x: 50-95, y: 30-50) ===")
for x1, y1, x2, y2 in wires:
    x1f, y1f, x2f, y2f = float(x1), float(y1), float(x2), float(y2)
    if ((50 <= x1f <= 95 or 50 <= x2f <= 95) and 
        (30 <= y1f <= 50 or 30 <= y2f <= 50)):
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")

# U14 at (140.0, 30.0) — look for wires near x=125..155, y=18..40
print("\n=== WIRES NEAR U14 (x: 125-155, y: 18-40) ===")
for x1, y1, x2, y2 in wires:
    x1f, y1f, x2f, y2f = float(x1), float(y1), float(x2), float(y2)
    if ((125 <= x1f <= 155 or 125 <= x2f <= 155) and 
        (18 <= y1f <= 40 or 18 <= y2f <= 40)):
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")

# Extract all labels
labels = re.findall(r'\(label "([^"]+)" \(at ([\d.]+) ([\d.]+)', content)
print(f"\n=== LABELS NEAR U1 (x: 50-95, y: 30-50) ===")
for name, x, y in labels:
    xf, yf = float(x), float(y)
    if 50 <= xf <= 95 and 30 <= yf <= 50:
        print(f"  '{name}' at ({x}, {y})")

print(f"\n=== LABELS NEAR U14 (x: 125-155, y: 18-40) ===")
for name, x, y in labels:
    xf, yf = float(x), float(y)
    if 125 <= xf <= 155 and 18 <= yf <= 40:
        print(f"  '{name}' at ({x}, {y})")

# Extract power symbols near U1/U14
# Power symbols: GND, +12V, +24V_IN, etc.
pwr_syms = re.findall(r'\(symbol \(lib_id "power:([^"]+)"\) \(at ([\d.]+) ([\d.]+)', content)
print(f"\n=== POWER SYMBOLS NEAR U1 (x: 50-95, y: 30-50) ===")
for name, x, y in pwr_syms:
    xf, yf = float(x), float(y)
    if 50 <= xf <= 95 and 30 <= yf <= 50:
        print(f"  '{name}' at ({x}, {y})")

print(f"\n=== POWER SYMBOLS NEAR U14 (x: 125-155, y: 18-40) ===")
for name, x, y in pwr_syms:
    xf, yf = float(x), float(y)
    if 125 <= xf <= 155 and 18 <= yf <= 40:
        print(f"  '{name}' at ({x}, {y})")

# Also check for net labels (global_label)
glabels = re.findall(r'\(global_label "([^"]+)" \(at ([\d.]+) ([\d.]+)', content)
print(f"\n=== GLOBAL LABELS NEAR U1 ===")
for name, x, y in glabels:
    xf, yf = float(x), float(y)
    if 50 <= xf <= 95 and 30 <= yf <= 50:
        print(f"  '{name}' at ({x}, {y})")

print(f"\n=== GLOBAL LABELS NEAR U14 ===")
for name, x, y in glabels:
    xf, yf = float(x), float(y)
    if 125 <= xf <= 155 and 18 <= yf <= 40:
        print(f"  '{name}' at ({x}, {y})")

# Also check net labels (hierarchical)
hlabels = re.findall(r'\(hierarchical_label "([^"]+)" \(at ([\d.]+) ([\d.]+)', content)
if hlabels:
    print(f"\n=== HIERARCHICAL LABELS NEAR U1/U14 ===")
    for name, x, y in hlabels:
        xf, yf = float(x), float(y)
        if (50 <= xf <= 95 and 30 <= yf <= 50) or (125 <= xf <= 155 and 18 <= yf <= 40):
            print(f"  '{name}' at ({x}, {y})")

# Check for no_connect symbols near U1/U14
nconn = re.findall(r'\(no_connect \(at ([\d.]+) ([\d.]+)', content)
print(f"\n=== NO_CONNECT NEAR U1/U14 ===")
for x, y in nconn:
    xf, yf = float(x), float(y)
    if (50 <= xf <= 95 and 30 <= yf <= 50) or (125 <= xf <= 155 and 18 <= yf <= 40):
        print(f"  at ({x}, {y})")
