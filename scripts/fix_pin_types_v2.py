#!/usr/bin/env python3
"""
Fix pin types precisely using balanced-paren pin block extraction.

Target changes:
  TEL5-2422:
    Pin 2 (-VIN(GND)): passive → power_out (revert wrong)
    Pin 3 (-VIN(GND)): power_out → passive (correct fix)
    Pin 9 (COMMON): unspecified → power_in
  ADP7118ARDZ:
    Pin 1 (VOUT, first occurrence): passive → power_out (revert wrong)
    Pin 2 (VOUT, first occurrence): power_out → passive (correct fix)
"""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    text = f.read()

def extract_balanced(text, start):
    """Extract balanced parens block."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
    return None, start

def find_all_pins_in_region(region):
    """Find all (pin ...) blocks in a text region, return list of (block, start_idx, num, type)."""
    results = []
    pos = 0
    while True:
        idx = region.find('(pin ', pos)
        if idx == -1:
            break
        block, end_pos = extract_balanced(region, idx)
        if block:
            num_m = re.search(r'\(number\s+"([^"]+)"', block)
            type_m = re.match(r'\(pin\s+(\w+)', block)
            name_m = re.search(r'\(name\s+"([^"]*)"', block)
            if num_m and type_m:
                results.append({
                    'block': block,
                    'idx': idx,
                    'len': len(block),
                    'num': num_m.group(1),
                    'type': type_m.group(1),
                    'name': name_m.group(1) if name_m else '?'
                })
        pos = idx + 1
    return results

changes_made = []

# ===== TEL5-2422 =====
print("=== TEL5-2422 ===")
cache_start = text.find('(lib_symbols')
tel_name_idx = text.find('"TEL5-2422"', cache_start)
if tel_name_idx >= 0:
    # Find the (symbol "TEL5-2422" ...) block start
    sym_start = text.rfind('(symbol ', max(0, tel_name_idx - 100), tel_name_idx)
    tel_block, tel_block_end = extract_balanced(text, sym_start)
    
    print(f"  Block found: {len(tel_block)} chars at pos {sym_start}")
    
    pins = find_all_pins_in_region(tel_block)
    print(f"  Found {len(pins)} pins:")
    for p in pins:
        print(f"    Pin {p['num']:>2} ({p['name']:>12}): {p['type']}")
    
    # Apply changes in REVERSE order to preserve indices
    pin_changes = [
        ('2', 'passive', 'power_out'),   # Revert wrong change
        ('3', 'power_out', 'passive'),   # Apply correct change
        ('9', 'unspecified', 'power_in'), # Apply correct change
    ]
    
    # Find which pins to change
    ops = []
    for target_num, old_type, new_type in pin_changes:
        for p in pins:
            if p['num'] == target_num and p['type'] == old_type:
                new_block = re.sub(r'\(pin\s+' + old_type, f'(pin {new_type}', p['block'], count=1)
                ops.append((p['idx'], p['len'], new_block, f"Pin {target_num}: {old_type} → {new_type}"))
                break
    
    # Sort by index descending to apply from end
    ops.sort(key=lambda x: x[0], reverse=True)
    
    for idx, length, new_block, desc in ops:
        tel_block = tel_block[:idx] + new_block + tel_block[idx+length:]
        changes_made.append(f"TEL5-2422 {desc}")
        print(f"  ✅ {desc}")
    
    # Replace in full text
    text = text[:sym_start] + tel_block + text[tel_block_end:]

# ===== ADP7118ARDZ =====
print("\n=== ADP7118ARDZ ===")
cache_start = text.find('(lib_symbols')
adp_name_idx = text.find('"ADP7118ARDZ"', cache_start)
if adp_name_idx >= 0:
    sym_start = text.rfind('(symbol ', max(0, adp_name_idx - 100), adp_name_idx)
    adp_block, adp_block_end = extract_balanced(text, sym_start)
    
    print(f"  Block found: {len(adp_block)} chars at pos {sym_start}")
    
    pins = find_all_pins_in_region(adp_block)
    print(f"  Found {len(pins)} pins:")
    for p in pins:
        print(f"    Pin {p['num']:>2} ({p['name']:>12}): {p['type']}")
    
    # For ADP7118ARDZ, there are multiple sub-symbols with duplicate pin numbers.
    # The FIRST Pin 1 (VOUT, passive) needs → power_out
    # The FIRST Pin 2 (VOUT, power_out) needs → passive
    
    pin1_vout = None
    pin2_vout = None
    for p in pins:
        if p['num'] == '1' and p['name'] == 'VOUT' and p['type'] == 'passive' and pin1_vout is None:
            pin1_vout = p
        elif p['num'] == '2' and p['name'] == 'VOUT' and p['type'] == 'power_out' and pin2_vout is None:
            pin2_vout = p
    
    ops = []
    if pin1_vout:
        new_block = re.sub(r'\(pin\s+passive', '(pin power_out', pin1_vout['block'], count=1)
        ops.append((pin1_vout['idx'], pin1_vout['len'], new_block, "Pin 1 (VOUT): passive → power_out"))
    if pin2_vout:
        new_block = re.sub(r'\(pin\s+power_out', '(pin passive', pin2_vout['block'], count=1)
        ops.append((pin2_vout['idx'], pin2_vout['len'], new_block, "Pin 2 (VOUT): power_out → passive"))
    
    ops.sort(key=lambda x: x[0], reverse=True)
    
    for idx, length, new_block, desc in ops:
        adp_block = adp_block[:idx] + new_block + adp_block[idx+length:]
        changes_made.append(f"ADP7118ARDZ {desc}")
        print(f"  ✅ {desc}")
    
    text = text[:sym_start] + adp_block + text[adp_block_end:]

# ===== VALIDATION =====
print("\n=== BRACKET BALANCE ===")
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"  Depth: {depth} ✅")

with open(SCH, "w") as f:
    f.write(text)

print(f"\n{len(changes_made)} changes:")
for c in changes_made:
    print(f"  {c}")
