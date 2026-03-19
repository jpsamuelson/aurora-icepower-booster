#!/usr/bin/env python3
"""Remove redundant PWR_FLAG #FLG0104 + its wire.
U1 Pin 2 (power_out) now drives GND via proper wire endpoints, making PWR_FLAG unnecessary."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
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
                return text[start:i+1], start, i+1
    return None, start, start

# 1. Remove #FLG0104 symbol instance
# Search for the symbol with Reference #FLG0104
flg_pat = re.compile(r'\(symbol\s*\(lib_id\s+"power:PWR_FLAG"\)')
pos = 0
while True:
    m = flg_pat.search(text, pos)
    if not m:
        break
    block, start, end = extract_balanced(text, m.start())
    if block and '#FLG0104' in block:
        # Remove the block + surrounding whitespace
        # Check for leading whitespace/newline
        rm_start = start
        rm_end = end
        # Remove trailing whitespace up to next non-space
        while rm_end < len(text) and text[rm_end] in ' \t\n':
            rm_end += 1
        text = text[:rm_start] + text[rm_end:]
        changes.append(f"Removed #FLG0104 PWR_FLAG symbol instance ({len(block)} chars)")
        break
    pos = m.end()

# 2. Remove the wire from #FLG0104 to GND: (95, 20) → (98, 20)
# This wire was added by fix_erc_all.py
wire_95_98 = re.search(r'\(wire\s*\(pts\s*\(xy\s+95(?:\.0)?\s+20(?:\.0)?\)\s*\(xy\s+98(?:\.0)?\s+20(?:\.0)?\)\)', text)
if wire_95_98:
    start = wire_95_98.start()
    end = wire_95_98.end()
    # Remove trailing whitespace
    while end < len(text) and text[end] in ' \t\n':
        end += 1
    text = text[:start] + text[end:]
    changes.append("Removed wire (95,20)→(98,20) that connected #FLG0104 to GND")

# 3. Also need to remove #FLG0104 from lib_symbols cache if it was added
# PWR_FLAG was already in cache (per prefix_analysis.py), so we should NOT remove it
# since other PWR_FLAGs (#FLG0101-0103) still use it

# 4. Undo wire split at (98, 21.19→18.65) that was split at y=20 for #FLG0104 connection
# Original wire was (98, 21.19) → (98, 18.65), split into:
#   (98, 21.19) → (98, 20) and (98, 20) → (98, 18.65)
# Need to rejoin these two segments
seg1 = re.search(r'\(wire\s*\(pts\s*\(xy\s+98(?:\.0)?\s+21\.19\)\s*\(xy\s+98(?:\.0)?\s+20(?:\.0)?\)\)', text)
seg2 = re.search(r'\(wire\s*\(pts\s*\(xy\s+98(?:\.0)?\s+20(?:\.0)?\)\s*\(xy\s+98(?:\.0)?\s+18\.65\)\)', text)

if seg1 and seg2:
    # Remove seg2 first (later in string)
    s2_start = seg2.start()
    s2_end = seg2.end()
    while s2_end < len(text) and text[s2_end] in ' \t\n':
        s2_end += 1
    
    # Replace seg1 with rejoined wire
    new_wire = '(wire (pts (xy 98.0 21.19) (xy 98.0 18.65)) (stroke (width 0) (type default)) (uuid "rejoin-98-wire"))'
    
    # Remove seg2 first (it's after seg1 in text)
    if s2_start > seg1.start():
        text = text[:s2_start] + text[s2_end:]
        text = text[:seg1.start()] + new_wire + text[seg1.end():]
    else:
        text = text[:seg1.start()] + new_wire + text[seg1.end():]
        # Recalculate seg2 position after seg1 change
        seg2_new = re.search(r'\(wire\s*\(pts\s*\(xy\s+98(?:\.0)?\s+20(?:\.0)?\)\s*\(xy\s+98(?:\.0)?\s+18\.65\)\)', text)
        if seg2_new:
            s2_start = seg2_new.start()
            s2_end = seg2_new.end()
            while s2_end < len(text) and text[s2_end] in ' \t\n':
                s2_end += 1
            text = text[:s2_start] + text[s2_end:]
    
    changes.append("Rejoined wire (98, 21.19→18.65) — removed split at y=20")
elif seg1:
    changes.append("WARNING: Found seg1 (98, 21.19→20) but not seg2 (98, 20→18.65)")
elif seg2:
    changes.append("WARNING: Found seg2 (98, 20→18.65) but not seg1 (98, 21.19→20)")
else:
    # Maybe the wire was not split, or has different coordinates
    # Search for any wire at x=98 near y=20
    print("  Note: Wire segments at x=98 near y=20 not found — may not have been split")

# Bracket balance
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"

with open(SCH, "w") as f:
    f.write(text)

print(f"Changes ({len(changes)}):")
for c in changes:
    print(f"  {c}")
print(f"File: {orig_len} → {len(text)} chars (delta: {len(text)-orig_len})")
print(f"Brackets balanced ✅")
