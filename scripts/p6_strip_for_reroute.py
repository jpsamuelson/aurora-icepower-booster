#!/usr/bin/env python3
"""
Step 0: Add island removal to GND zones, then strip all routing.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

# 1. Add island_removal_mode to both GND zones
# Insert after (thermal_bridge_width 0.5)
old_fill = '(thermal_bridge_width 0.5)\n                )'
new_fill = '(thermal_bridge_width 0.5)\n                        (island_removal_mode 2)\n                        (island_area_min 10)\n                )'

count = text.count(old_fill)
text = text.replace(old_fill, new_fill)
print(f"Added island removal settings to {count} zones")

# 2. Strip all routing (segments, vias, filled_polygons)
def remove_balanced_blocks(text, keyword):
    """Remove all top-level balanced blocks starting with keyword."""
    result = []
    i = 0
    removed = 0
    while i < len(text):
        # Check if we're at the start of the keyword
        if text[i:i+len(keyword)+1] == '(' + keyword:
            # Find the balanced block
            depth = 0
            j = i
            while j < len(text):
                if text[j] == '(':
                    depth += 1
                elif text[j] == ')':
                    depth -= 1
                    if depth == 0:
                        # Remove block and any trailing whitespace/newline
                        end = j + 1
                        while end < len(text) and text[end] in ' \t\n':
                            end += 1
                        removed += 1
                        i = end
                        break
                j += 1
            else:
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result), removed

text, seg_count = remove_balanced_blocks(text, 'segment')
print(f"Removed {seg_count} segments")

text, via_count = remove_balanced_blocks(text, 'via')
print(f"Removed {via_count} vias")

# Remove filled_polygon blocks within zones
text, fp_count = remove_balanced_blocks(text, 'filled_polygon')
print(f"Removed {fp_count} filled_polygons")

# Verify bracket balance
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(text)
print(f"Written {len(text)} bytes")
