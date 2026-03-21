#!/usr/bin/env python3
"""
Robust zone fill: fill zones via pcbnew, text-merge BOTH zones by UUID.
Handles any indentation format.
"""
import sys, os, re
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP = '/tmp/aurora-zones-filled.kicad_pcb'

# ── Step 1: Fill zones via pcbnew ──
print('Loading board for zone fill...')
board = pcbnew.LoadBoard(ORIG)
filler = pcbnew.ZONE_FILLER(board)
zones = board.Zones()
print(f'  Zones: {len(list(zones))}')
filler.Fill(board.Zones())
print('  Zones filled')
pcbnew.SaveBoard(TEMP, board)
print(f'  Saved: {TEMP}')

# ── Step 2: Extract zone blocks by UUID ──
def extract_zones_by_uuid(content):
    """Find zone blocks regardless of indentation, keyed by UUID."""
    zones = {}
    idx = 0
    while True:
        pos = content.find('(zone\n', idx)
        if pos == -1:
            pos = content.find('(zone ', idx)
        if pos == -1:
            break
        # Walk backwards to include any leading whitespace on the same line
        block_start = pos
        while block_start > 0 and content[block_start - 1] in ' \t':
            block_start -= 1
        # Find balanced closing paren
        depth = 0
        end = pos
        for i in range(pos, len(content)):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        block = content[block_start:end]
        uuid_m = re.search(r'\(uuid\s+"([^"]+)"\)', block)
        if uuid_m:
            zones[uuid_m.group(1)] = (block_start, end, block)
        idx = end
    return zones

with open(TEMP) as f:
    filled_text = f.read()
with open(ORIG) as f:
    orig_text = f.read()

orig_zones = extract_zones_by_uuid(orig_text)
filled_zones = extract_zones_by_uuid(filled_text)

print(f'\n  Original zones: {len(orig_zones)}')
for uid in orig_zones:
    layer_m = re.search(r'\(layer\s+"([^"]+)"\)', orig_zones[uid][2])
    print(f'    {uid[:8]}... layer={layer_m.group(1) if layer_m else "?"}')

print(f'  Filled zones:   {len(filled_zones)}')
for uid in filled_zones:
    layer_m = re.search(r'\(layer\s+"([^"]+)"\)', filled_zones[uid][2])
    fp_count = filled_zones[uid][2].count('filled_polygon')
    print(f'    {uid[:8]}... layer={layer_m.group(1) if layer_m else "?"} filled_polygons={fp_count}')

# ── Step 3: Replace zone blocks in original (from end to start for stable offsets) ──
replacements = []
for uid in orig_zones:
    if uid in filled_zones:
        start, end, _ = orig_zones[uid]
        _, _, filled_block = filled_zones[uid]
        replacements.append((start, end, filled_block, uid))

# Sort by position descending so we replace from end first
replacements.sort(key=lambda x: x[0], reverse=True)

result = orig_text
for start, end, filled_block, uid in replacements:
    result = result[:start] + filled_block + result[end:]
    layer_m = re.search(r'\(layer\s+"([^"]+)"\)', filled_block)
    print(f'  Replaced zone {uid[:8]}... ({layer_m.group(1) if layer_m else "?"})')

# ── Bracket balance ──
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in result)
if depth != 0:
    print(f'❌ Bracket imbalance: {depth}')
    sys.exit(1)
print(f'Bracket balance: OK')

with open(ORIG, 'w') as f:
    f.write(result)

print(f'\n✅ Zone fill merged: {len(replacements)} zones')
print(f'   Size: {len(result):,} bytes')
