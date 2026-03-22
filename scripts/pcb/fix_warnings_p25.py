#!/usr/bin/env python3
"""
Phase 2: XLR Silk-Segmente kürzen die über Board-Edge ragen.
Phase 5: Duplikat fp_text user "*" in U1 entfernen.

Board-Edge: x_max = 145.054mm
XLR Connectors J9-J14 sind 90° rotiert, ihre Silk-Linien ragen bis x ≈ 145.66mm

Strategie:
- Alle fp_line auf F.SilkS in J9-J14 Footprints finden
- Lokale Koordinaten → globale Koordinaten berechnen (inkl. 90° Rotation)
- Segmente die über x=144.754 (Board-Edge - 0.3mm) ragen: Endpunkte clippen
- U1: Zweites fp_text user "*" bei (0, -10.837334) auf F.SilkS entfernen
"""
import re, math

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

BOARD_EDGE_X = 145.054
SILK_MARGIN = 0.3  # mm von Board-Edge
CLIP_X = BOARD_EDGE_X - SILK_MARGIN  # 144.754mm

def rotate_point(lx, ly, angle_deg):
    """Rotate local point by angle (degrees CCW) around origin."""
    a = math.radians(angle_deg)
    gx = lx * math.cos(a) - ly * math.sin(a)
    gy = lx * math.sin(a) + ly * math.cos(a)
    return gx, gy

def local_to_global(lx, ly, fp_x, fp_y, fp_angle):
    """Convert footprint-local coords to global PCB coords."""
    rx, ry = rotate_point(lx, ly, -fp_angle)  # KiCad rotiert CW
    return fp_x + rx, fp_y + ry

def global_to_local(gx, gy, fp_x, fp_y, fp_angle):
    """Convert global PCB coords to footprint-local coords."""
    dx, dy = gx - fp_x, gy - fp_y
    rx, ry = rotate_point(dx, dy, fp_angle)  # Rückrotation
    return rx, ry

# ── Finde XLR Connector Footprints (J9-J14) ──
# Pattern: (footprint "Jack_XLR..." (at X Y 90)) mit Reference J9-J14
xlr_refs = ['J9', 'J10', 'J11', 'J12', 'J13', 'J14']

# Parse footprint positions
fp_positions = {}
for ref in xlr_refs:
    pattern = rf'\(property "Reference" "{ref}"'
    m = re.search(pattern, content)
    if not m:
        continue
    # Go backwards to find the footprint (at X Y angle)
    start = content.rfind('(footprint', 0, m.start())
    fp_block_start = content[start:m.start()]
    at_m = re.search(r'\(at\s+([\d.+-]+)\s+([\d.+-]+)(?:\s+([\d.+-]+))?\)', fp_block_start)
    if at_m:
        fp_x = float(at_m.group(1))
        fp_y = float(at_m.group(2))
        fp_a = float(at_m.group(3)) if at_m.group(3) else 0.0
        fp_positions[ref] = (fp_x, fp_y, fp_a)

print("XLR Connector Positionen:")
for ref, (x, y, a) in fp_positions.items():
    print(f"  {ref}: ({x}, {y}, {a}°)")

# ── Clippe Silk-Linien die über CLIP_X ragen ──
# Arbeite Footprint für Footprint
clipped_count = 0

for ref in xlr_refs:
    if ref not in fp_positions:
        continue
    fp_x, fp_y, fp_a = fp_positions[ref]
    
    # Finde den Footprint-Block
    ref_pattern = rf'\(property "Reference" "{ref}"'
    ref_m = re.search(ref_pattern, content)
    if not ref_m:
        continue
    
    # Finde Footprint-Start
    fp_start = content.rfind('(footprint', 0, ref_m.start())
    # Finde Footprint-Ende (balanced parens)
    depth = 0
    fp_end = fp_start
    for i in range(fp_start, len(content)):
        if content[i] == '(': depth += 1
        elif content[i] == ')': depth -= 1
        if depth == 0:
            fp_end = i + 1
            break
    
    fp_block = content[fp_start:fp_end]
    new_fp_block = fp_block
    
    # Finde alle fp_line auf SilkS in diesem Block
    for line_m in re.finditer(
        r'(\(fp_line\s*\n\s*\(start\s+([\d.+-]+)\s+([\d.+-]+)\)\s*\n\s*\(end\s+([\d.+-]+)\s+([\d.+-]+)\)\s*\n\s*\(stroke\s*\n\s*\(width\s+[\d.]+\)\s*\n\s*\(type\s+\w+\)\s*\)\s*\n\s*\(layer\s+"F\.SilkS"\)\s*\n\s*\(uuid\s+"[^"]+"\)\s*\))',
        new_fp_block
    ):
        sx, sy = float(line_m.group(2)), float(line_m.group(3))
        ex, ey = float(line_m.group(4)), float(line_m.group(5))
        
        # Convert to global
        gsx, gsy = local_to_global(sx, sy, fp_x, fp_y, fp_a)
        gex, gey = local_to_global(ex, ey, fp_x, fp_y, fp_a)
        
        # Check if either endpoint exceeds CLIP_X
        if gsx <= CLIP_X and gex <= CLIP_X:
            continue  # Both within bounds
        
        if gsx > CLIP_X and gex > CLIP_X:
            # Both out — remove this line entirely (replace with empty)
            new_fp_block = new_fp_block.replace(line_m.group(0), '', 1)
            clipped_count += 1
            continue
        
        # One in, one out — clip the out-of-bounds endpoint
        if gsx > CLIP_X:
            # Clip start point
            if abs(gex - gsx) > 0.001:
                t = (CLIP_X - gex) / (gsx - gex)
                new_gx = CLIP_X
                new_gy = gey + t * (gsy - gey)
            else:
                new_gx = CLIP_X
                new_gy = gsy
            new_lx, new_ly = global_to_local(new_gx, new_gy, fp_x, fp_y, fp_a)
            old_start = f'(start {sx} {sy})'
            new_start = f'(start {new_lx:.6f} {new_ly:.6f})'
            new_fp_block = new_fp_block.replace(
                line_m.group(0),
                line_m.group(0).replace(old_start, new_start),
                1
            )
            clipped_count += 1
        elif gex > CLIP_X:
            # Clip end point
            if abs(gsx - gex) > 0.001:
                t = (CLIP_X - gsx) / (gex - gsx)
                new_gx = CLIP_X
                new_gy = gsy + t * (gey - gsy)
            else:
                new_gx = CLIP_X
                new_gy = gey
            new_lx, new_ly = global_to_local(new_gx, new_gy, fp_x, fp_y, fp_a)
            old_end = f'(end {ex} {ey})'
            new_end = f'(end {new_lx:.6f} {new_ly:.6f})'
            new_fp_block = new_fp_block.replace(
                line_m.group(0),
                line_m.group(0).replace(old_end, new_end),
                1
            )
            clipped_count += 1
    
    content = content[:fp_start] + new_fp_block + content[fp_end:]

print(f"\nPhase 2: {clipped_count} Silk-Segmente geclippt")

# ── Phase 5: U1 Duplikat fp_text user "*" entfernen ──
# Suche den U1 Footprint-Block
u1_ref_m = re.search(r'\(property "Reference" "U1"', content)
if u1_ref_m:
    u1_fp_start = content.rfind('(footprint', 0, u1_ref_m.start())
    depth = 0
    u1_fp_end = u1_fp_start
    for i in range(u1_fp_start, len(content)):
        if content[i] == '(': depth += 1
        elif content[i] == ')': depth -= 1
        if depth == 0:
            u1_fp_end = i + 1
            break
    
    u1_block = content[u1_fp_start:u1_fp_end]
    
    # Finde alle fp_text user "*" auf F.SilkS bei (0, -10.837334)
    star_pattern = r'(\(fp_text user "\*"\s*\n\s*\(at 0 -10\.837334 0\)\s*\n\s*(?:\(unlocked yes\)\s*\n\s*)?\(layer "F\.SilkS"\)\s*\n\s*\(uuid "[^"]+"\)\s*\n\s*\(effects\s*\n\s*\(font\s*\n\s*\(size 1 1\)\s*\n\s*\(thickness 0\.15\)\s*\n\s*\)\s*\n\s*\)\s*\n\s*\))'
    
    star_matches = list(re.finditer(star_pattern, u1_block))
    if len(star_matches) >= 2:
        # Entferne das zweite Duplikat
        second = star_matches[1]
        u1_block = u1_block[:second.start()] + u1_block[second.end():]
        print(f"Phase 5: U1 Duplikat fp_text '*' entfernt")
    else:
        print(f"Phase 5: Nur {len(star_matches)} fp_text '*' bei (-10.837) gefunden, kein Duplikat")
    
    content = content[:u1_fp_start] + u1_block + content[u1_fp_end:]

# ── Bracket balance ──
depth_check = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
if depth_check != 0:
    print(f"❌ Bracket balance: {depth_check}")
    import sys; sys.exit(1)
print("Bracket balance: OK")

with open(PCB, 'w') as f:
    f.write(content)
print(f"\n✅ Gespeichert: {len(content):,} bytes")
