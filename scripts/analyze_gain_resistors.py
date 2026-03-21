#!/usr/bin/env python3
"""
Check placement of gain feedback resistors across all 6 channels.
R51-R56 or similar pattern. Also check R69's context.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

def extract_balanced(text, start):
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

# Find all resistors and their nets
print("=== Resistors with GAIN_OUT or GAIN_FB nets ===")
i = 0
gain_resistors = []
while True:
    idx = text.find('(footprint ', i)
    if idx < 0:
        break
    block, end = extract_balanced(text, idx)
    if not block:
        i = idx + 1
        continue
    
    ref_m = re.search(r'\(property\s+"Reference"\s+"(R\d+)"', block)
    if not ref_m:
        i = end
        continue
    ref = ref_m.group(1)
    
    # Check if this has GAIN_OUT or GAIN_FB net
    if 'GAIN' in block:
        fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
        if fp_at:
            x, y = float(fp_at.group(1)), float(fp_at.group(2))
            rot = float(fp_at.group(3) or 0)
            
            # Find nets for pads
            nets = []
            for pm in re.finditer(r'\(pad\s+"([^"]+)".*?\(net\s+\d+\s+"([^"]+)"\)', block, re.DOTALL):
                nets.append(f"pad{pm.group(1)}={pm.group(2)}")
            
            gain_resistors.append((ref, x, y, rot, nets))
    i = end

for ref, x, y, rot, nets in sorted(gain_resistors, key=lambda r: r[0]):
    print(f"  {ref}: ({x}, {y}, rot={rot}) nets: {', '.join(nets)}")

# Show all ICs and their positions for reference
print("\n=== IC positions (U1-U15) ===")
i = 0
while True:
    idx = text.find('(footprint ', i)
    if idx < 0:
        break
    block, end = extract_balanced(text, idx)
    if not block:
        i = idx + 1
        continue
    
    ref_m = re.search(r'\(property\s+"Reference"\s+"(U\d+)"', block)
    if not ref_m:
        i = end
        continue
    ref = ref_m.group(1)
    fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    fp_m = re.search(r'\(footprint\s+"([^"]+)"', block)
    if fp_at and fp_m:
        x, y = float(fp_at.group(1)), float(fp_at.group(2))
        rot = float(fp_at.group(3) or 0)
        print(f"  {ref}: ({x}, {y}, rot={rot}) fp={fp_m.group(1)}")
    i = end
