#!/usr/bin/env python3
"""Analyze OUT_COLD label placement and wire topology around XLR connectors."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# Find all OUT_COLD labels (remaining after F1 fix)
print("=== Remaining OUT_COLD labels ===")
for m in re.finditer(r'\(label "(/?)CH\d_OUT_COLD"', text):
    start = m.start()
    # Find the enclosing block
    depth = 0
    for i in range(start, min(start+500, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    # Extract position
    pos = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
    name = re.search(r'"([^"]*OUT_COLD[^"]*)"', block)
    if pos and name:
        print(f"  {name.group(1)} at ({pos.group(1)}, {pos.group(2)})")

# Find all COLD_RAW labels
print("\n=== COLD_RAW labels ===")
for m in re.finditer(r'\(label "[^"]*COLD_RAW[^"]*"', text):
    start = m.start()
    depth = 0
    for i in range(start, min(start+500, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    pos = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
    name = re.search(r'"([^"]*COLD_RAW[^"]*)"', block)
    if pos and name:
        print(f"  {name.group(1)} at ({pos.group(1)}, {pos.group(2)})")

# Find all HOT_RAW labels
print("\n=== HOT_RAW labels ===")
for m in re.finditer(r'\(label "[^"]*HOT_RAW[^"]*"', text):
    start = m.start()
    depth = 0
    for i in range(start, min(start+500, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    pos = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
    name = re.search(r'"([^"]*HOT_RAW[^"]*)"', block)
    if pos and name:
        print(f"  {name.group(1)} at ({pos.group(1)}, {pos.group(2)})")

# Find all HOT_IN labels
print("\n=== HOT_IN labels ===")
for m in re.finditer(r'\(label "[^"]*HOT_IN[^"]*"', text):
    start = m.start()
    depth = 0
    for i in range(start, min(start+500, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    pos = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
    name = re.search(r'"([^"]*HOT_IN[^"]*)"', block)
    if pos and name:
        print(f"  {name.group(1)} at ({pos.group(1)}, {pos.group(2)})")

# Find XLR connectors J3-J8 positions
print("\n=== XLR Input connectors J3-J8 ===")
for ref in ['J3','J4','J5','J6','J7','J8']:
    pat = rf'\(symbol.*?\(property "Reference" "{ref}"'
    for m in re.finditer(pat, text, re.DOTALL):
        # Go back to find (symbol start
        start = m.start()
        depth = 0
        for i in range(start, min(start+5000, len(text))):
            if text[i] == '(': depth += 1
            elif text[i] == ')': depth -= 1
            if depth == 0: break
        block = text[start:i+1]
        lib = re.search(r'lib_id "([^"]+)"', block)
        pos = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
        pins = re.findall(r'\(pin "([^"]+)" \(uuid', block)
        print(f"  {ref}: lib={lib.group(1) if lib else '?'}, pos={pos.group(1) if pos else '?'},{pos.group(2) if pos else '?'}, pins={pins}")

# Find XLR connectors J9-J14 positions
print("\n=== XLR Output connectors J9-J14 ===")
for ref in ['J9','J10','J11','J12','J13','J14']:
    pat = rf'\(symbol.*?\(property "Reference" "{ref}"'
    for m in re.finditer(pat, text, re.DOTALL):
        start = m.start()
        depth = 0
        for i in range(start, min(start+5000, len(text))):
            if text[i] == '(': depth += 1
            elif text[i] == ')': depth -= 1
            if depth == 0: break
        block = text[start:i+1]
        lib = re.search(r'lib_id "([^"]+)"', block)
        pos = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
        pins = re.findall(r'\(pin "([^"]+)" \(uuid', block)
        print(f"  {ref}: lib={lib.group(1) if lib else '?'}, pos={pos.group(1) if pos else '?'},{pos.group(2) if pos else '?'}, pins={pins}")

# Find all net labels and count occurrences
print("\n=== All unique net labels (count) ===")
labels = {}
for m in re.finditer(r'\(label "([^"]+)"', text):
    name = m.group(1)
    labels[name] = labels.get(name, 0) + 1
for name in sorted(labels):
    if labels[name] > 0:
        print(f"  {name}: {labels[name]}")
