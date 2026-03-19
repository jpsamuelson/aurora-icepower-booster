#!/usr/bin/env python3
"""
Repair: Move new wires from outside to inside kicad_sch scope.
The fix_u1_wires.py script's string replacements (5 wire endpoint changes) worked,
but the 4 new wires + 1 junction were inserted OUTSIDE the (kicad_sch ...) block.
Fix: Remove them from outside, re-insert before the (kicad_sch) closing bracket.
"""

import re, subprocess

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, 'r') as f:
    content = f.read()

original_len = len(content)

# The new wires/junction to move (they're at the end, outside kicad_sch scope)
elements_to_move = [
    '(wire (pts (xy 90.16 37.46) (xy 90.16 40)) (stroke (width 0) (type default))',
    '(wire (pts (xy 90.16 42.54) (xy 90.16 40)) (stroke (width 0) (type default))',
    '(wire (pts (xy 69.84 34.92) (xy 69.84 37.46)) (stroke (width 0) (type default))',
    '(wire (pts (xy 69.84 40) (xy 69.84 42.54)) (stroke (width 0) (type default))',
    '(junction (at 90.16 40) (diameter 0) (color 0 0 0 0)',
]

# Find and extract the 5 elements (including full line with UUID)
extracted_lines = []
for elem in elements_to_move:
    # Find the full line containing this element
    idx = content.find(elem)
    assert idx >= 0, f"Element not found: {elem[:50]}"
    # Find the line boundaries
    line_start = content.rfind('\n', 0, idx)
    if line_start < 0:
        line_start = 0
    else:
        line_start += 1  # skip the newline
    line_end = content.find('\n', idx)
    if line_end < 0:
        line_end = len(content)
    full_line = content[line_start:line_end]
    extracted_lines.append(full_line.strip())
    # Remove this line (including leading newline)
    remove_start = line_start - 1 if line_start > 0 else line_start  # include preceding newline
    content = content[:remove_start] + content[line_end:]
    print(f"Removed: {elem[:60]}...")

print(f"\nAfter removal: {len(content)} chars (was {original_len})")

# Now find the correct insertion point: just before the closing ) of (kicad_sch)
# The kicad_sch closing is the LAST ) that brings bracket depth to 0
# We'll find it by scanning for the position where adding one more ) would close kicad_sch
depth = 0
kicad_close_pos = -1
for i, ch in enumerate(content):
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
        if depth == 0:
            kicad_close_pos = i
            break

# Nope, that finds the FIRST depth-0 close. We need the LAST one.
# Actually kicad_sch opens at the very beginning, so the first depth-0 close IS the end.
# But some files have the header differently. Let me find where (kicad_sch opens.
kicad_start = content.find('(kicad_sch')
assert kicad_start >= 0

# Track depth from kicad_sch start
depth = 0
kicad_close_pos = -1
for i in range(kicad_start, len(content)):
    if content[i] == '(':
        depth += 1
    elif content[i] == ')':
        depth -= 1
        if depth == 0:
            kicad_close_pos = i
            break

assert kicad_close_pos > 0, "Could not find kicad_sch closing bracket"
print(f"(kicad_sch) closing bracket at position {kicad_close_pos}")
print(f"  Context: ...{repr(content[kicad_close_pos-20:kicad_close_pos+5])}")

# Insert the elements just before the closing bracket
# Find the newline before the closing bracket for clean insertion
insert_before = content.rfind('\n', 0, kicad_close_pos)
indent = '  '  # match existing indentation for top-level elements  
new_text = '\n' + '\n'.join(f'{indent}{line}' for line in extracted_lines)

content = content[:insert_before] + new_text + content[insert_before:]

# Verify bracket balance
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"\n✅ Brackets balanced")
print(f"   Final size: {len(content)} (was {original_len})")

# Verify the wires are now at depth 1 (inside kicad_sch)
wire_check = content.find('(wire (pts (xy 90.16 37.46)')
depth = 0
for ch in content[:wire_check]:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"   Wire depth after fix: {depth} (should be 1)")

with open(SCH, 'w') as f:
    f.write(content)
print("✅ Schematic saved")

# Verify netlist export
r = subprocess.run([
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "sch", "export", "netlist", "--output", "/tmp/u1_repair.net", SCH
], capture_output=True, text=True, timeout=30)
print(f"   Netlist: {'OK' if r.returncode == 0 else 'FAILED'} (rc={r.returncode})")
if r.returncode != 0:
    print(f"   stderr: {r.stderr[:500]}")
