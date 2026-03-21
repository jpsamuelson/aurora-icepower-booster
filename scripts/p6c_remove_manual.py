#!/usr/bin/env python3
"""
Remove the manually added route for CH6_GAIN_OUT (2 vias + 1 B.Cu segment).
They were the last items added to the PCB before zones.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

# Find net number
net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
net_num = net_m.group(1)

# Find all B.Cu segments and vias for this net that have the specific coordinates
# Via at (103.525, 183.855) and (112.0, 178.8)
# Segment (103.525, 183.855) -> (112.0, 178.8) on B.Cu

removed = 0

# Remove via at (103.525, 183.855) for this net
for coords in ['103.525 183.855', '112.0 178.8']:
    pat = re.compile(r'\t\(via\s+\(at\s+' + re.escape(coords) + r'\).*?\(net\s+' + net_num + r'\).*?\)\n', re.DOTALL)
    text, n = pat.subn('', text, count=1)
    removed += n

# Remove B.Cu segment between these points
pat = re.compile(r'\t\(segment\s+\(start\s+103\.525\s+183\.855\)\s+\(end\s+112\.0\s+178\.8\).*?\(net\s+' + net_num + r'\).*?\)\n', re.DOTALL)  
text, n = pat.subn('', text, count=1)
removed += n

print(f"Removed {removed} manual route elements")

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
print(f"Written {len(text)} bytes")
