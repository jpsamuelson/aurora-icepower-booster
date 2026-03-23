#!/usr/bin/env python3
"""Fix Kanal 1-6 gr_text stroke thickness from 0.1mm to 0.15mm."""
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

fixed = 0
new_content = content

for m in re.finditer(r'\(gr_text\b', new_content):
    block, end = extract_block(new_content, m.start())
    if block and re.search(r'"Kanal \d"', block):
        # Find stroke thickness 0.1 and replace with 0.15
        # Pattern in effects: (stroke (width 0.1) ...)
        # Or in font: (size X Y) (thickness 0.1)
        old_block = block
        
        # Fix thickness in (effects (font (size ...) (thickness 0.1)))
        new_block = re.sub(
            r'\(thickness\s+0\.1\)',
            '(thickness 0.15)',
            old_block
        )
        
        # Also fix stroke width if present
        new_block = re.sub(
            r'\(stroke\s+\(width\s+0\.1\)',
            '(stroke (width 0.15)',
            new_block
        )
        
        if new_block != old_block:
            new_content = new_content[:m.start()] + new_block + new_content[end:]
            kanal = re.search(r'"(Kanal \d)"', block).group(1)
            fixed += 1
            print(f"Fixed: {kanal} thickness 0.1 → 0.15mm")

print(f"\nFixed {fixed} Kanal labels")

# Balance check
depth = 0
for ch in new_content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"Bracket balance: {depth}")

with open(PCB, 'w') as f:
    f.write(new_content)
print("Written.")
