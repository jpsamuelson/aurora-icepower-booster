#!/usr/bin/env python3
"""
Compute schematic pin positions and compare with existing wire endpoints.
This tells us exactly which wires to move where.
"""
import math

# U1 TEL5-2422 at (80.0, 40.0) rotation 0°
U1_X, U1_Y, U1_ROT = 80.0, 40.0, 0.0

# U14 ADP7118ARDZ at (140.0, 30.0) rotation 0°
U14_X, U14_Y, U14_ROT = 140.0, 30.0, 0.0

def calc_pos(sx, sy, rot, px, py):
    theta = math.radians(rot)
    rx = px * math.cos(theta) - py * math.sin(theta)
    ry = px * math.sin(theta) + py * math.cos(theta)
    return round(sx + rx, 2), round(sy - ry, 2)

# ═══════════════════════════════════════════
# U1 TEL5-2422 — New pin positions
# ═══════════════════════════════════════════
print("=" * 70)
print("U1 TEL5-2422 — NEUE Pin-Endpunkte (Schematic-Koordinaten)")
print("=" * 70)

u1_pins = {
    # Local positions from cache
    "22": {"name": "+VIN",      "lx": -10.16, "ly": 5.08,  "angle": 0,   "net": "+24V_IN"},
    "23": {"name": "+VIN(dup)", "lx": -10.16, "ly": 2.54,  "angle": 0,   "net": "+24V_IN"},
    "2":  {"name": "-VIN(GND)", "lx": -10.16, "ly": 0.0,   "angle": 0,   "net": "GND"},
    "3":  {"name": "-VIN(GND)", "lx": -10.16, "ly": -2.54, "angle": 0,   "net": "GND"},
    "14": {"name": "+VOUT",     "lx": 10.16,  "ly": 5.08,  "angle": 180, "net": "+12V_RAW"},
    "16": {"name": "COMMON",    "lx": 10.16,  "ly": 2.54,  "angle": 180, "net": "GND"},
    "9":  {"name": "COMMON",    "lx": 10.16,  "ly": -2.54, "angle": 180, "net": "GND"},
    "11": {"name": "-VOUT",     "lx": 10.16,  "ly": -5.08, "angle": 180, "net": "-12V_RAW"},
}

for num in sorted(u1_pins.keys(), key=lambda x: int(x)):
    p = u1_pins[num]
    sx, sy = calc_pos(U1_X, U1_Y, U1_ROT, p["lx"], p["ly"])
    p["sch_x"] = sx
    p["sch_y"] = sy
    print(f"  Pin{num:>3s} ({p['name']:>12s}) → Schematic ({sx:>7.2f}, {sy:>7.2f}) | Net: {p['net']}")

# Old wires near U1 (from analysis):
print()
print("  BESTEHENDE WIRES nahe U1:")
u1_wires = [
    # (x1, y1, x2, y2) — description
    (50.00, 37.46, 72.38, 37.46),    # links → U1 links (ehem. Pin 1=+VIN)
    (37.62, 42.54, 72.38, 42.54),    # links → U1 links (ehem. Pin 7=-VIN)
    (87.62, 34.92, 85.08, 34.92),    # kurzer Draht rechts oben → Label +12V_RAW
    (87.62, 40.00, 85.08, 40.00),    # kurzer Draht rechts mitte → GND
    (87.62, 45.08, 85.08, 45.08),    # kurzer Draht rechts unten → Label -12V_RAW
    (98.00, 28.81, 98.00, 31.35),    # vertikaler Draht → +12V_RAW
    (98.00, 51.19, 98.00, 48.65),    # vertikaler Draht → -12V_RAW
]

for w in u1_wires:
    print(f"    ({w[0]:.2f}, {w[1]:.2f}) → ({w[2]:.2f}, {w[3]:.2f})")

# Now let's figure out the mapping
# OLD pins had their wire endpoints at these positions (from the old symbol):
# Old symbol had 5 pins: 1=+VIN, 7=-VIN, 14=-VOUT, 18=COM, 24=+VOUT
# With a standard DC/DC symbol (assuming same body), they were probably at:
# Pin 1 (+VIN):  left side, upper
# Pin 7 (-VIN):  left side, lower  
# Pin 24 (+VOUT): right side, upper
# Pin 18 (COM):   right side, middle
# Pin 14 (-VOUT): right side, lower

# The existing wires are:
# Left side: ends at x=72.38 (symbol body starts at 80-7.62=72.38)
#   y=37.46: This was going to the left-side pin (old pin at body edge)
#   y=42.54: This was going to another left-side pin

# Right side: ends at x=87.62 (symbol body ends at 80+7.62=87.62)
#   y=34.92: +12V_RAW label
#   y=40.00: GND power symbol
#   y=45.08: -12V_RAW label

# NEW pins have endpoints at:
# Left side (pin angle 0° = points right, wire comes from left):
#   Pin 22 (+VIN):     (80 - 10.16, 40 - 5.08) = (69.84, 34.92)
#   Pin 23 (+VIN dup): (80 - 10.16, 40 - 2.54) = (69.84, 37.46)
#   Pin 2 (-VIN GND):  (80 - 10.16, 40 - 0)    = (69.84, 40.00)
#   Pin 3 (-VIN GND):  (80 - 10.16, 40 + 2.54) = (69.84, 42.54)
# Right side (pin angle 180° = points left, wire comes from right):
#   Pin 14 (+VOUT):    (80 + 10.16, 40 - 5.08) = (90.16, 34.92)
#   Pin 16 (COM):      (80 + 10.16, 40 - 2.54) = (90.16, 37.46)
#   Pin 9 (COM):       (80 + 10.16, 40 + 2.54) = (90.16, 42.54)
#   Pin 11 (-VOUT):    (80 + 10.16, 40 + 5.08) = (90.16, 45.08)

print()
print("  ANALYSE: Left-side pins:")
print(f"    Pin 22 (+VIN)  endpoint: (69.84, 34.92) — need wire from +24V_IN")
print(f"    Pin 23 (+VIN)  endpoint: (69.84, 37.46) — tied to Pin 22")
print(f"    Pin 2  (GND)   endpoint: (69.84, 40.00) — need GND")
print(f"    Pin 3  (GND)   endpoint: (69.84, 42.54) — tied to Pin 2")
print()
print("  ANALYSE: Right-side pins:")
print(f"    Pin 14 (+VOUT) endpoint: (90.16, 34.92) — need +12V_RAW")
print(f"    Pin 16 (COM)   endpoint: (90.16, 37.46) — need GND")
print(f"    Pin 9  (COM)   endpoint: (90.16, 42.54) — need GND")
print(f"    Pin 11 (-VOUT) endpoint: (90.16, 45.08) — need -12V_RAW")
print()
print("  OLD WIRE ENDPOINTS → NEW PIN ENDPOINTS:")
print(f"    Wire ending (72.38, 37.46) was old +VIN → now Pin 23 at (69.84, 37.46): MOVE x1 72.38→69.84")
print(f"    Wire ending (72.38, 42.54) was old -VIN → now Pin 3 at (69.84, 42.54): MOVE x1 72.38→69.84")
print(f"    Wire ending (87.62, 34.92) was old +VOUT → now Pin 14 at (90.16, 34.92): MOVE x1 87.62→90.16")
print(f"    Wire ending (87.62, 40.00) was old COM → now Pin 16 at (90.16, 37.46): MOVE x1 87.62→90.16, y 40→37.46")
print(f"    Wire ending (87.62, 45.08) was old -VOUT → now Pin 11 at (90.16, 45.08): MOVE x1 87.62→90.16")
print()
print("  ADDITIONAL WIRES NEEDED:")
print(f"    NEW: Pin 22 (+VIN) at (69.84, 34.92) — connect to +24V_IN (tie to Pin 23 vertically)")
print(f"    NEW: Pin 2 (GND) at (69.84, 40.00) — need GND power symbol")
print(f"    NEW: Pin 9 (COM) at (90.16, 42.54) — need GND connection")

# ═══════════════════════════════════════════
# U14 ADP7118ARDZ — New pin positions
# ═══════════════════════════════════════════
print()
print("=" * 70)
print("U14 ADP7118ARDZ — NEUE Pin-Endpunkte (Schematic-Koordinaten)")
print("=" * 70)

u14_pins = {
    "1": {"name": "VOUT",      "lx": 10.16,  "ly": 7.62,  "angle": 180, "net": "V+"},
    "2": {"name": "VOUT(dup)", "lx": 10.16,  "ly": 5.08,  "angle": 180, "net": "V+"},
    "3": {"name": "SENSE/ADJ", "lx": 10.16,  "ly": 2.54,  "angle": 180, "net": "V+"},
    "4": {"name": "GND",       "lx": 10.16,  "ly": 0.0,   "angle": 180, "net": "GND"},
    "5": {"name": "EN",        "lx": -10.16, "ly": 2.54,  "angle": 0,   "net": "EN_CTRL"},
    "6": {"name": "SS",        "lx": -10.16, "ly": 0.0,   "angle": 0,   "net": "SS_U14"},
    "7": {"name": "VIN",       "lx": -10.16, "ly": 7.62,  "angle": 0,   "net": "+12V"},
    "8": {"name": "VIN(dup)",  "lx": -10.16, "ly": 5.08,  "angle": 0,   "net": "+12V"},
    "9": {"name": "GND(EP)",   "lx": 10.16,  "ly": -2.54, "angle": 180, "net": "GND"},
}

for num in sorted(u14_pins.keys(), key=lambda x: int(x)):
    p = u14_pins[num]
    sx, sy = calc_pos(U14_X, U14_Y, U14_ROT, p["lx"], p["ly"])
    p["sch_x"] = sx
    p["sch_y"] = sy
    print(f"  Pin{num:>3s} ({p['name']:>12s}) → Schematic ({sx:>7.2f}, {sy:>7.2f}) | Net: {p['net']}")

# Old ACPZN had 7 pins in a standard SOIC-8 layout:
# 1=VOUT, 2=SENSE, 3=GND, 4=EN, 5=SS, 6=VIN, 7=GND
# 
# Standard SOIC-8 pin arrangement in KiCad (pins 1-4 left, 5-8 right):
# Wait - for the ACPZN symbol in KiCad (Regulator_Linear:ADP7118ACPZN):
# Pins are arranged functionally, not by physical pin number.
# Let me check what wires exist and where they connect

print()
print("  BESTEHENDE WIRES nahe U14:")
u14_wires = [
    (125.00, 21.19, 125.00, 18.65),     # vertical above
    (128.81, 27.46, 128.81, 30.00),      # left pin → GND
    (129.84, 27.46, 127.00, 27.46),      # → +12V label
    (150.16, 27.46, 153.00, 27.46),      # → V+ label
    (118.00, 27.46, 121.19, 27.46),      # far left → VIN
    (125.00, 28.81, 125.00, 31.35),      # vertical → +12V label
    (150.16, 30.00, 150.16, 27.46),      # vertical right
    (129.84, 32.54, 132.38, 32.54),      # → EN_CTRL label
    (150.16, 32.54, 147.62, 32.54),      # → SS_U14 label
    (147.62, 32.54, 147.62, 34.19),      # vertical from SS
    (128.81, 35.08, 128.81, 37.00),      # → GND
    (140.00, 37.62, 140.00, 40.00),      # vertical → GND
    (147.62, 41.81, 147.62, 43.00),      # vertical → GND
]

for w in u14_wires:
    print(f"    ({w[0]:.2f}, {w[1]:.2f}) → ({w[2]:.2f}, {w[3]:.2f})")

# New pin positions (U14 at 140.0, 30.0):
# Left side (from left, wire endpoint = symbol_x - 10.16 = 129.84):
#   Pin 7 (VIN):  (129.84, 22.38)
#   Pin 8 (VIN):  (129.84, 24.92)
#   Pin 5 (EN):   (129.84, 27.46)
#   Pin 6 (SS):   (129.84, 30.00)
# Right side (wire endpoint = symbol_x + 10.16 = 150.16):
#   Pin 1 (VOUT): (150.16, 22.38)
#   Pin 2 (VOUT): (150.16, 24.92)
#   Pin 3 (SENSE):(150.16, 27.46)
#   Pin 4 (GND):  (150.16, 30.00)
#   Pin 9 (EP):   (150.16, 32.54)

print()
print("  NEUE Pin-Endpunkte:")
print(f"    Left side (x=129.84):")
print(f"      Pin 7 (VIN):  (129.84, 22.38) — need +12V")
print(f"      Pin 8 (VIN):  (129.84, 24.92) — need +12V")
print(f"      Pin 5 (EN):   (129.84, 27.46) — need EN_CTRL")
print(f"      Pin 6 (SS):   (129.84, 30.00) — need SS_U14")
print(f"    Right side (x=150.16):")
print(f"      Pin 1 (VOUT): (150.16, 22.38) — need V+")
print(f"      Pin 2 (VOUT): (150.16, 24.92) — need V+")
print(f"      Pin 3 (SENSE):(150.16, 27.46) — need V+ (already has wire!)")
print(f"      Pin 4 (GND):  (150.16, 30.00) — need GND (already has wire!)")
print(f"      Pin 9 (EP):   (150.16, 32.54) — need GND")

# Map old wires to new connections
print()
print("  OLD → NEW Wire Mapping:")
print()
print("  OLD ACPZN had pins at different positions. Current wires:")
print(f"    Wire to (129.84, 27.46) [left @ y=27.46]: was ACPZN Pin 4(EN)=EN_CTRL → is now ARDZ Pin 5(EN) at same pos! ✅")
print(f"    Wire to (129.84, 32.54) [left @ y=32.54]: was ACPZN Pin 5(SS)=EN_CTRL → OUTSIDE new symbol body!")
print(f"    Wire to (150.16, 27.46) [right @ y=27.46]: was ACPZN Pin 1+2(VOUT/SENSE)=V+ → is now ARDZ Pin 3(SENSE) ✅")
print(f"    Wire to (150.16, 30.00) [right @ y=30.00]: was ACPZN Pin 3(GND) → is now ARDZ Pin 4(GND) ✅")
print(f"    Wire to (150.16, 32.54) [right @ y=32.54]: was ACPZN Pin 5(SS)=SS_U14 → is now ARDZ Pin 9(EP)=GND")
print()
print("  WIRES TO ADD:")
print(f"    Pin 7 (VIN) at (129.84, 22.38): need wire + label +12V")
print(f"    Pin 8 (VIN) at (129.84, 24.92): tie to Pin 7")
print(f"    Pin 1 (VOUT) at (150.16, 22.38): need wire + label V+")
print(f"    Pin 2 (VOUT) at (150.16, 24.92): tie to Pin 1")
print(f"    Pin 6 (SS) at (129.84, 30.00): need wire + label SS_U14")
print(f"    Pin 9 (EP) at (150.16, 32.54): need GND (has old SS wire, rebind to GND)")
print()
print("  WIRES TO MODIFY:")
print(f"    Old EN_CTRL label at (132.38, 32.54): REMOVE (wrong position)")
print(f"    Old SS_U14 label at (147.62, 32.54): REMOVE from EP, add to Pin 6")
print(f"    Wire (128.81, 27.46→30.00): was GND for ACPZN Pin 3 — REASSIGN")
print(f"    Wire (128.81, 35.08→37.00): orphaned GND below symbol")
