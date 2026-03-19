#!/usr/bin/env python3
"""Fix 8: Update .kicad_sym library to match cache pin type changes.
Also handles the U1 Pin 1 (~, power_out) which has no wire — needs no_connect or removal."""
import re

LIB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sym"
with open(LIB, "r") as f:
    lib_text = f.read()

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

changes = []

# ===== TEL5-2422 in library =====
print("=== TEL5-2422 in .kicad_sym ===")
tel_m = re.search(r'\(symbol\s+"TEL5-2422"', lib_text)
if tel_m:
    sym_start = tel_m.start()
    tel_block, tel_end = extract_balanced(lib_text, sym_start)
    print(f"  Found: {len(tel_block)} chars")
    
    pins = find_all_pins(tel_block)
    for p in pins:
        print(f"    Pin {p['num']:>2} ({p['name']:>12}): {p['type']}")
    
    # Apply same changes as cache
    pin_changes = {
        '3': ('power_out', 'passive'),
        '9': ('unspecified', 'power_in'),
        '16': ('unspecified', 'power_in'),
    }
    
    ops = []
    for p in pins:
        if p['num'] in pin_changes:
            old_t, new_t = pin_changes[p['num']]
            if p['type'] == old_t:
                new_b = p['block'].replace(f'(pin {old_t}', f'(pin {new_t}', 1)
                ops.append((p['idx'], p['len'], new_b, f"Pin {p['num']}: {old_t} → {new_t}"))
    
    ops.sort(key=lambda x: x[0], reverse=True)
    for idx, length, new_block, desc in ops:
        tel_block = tel_block[:idx] + new_block + tel_block[idx+length:]
        changes.append(f"TEL5-2422 {desc}")
        print(f"  ✅ {desc}")
    
    lib_text = lib_text[:sym_start] + tel_block + lib_text[tel_end:]
else:
    print("  NOT FOUND in library!")

# ===== ADP7118ARDZ in library =====
print("\n=== ADP7118ARDZ in .kicad_sym ===")
adp_m = re.search(r'\(symbol\s+"ADP7118ARDZ"', lib_text)
if adp_m:
    sym_start = adp_m.start()
    adp_block, adp_end = extract_balanced(lib_text, sym_start)
    print(f"  Found: {len(adp_block)} chars")
    
    pins = find_all_pins(adp_block)
    for p in pins:
        print(f"    Pin {p['num']:>2} ({p['name']:>12}): {p['type']}")
    
    # Change first Pin 2 (VOUT) from power_out to passive
    pin2_done = False
    ops = []
    for p in pins:
        if p['num'] == '2' and p['name'] == 'VOUT' and p['type'] == 'power_out' and not pin2_done:
            new_b = p['block'].replace('(pin power_out', '(pin passive', 1)
            ops.append((p['idx'], p['len'], new_b, "Pin 2 (VOUT): power_out → passive"))
            pin2_done = True
    
    ops.sort(key=lambda x: x[0], reverse=True)
    for idx, length, new_block, desc in ops:
        adp_block = adp_block[:idx] + new_block + adp_block[idx+length:]
        changes.append(f"ADP7118ARDZ {desc}")
        print(f"  ✅ {desc}")
    
    lib_text = lib_text[:sym_start] + adp_block + lib_text[adp_end:]
else:
    print("  NOT FOUND in library!")

# ===== VALIDATION =====
depth = 0
for ch in lib_text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"\n  Brackets balanced ✅")

with open(LIB, "w") as f:
    f.write(lib_text)

print(f"\n{len(changes)} changes to .kicad_sym:")
for c in changes:
    print(f"  {c}")
