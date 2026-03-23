#!/usr/bin/env python3
"""Analyze U15 Pad1 GND disconnect — why can't the zone connect to this pad?"""
import re, math

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

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

# Find U15 footprint
u15_idx = content.find('"Reference" "U15"')
fp_start = content.rfind('(footprint', 0, u15_idx)
fp_block, fp_end = extract_block(content, fp_start)

# Get footprint position and angle
fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block[:500])
fx, fy = float(fp_at.group(1)), float(fp_at.group(2))
fa = float(fp_at.group(3)) if fp_at.group(3) else 0
print(f"U15 position: ({fx}, {fy}), angle: {fa}")

# Get footprint type
lib_match = re.search(r'\(footprint\s+"([^"]+)"', fp_block)
print(f"Footprint: {lib_match.group(1) if lib_match else '?'}")

# Find all pads
rad = math.radians(-fa) if fa != 0 else 0
print(f"\nPads:")
pad1_abs = None
for pm in re.finditer(r'\(pad\b', fp_block):
    pad_block, _ = extract_block(fp_block, pm.start())
    if not pad_block:
        continue
    
    pad_name_m = re.search(r'\(pad\s+"?([^"\s)]+)"?\s+(\w+)', pad_block)
    pad_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', pad_block)
    pad_size = re.search(r'\(size\s+([\d.-]+)\s+([\d.-]+)', pad_block)
    pad_net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"', pad_block)
    
    if pad_at:
        lx, ly = float(pad_at.group(1)), float(pad_at.group(2))
        if fa != 0:
            rx = lx * math.cos(rad) - ly * math.sin(rad)
            ry = lx * math.sin(rad) + ly * math.cos(rad)
        else:
            rx, ry = lx, ly
        ax, ay = fx + rx, fy + ry
        
        name = pad_name_m.group(1) if pad_name_m else "?"
        ptype = pad_name_m.group(2) if pad_name_m else "?"
        size = f"{pad_size.group(1)}x{pad_size.group(2)}" if pad_size else "?"
        net_id = int(pad_net.group(1)) if pad_net else -1
        net_name = pad_net.group(2) if pad_net else "none"
        
        # Check pad connection mode
        zone_connect = re.search(r'\(zone_connect\s+(\d+)\)', pad_block)
        zc = zone_connect.group(1) if zone_connect else "default"
        
        is_pad1 = name == "1"
        marker = "  <<<" if is_pad1 else ""
        print(f"  Pad {name} ({ptype}): abs=({ax:.3f}, {ay:.3f}) size={size} net={net_name}(id={net_id}) zone_connect={zc}{marker}")
        
        if is_pad1:
            pad1_abs = (ax, ay)
            pad1_size = (float(pad_size.group(1)), float(pad_size.group(2))) if pad_size else (0, 0)

if not pad1_abs:
    print("ERROR: Pad 1 not found!")
    exit(1)

px, py = pad1_abs
print(f"\n=== U15 Pad1 at ({px}, {py}), size={pad1_size} ===")

# Find all traces/vias/pads within 3mm radius that might block zone connection
print(f"\nNearby traces (within 3mm):")
for m in re.finditer(r'\(segment\b', content):
    block, _ = extract_block(content, m.start())
    if not block:
        continue
    s = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', block)
    e = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', block)
    net = re.search(r'\(net\s+(\d+)\)', block)
    layer = re.search(r'\(layer\s+"([^"]+)"', block)
    if s and e:
        sx, sy = float(s.group(1)), float(s.group(2))
        ex, ey = float(e.group(1)), float(e.group(2))
        # Check if any point of segment is within 3mm of pad1
        dist_s = math.sqrt((sx-px)**2 + (sy-py)**2)
        dist_e = math.sqrt((ex-px)**2 + (ey-py)**2)
        if dist_s < 3 or dist_e < 3:
            net_id = int(net.group(1)) if net else -1
            ly = layer.group(1) if layer else "?"
            print(f"  ({sx},{sy})→({ex},{ey}) net={net_id} [{ly}] dist={min(dist_s,dist_e):.2f}mm")

print(f"\nNearby vias (within 3mm):")
for m in re.finditer(r'\(via\b', content):
    block, _ = extract_block(content, m.start())
    if not block:
        continue
    at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)\)', block)
    net = re.search(r'\(net\s+(\d+)\)', block)
    if at:
        vx, vy = float(at.group(1)), float(at.group(2))
        dist = math.sqrt((vx-px)**2 + (vy-py)**2)
        if dist < 3:
            net_id = int(net.group(1)) if net else -1
            print(f"  Via at ({vx},{vy}) net={net_id} dist={dist:.2f}mm")

# Check zone connection mode for GND zones
print(f"\nGND Zone settings:")
for m in re.finditer(r'\(zone\b', content):
    block, end = extract_block(content, m.start())
    if not block:
        continue
    if '(net 134)' not in block and '"GND"' not in block:
        continue
    
    connect = re.search(r'\(connect_pads\s*(\w*)', block)
    thermal_width = re.search(r'\(thermal_width\s+([\d.]+)\)', block)
    thermal_gap = re.search(r'\(thermal_gap\s+([\d.]+)\)', block)
    min_thickness = re.search(r'\(min_thickness\s+([\d.]+)\)', block)
    layer = re.search(r'\(layer\s+"([^"]+)"', block)
    
    connect_mode = connect.group(1) if connect and connect.group(1) else "thermal_relief(default)"
    tw = thermal_width.group(1) if thermal_width else "?"
    tg = thermal_gap.group(1) if thermal_gap else "?"
    mt = min_thickness.group(1) if min_thickness else "?"
    ly = layer.group(1) if layer else "?"
    
    print(f"  [{ly}] connect_pads={connect_mode} thermal_width={tw} thermal_gap={tg} min_thickness={mt}")
