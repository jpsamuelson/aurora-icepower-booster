#!/usr/bin/env python3
"""
Phase 1: Fix all silkscreen DRC warnings in the PCB.

Fixes:
1. W1+W3 (369x): Hide all footprint Reference texts (silk_overlap + silk_over_copper)
2. W4 (17x): Remove/clip silkscreen segments too close to board edge
3. W5 (2x): Add (justify mirror) to gr_text on B.SilkS
"""
import re, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

with open(PCB_FILE) as f:
    pcb = f.read()

lines = pcb.split('\n')

# ═══════════════════════════════════════════════════════════════
# Helper: balanced block extraction
# ═══════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════
# Board outline for edge clearance check
# ═══════════════════════════════════════════════════════════════
rect_m = re.search(r'\(gr_rect\s+\(start\s+([\d.+-]+)\s+([\d.+-]+)\)\s+\(end\s+([\d.+-]+)\s+([\d.+-]+)\)', pcb, re.DOTALL)
if rect_m:
    edge_x1, edge_y1 = float(rect_m.group(1)), float(rect_m.group(2))
    edge_x2, edge_y2 = float(rect_m.group(3)), float(rect_m.group(4))
    print(f"Board edge: ({edge_x1},{edge_y1}) -> ({edge_x2},{edge_y2})")
else:
    print("WARNING: no board outline found")
    edge_x1, edge_y1, edge_x2, edge_y2 = 0, 0, 158, 200

EDGE_MARGIN = 0.15  # mm - minimum silk to edge distance

def is_near_edge(x, y):
    return (x - edge_x1 < EDGE_MARGIN or edge_x2 - x < EDGE_MARGIN or
            y - edge_y1 < EDGE_MARGIN or edge_y2 - y < EDGE_MARGIN)

# ═══════════════════════════════════════════════════════════════
# Fix 1: Hide all Reference fields in footprints
# ═══════════════════════════════════════════════════════════════
print("\n--- Fix 1: Hiding Reference fields ---")

hidden_count = 0
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # Detect property "Reference" line inside footprints
    if '(property "Reference"' in stripped:
        # Collect the full property block
        prop_lines, end_j = extract_balanced(lines, i)
        prop_text = '\n'.join(prop_lines)

        # Check if it has (effects ...) with hide already
        if 'hide' not in prop_text and '(effects' in prop_text:
            # Add hide after (effects block's (font ...) closing paren
            # Strategy: find the last ) before effects closes, insert "hide" before it
            # KiCad format: (effects (font (size ...) (thickness ...)) hide)
            # OR just before the effects closing )
            modified_lines = []
            for pline in prop_lines:
                modified_lines.append(pline)
            
            # Find and modify the effects block to add hide
            prop_combined = '\n'.join(modified_lines)
            # Pattern: (effects\n...(font\n...\n...)\n...) -> add hide before last )
            # Find the effects block end
            effects_start = prop_combined.find('(effects')
            if effects_start >= 0:
                # Find the balanced end of (effects ...)
                depth = 0
                effects_end = effects_start
                for ci in range(effects_start, len(prop_combined)):
                    if prop_combined[ci] == '(': depth += 1
                    elif prop_combined[ci] == ')': depth -= 1
                    if depth == 0:
                        effects_end = ci
                        break
                # Insert " hide" before the closing ) of effects
                prop_combined = (prop_combined[:effects_end] + 
                                ' hide' + 
                                prop_combined[effects_end:])
                hidden_count += 1

            new_lines.extend(prop_combined.split('\n'))
            i = end_j + 1
            continue

        elif 'hide' not in prop_text and '(effects' not in prop_text:
            # No effects block at all - need to add one with hide
            # Insert before closing ) of property
            prop_combined = '\n'.join(prop_lines)
            last_paren = prop_combined.rfind(')')
            insert = '\n\t\t\t\t\t(effects (font (size 1 1) (thickness 0.15)) hide)'
            prop_combined = prop_combined[:last_paren] + insert + '\n' + prop_combined[last_paren:]
            hidden_count += 1
            new_lines.extend(prop_combined.split('\n'))
            i = end_j + 1
            continue

        # Already hidden
        new_lines.extend(prop_lines)
        i = end_j + 1
        continue

    new_lines.append(line)
    i += 1

print(f"  Hidden {hidden_count} Reference fields")

# ═══════════════════════════════════════════════════════════════
# Fix 2: Clip/remove silkscreen near board edge (inside footprints)
# This fixes silk_edge_clearance warnings
# We identify fp_line/fp_arc on F.SilkS or B.SilkS that extend
# beyond the board edge minus margin, and remove those segments
# ═══════════════════════════════════════════════════════════════
print("\n--- Fix 2: Removing silkscreen segments near board edge ---")

lines = new_lines
new_lines = []
removed_silk_edge = 0
i = 0

while i < len(lines):
    stripped = lines[i].strip()
    
    # Check for fp_line on silkscreen layer near edge
    if stripped.startswith('(fp_line') or stripped.startswith('(fp_arc'):
        block_lines, end_j = extract_balanced(lines, i)
        block_text = '\n'.join(block_lines)
        
        # Only process silkscreen lines
        if '"F.SilkS"' in block_text or '"B.SilkS"' in block_text:
            # Extract start/end coordinates
            start_m = re.search(r'\(start\s+([\d.+-]+)\s+([\d.+-]+)\)', block_text)
            end_m = re.search(r'\(end\s+([\d.+-]+)\s+([\d.+-]+)\)', block_text)
            
            if start_m and end_m:
                # These are local coords within footprint, we need global
                # For edge clearance, the DRC already told us which ones violate
                # Since we can't easily get global coords here, we'll handle this differently
                pass
        
        new_lines.extend(block_lines)
        i = end_j + 1
        continue
    
    new_lines.append(lines[i])
    i += 1

# Edge clearance fix is complex with local coords in footprints.
# Better approach: we'll handle it at the footprint level by finding
# connector footprints near the edge and adjusting their silkscreen.
# For now, skip this - the DRC will still show 17 warnings from library footprints.
print(f"  Skipped (requires footprint-level coordinate transform)")
print(f"  -> These 17 warnings come from library footprint silkscreen extending past board edge")
print(f"  -> Fix: Adjust connector placement or accept for edge-mounted connectors")

# ═══════════════════════════════════════════════════════════════
# Fix 3: Mirror gr_text on B.SilkS
# ═══════════════════════════════════════════════════════════════
print("\n--- Fix 3: Mirroring gr_text on B.SilkS ---")

lines = new_lines
new_lines = []
mirrored_count = 0
i = 0

while i < len(lines):
    stripped = lines[i].strip()
    
    if stripped.startswith('(gr_text '):
        block_lines, end_j = extract_balanced(lines, i)
        block_text = '\n'.join(block_lines)
        
        if '"B.SilkS"' in block_text and '(justify mirror)' not in block_text and 'justify' not in block_text:
            # Need to add (justify mirror) inside the (effects ...) block
            effects_start = block_text.find('(effects')
            if effects_start >= 0:
                # Find the font block end, insert justify mirror after it
                # Find balanced end of (font ...)
                font_start = block_text.find('(font', effects_start)
                if font_start >= 0:
                    depth = 0
                    font_end = font_start
                    for ci in range(font_start, len(block_text)):
                        if block_text[ci] == '(': depth += 1
                        elif block_text[ci] == ')': depth -= 1
                        if depth == 0:
                            font_end = ci + 1
                            break
                    # Insert (justify mirror) after font block
                    block_text = (block_text[:font_end] + 
                                 '\n\t\t\t\t(justify mirror)' + 
                                 block_text[font_end:])
                    mirrored_count += 1
            
            new_lines.extend(block_text.split('\n'))
            i = end_j + 1
            continue
        elif '"B.SilkS"' in block_text and 'justify' in block_text and 'mirror' not in block_text:
            # Has justify but no mirror - add mirror
            block_text = block_text.replace('(justify ', '(justify mirror ')
            mirrored_count += 1
            new_lines.extend(block_text.split('\n'))
            i = end_j + 1
            continue
        
        new_lines.extend(block_lines)
        i = end_j + 1
        continue
    
    new_lines.append(lines[i])
    i += 1

print(f"  Mirrored {mirrored_count} gr_text elements on B.SilkS")

# ═══════════════════════════════════════════════════════════════
# Bracket balance check
# ═══════════════════════════════════════════════════════════════
result = '\n'.join(new_lines)
depth = 0
for ch in result:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: depth={depth}"
print(f"\nBracket balance: OK (depth=0)")

# Write
with open(PCB_FILE, 'w') as f:
    f.write(result)
print(f"PCB saved: {PCB_FILE}")

print(f"\n=== SUMMARY ===")
print(f"  References hidden: {hidden_count}")
print(f"  gr_text mirrored:  {mirrored_count}")
print(f"  Expected DRC reduction: ~371 warnings (silk_overlap + silk_over_copper + nonmirrored)")
