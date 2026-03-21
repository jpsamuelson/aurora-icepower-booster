#!/usr/bin/env python3
"""Compare CH1-CH5 GAIN_OUT routing to understand how Freerouting solved it.
Each channel has: U(8+ch) pin 7 → R(63+ch) pad 2 (gain feedback connection)
"""
import re

with open('aurora-dsp-icepower-booster.kicad_pcb') as f:
    t = f.read()

# Net name lookup
net_names = {}
for m in re.finditer(r'\(net\s+(\d+)\s+"([^"]+)"\)', t):
    net_names[int(m.group(1))] = m.group(2)

# Find GAIN_OUT nets for each channel
gain_out_nets = {}
for net_id, name in net_names.items():
    if 'GAIN_OUT' in name:
        gain_out_nets[name] = net_id

print('GAIN_OUT nets:', gain_out_nets)

# For each GAIN_OUT net, find all segments and vias
for name in sorted(gain_out_nets.keys()):
    net_id = gain_out_nets[name]
    print(f'\n=== {name} (net {net_id}) ===')
    
    segs = []
    for m in re.finditer(
        rf'\(segment\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)\s+'
        rf'\(width\s+([\d.]+)\)\s+\(layer\s+"([^"]+)"\)\s+\(net\s+{net_id}\)',
        t
    ):
        x1, y1 = float(m.group(1)), float(m.group(2))
        x2, y2 = float(m.group(3)), float(m.group(4))
        layer = m.group(6)
        w = m.group(5)
        segs.append((x1, y1, x2, y2, w, layer))
    
    vias = []
    for m in re.finditer(
        rf'\(via\s+\(at\s+([\d.]+)\s+([\d.]+)\)\s+\(size\s+([\d.]+)\)\s+\(drill\s+([\d.]+)\).*?\(net\s+{net_id}\)',
        t
    ):
        vias.append((float(m.group(1)), float(m.group(2)), m.group(3)))
    
    # Sort segments by x then y
    segs.sort(key=lambda s: (s[0], s[1]))
    
    print(f'  Segments: {len(segs)}')
    for x1, y1, x2, y2, w, layer in segs:
        # Only show segments near the R6x pad (x>100)
        if max(x1, x2) > 95:
            print(f'    ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w} {layer}')
    
    print(f'  Vias: {len(vias)}')
    for x, y, s in vias:
        print(f'    ({x},{y}) size={s}')
