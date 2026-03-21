#!/usr/bin/env python3
"""
Targeted silk reference repositioning based on DRC analysis.

Fixes:
1. XLR connectors (J9-J14): Move ref to connector center to avoid landing on nearby components
2. IC/cap pairs (U2-U13 + C2-C7,C26-C31): Move cap ref to opposite side to avoid overlap
3. MH1/MH2: Move ref below (positive Y) to avoid board edge
4. Specific over-copper: C80, D1, R84 — flip ref to other side
5. Remaining ref-vs-outline: Reduce text size for dense areas
"""
import re, json

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

# Build ref→override table: { "ref": (new_dx, new_dy) }
# None means: keep library default
overrides = {}

# 1. XLR male output connectors: move ref to center of connector body
# Current local (4.3, -10.0) with rot=90 puts ref at x=124 area (on resistors)
# Use (0, 0) to put ref at connector center
for j in ['J9', 'J10', 'J11', 'J12', 'J13', 'J14']:
    overrides[j] = (0.0, 0.0)

# XLR female input connectors (J3-J8) — currently no violations but let's be consistent
for j in ['J3', 'J4', 'J5', 'J6', 'J7', 'J8']:
    overrides[j] = (0.0, 0.0)

# 2. IC/cap pairs: flip cap refs to POSITIVE Y (below component)
# The bypass caps C2-C7 are next to ICs U2-U7
# The caps C26-C31 are next to ICs U8-U13 (second row)
for c in ['C2', 'C3', 'C4', 'C5', 'C6', 'C7',
          'C26', 'C27', 'C28', 'C29', 'C30', 'C31']:
    overrides[c] = (0.0, 1.68)  # flip from -1.68 to +1.68

# 3. MH1/MH2: flip ref below (positive Y = away from board edge at y=0)
overrides['MH1'] = (0.0, 4.15)
overrides['MH2'] = (0.0, 4.15)

# 4. Specific silk_over_copper fixes
# C80 at (46,28) rot=0 — ref at (0,-1.68) lands on nearby copper → flip
overrides['C80'] = (0.0, 1.68)

# D1 at (40,20) rot=0 — D_SMB ref at (0,-3.0) lands on copper → flip
overrides['D1'] = (0.0, 3.0)

# R84 at (123,96.32) rot=90 — ref landing on copper → flip
overrides['R84'] = (0.0, 1.65)

# 5. Additional overlapping resistors near XLR area
# R82-R87 and R88-R93 are in pairs that overlap with each other
# R82,R83,...R87 are at x≈123, R88-R93 at x≈123 but 7mm offset in Y
# Flip the second set (R88-R93) to positive Y side
for r in ['R88', 'R89', 'R90', 'R91', 'R92', 'R93']:
    overrides[r] = (0.0, 1.65)

# 6. C79 overlaps U1 outline — move ref further from U1
overrides['C79'] = (0.0, 1.68)  # flip to other side

# 7. C19 overlaps FB2 — flip C19 ref
overrides['C19'] = (0.0, 1.68)

# 8. U15 ref overlaps its own polygon — shift it up more
overrides['U15'] = (0.0, -4.5)  # slightly further above

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
    
    # Get reference
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    if not ref_m:
        i = end
        continue
    ref = ref_m.group(1)
    
    if ref in overrides:
        new_dx, new_dy = overrides[ref]
        
        # Find and replace the reference field's (at ...) 
        ref_at_pat = r'(\(property\s+"Reference"\s+"[^"]+"\s+\(at\s+)([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?(\))'
        ref_at_m = re.search(ref_at_pat, block)
        if ref_at_m:
            old_at = ref_at_m.group(0)
            old_angle = ref_at_m.group(4)
            
            if old_angle:
                new_at = f'{ref_at_m.group(1)}{new_dx} {new_dy} {old_angle})'
            else:
                new_at = f'{ref_at_m.group(1)}{new_dx} {new_dy})'
            
            # Replace in the original text (absolute position)
            abs_pos = idx + ref_at_m.start()
            abs_end = idx + ref_at_m.end()
            result_parts.append(text[last_end:abs_pos])
            result_parts.append(new_at)
            last_end = abs_end
            changes += 1
            
    i = end

result_parts.append(text[last_end:])
new_text = ''.join(result_parts)

# Verify bracket balance
depth = 0
for ch in new_text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"

print(f"Applied {changes} targeted reference overrides")
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(new_text)
print(f"Written {len(new_text)} bytes")
