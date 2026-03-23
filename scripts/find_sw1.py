#!/usr/bin/env python3
"""Find SW1 pad positions to determine safe J15 placement."""
import re, math, os
PCB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "aurora-dsp-icepower-booster.kicad_pcb")
with open(PCB) as f:
    text = f.read()
idx = text.find('"SW1"')
start = text.rfind('(footprint', 0, idx)
at_m = re.search(r'\(at ([\d.]+) ([\d.]+)( \d+)?\)', text[start:start+300])
fp_x, fp_y = float(at_m.group(1)), float(at_m.group(2))
rot = float((at_m.group(3) or ' 0').strip())
print(f'SW1 at ({fp_x}, {fp_y}), rotation={rot}')
end = text.find('(footprint', start+1)
if end == -1: end = len(text)
fp_text = text[start:end]
for m in re.finditer(r'\(pad\s+"([^"]*)"\s+\w+\s+\w+\s*\n\s*\(at\s+([\d.-]+)\s+([\d.-]+)\)', fp_text):
    pad_name, lx, ly = m.group(1), float(m.group(2)), float(m.group(3))
    rad = math.radians(rot)
    rx = lx * math.cos(rad) - ly * math.sin(rad)
    ry = lx * math.sin(rad) + ly * math.cos(rad)
    ax, ay = fp_x + rx, fp_y + ry
    print(f'  Pad "{pad_name}" local=({lx}, {ly}) abs=({ax:.2f}, {ay:.2f})')
