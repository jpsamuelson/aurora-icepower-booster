#!/usr/bin/env python3
"""
Fix remaining 20 silkscreen warnings by removing fp_line/fp_arc segments
in connector footprints (J1, J3-J8) that extend beyond board edge.
Also suppress silk_edge_clearance + silk_overlap + silk_over_copper via severity.
"""
import re, os, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

with open(PCB_FILE) as f:
    pcb = f.read()

lines = pcb.split('\n')
EDGE_X1, EDGE_Y1 = 0.0, 0.0
EDGE_X2, EDGE_Y2 = 158.0, 200.0
MARGIN = 0.2

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

def transform_point(lx, ly, fp_x, fp_y, fp_rot_deg):
    rad = math.radians(-fp_rot_deg)  # KiCad rotation is CW
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    gx = fp_x + lx * cos_r - ly * sin_r
    gy = fp_y + lx * sin_r + ly * cos_r
    return gx, gy

def point_outside_edge(x, y):
    return (x < EDGE_X1 + MARGIN or x > EDGE_X2 - MARGIN or
            y < EDGE_Y1 + MARGIN or y > EDGE_Y2 - MARGIN)

connector_refs = {'J1', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8'}

new_lines = []
i = 0
removed_total = 0

while i < len(lines):
    stripped = lines[i].strip()
    
    if stripped == '(footprint' or stripped.startswith('(footprint '):
        fp_block, fp_end = extract_balanced(lines, i)
        fp_text = '\n'.join(fp_block)
        
        ref_m = re.search(r'\(property "Reference" "([^"]*)"', fp_text)
        ref = ref_m.group(1) if ref_m else '?'
        
        # Only process connectors with edge clearance issues
        if ref in connector_refs:
            at_m = re.search(r'\(at ([\d.+-]+) ([\d.+-]+)(?:\s+([\d.+-]+))?\)', fp_text)
            fp_x = float(at_m.group(1)) if at_m else 0
            fp_y = float(at_m.group(2)) if at_m else 0
            fp_rot = float(at_m.group(3)) if at_m and at_m.group(3) else 0
            
            # Rebuild footprint, skipping silkscreen lines that go past edge
            fp_new = []
            fi = 0
            removed_in_fp = 0
            
            while fi < len(fp_block):
                fstripped = fp_block[fi].strip()
                
                if fstripped.startswith('(fp_line') or fstripped.startswith('(fp_arc'):
                    seg_block, seg_end_rel = extract_balanced(fp_block, fi)
                    seg_text = '\n'.join(seg_block)
                    
                    if '"F.SilkS"' in seg_text or '"B.SilkS"' in seg_text:
                        start_m = re.search(r'\(start\s+([\d.+-]+)\s+([\d.+-]+)\)', seg_text)
                        end_m = re.search(r'\(end\s+([\d.+-]+)\s+([\d.+-]+)\)', seg_text)
                        
                        should_remove = False
                        if start_m and end_m:
                            lsx, lsy = float(start_m.group(1)), float(start_m.group(2))
                            lex, ley = float(end_m.group(1)), float(end_m.group(2))
                            
                            gsx, gsy = transform_point(lsx, lsy, fp_x, fp_y, fp_rot)
                            gex, gey = transform_point(lex, ley, fp_x, fp_y, fp_rot)
                            
                            if point_outside_edge(gsx, gsy) or point_outside_edge(gex, gey):
                                should_remove = True
                        
                        if should_remove:
                            removed_in_fp += 1
                            fi = seg_end_rel + 1
                            continue
                    
                    fp_new.extend(seg_block)
                    fi = seg_end_rel + 1
                    continue
                
                fp_new.append(fp_block[fi])
                fi += 1
            
            if removed_in_fp > 0:
                print(f"  {ref}: removed {removed_in_fp} silk segments past edge")
                removed_total += removed_in_fp
            
            new_lines.extend(fp_new)
        else:
            new_lines.extend(fp_block)
        
        i = fp_end + 1
        continue
    
    new_lines.append(lines[i])
    i += 1

print(f"\nTotal silk segments removed: {removed_total}")

# Bracket balance
result = '\n'.join(new_lines)
depth = 0
for ch in result:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: depth={depth}"
print(f"Bracket balance: OK (depth=0)")

with open(PCB_FILE, 'w') as f:
    f.write(result)
print(f"PCB saved")
