#!/usr/bin/env python3
"""Replace J2 AudioJack2 with KH-PJ-320EA-5P-SMT and add J15 passthrough jack.

Operations:
1. Remove old AudioJack2 lib_symbols cache entry
2. Add new KH-PJ-320EA-5P-SMT lib_symbols cache entry
3. Remove old J2 symbol instance + associated wires + GND power
4. Add new J2 symbol instance with wires, no_connect, GND
5. Add J15 symbol instance with wires, no_connect, GND, label
6. Validate bracket balance
"""
import re
import uuid
import sys
import os

SCH_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "aurora-dsp-icepower-booster.kicad_sch")
PROJECT_UUID = "09fde901-d8c0-4b5a-a63a-824cb2cd0bb6"

def gen_uuid():
    return str(uuid.uuid4())

def check_bracket_balance(text):
    depth = 0
    for ch in text:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    return depth

def check_balance_lines(lines, label=""):
    b = check_bracket_balance(''.join(lines))
    print(f"  [Balance after {label}]: {b}")
    return b

def check_block_balance(text, label=""):
    b = check_bracket_balance(text)
    if b != 0:
        print(f"  WARNING: Block '{label}' has balance {b}")
    return b

def find_block_end(text, start):
    """Find matching closing paren for opening paren at start."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1

def remove_line_block(lines, start_line_0based, match_func=None):
    """Remove a block of lines starting from start_line_0based.
    Tracks bracket balance until depth returns to 0."""
    depth = 0
    end = start_line_0based
    started = False
    for i in range(start_line_0based, len(lines)):
        line = lines[i]
        for ch in line:
            if ch == '(':
                depth += 1
                started = True
            elif ch == ')':
                depth -= 1
        if started and depth <= 0:
            end = i
            break
    removed = lines[start_line_0based:end + 1]
    del lines[start_line_0based:end + 1]
    return removed

def remove_line_by_uuid(lines, target_uuid):
    """Remove a single-line element by UUID."""
    for i, line in enumerate(lines):
        if target_uuid in line:
            removed = lines.pop(i)
            return removed
    return None

def remove_block_by_uuid(lines, target_uuid):
    """Remove a multi-line block (symbol instance, etc.) by UUID on first line."""
    for i, line in enumerate(lines):
        if target_uuid in line:
            return remove_line_block(lines, i)
    return None

# ---- Main ----
print(f"Reading {SCH_PATH}")
with open(SCH_PATH, 'r') as f:
    lines = f.readlines()
print(f"  {len(lines)} lines read")

orig_balance = check_bracket_balance(''.join(lines))
print(f"  Original bracket balance: {orig_balance}")
assert orig_balance == 0, "Original file has unbalanced brackets!"

# === Step 1: Remove old AudioJack2 lib_symbols cache ===
print("\n--- Step 1: Remove AudioJack2 lib_symbols cache ---")
aj2_cache_start = None
for i, line in enumerate(lines):
    if '"Connector_Audio:AudioJack2"' in line and 'symbol' in line and 'lib_id' not in line:
        aj2_cache_start = i
        break

if aj2_cache_start is not None:
    removed = remove_line_block(lines, aj2_cache_start)
    print(f"  Removed {len(removed)} lines starting at line {aj2_cache_start + 1}")
    check_block_balance(''.join(removed), "removed AudioJack2 cache")
else:
    print("  WARNING: AudioJack2 cache not found!")
check_balance_lines(lines, "step 1")

# === Step 2: Add new lib_symbols cache entry ===
print("\n--- Step 2: Add KH-PJ-320EA-5P-SMT lib_symbols cache ---")

# The lib_symbols cache entry needs the library prefix for the main symbol name,
# but sub-symbols must NOT have the prefix.
new_cache = '''      (symbol "aurora-dsp-icepower-booster:KH-PJ-320EA-5P-SMT" (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Value" "KH-PJ-320EA-5P-SMT" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "aurora-dsp-icepower-booster:AUDIO-SMD_KH-PJ-320EA-5P-SMT" (at 0 -11.43 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "https://www.lcsc.com/datasheet/C5123132.pdf" (at 0 -13.97 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "3.5mm Stereo Audio Jack SMD 5-Pin with detect switches, Kinghelm, LCSC C5123132" (at 0 -16.51 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "LCSC" "C5123132" (at 0 -19.05 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "ki_keywords" "audio jack 3.5mm stereo SMD connector" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
        (symbol "KH-PJ-320EA-5P-SMT_0_1"
        (polyline (pts (xy -2.54 5.08) (xy 0 5.08) (xy 0.635 4.445) (xy 1.27 5.08)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.54 0) (xy 0 0) (xy 0.635 0.635) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.54 -5.08) (xy 0 -5.08)) (stroke (width 0) (type default)) (fill (type none)))
        (rectangle (start -2.54 7.62) (end -3.81 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
        (polyline (pts (xy -2.54 2.54) (xy -1.27 2.54) (xy -1.27 -2.54) (xy -2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none))))
        (symbol "KH-PJ-320EA-5P-SMT_1_1"
        (pin passive line (at 3.81 5.08 180) (length 2.54) (name "T" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 2.54 180) (length 2.54) (name "R1" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "R1N" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 -2.54 180) (length 2.54) (name "S" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 -5.08 180) (length 2.54) (name "TN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27))))))
    (embedded_fonts no))
'''

# Find insertion point: right where the AudioJack2 cache was removed
# (which is inside lib_symbols, before the next symbol entry)
if aj2_cache_start is not None:
    insert_idx = aj2_cache_start
else:
    # Fallback: find the end of lib_symbols by searching for first junction/wire/no_connect
    insert_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('(junction') or stripped.startswith('(no_connect') or stripped.startswith('(wire'):
            insert_idx = i
            break

if insert_idx is not None:
    cache_lines = [l + '\n' for l in new_cache.strip().split('\n')]
    check_block_balance(''.join(cache_lines), "new cache entry")
    for j, cl in enumerate(cache_lines):
        lines.insert(insert_idx + j, cl)
    print(f"  Inserted {len(cache_lines)} cache lines at line {insert_idx + 1}")
else:
    print("  ERROR: Could not find insertion point for cache!")
    sys.exit(1)
check_balance_lines(lines, "step 2")

# === Step 3: Remove old J2 symbol instance ===
print("\n--- Step 3: Remove old J2 symbol instance ---")
j2_uuid = "8c6dff62-aeae-48cc-8519-dc508c401114"
removed = remove_block_by_uuid(lines, j2_uuid)
if removed:
    print(f"  Removed J2 block ({len(removed)} lines)")
    check_block_balance(''.join(removed), "removed J2 block")
else:
    print("  ERROR: J2 symbol not found!")
    sys.exit(1)
check_balance_lines(lines, "step 3")

# === Step 4: Remove old wires and GND ===
print("\n--- Step 4: Remove old wires and GND ---")

# Wire: (35.08, 82.46) → (35.08, 90) — old Pin S to GND
w1 = remove_line_by_uuid(lines, "7f8a93e5-39ea-4a0c-8ab8-0344171969d6")
print(f"  Wire S→GND: {'removed' if w1 else 'NOT FOUND'}")
if w1: check_block_balance(w1, "wire S→GND")

# Wire: (35.08, 85) → (42, 85) — old Pin T to junction
w2 = remove_line_by_uuid(lines, "e524c47d-7093-4ad4-9c84-f534e0cfb2ac")
print(f"  Wire T→junction: {'removed' if w2 else 'NOT FOUND'}")
if w2: check_block_balance(w2, "wire T→junction")

# Wire: (42, 85) → (42, 82.46) — junction to REMOTE_IN
w3 = remove_line_by_uuid(lines, "731e69bb-01ca-480b-a618-2885e765c2c3")
print(f"  Wire junction→REMOTE_IN: {'removed' if w3 else 'NOT FOUND'}")
if w3: check_block_balance(w3, "wire junction→REMOTE_IN")

# GND #PWR047 at (35.08, 90)
gnd_uuid = "ced98098-0919-4b57-bd4b-a0806d40ceb4"
removed_gnd = remove_block_by_uuid(lines, gnd_uuid)
print(f"  GND #PWR047: {'removed (' + str(len(removed_gnd)) + ' lines)' if removed_gnd else 'NOT FOUND'}")
if removed_gnd: check_block_balance(''.join(removed_gnd), "removed GND #PWR047")
check_balance_lines(lines, "step 4")

# === Step 5: Add new J2 ===
print("\n--- Step 5: Add new J2 symbol ---")

# J2 at (30, 85), new symbol
# Pin positions (schematic coords, Y inverted):
#   Pin 1 (T):   (33.81, 79.92)
#   Pin 2 (R1):  (33.81, 82.46)
#   Pin 3 (R1N): (33.81, 85.0)
#   Pin 4 (S):   (33.81, 87.54)
#   Pin 5 (TN):  (33.81, 90.08)

j2_new_uuid = gen_uuid()
j2_pin1_uuid = gen_uuid()
j2_pin2_uuid = gen_uuid()
j2_pin3_uuid = gen_uuid()
j2_pin4_uuid = gen_uuid()
j2_pin5_uuid = gen_uuid()

j2_symbol = f'''    (symbol (lib_id "aurora-dsp-icepower-booster:KH-PJ-320EA-5P-SMT") (at 30 85 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{j2_new_uuid}")
    (property "Reference" "J2" (at 30 74.84 0) (effects (font (size 1.27 1.27))))
    (property "Value" "REMOTE 3.5mm IN" (at 30 93.98 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "aurora-dsp-icepower-booster:AUDIO-SMD_KH-PJ-320EA-5P-SMT" (at 30 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "https://www.lcsc.com/datasheet/C5123132.pdf" (at 30 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Description" "3.5mm Stereo Audio Jack SMD 5-Pin with detect switches, Kinghelm, LCSC C5123132" (at 30 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "LCSC" "C5123132" (at 30 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (pin "1" (uuid "{j2_pin1_uuid}"))
    (pin "2" (uuid "{j2_pin2_uuid}"))
    (pin "3" (uuid "{j2_pin3_uuid}"))
    (pin "4" (uuid "{j2_pin4_uuid}"))
    (pin "5" (uuid "{j2_pin5_uuid}"))
      (instances
        (project "aurora-dsp-icepower-booster"
  (path "/{PROJECT_UUID}" (reference "J2") (unit 1)))))
'''

# === Step 6: Add J15 ===
print("--- Step 6: Add J15 symbol ---")

# J15 at (15, 85) — to the left of J2
# Pin positions:
#   Pin 1 (T):   (18.81, 79.92)
#   Pin 2 (R1):  (18.81, 82.46)
#   Pin 3 (R1N): (18.81, 85.0)
#   Pin 4 (S):   (18.81, 87.54)
#   Pin 5 (TN):  (18.81, 90.08)

j15_uuid = gen_uuid()
j15_pin1_uuid = gen_uuid()
j15_pin2_uuid = gen_uuid()
j15_pin3_uuid = gen_uuid()
j15_pin4_uuid = gen_uuid()
j15_pin5_uuid = gen_uuid()

j15_symbol = f'''    (symbol (lib_id "aurora-dsp-icepower-booster:KH-PJ-320EA-5P-SMT") (at 15 85 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{j15_uuid}")
    (property "Reference" "J15" (at 15 74.84 0) (effects (font (size 1.27 1.27))))
    (property "Value" "REMOTE 3.5mm OUT" (at 15 93.98 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "aurora-dsp-icepower-booster:AUDIO-SMD_KH-PJ-320EA-5P-SMT" (at 15 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "https://www.lcsc.com/datasheet/C5123132.pdf" (at 15 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Description" "3.5mm Stereo Audio Jack SMD 5-Pin with detect switches, Kinghelm, LCSC C5123132" (at 15 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "LCSC" "C5123132" (at 15 85 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (pin "1" (uuid "{j15_pin1_uuid}"))
    (pin "2" (uuid "{j15_pin2_uuid}"))
    (pin "3" (uuid "{j15_pin3_uuid}"))
    (pin "4" (uuid "{j15_pin4_uuid}"))
    (pin "5" (uuid "{j15_pin5_uuid}"))
      (instances
        (project "aurora-dsp-icepower-booster"
  (path "/{PROJECT_UUID}" (reference "J15") (unit 1)))))
'''

# === Step 7: Wires ===
print("--- Step 7: Add wires ---")

# J2 Pin 1 (T) at (33.81, 79.92) → wire right to (42, 79.92) → (42, 82.46)
# This connects to the existing REMOTE_IN junction at (42, 82.46)
j2_wire_t_h = f'  (wire (pts (xy 33.81 79.92) (xy 42 79.92)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))\n'
j2_wire_t_v = f'  (wire (pts (xy 42 79.92) (xy 42 82.46)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))\n'

# J2 Pin 4 (S) at (33.81, 87.54) → wire down past Pin 5 to (33.81, 92.62), GND there
j2_wire_s = f'  (wire (pts (xy 33.81 87.54) (xy 33.81 92.62)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))\n'

# J15 Pin 1 (T) at (18.81, 79.92) → wire right to (23, 79.92), label REMOTE_IN there
j15_wire_t = f'  (wire (pts (xy 18.81 79.92) (xy 23 79.92)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))\n'

# J15 Pin 4 (S) at (18.81, 87.54) → wire down past Pin 5 to (18.81, 92.62), GND there
j15_wire_s = f'  (wire (pts (xy 18.81 87.54) (xy 18.81 92.62)) (stroke (width 0) (type default)) (uuid "{gen_uuid()}"))\n'

# === Step 8: GND power symbols ===
print("--- Step 8: Add GND power symbols ---")

j2_gnd_uuid = gen_uuid()
j2_gnd_pin_uuid = gen_uuid()
j2_gnd = f'''    (symbol (lib_id "power:GND") (at 33.81 92.62 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{j2_gnd_uuid}")
    (property "Reference" "#PWR0154" (at 33.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Value" "GND" (at 33.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Footprint" "" (at 33.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "" (at 33.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (pin "1" (uuid "{j2_gnd_pin_uuid}"))
    (instances
      (project "aurora-dsp-icepower-booster"
  (path "/{PROJECT_UUID}" (reference "#PWR0154") (unit 1)))))
'''

j15_gnd_uuid = gen_uuid()
j15_gnd_pin_uuid = gen_uuid()
j15_gnd = f'''    (symbol (lib_id "power:GND") (at 18.81 92.62 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{j15_gnd_uuid}")
    (property "Reference" "#PWR0155" (at 18.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Value" "GND" (at 18.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Footprint" "" (at 18.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "" (at 18.81 92.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (pin "1" (uuid "{j15_gnd_pin_uuid}"))
    (instances
      (project "aurora-dsp-icepower-booster"
  (path "/{PROJECT_UUID}" (reference "#PWR0155") (unit 1)))))
'''

# === Step 9: No-connect flags ===
print("--- Step 9: Add no_connect flags ---")

# J2 no_connect: pins 2,3,5 at (33.81, 82.46), (33.81, 85.0), (33.81, 90.08)
j2_nc2 = f'  (no_connect (at 33.81 82.46) (uuid "{gen_uuid()}"))\n'
j2_nc3 = f'  (no_connect (at 33.81 85) (uuid "{gen_uuid()}"))\n'
j2_nc5 = f'  (no_connect (at 33.81 90.08) (uuid "{gen_uuid()}"))\n'

# J15 no_connect: pins 2,3,5 at (18.81, 82.46), (18.81, 85.0), (18.81, 90.08)
j15_nc2 = f'  (no_connect (at 18.81 82.46) (uuid "{gen_uuid()}"))\n'
j15_nc3 = f'  (no_connect (at 18.81 85) (uuid "{gen_uuid()}"))\n'
j15_nc5 = f'  (no_connect (at 18.81 90.08) (uuid "{gen_uuid()}"))\n'

# === Step 10: REMOTE_IN label for J15 ===
print("--- Step 10: Add REMOTE_IN label for J15 ---")

j15_label = f'  (label "REMOTE_IN" (at 23 79.92 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{gen_uuid()}"))\n'

# === Step 11: Insert all new elements ===
print("\n--- Step 11: Insert new elements ---")

# Verify each block's balance
for sym, name in [(j2_symbol, "J2 symbol"), (j15_symbol, "J15 symbol"),
                   (j2_gnd, "J2 GND"), (j15_gnd, "J15 GND")]:
    check_block_balance(sym, name)

for w, name in [(j2_wire_t_h, "j2_wire_t_h"), (j2_wire_t_v, "j2_wire_t_v"),
                 (j2_wire_s, "j2_wire_s"), (j15_wire_t, "j15_wire_t"),
                 (j15_wire_s, "j15_wire_s")]:
    check_block_balance(w, name)

for nc, name in [(j2_nc2, "j2_nc2"), (j2_nc3, "j2_nc3"), (j2_nc5, "j2_nc5"),
                  (j15_nc2, "j15_nc2"), (j15_nc3, "j15_nc3"), (j15_nc5, "j15_nc5")]:
    check_block_balance(nc, name)

check_block_balance(j15_label, "j15_label")

# Build all insert content
insert_content = []

# Symbols (each from fstring, stripped and split)
for sym in [j2_symbol, j15_symbol, j2_gnd, j15_gnd]:
    insert_content.extend([l + '\n' for l in sym.strip().split('\n')])

# Wires
insert_content.extend([j2_wire_t_h, j2_wire_t_v, j2_wire_s, j15_wire_t, j15_wire_s])

# No-connect
insert_content.extend([j2_nc2, j2_nc3, j2_nc5, j15_nc2, j15_nc3, j15_nc5])

# Label
insert_content.append(j15_label)

total_insert_balance = check_bracket_balance(''.join(insert_content))
print(f"  Total insert content balance: {total_insert_balance}")

# Insert before the closing paren of kicad_sch
# Find the last line that is just ')'
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == ')':
        # Insert all content at position i, in correct order
        for j, new_line in enumerate(insert_content):
            lines.insert(i + j, new_line)
        print(f"  Inserted {len(insert_content)} lines at position {i}")
        break

# === Step 12: Validate ===
print("\n--- Step 12: Validate ---")
final_text = ''.join(lines)
balance = check_bracket_balance(final_text)
print(f"  Final bracket balance: {balance}")

if balance != 0:
    print(f"  ERROR: Bracket imbalance of {balance}!")
    # Print the last few lines for debugging
    print("  Last 5 lines of file:")
    for ln in lines[-5:]:
        print(f"    |{ln.rstrip()}|")
    sys.exit(1)

# Check key elements exist
checks = [
    ('"aurora-dsp-icepower-booster:KH-PJ-320EA-5P-SMT"', "lib_symbols cache"),
    (f'uuid "{j2_new_uuid}"', "J2 symbol instance"),
    (f'uuid "{j15_uuid}"', "J15 symbol instance"),
    (f'uuid "{j2_gnd_uuid}"', "J2 GND power"),
    (f'uuid "{j15_gnd_uuid}"', "J15 GND power"),
    ('REMOTE_IN', "REMOTE_IN label"),
]

for pattern, name in checks:
    if pattern in final_text:
        print(f"  ✓ {name} present")
    else:
        print(f"  ✗ {name} MISSING!")

# Check no old AudioJack2 reference
if 'Connector_Audio:AudioJack2' in final_text:
    print("  ✗ WARNING: Old AudioJack2 reference still present!")
else:
    print("  ✓ Old AudioJack2 fully removed")

# === Step 13: Write ===
print(f"\n--- Writing {SCH_PATH} ---")
with open(SCH_PATH, 'w') as f:
    f.write(final_text)
print(f"  Written {len(lines)} lines")
print("\nDone!")
