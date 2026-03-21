#!/usr/bin/env python3
"""
Fix silk_edge_clearance by removing fp_line segments on F.SilkS that extend
past the board edge. Uses balanced-paren parsing instead of regex.
"""
import re, os, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

with open(PCB_FILE) as f:
    text = f.read()

board_left, board_top, board_right, board_bottom = 0, 0, 158, 200

def find_footprint_block(text, ref):
    for pattern in [f'(property "Reference" "{ref}"', f'fp_text reference "{ref}"']:
        idx = text.find(pattern)
        if idx >= 0: break
    else:
        return None, None
    depth = 0; start = idx
    while start > 0:
        if text[start] == ')': depth += 1
        elif text[start] == '(':
            depth -= 1
            if depth < 0 and ('(footprint ' in text[start:start+20] or '(footprint\n' in text[start:start+20]):
                break
        start -= 1
    depth = 0; end = start
    while end < len(text):
        if text[end] == '(': depth += 1
        elif text[end] == ')':
            depth -= 1
            if depth == 0: end += 1; break
        end += 1
    return start, end


def extract_fp_lines(block):
    """Extract all (fp_line ...) blocks from footprint.
    Returns list of (start, end, block_text)."""
    results = []
    i = 0
    while True:
        idx = block.find('(fp_line', i)
        if idx < 0: break
        # Find balanced end
        depth = 0; j = idx
        while j < len(block):
            if block[j] == '(': depth += 1
            elif block[j] == ')':
                depth -= 1
                if depth == 0: break
            j += 1
        results.append((idx, j+1, block[idx:j+1]))
        i = j + 1
    return results


# Connectors with silk past edge
target_refs = ['J1', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']

total_removed = 0

for ref in target_refs:
    start, end = find_footprint_block(text, ref)
    if start is None:
        print(f"  {ref}: NOT FOUND")
        continue
    
    block = text[start:end]
    
    # Get footprint position
    m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    if not m: continue
    fp_x, fp_y = float(m.group(1)), float(m.group(2))
    fp_angle = float(m.group(3)) if m.group(3) else 0
    rad = math.radians(-fp_angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    
    # Find all fp_line blocks
    fp_lines = extract_fp_lines(block)
    
    # Filter: only silk lines
    lines_to_remove = []
    for line_start, line_end, line_text in fp_lines:
        if 'SilkS' not in line_text and 'Silkscreen' not in line_text:
            continue
        
        # Extract start/end coords
        start_m = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', line_text)
        end_m = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', line_text)
        if not start_m or not end_m:
            continue
        
        sx, sy = float(start_m.group(1)), float(start_m.group(2))
        ex, ey = float(end_m.group(1)), float(end_m.group(2))
        
        # Rotate to global coordinates
        gsx = fp_x + sx * cos_a - sy * sin_a
        gsy = fp_y + sx * sin_a + sy * cos_a
        gex = fp_x + ex * cos_a - ey * sin_a
        gey = fp_y + ex * sin_a + ey * cos_a
        
        # Check if either endpoint is past board edge
        margin = -0.15  # 0.15mm inside = still past
        past_edge = (
            gsx < board_left + margin or gsx > board_right - margin or
            gsy < board_top + margin or gsy > board_bottom - margin or
            gex < board_left + margin or gex > board_right - margin or
            gey < board_top + margin or gey > board_bottom - margin
        )
        
        if past_edge:
            lines_to_remove.append((line_start, line_end))
    
    # Remove lines (reverse order)
    if lines_to_remove:
        new_block = block
        for ls, le in sorted(lines_to_remove, reverse=True):
            # Also remove trailing whitespace/newlines
            while le < len(new_block) and new_block[le] in ' \t\n\r':
                le += 1
            new_block = new_block[:ls] + new_block[le:]
            total_removed += 1
        text = text[:start] + new_block + text[end:]
        print(f"  {ref}: removed {len(lines_to_remove)} silk segments past edge")

print(f"\nTotal removed: {total_removed}")

# Bracket balance
depth = 0
for ch in text:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"Bracket balance: OK")

with open(PCB_FILE, 'w') as f:
    f.write(text)
print(f"Written: {len(text)} bytes")
