#!/usr/bin/env python3
"""Find pin offsets by searching for specific symbol blocks."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

lib_start = text.find('(lib_symbols')
inst_start = text.find('(symbol (lib_id', lib_start + 1)
cache = text[lib_start:inst_start]

# Find Device:R subsymbol
# In the cache it's stored as (symbol "Device:R" ...) containing (symbol "Device:R_0_1" ...)
# But our file is one long line, so we need to handle that

# Find all "(symbol " in cache
import re

print("=== Searching for key symbol definitions ===")
for target in ['Device:R', 'Device:D', 'Connector_Audio:XLR3"', 'Connector_Audio:XLR3_Ground"']:
    clean_target = target.rstrip('"')
    idx = cache.find(f'(symbol "{clean_target}"')
    if idx >= 0:
        # Show context
        snippet = cache[idx:idx+200]
        print(f"\n{clean_target} found at offset {idx}:")
        print(f"  {snippet[:150]}...")
    else:
        print(f"\n{clean_target}: NOT FOUND in cache")

# Let's try to find pins near "Device:R" in the cache
print("\n\n=== Finding Device:R pins ===")
r_idx = cache.find('"Device:R"')
if r_idx >= 0:
    # Extract a large block from this position
    block = cache[r_idx:r_idx+5000]
    # Find all pins
    for pm in re.finditer(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', block):
        # Find the nearest "(number ..." after this pin
        rest = block[pm.end():]
        nm = re.search(r'\(number "([^"]+)"\)', rest[:200])
        if nm:
            print(f"  Pin {nm.group(1)} ({pm.group(1)} {pm.group(2)}): at ({pm.group(3)}, {pm.group(4)}) rot={pm.group(5) or 0}")

print("\n\n=== Finding Device:D pins ===")
d_idx = cache.find('"Device:D"')
if d_idx >= 0:
    block = cache[d_idx:d_idx+5000]
    for pm in re.finditer(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', block):
        rest = block[pm.end():]
        nm = re.search(r'\(number "([^"]+)"\)', rest[:200])
        if nm:
            print(f"  Pin {nm.group(1)} ({pm.group(1)} {pm.group(2)}): at ({pm.group(3)}, {pm.group(4)}) rot={pm.group(5) or 0}")

print("\n\n=== Finding XLR3_Ground pins ===")
x_idx = cache.find('"Connector_Audio:XLR3_Ground"')
if x_idx >= 0:
    block = cache[x_idx:x_idx+10000]
    for pm in re.finditer(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', block):
        rest = block[pm.end():]
        nm = re.search(r'\(number "([^"]+)"\)', rest[:200])
        if nm:
            print(f"  Pin {nm.group(1)} ({pm.group(1)} {pm.group(2)}): at ({pm.group(3)}, {pm.group(4)}) rot={pm.group(5) or 0}")

print("\n\n=== Finding XLR3 pins (output) ===")
# XLR3 without _Ground - need to be careful not to match XLR3_Ground
# Search for "Connector_Audio:XLR3" followed by " (not _)
for m in re.finditer(r'"Connector_Audio:XLR3"', cache):
    block = cache[m.start():m.start()+10000]
    for pm in re.finditer(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', block):
        rest = block[pm.end():]
        nm = re.search(r'\(number "([^"]+)"\)', rest[:200])
        if nm:
            print(f"  Pin {nm.group(1)} ({pm.group(1)} {pm.group(2)}): at ({pm.group(3)}, {pm.group(4)}) rot={pm.group(5) or 0}")
    break
