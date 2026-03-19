#!/usr/bin/env python3
"""
Fix U1 (TEL5-2422) wire routing.

U1 at (80, 40), rotation 0°
Old pin endpoints at body edge: left x=72.38, right x=87.62
New pin endpoints at ±10.16 from center: left x=69.84, right x=90.16

Verified existing wires:
  (50 37.46) → (72.38 37.46)      old +VIN, label +24V_IN chain
  (37.62 42.54) → (72.38 42.54)   old -VIN GND chain
  (87.62 34.92) → (85.08 34.92)   old +VOUT → +12V_RAW label
  (87.62 40) → (85.08 40)         old COM → GND at (85.08, 40)
  (87.62 45.08) → (85.08 45.08)   old -VOUT → -12V_RAW label

New pin layout:
  Left:  Pin 22(+VIN) y=34.92  Pin 23(+VIN) y=37.46
         Pin 2(GND)   y=40     Pin 3(GND)   y=42.54
  Right: Pin 14(+VOUT) y=34.92  Pin 16(COM) y=37.46
         Pin 9(COM)    y=42.54  Pin 11(-VOUT) y=45.08
"""

import uuid, subprocess

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, 'r') as f:
    content = f.read()

original_len = len(content)

def gen_uuid():
    return str(uuid.uuid4())

changes = 0

# ─── 1. Left wire +VIN: extend from 72.38 to 69.84 ───
old = '(wire (pts (xy 50 37.46) (xy 72.38 37.46))'
new = '(wire (pts (xy 50 37.46) (xy 69.84 37.46))'
assert old in content, f"Wire not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"1. +VIN wire extended to Pin 23")

# ─── 2. Left wire GND: extend from 72.38 to 69.84 ───
old = '(wire (pts (xy 37.62 42.54) (xy 72.38 42.54))'
new = '(wire (pts (xy 37.62 42.54) (xy 69.84 42.54))'
assert old in content, f"Wire not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"2. GND wire extended to Pin 3")

# ─── 3. Right wire +VOUT: extend from 87.62 to 90.16 ───
old = '(wire (pts (xy 87.62 34.92) (xy 85.08 34.92))'
new = '(wire (pts (xy 90.16 34.92) (xy 85.08 34.92))'
assert old in content, f"Wire not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"3. +VOUT wire extended to Pin 14")

# ─── 4. Right wire -VOUT: extend from 87.62 to 90.16 ───
old = '(wire (pts (xy 87.62 45.08) (xy 85.08 45.08))'
new = '(wire (pts (xy 90.16 45.08) (xy 85.08 45.08))'
assert old in content, f"Wire not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"4. -VOUT wire extended to Pin 11")

# ─── 5. Right wire COM→GND: extend x from 87.62 to 90.16 ───
old = '(wire (pts (xy 87.62 40) (xy 85.08 40))'
new = '(wire (pts (xy 90.16 40) (xy 85.08 40))'
assert old in content, f"Wire not found: {old}"
content = content.replace(old, new, 1)
changes += 1
print(f"5. COM→GND wire extended to x=90.16")

# ─── 6-9: New wires ───
new_wires = [
    # 6. Vertical: Pin 16 (90.16, 37.46) → junction (90.16, 40)
    f'  (wire (pts (xy 90.16 37.46) (xy 90.16 40)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))',
    # 7. Vertical: Pin 9 (90.16, 42.54) → junction (90.16, 40)
    f'  (wire (pts (xy 90.16 42.54) (xy 90.16 40)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))',
    # 8. Vertical: Pin 22 (69.84, 34.92) → Pin 23 (69.84, 37.46)
    f'  (wire (pts (xy 69.84 34.92) (xy 69.84 37.46)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))',
    # 9. Vertical: Pin 2 (69.84, 40) → Pin 3 (69.84, 42.54)
    f'  (wire (pts (xy 69.84 40) (xy 69.84 42.54)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))',
]

# Junction at (90.16, 40) where 3 wires meet
new_junction = f'  (junction (at 90.16 40) (diameter 0) (color 0 0 0 0) (uuid "{gen_uuid()}"))'

# Insert new elements before the last closing paren
insert_pos = content.rfind('\n)')
new_text = '\n' + '\n'.join(new_wires) + '\n' + new_junction
content = content[:insert_pos] + new_text + content[insert_pos:]
print(f"6-9. Added 4 new wires + 1 junction")

# ─── Validate bracket balance ───
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"\n✅ Bracket balance OK")
print(f"   Original: {original_len}, New: {len(content)}, Delta: +{len(content) - original_len}")

with open(SCH, 'w') as f:
    f.write(content)
print(f"✅ Schematic saved")

# Netlist export test
r = subprocess.run([
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "sch", "export", "netlist", "--output", "/tmp/u1_fix_netlist.net", SCH
], capture_output=True, text=True, timeout=30)
print(f"   Netlist export: {'OK' if r.returncode == 0 else 'FAILED'} (rc={r.returncode})")
if r.returncode != 0:
    print(f"   stderr: {r.stderr[:500]}")
