#!/usr/bin/env python3
"""
Remove all filled_polygon blocks that have (island) tag.
pcbnew marks isolated zone fill fragments with (island).
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

# Count island polygons
island_count = content.count('(island)')
print(f"Island-tagged filled_polygons: {island_count}")

# Remove all filled_polygon blocks that contain (island)
# These are at indentation level 4 (tabs) inside zone blocks
lines = content.split('\n')
result_lines = []
removed = 0
i = 0

while i < len(lines):
    stripped = lines[i].strip()
    
    if stripped == '(filled_polygon' or stripped.startswith('(filled_polygon '):
        # Collect block
        depth = 0
        block_lines = []
        j = i
        while j < len(lines):
            block_lines.append(lines[j])
            for ch in lines[j]:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            if depth <= 0:
                break
            j += 1
        
        block = '\n'.join(block_lines)
        
        if '(island)' in block:
            # Skip this island polygon
            removed += 1
            i = j + 1
            continue
        
        result_lines.extend(block_lines)
        i = j + 1
        continue
    
    result_lines.append(lines[i])
    i += 1

content = '\n'.join(result_lines)

# Clean up excessive empty lines
content = re.sub(r'\n{3,}', '\n\n', content)

# Bracket balance
depth_check = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
if depth_check != 0:
    print(f"❌ Bracket balance: {depth_check}")
    import sys; sys.exit(1)

with open(PCB, 'w') as f:
    f.write(content)

print(f"\n✅ Island-Polygone entfernt: {removed}")
print(f"   Bracket balance: OK")
print(f"   Größe: {len(content):,} bytes")
