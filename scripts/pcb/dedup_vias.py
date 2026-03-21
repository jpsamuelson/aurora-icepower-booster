#!/usr/bin/env python3
"""Remove duplicate vias (same position + same net)."""
import re, os

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

# Extract all via blocks with positions
lines = content.split('\n')
result_lines = []
seen_vias = set()
removed = 0
i = 0

while i < len(lines):
    stripped = lines[i].strip()
    if stripped == '(via' or stripped.startswith('(via '):
        # Check it's at top level (1 tab)
        if lines[i].startswith('\t') and not lines[i].startswith('\t\t'):
            # Extract the entire via block
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
            
            # Extract position and net for dedup key
            at_m = re.search(r'\(at\s+([\d.+-]+)\s+([\d.+-]+)\)', block)
            net_m = re.search(r'\(net\s+(\d+)\)', block)
            
            if at_m and net_m:
                key = (at_m.group(1), at_m.group(2), net_m.group(1))
                if key in seen_vias:
                    # Skip duplicate
                    removed += 1
                    i = j + 1
                    continue
                seen_vias.add(key)
            
            result_lines.extend(block_lines)
            i = j + 1
            continue
    
    result_lines.append(lines[i])
    i += 1

content = '\n'.join(result_lines)

# Bracket balance
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
if depth != 0:
    print(f"❌ Bracket balance: {depth}")
    import sys; sys.exit(1)

with open(PCB, 'w') as f:
    f.write(content)

print(f"Removed {removed} duplicate vias")
print(f"Remaining vias: {len(seen_vias)}")
print(f"Size: {len(content):,} bytes")
print("Bracket balance: OK")
