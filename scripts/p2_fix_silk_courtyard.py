#!/usr/bin/env python3
"""
Fix all silk and courtyard DRC violations.

1. silk_overlap: Reposition reference fields that overlap other silk
2. silk_edge_clearance: Remove/shorten connector silk segments past board edge
3. silk_over_copper: Move reference fields off pads
4. courtyards_overlap: Move C18/C79 away from U1

Strategy:
- Parse DRC JSON to get all violations
- For each violation, determine the fix (move ref, shorten silk, etc.)
- Apply fixes to PCB text
"""
import json, re, os, sys, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
DRC_FILE = '/tmp/drc_nosuppress.json'

with open(DRC_FILE) as f:
    drc = json.load(f)

with open(PCB_FILE) as f:
    text = f.read()

# ────────────────────────────────────────────────────────────
# Helper: Extract footprint blocks
# ────────────────────────────────────────────────────────────

def find_footprint_block(text, ref):
    """Find the footprint block for a given reference, return (start, end) indices."""
    # Try new property format first
    pattern = f'(property "Reference" "{ref}"'
    idx = text.find(pattern)
    # Try old fp_text format
    if idx < 0:
        pattern = f'fp_text reference "{ref}"'
        idx = text.find(pattern)
    if idx < 0:
        return None, None
    # Walk backwards to find the opening (footprint
    depth = 0
    start = idx
    while start > 0:
        if text[start] == ')':
            depth += 1
        elif text[start] == '(':
            depth -= 1
            if depth < 0:
                after = text[start:start+20]
                if '(footprint ' in after or '(footprint\n' in after:
                    break
        start -= 1
    # Walk forward from start to find matching close
    depth = 0
    end = start
    while end < len(text):
        if text[end] == '(':
            depth += 1
        elif text[end] == ')':
            depth -= 1
            if depth == 0:
                end += 1
                break
        end += 1
    return start, end


def get_footprint_position(text, ref):
    """Get (x, y, angle) of a footprint."""
    start, end = find_footprint_block(text, ref)
    if start is None:
        return None
    block = text[start:end]
    # First (at ...) in footprint is its position
    m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    if m:
        x, y = float(m.group(1)), float(m.group(2))
        angle = float(m.group(3)) if m.group(3) else 0
        return (x, y, angle)
    return None


def get_ref_field_in_footprint(text, ref):
    """Find the Reference field property within a footprint and return its text range."""
    start, end = find_footprint_block(text, ref)
    if start is None:
        return None, None, None
    block = text[start:end]
    # Try new format: (property "Reference" "..." ...)
    prop_idx = block.find(f'(property "Reference" "{ref}"')
    if prop_idx < 0:
        # Try old format: (fp_text reference "..." ...)
        prop_idx = block.find(f'(fp_text reference "{ref}"')
    if prop_idx < 0:
        return None, None, None
    # Find balanced end of this property
    depth = 0
    j = prop_idx
    while j < len(block):
        if block[j] == '(':
            depth += 1
        elif block[j] == ')':
            depth -= 1
            if depth == 0:
                break
        j += 1
    prop_text = block[prop_idx:j+1]
    abs_start = start + prop_idx
    abs_end = start + j + 1
    return abs_start, abs_end, prop_text


# ────────────────────────────────────────────────────────────
# Fix 1: silk_edge_clearance — connector silk past board edge
# ────────────────────────────────────────────────────────────

print("=== Fix silk_edge_clearance ===")

# The XLR connectors (J1, J3-J8) have silk segments extending past the board edge.
# These are graphical segments inside the footprint blocks.
# Fix: Find these segments and remove them (they're beyond the board edge anyway).

# Also: Reference fields of U14, MH1, MH2 near edge - move them inward.

edge_violations = [v for v in drc['violations'] if v['type'] == 'silk_edge_clearance']
edge_refs = set()
edge_mh_refs = set()
for v in edge_violations:
    for it in v.get('items', []):
        d = it.get('description', '')
        m = re.search(r'of (\w+)', d)
        if m:
            ref = m.group(1)
            if ref.startswith('J'):
                edge_refs.add(ref)
            elif ref.startswith('MH') or ref.startswith('U'):
                edge_mh_refs.add(ref)

# For XLR connectors: find and remove silk segments that extend past the board edge
# Board outline is on Edge.Cuts layer - get its bounds
# Get board outline bounds
edge_cuts_lines = re.findall(r'\(gr_rect\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)', text)
board_left = board_top = float('inf')
board_right = board_bottom = float('-inf')
for m in edge_cuts_lines:
    x1, y1, x2, y2 = float(m[0]), float(m[1]), float(m[2]), float(m[3])
    board_left = min(board_left, x1, x2)
    board_right = max(board_right, x1, x2)
    board_top = min(board_top, y1, y2)
    board_bottom = max(board_bottom, y1, y2)

print(f"Board bounds: ({board_left}, {board_top}) - ({board_right}, {board_bottom})")

# For each XLR connector footprint, find silk segments that go past the edge
silk_removed = 0
for ref in sorted(edge_refs):
    start, end = find_footprint_block(text, ref)
    if start is None:
        print(f"  WARNING: {ref} not found")
        continue
    
    block = text[start:end]
    fp_pos = get_footprint_position(text, ref)
    if fp_pos is None:
        continue
    
    # Find all fp_line segments on F.SilkS layer within this footprint
    # We need to identify segments that extend past the board edge
    # The segment positions are relative to the footprint's position and rotation
    # For simplicity, we'll look for segments on the silk layer and check if
    # any coordinate (after rotation) extends past the board edge
    
    # Remove fp_line segments on F.SilkS/B.SilkS that are at the board edge
    # These are typically the connector outline segments
    new_block = block
    fp_x, fp_y, fp_angle = fp_pos
    
    # Find all silk segments in this footprint (both quoted and unquoted layer names)
    silk_segs = list(re.finditer(
        r'\(fp_line\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)'
        r'[^)]*\(layer\s+"?[FB]\.SilkS(?:creen)?"?\)[^)]*\)',
        new_block))
    
    for seg_m in reversed(silk_segs):
        # Convert local coords to global
        sx, sy = float(seg_m.group(1)), float(seg_m.group(2))
        ex, ey = float(seg_m.group(3)), float(seg_m.group(4))
        
        # Rotate
        rad = math.radians(-fp_angle)  # KiCad rotation is CW positive
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        
        gsx = fp_x + sx * cos_a - sy * sin_a
        gsy = fp_y + sx * sin_a + sy * cos_a
        gex = fp_x + ex * cos_a - ey * sin_a
        gey = fp_y + ex * sin_a + ey * cos_a
        
        # Check if either endpoint is past board edge (with 0.1mm margin)
        margin = 0.1
        if (gsx < board_left - margin or gsx > board_right + margin or 
            gsy < board_top - margin or gsy > board_bottom + margin or
            gex < board_left - margin or gex > board_right + margin or
            gey < board_top - margin or gey > board_bottom + margin):
            # Remove this segment
            new_block = new_block[:seg_m.start()] + new_block[seg_m.end():]
            silk_removed += 1
    
    if new_block != block:
        text = text[:start] + new_block + text[end:]

print(f"  Removed {silk_removed} silk segments past board edge")

# Move reference fields for MH1, MH2, U14 away from edge
for ref in sorted(edge_mh_refs):
    abs_start, abs_end, prop_text = get_ref_field_in_footprint(text, ref)
    if abs_start is None:
        continue
    
    # Parse current position
    at_m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', prop_text)
    if at_m:
        rx, ry = float(at_m.group(1)), float(at_m.group(2))
        # Get footprint position
        fp_pos = get_footprint_position(text, ref)
        if fp_pos:
            fx, fy, _ = fp_pos
            # Move reference 2mm inward from edge (towards board center)
            new_rx = rx
            new_ry = ry
            global_rx = fx + rx
            global_ry = fy + ry
            if global_rx < board_left + 1:
                new_rx = rx + 2
            if global_rx > board_right - 1:
                new_rx = rx - 2
            if global_ry < board_top + 1:
                new_ry = ry + 2
            if global_ry > board_bottom - 1:
                new_ry = ry - 2
            
            if new_rx != rx or new_ry != ry:
                new_prop = prop_text.replace(
                    f'(at {at_m.group(1)} {at_m.group(2)}',
                    f'(at {new_rx:.4f} {new_ry:.4f}'
                )
                text = text[:abs_start] + new_prop + text[abs_end:]
                print(f"  {ref}: moved ref ({rx},{ry}) -> ({new_rx:.1f},{new_ry:.1f})")

# ────────────────────────────────────────────────────────────
# Fix 2: silk_over_copper — reference fields on pads
# ────────────────────────────────────────────────────────────

print("\n=== Fix silk_over_copper ===")

silk_copper_violations = [v for v in drc['violations'] if v['type'] == 'silk_over_copper']
copper_refs = set()
copper_segments = 0
for v in silk_copper_violations:
    for it in v.get('items', []):
        d = it.get('description', '')
        if 'Reference field' in d:
            m = re.search(r'of (\w+)', d)
            if m:
                copper_refs.add(m.group(1))
        elif 'Segment of' in d:
            copper_segments += 1

print(f"  Reference fields on copper: {sorted(copper_refs)}")
print(f"  Silk segments on copper: {copper_segments}")

# Move reference fields off pads by shifting them
for ref in sorted(copper_refs):
    abs_start, abs_end, prop_text = get_ref_field_in_footprint(text, ref)
    if abs_start is None:
        print(f"  WARNING: {ref} ref field not found")
        continue
    
    at_m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', prop_text)
    if at_m:
        rx, ry = float(at_m.group(1)), float(at_m.group(2))
        # Move the reference 1.5mm away from center (upward in local coords)
        new_ry = ry - 1.5
        new_prop = prop_text.replace(
            f'(at {at_m.group(1)} {at_m.group(2)}',
            f'(at {rx:.4f} {new_ry:.4f}'
        )
        text = text[:abs_start] + new_prop + text[abs_end:]
        print(f"  {ref}: moved ref y {ry} -> {new_ry:.1f}")


# ────────────────────────────────────────────────────────────
# Fix 3: courtyards_overlap — C18/C79 vs U1
# ────────────────────────────────────────────────────────────

print("\n=== Fix courtyards_overlap ===")

# C18 and C79 overlap with U1 (the TEL5 DC-DC converter)
# Need to check current positions and move caps slightly
for cap_ref in ['C18', 'C79']:
    fp_pos = get_footprint_position(text, cap_ref)
    u1_pos = get_footprint_position(text, 'U1')
    if fp_pos and u1_pos:
        print(f"  {cap_ref}: at ({fp_pos[0]}, {fp_pos[1]}), U1 at ({u1_pos[0]}, {u1_pos[1]})")
        
        # Calculate direction away from U1
        dx = fp_pos[0] - u1_pos[0]
        dy = fp_pos[1] - u1_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            # Move 0.5mm away from U1
            move_x = (dx / dist) * 0.5
            move_y = (dy / dist) * 0.5
            new_x = fp_pos[0] + move_x
            new_y = fp_pos[1] + move_y
            
            start, end = find_footprint_block(text, cap_ref)
            if start is not None:
                block = text[start:end]
                # Find first (at ...) which is the footprint position
                first_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
                if first_at:
                    old_at = first_at.group(0)
                    angle_str = f' {first_at.group(3)}' if first_at.group(3) else ''
                    new_at = f'(at {new_x:.4f} {new_y:.4f}{angle_str})'
                    new_block = block.replace(old_at, new_at, 1)
                    text = text[:start] + new_block + text[end:]
                    print(f"  {cap_ref}: moved ({fp_pos[0]:.1f},{fp_pos[1]:.1f}) -> ({new_x:.1f},{new_y:.1f})")


# ────────────────────────────────────────────────────────────
# Validate and write
# ────────────────────────────────────────────────────────────

depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: depth={depth}"
print(f"\nBracket balance: OK")

with open(PCB_FILE, 'w') as f:
    f.write(text)
print(f"Written: {len(text)} bytes")
