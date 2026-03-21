#!/usr/bin/env python3
"""
Fix regressions from p5g: restore XLR refs to safe positions,
fix R88-R93 direction, C80/D1 adjustments.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

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

# Override table
# XLR connectors: original library position was (4.3, -10.0) which worked for 
# input connectors (J3-J8) but NOT for outputs (J9-J14).
# For J9-J14 rot=90°: (4.3,-10) → global (134+10, y+4.3)=(144,y+4.3) — works, in connector body
# For J3-J8 rot=180°: (4.3,-10) → global (12.58-4.3, 44.45+10)=(8.28,54.45) — works, in connector body
# The previous NO-violation state had these refs. Restore them.
overrides = {}

# Restore XLR to library defaults (4.3, -10.0)
for j in ['J3', 'J4', 'J5', 'J6', 'J7', 'J8',
          'J9', 'J10', 'J11', 'J12', 'J13', 'J14']:
    overrides[j] = (4.3, -10.0)

# R84, R88-R93: flipping Y didn't work (lands on XLR pads)
# Try shifting in X direction instead: (1.65, 0) or (-1.65, 0)
# With rot=90°: local (1.65, 0) → global (0, 1.65) — offset along Y, away from both sides
# But sign: 90° CCW rotation: x'=0*cos90-0*sin90=0, y'=0*sin90+0*cos90=0? 
# Local (1.65, 0): x'=1.65*cos90=0, y'=1.65*sin90=1.65, global offset=(0, 1.65)
# That shifts DOWN (larger Y) which should be clear of XLR pads
# Actually the standard ref position at (0, -1.65) already causes issues.
# The problem is these resistors are packed between other resistors and XLR connectors.
# Better approach: just use library default (0, -1.65) — the original DRC only had 1 over_copper (R84)
# The R88-R93 flip was causing the 6 new violations. Let me restore those to library default too.
overrides['R84'] = (0.0, -1.65)  # restore library default
for r in ['R88', 'R89', 'R90', 'R91', 'R92', 'R93']:
    overrides[r] = (0.0, -1.65)  # restore library default

# Apply overrides
i = 0
changes = 0
result_parts = []
last_end = 0

while True:
    idx = text.find('(footprint ', i)
    if idx < 0:
        break
    block, end = extract_balanced(text, idx)
    if not block:
        i = idx + 1
        continue
    
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    if not ref_m:
        i = end
        continue
    ref = ref_m.group(1)
    
    if ref in overrides:
        new_dx, new_dy = overrides[ref]
        ref_at_pat = r'(\(property\s+"Reference"\s+"[^"]+"\s+\(at\s+)([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?(\))'
        ref_at_m = re.search(ref_at_pat, block)
        if ref_at_m:
            old_angle = ref_at_m.group(4)
            if old_angle:
                new_at = f'{ref_at_m.group(1)}{new_dx} {new_dy} {old_angle})'
            else:
                new_at = f'{ref_at_m.group(1)}{new_dx} {new_dy})'
            
            abs_pos = idx + ref_at_m.start()
            abs_end = idx + ref_at_m.end()
            result_parts.append(text[last_end:abs_pos])
            result_parts.append(new_at)
            last_end = abs_end
            changes += 1
    i = end

result_parts.append(text[last_end:])
new_text = ''.join(result_parts)

depth = 0
for ch in new_text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"

print(f"Applied {changes} regression fixes")
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(new_text)
print(f"Written {len(new_text)} bytes")
