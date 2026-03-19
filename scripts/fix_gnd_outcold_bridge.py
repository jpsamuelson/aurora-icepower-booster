#!/usr/bin/env python3
"""Fix F1 part 2: Remove 6 CHx_OUT_COLD labels that are on GND wire chains.

These labels at x=285 bridge OUT_COLD nets into GND. Removing them separates
the OUT_COLD nets from GND while preserving the other 30 OUT_COLD labels on
correct wire chains.

Labels to remove:
  CH1_OUT_COLD at (285, 104)
  CH2_OUT_COLD at (285, 184)
  CH3_OUT_COLD at (285, 264)
  CH4_OUT_COLD at (285, 344)
  CH5_OUT_COLD at (285, 424)
  CH6_OUT_COLD at (285, 504)
"""
import re
import os

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sch")

def extract_balanced_block(content, start_idx):
    depth = 0
    for i in range(start_idx, len(content)):
        if content[i] == '(': depth += 1
        elif content[i] == ')': depth -= 1
        if depth == 0:
            return content[start_idx:i + 1], i + 1
    raise ValueError(f"Unbalanced at {start_idx}")

def check_balance(content, label=""):
    depth = 0
    for ch in content:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
    if depth != 0:
        raise ValueError(f"Bracket {label}: {depth}")
    print(f"  ✓ Bracket balance OK {label}")

with open(SCH_FILE) as f:
    sch = f.read()

check_balance(sch, "(before)")

# Find and remove the 6 problematic labels
targets = [
    ("CH1_OUT_COLD", "285", "104"),
    ("CH2_OUT_COLD", "285", "184"),
    ("CH3_OUT_COLD", "285", "264"),
    ("CH4_OUT_COLD", "285", "344"),
    ("CH5_OUT_COLD", "285", "424"),
    ("CH6_OUT_COLD", "285", "504"),
]

removed = 0
for name, tx, ty in targets:
    # Find the label - use flexible number matching
    pattern = rf'\(label "{name}" \(at {tx} {ty} \d+\)'
    m = re.search(pattern, sch)
    if m:
        block, end = extract_balanced_block(sch, m.start())
        line = sch[:m.start()].count('\n') + 1
        print(f"  Removing: {name} at ({tx}, {ty}) line {line}")
        # Remove the label block (and any surrounding whitespace/newline)
        # Check if there's a newline before and after
        start = m.start()
        # Remove leading whitespace on the same line
        while start > 0 and sch[start-1] in ' \t':
            start -= 1
        # Remove trailing newline
        if end < len(sch) and sch[end] == '\n':
            end += 1
        sch = sch[:start] + sch[end:]
        removed += 1
    else:
        print(f"  NOT FOUND: {name} at ({tx}, {ty})")

check_balance(sch, "(after removal)")

with open(SCH_FILE, 'w') as f:
    f.write(sch)

print(f"\n✓ Removed {removed}/6 OUT_COLD labels from GND wire chains")
print(f"  Schematic: {len(sch)} chars")
