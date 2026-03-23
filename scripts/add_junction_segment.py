#!/usr/bin/env python3
"""Add missing segment from junction (31.7356, 11.5) to (36.292, 15.0)."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

def extract_block(text, start):
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(': depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0: return text[start:i+1], i+1
        i += 1
    return None, start

# Find last segment
last_seg_end = 0
for m in re.finditer(r'\(segment\b', content):
    block, end = extract_block(content, m.start())
    if block:
        last_seg_end = end

new_seg = """
	(segment
		(start 31.7356 11.5)
		(end 36.292 15.0)
		(width 0.25)
		(layer "F.Cu")
		(net 130)
		(uuid "a1b2c3d4-reroute-junction-far")
	)"""

content = content[:last_seg_end] + new_seg + content[last_seg_end:]

# Balance check
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"Bracket balance: {depth}")

with open(PCB, 'w') as f:
    f.write(content)
print("Added junction→far segment (31.7356, 11.5) → (36.292, 15.0)")

# Verify all REMOTE_IN segments
print("\nAll REMOTE_IN segments:")
with open(PCB) as f:
    v = f.read()
for m in re.finditer(r'\(segment\b', v):
    block, _ = extract_block(v, m.start())
    if block and '(net 130)' in block:
        s = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', block)
        e = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', block)
        if s and e:
            print(f"  ({s.group(1)}, {s.group(2)}) → ({e.group(1)}, {e.group(2)})")
