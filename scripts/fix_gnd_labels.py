#!/usr/bin/env python3
"""F1 Fix: Replace all 143 GND labels with power:GND symbols.

Root Cause: Regular labels don't create power nets. When a "GND" label and a "CH1_OUT_COLD" 
label exist on the same wire chain, KiCad merges them alphabetically → CH1_OUT_COLD wins.

Fix: Replace all (label "GND" ...) with (symbol (lib_id "power:GND") ...) power symbols.
Power symbols create global power nets that KiCad treats differently from regular labels.

Each power:GND symbol needs:
1. A lib_symbols cache entry for power:GND (once)
2. A (symbol (lib_id "power:GND") ...) instance at each label position
3. Pin "1" connected to the wire at that position
4. A unique #PWR reference designator
5. Remove the original (label "GND" ...) entry
"""

import re
import sys
import os
import uuid as uuid_mod

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sch")
KICAD_SYMBOLS = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/power.kicad_sym"

def extract_balanced_block(content, start_idx):
    depth = 0
    for i in range(start_idx, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
        if depth == 0:
            return content[start_idx:i + 1], i + 1
    raise ValueError(f"Unbalanced parens at {start_idx}")

def check_balance(content, label=""):
    depth = 0
    for ch in content:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    if depth != 0:
        raise ValueError(f"Bracket balance {label}: {depth}")
    print(f"  ✓ Bracket balance OK {label}")

def fmt(v):
    """Format coordinate value: integers as X.0, else as-is."""
    if v == int(v):
        return f"{int(v)}"
    return f"{v}"

print("=" * 60)
print("F1: Replace 143 GND labels with power:GND symbols")
print("=" * 60)

with open(SCH_FILE, 'r') as f:
    sch = f.read()

print(f"\nSchematic: {len(sch)} chars")
check_balance(sch, "(original)")

# ============================================================
# STEP 1: Extract power:GND from KiCad system library
# ============================================================
print("\n--- Extracting power:GND from system library ---")
with open(KICAD_SYMBOLS, 'r') as f:
    power_lib = f.read()

idx = power_lib.find('(symbol "GND"')
gnd_sym_block, _ = extract_balanced_block(power_lib, idx)

# Convert to cache format: add library prefix "power:" to main symbol name
# Sub-symbols keep bare names (per SKILL.md rule 3)
cache_entry = gnd_sym_block.replace('(symbol "GND"', '(symbol "power:GND"', 1)
# The sub-symbols "GND_0_1" and "GND_1_1" should NOT have "power:" prefix — they stay as-is
check_balance(cache_entry, "(GND cache entry)")
print(f"  Cache entry: {len(cache_entry)} chars")

# ============================================================
# STEP 2: Find all GND labels and collect their data
# ============================================================
print("\n--- Finding all GND labels ---")

gnd_labels = []
for m in re.finditer(r'\(label "GND" \(at ([\d.]+) ([\d.]+) (\d+)\)', sch):
    x, y, angle = m.group(1), m.group(2), m.group(3)
    block_start = m.start()
    block, block_end = extract_balanced_block(sch, block_start)
    uuid_m = re.search(r'\(uuid "([^"]+)"\)', block)
    gnd_labels.append({
        'x': x, 'y': y, 'angle': angle,
        'uuid': uuid_m.group(1) if uuid_m else str(uuid_mod.uuid4()),
        'start': block_start, 'end': block_end,
        'block': block
    })

print(f"  Found {len(gnd_labels)} GND labels")

# ============================================================
# STEP 3: Find existing #PWR references to avoid duplicates
# ============================================================
existing_pwr = set()
for m in re.finditer(r'reference "#PWR(\d+)"', sch):
    existing_pwr.add(int(m.group(1)))

# Also check (property "Reference" "#PWRxxx" patterns
for m in re.finditer(r'"Reference" "#PWR(\d+)"', sch):
    existing_pwr.add(int(m.group(1)))

print(f"  Existing #PWR references: {sorted(existing_pwr)}")

# Start numbering from max+1
pwr_counter = max(existing_pwr) + 1 if existing_pwr else 1

# ============================================================
# STEP 4: Build replacement power:GND symbol instances
# ============================================================
print("\n--- Building power:GND symbol instances ---")

# The power:GND symbol has a single pin at (0,0) with angle 270° (pointing down).
# When we place the symbol at a label position, the pin connects where the label was.
# However, labels in KiCad connect at their anchor point, and power symbols connect
# at their pin position relative to the symbol origin.
#
# For power:GND: The pin is at local (0,0) with 270° direction.
# The GND triangle graphic is below, the pin connection point is at origin.
# So placing the symbol at the same (x,y) as the old label should work.

# Project UUID for instances path
project_uuid = "09fde901-d8c0-4b5a-a63a-824cb2cd0bb6"

replacements = []
for i, lbl in enumerate(gnd_labels):
    pwr_ref = f"#PWR{pwr_counter:03d}"
    pwr_counter += 1
    sym_uuid = str(uuid_mod.uuid4())
    pin_uuid = str(uuid_mod.uuid4())
    
    x, y, angle = lbl['x'], lbl['y'], lbl['angle']
    
    # Build power:GND symbol instance
    sym_instance = (
        f'(symbol (lib_id "power:GND") (at {x} {y} 0) (unit 1)'
        f' (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
        f' (uuid "{sym_uuid}")\n'
        f'    (property "Reference" "{pwr_ref}" (at {x} {y} 0)'
        f' (effects (font (size 1.27 1.27)) (hide yes)))\n'
        f'    (property "Value" "GND" (at {x} {y} 0)'
        f' (effects (font (size 1.27 1.27)) (hide yes)))\n'
        f'    (property "Footprint" "" (at {x} {y} 0)'
        f' (effects (font (size 1.27 1.27)) (hide yes)))\n'
        f'    (property "Datasheet" "" (at {x} {y} 0)'
        f' (effects (font (size 1.27 1.27)) (hide yes)))\n'
        f'    (pin "1" (uuid "{pin_uuid}"))\n'
        f'    (instances\n'
        f'      (project "aurora-dsp-icepower-booster"\n'
        f'  (path "/{project_uuid}" (reference "{pwr_ref}") (unit 1)))))'
    )
    
    check_balance(sym_instance, f"(GND sym #{i+1})")
    replacements.append({
        'old_start': lbl['start'],
        'old_end': lbl['end'],
        'new_text': sym_instance
    })

print(f"  Built {len(replacements)} replacement instances")

# ============================================================
# STEP 5: Apply all replacements (reverse order to preserve positions)
# ============================================================
print("\n--- Applying replacements ---")

# Sort by start position in reverse to avoid offset issues
replacements.sort(key=lambda r: r['old_start'], reverse=True)

new_sch = sch
for r in replacements:
    new_sch = new_sch[:r['old_start']] + r['new_text'] + new_sch[r['old_end']:]

# ============================================================
# STEP 6: Add power:GND to lib_symbols cache
# ============================================================
print("--- Adding power:GND to lib_symbols cache ---")

# Find the lib_symbols section
lib_sym_match = re.search(r'\(lib_symbols', new_sch)
if not lib_sym_match:
    print("ERROR: lib_symbols section not found!")
    sys.exit(1)

# Insert after (lib_symbols
insert_pos = lib_sym_match.end()
# Add a newline + the cache entry
new_sch = new_sch[:insert_pos] + '\n    ' + cache_entry + '\n' + new_sch[insert_pos:]

# ============================================================
# STEP 7: Validate and write
# ============================================================
print("\n--- Validation ---")
check_balance(new_sch, "(after F1 fix)")

# Verify no more (label "GND" ...) remain
remaining = len(re.findall(r'\(label "GND"', new_sch))
print(f"  Remaining GND labels: {remaining}")
if remaining > 0:
    print("  WARNING: Some GND labels were not replaced!")

# Count power:GND instances
power_gnd_count = len(re.findall(r'lib_id "power:GND"', new_sch))
print(f"  power:GND instances: {power_gnd_count}")

with open(SCH_FILE, 'w') as f:
    f.write(new_sch)
print(f"\n✓ Schematic written: {len(new_sch)} chars")

print("\n" + "=" * 60)
print(f"F1 COMPLETE — {len(replacements)} GND labels → power:GND symbols")
print("  This should fix F1, F2, F3, F7, F8 (cascade)")
print("=" * 60)
