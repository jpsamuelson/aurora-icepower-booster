#!/usr/bin/env python3
"""Fix F5+F6: Rgnd resistors R2,R4,R6,R8,R10,R12.
Current state:
- R2: pin1=unconnected, pin2=CH1_HOT_IN → need pin1 on GND
- R4: pin1=CH2_HOT_IN, pin2=CH2_HOT_IN → need pin1 on GND (remove HOT_IN connection)
- Same for R6,R8,R10,R12

R2-R12 positions (from analysis):
- R2 at (55, 107) rot=0° → pin1=(55, 103.19), pin2=(55, 110.81)
- Pattern: all at (55, ch_y-3) rot=0°

Strategy:
- R2.pin1 at (55, 103.19) is unconnected → add GND power symbol
- R4.pin1 at (55, 183.19) is on HOT_IN → find wire connecting it, remove it, add GND
- Same for R6,R8,R10,R12

For R4-R12: pin1 and pin2 are both on HOT_IN. This means the wire from pin1 
connects to the HOT_IN wire chain. Need to break that connection and add GND."""
import re, math, uuid, subprocess

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()
orig_len = len(text)

# Rgnd positions: R2 at (55, 107), R4-R12 at (55, ch_y-3)
ch_y = {1: 110, 2: 190, 3: 270, 4: 350, 5: 430, 6: 510}
rgnd = {
    1: {'ref': 'R2', 'pos': (55, 107), 'pin1': (55, 103.19)},
    2: {'ref': 'R4', 'pos': (55, 187), 'pin1': (55, 183.19)},
    3: {'ref': 'R6', 'pos': (55, 267), 'pin1': (55, 263.19)},
    4: {'ref': 'R8', 'pos': (55, 347), 'pin1': (55, 343.19)},
    5: {'ref': 'R10', 'pos': (55, 427), 'pin1': (55, 423.19)},
    6: {'ref': 'R12', 'pos': (55, 507), 'pin1': (55, 503.19)},
}

# First, find wires connected to each pin1
print("=== Current wires at Rgnd pin1 positions ===")
for ch, info in rgnd.items():
    px, py = info['pin1']
    ref = info['ref']
    wires_at_pin = []
    for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
        x1, y1 = float(m.group(1)), float(m.group(2))
        x2, y2 = float(m.group(3)), float(m.group(4))
        if (abs(x1-px)<0.1 and abs(y1-py)<0.1) or (abs(x2-px)<0.1 and abs(y2-py)<0.1):
            wires_at_pin.append(((x1,y1),(x2,y2)))
    
    print(f"\n  CH{ch} {ref} pin1 at ({px}, {py}):")
    for (x1,y1),(x2,y2) in wires_at_pin:
        print(f"    Wire: ({x1}, {y1}) → ({x2}, {y2})")
    if not wires_at_pin:
        print(f"    No wires (pin is floating)")
