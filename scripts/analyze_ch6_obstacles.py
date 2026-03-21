#!/usr/bin/env python3
"""Analyze obstacles near x=112 in CH6 area for route planning."""
import re

with open('aurora-dsp-icepower-booster.kicad_pcb') as f:
    t = f.read()

print('=== Segments crossing x=112 ±1mm, y=170-195 ===')
for m in re.finditer(r'\(segment\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)\s+\(width\s+([\d.]+)\)\s+\(layer\s+"([^"]+)"\)\s+\(net\s+(\d+)\)', t):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)
    if xmin <= 113 and xmax >= 111 and ymin <= 195 and ymax >= 170:
        net = int(m.group(7))
        layer = m.group(6)
        w = m.group(5)
        if abs(x2 - x1) > 0.01:
            t_param = (112 - x1) / (x2 - x1)
            if 0 <= t_param <= 1:
                y_at_112 = y1 + t_param * (y2 - y1)
                print(f'  ({x1:.1f},{y1:.1f})->({x2:.1f},{y2:.1f}) w={w} {layer} net={net} y@x112={y_at_112:.2f}')
        elif abs(x1 - 112) < 1:
            print(f'  ({x1:.1f},{y1:.1f})->({x2:.1f},{y2:.1f}) w={w} {layer} net={net} VERTICAL')

print()
print('=== Vias near x=112 ±2mm, y=170-195 ===')
for m in re.finditer(r'\(via\s+\(at\s+([\d.]+)\s+([\d.]+)\)\s+\(size\s+([\d.]+)\)\s+\(drill\s+([\d.]+)\).*?\(net\s+(\d+)\)', t):
    x, y = float(m.group(1)), float(m.group(2))
    if 110 <= x <= 114 and 170 <= y <= 195:
        print(f'  ({x},{y}) size={m.group(3)} net={m.group(5)}')

# Also check pads at (112, 178.8) area
print()
print('=== Net names for relevant nets ===')
for net_id in [106, 111, 112, 117, 118, 120, 132, 133, 134]:
    m = re.search(rf'\(net\s+{net_id}\s+"([^"]+)"\)', t)
    if m:
        print(f'  Net {net_id}: {m.group(1)}')
