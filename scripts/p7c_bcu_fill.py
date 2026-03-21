#!/usr/bin/env python3
"""Fill ALL zones, but only inject B.Cu filled_polygon blocks."""
import sys, os, re
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster'
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
BCU_ZONE_UUID = 'da5ecc6e-fe84-4592-8349-d0063b3d2bc0'
TEMP = '/tmp/aurora-all-filled.kicad_pcb'

board = pcbnew.LoadBoard(PCB)
print("Zones:")
for z in board.Zones():
    print(f"  {z.GetLayerName()} net={z.GetNetname()} uuid={z.m_Uuid.AsString()}")

# Fill all zones
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(TEMP, board)
print(f"Filled + saved to {TEMP}")

# Now extract B.Cu zone fill data and inject
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
with open(PCB) as f:
    orig_text = f.read()

# Find B.Cu zone by UUID in filled text and extract filled_polygon blocks
bcu_pos = filled_text.find(f'(uuid "{BCU_ZONE_UUID}")')
if bcu_pos < 0:
    # Try alternative: find by layer name context
    print("Looking for B.Cu zone by layer...")
    bcu_pos = filled_text.find('"B.Cu"')
    # Find the enclosing zone
    zone_start = filled_text.rfind('(zone', 0, bcu_pos)
    # Verify it has the right net
    zone_block, zone_end = extract_balanced(filled_text, zone_start)
    print(f"Found zone: {zone_block[:200]}...")
else:
    zone_start = filled_text.rfind('(zone', 0, bcu_pos)
    zone_block, zone_end = extract_balanced(filled_text, zone_start)

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

print(f"B.Cu zone: {len(filled_polys)} filled_polygon blocks")

if len(filled_polys) == 0:
    # Maybe the UUID was changed by pcbnew. Search all zones for B.Cu
    print("\nSearching all zones in filled copy...")
    idx = 0
    while True:
        zs = filled_text.find('(zone', idx)
        if zs < 0:
            break
        zb, ze = extract_balanced(filled_text, zs)
        if zb and '"B.Cu"' in zb[:500]:
            print(f"Found B.Cu zone at pos {zs}")
            fp_idx = 0
            while True:
                fp_start = zb.find('(filled_polygon', fp_idx)
                if fp_start < 0:
                    break
                fp_block, fp_end = extract_balanced(zb, fp_start)
                if fp_block:
                    filled_polys.append(fp_block)
                fp_idx = fp_end if fp_block else fp_start + 1
            print(f"  Got {len(filled_polys)} filled_polygon blocks")
            break
        idx = ze if ze > zs else zs + 1

if len(filled_polys) == 0:
    print("No filled polygons found for B.Cu zone!")
    sys.exit(1)

# Inject into original — find B.Cu zone
bcu_orig_pos = orig_text.find(f'(uuid "{BCU_ZONE_UUID}")')
zone_orig_start = orig_text.rfind('(zone', 0, bcu_orig_pos)
zone_orig_block, zone_orig_end = extract_balanced(orig_text, zone_orig_start)

# Find the last (polygon or (fill block and insert after it
last_poly = zone_orig_block.rfind(')\n\t\t)')
if last_poly >= 0:
    insert_offset = last_poly + 1  # after the first )
else:
    insert_offset = len(zone_orig_block) - 2  # before last )

fp_text = '\n'
for poly in filled_polys:
    lines = poly.split('\n')
    indented = '\n'.join('\t\t' + line.lstrip() if line.strip() else '' for line in lines)
    fp_text += indented + '\n'

abs_insert = zone_orig_start + insert_offset
orig_text = orig_text[:abs_insert] + fp_text + orig_text[abs_insert:]

depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in orig_text)
assert depth == 0, f"Bracket imbalance: {depth}"
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(orig_text)
print(f"Written {len(orig_text):,} bytes")
