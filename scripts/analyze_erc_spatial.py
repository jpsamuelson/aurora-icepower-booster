#!/usr/bin/env python3
"""Deep spatial analysis of each ERC error — find nearby wires, labels, and components."""

import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, "r") as f:
    text = f.read()

# Parse all wires
wires = []
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    wires.append({
        'x1': float(m.group(1)), 'y1': float(m.group(2)),
        'x2': float(m.group(3)), 'y2': float(m.group(4))
    })

# Parse all labels
labels = []
for m in re.finditer(r'\(label\s+"([^"]+)"\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    labels.append({
        'name': m.group(1),
        'x': float(m.group(2)), 'y': float(m.group(3)),
        'rot': int(m.group(4))
    })

# Parse all power symbols
power_symbols = []
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"(power:[^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    lib_id = m.group(1)
    x, y, rot = float(m.group(2)), float(m.group(3)), int(m.group(4))
    start = m.start()
    chunk = text[start:start+2000]
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
    val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', chunk)
    ref = ref_m.group(1) if ref_m else "?"
    val = val_m.group(1) if val_m else "?"
    power_symbols.append({'ref': ref, 'lib_id': lib_id, 'value': val, 'x': x, 'y': y, 'rot': rot, 'start': start})

def find_wires_near(x, y, radius=5.0):
    """Find wires with an endpoint within radius of (x,y)."""
    results = []
    for w in wires:
        for wx, wy in [(w['x1'], w['y1']), (w['x2'], w['y2'])]:
            if abs(wx - x) < radius and abs(wy - y) < radius:
                results.append(w)
                break
    return results

def find_labels_near(x, y, radius=5.0):
    results = []
    for l in labels:
        if abs(l['x'] - x) < radius and abs(l['y'] - y) < radius:
            results.append(l)
    return results

def find_power_near(x, y, radius=5.0):
    results = []
    for p in power_symbols:
        if abs(p['x'] - x) < radius and abs(p['y'] - y) < radius:
            results.append(p)
    return results

# GND power symbol pin position: For a GND symbol at (x,y) with rotation 0,
# the pin is at (x, y) — the connection point is at the symbol position.
# Actually in KiCad, power symbols have their pin at the origin (0,0) of the symbol.

print("=" * 70)
print("RÄUMLICHE ANALYSE JEDES ERRORS")
print("=" * 70)

# ===== Error 1: #PWR063 at (55.0, 42.54) =====
print("\n--- Error 1: #PWR063 (GND) at (55.0, 42.54) ---")
nearby_w = find_wires_near(55.0, 42.54, 3)
nearby_l = find_labels_near(55.0, 42.54, 5)
nearby_p = find_power_near(55.0, 42.54, 5)
print(f"  Nearby wires ({len(nearby_w)}):")
for w in nearby_w:
    print(f"    ({w['x1']}, {w['y1']}) → ({w['x2']}, {w['y2']})")
print(f"  Nearby labels ({len(nearby_l)}):")
for l in nearby_l:
    print(f"    '{l['name']}' at ({l['x']}, {l['y']})")
print(f"  Nearby power symbols ({len(nearby_p)}):")
for p in nearby_p:
    print(f"    {p['ref']} ({p['value']}) at ({p['x']}, {p['y']})")

# What's around (55, 42.54)? This is in the U1 area (U1 at 80, 40)
# Actually 55 is to the left of U1

# ===== Errors 8-13: #PWR at x=285, y=115/195/275/355/435/515 =====
print("\n--- Errors 8-13: 6× GND at x=285 (Audio Channels area) ---")
for ref, ypos in [('#PWR014', 115.0), ('#PWR083', 195.0), ('#PWR005', 275.0),
                   ('#PWR088', 355.0), ('#PWR028', 435.0), ('#PWR037', 515.0)]:
    nearby_w = find_wires_near(285.0, ypos, 3)
    nearby_l = find_labels_near(285.0, ypos, 5)
    nearby_p = find_power_near(285.0, ypos, 5)
    print(f"\n  {ref} at (285.0, {ypos}):")
    print(f"    Wires near ({len(nearby_w)}):", end=" ")
    for w in nearby_w:
        print(f"({w['x1']},{w['y1']})→({w['x2']},{w['y2']})", end=" ")
    print()
    print(f"    Labels near: ", end="")
    for l in nearby_l:
        print(f"'{l['name']}' @ ({l['x']},{l['y']})", end=" ")
    print()
    print(f"    Power near: ", end="")
    for p in nearby_p:
        if p['ref'] != ref:
            print(f"{p['ref']}({p['value']}) @ ({p['x']},{p['y']})", end=" ")
    print()

# ===== Error 3: #PWR001 at (98.0, 18.65) =====
print("\n--- Error 3: #PWR001 (GND) at (98.0, 18.65) ---")
nearby_w = find_wires_near(98.0, 18.65, 5)
nearby_l = find_labels_near(98.0, 18.65, 10)
nearby_p = find_power_near(98.0, 18.65, 10)
print(f"  Nearby wires ({len(nearby_w)}):")
for w in nearby_w:
    print(f"    ({w['x1']}, {w['y1']}) → ({w['x2']}, {w['y2']})")
print(f"  Nearby labels ({len(nearby_l)}):")
for l in nearby_l:
    print(f"    '{l['name']}' at ({l['x']}, {l['y']})")
print(f"  Nearby power symbols ({len(nearby_p)}):")
for p in nearby_p:
    print(f"    {p['ref']} ({p['value']}) at ({p['x']}, {p['y']})")

# ===== Errors 4+5: U14 SS Pin at ~(129.84, 30) and label SS_U14 =====
print("\n--- Errors 4+5: U14 Pin 6 (SS) + SS_U14 Label ---")
# U14 is at (140.0, 30.0)
# Pin 6 (SS) - need to find its position
# Label SS_U14
for l in labels:
    if l['name'] == 'SS_U14':
        print(f"  SS_U14 label at ({l['x']}, {l['y']}), rot={l['rot']}")
        nearby_w = find_wires_near(l['x'], l['y'], 3)
        print(f"  Wires near label ({len(nearby_w)}):")
        for w in nearby_w:
            print(f"    ({w['x1']}, {w['y1']}) → ({w['x2']}, {w['y2']})")

# Check all wires near U14 Pin 6 area
print(f"\n  Wires near U14 SS area (129-135, 29-31):")
for w in wires:
    for wx, wy in [(w['x1'], w['y1']), (w['x2'], w['y2'])]:
        if 128 < wx < 136 and 28 < wy < 32:
            print(f"    ({w['x1']}, {w['y1']}) → ({w['x2']}, {w['y2']})")
            break

# ===== Error 6: C22 Pin 1 at (147.62, 34.19) =====
print("\n--- Error 6: C22 (100nF C0G) at (147.62, 38.0) ---")
nearby_w = find_wires_near(147.62, 38.0, 5)
print(f"  Wires near C22 ({len(nearby_w)}):")
for w in nearby_w:
    print(f"    ({w['x1']}, {w['y1']}) → ({w['x2']}, {w['y2']})")
nearby_w2 = find_wires_near(147.62, 34.19, 5)
print(f"  Wires near C22 Pin1 area ({len(nearby_w2)}):")
for w in nearby_w2:
    print(f"    ({w['x1']}, {w['y1']}) → ({w['x2']}, {w['y2']})")
# Check Pin 1 and Pin 2 positions for a vertical capacitor at (147.62, 38.0)
# Standard Device:C has pins at +/- 1.27mm from center
# At rotation 0: Pin 1 at (x, y-1.27), Pin 2 at (x, y+1.27)
print(f"\n  C22 expected Pin positions:")
print(f"    Pin 1 (top): (147.62, {38.0 - 1.27:.2f}) = (147.62, 36.73)")
print(f"    Pin 2 (bottom): (147.62, {38.0 + 1.27:.2f}) = (147.62, 39.27)")

# Check for C22 in schematic - get its actual rotation
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"Device:C"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    x, y, rot = float(m.group(1)), float(m.group(2)), int(m.group(3))
    start = m.start()
    chunk = text[start:start+2000]
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
    if ref_m and ref_m.group(1) == 'C22':
        print(f"\n  C22 actual: at ({x}, {y}), rotation={rot}°")
        break

# ===== lib_symbols cache analysis for U1 and U14 =====
print("\n" + "=" * 70)
print("LIB_SYMBOLS CACHE — Pin-Typen-Analyse")
print("=" * 70)

# Find U1 (TEL5-2422) in lib_symbols cache
print("\n  U1 TEL5-2422 Pin-Typen im Cache:")
cache_start = text.find('(lib_symbols')
if cache_start >= 0:
    # Find TEL5-2422 in cache
    tel_start = text.find('"TEL5-2422"', cache_start)
    if tel_start >= 0:
        # Extract pin definitions
        chunk = text[tel_start:tel_start+5000]
        pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at\s+[\d.\-\s]+\).*?\(name\s+"([^"]+)".*?\(number\s+"(\d+)"', chunk)
        for pin_type, name, number in pins:
            print(f"    Pin {number} ({name}): type={pin_type}")

    # Find ADP7118ARDZ in cache
    print("\n  U14 ADP7118ARDZ Pin-Typen im Cache:")
    adp_start = text.find('"ADP7118ARDZ"', cache_start)
    if adp_start >= 0:
        chunk = text[adp_start:adp_start+5000]
        pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at\s+[\d.\-\s]+\).*?\(name\s+"([^"]+)".*?\(number\s+"(\d+)"', chunk)
        for pin_type, name, number in pins:
            print(f"    Pin {number} ({name}): type={pin_type}")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
