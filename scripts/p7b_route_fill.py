#!/usr/bin/env python3
"""
Add CH6_GAIN_OUT manual B.Cu detour + B.Cu-only zone fill.
Route goes south around V- and BUF_DRIVE on B.Cu at x=123.
Then fill only B.Cu GND zone (F.Cu zone fill causes DRC errors).
"""
import sys, os, re, uuid as uuid_mod

sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster'
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
BCU_ZONE_UUID = 'da5ecc6e-fe84-4592-8349-d0063b3d2bc0'

with open(PCB) as f:
    text = f.read()

# ── Add manual route for CH6_GAIN_OUT ──
net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
NET = int(net_m.group(1))

VIA_SIZE = 0.6
VIA_DRILL = 0.3
TRACE_W = 0.5

def gen_seg(start, end, width, layer, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(segment (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) (width {width}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def gen_via(pos, size, drill, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(via (at {pos[0]} {pos[1]}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

# B.Cu detour: existing B.Cu endpoint → south → east → north → via → F.Cu stub
start = (93.4766, 185.4828)  # existing B.Cu endpoint
wp1 = (93.48, 193)            # south (below all obstacles)
wp2 = (123, 193)              # east (past BUF_DRIVE at x=120.8)
wp3 = (123, 179)              # north (to R69 latitude)
via_pt = (123, 179)           # via to F.Cu
end_pt = (112, 178.8)         # R69 pad 2

routing = ''
routing += gen_seg(start, wp1, TRACE_W, 'B.Cu', NET)
routing += gen_seg(wp1, wp2, TRACE_W, 'B.Cu', NET)
routing += gen_seg(wp2, wp3, TRACE_W, 'B.Cu', NET)
routing += gen_via(via_pt, VIA_SIZE, VIA_DRILL, NET)
routing += gen_seg(via_pt, end_pt, TRACE_W, 'F.Cu', NET)

# Insert before zones
last_pos = 0
for m in re.finditer(r'\t\((?:segment|via)\s', text):
    match_start = m.start()
    depth = 0
    i = match_start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                last_pos = i + 1
                break
        i += 1

insert_pos = last_pos
while insert_pos < len(text) and text[insert_pos] in ' \t\n':
    insert_pos += 1

text = text[:insert_pos] + '\n' + routing + text[insert_pos:]
print(f"Added manual route: B.Cu {start}→{wp1}→{wp2}→{wp3}→Via→F.Cu→{end_pt}")

# Save before zone fill
with open(PCB, 'w') as f:
    f.write(text)

# ── B.Cu-only zone fill ──
print("\nRunning B.Cu-only zone fill...")
board = pcbnew.LoadBoard(PCB)
filler = pcbnew.ZONE_FILLER(board)

# Only fill B.Cu zone
for zone in board.Zones():
    if zone.GetLayerName() == 'B.Cu':
        zone_list = pcbnew.ZONES()
        zone_list.append(zone)
        filler.Fill(zone_list)
        print(f"  B.Cu zone filled")
    else:
        print(f"  {zone.GetLayerName()} zone SKIPPED")

TEMP = '/tmp/aurora-bcu-filled.kicad_pcb'
pcbnew.SaveBoard(TEMP, board)

# Extract filled_polygon from B.Cu zone only
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

# Find B.Cu zone in filled copy and extract filled_polygon blocks
bcu_pos = filled_text.find(f'(uuid "{BCU_ZONE_UUID}")')
if bcu_pos < 0:
    print("B.Cu zone not found in filled copy!")
    sys.exit(1)

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

print(f"  Extracted {len(filled_polys)} filled_polygon blocks from B.Cu zone")

# Inject into original PCB 
with open(PCB) as f:
    text = f.read()

# Find B.Cu zone in original
bcu_orig_pos = text.find(f'(uuid "{BCU_ZONE_UUID}")')
zone_orig_start = text.rfind('(zone', 0, bcu_orig_pos)
zone_orig_block, zone_orig_end = extract_balanced(text, zone_orig_start)

# Insert filled_polygon blocks before the zone's last closing paren
# Find the last (polygon ...) block end, insert after it
last_poly = zone_orig_block.rfind('(polygon')
if last_poly >= 0:
    poly_block, poly_end = extract_balanced(zone_orig_block, last_poly)
    insert_offset = poly_end
else:
    insert_offset = len(zone_orig_block) - 1

# Build the fill text
fp_text = '\n'
for poly in filled_polys:
    lines = poly.split('\n')
    indented = '\n'.join('\t\t' + line.lstrip() if line.strip() else '' for line in lines)
    fp_text += indented + '\n'

# Insert in the original text
abs_insert = zone_orig_start + insert_offset
text = text[:abs_insert] + fp_text + text[abs_insert:]

# Verify brackets
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
if depth != 0:
    print(f"❌ Bracket imbalance: {depth}")
    sys.exit(1)

print("Bracket balance OK")
with open(PCB, 'w') as f:
    f.write(text)
print(f"Written {len(text):,} bytes")
