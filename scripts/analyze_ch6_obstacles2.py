#!/usr/bin/env python3
"""Analyze ALL obstacles in the CH6 routing area for route planning."""
import re

with open('aurora-dsp-icepower-booster.kicad_pcb') as f:
    t = f.read()

# Net name lookup
net_names = {}
for m in re.finditer(r'\(net\s+(\d+)\s+"([^"]+)"\)', t):
    net_names[int(m.group(1))] = m.group(2)

# Proposed route: B.Cu (93.48,193)->(108,193)->(108,177), Via(108,177), F.Cu (108,177)->(112,177)->(112,178.8)
# Check rectangle: x=106-114, y=175-195 on BOTH layers

print('=== ALL segments in x=106-114, y=175-195 ===')
segs = []
for m in re.finditer(r'\(segment\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)\s+\(width\s+([\d.]+)\)\s+\(layer\s+"([^"]+)"\)\s+\(net\s+(\d+)\)', t):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)
    if xmin <= 114 and xmax >= 106 and ymin <= 195 and ymax >= 175:
        net = int(m.group(7))
        name = net_names.get(net, '?')
        layer = m.group(6)
        w = m.group(5)
        segs.append((x1, y1, x2, y2, w, layer, net, name))
        print(f'  ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w} {layer} net={net} {name}')

print(f'\n=== ALL vias in x=106-114, y=175-195 ===')
for m in re.finditer(r'\(via\s+\(at\s+([\d.]+)\s+([\d.]+)\)\s+\(size\s+([\d.]+)\)\s+\(drill\s+([\d.]+)\).*?\(net\s+(\d+)\)', t):
    x, y = float(m.group(1)), float(m.group(2))
    if 106 <= x <= 114 and 175 <= y <= 195:
        net = int(m.group(5))
        name = net_names.get(net, '?')
        print(f'  ({x},{y}) size={m.group(3)} net={net} {name}')

# Check specifically at y=177 on F.Cu, x=106-114
print(f'\n=== F.Cu segments crossing y=177 ±1mm, x=106-114 ===')
for x1, y1, x2, y2, w, layer, net, name in segs:
    if layer != 'F.Cu':
        continue
    ymin, ymax = min(y1, y2), max(y1, y2)
    if ymin <= 178 and ymax >= 176:
        print(f'  ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w} net={net} {name}')

# Check B.Cu at x=108, y=177-193
print(f'\n=== B.Cu segments crossing x=108 ±1mm, y=177-193 ===')
for x1, y1, x2, y2, w, layer, net, name in segs:
    if layer != 'B.Cu':
        continue
    xmin, xmax = min(x1, x2), max(x1, x2)
    if xmin <= 109 and xmax >= 107:
        if abs(x2 - x1) > 0.01:
            t_param = (108 - x1) / (x2 - x1)
            if 0 <= t_param <= 1:
                y_cross = y1 + t_param * (y2 - y1)
                if 177 <= y_cross <= 193:
                    print(f'  ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w} net={net} {name} crosses x=108 at y={y_cross:.2f}')
        else:
            print(f'  ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w} net={net} {name} NEAR x=108')
