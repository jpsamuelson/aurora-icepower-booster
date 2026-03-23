#!/usr/bin/env python3
"""Add REMOTE_IN traces connecting J2 and J15 pads to existing network.

Uses readlines/writelines for safe line-based manipulation.
"""
import uuid
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_PATH = os.path.join(BASE, "aurora-dsp-icepower-booster.kicad_pcb")

NET_REMOTE_IN = 130

def uu():
    return str(uuid.uuid4())

print(f"Reading {PCB_PATH}")
with open(PCB_PATH, 'r') as f:
    lines = f.readlines()
print(f"  {len(lines)} lines")

# Route J2 Pad1 (34.62, 1.33) → junction (31.7356, 2.58)
# These 2 segments connect J2 to the existing REMOTE_IN protection network
#
# Route J15 Pad1 (23.15, 1.33) → junction (31.7356, 2.58) avoiding J2 Pad5 at (26.32, 1.33)
# J2 Pad5 extends X:25.67-26.97, Y:-0.17-2.83 → route above at Y=3.5
# Path: (23.15,1.33)→(25.1,1.33)→(25.1,3.5)→(28,3.5)→(28,2.58)→(31.7356,2.58)
new_segments = [
    # J2 → junction: horizontal then vertical
    f'\t(segment\n\t\t(start 34.62 1.33)\n\t\t(end 31.7356 1.33)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 31.7356 1.33)\n\t\t(end 31.7356 2.58)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    # J15 → junction: route above J2 Pad5
    f'\t(segment\n\t\t(start 23.15 1.33)\n\t\t(end 25.1 1.33)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 25.1 1.33)\n\t\t(end 25.1 3.5)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 25.1 3.5)\n\t\t(end 28 3.5)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 28 3.5)\n\t\t(end 28 2.58)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 28 2.58)\n\t\t(end 31.7356 2.58)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
]

# Find the last complete segment block to insert after
# Look for the last line that closes a segment with ")"
last_segment_close = None
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == ')' and i > 0:
        # Check if this closes a segment
        for j in range(i - 1, max(i - 10, 0), -1):
            if lines[j].strip().startswith('(segment'):
                last_segment_close = i
                break
            elif lines[j].strip().startswith('(via') or lines[j].strip().startswith('(zone'):
                break
        if last_segment_close is not None:
            break

if last_segment_close is None:
    print("  ERROR: Could not find segment section!")
    sys.exit(1)

# Insert after the last segment closing
insert_at = last_segment_close + 1
for j, seg in enumerate(new_segments):
    lines.insert(insert_at + j, seg)

print(f"  Inserted {len(new_segments)} segments at line {insert_at + 1}")

# Balance check
d = 0
final = ''.join(lines)
for c in final:
    if c == '(':
        d += 1
    elif c == ')':
        d -= 1
print(f"  Balance: {d}")

if d != 0:
    print("  ERROR: Bracket imbalance!")
    sys.exit(1)

# Verify kicad-cli can load
with open(PCB_PATH, 'w') as f:
    f.write(final)
print(f"  Written {len(lines)} lines. Done!")
