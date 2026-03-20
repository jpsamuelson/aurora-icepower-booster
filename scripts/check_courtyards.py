#!/usr/bin/env python3
"""Extract courtyard extents for key components from PCB."""
import re, math

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

def extract_footprint_block(text, ref):
    """Extract the footprint block for a given reference."""
    # Try both KiCad 9 property format and older fp_text format
    for pattern in [f'"Reference" "{ref}"', f'reference "{ref}"']:
        idx = text.find(pattern)
        if idx >= 0:
            break
    if idx < 0:
        return None
    start = text.rfind('(footprint', 0, idx)
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

def get_courtyard_extent(block):
    """Get local courtyard bounding box from footprint block."""
    xs, ys = [], []
    # fp_line on CrtYd (single-line format)
    for m in re.finditer(r'\(fp_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\)[^)]*\(layer\s+"F\.CrtYd"\)', block):
        xs.extend([float(m.group(1)), float(m.group(3))])
        ys.extend([float(m.group(2)), float(m.group(4))])
    # fp_rect on CrtYd (multi-line KiCad 9 format)
    for m in re.finditer(r'\(fp_rect\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\).*?\(layer\s+"F\.CrtYd"\)', block, re.DOTALL):
        xs.extend([float(m.group(1)), float(m.group(3))])
        ys.extend([float(m.group(2)), float(m.group(4))])
    # fp_line on CrtYd (multi-line)
    for m in re.finditer(r'\(fp_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\).*?\(layer\s+"F\.CrtYd"\)', block, re.DOTALL):
        xs.extend([float(m.group(1)), float(m.group(3))])
        ys.extend([float(m.group(2)), float(m.group(4))])
    # fp_poly on CrtYd
    for m in re.finditer(r'\(fp_poly\s+\(pts\s+(.*?)\).*?\(layer\s+"F\.CrtYd"\)', block, re.DOTALL):
        for pm in re.finditer(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', m.group(1)):
            xs.append(float(pm.group(1)))
            ys.append(float(pm.group(2)))
    if xs:
        return (min(xs), min(ys), max(xs), max(ys))
    return None

def get_position(block):
    """Get position and rotation from footprint block."""
    m = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block)
    if m:
        x, y = float(m.group(1)), float(m.group(2))
        rot = float(m.group(3)) if m.group(3) else 0.0
        return x, y, rot
    return None

def rotate_bbox(local_bbox, rot_deg):
    """Rotate local bbox corners by rot_deg and return new AABB."""
    lx0, ly0, lx1, ly1 = local_bbox
    corners = [(lx0, ly0), (lx1, ly0), (lx0, ly1), (lx1, ly1)]
    rad = math.radians(rot_deg)
    rxs, rys = [], []
    for cx, cy in corners:
        rx = cx * math.cos(rad) - cy * math.sin(rad)
        ry = cx * math.sin(rad) + cy * math.cos(rad)
        rxs.append(rx)
        rys.append(ry)
    return (min(rxs), min(rys), max(rxs), max(rys))

with open(PCB) as f:
    text = f.read()

for ref in ['U1', 'U2', 'U14', 'U15']:
    block = extract_footprint_block(text, ref)
    if not block:
        print(f"{ref}: NOT FOUND")
        continue
    pos = get_position(block)
    local = get_courtyard_extent(block)
    if pos and local:
        x, y, rot = pos
        rotated = rotate_bbox(local, rot)
        world = (x + rotated[0], y + rotated[1], x + rotated[2], y + rotated[3])
        print(f"{ref} at ({x},{y},{rot}°):")
        print(f"  Local CrtYd: [{local[0]:.2f},{local[1]:.2f}] to [{local[2]:.2f},{local[3]:.2f}]")
        print(f"  World CrtYd: [{world[0]:.2f},{world[1]:.2f}] to [{world[2]:.2f},{world[3]:.2f}]")
    else:
        print(f"{ref} at {pos}: no courtyard found in block ({len(block)} chars)")
        # Check what layers exist
        layers = re.findall(r'\(layer\s+"([^"]+)"\)', block)
        crtyd = [l for l in layers if 'CrtYd' in l]
        print(f"  CrtYd layers found: {crtyd}")
