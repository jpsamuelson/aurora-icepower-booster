#!/usr/bin/env python3
"""Rejoin wire segments (98, 21.19→20) + (98, 20→18.65) → (98, 21.19→18.65)
after PWR_FLAG removal removed the T-junction at y=20."""
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
                return start, i+1
    return start, start

# Find exact positions
seg1_m = re.search(r'\(wire\s*\(pts\s*\(xy 98(?:\.0)? 21\.19\)\s*\(xy 98(?:\.0)? 20(?:\.0)?\)\)', text)
seg2_m = re.search(r'\(wire\s*\(pts\s*\(xy 98(?:\.0)? 20(?:\.0)?\)\s*\(xy 98(?:\.0)? 18\.65\)\)', text)

if not seg1_m or not seg2_m:
    print("Segments not found!")
    exit(1)

# Extract full balanced blocks
s1_start, s1_end = extract_balanced(text, seg1_m.start())
s2_start, s2_end = extract_balanced(text, seg2_m.start())

print(f"Seg1: pos {s1_start}-{s1_end}: {text[s1_start:s1_end][:80]}...")
print(f"Seg2: pos {s2_start}-{s2_end}: {text[s2_start:s2_end][:80]}...")

# Build replacement
new_wire = '(wire (pts (xy 98.0 21.19) (xy 98.0 18.65)) (stroke (width 0) (type default)) (uuid "rejoin-98-vert"))'

# Remove seg2 first (later in file), replace seg1 with joined wire
text = text[:s2_start] + text[s2_end:]
text = text[:s1_start] + new_wire + text[s1_end:]

# Bracket check
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"

with open(SCH, "w") as f:
    f.write(text)

print(f"\n✅ Rejoined wire (98, 21.19→18.65)")
print(f"Brackets balanced ✅")
