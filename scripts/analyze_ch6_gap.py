#!/usr/bin/env python3
"""
Analyze the CH6_GAIN_OUT routing gap and nearby obstacles.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

# Find net number for CH6_GAIN_OUT
net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
net_num = net_m.group(1) if net_m else None
print(f"CH6_GAIN_OUT = net {net_num}")

# Find all segments on this net
print(f"\nSegments for net {net_num}:")
for m in re.finditer(r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+([\d.-]+)\)\s+\(layer\s+"([^"]+)"\)[^)]*\(net\s+' + net_num + r'\)', text):
    print(f"  ({m.group(1)},{m.group(2)}) -> ({m.group(3)},{m.group(4)}) w={m.group(5)} layer={m.group(6)}")

print(f"\nVias for net {net_num}:")
for m in re.finditer(r'\(via\s+\(at\s+([\d.-]+)\s+([\d.-]+)\)\s+\(size\s+([\d.-]+)\)[^)]*\(net\s+' + net_num + r'\)', text):
    print(f"  ({m.group(1)},{m.group(2)}) size={m.group(3)}")

# Find all pads connected to this net
print(f"\nPads for net CH6_GAIN_OUT:")

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

i = 0
while True:
    idx = text.find('(footprint ', i)
    if idx < 0:
        break
    block, end = extract_balanced(text, idx)
    if not block:
        i = idx + 1
        continue
    
    if f'(net {net_num} ' not in block and f'(net {net_num})' not in block:
        i = end
        continue
    
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    ref = ref_m.group(1) if ref_m else '?'
    fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    fx, fy = float(fp_at.group(1)), float(fp_at.group(2))
    frot = float(fp_at.group(3) or 0)
    
    for pm in re.finditer(r'\(pad\s+"([^"]+)"[^)]*\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\).*?\(net\s+' + net_num + r'\s', block, re.DOTALL):
        pad_name = pm.group(1)
        px, py = float(pm.group(2)), float(pm.group(3))
        print(f"  {ref} pad {pad_name}: fp_pos=({fx},{fy},{frot}) pad_local=({px},{py})")
    
    i = end

# Find ALL segments near the gap area (y=178-184, x=97-112)
print(f"\nAll segments near gap area (x=95-115, y=175-190):")
for m in re.finditer(r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+([\d.-]+)\)\s+\(layer\s+"([^"]+)"\)[^)]*\(net\s+(\d+)\)', text):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    if (95 <= x1 <= 115 or 95 <= x2 <= 115) and (175 <= y1 <= 190 or 175 <= y2 <= 190):
        net = m.group(7)
        layer = m.group(6)
        w = m.group(5)
        # Get net name
        net_name_m = re.search(r'\(net\s+' + net + r'\s+"([^"]+)"\)', text)
        nn = net_name_m.group(1) if net_name_m else f"net_{net}"
        print(f"  ({x1},{y1})->({x2},{y2}) w={w} layer={layer} net={nn}")
