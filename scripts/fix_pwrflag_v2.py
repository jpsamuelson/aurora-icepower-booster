#!/usr/bin/env python3
"""Remove PWR_FLAG #FLG0104 + its wire + rejoin split wire.
U1 Pin 2 (power_out) drives GND, making the PWR_FLAG redundant."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    text = f.read()

orig_len = len(text)
changes = []

def extract_balanced(text, start):
    """Extract balanced parenthesized block starting at position start."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], start, i+1
    return None, start, start

# =========================================================
# 1. Find and remove #FLG0104 symbol instance
# =========================================================
# Search for PWR_FLAG symbols and check which one is #FLG0104
flg_removed = False
search_pos = 0
while True:
    idx = text.find('(symbol (lib_id "power:PWR_FLAG")', search_pos)
    if idx == -1:
        break
    block, bstart, bend = extract_balanced(text, idx)
    if block and '#FLG0104' in block:
        print(f"Found #FLG0104 at pos {bstart}, length {len(block)} chars")
        # Verify it's at (95, 20)
        if '95' in block and '20' in block:
            text = text[:bstart] + text[bend:]
            changes.append(f"Removed #FLG0104 PWR_FLAG ({len(block)} chars)")
            flg_removed = True
            break
    search_pos = idx + 1

if not flg_removed:
    print("WARNING: #FLG0104 not found!")

# =========================================================
# 2. Remove wire (95, 20) → (98, 20)
# =========================================================
wire_pat = re.compile(r'\(wire\s+\(pts\s+\(xy\s+95(?:\.0)?\s+20(?:\.0)?\)\s+\(xy\s+98(?:\.0)?\s+20(?:\.0)?\)\)\s*\(stroke[^)]*\)\s*\(uuid\s+"[^"]*"\)\s*\)')
m = wire_pat.search(text)
if m:
    text = text[:m.start()] + text[m.end():]
    changes.append(f"Removed wire (95,20)→(98,20)")
else:
    print("WARNING: Wire (95,20)→(98,20) not found!")
    # Try simpler pattern
    simple = re.search(r'\(wire\s*\(pts\s*\(xy 95\.0 20\.0\)\s*\(xy 98\.0 20\.0\)\)', text)
    if simple:
        block, bstart, bend = extract_balanced(text, simple.start())
        if block:
            text = text[:bstart] + text[bend:]
            changes.append(f"Removed wire (95,20)→(98,20) [simple match]")

# =========================================================
# 3. Rejoin wire split at x=98: (98, 21.19→20) + (98, 20→18.65) → (98, 21.19→18.65)
# =========================================================
# Find both segments
seg1_pat = re.compile(r'\(wire\s+\(pts\s+\(xy\s+98(?:\.0)?\s+21\.19\)\s+\(xy\s+98(?:\.0)?\s+20(?:\.0)?\)\)\s*\(stroke[^)]*\)\s*\(uuid\s+"[^"]*"\)\s*\)')
seg2_pat = re.compile(r'\(wire\s+\(pts\s+\(xy\s+98(?:\.0)?\s+20(?:\.0)?\)\s+\(xy\s+98(?:\.0)?\s+18\.65\)\)\s*\(stroke[^)]*\)\s*\(uuid\s+"[^"]*"\)\s*\)')

s1 = seg1_pat.search(text)
s2 = seg2_pat.search(text)

if not s1:
    # Try simpler match
    s1_simple = re.search(r'\(wire\s*\(pts\s*\(xy 98\.0 21\.19\)\s*\(xy 98\.0 20\.0\)\)', text)
    if s1_simple:
        _, s1_start, s1_end = extract_balanced(text, s1_simple.start())
        s1 = type('Match', (), {'start': lambda self: s1_start, 'end': lambda self: s1_end})()

if not s2:
    s2_simple = re.search(r'\(wire\s*\(pts\s*\(xy 98\.0 20\.0\)\s*\(xy 98\.0 18\.65\)\)', text)
    if s2_simple:
        _, s2_start, s2_end = extract_balanced(text, s2_simple.start())
        s2 = type('Match', (), {'start': lambda self: s2_start, 'end': lambda self: s2_end})()

if s1 and s2:
    new_wire = '(wire (pts (xy 98.0 21.19) (xy 98.0 18.65)) (stroke (width 0) (type default)) (uuid "rejoin-98-vert"))'
    
    # Remove in reverse order (later position first)
    pos1, end1 = s1.start(), s1.end()
    pos2, end2 = s2.start(), s2.end()
    
    if pos2 > pos1:
        text = text[:pos2] + text[end2:]
        text = text[:pos1] + new_wire + text[end1:]
    else:
        text = text[:pos1] + text[end1:]
        text = text[:pos2] + new_wire + text[end2:]
    
    changes.append("Rejoined wire (98, 21.19→18.65)")
else:
    if not s1:
        print("WARNING: Segment (98, 21.19→20) not found")
    if not s2:
        print("WARNING: Segment (98, 20→18.65) not found")

# =========================================================
# VALIDATION
# =========================================================
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
if depth != 0:
    print(f"❌ Bracket imbalance: {depth}")
    print("NOT saving file!")
    exit(1)

with open(SCH, "w") as f:
    f.write(text)

print(f"\n{len(changes)} changes:")
for c in changes:
    print(f"  ✅ {c}")
print(f"File: {orig_len} → {len(text)} chars (delta: {len(text)-orig_len})")
print(f"Brackets balanced ✅")
