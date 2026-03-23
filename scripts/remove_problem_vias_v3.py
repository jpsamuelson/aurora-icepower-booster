#!/usr/bin/env python3
"""Remove problematic vias by position and net ID."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

# Targets: (x, y, net_id)
# net 130 = /REMOTE_IN, net 134 = GND
TARGETS = [
    (12.5, 2.5, 134),   # GND via shorting J15 Pad2
    (22.5, 2.5, 130),   # Dangling REMOTE_IN via
]

via_pattern = re.compile(r'\(via\b')

def extract_block(text, start):
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
    
    net_match = re.search(r'\(net\s+(\d+)\)', block)
    net_id = int(net_match.group(1)) if net_match else -1
    
    for tx, ty, tnet in TARGETS:
        if abs(x - tx) < 0.1 and abs(y - ty) < 0.1 and net_id == tnet:
            removals.append((m.start(), end, x, y, net_id))
            print(f"Found target via at ({x}, {y}) net={net_id}")

print(f"\nRemoving {len(removals)} vias")

if removals:
    new_content = content
    for start, end, x, y, net in sorted(removals, key=lambda r: r[0], reverse=True):
        # Also remove any trailing whitespace/newlines
        while end < len(new_content) and new_content[end] in ' \t\n':
            end += 1
        new_content = new_content[:start] + new_content[end:]
        print(f"Removed via at ({x}, {y}) net={net}")
    
    depth = 0
    for ch in new_content:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    print(f"Bracket balance: {depth}")
    
    with open(PCB, "w") as f:
        f.write(new_content)
    print("Written.")
