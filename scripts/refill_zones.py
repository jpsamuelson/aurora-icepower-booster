#!/usr/bin/env python3
"""
Refill GND zones using pcbnew Python API.
Robust bracket-balanced extraction for text-merge.
"""
import re, os, sys, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP_PCB = '/tmp/aurora-zone-refill.kicad_pcb'

def extract_balanced(lines, start):
    depth = 0
    block = []
    j = start
    while j < len(lines):
        block.append(lines[j])
        for ch in lines[j]:
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
        if depth <= 0:
            return block, j
        j += 1
    return block, j

def extract_filled_polygons(zone_lines):
    fills = []
    i = 0
    while i < len(zone_lines):
        if zone_lines[i].strip().startswith('(filled_polygon'):
            block, end_j = extract_balanced(zone_lines, i)
            fills.append(block)
            i = end_j + 1
            continue
        i += 1
    return fills

def remove_filled_polygons(zone_lines):
    result = []
    i = 0
    while i < len(zone_lines):
        if zone_lines[i].strip().startswith('(filled_polygon'):
            _, end_j = extract_balanced(zone_lines, i)
            i = end_j + 1
            continue
        result.append(zone_lines[i])
        i += 1
    return result

# Step 1: Copy to temp
shutil.copy2(PCB_FILE, TEMP_PCB)
print(f"Copied to {TEMP_PCB}")

# Step 2: pcbnew zone fill
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

board = pcbnew.LoadBoard(TEMP_PCB)
filler = pcbnew.ZONE_FILLER(board)
print("Filling zones...")
filler.Fill(board.Zones())
pcbnew.SaveBoard(TEMP_PCB, board)
print("Zones filled")

# Step 3: Read both
with open(TEMP_PCB) as f:
    temp_lines = f.read().split('\n')
with open(PCB_FILE) as f:
    orig_lines = f.read().split('\n')

# Step 4: Extract zones by UUID from temp
temp_zones = {}
i = 0
while i < len(temp_lines):
    if temp_lines[i].strip() == '(zone' or temp_lines[i].strip().startswith('(zone '):
        block, end_j = extract_balanced(temp_lines, i)
        text = '\n'.join(block)
        uuid_m = re.search(r'\(uuid "([^"]+)"\)', text)
        if uuid_m:
            temp_zones[uuid_m.group(1)] = block
        i = end_j + 1
        continue
    i += 1
print(f"Found {len(temp_zones)} zones in temp")

# Step 5: Replace fills in original
new_lines = []
i = 0
replaced = 0
while i < len(orig_lines):
    if orig_lines[i].strip() == '(zone' or orig_lines[i].strip().startswith('(zone '):
        block, end_j = extract_balanced(orig_lines, i)
        text = '\n'.join(block)
        uuid_m = re.search(r'\(uuid "([^"]+)"\)', text)
        
        if uuid_m and uuid_m.group(1) in temp_zones:
            uuid = uuid_m.group(1)
            new_fills = extract_filled_polygons(temp_zones[uuid])
            cleaned = remove_filled_polygons(block)
            
            last_line = cleaned.pop()
            for fill in new_fills:
                cleaned.extend(fill)
            cleaned.append(last_line)
            
            new_lines.extend(cleaned)
            replaced += 1
            print(f"  Zone {uuid[:8]}...: {len(new_fills)} fill polygons")
        else:
            new_lines.extend(block)
        
        i = end_j + 1
        continue
    
    new_lines.append(orig_lines[i])
    i += 1

print(f"Replaced fills for {replaced} zones")

# Bracket check
result = '\n'.join(new_lines)
depth = 0
for ch in result:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: depth={depth}"
print(f"Bracket balance: OK")

with open(PCB_FILE, 'w') as f:
    f.write(result)
print(f"PCB saved")

os.remove(TEMP_PCB)
print("Done")
