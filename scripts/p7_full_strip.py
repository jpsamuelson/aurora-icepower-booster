#!/usr/bin/env python3
"""
Full clean slate: remove ALL routing (segments, vias, filled_polygons)
and prepare for a fresh Freerouting run.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

def remove_balanced_blocks(text, keyword):
    result = []
    i = 0
    removed = 0
    kw = '(' + keyword
    kw_len = len(kw)
    while i < len(text):
        if text[i:i+kw_len] == kw and (i+kw_len >= len(text) or text[i+kw_len] in ' \t\n('):
            depth = 0
            j = i
            while j < len(text):
                if text[j] == '(':
                    depth += 1
                elif text[j] == ')':
                    depth -= 1
                    if depth == 0:
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

text, segs = remove_balanced_blocks(text, 'segment')
print(f"Removed {segs} segments")
text, vias = remove_balanced_blocks(text, 'via')
print(f"Removed {vias} vias")
text, fps = remove_balanced_blocks(text, 'filled_polygon')
print(f"Removed {fps} filled_polygons")

# Verify
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
print(f"Written {len(text):,} bytes")
