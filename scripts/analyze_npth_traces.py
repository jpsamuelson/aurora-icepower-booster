#!/usr/bin/env python3
"""Analyze J2 NPTH position and REMOTE_IN trace geometry to plan reroute."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

def extract_block(text, start):
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
        i += 1
    return None, start

# Find J2 footprint and its NPTH pads
print("=== J2 FOOTPRINT ANALYSIS ===")
j2_match = re.search(r'\(footprint\b[^)]*\n[^)]*"Reference"\s+"J2"', content)
if not j2_match:
    # Try finding J2 reference differently
    j2_idx = content.find('"Reference" "J2"')
    if j2_idx >= 0:
        # Walk back to find footprint start
        fp_start = content.rfind('(footprint', 0, j2_idx)
        if fp_start >= 0:
            fp_block, fp_end = extract_block(content, fp_start)
            
            # Get footprint position
            fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block[:500])
            if fp_at:
                fx = float(fp_at.group(1))
                fy = float(fp_at.group(2))
                fa = float(fp_at.group(3)) if fp_at.group(3) else 0
                print(f"J2 position: ({fx}, {fy}), angle: {fa}")
            
            # Find all pads
            for pm in re.finditer(r'\(pad\b', fp_block):
                pad_block, _ = extract_block(fp_block, pm.start())
                if pad_block:
                    pad_type = re.search(r'\(pad\s+"?([^"\s)]+)"?\s+(\w+)', pad_block)
                    pad_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', pad_block)
                    pad_size = re.search(r'\(size\s+([\d.-]+)\s+([\d.-]+)', pad_block)
                    pad_drill = re.search(r'\(drill\s+([\d.-]+)', pad_block)
                    pad_net = re.search(r'\(net\s+\d+\s+"([^"]*)"', pad_block)
                    
                    if pad_type and pad_at:
                        name = pad_type.group(1)
                        ptype = pad_type.group(2)
                        lx = float(pad_at.group(1))
                        ly = float(pad_at.group(2))
                        size = f"{pad_size.group(1)}x{pad_size.group(2)}" if pad_size else "?"
                        drill = pad_drill.group(1) if pad_drill else "none"
                        net = pad_net.group(1) if pad_net else "no net"
                        
                        import math
                        rad = math.radians(-fa)
                        rx = lx * math.cos(rad) - ly * math.sin(rad)
                        ry = lx * math.sin(rad) + ly * math.cos(rad)
                        ax = fx + rx
                        ay = fy + ry
                        
                        is_npth = "np_thru_hole" in pad_block
                        marker = " *** NPTH ***" if is_npth else ""
                        print(f"  Pad {name} ({ptype}): local=({lx}, {ly}) abs=({ax:.3f}, {ay:.3f}) size={size} drill={drill} net={net}{marker}")

# Find REMOTE_IN traces
print("\n=== REMOTE_IN TRACES ===")
remote_in_net = 130
segment_pattern = re.compile(r'\(segment\b')
remote_segments = []

for m in segment_pattern.finditer(content):
    block, end = extract_block(content, m.start())
    if block and f'(net {remote_in_net})' in block:
        start_match = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', block)
        end_match = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', block)
        width_match = re.search(r'\(width\s+([\d.-]+)\)', block)
        layer_match = re.search(r'\(layer\s+"([^"]+)"\)', block)
        
        if start_match and end_match:
            sx, sy = float(start_match.group(1)), float(start_match.group(2))
            ex, ey = float(end_match.group(1)), float(end_match.group(2))
            w = float(width_match.group(1)) if width_match else 0
            layer = layer_match.group(1) if layer_match else "?"
            
            remote_segments.append({
                'sx': sx, 'sy': sy, 'ex': ex, 'ey': ey,
                'w': w, 'layer': layer, 'block': block, 'offset': m.start()
            })
            print(f"  ({sx}, {sy}) → ({ex}, {ey}) w={w} [{layer}]")

# Find REMOTE_IN vias
print("\n=== REMOTE_IN VIAS ===")
for m in re.finditer(r'\(via\b', content):
    block, end = extract_block(content, m.start())
    if block and f'(net {remote_in_net})' in block:
        at_match = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)\)', block)
        if at_match:
            x, y = float(at_match.group(1)), float(at_match.group(2))
            print(f"  Via at ({x}, {y})")

# Calculate clearance needed
print("\n=== CLEARANCE ANALYSIS ===")
# NPTH position will be determined above
# The traces at Y=10.4436 need to clear the NPTH
# Minimum hole_clearance is 0.25mm
# Need to know NPTH diameter to calculate safe route
