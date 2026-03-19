#!/usr/bin/env python3
"""Final context: check exactly SS_U14 label, #PWR001 neighborhood, C22 context,
and the dangling wire fragment."""

import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, "r") as f:
    text = f.read()

# Parse ALL wires
wires = []
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    wires.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))))

def wire_endpoints_at(x, y, tol=0.01):
    hits = []
    for x1, y1, x2, y2 in wires:
        if abs(x1-x) < tol and abs(y1-y) < tol:
            hits.append(('start', x1, y1, x2, y2))
        if abs(x2-x) < tol and abs(y2-y) < tol:
            hits.append(('end', x1, y1, x2, y2))
    return hits

# ===== 1. Find SS_U14 label exact text in .kicad_sch =====
print("=" * 70)
print("1. SS_U14 Label — Raw .kicad_sch Text")
print("=" * 70)
idx = text.find('"SS_U14"')
if idx >= 0:
    # Show surrounding context
    # Find the enclosing (label ...) block
    start = text.rfind('(label', max(0, idx-100), idx)
    if start >= 0:
        # Find matching close paren
        depth = 0
        end = start
        for i in range(start, min(start+500, len(text))):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        raw = text[start:end]
        print(f"  Raw: {raw}")

# ===== 2. #PWR001 area at (98.0, 21.19) — what should connect? =====
print("\n" + "=" * 70)
print("2. #PWR001 Area — What's near (98.0, 21.19)?")
print("=" * 70)

# Find all symbols near (98, 21)
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    lib_id = m.group(1)
    x, y = float(m.group(2)), float(m.group(3))
    if abs(x - 98.0) < 15 and abs(y - 21.19) < 15:
        start = m.start()
        chunk = text[start:start+1500]
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', chunk)
        ref = ref_m.group(1) if ref_m else "?"
        val = val_m.group(1) if val_m else "?"
        print(f"  {ref} ({val}) at ({x}, {y}) — lib_id={lib_id}")

# Find labels near (98, 21.19)
for m in re.finditer(r'\(label\s+"([^"]+)"\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
    lx, ly = float(m.group(2)), float(m.group(3))
    if abs(lx - 98.0) < 15 and abs(ly - 21.19) < 15:
        print(f"  Label '{m.group(1)}' at ({lx}, {ly})")

# Find power symbols near (98, 21.19)
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"(power:[^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
    x, y = float(m.group(2)), float(m.group(3))
    if abs(x - 98.0) < 15 and abs(y - 21.19) < 10:
        start = m.start()
        chunk = text[start:start+1500]
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
        ref = ref_m.group(1) if ref_m else "?"
        print(f"  Power {ref} ({m.group(1)}) at ({x}, {y})")

# Wires near (98, 21.19)
print(f"\n  Wires near (98, 21.19):")
for x1, y1, x2, y2 in wires:
    for wx, wy in [(x1, y1), (x2, y2)]:
        if abs(wx - 98.0) < 5 and abs(wy - 21.19) < 5:
            print(f"    ({x1},{y1})→({x2},{y2})")
            break

# ===== 3. C22 Pin 1 context — what net should it connect to? =====
print("\n" + "=" * 70)
print("3. C22 Pin 1 at (147.62, 34.19) — What should connect?")
print("=" * 70)

# What's near Pin 1 at (147.62, 34.19)?
print("  Symbols near C22 Pin 1:")
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    x, y = float(m.group(2)), float(m.group(3))
    if abs(x - 147.62) < 10 and abs(y - 34.19) < 10:
        start = m.start()
        chunk = text[start:start+1500]
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', chunk)
        ref = ref_m.group(1) if ref_m else "?"
        val = val_m.group(1) if val_m else "?"
        print(f"    {ref} ({val}) at ({x}, {y})")

# Wires near C22 Pin 1
print(f"\n  Wires near (147.62, 34.19):")
for x1, y1, x2, y2 in wires:
    for wx, wy in [(x1, y1), (x2, y2)]:
        if abs(wx - 147.62) < 5 and abs(wy - 34.19) < 5:
            print(f"    ({x1},{y1})→({x2},{y2})")
            break

# Labels near C22 Pin 1
print(f"\n  Labels near (147.62, 34.19):")
for m in re.finditer(r'\(label\s+"([^"]+)"\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
    lx, ly = float(m.group(2)), float(m.group(3))
    if abs(lx - 147.62) < 10 and abs(ly - 34.19) < 10:
        print(f"    '{m.group(1)}' at ({lx}, {ly})")

# What's C22 Pin 2 connected to?
print(f"\n  C22 Pin 2 at (147.62, 41.81):")
ep = wire_endpoints_at(147.62, 41.81)
for e in ep:
    other_x = e[3] if e[0] == 'start' else e[1]
    other_y = e[4] if e[0] == 'start' else e[2]
    print(f"    Wire → ({other_x}, {other_y})")
    # What's at the other end?
    ep2 = wire_endpoints_at(other_x, other_y)
    for e2 in ep2:
        if e2[1:] != e[1:]:  # Different wire
            print(f"      Then → ({e2[3] if e2[0]=='start' else e2[1]}, {e2[4] if e2[0]=='start' else e2[2]})")

# What's at (147.62, 43.0)?
print(f"\n  What's at (147.62, 43.0)?")
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"(power:[^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
    x, y = float(m.group(2)), float(m.group(3))
    if abs(x - 147.62) < 1 and abs(y - 43.0) < 1:
        start = m.start()
        chunk = text[start:start+1500]
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
        print(f"    Power {ref_m.group(1) if ref_m else '?'} ({m.group(1)}) at ({x}, {y})")

# ===== 4. Check U14 area — all capacitors =====
print("\n" + "=" * 70)
print("4. All Capacitors near U14 (120-160, 20-50)")
print("=" * 70)
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"Device:C"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    x, y, rot = float(m.group(1)), float(m.group(2)), int(m.group(3))
    if 120 < x < 160 and 20 < y < 50:
        start = m.start()
        chunk = text[start:start+1500]
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', chunk)
        ref = ref_m.group(1) if ref_m else "?"
        val = val_m.group(1) if val_m else "?"
        print(f"  {ref} ({val}) at ({x}, {y}), rot={rot}°")

# ===== 5. Dangling wire (W5) — Find tiny wires =====
print("\n" + "=" * 70)
print("5. Dangling Wire Fragment (length ≤ 0.1mm)")
print("=" * 70)
import math
for x1, y1, x2, y2 in wires:
    length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    if length < 0.1:  # Less than 0.1mm
        print(f"  Tiny wire: ({x1},{y1})→({x2},{y2}), length={length:.4f}mm")
        # Check what's at each end
        ep1 = wire_endpoints_at(x1, y1)
        ep2 = wire_endpoints_at(x2, y2)
        print(f"    Start connects to {len(ep1)-1} other wires")
        print(f"    End connects to {len(ep2)-1} other wires")

# Also check for wires with length 0.0238 as reported
for x1, y1, x2, y2 in wires:
    length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    if 0.02 < length < 0.03:
        print(f"  ~0.024mm wire: ({x1},{y1})→({x2},{y2}), length={length:.4f}mm")

# ===== 6. Check what net U14 VOUT is on =====
print("\n" + "=" * 70)
print("6. U14 Output Area — V+ net connections")
print("=" * 70)
# Where is U14 Pin 1 (VOUT)?
# U14 at (140, 30), Pin 1 position depends on cache
# Find ADP7118ARDZ pin positions
cache_start = text.find('(lib_symbols')
adp_idx = text.find('"ADP7118ARDZ"', cache_start)
if adp_idx >= 0:
    chunk = text[adp_idx:adp_idx+5000]
    # Find the main symbol unit pins
    # Looking for unit 0 (the first one) pins
    pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+\d+)?\).*?\(name\s+"([^"]+)".*?\(number\s+"(\d+)"', chunk)
    print("  ADP7118ARDZ pin positions (local coords, first unit):")
    for ptype, px, py, pname, pnum in pins:
        # U14 at (140, 30), rotation 0
        # schematic = symbol + local (with Y inversion)
        sch_x = 140.0 + float(px)
        sch_y = 30.0 - float(py)
        print(f"    Pin {pnum} ({pname}, {ptype}): local ({px}, {py}) → sch ({sch_x:.2f}, {sch_y:.2f})")
