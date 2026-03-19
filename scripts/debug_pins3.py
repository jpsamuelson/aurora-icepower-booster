#!/usr/bin/env python3
"""Extract full symbol blocks from cache using bracket matching."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

lib_start = text.find('(lib_symbols')
inst_start = text.find('(symbol (lib_id', lib_start + 1)
cache = text[lib_start:inst_start]

def extract_block(text, start):
    """Extract a balanced bracket block starting at position start."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: return text[start:i+1]
    return ""

# Find Device:R
for target in ['Device:R', 'Device:D', 'Connector_Audio:XLR3_Ground', 'Connector_Audio:XLR3']:
    idx = cache.find(f'(symbol "{target}"')
    if idx < 0:
        print(f"{target}: NOT FOUND")
        continue
    
    block = extract_block(cache, idx)
    print(f"\n=== {target} ({len(block)} chars) ===")
    
    # Find all pins in the block
    for pm in re.finditer(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', block):
        # Find nearest (number ...)
        rest = block[pm.end():pm.end()+500]
        nm = re.search(r'\(number "([^"]+)"\)', rest)
        pnum = nm.group(1) if nm else "?"
        print(f"  Pin {pnum} ({pm.group(1)}): at ({pm.group(3)}, {pm.group(4)}) rot={pm.group(5) or 0}")
