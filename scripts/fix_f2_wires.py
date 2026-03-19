#!/usr/bin/env python3
"""Fix F2 Phase 2: Break wire crossings between HOT_RAW and OUT_COLD nets.

For each channel, at x=280-285 area:
1. Delete vertical wire (280, ch_y-6) → (280, ch_y-4.81) 
   → this prevents the OUT_COLD vertical wire from crossing the HOT_RAW horizontal wire
2. Delete vertical wire (285, ch_y-6) → (285, ch_y-4.81)
   → this prevents the ESD/GND vertical chain from crossing the HOT_RAW horizontal wire
3. Remove orphaned OUT_COLD label at (280, ch_y-6)
4. Add new short wire stub at R88.pin1 position + OUT_COLD label
"""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()
orig_len = len(text)

ch_y = {1: 110, 2: 190, 3: 270, 4: 350, 5: 430, 6: 510}

# Helper: format coordinate for matching (integer or float)
def coord_str(v):
    """Return both possible forms: '104' and '104.0'"""
    if v == int(v):
        return [str(int(v)), f"{v:.1f}"]
    else:
        return [f"{v:.2f}", f"{v}"]

def remove_wire(text, x1, y1, x2, y2):
    """Remove a wire from the schematic text. Returns (new_text, success)."""
    # Try multiple coordinate formats
    patterns = []
    for sx1 in coord_str(x1):
        for sy1 in coord_str(y1):
            for sx2 in coord_str(x2):
                for sy2 in coord_str(y2):
                    # Wire format: (wire (pts (xy X1 Y1) (xy X2 Y2)) ...)
                    pat = rf'\(wire \(pts \(xy {re.escape(sx1)} {re.escape(sy1)}\) \(xy {re.escape(sx2)} {re.escape(sy2)}\)\)'
                    patterns.append(pat)
    
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            # Find the full wire block (may include UUID)
            start = m.start()
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '(': depth += 1
                elif text[i] == ')': depth -= 1
                if depth == 0: break
            wire_block = text[start:i+1]
            # Remove the block (and any preceding whitespace/newline)
            # Check for leading whitespace
            pre_start = start
            while pre_start > 0 and text[pre_start-1] in ' \t\n':
                if text[pre_start-1] == '\n':
                    pre_start -= 1
                    break
                pre_start -= 1
            text = text[:pre_start] + text[i+1:]
            return text, True
    
    return text, False

def remove_label(text, label_name, x, y):
    """Remove a label at specific position."""
    patterns = []
    for sx in coord_str(x):
        for sy in coord_str(y):
            pat = rf'\(label "{re.escape(label_name)}" \(at {re.escape(sx)} {re.escape(sy)}\b'
            patterns.append(pat)
    
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            start = m.start()
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '(': depth += 1
                elif text[i] == ')': depth -= 1
                if depth == 0: break
            label_block = text[start:i+1]
            pre_start = start
            while pre_start > 0 and text[pre_start-1] in ' \t\n':
                if text[pre_start-1] == '\n':
                    pre_start -= 1
                    break
                pre_start -= 1
            text = text[:pre_start] + text[i+1:]
            return text, True
    
    return text, False

# Process each channel
total_removed_wires = 0
total_removed_labels = 0

for ch, cy in ch_y.items():
    y_top = cy - 6       # 104, 184, ...
    y_pin1 = cy - 4.81   # 105.19, 185.19, ...
    
    label_name = f"CH{ch}_OUT_COLD"
    
    # 1. Remove vertical wire at x=280: (280, y_top) → (280, y_pin1)
    text, ok = remove_wire(text, 280, y_top, 280, y_pin1)
    if ok:
        total_removed_wires += 1
        print(f"  CH{ch}: Removed wire (280, {y_top}) → (280, {y_pin1})")
    else:
        print(f"  CH{ch}: WARNING - wire (280, {y_top}) → (280, {y_pin1}) NOT FOUND")
    
    # 2. Remove vertical wire at x=285: (285, y_top) → (285, y_pin1)
    text, ok = remove_wire(text, 285, y_top, 285, y_pin1)
    if ok:
        total_removed_wires += 1
        print(f"  CH{ch}: Removed wire (285, {y_top}) → (285, {y_pin1})")
    else:
        print(f"  CH{ch}: WARNING - wire (285, {y_top}) → (285, {y_pin1}) NOT FOUND")
    
    # 3. Remove orphaned OUT_COLD label at (280, y_top)
    text, ok = remove_label(text, label_name, 280, y_top)
    if ok:
        total_removed_labels += 1
        print(f"  CH{ch}: Removed label {label_name} at (280, {y_top})")
    else:
        print(f"  CH{ch}: WARNING - label {label_name} at (280, {y_top}) NOT FOUND")

print(f"\nRemoved {total_removed_wires} wires, {total_removed_labels} labels")

# 4. Add new wire stubs + OUT_COLD labels for R88 (Zobel cold) pins
# R88.pin1 at (280, ch_y-4.81) → add wire going LEFT to (279, ch_y-4.81)
# Then add OUT_COLD label at (279, ch_y-4.81) pointing LEFT (angle 180)

# Find insertion point: before the last closing paren of the root schematic
# Insert before the final ')' of (kicad_sch ...)
insert_pos = text.rfind(')')

new_elements = []
import uuid

for ch, cy in ch_y.items():
    y_pin1 = round(cy - 4.81, 2)
    label_name = f"CH{ch}_OUT_COLD"
    uid_wire = str(uuid.uuid4())
    uid_label = str(uuid.uuid4())
    
    # New wire: (280, y_pin1) → (279, y_pin1) 
    wire_str = f'(wire (pts (xy 280 {y_pin1}) (xy 279 {y_pin1})) (stroke (width 0) (type default)) (uuid "{uid_wire}"))'
    new_elements.append(wire_str)
    
    # New label at (279, y_pin1) pointing left (angle 180)
    label_str = f'(label "{label_name}" (at 279 {y_pin1} 180) (effects (font (size 1.27 1.27))) (uuid "{uid_label}"))'
    new_elements.append(label_str)
    
    print(f"  CH{ch}: Added wire (280, {y_pin1}) → (279, {y_pin1}) + label {label_name}")

# Insert all new elements
insert_text = '\n    ' + '\n    '.join(new_elements) + '\n  '
text = text[:insert_pos] + insert_text + text[insert_pos:]

print(f"\nAdded {len(new_elements)} new elements ({len(new_elements)//2} wires + {len(new_elements)//2} labels)")

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

# Count labels
out_cold = len(re.findall(r'\(label "CH\d_OUT_COLD"', text))
hot_raw = len(re.findall(r'\(label "CH\d_HOT_RAW"', text))
print(f"Label counts: OUT_COLD={out_cold}, HOT_RAW={hot_raw}")
