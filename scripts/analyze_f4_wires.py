#!/usr/bin/env python3
"""Find all wires connecting R20.pin1 to the HOT_IN net.
We need to disconnect R20.pin1 and reconnect to INV_IN."""
import re, math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# Find ALL wires in the R20 area (x=50-85, y=93-115) for CH1
print("=== All wires near R20 area (x=50-85, y=93-115) ===")
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    if ((50 <= x1 <= 85 and 93 <= y1 <= 115) or (50 <= x2 <= 85 and 93 <= y2 <= 115)):
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")

# Also find component positions in this area
print("\n=== Components near R20 area ===")
for ref in ['R14', 'R15', 'R20', 'R2', 'R3', 'U2', 'C62', 'C63']:
    pat = rf'\(property "Reference" "{re.escape(ref)}"'
    for m_ref in re.finditer(pat, text):
        pos = m_ref.start()
        start = pos
        depth = 0
        while start > 0:
            start -= 1
            if text[start] == ')': depth += 1
            elif text[start] == '(':
                depth -= 1
                if depth < 0: break
        if start < text.find('(symbol (lib_id'):
            continue
        depth = 0
        for end in range(start, min(start+10000, len(text))):
            if text[end] == '(': depth += 1
            elif text[end] == ')': depth -= 1
            if depth == 0: break
        block = text[start:end+1]
        pos_m = re.search(r'\(at ([\d.]+) ([\d.]+)(?:\s+(\d+))?\)', block)
        lib_m = re.search(r'lib_id "([^"]+)"', block)
        val_m = re.search(r'\(property "Value" "([^"]+)"', block)
        if pos_m:
            sx, sy = float(pos_m.group(1)), float(pos_m.group(2))
            rot = int(pos_m.group(3)) if pos_m.group(3) else 0
            lib = lib_m.group(1) if lib_m else '?'
            val = val_m.group(1) if val_m else '?'
            
            # Compute pin positions for Device:R (pins at (0, ±3.81))
            if 'Device:R' in lib:
                angle = math.radians(rot)
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                p1_x = round(sx + (-3.81 * sin_a), 2)
                p1_y = round(sy - (3.81 * cos_a), 2)
                p2_x = round(sx + (3.81 * sin_a), 2)
                p2_y = round(sy - (-3.81 * cos_a), 2)
                print(f"  {ref} ({val}) at ({sx}, {sy}) rot={rot}°: pin1=({p1_x}, {p1_y}), pin2=({p2_x}, {p2_y})")
            elif 'LM4562' in lib or 'Amplifier_Operational' in lib:
                print(f"  {ref} ({val}) at ({sx}, {sy}) rot={rot}° lib={lib}")
            else:
                print(f"  {ref} ({val}) at ({sx}, {sy}) rot={rot}° lib={lib}")
        break

# Find all labels in the area
print("\n=== Labels near R20 area ===")
for m in re.finditer(r'\(label "([^"]+)" \(at ([\d.]+) ([\d.]+)', text):
    lx, ly = float(m.group(2)), float(m.group(3))
    if 50 <= lx <= 85 and 90 <= ly <= 115:
        print(f"  {m.group(1)} at ({lx}, {ly})")

# Show the approach: R20.pin1 is at (80, 96.19). It connects via wire(s)
# to the HOT_IN wire group. We need to:
# 1. Find the wire directly connected to R20.pin1
# 2. Remove that wire
# 3. Add an INV_IN label at R20.pin1
print("\n=== Wires with endpoint at R20.pin1 (80, 96.19) ===")
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    if (abs(x1-80)<0.01 and abs(y1-96.19)<0.01) or (abs(x2-80)<0.01 and abs(y2-96.19)<0.01):
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")
