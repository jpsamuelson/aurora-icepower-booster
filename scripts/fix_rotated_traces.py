#!/usr/bin/env python3
"""Fix REMOTE_IN traces after J2/J15 rotation to -90°.

1. Remove old traces (7 segments I added for non-rotated positions)
2. Remove dangling vertical segment that no longer connects to anything
3. Add new traces from rotated pad positions to existing junction
"""
import re
import uuid
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_PATH = os.path.join(BASE, "aurora-dsp-icepower-booster.kicad_pcb")

NET_REMOTE_IN = 130

def uu():
    return str(uuid.uuid4())

def balance(text):
    d = 0
    for c in text:
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
    return d

def find_block_end(lines, start):
    d = 0
    s = False
    for i in range(start, len(lines)):
        for c in lines[i]:
            if c == '(':
                d += 1
                s = True
            elif c == ')':
                d -= 1
        if s and d <= 0:
            return i
    return len(lines) - 1

# Segments to remove: my old 7 traces + dangling vertical
# Format: (start_x, start_y, end_x, end_y) - match either direction
OLD_SEGMENTS = [
    # My 7 added segments (old non-rotated routing)
    (34.62, 1.33, 31.7356, 1.33),
    (31.7356, 1.33, 31.7356, 2.58),
    (23.15, 1.33, 25.1, 1.33),
    (25.1, 1.33, 25.1, 3.5),
    (25.1, 3.5, 28, 3.5),
    (28, 3.5, 28, 2.58),
    (28, 2.58, 31.7356, 2.58),
    # Dangling vertical (bottom half no longer connects to anything)
    (31.7356, 2.58, 31.7356, 10.4436),
]

# New pad positions (after -90° rotation)
# J2 Pad1: (36.262, 10.339)
# J15 Pad1: (20.006, 10.246)
# Existing junction: (31.7356, 10.4436)
#
# Routing plan (orthogonal, clean):
# J2: (36.262, 10.339) → (36.262, 10.4436) → (31.7356, 10.4436)
# J15: (20.006, 10.246) → (20.006, 10.4436) → (31.7356, 10.4436)

NEW_SEGMENTS = [
    # J2 Pad1 → junction
    (36.262, 10.339, 36.262, 10.4436),
    (36.262, 10.4436, 31.7356, 10.4436),
    # J15 Pad1 → junction
    (20.006, 10.246, 20.006, 10.4436),
    (20.006, 10.4436, 31.7356, 10.4436),
]


def seg_matches(block, sx, sy, ex, ey, tol=0.02):
    """Check if a segment block matches the given start/end (either direction)."""
    sm = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', block)
    em = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', block)
    if not sm or not em:
        return False
    bsx, bsy = float(sm.group(1)), float(sm.group(2))
    bex, bey = float(em.group(1)), float(em.group(2))
    # Check forward match
    if (abs(bsx-sx) < tol and abs(bsy-sy) < tol and
        abs(bex-ex) < tol and abs(bey-ey) < tol):
        return True
    # Check reverse match
    if (abs(bsx-ex) < tol and abs(bsy-ey) < tol and
        abs(bex-sx) < tol and abs(bey-sy) < tol):
        return True
    return False


# ---- Main ----
print(f"Reading {PCB_PATH}")
with open(PCB_PATH, 'r') as f:
    lines = f.readlines()
print(f"  {len(lines)} lines, balance={balance(''.join(lines))}")

# Step 1: Remove old segments
print("\n--- Step 1: Remove old segments ---")
removed = 0
i = 0
while i < len(lines):
    s = lines[i].strip()
    if s.startswith('(segment'):
        end = find_block_end(lines, i)
        block = ''.join(lines[i:end+1])

        # Check if it's net 130
        if f'(net {NET_REMOTE_IN})' not in block:
            i += 1
            continue

        for sx, sy, ex, ey in OLD_SEGMENTS:
            if seg_matches(block, sx, sy, ex, ey):
                del lines[i:end+1]
                removed += 1
                break
        else:
            i += 1
            continue
        continue  # Don't increment i after deletion
    i += 1

print(f"  Removed {removed}/{len(OLD_SEGMENTS)} segments")
print(f"  Balance after removal: {balance(''.join(lines))}")

# Step 2: Add new segments
print("\n--- Step 2: Add new traces ---")
new_seg_text = ""
for sx, sy, ex, ey in NEW_SEGMENTS:
    new_seg_text += f'\t(segment\n\t\t(start {sx} {sy})\n\t\t(end {ex} {ey})\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n'

seg_lines = new_seg_text.splitlines(keepends=True)
seg_lines = [l if l.endswith('\n') else l + '\n' for l in seg_lines]

# Find insertion point: after last segment block
last_seg_close = None
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == ')' and i > 0:
        for j in range(i - 1, max(i - 10, 0), -1):
            if lines[j].strip().startswith('(segment'):
                last_seg_close = i
                break
            elif lines[j].strip().startswith('(via') or lines[j].strip().startswith('(zone'):
                break
        if last_seg_close is not None:
            break

if last_seg_close is None:
    print("  ERROR: No segments found!")
    sys.exit(1)

ins = last_seg_close + 1
for j, sl in enumerate(seg_lines):
    lines.insert(ins + j, sl)

print(f"  Inserted {len(NEW_SEGMENTS)} new segments at line {ins}")

# Step 3: Validate
print("\n--- Step 3: Validate ---")
final = ''.join(lines)
b = balance(final)
print(f"  Balance: {b}")

if b != 0:
    print(f"  ERROR: imbalance {b}")
    sys.exit(1)

# Verify new traces exist
for sx, sy, ex, ey in NEW_SEGMENTS:
    found = f'(start {sx} {sy})' in final and f'(end {ex} {ey})' in final
    print(f"  {'OK' if found else 'MISSING'} ({sx},{sy}) → ({ex},{ey})")

print(f"\n--- Writing ---")
with open(PCB_PATH, 'w') as f:
    f.write(final)
print(f"  {len(lines)} lines. Done!")
