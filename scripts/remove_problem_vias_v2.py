#!/usr/bin/env python3
"""Find and remove vias near specific positions."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

# Find all via blocks (multi-line, balanced parens)
# Pattern: (via ... ) with nested parens
via_pattern = re.compile(r'\(via\b')

TARGETS = [
    (12.5, 2.5, "GND"),       # shorts with J15 Pad2
    (22.5, 2.5, "REMOTE_IN"), # dangling
]

def extract_block(text, start):
    """Extract balanced parenthesized block starting at 'start'."""
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

# Find all vias and check against targets
removals = []
for m in via_pattern.finditer(content):
    block, end = extract_block(content, m.start())
    if block is None:
        continue
    
    at_match = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)\)', block)
    if not at_match:
        continue
    
    x = float(at_match.group(1))
    y = float(at_match.group(2))
    
    for tx, ty, tnet in TARGETS:
        if abs(x - tx) < 0.5 and abs(y - ty) < 0.5:
            net_match = re.search(r'\(net\s+\d+\s+"([^"]*)"', block)
            net_name = net_match.group(1) if net_match else "unknown"
            print(f"Found via at ({x}, {y}) net={net_name} — checking against target ({tx}, {ty}) net={tnet}")
            if tnet in net_name:
                removals.append((m.start(), end, x, y, net_name))
                print(f"  → WILL REMOVE")

print(f"\nFound {len(removals)} vias to remove")

if removals:
    # Remove in reverse order to keep positions valid
    new_content = content
    for start, end, x, y, net in sorted(removals, key=lambda r: r[0], reverse=True):
        new_content = new_content[:start] + new_content[end:]
        print(f"Removed via at ({x}, {y}) net={net}")
    
    # Balance check
    depth = 0
    for ch in new_content:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    print(f"Bracket balance: {depth}")
    
    with open(PCB, "w") as f:
        f.write(new_content)
    print("Written to PCB.")
