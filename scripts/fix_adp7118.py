#!/usr/bin/env python3
"""F9 Fix: Replace ADP7118ACPZN (7-pin LFCSP) with ADP7118ARDZ-R7 (9-pin SOIC-8+EP).

Current state:
  - lib_id: Regulator_Linear:ADP7118ACPZN (7 pins: 1=VOUT, 2=SENSE, 3=GND, 4=EN, 5=SS, 6=VIN, 7=GND)
  - Value: ADP7118ARDZ-11
  - Footprint: Package_SO:SOIC-8_3.9x4.9mm_P1.27mm

Target:
  - lib_id: aurora-dsp-icepower-booster:ADP7118ARDZ (custom, 9 pins)
  - Value: ADP7118ARDZ-11
  - Footprint: project:SOIC127P600X175-9N (with exposed pad)
  - Pins: 1,2=VOUT, 3=SENSE/ADJ, 4=GND, 5=EN, 6=SS, 7,8=VIN, 9=GND(EP)

Pin mapping (ACPZN → ARDZ):
  ACPZN Pin 1 (VOUT)  → ARDZ Pin 1 (VOUT)
  ACPZN Pin 2 (SENSE) → ARDZ Pin 3 (SENSE/ADJ)
  ACPZN Pin 3 (GND)   → ARDZ Pin 4 (GND)
  ACPZN Pin 4 (EN)    → ARDZ Pin 5 (EN)
  ACPZN Pin 5 (SS)    → ARDZ Pin 6 (SS)
  ACPZN Pin 6 (VIN)   → ARDZ Pin 7 (VIN)
  ACPZN Pin 7 (GND)   → ARDZ Pin 4 (GND, same as pin 3 mapping — MERGED)
  New pins: 2 (VOUT), 8 (VIN), 9 (GND EP)
"""

import re
import sys
import os
import uuid as uuid_mod

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sch")

def extract_balanced_block(content, start_idx):
    depth = 0
    for i in range(start_idx, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
        if depth == 0:
            return content[start_idx:i + 1], i + 1
    raise ValueError(f"Unbalanced parens starting at {start_idx}")

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

print("=" * 60)
print("F9: ADP7118 ACPZN → ARDZ Symbol + Footprint Fix")
print("=" * 60)

with open(SCH_FILE, 'r') as f:
    sch = f.read()

print(f"\nSchematic: {len(sch)} chars")
check_balance(sch, "(original)")

# ============================================================
# STEP 1: Find and replace lib_symbols cache entry
# ============================================================
cache_match = re.search(r'\(symbol "Regulator_Linear:ADP7118ACPZN"', sch)
if not cache_match:
    print("ERROR: ADP7118ACPZN cache entry not found!")
    sys.exit(1)

cache_block, cache_end = extract_balanced_block(sch, cache_match.start())
cache_start = cache_match.start()
print(f"\nOld cache entry: chars {cache_start}-{cache_end}, {len(cache_block)} chars")
print(cache_block[:500])

# Build new cache entry for ADP7118ARDZ
# Based on ARDZ-R7 datasheet: Pin 1,2=VOUT, 3=SENSE/ADJ, 4=GND, 5=EN, 6=SS, 7,8=VIN, 9=GND(EP)
new_cache = '''(symbol "aurora-dsp-icepower-booster:ADP7118ARDZ" (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ADP7118ARDZ" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "project:SOIC127P600X175-9N" (at 0 -5.08 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "https://www.analog.com/media/en/technical-documentation/data-sheets/ADP7118.pdf" (at 0 -7.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "Analog Devices ADP7118ARDZ, 200mA Low-Noise LDO, adj/fixed, SOIC-8 with Exposed Pad" (at 0 -10.16 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "ki_keywords" "LDO regulator low-noise ADP7118" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "ADP7118ARDZ_0_1"
        (rectangle (start -7.62 8.89) (end 7.62 -11.43) (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "ADP7118ARDZ_1_1"
        (pin power_out line (at 10.16 7.62 180) (length 2.54) (name "VOUT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 10.16 5.08 180) (length 2.54) (name "VOUT" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin input line (at 10.16 2.54 180) (length 2.54) (name "SENSE/ADJ" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 10.16 0 180) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at -10.16 2.54 0) (length 2.54) (name "EN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at -10.16 0 0) (length 2.54) (name "SS" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -10.16 7.62 0) (length 2.54) (name "VIN" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -10.16 5.08 0) (length 2.54) (name "VIN" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 10.16 -2.54 180) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27))))))
      (embedded_fonts no))'''

check_balance(new_cache, "(new ADP7118 cache)")

# ============================================================
# STEP 2: Find U14 instance
# ============================================================
u14_match = re.search(r'\(symbol \(lib_id "Regulator_Linear:ADP7118ACPZN"\)', sch)
if not u14_match:
    print("ERROR: U14 ADP7118 instance not found!")
    sys.exit(1)

u14_block, u14_end = extract_balanced_block(sch, u14_match.start())
u14_start = u14_match.start()
print(f"\nU14 instance: chars {u14_start}-{u14_end}, {len(u14_block)} chars")
print(u14_block)

# Extract pin entries
pin_entries = []
for pin_m in re.finditer(r'\(pin "(\d+)" \(uuid "([^"]+)"\)\)', u14_block):
    pin_entries.append((pin_m.group(1), pin_m.group(2)))
    print(f"  Pin {pin_m.group(1)} → UUID {pin_m.group(2)}")

# ============================================================
# STEP 3: Build new U14 instance
# ============================================================
# Pin mapping: ACPZN → ARDZ
# ACPZN  1 (VOUT)  → ARDZ 1 (VOUT)
# ACPZN  2 (SENSE) → ARDZ 3 (SENSE/ADJ)
# ACPZN  3 (GND)   → ARDZ 4 (GND)
# ACPZN  4 (EN)    → ARDZ 5 (EN)
# ACPZN  5 (SS)    → ARDZ 6 (SS)
# ACPZN  6 (VIN)   → ARDZ 7 (VIN)
# ACPZN  7 (GND)   → ARDZ 9 (GND EP — better thermal)

pin_remap = {
    "1": "1",   # VOUT → VOUT
    "2": "3",   # SENSE → SENSE/ADJ
    "3": "4",   # GND → GND
    "4": "5",   # EN → EN
    "5": "6",   # SS → SS
    "6": "7",   # VIN → VIN
    "7": "9",   # GND → GND (EP)
}

new_u14 = u14_block

# Change lib_id
new_u14 = new_u14.replace(
    'lib_id "Regulator_Linear:ADP7118ACPZN"',
    'lib_id "aurora-dsp-icepower-booster:ADP7118ARDZ"'
)

# Change footprint
new_u14 = new_u14.replace(
    'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    'project:SOIC127P600X175-9N'
)

# Change value (keep ARDZ-11 but remove the mismatch)
# Value is already ADP7118ARDZ-11, that's fine

# Remap pins
for old_pin, old_uuid in pin_entries:
    new_pin = pin_remap.get(old_pin, old_pin)
    old_str = f'(pin "{old_pin}" (uuid "{old_uuid}"))'
    new_str = f'(pin "{new_pin}" (uuid "{old_uuid}"))'
    new_u14 = new_u14.replace(old_str, new_str)

# Add extra pins (2=VOUT, 8=VIN)
extra_pins = [
    ("2", str(uuid_mod.uuid4())),   # VOUT second pin
    ("8", str(uuid_mod.uuid4())),   # VIN second pin
]

# Find last pin entry and add after it
last_pin_idx = new_u14.rfind('(pin "')
last_pin_end = new_u14.find(')', new_u14.find(')', last_pin_idx) + 1) + 1
insert_point = last_pin_end

extra_pin_text = ""
for pin, uid in extra_pins:
    extra_pin_text += f'\n    (pin "{pin}" (uuid "{uid}"))'

new_u14 = new_u14[:insert_point] + extra_pin_text + new_u14[insert_point:]

check_balance(new_u14, "(new U14)")
print(f"\n--- New U14 instance ---")
print(new_u14)

# ============================================================
# STEP 4: Apply changes  
# ============================================================
print("\n--- Applying changes ---")

# Replace cache
new_sch = sch[:cache_start] + new_cache + sch[cache_end:]
print(f"  Cache replaced: {len(cache_block)} → {len(new_cache)} chars")

# Re-find U14 in modified content
u14_match2 = re.search(r'\(symbol \(lib_id "Regulator_Linear:ADP7118ACPZN"\)', new_sch)
if u14_match2:
    # Still found old reference — this means the instance wasn't in the cache
    u14_block2, u14_end2 = extract_balanced_block(new_sch, u14_match2.start())
    new_sch = new_sch[:u14_match2.start()] + new_u14 + new_sch[u14_end2:]
else:
    # The instance lib_id already changed (unlikely)
    u14_match2 = re.search(r'\(symbol \(lib_id "aurora-dsp-icepower-booster:ADP7118ARDZ"\)', new_sch)
    if u14_match2:
        u14_block2, u14_end2 = extract_balanced_block(new_sch, u14_match2.start())
        new_sch = new_sch[:u14_match2.start()] + new_u14 + new_sch[u14_end2:]

check_balance(new_sch, "(after all edits)")

# ============================================================
# STEP 5: Write and validate
# ============================================================
with open(SCH_FILE, 'w') as f:
    f.write(new_sch)
print(f"\n✓ Schematic written: {len(new_sch)} chars")

# ============================================================
# STEP 6: Copy SOIC127P600X175-9N footprint to project
# ============================================================
fp_src = "/tmp/fp_extract/ADP7118ARDZ/SOIC127P600X175-9N.kicad_mod"
fp_dest_dir = os.path.join(PROJECT_DIR, "footprints.pretty")
fp_dest = os.path.join(fp_dest_dir, "SOIC127P600X175-9N.kicad_mod")

if os.path.exists(fp_src):
    with open(fp_src, 'r') as f:
        fp_content = f.read()
    with open(fp_dest, 'w') as f:
        f.write(fp_content)
    print(f"✓ Footprint copied to {fp_dest}")
else:
    print(f"WARNING: Footprint source not found at {fp_src}")
    print("  You may need to re-extract from footprints/ADP7118ARDZ.zip")

# ============================================================
# STEP 7: Update custom symbol library (add ADP7118ARDZ)
# ============================================================
with open(os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sym"), 'r') as f:
    sym_lib = f.read()

# Insert new symbol before the closing )
new_sym_entry = '''
  (symbol "ADP7118ARDZ"
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "U"
      (at 2.54 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "ADP7118ARDZ"
      (at 0 -2.54 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "project:SOIC127P600X175-9N"
      (at 0 -5.08 0)
      (effects (font (size 1.27 1.27)))
      (hide yes)
    )
    (property "Datasheet" "https://www.analog.com/media/en/technical-documentation/data-sheets/ADP7118.pdf"
      (at 0 -7.62 0)
      (effects (font (size 1.27 1.27)))
      (hide yes)
    )
    (property "Description" "Analog Devices ADP7118ARDZ, 200mA Low-Noise LDO, SOIC-8 with Exposed Pad"
      (at 0 -10.16 0)
      (effects (font (size 1.27 1.27)))
      (hide yes)
    )
    (property "ki_keywords" "LDO regulator low-noise ADP7118"
      (at 0 0 0)
      (effects (font (size 1.27 1.27)))
      (hide yes)
    )
    (symbol "ADP7118ARDZ_0_1"
      (rectangle
        (start -7.62 8.89)
        (end 7.62 -11.43)
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
    )
    (symbol "ADP7118ARDZ_1_1"
      (pin power_out line (at 10.16 7.62 180) (length 2.54) (name "VOUT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin power_out line (at 10.16 5.08 180) (length 2.54) (name "VOUT" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      (pin input line (at 10.16 2.54 180) (length 2.54) (name "SENSE/ADJ" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at 10.16 0 180) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      (pin input line (at -10.16 2.54 0) (length 2.54) (name "EN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      (pin input line (at -10.16 0 0) (length 2.54) (name "SS" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at -10.16 7.62 0) (length 2.54) (name "VIN" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at -10.16 5.08 0) (length 2.54) (name "VIN" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at 10.16 -2.54 180) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))
    )
  )'''

# Insert before the last closing paren of the lib
last_close = sym_lib.rstrip().rfind(')')
new_sym_lib = sym_lib[:last_close] + new_sym_entry + '\n)\n'

check_balance(new_sym_lib, "(symbol library)")

with open(os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sym"), 'w') as f:
    f.write(new_sym_lib)
print(f"✓ Symbol library updated: {len(new_sym_lib)} chars")

print("\n" + "=" * 60)
print("F9 COMPLETE — ADP7118 ACPZN → ARDZ replaced")
print("  Old: 7 pins (ACPZN, LFCSP-6)")
print("  New: 9 pins (ARDZ, SOIC-8 + EP)")
print("  Footprint: project:SOIC127P600X175-9N")
print("  Pin remap: 1→1, 2→3, 3→4, 4→5, 5→6, 6→7, 7→9")
print("  New pins: 2 (VOUT), 8 (VIN)")
print("=" * 60)
