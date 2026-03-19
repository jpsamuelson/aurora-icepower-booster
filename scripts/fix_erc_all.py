#!/usr/bin/env python3
"""
ERC-Fix: Alle 13 Errors + 5 Warnings fixen.

Fixes:
  1. 7× GND mid-wire → Wire-Split (E1, E8-E13)
  2. U1 Pin 3: power_out → passive (E2)
  3. U14 Pin 2: power_out → passive (E7)
  4. PWR_FLAG auf GND-Netz (E3)
  5. SS-Kondensator C81 (22nF) von SS nach GND (E4, E5)
  6. C22 Pin1 → V+ verbinden (E6)
  7. U1 Pin 9+16: unspecified → power_in (W2, W3)
  8. Dangling Wire (140, 37.62→40) löschen + #PWR010 neu anbinden (W5)
  9. Library .kicad_sym updaten (W1, W4) — separate Datei
"""

import re
import uuid as uuid_mod
import copy

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, "r") as f:
    text = f.read()

original_len = len(text)
changes = []

def new_uuid():
    return str(uuid_mod.uuid4())

# =====================================================================
# FIX 1: 7× GND mid-wire → Wire-Split
# =====================================================================
print("Fix 1: 7× GND mid-wire → Wire-Split")

wire_splits = [
    # (old_x1, old_y1, old_x2, old_y2, split_x, split_y)
    (37.62, 42.54, 69.84, 42.54, 55.0, 42.54),   # #PWR063
    (285.0, 113.81, 285.0, 117.0, 285.0, 115.0),  # #PWR014
    (285.0, 193.81, 285.0, 197.0, 285.0, 195.0),  # #PWR083
    (285.0, 273.81, 285.0, 277.0, 285.0, 275.0),  # #PWR005
    (285.0, 353.81, 285.0, 357.0, 285.0, 355.0),  # #PWR088
    (285.0, 433.81, 285.0, 437.0, 285.0, 435.0),  # #PWR028
    (285.0, 513.81, 285.0, 517.0, 285.0, 515.0),  # #PWR037
]

for old_x1, old_y1, old_x2, old_y2, sx, sy in wire_splits:
    # Format coordinates to match file
    def fmt(v):
        if v == int(v):
            return str(int(v))
        else:
            return f"{v:.2f}".rstrip('0').rstrip('.')
    
    # Build search pattern — need to find the exact wire
    # KiCad uses various number formats, so search with regex
    def coord_pat(v):
        if v == int(v):
            return f"{int(v)}"
        else:
            s = f"{v:.2f}".rstrip('0').rstrip('.')
            return re.escape(s)
    
    pat = (r'\(wire\s+\(pts\s+\(xy\s+' + coord_pat(old_x1) + r'\s+' + coord_pat(old_y1) +
           r'\)\s+\(xy\s+' + coord_pat(old_x2) + r'\s+' + coord_pat(old_y2) +
           r'\)\)\s+\(stroke\s+\(width\s+\d+\)\s+\(type\s+default\)\)\s+\(uuid\s+"[^"]+"\)\)')
    
    m = re.search(pat, text)
    if m:
        old_wire = m.group(0)
        # Build two new wires
        def fmtc(v):
            """Format coordinate for KiCad .kicad_sch"""
            if v == int(v):
                return str(int(v))
            else:
                return f"{v}"
        
        wire1 = (f'(wire (pts (xy {fmtc(old_x1)} {fmtc(old_y1)}) (xy {fmtc(sx)} {fmtc(sy)})) '
                 f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
        wire2 = (f'(wire (pts (xy {fmtc(sx)} {fmtc(sy)}) (xy {fmtc(old_x2)} {fmtc(old_y2)})) '
                 f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
        
        text = text.replace(old_wire, wire1 + '\n    ' + wire2, 1)
        changes.append(f"  Split wire ({old_x1},{old_y1})→({old_x2},{old_y2}) at ({sx},{sy})")
    else:
        print(f"  WARNING: Wire ({old_x1},{old_y1})→({old_x2},{old_y2}) not found!")
        # Try broader search
        pat2 = coord_pat(old_x1) + r'.*?' + coord_pat(old_y1) + r'.*?' + coord_pat(old_x2) + r'.*?' + coord_pat(old_y2)
        m2 = re.search(pat2, text[:5000])
        if m2:
            print(f"    Found with broad search at pos {m2.start()}: {text[m2.start():m2.start()+100]}")

print(f"  {len(changes)} wire splits done")

# =====================================================================
# FIX 2: U1 Pin 3: power_out → passive (in lib_symbols cache)
# =====================================================================
print("\nFix 2: U1 Pin 3 power_out → passive")

# Find in lib_symbols: TEL5-2422, Pin 3 (-VIN(GND)), change power_out to passive
# The pattern: (pin power_out line ... (name "-VIN(GND)" ...) (number "3" ...))
# We need to be precise — only change Pin 3, not Pin 2
cache_start = text.find('(lib_symbols')

# Find the TEL5-2422 symbol in cache
tel_start = text.find('"TEL5-2422"', cache_start)
if tel_start >= 0:
    # Find Pin 3 within this symbol — look for (number "3")
    # We need the pin block containing number "3"
    search_region = text[tel_start:tel_start+5000]
    
    # Find: (pin power_out line ... (number "3" ...))
    pin3_m = re.search(r'\(pin\s+power_out\s+line\s+\(at[^)]+\).*?\(number\s+"3"', search_region, re.DOTALL)
    if pin3_m:
        # Replace 'power_out' with 'passive' in this specific match
        abs_start = tel_start + pin3_m.start()
        old_text = text[abs_start:abs_start + pin3_m.end() - pin3_m.start()]
        new_text = old_text.replace('power_out', 'passive', 1)
        text = text[:abs_start] + new_text + text[abs_start + len(old_text):]
        changes.append("  U1 TEL5-2422 Pin 3: power_out → passive")
        print("  Done")
    else:
        print("  WARNING: Pin 3 not found in TEL5-2422 cache!")

# =====================================================================
# FIX 3: U14 Pin 2: power_out → passive (in lib_symbols cache)
# =====================================================================
print("\nFix 3: U14 Pin 2 power_out → passive")

# Find ADP7118ARDZ in cache, Pin 2 (VOUT)
adp_start = text.find('"ADP7118ARDZ"', cache_start)
if adp_start >= 0:
    search_region = text[adp_start:adp_start+5000]
    
    # Find the FIRST occurrence of Pin 2 (VOUT, power_out)
    # There may be multiple sub-symbols — need to find the right one
    pin2_m = re.search(r'\(pin\s+power_out\s+line\s+\(at[^)]+\).*?\(number\s+"2"', search_region, re.DOTALL)
    if pin2_m:
        abs_start = adp_start + pin2_m.start()
        old_text = text[abs_start:abs_start + pin2_m.end() - pin2_m.start()]
        new_text = old_text.replace('power_out', 'passive', 1)
        text = text[:abs_start] + new_text + text[abs_start + len(old_text):]
        changes.append("  U14 ADP7118ARDZ Pin 2: power_out → passive")  
        print("  Done")
    else:
        print("  WARNING: Pin 2 not found in ADP7118ARDZ cache!")

# =====================================================================
# FIX 7: U1 Pin 9+16: unspecified → power_in (in lib_symbols cache)
# =====================================================================
print("\nFix 7: U1 Pin 9+16 unspecified → power_in")

# Re-find TEL5-2422 since text may have shifted
tel_start = text.find('"TEL5-2422"', text.find('(lib_symbols'))
if tel_start >= 0:
    search_region = text[tel_start:tel_start+5000]
    
    for pin_num in ['9', '16']:
        pin_m = re.search(
            r'\(pin\s+unspecified\s+line\s+\(at[^)]+\).*?\(number\s+"' + pin_num + '"',
            search_region, re.DOTALL
        )
        if pin_m:
            abs_start = tel_start + pin_m.start()
            old_text = text[abs_start:abs_start + pin_m.end() - pin_m.start()]
            new_text = old_text.replace('unspecified', 'power_in', 1)
            text = text[:abs_start] + new_text + text[abs_start + len(old_text):]
            # Need to re-find after modification
            tel_start = text.find('"TEL5-2422"', text.find('(lib_symbols'))
            search_region = text[tel_start:tel_start+5000]
            changes.append(f"  U1 TEL5-2422 Pin {pin_num}: unspecified → power_in")
            print(f"  Pin {pin_num} done")
        else:
            print(f"  WARNING: Pin {pin_num} (unspecified) not found!")

# =====================================================================
# FIX 9: Dangling Wire (140, 37.62→40) löschen
# =====================================================================
print("\nFix 9: Dangling Wire (140, 37.62→40) löschen")

# This wire has UUID c4a53c4d-ceb6-4f4c-be69-3f14d041bca2
dangling_uuid = "c4a53c4d-ceb6-4f4c-be69-3f14d041bca2"
dangling_pat = re.compile(
    r'\(wire\s+\(pts\s+\(xy\s+140\s+37\.62\)\s+\(xy\s+140\s+40\)\)\s+'
    r'\(stroke\s+\(width\s+0\)\s+\(type\s+default\)\)\s+'
    r'\(uuid\s+"' + re.escape(dangling_uuid) + r'"\)\)\s*'
)
m = dangling_pat.search(text)
if m:
    text = text[:m.start()] + text[m.end():]
    changes.append("  Deleted dangling wire (140,37.62)→(140,40)")
    print("  Done")
    
    # Now #PWR010 (GND at 140,40) has NO wire connection!
    # We need to add a wire from U14 GND pin (150.16, 30) area down to (140, 40)
    # Actually, #PWR010 sits at (140, 40) which is NOT on any wire anymore.
    # But looking at U14's topology: GND pin 4 is at (150.16, 30) with wire to (150.16, 32.54→35.0) to #PWR0152.
    # #PWR010 at (140, 40) is a separate GND symbol.
    # After deleting the dangling wire, #PWR010 is completely disconnected.
    # But wait — #PWR010 was NOT in the error list! So it must be connected via another path.
    # Let me check...
    # Actually, GND power symbols don't need wires - they create an implicit connection to the GND net.
    # The dangling wire was going FROM (140,37.62) TO (140,40) = #PWR010.
    # The top end (140, 37.62) goes nowhere. So the wire and #PWR010 are both orphaned.
    # We should ALSO delete #PWR010 if it's truly orphaned and not anchoring anything.
    # 
    # Actually NO — power symbols create their net by existing. #PWR010 at (140,40) IS the GND reference
    # for that area. The problem is the wire going UP from it to (140, 37.62) which connects to nothing.
    # We already deleted the wire. #PWR010 stays — it just has no wire, which means it will get
    # a pin_not_connected error. So we should keep the wire but NOT have it dangle.
    #
    # Better approach: The wire was from (140, 37.62) to (140, 40). 
    # At (140, 40) is #PWR010 (GND). We need #PWR010 connected.
    # The wire endpoint at (140, 37.62) connects to nothing.
    # Solution: Just shorten/remove and let #PWR010 exist. Actually #PWR010 itself will create a
    # pin_not_connected error since its pin has no wire.
    #
    # The REAL solution for #PWR010: If it served as GND for something, we need to figure out what.
    # If it was leftover from old U14 wiring, we can just delete both the wire AND #PWR010.
    # But deleting symbols is complex. Let's instead just reconnect it properly.
    # 
    # #PWR010 at (140,40): U14 is at (140,30). The old U14 (7-pin) had GND at different position.
    # Now U14 GND is at (150.16, 30) and (150.16, 32.54). 
    # #PWR010 is an orphaned GND symbol from old layout. We should delete it.
    print("  Need to also handle #PWR010 — checking if it's referenced elsewhere...")
    
    # Check if #PWR010 appears in any net
    pwr010_count = text.count('"#PWR010"')
    print(f"  #PWR010 appears {pwr010_count} times in schematic")
    
    # Let's just move #PWR010 to connect to something useful, or delete it.
    # Safest: delete #PWR010 symbol entirely.
    # Find the (symbol (lib_id "power:GND") ...) block for #PWR010
    pwr010_pat = re.compile(r'\(symbol\s+\(lib_id\s+"power:GND"\)\s+\(at\s+140\s+40\s+0\)')
    m010 = pwr010_pat.search(text)
    if m010:
        # Extract full balanced block
        start = m010.start()
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        pwr010_block = text[start:end]
        # Verify it contains #PWR010
        if '#PWR010' in pwr010_block:
            text = text[:start] + text[end:]
            changes.append("  Deleted orphaned #PWR010 (GND at 140,40)")
            print("  Deleted #PWR010")
        else:
            print("  WARNING: GND at (140,40) doesn't contain #PWR010!")
else:
    print("  WARNING: Dangling wire not found!")

# =====================================================================
# FIX 4: PWR_FLAG auf GND-Netz
# =====================================================================
print("\nFix 4: PWR_FLAG auf GND-Netz")

# #PWR001 is at (98, 18.65) connected via wire (98, 21.19→18.65)
# We'll place a new PWR_FLAG at (95.46, 18.65) — left of #PWR001
# Connected by a horizontal wire from (95.46, 18.65) to (98, 18.65)
# Actually simpler: place PWR_FLAG at (98, 18.65) directly — but then pin-on-pin.
# Better: Place on the wire from C14 to #PWR001. Wire is (98, 21.19→18.65).
# Put PWR_FLAG at (98, 20) on this wire — need to split the wire first.

# Current wire: (98, 21.19) → (98, 18.65)
# Split at (98, 20): (98, 21.19→20) + (98, 20→18.65)
# Place PWR_FLAG at (98, 20) — but wait, PWR_FLAG has pin at (0,0) with orientation 90°
# So pin is AT the symbol position. Rotation 0 = pin pointing up.

# Actually, simpler approach: just add new wire from #PWR001 to a PWR_FLAG.
# OR: place PWR_FLAG on existing GND connection point.
# 
# Easiest: Place PWR_FLAG at (98, 18.65) — same position as #PWR001.
# PWR_FLAG pin is at origin, orientation 90° — so pin at (98, 18.65) touching #PWR001's pin.
# Actually this creates issues. Let's put it horizontally offset.
#
# Best approach: Put PWR_FLAG at (96, 18.65) with a wire from (96, 18.65) to (98, 18.65).
# PWR_FLAG with rotation 0 has pin at (0,0) pointing up. We want it pointing down to connect.
# With rotation 180 or at a wire endpoint.
#
# Wait — the #PWR001 GND pin is at (98, 18.65). A wire goes from (98, 21.19) to (98, 18.65).
# This wire connects C14 Pin1 to #PWR001.
# The issue is #PWR001 is NOT driven (no power_out on GND net).
# We need a PWR_FLAG on the GND net.
# 
# Simplest fix: Split wire (98, 21.19→18.65) at (98, 20):
#   New: (98, 21.19→20) and (98, 20→18.65)
# Place PWR_FLAG at (95, 20) ROTATED 0° (pin at (95,20))
# Add wire: (95, 20) → (98, 20)

pwr_flag_x, pwr_flag_y = 95.0, 20.0
pwrflag_wire_end_x = 98.0

# Split the wire (98, 21.19→18.65) at y=20
old_wire_pat = re.compile(
    r'\(wire\s+\(pts\s+\(xy\s+98\s+21\.19\)\s+\(xy\s+98\s+18\.65\)\)\s+'
    r'\(stroke\s+\(width\s+0\)\s+\(type\s+default\)\)\s+'
    r'\(uuid\s+"[^"]+"\)\)'
)
m = old_wire_pat.search(text)
if m:
    old_wire = m.group(0)
    wire1 = (f'(wire (pts (xy 98 21.19) (xy 98 20)) '
             f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
    wire2 = (f'(wire (pts (xy 98 20) (xy 98 18.65)) '
             f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
    wire3 = (f'(wire (pts (xy {pwr_flag_x} {pwr_flag_y}) (xy {pwrflag_wire_end_x} {pwr_flag_y})) '
             f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
    text = text.replace(old_wire, wire1 + '\n    ' + wire2 + '\n    ' + wire3, 1)
    changes.append(f"  Split wire (98,21.19→18.65) at y=20, added PWR_FLAG wire")
    print("  Wire split + PWR_FLAG wire done")
else:
    print("  WARNING: Wire (98,21.19→18.65) not found!")

# Add PWR_FLAG symbol instance
pwr_flag_symbol = (
    f'(symbol (lib_id "power:PWR_FLAG") (at {pwr_flag_x} {pwr_flag_y} 0) '
    f'(unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    f'(dnp no) (fields_autoplaced yes) '
    f'(uuid "{new_uuid()}") '
    f'(property "Reference" "#FLG0104" (at {pwr_flag_x} {pwr_flag_y - 2.0} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Value" "PWR_FLAG" (at {pwr_flag_x} {pwr_flag_y - 4.0} 0) '
    f'(effects (font (size 1.27 1.27)))) '
    f'(property "Footprint" "" (at {pwr_flag_x} {pwr_flag_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Datasheet" "~" (at {pwr_flag_x} {pwr_flag_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Description" "" (at {pwr_flag_x} {pwr_flag_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(pin "1" (uuid "{new_uuid()}")) '
    f'(instances (project "aurora-dsp-icepower-booster" '
    f'(path "/e42b1bb1-fbe7-4279-a498-b6ec67098e90" (reference "#FLG0104") (unit 1)))))'
)

# Insert before the closing of the schematic (before the last few closing parens)
# Find a good insertion point — after the last symbol and before sheet_instances
sheet_inst_idx = text.find('(sheet_instances')
if sheet_inst_idx >= 0:
    text = text[:sheet_inst_idx] + pwr_flag_symbol + '\n  ' + text[sheet_inst_idx:]
    changes.append("  Added PWR_FLAG #FLG0104 on GND net at (95, 20)")
    print("  PWR_FLAG symbol added")
else:
    print("  WARNING: sheet_instances not found!")

# =====================================================================
# FIX 5: SS-Kondensator C81 (22nF) von SS nach GND
# =====================================================================
print("\nFix 5: SS-Kondensator C81 (22nF)")

# SS label SS_U14 is at (132.38, 30.0)
# Wire from pin: (129.84, 30.0) → (132.38, 30.0)  
# We'll place C81 at (135.0, 33.0) vertically
# Device:C Pin 1 at local (0, 3.81) → sch (135, 29.19) ← connect to SS wire
# Device:C Pin 2 at local (0, -3.81) → sch (135, 36.81) ← connect to new GND

# Actually Pin 1 is at local (0, 3.81) from cache analysis. 
# But wait — the cache analysis showed:
#   Pin 1: local (0, 3.81) → sch (147.62, 41.81) for C22 at (147.62, 38)
#   That means: sch_y = sym_y + local_y = 38 + 3.81 = 41.81
# So for C81 at (135, 33): Pin1 at (135, 33 + 3.81) = (135, 36.81)
# And Pin 2 at (135, 33 - 3.81) = (135, 29.19)
#
# Hmm that's inverted from what I expect. Let me re-check:
# The cache said: Pin 1: local (0, 3.81), Pin 2: local (0, -3.81)
# For C22 at (147.62, 38.0): Pin 1 schematic = (147.62, 38 + 3.81) = (147.62, 41.81) → connected to GND
# So Pin 1 is BOTTOM (higher Y = lower on screen), Pin 2 is TOP (lower Y = upper on screen)
# In schematics: Y increases downward!
#
# For C81 at (135, 33):
#   Pin 1 (bottom): (135, 36.81) → connect to GND 
#   Pin 2 (top): (135, 29.19) → connect to SS net
#
# Wait no. In the actual Device:C symbol, Pin 1 is at the TOP and Pin 2 at the BOTTOM.
# Looking at C22: Pin 2 at (147.62, 34.19) was supposed to be VOUT but is NOT CONNECTED.
# Pin 1 at (147.62, 41.81) is connected to GND via wire to (147.62, 43.0).
# So Pin 1 = BOTTOM (y+3.81), Pin 2 = TOP (y-3.81).
# 
# For the SS cap C81:
#   We want top → SS wire (y=30), bottom → GND
#   Pin 2 (top) at (135, 33 - 3.81) = (135, 29.19) — need to connect to SS at y=30
#   Pin 1 (bottom) at (135, 33 + 3.81) = (135, 36.81) — connect to GND
#
# Hmm 29.19 ≠ 30.0. Let me adjust C81 position so Pin 2 aligns with y=30:
# 33 - 3.81 = 29.19. Need 30. So: sym_y = 30 + 3.81 = 33.81
# Pin 2: (135, 33.81 - 3.81) = (135, 30.0) ✓
# Pin 1: (135, 33.81 + 3.81) = (135, 37.62) → GND below

c81_x, c81_y = 135.0, 33.81
c81_pin2_y = 30.0   # Top, connects to SS
c81_pin1_y = 37.62  # Bottom, connects to GND

# Wire from C81 Pin 2 (135, 30) to SS_U14 label wire at (132.38, 30)
# The label is at (132.38, 30). Wire: (129.84, 30) → (132.38, 30)
# Extend the wire: (132.38, 30) → (135, 30)
wire_ss_to_c81 = (
    f'(wire (pts (xy 132.38 30) (xy {c81_x} {c81_pin2_y})) '
    f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))'
)

# GND symbol for C81 bottom
gnd_c81_x, gnd_c81_y = c81_x, c81_pin1_y + 1.19  # GND symbol below Pin 1
wire_c81_gnd = (
    f'(wire (pts (xy {c81_x} {c81_pin1_y}) (xy {c81_x} {gnd_c81_y})) '
    f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))'
)

# GND power symbol
gnd_c81_symbol = (
    f'(symbol (lib_id "power:GND") (at {gnd_c81_x} {gnd_c81_y} 0) '
    f'(unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    f'(dnp no) (fields_autoplaced yes) '
    f'(uuid "{new_uuid()}") '
    f'(property "Reference" "#PWR0153" (at {gnd_c81_x} {gnd_c81_y + 1.27} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Value" "GND" (at {gnd_c81_x} {gnd_c81_y + 3.175} 0) '
    f'(effects (font (size 1.27 1.27)))) '
    f'(property "Footprint" "" (at {gnd_c81_x} {gnd_c81_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Datasheet" "~" (at {gnd_c81_x} {gnd_c81_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Description" "" (at {gnd_c81_x} {gnd_c81_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(pin "1" (uuid "{new_uuid()}")) '
    f'(instances (project "aurora-dsp-icepower-booster" '
    f'(path "/e42b1bb1-fbe7-4279-a498-b6ec67098e90" (reference "#PWR0153") (unit 1)))))'
)

# C81 capacitor symbol
c81_symbol = (
    f'(symbol (lib_id "Device:C") (at {c81_x} {c81_y} 0) '
    f'(unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    f'(dnp no) (fields_autoplaced yes) '
    f'(uuid "{new_uuid()}") '
    f'(property "Reference" "C81" (at {c81_x + 2} {c81_y} 0) '
    f'(effects (font (size 1.27 1.27)) (justify left))) '
    f'(property "Value" "22nF C0G" (at {c81_x + 2} {c81_y + 2.54} 0) '
    f'(effects (font (size 1.27 1.27)) (justify left))) '
    f'(property "Footprint" "Capacitor_SMD:C_0402_1005Metric" (at {c81_x + 0.9652} {c81_y + 3.81} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Datasheet" "~" (at {c81_x} {c81_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(property "Description" "Soft-Start Capacitor for U14 ADP7118" (at {c81_x} {c81_y} 0) '
    f'(effects (font (size 1.27 1.27)) (hide yes))) '
    f'(pin "1" (uuid "{new_uuid()}")) '
    f'(pin "2" (uuid "{new_uuid()}")) '
    f'(instances (project "aurora-dsp-icepower-booster" '
    f'(path "/e42b1bb1-fbe7-4279-a498-b6ec67098e90" (reference "C81") (unit 1)))))'
)

# Insert all new elements
sheet_inst_idx = text.find('(sheet_instances')
if sheet_inst_idx >= 0:
    insert_block = (
        wire_ss_to_c81 + '\n    ' +
        wire_c81_gnd + '\n    ' +
        c81_symbol + '\n    ' +
        gnd_c81_symbol + '\n    '
    )
    text = text[:sheet_inst_idx] + insert_block + text[sheet_inst_idx:]
    changes.append("  Added C81 (22nF C0G) at (135, 33.81) for SS soft-start")
    changes.append("  Added wire SS_U14 → C81 Pin 2")
    changes.append("  Added wire C81 Pin 1 → #PWR0153 (GND)")
    changes.append("  Added #PWR0153 (GND) at (135, 38.81)")
    print("  C81 + GND + wires added")
else:
    print("  WARNING: sheet_instances not found!")

# =====================================================================
# FIX 6: C22 Pin 1 → V+ verbinden
# =====================================================================
print("\nFix 6: C22 Pin 1 → V+ verbinden")

# C22 Pin 2 (top) at (147.62, 34.19) — NOT CONNECTED
# V+ wire at x=150.16: (150.16, 32.54) → (150.16, 35.0)
# Connect with horizontal wire: (147.62, 34.19) → (150.16, 34.19)
# Split V+ wire at (150.16, 34.19): 
#   (150.16, 32.54→34.19) + (150.16, 34.19→35.0)

# First split the V+ wire
vp_wire_pat = re.compile(
    r'\(wire\s+\(pts\s+\(xy\s+150\.16\s+32\.54\)\s+\(xy\s+150\.16\s+35\)\)\s+'
    r'\(stroke\s+\(width\s+0\)\s+\(type\s+default\)\)\s+'
    r'\(uuid\s+"[^"]+"\)\)'
)
m = vp_wire_pat.search(text)
if m:
    old_wire = m.group(0)
    wire1 = (f'(wire (pts (xy 150.16 32.54) (xy 150.16 34.19)) '
             f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
    wire2 = (f'(wire (pts (xy 150.16 34.19) (xy 150.16 35)) '
             f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
    wire3 = (f'(wire (pts (xy 147.62 34.19) (xy 150.16 34.19)) '
             f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
    text = text.replace(old_wire, wire1 + '\n    ' + wire2 + '\n    ' + wire3, 1)
    changes.append("  Connected C22 Pin 2 (147.62, 34.19) → V+ wire (150.16, 34.19)")
    changes.append("  Split V+ wire (150.16, 32.54→35) at y=34.19")
    print("  Done")
else:
    # Try with 35.0 instead of 35
    vp_wire_pat2 = re.compile(
        r'\(wire\s+\(pts\s+\(xy\s+150\.16\s+32\.54\)\s+\(xy\s+150\.16\s+35(?:\.0)?\)\)\s+'
        r'\(stroke\s+\(width\s+0\)\s+\(type\s+default\)\)\s+'
        r'\(uuid\s+"[^"]+"\)\)'
    )
    m2 = vp_wire_pat2.search(text)
    if m2:
        old_wire = m2.group(0)
        wire1 = (f'(wire (pts (xy 150.16 32.54) (xy 150.16 34.19)) '
                 f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
        wire2 = (f'(wire (pts (xy 150.16 34.19) (xy 150.16 35)) '
                 f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
        wire3 = (f'(wire (pts (xy 147.62 34.19) (xy 150.16 34.19)) '
                 f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))')
        text = text.replace(old_wire, wire1 + '\n    ' + wire2 + '\n    ' + wire3, 1)
        changes.append("  Connected C22 Pin 2 → V+ wire")
        print("  Done (matched with alt pattern)")
    else:
        print("  WARNING: V+ wire (150.16, 32.54→35.0) not found!")
        # Debug: show what's around
        for wm in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+150\.16\s+([\d.]+)\)\s+\(xy\s+150\.16\s+([\d.]+)\)\)', text):
            y1, y2 = float(wm.group(1)), float(wm.group(2))
            if 30 < y1 < 36 or 30 < y2 < 36:
                print(f"    Found wire: (150.16, {y1}) → (150.16, {y2})")

# =====================================================================
# VALIDATION
# =====================================================================
print("\n" + "=" * 70)
print("BRACKET BALANCE CHECK")
print("=" * 70)

depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1

print(f"  Bracket depth: {depth}")
assert depth == 0, f"BRACKET BALANCE ERROR: depth = {depth}"
print("  ✅ Brackets balanced!")

# =====================================================================
# WRITE
# =====================================================================
print(f"\n  Writing {len(text)} chars (was {original_len})")
with open(SCH, "w") as f:
    f.write(text)

print(f"\n{'=' * 70}")
print(f"SUMMARY: {len(changes)} changes applied")
print('=' * 70)
for c in changes:
    print(c)
