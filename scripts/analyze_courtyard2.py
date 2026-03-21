#!/usr/bin/env python3
"""Check courtyard bounds of U1, U15 and find clear position for C79."""
import re, os, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

with open(PCB_FILE) as f:
    text = f.read()

def find_footprint_block(text, ref):
    for pattern in [f'(property "Reference" "{ref}"', f'fp_text reference "{ref}"']:
        idx = text.find(pattern)
        if idx >= 0:
            break
    else:
        return None
    depth = 0
    start = idx
    while start > 0:
        if text[start] == ')': depth += 1
        elif text[start] == '(':
            depth -= 1
            if depth < 0:
                after = text[start:start+20]
                if '(footprint ' in after or '(footprint\n' in after:
                    break
        start -= 1
    depth = 0
    end = start
    while end < len(text):
        if text[end] == '(': depth += 1
        elif text[end] == ')':
            depth -= 1
            if depth == 0:
                end += 1
                break
        end += 1
    return text[start:end]

def get_courtyard_bounds(block, fp_x, fp_y, fp_angle):
    rad = math.radians(-fp_angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    xs, ys = [], []
    for m in re.finditer(r'\(fp_line\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)[^)]*\(layer\s+"?[FB]\.CrtYd"?\)', block):
        for gx, gy in [(float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4)))]:
            rx = fp_x + gx * cos_a - gy * sin_a
            ry = fp_y + gx * sin_a + gy * cos_a
            xs.append(rx); ys.append(ry)
    for m in re.finditer(r'\(fp_rect\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)[^)]*\(layer\s+"?[FB]\.CrtYd"?\)', block):
        for gx, gy in [(float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4))),
                        (float(m.group(1)), float(m.group(4))), (float(m.group(3)), float(m.group(2)))]:
            rx = fp_x + gx * cos_a - gy * sin_a
            ry = fp_y + gx * sin_a + gy * cos_a
            xs.append(rx); ys.append(ry)
    if xs and ys:
        return (min(xs), min(ys), max(xs), max(ys))
    return None

for ref in ['U1', 'U15', 'C18', 'C79']:
    block = find_footprint_block(text, ref)
    if not block:
        print(f"{ref}: NOT FOUND"); continue
    m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    if m:
        x, y = float(m.group(1)), float(m.group(2))
        angle = float(m.group(3)) if m.group(3) else 0
        bounds = get_courtyard_bounds(block, x, y, angle)
        print(f"{ref}: pos=({x}, {y}, {angle}°) courtyard={bounds}")
