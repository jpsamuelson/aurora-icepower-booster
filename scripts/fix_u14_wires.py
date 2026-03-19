#!/usr/bin/env python3
"""
Fix U14 ADP7118ARDZ wire routing.

U14 at (140, 30), rotation 0°
New pin layout (9 pins):
  Left:  Pin 7(VIN)  y=22.38  Pin 8(VIN)  y=24.92
         Pin 5(EN)   y=27.46  Pin 6(SS)   y=30.00
  Right: Pin 1(VOUT) y=22.38  Pin 2(VOUT) y=24.92
         Pin 3(SENSE) y=27.46  Pin 4(GND) y=30.00
         Pin 9(GND/EP) y=32.54

Current wiring problems:
  Pin 5 (EN) at (129.84, 27.46) → +12V label (WRONG, should be EN_CTRL)
  Pin 4 (GND) at (150.16, 30) → vertical wire to Pin 3 SENSE (WRONG, dead short!)
  Pin 9 (EP) at (150.16, 32.54) → SS_U14 label (WRONG, should be GND)
  Pin 1,2 (VOUT) → NO connection
  Pin 6 (SS) → NO connection
  Pin 7,8 (VIN) → NO connection
"""

import uuid, subprocess, re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, 'r') as f:
    content = f.read()

original_len = len(content)

def gen_uuid():
    return str(uuid.uuid4())

changes = 0

# ─── R1: DELETE vertical wire (150.16, 30) → (150.16, 27.46) ───
# This shorts Pin 4 (GND) to Pin 3 (SENSE) — catastrophic!
old = '(wire (pts (xy 150.16 30) (xy 150.16 27.46))'
assert content.count(old) == 1, f"Expected 1 match, got {content.count(old)}"
# Find and remove the full line
idx = content.find(old)
line_start = content.rfind('\n', 0, idx)
line_end = content.find('\n', idx)
content = content[:line_start] + content[line_end:]
changes += 1
print(f"R1. DELETED wire (150.16,30)→(150.16,27.46) — removed GND↔SENSE short")

# ─── R2: MOVE +12V wire from Pin 5(EN) to Pin 7(VIN) ───
old = '(wire (pts (xy 129.84 27.46) (xy 127 27.46))'
new = '(wire (pts (xy 129.84 22.38) (xy 127 22.38))'
assert old in content, f"Wire not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"R2. MOVED +12V wire to Pin 7 (VIN) at y=22.38")

# ─── R3: MOVE +12V label to match new wire position ───
old = '(label "+12V" (at 127 27.46 0)'
new = '(label "+12V" (at 127 22.38 0)'
assert old in content, f"Label not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"R3. MOVED +12V label to (127, 22.38)")

# ─── R4: MOVE EN_CTRL wire from orphaned position to Pin 5(EN) ───
old = '(wire (pts (xy 129.84 32.54) (xy 132.38 32.54))'
new = '(wire (pts (xy 129.84 27.46) (xy 132.38 27.46))'
assert old in content, f"Wire not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"R4. MOVED EN_CTRL wire to Pin 5 (EN) at y=27.46")

# ─── R5: MOVE EN_CTRL label to match new wire ───
old = '(label "EN_CTRL" (at 132.38 32.54 0)'
new = '(label "EN_CTRL" (at 132.38 27.46 0)'
assert old in content, f"Label not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"R5. MOVED EN_CTRL label to (132.38, 27.46)")

# ─── R6: CHANGE wire at Pin 9 from SS_U14 to just a stub (will add GND below) ───
# DELETE old wire (150.16, 32.54) → (147.62, 32.54) which went to SS_U14
old = '(wire (pts (xy 150.16 32.54) (xy 147.62 32.54))'
assert content.count(old) == 1
idx = content.find(old)
line_start = content.rfind('\n', 0, idx)
line_end = content.find('\n', idx)
content = content[:line_start] + content[line_end:]
changes += 1
print(f"R6. DELETED wire Pin 9→SS_U14")

# ─── R7: MOVE SS_U14 label to Pin 6 (SS) side ───
old = '(label "SS_U14" (at 147.62 32.54 0)'
new = '(label "SS_U14" (at 132.38 30 0)'
assert old in content, f"Label not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"R7. MOVED SS_U14 label to (132.38, 30) for Pin 6")

# ─── R8: Delete dangling wire (147.62, 32.54)→(147.62, 34.19) ───
# This was below the old SS_U14 label
old = '(wire (pts (xy 147.62 32.54) (xy 147.62 34.19))'
if old in content:
    idx = content.find(old)
    line_start = content.rfind('\n', 0, idx)
    line_end = content.find('\n', idx)
    content = content[:line_start] + content[line_end:]
    changes += 1
    print(f"R8. DELETED dangling wire (147.62,32.54)→(147.62,34.19)")
else:
    print(f"R8. SKIP (wire not found)")

print(f"\n--- {changes} replacements done ---\n")

# ─── Now add new wires, labels and GND symbol ───
# Find the kicad_sch closing bracket for proper insertion
kicad_start = content.find('(kicad_sch')
depth = 0
kicad_close_pos = -1
for i in range(kicad_start, len(content)):
    if content[i] == '(':
        depth += 1
    elif content[i] == ')':
        depth -= 1
        if depth == 0:
            kicad_close_pos = i
            break
assert kicad_close_pos > 0
insert_before = content.rfind('\n', 0, kicad_close_pos)
print(f"Inserting new elements at position {insert_before} (kicad_sch closes at {kicad_close_pos})")

new_elements = []

# N1: VIN tie wire Pin 7↔Pin 8
new_elements.append(f'  (wire (pts (xy 129.84 22.38) (xy 129.84 24.92)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))')
print("N1. Added VIN tie wire Pin 7→Pin 8")

# N2: VOUT tie wire Pin 1→Pin 2→Pin 3
# Single wire from (150.16, 22.38) to (150.16, 27.46)
new_elements.append(f'  (wire (pts (xy 150.16 22.38) (xy 150.16 27.46)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))')
print("N2. Added VOUT tie wire Pin 1→Pin 3 (through Pin 2)")

# N3: SS wire at Pin 6
new_elements.append(f'  (wire (pts (xy 129.84 30) (xy 132.38 30)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))')
print("N3. Added SS wire at Pin 6")

# N4: GND vertical wire Pin 4→Pin 9
new_elements.append(f'  (wire (pts (xy 150.16 30) (xy 150.16 32.54)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))')
print("N4. Added GND tie wire Pin 4→Pin 9")

# N5: GND extension below Pin 9
new_elements.append(f'  (wire (pts (xy 150.16 32.54) (xy 150.16 35)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))')
print("N5. Added GND extension wire to (150.16, 35)")

# N6: GND power symbol at (150.16, 35)
gnd_uuid = gen_uuid()
pin_uuid = gen_uuid()
new_elements.append(f'  (symbol (lib_id "power:GND") (at 150.16 35 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{gnd_uuid}")\n    (property "Reference" "#PWR0152" (at 150.16 35 0) (effects (font (size 1.27 1.27)) (hide yes)))\n    (property "Value" "GND" (at 150.16 35 0) (effects (font (size 1.27 1.27)) (hide yes)))\n    (property "Footprint" "" (at 150.16 35 0) (effects (font (size 1.27 1.27)) (hide yes)))\n    (property "Datasheet" "" (at 150.16 35 0) (effects (font (size 1.27 1.27)) (hide yes)))\n    (pin "1" (uuid "{pin_uuid}"))\n    (instances\n      (project "aurora-dsp-icepower-booster"\n  (path "/09fde901-d8c0-4b5a-a63a-824cb2cd0bb6" (reference "#PWR0152") (unit 1)))))')
print("N6. Added GND power symbol at (150.16, 35)")

# Insert
new_text = '\n' + '\n'.join(new_elements)
content = content[:insert_before] + new_text + content[insert_before:]
print(f"\n--- Inserted {len(new_elements)} new elements ---")

# ─── Validate ───
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"\n✅ Brackets balanced")
print(f"   Original: {original_len}, Final: {len(content)}")

# Verify wire depths
for marker in ['(wire (pts (xy 129.84 22.38) (xy 129.84 24.92))',
               '(wire (pts (xy 150.16 22.38) (xy 150.16 27.46))']:
    pos = content.find(marker)
    d = 0
    for ch in content[:pos]:
        if ch == '(': d += 1
        elif ch == ')': d -= 1
    assert d == 1, f"Wire at depth {d} instead of 1: {marker[:50]}"
print("   All new wires at depth 1 ✅")

with open(SCH, 'w') as f:
    f.write(content)
print("✅ Schematic saved")

# Netlist export test
r = subprocess.run([
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "sch", "export", "netlist", "--output", "/tmp/u14_fix.net", SCH
], capture_output=True, text=True, timeout=30)
print(f"   Netlist: {'OK' if r.returncode == 0 else 'FAILED'} (rc={r.returncode})")
if r.returncode != 0:
    print(f"   stderr: {r.stderr[:500]}")
