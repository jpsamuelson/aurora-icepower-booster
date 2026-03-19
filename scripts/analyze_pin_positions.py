#!/usr/bin/env python3
"""
Analyze U1 (TEL5-2422) and U14 (ADP7118ARDZ) pin positions.
Extracts:
1. Symbol instance position + rotation
2. lib_symbols cache pin definitions
3. Calculated schematic pin positions
4. Existing wires near the symbol
5. Existing labels/power symbols near the symbol
"""

import re, math, os

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, 'r') as f:
    content = f.read()

def extract_balanced_block(text, start_pos):
    """Extract balanced parentheses block starting at start_pos."""
    depth = 0
    i = start_pos
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start_pos:i+1]
        i += 1
    return None

def find_symbol_instance(text, ref):
    """Find symbol instance block by reference."""
    # Find (symbol (lib_id ...) (at ...) ... (property "Reference" "ref" ...))
    # Need to scan all top-level symbol blocks
    pattern = rf'\(symbol\s+\(lib_id\s+"[^"]*"\)'
    for m in re.finditer(pattern, text):
        block = extract_balanced_block(text, m.start())
        if block and f'"Reference" "{ref}"' in block:
            return block
    return None

def find_lib_cache(text, lib_id):
    """Find lib_symbols cache entry."""
    pattern = rf'\(symbol\s+"{re.escape(lib_id)}"'
    m = re.search(pattern, text)
    if m:
        return extract_balanced_block(text, m.start())
    return None

def get_pins_from_cache(cache_block):
    """Extract pin positions from lib_symbols cache."""
    pins = {}
    for m in re.finditer(r'\(pin\s+(\w+)\s+(\w+)\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\)[^)]*\(length\s+([-\d.]+)\).*?\(name\s+"([^"]*)"\).*?\(number\s+"([^"]*)"\)', cache_block, re.DOTALL):
        pin_type, pin_style, px, py, angle, length, name, number = m.groups()
        pins[number] = {
            "local_x": float(px), "local_y": float(py),
            "angle": int(angle), "name": name,
            "type": pin_type, "length": float(length)
        }
    return pins

def calc_schematic_pos(sx, sy, rot_deg, px, py):
    """Calculate schematic position of a pin."""
    theta = math.radians(rot_deg)
    rx = px * math.cos(theta) - py * math.sin(theta)
    ry = px * math.sin(theta) + py * math.cos(theta)
    return round(sx + rx, 2), round(sy - ry, 2)

def find_wires_near(text, cx, cy, radius=20):
    """Find all wires within radius of center point."""
    wires = []
    for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([-\d.]+)\s+([-\d.]+)\)\s*\(xy\s+([-\d.]+)\s+([-\d.]+)\)\)', text):
        x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
        d1 = math.sqrt((x1-cx)**2 + (y1-cy)**2)
        d2 = math.sqrt((x2-cx)**2 + (y2-cy)**2)
        if d1 < radius or d2 < radius:
            wires.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "pos": m.start()})
    return wires

def find_labels_near(text, cx, cy, radius=20):
    """Find all labels within radius."""
    labels = []
    for m in re.finditer(r'\(label\s+"([^"]*)"\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', text):
        name, x, y, angle = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))
        d = math.sqrt((x-cx)**2 + (y-cy)**2)
        if d < radius:
            labels.append({"name": name, "x": x, "y": y, "angle": angle, "dist": round(d, 2)})
    return labels

def find_power_symbols_near(text, cx, cy, radius=20):
    """Find power symbols near point."""
    results = []
    for m in re.finditer(r'\(symbol\s+\(lib_id\s+"(power:[^"]*)"\)\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', text):
        lib_id, x, y, angle = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))
        d = math.sqrt((x-cx)**2 + (y-cy)**2)
        if d < radius:
            block = extract_balanced_block(text, m.start())
            ref = ""
            if block:
                rm = re.search(r'"Reference"\s+"([^"]*)"', block)
                if rm: ref = rm.group(1)
            results.append({"lib_id": lib_id, "ref": ref, "x": x, "y": y, "angle": angle, "dist": round(d, 2)})
    return results

# ══════════════════════════════════════════════════
# U1 (TEL5-2422) Analysis
# ══════════════════════════════════════════════════
print("=" * 70)
print("U1 (TEL5-2422) — Pin-Position-Analyse")
print("=" * 70)

u1_block = find_symbol_instance(content, "U1")
if u1_block:
    # Extract position and rotation
    m = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\s*([-\d.]*)\)', u1_block)
    u1_x, u1_y = float(m.group(1)), float(m.group(2))
    u1_rot = float(m.group(3)) if m.group(3) else 0
    
    # Extract lib_id
    m = re.search(r'\(lib_id\s+"([^"]*)"', u1_block)
    u1_lib_id = m.group(1)
    
    print(f"  Position: ({u1_x}, {u1_y})")
    print(f"  Rotation: {u1_rot}°")
    print(f"  lib_id: {u1_lib_id}")
    
    # Get pin positions from cache
    cache = find_lib_cache(content, u1_lib_id)
    if cache:
        pins = get_pins_from_cache(cache)
        print(f"\n  lib_symbols Cache: {len(pins)} Pins")
        print(f"  {'Pin':>4s} {'Name':>15s} {'Local X':>8s} {'Local Y':>8s} {'Angle':>6s} {'Sch X':>8s} {'Sch Y':>8s}")
        print(f"  {'─'*4} {'─'*15} {'─'*8} {'─'*8} {'─'*6} {'─'*8} {'─'*8}")
        
        for num in sorted(pins.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            p = pins[num]
            sx, sy = calc_schematic_pos(u1_x, u1_y, u1_rot, p["local_x"], p["local_y"])
            print(f"  {num:>4s} {p['name']:>15s} {p['local_x']:>8.2f} {p['local_y']:>8.2f} {p['angle']:>6d} {sx:>8.2f} {sy:>8.2f}")
    else:
        print("  ⚠️  lib_symbols Cache NICHT GEFUNDEN!")
    
    # Find wires near U1
    print(f"\n  Wires im Bereich ±20mm um ({u1_x}, {u1_y}):")
    wires = find_wires_near(content, u1_x, u1_y, 20)
    for w in sorted(wires, key=lambda w: w["y1"]):
        print(f"    ({w['x1']:.2f}, {w['y1']:.2f}) → ({w['x2']:.2f}, {w['y2']:.2f})")
    
    # Find labels near U1
    print(f"\n  Labels im Bereich ±20mm:")
    labels = find_labels_near(content, u1_x, u1_y, 20)
    for l in sorted(labels, key=lambda l: l["dist"]):
        print(f"    '{l['name']}' at ({l['x']:.2f}, {l['y']:.2f}) @ {l['angle']}° [dist={l['dist']}]")
    
    # Find power symbols near U1
    print(f"\n  Power-Symbole im Bereich ±20mm:")
    power = find_power_symbols_near(content, u1_x, u1_y, 20)
    for p in sorted(power, key=lambda p: p["dist"]):
        print(f"    {p['lib_id']} ({p['ref']}) at ({p['x']:.2f}, {p['y']:.2f}) @ {p['angle']}° [dist={p['dist']}]")
else:
    print("  ⚠️  U1 Instanz NICHT GEFUNDEN!")

# ══════════════════════════════════════════════════
# U14 (ADP7118ARDZ) Analysis
# ══════════════════════════════════════════════════
print()
print("=" * 70)
print("U14 (ADP7118ARDZ) — Pin-Position-Analyse")
print("=" * 70)

u14_block = find_symbol_instance(content, "U14")
if u14_block:
    m = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)\s*([-\d.]*)\)', u14_block)
    u14_x, u14_y = float(m.group(1)), float(m.group(2))
    u14_rot = float(m.group(3)) if m.group(3) else 0
    
    m = re.search(r'\(lib_id\s+"([^"]*)"', u14_block)
    u14_lib_id = m.group(1)
    
    print(f"  Position: ({u14_x}, {u14_y})")
    print(f"  Rotation: {u14_rot}°")
    print(f"  lib_id: {u14_lib_id}")
    
    cache = find_lib_cache(content, u14_lib_id)
    if cache:
        pins = get_pins_from_cache(cache)
        print(f"\n  lib_symbols Cache: {len(pins)} Pins")
        print(f"  {'Pin':>4s} {'Name':>15s} {'Local X':>8s} {'Local Y':>8s} {'Angle':>6s} {'Sch X':>8s} {'Sch Y':>8s}")
        print(f"  {'─'*4} {'─'*15} {'─'*8} {'─'*8} {'─'*6} {'─'*8} {'─'*8}")
        
        for num in sorted(pins.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            p = pins[num]
            sx, sy = calc_schematic_pos(u14_x, u14_y, u14_rot, p["local_x"], p["local_y"])
            print(f"  {num:>4s} {p['name']:>15s} {p['local_x']:>8.2f} {p['local_y']:>8.2f} {p['angle']:>6d} {sx:>8.2f} {sy:>8.2f}")
    else:
        print("  ⚠️  lib_symbols Cache NICHT GEFUNDEN!")
    
    print(f"\n  Wires im Bereich ±20mm um ({u14_x}, {u14_y}):")
    wires = find_wires_near(content, u14_x, u14_y, 20)
    for w in sorted(wires, key=lambda w: w["y1"]):
        print(f"    ({w['x1']:.2f}, {w['y1']:.2f}) → ({w['x2']:.2f}, {w['y2']:.2f})")
    
    print(f"\n  Labels im Bereich ±20mm:")
    labels = find_labels_near(content, u14_x, u14_y, 20)
    for l in sorted(labels, key=lambda l: l["dist"]):
        print(f"    '{l['name']}' at ({l['x']:.2f}, {l['y']:.2f}) @ {l['angle']}° [dist={l['dist']}]")
    
    print(f"\n  Power-Symbole im Bereich ±20mm:")
    power = find_power_symbols_near(content, u14_x, u14_y, 20)
    for p in sorted(power, key=lambda p: p["dist"]):
        print(f"    {p['lib_id']} ({p['ref']}) at ({p['x']:.2f}, {p['y']:.2f}) @ {p['angle']}° [dist={p['dist']}]")
else:
    print("  ⚠️  U14 Instanz NICHT GEFUNDEN!")

# ══════════════════════════════════════════════════
# Also show what the OLD pins were (from FINDINGS.md)
# ══════════════════════════════════════════════════
print()
print("=" * 70)
print("REFERENZ: Alte vs. Neue Pin-Nummern")
print("=" * 70)
print()
print("TEL5-2422:")
print("  Alt (FINDINGS.md):  1=+VIN, 7=-VIN, 14=-VOUT, 18=COM, 24=+VOUT")
print("  Neu (TRACO DB):     2=+VIN, 3=-VIN, 9=COM, 11=-VOUT, 14=+VOUT, 16=COM, 22=+VIN, 23=-VIN")
print()
print("ADP7118:")
print("  Alt (ACPZN):  1=VOUT, 2=SENSE, 3=GND, 4=EN, 5=SS, 6=VIN, 7=GND")
print("  Neu (ARDZ):   1=VOUT, 2=SENSE, 3=GND, 4=EN, 5=NC, 6=SS, 7=VIN, 8=VIN, 9=EP(GND)")
