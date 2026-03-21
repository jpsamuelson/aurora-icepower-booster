#!/usr/bin/env python3
"""
Robust zone fill: extract filled_polygon blocks from pcbnew output
and inject them into the correct zone blocks in the original PCB.
"""
import sys, os, re
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster'
ORIG = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP = '/tmp/aurora-zones-filled2.kicad_pcb'

# Step 1: Fill zones using pcbnew
board = pcbnew.LoadBoard(ORIG)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(TEMP, board)
print(f"Zone fill done, saved temp: {TEMP}")

# Step 2: Extract filled_polygon blocks per zone UUID from filled copy
with open(TEMP) as f:
    filled_text = f.read()

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

def find_zone_filled_polys(text):
    """For each zone (by UUID), extract all filled_polygon blocks."""
    zones = {}
    idx = 0
    while True:
        # Find zone start
        zone_start = text.find('(zone', idx)
        if zone_start < 0:
            break
        zone_block, zone_end = extract_balanced(text, zone_start)
        if not zone_block:
            idx = zone_start + 1
            continue
        
        # Get UUID
        uuid_m = re.search(r'\(uuid "([^"]+)"\)', zone_block)
        if not uuid_m:
            idx = zone_end
            continue
        uid = uuid_m.group(1)
        
        # Extract all filled_polygon blocks within this zone
        filled = []
        fp_idx = 0
        while True:
            fp_start = zone_block.find('(filled_polygon', fp_idx)
            if fp_start < 0:
                break
            fp_block, fp_end = extract_balanced(zone_block, fp_start)
            if fp_block:
                filled.append(fp_block)
            fp_idx = fp_end if fp_block else fp_start + 1
        
        zones[uid] = filled
        idx = zone_end
    
    return zones

filled_zones = find_zone_filled_polys(filled_text)
print(f"\nFilled zones found: {len(filled_zones)}")
for uid, polys in filled_zones.items():
    print(f"  Zone {uid[:8]}...: {len(polys)} filled_polygon blocks")

# Step 3: In the original, find each zone by UUID and inject filled_polygons
with open(ORIG) as f:
    orig_text = f.read()

# First, remove any existing filled_polygon blocks
def remove_filled_polys(text):
    """Remove all filled_polygon balanced blocks."""
    result = []
    i = 0
    removed = 0
    while i < len(text):
        if text[i:i+16] == '(filled_polygon':
            block, end = extract_balanced(text, i)
            if block:
                # Skip the block and any trailing whitespace/newline
                j = end
                while j < len(text) and text[j] in ' \t\n':
                    j += 1
                i = j
                removed += 1
                continue
        result.append(text[i])
        i += 1
    return ''.join(result), removed

orig_text, removed = remove_filled_polys(orig_text)
print(f"\nRemoved {removed} existing filled_polygon blocks from original")

# Now inject new filled_polygon blocks into each zone
for uid, polys in filled_zones.items():
    if not polys:
        continue
    
    # Find the zone with this UUID in the original
    uid_pos = orig_text.find(f'(uuid "{uid}")')
    if uid_pos < 0:
        print(f"  Zone {uid[:8]}... NOT FOUND in original!")
        continue
    
    # Find the zone's closing paren
    # Go backwards to find the zone start
    zone_start = orig_text.rfind('(zone', 0, uid_pos)
    if zone_start < 0:
        print(f"  Zone {uid[:8]}... zone start not found!")
        continue
    
    zone_block, zone_end = extract_balanced(orig_text, zone_start)
    if not zone_block:
        print(f"  Zone {uid[:8]}... balanced extraction failed!")
        continue
    
    # Insert filled_polygon blocks before the zone's closing paren
    # The zone ends with \t\t)\n — we insert before the last )
    insert_pos = zone_end - 1  # position of the closing )
    # Back up past whitespace
    while insert_pos > zone_start and orig_text[insert_pos-1] in ' \t\n':
        insert_pos -= 1
    insert_pos += 1  # move past the last newline/space
    
    # Build filled polygon text with proper indentation
    fp_text = ''
    for poly in polys:
        # Reindent to match zone context (2 tabs)
        lines = poly.split('\n')
        indented = '\n'.join('\t\t' + line.lstrip() if line.strip() else '' for line in lines)
        fp_text += indented + '\n'
    
    orig_text = orig_text[:insert_pos] + fp_text + orig_text[insert_pos:]
    print(f"  Zone {uid[:8]}...: injected {len(polys)} filled_polygon blocks")

# Verify brackets
depth = 0
for ch in orig_text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
if depth != 0:
    print(f"❌ Bracket imbalance: {depth}")
    sys.exit(1)

print("Bracket balance OK")
with open(ORIG, 'w') as f:
    f.write(orig_text)
print(f"Written {len(orig_text):,} bytes")
