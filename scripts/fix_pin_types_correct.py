#!/usr/bin/env python3
"""
Fix the pin type changes that landed on wrong pins due to cross-matching regex.

Current state (wrong):
  U1 Pin 2: passive  ← should be power_out
  U1 Pin 3: power_out ← should be passive  
  U1 Pin 9: unspecified ← should be power_in
  U14 Pin 1 (first unit): passive ← should be power_out
  U14 Pin 2 (first unit): power_out ← should be passive

Fix: Use balanced-paren pin block extraction to change exactly the right pin.
"""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    text = f.read()

def extract_balanced_block(text, start):
    """Extract balanced parentheses block starting at index 'start'."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
    return None, start

def find_pin_block_by_number(region, pin_number):
    """Find a (pin ...) block that contains (number "pin_number")."""
    pos = 0
    while True:
        idx = region.find('(pin ', pos)
        if idx == -1:
            break
        block, end = extract_balanced_block(region, idx)
        if block and f'(number "{pin_number}"' in block:
            return block, idx
        pos = idx + 1
    return None, -1

def change_pin_type_in_block(block, old_type, new_type):
    """Change pin type in a pin block."""
    return block.replace(f'(pin {old_type} ', f'(pin {new_type} ', 1)

changes = []
cache_start = text.find('(lib_symbols')

# ===== TEL5-2422 =====
tel_start = text.find('"TEL5-2422"', cache_start)
if tel_start >= 0:
    # Find the full TEL5-2422 cache block
    tel_block, tel_end = extract_balanced_block(text, text.rfind('(symbol', max(0, tel_start-50), tel_start))
    
    if tel_block:
        # Fix Pin 2: passive → power_out (revert wrong change)
        pin2_block, pin2_idx = find_pin_block_by_number(tel_block, '2')
        if pin2_block:
            if '(pin passive' in pin2_block:
                new_pin2 = change_pin_type_in_block(pin2_block, 'passive', 'power_out')
                tel_block = tel_block[:pin2_idx] + new_pin2 + tel_block[pin2_idx+len(pin2_block):]
                changes.append("U1 Pin 2: passive → power_out (revert)")
                print("  Pin 2: reverted to power_out ✅")
            else:
                print(f"  Pin 2: already correct type")
        
        # Fix Pin 3: power_out → passive (the correct change)
        pin3_block, pin3_idx = find_pin_block_by_number(tel_block, '3')
        if pin3_block:
            if '(pin power_out' in pin3_block:
                new_pin3 = change_pin_type_in_block(pin3_block, 'power_out', 'passive')
                tel_block = tel_block[:pin3_idx] + new_pin3 + tel_block[pin3_idx+len(pin3_block):]
                changes.append("U1 Pin 3: power_out → passive")
                print("  Pin 3: changed to passive ✅")
        
        # Fix Pin 9: unspecified → power_in
        pin9_block, pin9_idx = find_pin_block_by_number(tel_block, '9')
        if pin9_block:
            if '(pin unspecified' in pin9_block:
                new_pin9 = change_pin_type_in_block(pin9_block, 'unspecified', 'power_in')
                tel_block = tel_block[:pin9_idx] + new_pin9 + tel_block[pin9_idx+len(pin9_block):]
                changes.append("U1 Pin 9: unspecified → power_in")
                print("  Pin 9: changed to power_in ✅")
            elif '(pin power_in' in pin9_block:
                print("  Pin 9: already power_in ✅")
        
        # Verify Pin 16 is power_in
        pin16_block, _ = find_pin_block_by_number(tel_block, '16')
        if pin16_block and '(pin power_in' in pin16_block:
            print("  Pin 16: already power_in ✅")
        
        # Replace the entire TEL5-2422 block in text
        old_start = text.rfind('(symbol', max(0, tel_start-50), tel_start)
        old_end = tel_end  # Wrong — need to recalculate from text
        _, old_end2 = extract_balanced_block(text, old_start)
        text = text[:old_start] + tel_block + text[old_end2:]

# ===== ADP7118ARDZ =====
cache_start = text.find('(lib_symbols')
adp_start = text.find('"ADP7118ARDZ"', cache_start)
if adp_start >= 0:
    adp_sym_start = text.rfind('(symbol', max(0, adp_start-50), adp_start)
    adp_block, adp_end = extract_balanced_block(text, adp_sym_start)
    
    if adp_block:
        # The ADP7118ARDZ has multiple sub-symbols. The first sub-symbol (unit 1) has the 
        # pins we care about. We need to find Pin 1 and Pin 2 in the FIRST sub-symbol.
        # The first sub-symbol is "ADP7118ARDZ_0_1" or similar.
        
        # Find ALL pin blocks with number "1" and "2"
        # We need to change only in the first unit's sub-symbol
        # The first unit sub-symbol contains: Pin 1 (VOUT), Pin 2 (VOUT), etc.
        
        # Actually let's find the first sub-symbol that contains Pin 1 with name VOUT
        # and change that Pin 1 from passive back to power_out,
        # then find Pin 2 in same sub-symbol and change to passive
        
        # Find all pin blocks with their positions
        pin_blocks = []
        pos = 0
        while True:
            idx = adp_block.find('(pin ', pos)
            if idx == -1:
                break
            block, end = extract_balanced_block(adp_block, idx)
            if block:
                num_m = re.search(r'\(number "(\d+)"', block)
                name_m = re.search(r'\(name "([^"]*)"', block)
                type_m = re.search(r'\(pin (\w+)', block)
                if num_m:
                    pin_blocks.append({
                        'num': num_m.group(1), 
                        'name': name_m.group(1) if name_m else '?',
                        'type': type_m.group(1) if type_m else '?',
                        'block': block, 
                        'idx': idx,
                        'end': end - idx
                    })
            pos = idx + 1
        
        print(f"\n  ADP7118ARDZ found {len(pin_blocks)} pins:")
        for p in pin_blocks:
            print(f"    Pin {p['num']:>2} ({p['name']:>10}, {p['type']:>10})")
        
        # Find the VOUT pins: Pin 1 and Pin 2 in the first unit
        # Pin 1 (VOUT) currently passive → should be power_out
        # Pin 2 (VOUT) currently power_out → should be passive
        
        # We need to work backwards through the blocks to avoid index shifts
        changes_to_make = []
        for p in pin_blocks:
            if p['num'] == '1' and p['name'] == 'VOUT' and p['type'] == 'passive':
                changes_to_make.append((p, 'passive', 'power_out'))
            elif p['num'] == '2' and p['name'] == 'VOUT' and p['type'] == 'power_out':
                changes_to_make.append((p, 'power_out', 'passive'))
        
        # Apply in reverse order of position
        changes_to_make.sort(key=lambda x: x[0]['idx'], reverse=True)
        for p, old_t, new_t in changes_to_make:
            old_block = p['block']
            new_block = change_pin_type_in_block(old_block, old_t, new_t)
            idx = p['idx']
            adp_block = adp_block[:idx] + new_block + adp_block[idx+len(old_block):]
            changes.append(f"U14 Pin {p['num']} ({p['name']}): {old_t} → {new_t}")
            print(f"  Pin {p['num']} ({p['name']}): {old_t} → {new_t} ✅")
        
        # Replace in text
        text = text[:adp_sym_start] + adp_block + text[adp_end:]

# ===== VALIDATION =====
print("\n=== BRACKET BALANCE ===")
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket balance: {depth}"
print(f"  Depth: {depth} ✅")

# Write
with open(SCH, "w") as f:
    f.write(text)

print(f"\n{len(changes)} changes applied:")
for c in changes:
    print(f"  {c}")
