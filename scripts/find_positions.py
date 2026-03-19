#!/usr/bin/env python3
"""Find positions of key components: R94-R104 (EMI filter Rs), D8-D25 (ESD TVS),
and compare with cold path equivalents R95-R105."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

def find_symbol(ref_name):
    """Find a symbol instance by reference designator."""
    # Pattern: search for the property "Reference" "REF" within a symbol block
    pat = rf'\(property "Reference" "{re.escape(ref_name)}"'
    for m in re.finditer(pat, text):
        # Walk backwards to find the enclosing (symbol (lib_id ...))
        pos = m.start()
        # Find the start of this symbol block
        depth = 0
        start = pos
        while start > 0:
            start -= 1
            if text[start] == ')': depth += 1
            elif text[start] == '(': 
                depth -= 1
                if depth < 0:
                    break
        
        # Now find the end of this symbol block
        depth = 0
        for end in range(start, min(start + 10000, len(text))):
            if text[end] == '(': depth += 1
            elif text[end] == ')': depth -= 1
            if depth == 0: break
        
        block = text[start:end+1]
        
        # Skip if this is inside lib_symbols cache
        if start < text.find('(symbol (lib_id'):
            continue
        
        lib_m = re.search(r'lib_id "([^"]+)"', block)
        pos_m = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
        val_m = re.search(r'\(property "Value" "([^"]+)"', block)
        
        if pos_m:
            return {
                'ref': ref_name,
                'lib': lib_m.group(1) if lib_m else '?',
                'pos': (float(pos_m.group(1)), float(pos_m.group(2))),
                'value': val_m.group(1) if val_m else '?',
            }
    return None

# Find all EMI filter and output series resistors
print("=== EMI / Output Resistors (47Ω) — Hot path ===")
for r in ['R94', 'R96', 'R98', 'R100', 'R102', 'R104']:
    info = find_symbol(r)
    if info:
        print(f"  {info['ref']}: val={info['value']}, pos={info['pos']}, lib={info['lib']}")

print("\n=== EMI / Output Resistors (47Ω) — Cold path ===")
for r in ['R95', 'R97', 'R99', 'R101', 'R103', 'R105']:
    info = find_symbol(r)
    if info:
        print(f"  {info['ref']}: val={info['value']}, pos={info['pos']}, lib={info['lib']}")

print("\n=== Output Series Resistors (47Ω) — Hot ===")
for r in ['R76', 'R77', 'R78', 'R36', 'R37']:
    info = find_symbol(r)
    if info:
        print(f"  {info['ref']}: val={info['value']}, pos={info['pos']}, lib={info['lib']}")

print("\n=== Output Series Resistors (47Ω) — Cold (R58-R63) ===")
for r in ['R58', 'R59', 'R60', 'R61', 'R62', 'R63']:
    info = find_symbol(r)
    if info:
        print(f"  {info['ref']}: val={info['value']}, pos={info['pos']}, lib={info['lib']}")

print("\n=== Zobel Resistors (R82-R93) ===")
for r in ['R82', 'R83', 'R84', 'R85', 'R86', 'R87', 'R88', 'R89', 'R90', 'R91', 'R92', 'R93']:
    info = find_symbol(r)
    if info:
        print(f"  {info['ref']}: val={info['value']}, pos={info['pos']}, lib={info['lib']}")

print("\n=== ESD Diodes D8-D25 ===")
for d in range(8, 26):
    info = find_symbol(f'D{d}')
    if info:
        print(f"  {info['ref']}: val={info['value']}, pos={info['pos']}, lib={info['lib']}")

print("\n=== XLR Connectors ===")
for j in range(3, 15):
    info = find_symbol(f'J{j}')
    if info:
        print(f"  {info['ref']}: val={info['value']}, pos={info['pos']}, lib={info['lib']}")
