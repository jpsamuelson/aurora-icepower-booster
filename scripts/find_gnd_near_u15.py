#!/usr/bin/env python3
"""Find nearest GND connections to U15 Pad1 and add a trace stub."""
import re, math

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"
GND_NET = 134
PAD1_X, PAD1_Y = 126.8625, 23.05
PAD1_W, PAD1_H = 1.325, 0.6  # size

with open(PCB) as f:
    content = f.read()

def extract_block(text, start):
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(': depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0: return text[start:i+1], i+1
        i += 1
    return None, start

# Find nearest GND vias
print("=== Nearest GND Vias ===")
gnd_vias = []
for m in re.finditer(r'\(via\b', content):
    block, _ = extract_block(content, m.start())
    if not block or f'(net {GND_NET})' not in block:
        continue
    at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)\)', block)
    if at:
        vx, vy = float(at.group(1)), float(at.group(2))
        dist = math.sqrt((vx-PAD1_X)**2 + (vy-PAD1_Y)**2)
        gnd_vias.append((vx, vy, dist))

gnd_vias.sort(key=lambda v: v[2])
for vx, vy, dist in gnd_vias[:10]:
    print(f"  Via at ({vx}, {vy}) dist={dist:.2f}mm")

# Find nearest GND traces
print("\n=== Nearest GND Traces ===")
gnd_traces = []
for m in re.finditer(r'\(segment\b', content):
    block, _ = extract_block(content, m.start())
    if not block or f'(net {GND_NET})' not in block:
        continue
    s = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', block)
    e = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', block)
    layer = re.search(r'\(layer\s+"([^"]+)"', block)
    if s and e:
        sx, sy = float(s.group(1)), float(s.group(2))
        ex, ey = float(e.group(1)), float(e.group(2))
        ly = layer.group(1) if layer else "?"
        dist_s = math.sqrt((sx-PAD1_X)**2 + (sy-PAD1_Y)**2)
        dist_e = math.sqrt((ex-PAD1_X)**2 + (ey-PAD1_Y)**2)
        min_dist = min(dist_s, dist_e)
        gnd_traces.append((sx, sy, ex, ey, ly, min_dist))

gnd_traces.sort(key=lambda t: t[5])
for sx, sy, ex, ey, ly, dist in gnd_traces[:10]:
    print(f"  ({sx},{sy})→({ex},{ey}) [{ly}] dist={dist:.2f}mm")

# Find nearest GND pads of other components
print("\n=== Nearest GND Pads ===")
gnd_pads = []
for m in re.finditer(r'\(footprint\b', content):
    fp_block, fp_end = extract_block(content, m.start())
    if not fp_block:
        continue
    
    fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block[:500])
    if not fp_at:
        continue
    fx = float(fp_at.group(1))
    fy = float(fp_at.group(2))
    fa = float(fp_at.group(3)) if fp_at.group(3) else 0
    
    # Quick distance check
    if math.sqrt((fx-PAD1_X)**2 + (fy-PAD1_Y)**2) > 10:
        continue
    
    ref_match = re.search(r'"Reference"\s+"([^"]+)"', fp_block)
    ref = ref_match.group(1) if ref_match else "?"
    
    rad = math.radians(-fa) if fa != 0 else 0
    for pm in re.finditer(r'\(pad\b', fp_block):
        pad_block, _ = extract_block(fp_block, pm.start())
        if not pad_block or f'(net {GND_NET})' not in pad_block:
            continue
        pad_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', pad_block)
        if pad_at:
            lx, ly = float(pad_at.group(1)), float(pad_at.group(2))
            if fa != 0:
                rx = lx * math.cos(rad) - ly * math.sin(rad)
                ry = lx * math.sin(rad) + ly * math.cos(rad)
            else:
                rx, ry = lx, ly
            ax, ay = fx + rx, fy + ry
            dist = math.sqrt((ax-PAD1_X)**2 + (ay-PAD1_Y)**2)
            if dist < 5 and dist > 0.1:
                pad_name = re.search(r'\(pad\s+"?([^"\s)]+)"?', pad_block)
                pname = pad_name.group(1) if pad_name else "?"
                gnd_pads.append((ref, pname, ax, ay, dist))

gnd_pads.sort(key=lambda p: p[4])
for ref, pname, ax, ay, dist in gnd_pads[:5]:
    print(f"  {ref} Pad{pname} at ({ax:.3f}, {ay:.3f}) dist={dist:.2f}mm")

# Determine best route: pad edge to nearest GND element
pad_left = PAD1_X - PAD1_W/2   # 126.2
pad_right = PAD1_X + PAD1_W/2  # 127.525
pad_top = PAD1_Y - PAD1_H/2    # 22.75
pad_bottom = PAD1_Y + PAD1_H/2 # 23.35

print(f"\nPad1 extent: X=[{pad_left:.3f}, {pad_right:.3f}] Y=[{pad_top:.3f}, {pad_bottom:.3f}]")
print(f"Pad1 left edge center: ({pad_left:.3f}, {PAD1_Y})")
