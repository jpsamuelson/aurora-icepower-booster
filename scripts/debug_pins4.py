#!/usr/bin/env python3
"""Extract pin numbers from lib_symbols - debug raw text."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

lib_start = text.find('(lib_symbols')
inst_start = text.find('(symbol (lib_id', lib_start + 1)
cache = text[lib_start:inst_start]

def extract_block(s, start):
    depth = 0
    for i in range(start, len(s)):
        if s[i] == '(': depth += 1
        elif s[i] == ')': depth -= 1
        if depth == 0: return s[start:i+1]
    return ""

# For Device:R - show raw pin blocks
idx = cache.find('(symbol "Device:R"')
block = extract_block(cache, idx)

# Find each (pin ...) block and extract it
for pm in re.finditer(r'\(pin ', block):
    pin_block = extract_block(block, pm.start())
    # Parse number from pin_block
    nm = re.search(r'\(number "([^"]+)"\)', pin_block)
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', pin_block)
    name = re.search(r'\(name "([^"]+)"\)', pin_block)
    if nm and at:
        print(f"Device:R Pin {nm.group(1)} (name={name.group(1) if name else '?'}): at ({at.group(1)}, {at.group(2)}) rot={at.group(3) or 0}")

# For Device:D
idx = cache.find('(symbol "Device:D"')
block = extract_block(cache, idx)
for pm in re.finditer(r'\(pin ', block):
    pin_block = extract_block(block, pm.start())
    nm = re.search(r'\(number "([^"]+)"\)', pin_block)
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', pin_block)
    name = re.search(r'\(name "([^"]+)"\)', pin_block)
    if nm and at:
        print(f"Device:D Pin {nm.group(1)} (name={name.group(1) if name else '?'}): at ({at.group(1)}, {at.group(2)}) rot={at.group(3) or 0}")

# For XLR3_Ground
idx = cache.find('(symbol "Connector_Audio:XLR3_Ground"')
block = extract_block(cache, idx)
for pm in re.finditer(r'\(pin ', block):
    pin_block = extract_block(block, pm.start())
    nm = re.search(r'\(number "([^"]+)"\)', pin_block)
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', pin_block)
    name = re.search(r'\(name "([^"]+)"\)', pin_block)
    if nm and at:
        print(f"XLR3_Ground Pin {nm.group(1)} (name={name.group(1) if name else '?'}): at ({at.group(1)}, {at.group(2)}) rot={at.group(3) or 0}")

# For XLR3
for m in re.finditer(r'\(symbol "Connector_Audio:XLR3"', cache):
    block = extract_block(cache, m.start())
    if 'Ground' not in block[:50]:
        for pm in re.finditer(r'\(pin ', block):
            pin_block = extract_block(block, pm.start())
            nm = re.search(r'\(number "([^"]+)"\)', pin_block)
            at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\)', pin_block)
            name = re.search(r'\(name "([^"]+)"\)', pin_block)
            if nm and at:
                print(f"XLR3 Pin {nm.group(1)} (name={name.group(1) if name else '?'}): at ({at.group(1)}, {at.group(2)}) rot={at.group(3) or 0}")
        break
