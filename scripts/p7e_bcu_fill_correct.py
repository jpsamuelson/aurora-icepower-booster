#!/usr/bin/env python3
"""
Correct B.Cu zone fill: fill via pcbnew, extract B.Cu filled_polygon,
inject it AFTER the (polygon ...) block in the B.Cu zone (not inside it).
"""
import sys, os, re
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster'
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
BCU_ZONE_UUID = 'da5ecc6e-fe84-4592-8349-d0063b3d2bc0'
TEMP = '/tmp/aurora-fill-correct.kicad_pcb'

# Step 1: Fill zones via pcbnew
board = pcbnew.LoadBoard(PCB)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(TEMP, board)
print(f"Zones filled. Temp: {TEMP}")

# Step 2: Extract filled_polygon from B.Cu zone
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

with open(TEMP) as f:
    filled_text = f.read()

# Find B.Cu zone by UUID
bcu_pos = filled_text.find(f'(uuid "{BCU_ZONE_UUID}")')
zone_start = filled_text.rfind('(zone', 0, bcu_pos)
zone_block, zone_end = extract_balanced(filled_text, zone_start)

# Extract filled_polygon blocks
filled_polys = []
fp_idx = 0
while True:
    fp_start = zone_block.find('(filled_polygon', fp_idx)
    if fp_start < 0:
        break
    fp_block, fp_end = extract_balanced(zone_block, fp_start)
    if fp_block:
        filled_polys.append(fp_block)
    fp_idx = fp_end if fp_block else fp_start + 1

print(f"Extracted {len(filled_polys)} filled_polygon blocks from B.Cu zone")

if not filled_polys:
    print("No fill data! Exiting.")
    sys.exit(1)

# Step 3: Inject into original PCB, AFTER the (polygon ...) block
with open(PCB) as f:
    orig_text = f.read()

# Find B.Cu zone by UUID in original
bcu_orig_pos = orig_text.find(f'(uuid "{BCU_ZONE_UUID}")')
zone_orig_start = orig_text.rfind('(zone', 0, bcu_orig_pos)
zone_orig_block, zone_orig_end = extract_balanced(orig_text, zone_orig_start)

# Find the (polygon ...) block within the zone and get its end position
poly_start = zone_orig_block.find('(polygon')
if poly_start < 0:
    print("No (polygon) found in B.Cu zone!")
    sys.exit(1)

poly_block, poly_end_local = extract_balanced(zone_orig_block, poly_start)
print(f"Found (polygon) block, local end at offset {poly_end_local}")

# The insertion point in the original text is AFTER the polygon block
# which is: zone_orig_start + poly_end_local
abs_insert = zone_orig_start + poly_end_local

# Build properly indented fill text
fp_text = '\n'
for poly in filled_polys:
    lines = poly.split('\n')
    indented_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped:
            indented_lines.append('\t\t' + stripped)
        else:
            indented_lines.append('')
    fp_text += '\n'.join(indented_lines) + '\n'

# Insert
orig_text = orig_text[:abs_insert] + fp_text + orig_text[abs_insert:]

# Verify brackets
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in orig_text)
if depth != 0:
    print(f"❌ Bracket imbalance: {depth}")
    # Find the error location
    d = 0
    for i, c in enumerate(orig_text):
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d < 0:
                print(f"Negative depth at pos {i}")
                print(f"Context: ...{orig_text[max(0,i-100):i+100]}...")
                break
    sys.exit(1)

print("Bracket balance OK")
with open(PCB, 'w') as f:
    f.write(orig_text)
print(f"Written {len(orig_text):,} bytes")
