#!/usr/bin/env python3
"""Fix F2: Rename misplaced OUT_COLD labels to HOT_RAW.
For each channel, 2 labels need renaming:
  - At x=42 (connects J3-J8.pin2 = XLR input hot)
  - At (280, ch_y-5) (connects R94/96/98/100/102/104.pin1 = EMI filter input)
The remaining 3 OUT_COLD labels per channel stay (output side: R58, J9, R88)."""
import re, sys

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()
orig_len = len(text)

# Channel Y-coordinates (XLR connector Y position)
ch_y = {1: 110, 2: 190, 3: 270, 4: 350, 5: 430, 6: 510}

# Labels to rename: (old_label, new_label, x, y)
renames = []
for ch, cy in ch_y.items():
    old = f"CH{ch}_OUT_COLD"
    new = f"CH{ch}_HOT_RAW"
    # Label at x=42 (J*.pin2 area)
    renames.append((old, new, 42, cy))
    # Label at x=280, y = ch_y - 5 (R94 EMI filter area)
    renames.append((old, new, 280, cy - 5))

print(f"Will rename {len(renames)} labels:")
for old, new, x, y in renames:
    print(f"  {old} at ({x}, {y}) -> {new}")

# Perform renames
renamed = 0
for old_name, new_name, target_x, target_y in renames:
    # Find the label in the text
    # Pattern: (label "CH*_OUT_COLD" (at X Y ...
    # We need to match the exact position
    pattern = rf'\(label "{re.escape(old_name)}" \(at {target_x}(?:\.0)? {target_y}(?:\.0)? '
    matches = list(re.finditer(pattern, text))
    
    if len(matches) == 0:
        # Try with more flexible coordinate matching (±0.5)
        print(f"  WARNING: No exact match for {old_name} at ({target_x}, {target_y})")
        # Try broader search
        for m in re.finditer(rf'\(label "{re.escape(old_name)}" \(at ([\d.]+) ([\d.]+)', text):
            lx, ly = float(m.group(1)), float(m.group(2))
            if abs(lx - target_x) < 1 and abs(ly - target_y) < 1:
                print(f"    Found nearby at ({lx}, {ly})")
                # Replace
                old_str = f'(label "{old_name}"'
                new_str = f'(label "{new_name}"'
                pos = m.start()
                text = text[:pos] + text[pos:].replace(old_str, new_str, 1)
                renamed += 1
                break
        continue
    
    if len(matches) > 1:
        print(f"  WARNING: Multiple matches for {old_name} at ({target_x}, {target_y}): {len(matches)}")
    
    # Replace the first match
    m = matches[0]
    pos = m.start()
    old_str = f'(label "{old_name}"'
    new_str = f'(label "{new_name}"'
    text = text[:pos] + text[pos:].replace(old_str, new_str, 1)
    renamed += 1

print(f"\nRenamed {renamed}/{len(renames)} labels")

# Verify bracket balance
depth = 0
for ch in text:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"Bracket balance: OK")

# Write back
with open(SCH, 'w') as f:
    f.write(text)
print(f"Schematic written: {len(text)} chars (was {orig_len})")

# Count remaining OUT_COLD and new HOT_RAW labels
out_cold = len(re.findall(r'\(label "CH\d_OUT_COLD"', text))
hot_raw = len(re.findall(r'\(label "CH\d_HOT_RAW"', text))
print(f"\nLabel counts: OUT_COLD={out_cold}, HOT_RAW={hot_raw}")
