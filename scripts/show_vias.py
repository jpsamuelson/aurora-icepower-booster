#!/usr/bin/env python3
"""Show full via blocks near target positions."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

via_pattern = re.compile(r'\(via\b')

TARGETS = [
    (12.5, 2.5),
    (22.5, 2.5),
]

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

for m in via_pattern.finditer(content):
    block, end = extract_block(content, m.start())
    if block is None:
        continue
    at_match = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)\)', block)
    if not at_match:
        continue
    x = float(at_match.group(1))
    y = float(at_match.group(2))
    for tx, ty in TARGETS:
        if abs(x - tx) < 0.5 and abs(y - ty) < 0.5:
            print(f"=== Via at ({x}, {y}) offset={m.start()} ===")
            print(block[:500])
            print("---")
