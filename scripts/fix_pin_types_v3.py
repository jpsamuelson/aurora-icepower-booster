#!/usr/bin/env python3
"""Fix pin types using correct symbol names from lib_symbols cache."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    text = f.read()

def extract_balanced(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
    return None, start

def find_all_pins(region):
    results = []
    pos = 0
    while True:
        idx = region.find('(pin ', pos)
        if idx == -1:
            break
        block, _ = extract_balanced(region, idx)
        if block:
            num_m = re.search(r'\(number\s+"([^"]+)"', block)
            type_m = re.match(r'\(pin\s+(\w+)', block)
            name_m = re.search(r'\(name\s+"([^"]*)"', block)
            if num_m and type_m:
                results.append({
                    'block': block, 'idx': idx, 'len': len(block),
                    'num': num_m.group(1), 'type': type_m.group(1),
                    'name': name_m.group(1) if name_m else '?'
                })
        pos = idx + 1
    return results

changes_made = []

# ===== TEL5-2422 =====
print("=== TEL5-2422 ===")
# Find by full name in lib_symbols
tel_pat = re.search(r'\(symbol\s+"aurora-dsp-icepower-booster:TEL5-2422"', text)
if tel_pat:
    sym_start = tel_pat.start()
    tel_block, tel_end = extract_balanced(text, sym_start)
    print(f"  Block: {len(tel_block)} chars at {sym_start}")
    
    pins = find_all_pins(tel_block)
    print(f"  {len(pins)} pins found:")
    for p in pins:
        print(f"    Pin {p['num']:>2} ({p['name']:>12}): {p['type']}")
    
    # Changes needed:
    #   Pin 2 (-VIN(GND)): passive → power_out (revert)
    #   Pin 3 (-VIN(GND)): power_out → passive (correct)
    #   Pin 9 (COMMON): unspecified → power_in
    ops = []
    for p in pins:
        if p['num'] == '2' and p['type'] == 'passive':
            new_b = re.sub(r'\(pin passive', '(pin power_out', p['block'], 1)
            ops.append((p['idx'], p['len'], new_b, "Pin 2: passive → power_out"))
        elif p['num'] == '3' and p['type'] == 'power_out':
            new_b = re.sub(r'\(pin power_out', '(pin passive', p['block'], 1)
            ops.append((p['idx'], p['len'], new_b, "Pin 3: power_out → passive"))
        elif p['num'] == '9' and p['type'] == 'unspecified':
            new_b = re.sub(r'\(pin unspecified', '(pin power_in', p['block'], 1)
            ops.append((p['idx'], p['len'], new_b, "Pin 9: unspecified → power_in"))
    
    # Apply reverse order
    ops.sort(key=lambda x: x[0], reverse=True)
    for idx, length, new_block, desc in ops:
        tel_block = tel_block[:idx] + new_block + tel_block[idx+length:]
        changes_made.append(f"TEL5-2422 {desc}")
        print(f"  ✅ {desc}")
    
    text = text[:sym_start] + tel_block + text[tel_end:]
else:
    print("  NOT FOUND!")

# ===== ADP7118ARDZ =====
print("\n=== ADP7118ARDZ ===")
adp_pat = re.search(r'\(symbol\s+"aurora-dsp-icepower-booster:ADP7118ARDZ"', text)
if adp_pat:
    sym_start = adp_pat.start()
    adp_block, adp_end = extract_balanced(text, sym_start)
    print(f"  Block: {len(adp_block)} chars at {sym_start}")
    
    pins = find_all_pins(adp_block)
    print(f"  {len(pins)} pins found:")
    for p in pins:
        print(f"    Pin {p['num']:>2} ({p['name']:>12}): {p['type']}")
    
    # Changes needed:
    #   First Pin 1 (VOUT): passive → power_out (revert)
    #   First Pin 2 (VOUT): power_out → passive (correct)
    pin1_done = False
    pin2_done = False
    ops = []
    for p in pins:
        if p['num'] == '1' and p['name'] == 'VOUT' and p['type'] == 'passive' and not pin1_done:
            new_b = re.sub(r'\(pin passive', '(pin power_out', p['block'], 1)
            ops.append((p['idx'], p['len'], new_b, "Pin 1 (VOUT): passive → power_out"))
            pin1_done = True
        elif p['num'] == '2' and p['name'] == 'VOUT' and p['type'] == 'power_out' and not pin2_done:
            new_b = re.sub(r'\(pin power_out', '(pin passive', p['block'], 1)
            ops.append((p['idx'], p['len'], new_b, "Pin 2 (VOUT): power_out → passive"))
            pin2_done = True
    
    ops.sort(key=lambda x: x[0], reverse=True)
    for idx, length, new_block, desc in ops:
        adp_block = adp_block[:idx] + new_block + adp_block[idx+length:]
        changes_made.append(f"ADP7118ARDZ {desc}")
        print(f"  ✅ {desc}")
    
    text = text[:sym_start] + adp_block + text[adp_end:]
else:
    print("  NOT FOUND!")

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

print(f"\n{len(changes_made)} changes applied:")
for c in changes_made:
    print(f"  {c}")
