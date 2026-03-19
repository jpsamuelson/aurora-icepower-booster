#!/usr/bin/env python3
"""Find pin offsets from lib_symbols cache, with debug."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# Find the lib_symbols section boundaries
lib_start = text.find('(lib_symbols')
# Find start of first symbol instance
inst_start = text.find('(symbol (lib_id', lib_start + 1)
cache = text[lib_start:inst_start]

print(f"lib_symbols section: {len(cache)} chars, from pos {lib_start} to {inst_start}")

# Find all sub-symbol names that contain pins
# In KiCad, pins are in sub-symbols like "Device:R_0_1"
pin_locs = {}  # sub_symbol_name -> [(pin_num, x, y)]

# Find ALL pin definitions in the cache
pins_in_cache = list(re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', cache))
print(f"Total pins found in cache: {len(pins_in_cache)}")

# Show first few pins with context
for i, pm in enumerate(pins_in_cache[:5]):
    start = max(0, pm.start() - 200)
    ctx = cache[start:pm.end() + 100]
    # Find the enclosing symbol name
    sym_m = re.search(r'\(symbol "([^"]+)"', cache[:pm.start()][::-1][:500][::-1])
    print(f"\nPin {i}: at ({pm.group(1)}, {pm.group(2)})")
    
# Better approach: find all sub-symbols with pins
print("\n\n=== Sub-symbols with pins ===")

for m in re.finditer(r'\(symbol "([^"]+)"', cache):
    sym_name = m.group(1)
    start = m.start()
    
    # Find the block
    depth = 0
    for i in range(start, min(start + 10000, len(cache))):
        if cache[i] == '(': depth += 1
        elif cache[i] == ')': depth -= 1
        if depth == 0: break
    block = cache[start:i+1]
    
    # Find pins in this block
    pins = []
    for pm in re.finditer(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\).*?\(number "([^"]+)"\)', block, re.DOTALL):
        pins.append({
            'type': pm.group(1), 'style': pm.group(2),
            'x': float(pm.group(3)), 'y': float(pm.group(4)),
            'rot': int(pm.group(5)) if pm.group(5) else 0,
            'num': pm.group(6),
        })
    
    if pins and ('Device' in sym_name or 'XLR' in sym_name or 'Connector' in sym_name):
        print(f"\n  {sym_name}:")
        for p in pins:
            print(f"    Pin {p['num']} ({p['type']} {p['style']}): at ({p['x']}, {p['y']}) rot={p['rot']}°")
