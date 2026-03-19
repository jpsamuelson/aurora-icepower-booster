#!/usr/bin/env python3
"""Check what's at the dangling wire locations and investigate SS pin requirements."""

import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    text = f.read()

# ===== 1. What's at (42.0, 82.46) and (60.0, 82.46)? =====
print("=" * 70)
print("1. Dangling Wire Context")
print("=" * 70)

for target_x, target_y, desc in [(42.0, 82.0, "Wire @42,82"), (60.0, 83.0, "Wire @60,83")]:
    print(f"\n  --- {desc} area ---")
    # Find symbols nearby
    for m in re.finditer(r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
        x, y = float(m.group(2)), float(m.group(3))
        if abs(x - target_x) < 10 and abs(y - target_y) < 10:
            start = m.start()
            chunk = text[start:start+1500]
            ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
            val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', chunk)
            ref = ref_m.group(1) if ref_m else "?"
            val = val_m.group(1) if val_m else "?"
            print(f"    {ref} ({val}) at ({x}, {y})")
    
    # Labels
    for m in re.finditer(r'\(label\s+"([^"]+)"\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
        lx, ly = float(m.group(2)), float(m.group(3))
        if abs(lx - target_x) < 10 and abs(ly - target_y) < 10:
            print(f"    Label '{m.group(1)}' at ({lx}, {ly})")
    
    # Power symbols
    for m in re.finditer(r'\(symbol\s+\(lib_id\s+"(power:[^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
        x, y = float(m.group(2)), float(m.group(3))
        if abs(x - target_x) < 10 and abs(y - target_y) < 10:
            start = m.start()
            chunk = text[start:start+1500]
            ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
            ref = ref_m.group(1) if ref_m else "?"
            print(f"    Power {ref} ({m.group(1)}) at ({x}, {y})")
    
    # All wires in area
    print(f"    Wires:")
    for wm in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
        x1, y1, x2, y2 = float(wm.group(1)), float(wm.group(2)), float(wm.group(3)), float(wm.group(4))
        if (abs(x1 - target_x) < 10 and abs(y1 - target_y) < 10) or \
           (abs(x2 - target_x) < 10 and abs(y2 - target_y) < 10):
            print(f"      ({x1},{y1})→({x2},{y2})")

# ===== 2. Check what U1 Pin 1 actually is =====
print("\n" + "=" * 70)
print("2. U1 — Full Pin Map Verification")
print("=" * 70)
# U1 at (80, 40). Check all pin positions
cache_start = text.find('(lib_symbols')
tel_idx = text.find('"TEL5-2422"', cache_start)
if tel_idx >= 0:
    chunk = text[tel_idx:tel_idx+5000]
    pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+\d+)?\).*?\(name\s+"([^"]+)".*?\(number\s+"(\d+)"', chunk)
    print("  All TEL5-2422 Pins:")
    for ptype, px, py, pname, pnum in pins:
        sch_x = 80.0 + float(px)
        sch_y = 40.0 - float(py)  # Y axis inverted
        print(f"    Pin {pnum:>2} ({pname:>12}, {ptype:>12}): local ({px:>6}, {py:>6}) → sch ({sch_x:.2f}, {sch_y:.2f})")

# ===== 3. C22 — What net should Pin 1 go to? =====
print("\n" + "=" * 70)
print("3. C22 — Circuit Intent Analysis")
print("=" * 70)
print("  C22: 100nF C0G at (147.62, 38.0)")
print("  Pin 1 (top): (147.62, 34.19) → NOT CONNECTED")
print("  Pin 2 (bot): (147.62, 41.81) → wire to GND (#PWR103 at 147.62, 43.0)")
print()
print("  U14 ADP7118ARDZ at (140, 30):")
print("    Output pins (VOUT): (150.16, 22.38) and (150.16, 24.92)")
print("    GND pins: (150.16, 30.00) and (150.16, 32.54)")
print("    SENSE/ADJ pin: (150.16, 27.46)")
print()
print("  Nearby V+ wire path:")
# Trace from V+ label  
visited = set()
to_visit = [(153.0, 27.46)]  # V+ label position
vplus_points = []
for wm in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    x1, y1, x2, y2 = float(wm.group(1)), float(wm.group(2)), float(wm.group(3)), float(wm.group(4))
    # Just find wires near V+ label
    if 148 < x1 < 155 and 20 < y1 < 35:
        print(f"    Wire: ({x1},{y1})→({x2},{y2})")
    elif 148 < x2 < 155 and 20 < y2 < 35:
        print(f"    Wire: ({x1},{y1})→({x2},{y2})")

# ===== 4. SS pin on ADP7118: datasheet says =====
print("\n" + "=" * 70)
print("4. ADP7118 SS Pin — Datasheet Requirements")
print("=" * 70)
print("""
  From ADP7118 datasheet (Analog Devices):
  
  SS (Soft-Start) Pin:
  - Connect an external capacitor from SS to GND for soft-start timing
  - CSS determines the soft-start time: t_ss = CSS × VREF / I_SS
  - Typical I_SS = 3µA, VREF = 1.22V
  - For 10ms soft-start: CSS = 10ms × 3µA / 1.22V ≈ 24.6nF → use 22nF or 33nF
  - If soft-start is NOT needed: Connect SS directly to VOUT
  - DO NOT leave SS floating (high-impedance → unpredictable behavior)
  
  Current state in schematic:
  - Pin 6 (SS) → wire → label SS_U14 → NOTHING ELSE
  - No capacitor on SS_U14 net
  - Not connected to VOUT
  - ⚠️ Effectively floating! Design error!
""")

# ===== 5. Check what's at #FLG positions =====
print("=" * 70)
print("5. Summary of All PWR_FLAG Positions")
print("=" * 70)
print("  #FLG0101 at (50.0, 35.0) → on +24V_IN net")
print("  #FLG0102 at (118.35, 31.35) → on +12V net")
print("  #FLG0103 at (118.35, 48.65) → on -12V net")
print("  ⚠️ MISSING: PWR_FLAG on GND net!")
print("  ⚠️ MISSING: PWR_FLAG on V+ net (if it has only power_out + passive)")
