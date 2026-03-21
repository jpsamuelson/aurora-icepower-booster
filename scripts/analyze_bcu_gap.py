#!/usr/bin/env python3
"""
Map B.Cu traces near the CH6_GAIN_OUT gap area to find a clear path.
"""
import re

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

# Find ALL B.Cu segments in the area x=95-120, y=170-195
print("B.Cu segments near gap (x=95-120, y=170-195):")
for m in re.finditer(r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+([\d.-]+)\)\s+\(layer\s+"B\.Cu"\)[^)]*\(net\s+(\d+)\)', text):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    if (95 <= x1 <= 120 or 95 <= x2 <= 120) and (170 <= y1 <= 195 or 170 <= y2 <= 195):
        net = m.group(6)
        w = m.group(5)
        net_m = re.search(r'\(net\s+' + net + r'\s+"([^"]+)"\)', text)
        nn = net_m.group(1) if net_m else f"net_{net}"
        print(f"  ({x1:.1f},{y1:.1f})->({x2:.1f},{y2:.1f}) w={w} [{nn}]")

# Also find B.Cu vias in this area (existing routing)
print("\nB.Cu vias near gap:")
for m in re.finditer(r'\(via\s+\(at\s+([\d.-]+)\s+([\d.-]+)\)', text):
    x, y = float(m.group(1)), float(m.group(2))
    if 95 <= x <= 120 and 170 <= y <= 195:
        # Find the net
        via_start = m.start()
        via_text = text[via_start:via_start+200]
        net_m2 = re.search(r'\(net\s+(\d+)\)', via_text)
        if net_m2:
            net = net_m2.group(1)
            net_name_m = re.search(r'\(net\s+' + net + r'\s+"([^"]+)"\)', text)
            nn = net_name_m.group(1) if net_name_m else f"net_{net}"
            print(f"  ({x:.1f},{y:.1f}) [{nn}]")

# Show F.Cu CH6_GAIN_OUT trace endpoints to understand the gap
print("\nCH6_GAIN_OUT full route:")
net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
net_num = net_m.group(1)
for m in re.finditer(r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+([\d.-]+)\)\s+\(layer\s+"([^"]+)"\)[^)]*\(net\s+' + net_num + r'\)', text):
    print(f"  ({m.group(1)},{m.group(2)})->({m.group(3)},{m.group(4)}) layer={m.group(6)}")
