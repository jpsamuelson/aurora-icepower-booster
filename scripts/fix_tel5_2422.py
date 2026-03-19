#!/usr/bin/env python3
"""F10 Fix: Replace TEL5-2422 symbol (wrong pins 1,7,14,18,24) with correct TRACO pinout (2,3,9,11,14,16,22,23).

This script:
1. Replaces the lib_symbols cache entry with the correct symbol (from provided ZIP)
2. Updates the U1 component instance (pin numbers, footprint)
3. Updates the custom .kicad_sym library
4. Rewires connections to match new pin numbers
5. Validates bracket balance
"""

import re
import sys
import os

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sch")
SYM_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sym")

def extract_balanced_block(content, start_idx):
    """Extract a balanced parentheses block starting at start_idx."""
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
    """Check bracket balance."""
    depth = 0
    for ch in content:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    if depth != 0:
        raise ValueError(f"Bracket balance {label}: {depth}")
    print(f"  ✓ Bracket balance OK {label}")

# ============================================================
# STEP 0: Analyze current state
# ============================================================
print("=" * 60)
print("F10: TEL5-2422 Symbol + Footprint Fix")
print("=" * 60)

with open(SCH_FILE, 'r') as f:
    sch = f.read()

print(f"\nSchematic: {len(sch)} chars")
check_balance(sch, "(original)")

# Find U1 instance
u1_match = re.search(r'\(symbol \(lib_id "aurora-dsp-icepower-booster:TEL5-2422"\)', sch)
if not u1_match:
    print("ERROR: U1 TEL5-2422 instance not found!")
    sys.exit(1)

u1_block, u1_end = extract_balanced_block(sch, u1_match.start())
u1_start = u1_match.start()
print(f"\nU1 instance: chars {u1_start}-{u1_end}, {len(u1_block)} chars")

# Find lib_symbols cache entry
cache_match = re.search(r'\(symbol "aurora-dsp-icepower-booster:TEL5-2422"', sch)
if not cache_match:
    print("ERROR: TEL5-2422 cache entry not found!")
    sys.exit(1)

cache_block, cache_end = extract_balanced_block(sch, cache_match.start())
cache_start = cache_match.start()
print(f"Cache entry: chars {cache_start}-{cache_end}, {len(cache_block)} chars")

# Show current pin numbers in U1 instance
print("\n--- Current U1 pin connections ---")
for pin_m in re.finditer(r'\(pin "(\d+)"', u1_block):
    pin_num = pin_m.group(1)
    # Get the uuid after this pin
    pin_start = pin_m.start()
    pin_block, _ = extract_balanced_block(u1_block, pin_m.start() - u1_block.rfind('(', 0, pin_m.start()))
    print(f"  Pin {pin_num}")

# Current pins in cache: 1, 7, 14, 18, 24
# Correct pins (TRACO datasheet): 2, 3, 9, 11, 14, 16, 22, 23
# Pin mapping (function → old_number → new_number):
#   +VIN   → 1  → 22,23 (two pins)
#   -VIN   → 7  → 2,3   (two pins)
#   +VOUT  → 24 → 14
#   COM    → 18 → 9,16  (two pins)
#   -VOUT  → 14 → 11

# ============================================================
# STEP 1: Build new lib_symbols cache entry
# ============================================================
print("\n--- Building new lib_symbols cache entry ---")

# The new symbol has 8 pins instead of 5
# We need to build a proper KiCad 9 format cache entry
new_cache = '''(symbol "aurora-dsp-icepower-booster:TEL5-2422" (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TEL5-2422" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "TEL5_DUAL_TRP" (at 0 -5.08 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "https://tracopower.com/tel5-datasheet/" (at 0 -7.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "TRACO TEL 5-2422, 5W Isolated DC/DC Converter, 18-36V Input, +/-12V Output, DIP-24" (at 0 -10.16 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "ki_keywords" "TRACO TEL5 isolated DC-DC converter dual output" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "TEL5-2422_0_1"
        (rectangle (start -7.62 8.89) (end 7.62 -11.43) (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "TEL5-2422_1_1"
        (pin power_in line (at -10.16 5.08 0) (length 2.54) (name "+VIN" (effects (font (size 1.27 1.27)))) (number "22" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -10.16 2.54 0) (length 2.54) (name "+VIN" (effects (font (size 1.27 1.27)))) (number "23" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at -10.16 0 0) (length 2.54) (name "-VIN(GND)" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at -10.16 -2.54 0) (length 2.54) (name "-VIN(GND)" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 10.16 5.08 180) (length 2.54) (name "+VOUT" (effects (font (size 1.27 1.27)))) (number "14" (effects (font (size 1.27 1.27)))))
        (pin unspecified line (at 10.16 2.54 180) (length 2.54) (name "COMMON" (effects (font (size 1.27 1.27)))) (number "16" (effects (font (size 1.27 1.27)))))
        (pin unspecified line (at 10.16 -2.54 180) (length 2.54) (name "COMMON" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 10.16 -5.08 180) (length 2.54) (name "-VOUT" (effects (font (size 1.27 1.27)))) (number "11" (effects (font (size 1.27 1.27))))))
      (embedded_fonts no))'''

check_balance(new_cache, "(new cache)")

# ============================================================
# STEP 2: Analyze U1 instance to understand wire connections
# ============================================================
print("\n--- Analyzing U1 instance ---")
print(u1_block)

# ============================================================
# STEP 3: Build new U1 instance
# ============================================================
# We need to preserve: position, UUID, mirror, unit, properties
# But change: pin numbers in the (pin "X" (uuid ...)) entries

# Extract U1 position
pos_match = re.search(r'\(at ([\d.]+) ([\d.]+)', u1_block)
if pos_match:
    u1_x, u1_y = float(pos_match.group(1)), float(pos_match.group(2))
    print(f"\nU1 position: ({u1_x}, {u1_y})")

# Extract mirror
mirror_match = re.search(r'\(mirror ([xy]+)\)', u1_block)
mirror = mirror_match.group(1) if mirror_match else None
print(f"U1 mirror: {mirror}")

# Extract UUID
uuid_match = re.search(r'\(uuid "([^"]+)"\)', u1_block)
u1_uuid = uuid_match.group(1) if uuid_match else None
print(f"U1 UUID: {u1_uuid}")

# Extract all pin entries with their UUIDs
pin_entries = []
for pin_m in re.finditer(r'\(pin "(\d+)" \(uuid "([^"]+)"\)\)', u1_block):
    pin_entries.append((pin_m.group(1), pin_m.group(2)))
    print(f"  Pin {pin_m.group(1)} → UUID {pin_m.group(2)}")

# OLD pin mapping:  1=+VIN, 7=-VIN, 14=-VOUT, 18=COM, 24=+VOUT
# NEW pin mapping: 22=+VIN, 23=+VIN, 2=-VIN(GND), 3=-VIN(GND), 
#                  14=+VOUT, 16=COMMON, 9=COMMON, 11=-VOUT

# Map old pin connections to functions:
old_pin_to_function = {}
for pin_num, pin_uuid in pin_entries:
    if pin_num == "1":
        old_pin_to_function[pin_uuid] = "+VIN"      # Was +VIN on old pin 1
    elif pin_num == "7":
        old_pin_to_function[pin_uuid] = "-VIN"      # Was -VIN on old pin 7
    elif pin_num == "24":
        old_pin_to_function[pin_uuid] = "+VOUT"     # Was +VOUT on old pin 24
    elif pin_num == "18":
        old_pin_to_function[pin_uuid] = "COM"       # Was COM on old pin 18
    elif pin_num == "14":
        old_pin_to_function[pin_uuid] = "-VOUT"     # Was -VOUT on old pin 14

# New pin assignments (use primary pin for each function):
function_to_new_pin = {
    "+VIN": "22",       # +VIN(VCC) - primary pin
    "-VIN": "2",        # -VIN(GND) - primary pin
    "+VOUT": "14",      # +VOUT
    "COM": "16",        # COMMON - primary pin
    "-VOUT": "11",      # -VOUT
}

# Build the new pin section
# The old symbol had 5 pins, the new one has 8
# We keep the 5 existing UUID mappings but change pin numbers
# We need to ADD 3 new pins (23, 3, 9) with new UUIDs
import uuid as uuid_mod

new_pin_entries = []
for old_pin, old_uuid in pin_entries:
    func = old_pin_to_function.get(old_uuid)
    new_pin = function_to_new_pin.get(func, old_pin)
    new_pin_entries.append((new_pin, old_uuid))
    print(f"  Remap: old pin {old_pin} ({func}) → new pin {new_pin}")

# Add the 3 extra pins (23=+VIN, 3=-VIN, 9=COMMON) 
extra_pins = [
    ("23", str(uuid_mod.uuid4())),  # +VIN second pin
    ("3", str(uuid_mod.uuid4())),   # -VIN second pin  
    ("9", str(uuid_mod.uuid4())),   # COMMON second pin
]
for pin, uid in extra_pins:
    new_pin_entries.append((pin, uid))
    print(f"  Add: new pin {pin} → UUID {uid}")

# Build new U1 block
# First, replace pin numbers in existing block
new_u1 = u1_block

# Replace each old pin reference
for old_pin, old_uuid in pin_entries:
    func = old_pin_to_function.get(old_uuid)
    new_pin = function_to_new_pin.get(func, old_pin)
    old_str = f'(pin "{old_pin}" (uuid "{old_uuid}"))'
    new_str = f'(pin "{new_pin}" (uuid "{old_uuid}"))'
    new_u1 = new_u1.replace(old_str, new_str)

# Add the extra pin entries before closing parenthesis
# Find the last (pin entry and add after it
last_pin_idx = new_u1.rfind('(pin "')
last_pin_end = new_u1.find(')', new_u1.find(')', last_pin_idx) + 1) + 1
insert_point = last_pin_end

extra_pin_text = ""
for pin, uid in extra_pins:
    extra_pin_text += f'\n        (pin "{pin}" (uuid "{uid}"))'

new_u1 = new_u1[:insert_point] + extra_pin_text + new_u1[insert_point:]

# Update footprint property
new_u1 = new_u1.replace(
    'Package_DIP:DIP-24_W15.24mm',
    'TEL5_DUAL_TRP'
)

check_balance(new_u1, "(new U1)")

print(f"\n--- New U1 instance ---")
print(new_u1)

# ============================================================
# STEP 4: Apply changes to schematic
# ============================================================
print("\n--- Applying changes ---")

# Replace cache entry
new_sch = sch[:cache_start] + new_cache + sch[cache_end:]

# Recalculate positions since cache replacement may have changed offsets
offset = len(new_cache) - len(cache_block)
print(f"  Cache size delta: {offset} chars")

# Now replace U1 instance  
# Re-find U1 in modified content
u1_match2 = re.search(r'\(symbol \(lib_id "aurora-dsp-icepower-booster:TEL5-2422"\)', new_sch)
if not u1_match2:
    print("ERROR: Could not find U1 after cache replacement!")
    sys.exit(1)

u1_block2, u1_end2 = extract_balanced_block(new_sch, u1_match2.start())
new_sch = new_sch[:u1_match2.start()] + new_u1 + new_sch[u1_end2:]

check_balance(new_sch, "(after schematic edit)")

# ============================================================
# STEP 5: Write updated schematic
# ============================================================
with open(SCH_FILE, 'w') as f:
    f.write(new_sch)
print(f"\n✓ Schematic written: {len(new_sch)} chars")

# ============================================================
# STEP 6: Update custom symbol library
# ============================================================
print("\n--- Updating custom symbol library ---")

new_sym_lib = '''(kicad_symbol_lib
  (version 20241209)
  (generator "kicad-mcp")
  (generator_version "9.0")
  (symbol "TEL5-2422"
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "U"
      (at 2.54 0 0)
      (effects
        (font (size 1.27 1.27))
      )
    )
    (property "Value" "TEL5-2422"
      (at 0 -2.54 0)
      (effects
        (font (size 1.27 1.27))
      )
    )
    (property "Footprint" "TEL5_DUAL_TRP"
      (at 0 -5.08 0)
      (effects
        (font (size 1.27 1.27))
      )
      (hide yes)
    )
    (property "Datasheet" "https://tracopower.com/tel5-datasheet/"
      (at 0 -7.62 0)
      (effects
        (font (size 1.27 1.27))
      )
      (hide yes)
    )
    (property "Description" "TRACO TEL 5-2422, 5W Isolated DC/DC Converter, 18-36V Input, +/-12V Output, DIP-24"
      (at 0 -10.16 0)
      (effects
        (font (size 1.27 1.27))
      )
      (hide yes)
    )
    (property "ki_keywords" "TRACO TEL5 isolated DC-DC converter dual output"
      (at 0 0 0)
      (effects
        (font (size 1.27 1.27))
      )
      (hide yes)
    )
    (symbol "TEL5-2422_0_1"
      (rectangle
        (start -7.62 8.89)
        (end 7.62 -11.43)
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
    )
    (symbol "TEL5-2422_1_1"
      (pin power_in line
        (at -10.16 5.08 0)
        (length 2.54)
        (name "+VIN"
          (effects (font (size 1.27 1.27)))
        )
        (number "22"
          (effects (font (size 1.27 1.27)))
        )
      )
      (pin power_in line
        (at -10.16 2.54 0)
        (length 2.54)
        (name "+VIN"
          (effects (font (size 1.27 1.27)))
        )
        (number "23"
          (effects (font (size 1.27 1.27)))
        )
      )
      (pin power_out line
        (at -10.16 0 0)
        (length 2.54)
        (name "-VIN(GND)"
          (effects (font (size 1.27 1.27)))
        )
        (number "2"
          (effects (font (size 1.27 1.27)))
        )
      )
      (pin power_out line
        (at -10.16 -2.54 0)
        (length 2.54)
        (name "-VIN(GND)"
          (effects (font (size 1.27 1.27)))
        )
        (number "3"
          (effects (font (size 1.27 1.27)))
        )
      )
      (pin power_out line
        (at 10.16 5.08 180)
        (length 2.54)
        (name "+VOUT"
          (effects (font (size 1.27 1.27)))
        )
        (number "14"
          (effects (font (size 1.27 1.27)))
        )
      )
      (pin unspecified line
        (at 10.16 2.54 180)
        (length 2.54)
        (name "COMMON"
          (effects (font (size 1.27 1.27)))
        )
        (number "16"
          (effects (font (size 1.27 1.27)))
        )
      )
      (pin unspecified line
        (at 10.16 -2.54 180)
        (length 2.54)
        (name "COMMON"
          (effects (font (size 1.27 1.27)))
        )
        (number "9"
          (effects (font (size 1.27 1.27)))
        )
      )
      (pin power_out line
        (at 10.16 -5.08 180)
        (length 2.54)
        (name "-VOUT"
          (effects (font (size 1.27 1.27)))
        )
        (number "11"
          (effects (font (size 1.27 1.27)))
        )
      )
    )
  )
)
'''

check_balance(new_sym_lib, "(symbol library)")

with open(SYM_FILE, 'w') as f:
    f.write(new_sym_lib)
print(f"✓ Symbol library written: {len(new_sym_lib)} chars")

# ============================================================
# STEP 7: Copy footprint to project
# ============================================================
fp_src = "/tmp/fp_extract/TEL_5_2422/KiCADv6/footprints.pretty/TEL5_DUAL_TRP.kicad_mod"
fp_dest_dir = os.path.join(PROJECT_DIR, "footprints.pretty")
fp_dest = os.path.join(fp_dest_dir, "TEL5_DUAL_TRP.kicad_mod")

os.makedirs(fp_dest_dir, exist_ok=True)
with open(fp_src, 'r') as f:
    fp_content = f.read()
with open(fp_dest, 'w') as f:
    f.write(fp_content)
print(f"✓ Footprint copied to {fp_dest}")

print("\n" + "=" * 60)
print("F10 COMPLETE — TEL5-2422 symbol + footprint replaced")
print("  Old pins: 1, 7, 14, 18, 24")
print("  New pins: 2, 3, 9, 11, 14, 16, 22, 23")
print("  New footprint: TEL5_DUAL_TRP (8 THT pads)")
print("=" * 60)
print("\nNOTE: Wire connections still reference old positions.")
print("  The symbol shape changed (bigger box), so wires need adjustment.")
print("  This will be handled in a follow-up step after visual inspection.")
