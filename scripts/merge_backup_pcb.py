#!/usr/bin/env python3
"""Merge user's backup PCB changes with J2/J15 modifications.

Strategy: Start from user's backup PCB (has 3D model + silkscreen fixes),
then apply the J2/J15 changes (remove old J2, add new J2+J15, add traces).
"""
import re
import uuid
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_PATH = os.path.join(BASE, "aurora-dsp-icepower-booster.kicad_pcb")
BACKUP_PCB = "/tmp/kicad-backup/aurora-dsp-icepower-booster.kicad_pcb"

NET_REMOTE_IN = 130
NET_GND = 134

# Old Lumberg pad positions (for stale trace removal)
OLD_PAD_POS = [
    (26.42, 2.58), (34.52, 2.58),
    (26.42, 11.43), (34.52, 11.43),
]


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


def pad_net(pad_nets, num):
    if num in pad_nets:
        nid, nn = pad_nets[num]
        return f'\t\t\t(net {nid} "{nn}")\n'
    return ''


def make_footprint(ref, val, px, py, pad_nets):
    pn = pad_net
    return f"""\t(footprint "aurora-dsp-icepower-booster:AUDIO-SMD_KH-PJ-320EA-5P-SMT"
\t\t(layer "F.Cu")
\t\t(uuid "{uu()}")
\t\t(at {px} {py})
\t\t(descr "KH-PJ-320EA-5P-SMT 3.5mm Stereo Audio Jack SMD 5-Pin, Kinghelm, LCSC C5123132")
\t\t(tags "audio jack 3.5mm stereo SMD kinghelm")
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -7.75 0)
\t\t\t(unlocked yes)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{uu()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "{val}"
\t\t\t(at 0 7.75 0)
\t\t\t(unlocked yes)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{uu()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" "https://www.lcsc.com/datasheet/C5123132.pdf"
\t\t\t(at 0 0 0)
\t\t\t(unlocked yes)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{uu()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Description" "3.5mm Stereo Audio Jack SMD 5-Pin"
\t\t\t(at 0 0 0)
\t\t\t(unlocked yes)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{uu()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "LCSC" "C5123132"
\t\t\t(at 0 0 0)
\t\t\t(unlocked yes)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{uu()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(attr smd)
\t\t(fp_line (start -6.36 -3.94) (end -6.36 3.05) (stroke (width 0.25) (type solid)) (layer "F.Fab") (uuid "{uu()}"))
\t\t(fp_line (start 4.90 -0.41) (end 4.90 -2.04) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start 3.17 -4.00) (end 3.27 -4.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start 4.90 0.41) (end 4.90 3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start 4.90 3.00) (end 3.63 3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -9.15 -3.00) (end -6.35 -3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -9.15 3.00) (end -6.35 3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -9.15 3.00) (end -9.15 -3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -0.27 3.00) (end 1.87 3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -3.27 3.00) (end -2.03 3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -6.35 3.00) (end -5.03 3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -3.27 -4.00) (end 3.17 -4.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -6.35 -4.00) (end -5.03 -4.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_line (start -6.35 -4.00) (end -6.35 3.00) (stroke (width 0.25) (type solid)) (layer "F.SilkS") (uuid "{uu()}"))
\t\t(fp_text user "${{REFERENCE}}"
\t\t\t(at 0 0 0)
\t\t\t(unlocked yes)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{uu()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pad "1" smd rect
\t\t\t(at 4.15 -3.75)
\t\t\t(size 1.30 3.00)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask")
{pn(pad_nets, "1")}\t\t\t(uuid "{uu()}")
\t\t)
\t\t(pad "2" smd rect
\t\t\t(at -4.15 3.75)
\t\t\t(size 1.30 3.00)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask")
{pn(pad_nets, "2")}\t\t\t(uuid "{uu()}")
\t\t)
\t\t(pad "3" smd rect
\t\t\t(at -1.15 3.75)
\t\t\t(size 1.30 3.00)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask")
{pn(pad_nets, "3")}\t\t\t(uuid "{uu()}")
\t\t)
\t\t(pad "4" smd rect
\t\t\t(at 2.75 3.75)
\t\t\t(size 1.30 3.00)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask")
{pn(pad_nets, "4")}\t\t\t(uuid "{uu()}")
\t\t)
\t\t(pad "5" smd rect
\t\t\t(at -4.15 -3.75)
\t\t\t(size 1.30 3.00)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask")
{pn(pad_nets, "5")}\t\t\t(uuid "{uu()}")
\t\t)
\t\t(pad "" np_thru_hole circle
\t\t\t(at -2.65 0)
\t\t\t(size 1.50 1.50)
\t\t\t(drill 1.50)
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(uuid "{uu()}")
\t\t)
\t\t(pad "" np_thru_hole circle
\t\t\t(at 4.05 0)
\t\t\t(size 1.50 1.50)
\t\t\t(drill 1.50)
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(uuid "{uu()}")
\t\t)
\t\t(fp_circle (center 4.85 -5.00) (end 4.88 -5.00) (stroke (width 0.06) (type solid)) (layer "F.Fab") (uuid "{uu()}"))
\t\t(fp_circle (center 4.05 0) (end 4.30 0) (stroke (width 0.50) (type solid)) (layer "Cmts.User") (uuid "{uu()}"))
\t\t(fp_circle (center -2.65 0) (end -2.40 0) (stroke (width 0.50) (type solid)) (layer "Cmts.User") (uuid "{uu()}"))
\t\t(embedded_fonts no)
\t\t(model "${{KIPRJMOD}}/footprints.pretty/3dshapes/AUDIO-SMD_KH-PJ-320EA-5P-SMT.step"
\t\t\t(offset
\t\t\t\t(xyz -0.67 0 2.7)
\t\t\t)
\t\t\t(scale
\t\t\t\t(xyz 1 1 1)
\t\t\t)
\t\t\t(rotate
\t\t\t\t(xyz -0 -0 -0)
\t\t\t)
\t\t)
\t)
"""


# ---- Main ----
print(f"=== Reading BACKUP PCB (user's version with 3D model + silkscreen fixes) ===")
with open(BACKUP_PCB, 'r') as f:
    lines = f.readlines()
print(f"  {len(lines)} lines, balance={balance(''.join(lines))}")

# Step 1: Remove old J2 (Lumberg)
print("\n--- Step 1: Remove old J2 Lumberg ---")
j2_start = None
for i, l in enumerate(lines):
    if '"J2"' in l and 'Reference' in l:
        for j in range(i, max(i - 20, 0), -1):
            if lines[j].strip().startswith('(footprint'):
                j2_start = j
                break
        break

if j2_start is None:
    print("  ERROR: J2 not found!")
    sys.exit(1)

j2_end = find_block_end(lines, j2_start)
removed = lines[j2_start:j2_end + 1]
print(f"  Lines {j2_start+1}-{j2_end+1} ({len(removed)} lines, balance={balance(''.join(removed))})")
del lines[j2_start:j2_end + 1]
print(f"  After removal: balance={balance(''.join(lines))}")

# Step 2: Remove stale traces at old J2 pad positions
print("\n--- Step 2: Remove stale traces ---")
count = 0
i = 0
while i < len(lines):
    s = lines[i].strip()
    if s.startswith('(segment'):
        end = find_block_end(lines, i)
        block = ''.join(lines[i:end + 1])

        sm = re.search(r'\(start\s+([\d.]+)\s+([\d.]+)\)', block)
        em = re.search(r'\(end\s+([\d.]+)\s+([\d.]+)\)', block)

        rm = False
        for m in [sm, em]:
            if m:
                x, y = float(m.group(1)), float(m.group(2))
                for px, py in OLD_PAD_POS:
                    if abs(x - px) < 0.02 and abs(y - py) < 0.02:
                        rm = True
                        break
            if rm:
                break

        if rm:
            del lines[i:end + 1]
            count += 1
            continue
    i += 1

print(f"  Removed {count} segments, balance={balance(''.join(lines))}")

# Step 3: Insert new footprints
print("\n--- Step 3: Insert J2 + J15 ---")

j2_nets = {"1": (NET_REMOTE_IN, "/REMOTE_IN"), "4": (NET_GND, "GND")}
j15_nets = {"1": (NET_REMOTE_IN, "/REMOTE_IN"), "4": (NET_GND, "GND")}

j2_text = make_footprint("J2", "REMOTE 3.5mm IN", 30.47, 5.08, j2_nets)
j15_text = make_footprint("J15", "REMOTE 3.5mm OUT", 19, 5.08, j15_nets)

print(f"  J2: balance={balance(j2_text)}")
print(f"  J15: balance={balance(j15_text)}")

both = j2_text + "\n" + j15_text + "\n"
fp_lines = both.splitlines(keepends=True)
fp_lines = [l if l.endswith('\n') else l + '\n' for l in fp_lines]

# Insert before first (segment or (via or (zone
ins = None
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith('(segment') or s.startswith('(via') or s.startswith('(zone'):
        ins = i
        break

if ins is None:
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == ')':
            ins = i
            break

for j, fl in enumerate(fp_lines):
    lines.insert(ins + j, fl)

print(f"  Inserted {len(fp_lines)} lines at {ins}")

# Step 4: Add REMOTE_IN traces
print("\n--- Step 4: Add REMOTE_IN traces ---")

new_segments = [
    # J2 Pad1 (34.62, 1.33) → junction (31.7356, 2.58)
    f'\t(segment\n\t\t(start 34.62 1.33)\n\t\t(end 31.7356 1.33)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 31.7356 1.33)\n\t\t(end 31.7356 2.58)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    # J15 Pad1 (23.15, 1.33) → junction via bypass around J2 Pad5 at (26.32, 1.33)
    f'\t(segment\n\t\t(start 23.15 1.33)\n\t\t(end 25.1 1.33)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 25.1 1.33)\n\t\t(end 25.1 3.5)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 25.1 3.5)\n\t\t(end 28 3.5)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 28 3.5)\n\t\t(end 28 2.58)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
    f'\t(segment\n\t\t(start 28 2.58)\n\t\t(end 31.7356 2.58)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net {NET_REMOTE_IN})\n\t\t(uuid "{uu()}")\n\t)\n',
]

# Find last segment to insert after
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

seg_insert = last_seg_close + 1
for j, seg in enumerate(new_segments):
    lines.insert(seg_insert + j, seg)

print(f"  Inserted {len(new_segments)} segments at line {seg_insert}")

# Step 5: Validate
print("\n--- Step 5: Validate ---")
final = ''.join(lines)
b = balance(final)
print(f"  Final balance: {b}")

if b != 0:
    print(f"  ERROR: imbalance {b}")
    sys.exit(1)

for chk, name in [
    ('"REMOTE 3.5mm IN"', "J2 value"),
    ('"REMOTE 3.5mm OUT"', "J15 value"),
    ('KH-PJ-320EA-5P-SMT', "footprint"),
    (f'(net {NET_REMOTE_IN} "/REMOTE_IN")', "REMOTE_IN net"),
    (f'(net {NET_GND} "GND")', "GND net"),
]:
    print(f"  {'OK' if chk in final else 'MISSING'} {name}")

# Verify user's changes survived
user_checks = [
    ('NC3MBH--3DModel-STEP-510211.STEP', "NC3MBH custom 3D"),
    ('NC3FBH2_Horizontal.step', "NC3FBH2 custom 3D"),
    ('TEL_5-2422.step', "TEL5 custom 3D"),
    ('15.52', "XLR silkscreen extension"),
]
print("\n  User changes preserved:")
for chk, name in user_checks:
    count = final.count(chk)
    print(f"  {'OK' if count > 0 else 'MISSING'} {name} ({count}x)")

print(f"\n--- Writing to {PCB_PATH} ---")
with open(PCB_PATH, 'w') as f:
    f.write(final)
print(f"  {len(lines)} lines. Done!")
