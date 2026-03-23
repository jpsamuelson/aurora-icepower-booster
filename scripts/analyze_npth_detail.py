#!/usr/bin/env python3
"""Find NPTH pad positions in J2 with full detail."""
import re, math

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    c = f.read()

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

j2_idx = c.find('"Reference" "J2"')
fp_start = c.rfind('(footprint', 0, j2_idx)
fp_block, _ = extract_block(c, fp_start)

# Get footprint position
fp_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block[:500])
fx, fy = float(fp_at.group(1)), float(fp_at.group(2))
fa = float(fp_at.group(3)) if fp_at.group(3) else 0
print(f"J2: ({fx}, {fy}), angle={fa}")

rad = math.radians(-fa)

# Find ALL pads including NPTH
for pm in re.finditer(r'\(pad\b', fp_block):
    pad_block, _ = extract_block(fp_block, pm.start())
    if not pad_block:
        continue
    
    is_npth = 'np_thru_hole' in pad_block
    pad_name_m = re.search(r'\(pad\s+"([^"]*)"\s+(\w+)', pad_block)
    pad_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', pad_block)
    pad_size = re.search(r'\(size\s+([\d.-]+)\s+([\d.-]+)', pad_block)
    pad_drill = re.search(r'\(drill\s+([\d.-]+)', pad_block)
    
    if pad_at:
        lx = float(pad_at.group(1))
        ly = float(pad_at.group(2))
        rx = lx * math.cos(rad) - ly * math.sin(rad)
        ry = lx * math.sin(rad) + ly * math.cos(rad)
        ax = fx + rx
        ay = fy + ry
        
        name = pad_name_m.group(1) if pad_name_m else "?"
        ptype = pad_name_m.group(2) if pad_name_m else "?"
        size = f"{pad_size.group(1)}x{pad_size.group(2)}" if pad_size else "?"
        drill = pad_drill.group(1) if pad_drill else "none"
        
        marker = " <<< NPTH" if is_npth else ""
        print(f"  Pad '{name}' {ptype}: local=({lx}, {ly}) → abs=({ax:.3f}, {ay:.3f}) size={size} drill={drill}{marker}")
        
        if is_npth:
            drill_r = float(drill) / 2 if drill != "none" else 0
            clearance = 0.25  # board setup hole_clearance
            exclusion_r = drill_r + clearance
            print(f"    Drill radius: {drill_r}mm, exclusion zone radius: {exclusion_r}mm")
            print(f"    Traces must be at least {exclusion_r}mm from center ({ax:.3f}, {ay:.3f})")

# Show current trace path
print(f"\nCurrent REMOTE_IN trace Y=10.4436")
print(f"NPTH at (32.512, 10.239) → distance = {abs(10.4436 - 10.239):.3f}mm vertical")
print(f"With trace width 0.25mm, edge at Y={10.4436 + 0.125:.4f}")
print(f"Drill edge at Y={10.239 + 0.75:.3f} (drill=1.5mm)")
print(f"Minimum Y for trace center: {10.239 + 0.75 + 0.25 + 0.125:.4f}")
