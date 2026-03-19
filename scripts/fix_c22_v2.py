#!/usr/bin/env python3
"""Fix C22 Pin 1 connection:
- Remove incorrect wire (147.62,34.19)→(150.16,34.19) connecting to GND
- Rejoin GND wire (150.16, 32.54→34.19) + (150.16, 34.19→35.0) → (150.16, 32.54→35.0)
- Add V+ label at C22 Pin 1 (147.62, 34.19)
"""
import re, uuid

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

orig_len = len(text)
changes = []

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

# 1. Remove incorrect horizontal wire (147.62, 34.19) → (150.16, 34.19)
m = re.search(r'\(wire\s*\(pts\s*\(xy 147\.62 34\.19\)\s*\(xy 150\.16 34\.19\)\)', text)
if m:
    start, end = extract_balanced(text, m.start())
    text = text[:start] + text[end:]
    changes.append("Removed wrong wire (147.62,34.19)→(150.16,34.19) [was connecting to GND]")
else:
    print("WARNING: Horizontal wire not found!")

# 2. Rejoin GND wire segments (150.16, 32.54→34.19) + (150.16, 34.19→35.0)
seg1 = re.search(r'\(wire\s*\(pts\s*\(xy 150\.16 32\.54\)\s*\(xy 150\.16 34\.19\)\)', text)
seg2 = re.search(r'\(wire\s*\(pts\s*\(xy 150\.16 34\.19\)\s*\(xy 150\.16 35(?:\.0)?\)\)', text)

if seg1 and seg2:
    s1_start, s1_end = extract_balanced(text, seg1.start())
    s2_start, s2_end = extract_balanced(text, seg2.start())
    
    new_wire = f'(wire (pts (xy 150.16 32.54) (xy 150.16 35.0)) (stroke (width 0) (type default)) (uuid "{uuid.uuid4()}"))'
    
    if s2_start > s1_start:
        text = text[:s2_start] + text[s2_end:]
        text = text[:s1_start] + new_wire + text[s1_end:]
    else:
        text = text[:s1_start] + text[s1_end:]
        seg2_new = re.search(r'\(wire\s*\(pts\s*\(xy 150\.16 34\.19\)\s*\(xy 150\.16 35', text)
        if seg2_new:
            s2s, s2e = extract_balanced(text, seg2_new.start())
            text = text[:s2s] + new_wire + text[s2e:]
    
    changes.append("Rejoined GND wire (150.16, 32.54→35.0)")
else:
    if not seg1:
        print("WARNING: GND segment (150.16, 32.54→34.19) not found!")
    if not seg2:
        print("WARNING: GND segment (150.16, 34.19→35.0) not found!")

# 3. Add V+ label at C22 Pin 1 (147.62, 34.19) pointing left
# Label needs to be at the pin location, facing the pin
# C22 Pin 1 is at local (0, 3.81) = schematic top of capacitor = (147.62, 34.19)
# Label pointing to the right (angle 0) connects at its left end
# For a label at (147.62, 34.19), angle 0 means text goes right from connection point
uid = str(uuid.uuid4())
v_plus_label = f'(label "V+" (at 147.62 34.19 0) (effects (font (size 1.27 1.27))) (uuid "{uid}"))'

# Insert before the last closing paren of the main schematic
# Find the position just before the final `)` of the schematic
# Looking for a safe insertion point — after the last wire or symbol
insert_pos = text.rfind('(wire ')
if insert_pos == -1:
    insert_pos = text.rfind('(symbol ')
# Find end of this block
_, insert_after = extract_balanced(text, insert_pos)
text = text[:insert_after] + ' ' + v_plus_label + text[insert_after:]
changes.append("Added V+ label at (147.62, 34.19) for C22 Pin 1")

# Bracket balance
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
if depth != 0:
    print(f"❌ Bracket imbalance: {depth}")
    exit(1)

with open(SCH, "w") as f:
    f.write(text)

print(f"{len(changes)} changes:")
for c in changes:
    print(f"  ✅ {c}")
print(f"File: {orig_len} → {len(text)} chars (delta: {len(text)-orig_len})")
print(f"Brackets balanced ✅")
