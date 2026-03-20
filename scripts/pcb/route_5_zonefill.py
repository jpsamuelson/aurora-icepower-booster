#!/usr/bin/env python3
"""
Phase 5: Zone-fill via pcbnew, then text-merge filled polygons back into original.

pcbnew.SaveBoard() corrupts KiCad 9 files — so we:
1. Fill zones on a copy via pcbnew API
2. Extract filled_polygon blocks from the copy
3. Merge them into the original PCB by matching zone UUIDs
"""
import sys, os, re, shutil
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.11/site-packages')
import pcbnew

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORIG = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP = '/tmp/aurora-zones-filled.kicad_pcb'

# ── Step 1: Fill zones on a copy ──
print(f'Loading board for zone fill...')
board = pcbnew.LoadBoard(ORIG)
filler = pcbnew.ZONE_FILLER(board)
zones = board.Zones()
zone_list = list(zones)
print(f'  Zones: {len(zone_list)}')
filler.Fill(zones)
print(f'  Zones filled')

pcbnew.SaveBoard(TEMP, board)
print(f'  Saved filled copy: {TEMP}')

# ── Step 2: Extract filled_polygon from filled copy ──
with open(TEMP) as f:
    filled_text = f.read()
with open(ORIG) as f:
    orig_text = f.read()

# Extract zone blocks with their UUIDs
def extract_zone_blocks(content):
    """Extract zone blocks with UUID and filled_polygon content."""
    zones_data = {}
    idx = 0
    while True:
        start = content.find('\t(zone\n', idx)
        if start == -1:
            start = content.find('\t(zone ', idx)
        if start == -1:
            break
        # Find balanced end
        depth = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        block = content[start:end]
        # Extract UUID
        uuid_m = re.search(r'\(uuid "([^"]+)"\)', block)
        if uuid_m:
            uid = uuid_m.group(1)
            zones_data[uid] = block
        idx = end
    return zones_data

filled_zones = extract_zone_blocks(filled_text)
orig_zones = extract_zone_blocks(orig_text)

print(f'\n  Original zones: {len(orig_zones)}')
print(f'  Filled zones:   {len(filled_zones)}')

# ── Step 3: Replace zone blocks in original with filled versions ──
result = orig_text
replaced = 0
for uid, orig_block in orig_zones.items():
    if uid in filled_zones:
        filled_block = filled_zones[uid]
        # Fix library prefix if pcbnew stripped it
        # Also normalize indentation
        result = result.replace(orig_block, filled_block)
        replaced += 1
        print(f'  Zone {uid[:8]}... replaced')

# Fix any footprint library prefixes that pcbnew may have stripped
# pcbnew generates "R_0805_2012Metric" → must be "Resistor_SMD:R_0805_2012Metric"
# This is handled by the zone blocks only containing zone data, not footprints

# ── Bracket balance ──
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in result)
if depth != 0:
    print(f'❌ Bracket balance: {depth}')
    # Attempt recovery — don't write
    sys.exit(1)

print(f'Bracket balance: OK')

with open(ORIG, 'w') as f:
    f.write(result)
print(f'\n✅ Zone fill merged: {replaced} zones')
print(f'   Size: {len(result):,} bytes')
