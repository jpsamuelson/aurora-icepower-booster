#!/usr/bin/env python3
"""
Investigate the CH6_GAIN_OUT routing issue and existing traces.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

# Find all segments and vias for net CH6_GAIN_OUT
# First find the net number
net_m = re.search(r'\(net\s+(\d+)\s+"[^"]*CH6_GAIN_OUT[^"]*"\)', text)
if net_m:
    net_num = net_m.group(1)
    print(f"CH6_GAIN_OUT is net {net_num}")
    
    # Count segments for this net
    seg_count = 0
    for m in re.finditer(r'\(segment\s.*?net\s+' + net_num + r'\b.*?\)', text, re.DOTALL):
        seg_count += 1
    print(f"Found {seg_count} segments for net {net_num}")
    
    via_count = 0
    for m in re.finditer(r'\(via\s.*?net\s+' + net_num + r'\b.*?\)', text, re.DOTALL):
        via_count += 1
    print(f"Found {via_count} vias for net {net_num}")

# Also check: how many total segments and vias?
total_segs = len(re.findall(r'\(segment\b', text))
total_vias = len(re.findall(r'\(via\b', text))
print(f"\nTotal: {total_segs} segments, {total_vias} vias")

# Find R69 pad 2 position (from footprint)
r69_block = None
idx = 0
while True:
    idx = text.find('(footprint ', idx)
    if idx < 0:
        break
    # Quick check for R69
    depth = 0
    i = idx
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                break
        i += 1
    block = text[idx:i+1]
    if '"R69"' in block and '"Reference"' in block:
        # Get footprint position
        fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
        if fp_at:
            fx, fy = float(fp_at.group(1)), float(fp_at.group(2))
            frot = float(fp_at.group(3) or 0)
            print(f"\nR69: pos=({fx},{fy}) rot={frot}")
            
            # Find pads
            for pm in re.finditer(r'\(pad\s+"([^"]+)"[^)]*\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)[^)]*\(net\s+(\d+)\s+"([^"]*)"', block, re.DOTALL):
                pad_name = pm.group(1)
                px, py = float(pm.group(2)), float(pm.group(3))
                pad_net = pm.group(5), pm.group(6)
                print(f"  Pad {pad_name}: local=({px},{py}) net={pad_net}")
        break
    idx = i + 1

# Also check zone min_thickness and island settings
for zm in re.finditer(r'\(zone\s.*?\(net_name\s+"GND"\)', text, re.DOTALL):
    start = zm.start()
    # Find zone settings in the first few hundred chars
    zone_start = text[start:start+500]
    print(f"\nGND Zone snippet: {zone_start[:300]}...")
