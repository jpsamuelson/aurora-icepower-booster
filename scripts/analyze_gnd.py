#!/usr/bin/env python3
"""F1 Analysis: Understand all GND labels and their positions.

This script:
1. Finds all GND labels in the schematic
2. Checks if power:GND exists in lib_symbols cache
3. Outputs what needs to change
"""

import re
import os

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sch")

with open(SCH_FILE, 'r') as f:
    sch = f.read()

# Find all GND labels
gnd_labels = []
for m in re.finditer(r'\(label "GND" \(at ([\d.]+) ([\d.]+) (\d+)\)', sch):
    x, y, angle = float(m.group(1)), float(m.group(2)), int(m.group(3))
    # Get UUID
    block_start = m.start()
    # Find the containing (label block
    depth = 0
    end = block_start
    for i in range(block_start, min(block_start + 500, len(sch))):
        if sch[i] == '(': depth += 1
        elif sch[i] == ')': depth -= 1
        if depth == 0:
            end = i + 1
            break
    block = sch[block_start:end]
    uuid_m = re.search(r'\(uuid "([^"]+)"\)', block)
    uid = uuid_m.group(1) if uuid_m else "?"
    line_num = sch[:block_start].count('\n') + 1
    gnd_labels.append({
        'x': x, 'y': y, 'angle': angle, 'uuid': uid,
        'line': line_num, 'start': block_start, 'end': end,
        'block': block
    })

print(f"Found {len(gnd_labels)} GND labels:")
for i, lbl in enumerate(gnd_labels):
    print(f"  [{i+1:3d}] at ({lbl['x']}, {lbl['y']}) angle={lbl['angle']}° line={lbl['line']}")

# Check for power:GND in lib_symbols
has_power_gnd = 'symbol "power:GND"' in sch
print(f"\npower:GND in lib_symbols cache: {'YES' if has_power_gnd else 'NO'}")

# Check for any power symbols
power_symbols = re.findall(r'\(symbol \(lib_id "power:([^"]+)"\)', sch)
print(f"Power symbol instances: {power_symbols}")

# Check for global labels
global_gnd = re.findall(r'\(global_label "GND"', sch)
print(f"Global GND labels: {len(global_gnd)}")

# Check for net_class_flag labels (these are the problematic ones)
print(f"\nSample GND label block:")
if gnd_labels:
    print(gnd_labels[0]['block'])
