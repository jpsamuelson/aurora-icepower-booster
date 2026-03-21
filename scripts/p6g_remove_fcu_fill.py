#!/usr/bin/env python3
"""
Remove F.Cu zone filled_polygon blocks. Keep B.Cu fills.
The F.Cu zone fragments cause more DRC issues than they solve.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'
FCU_ZONE_UUID = '0610c18b-8187-4528-8878-9fbc7b763ffa'

with open(PCB) as f:
    text = f.read()

def extract_balanced(text, start):
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
        i += 1
    return None, start

# Find the F.Cu zone block
fcu_zone_pos = text.find(f'(uuid "{FCU_ZONE_UUID}")')
if fcu_zone_pos < 0:
    print("F.Cu zone not found!")
    exit(1)

# Find zone start
zone_start = text.rfind('(zone', 0, fcu_zone_pos)
zone_block, zone_end = extract_balanced(text, zone_start)

# Remove filled_polygon blocks from this zone only
removed = 0
new_zone = ''
i = 0
while i < len(zone_block):
    if zone_block[i:i+16] == '(filled_polygon':
        fp_block, fp_end = extract_balanced(zone_block, i)
        if fp_block:
            # Skip this block + trailing whitespace
            j = fp_end - zone_start if fp_end > zone_start else fp_end
            # Actually fp_end is relative to zone_block start
            # Just recalculate
            local_end = i + len(fp_block)
            while local_end < len(zone_block) and zone_block[local_end] in ' \t\n':
                local_end += 1
            i = local_end
            removed += 1
            continue
    new_zone += zone_block[i]
    i += 1

# Replace the zone block in the text
text = text[:zone_start] + new_zone + text[zone_end:]

print(f"Removed {removed} filled_polygon blocks from F.Cu GND zone")

# Verify brackets
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
