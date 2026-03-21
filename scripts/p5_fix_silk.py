#!/usr/bin/env python3
"""
Fix ALL remaining silk DRC violations.

1. silk_edge_clearance: Remove XLR connector silk segments past board edge
2. silk_over_copper: Move reference fields off pads
3. silk_overlap: Reposition overlapping reference fields

Reads DRC JSON to know exactly which items need fixing.
"""
import json, re, os, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
DRC_FILE = '/tmp/drc_final1.json'

with open(DRC_FILE) as f:
    drc = json.load(f)

with open(PCB_FILE) as f:
    text = f.read()

# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

def find_footprint_block(text, ref):
    for pattern in [f'(property "Reference" "{ref}"', f'fp_text reference "{ref}"']:
        idx = text.find(pattern)
        if idx >= 0: break
    else:
        return None, None
    depth = 0; start = idx
    while start > 0:
        if text[start] == ')': depth += 1
        elif text[start] == '(':
            depth -= 1
            if depth < 0 and ('(footprint ' in text[start:start+20] or '(footprint\n' in text[start:start+20]):
                break
        start -= 1
    depth = 0; end = start
    while end < len(text):
        if text[end] == '(': depth += 1
        elif text[end] == ')':
            depth -= 1
            if depth == 0: end += 1; break
        end += 1
    return start, end


def get_footprint_position(text, ref):
    start, end = find_footprint_block(text, ref)
    if start is None: return None
    block = text[start:end]
    m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    if m:
        return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)
    return None


# ────────────────────────────────────────────────────────────
# Fix 1: silk_edge_clearance — remove connector silk past edge
# ────────────────────────────────────────────────────────────

print("=== Fix silk_edge_clearance ===")

# Board bounds
board_left, board_top, board_right, board_bottom = 0, 0, 158, 200

# Identify connectors from DRC
edge_violations = [v for v in drc['violations'] if v['type'] == 'silk_edge_clearance']
edge_connector_refs = set()
for v in edge_violations:
    for it in v.get('items', []):
        d = it.get('description', '')
        m = re.search(r'of (\w+)', d)
        if m:
            ref = m.group(1)
            if ref.startswith('J') or ref.startswith('MH'):
                edge_connector_refs.add(ref)

print(f"  Connectors with silk past edge: {sorted(edge_connector_refs)}")

# For each connector, find silk segments and check if they extend past board edge
total_removed = 0
for ref in sorted(edge_connector_refs):
    start, end = find_footprint_block(text, ref)
    if start is None:
        continue
    block = text[start:end]
    
    fp_pos = get_footprint_position(text, ref)
    if fp_pos is None:
        continue
    fp_x, fp_y, fp_angle = fp_pos
    rad = math.radians(-fp_angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    
    # Find all fp_line segments on silk layers (both quoted and unquoted)
    silk_pattern = re.compile(
        r'\(fp_line\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s*'
        r'(?:\(stroke[^)]*\)\s*)?'
        r'\(layer\s+"?([FB]\.SilkS(?:creen)?)"?\)\s*'
        r'(?:\(uuid\s+"[^"]*"\)\s*)?'
        r'\(width\s+[\d.]+\)\s*\)')
    
    # Also try alternative ordering where layer comes after width
    silk_pattern2 = re.compile(
        r'\(fp_line\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s*'
        r'\(layer\s+"?([FB]\.SilkS(?:creen)?)"?\)\s*'
        r'\(width\s+[\d.]+\)\s*\)')
        
    segments_to_remove = []
    
    for pattern in [silk_pattern, silk_pattern2]:
        for m in pattern.finditer(block):
            sx, sy = float(m.group(1)), float(m.group(2))
            ex, ey = float(m.group(3)), float(m.group(4))
            
            # Rotate local coords to global
            gsx = fp_x + sx * cos_a - sy * sin_a
            gsy = fp_y + sx * sin_a + sy * cos_a
            gex = fp_x + ex * cos_a - ey * sin_a
            gey = fp_y + ex * sin_a + ey * cos_a
            
            margin = -0.1  # Slightly inside board edge counts
            if (gsx < board_left + margin or gsx > board_right - margin or
                gsy < board_top + margin or gsy > board_bottom - margin or
                gex < board_left + margin or gex > board_right - margin or
                gey < board_top + margin or gey > board_bottom - margin):
                segments_to_remove.append((m.start(), m.end(), m.group(0)[:50]))
    
    # Remove segments (reverse order to maintain indices)
    new_block = block
    for seg_start, seg_end, preview in sorted(segments_to_remove, reverse=True):
        new_block = new_block[:seg_start] + new_block[seg_end:]
        total_removed += 1
    
    if new_block != block:
        text = text[:start] + new_block + text[end:]

print(f"  Removed {total_removed} silk segments past board edge")

# If no segments were found via regex, let's try a simpler approach:
# Just find segments at the specific positions mentioned in DRC
if total_removed == 0:
    print("  Using position-based approach...")
    for v in edge_violations:
        for it in v.get('items', []):
            d = it.get('description', '')
            pos = it.get('pos', {})
            if 'Segment of' in d and pos:
                ref_m = re.search(r'of (\w+)', d)
                if ref_m:
                    ref = ref_m.group(1)
                    px, py = pos.get('x', 0), pos.get('y', 0)
                    # This segment is at a specific global position
                    # We need to find it in the footprint and remove it
                    # For now, just note it
                    print(f"    {ref}: silk at ({px:.1f}, {py:.1f}) past edge")


# ────────────────────────────────────────────────────────────
# Fix 2: silk_over_copper — move reference fields off pads
# ────────────────────────────────────────────────────────────

print("\n=== Fix silk_over_copper ===")

copper_violations = [v for v in drc['violations'] if v['type'] == 'silk_over_copper']
for v in copper_violations:
    for it in v.get('items', []):
        d = it.get('description', '')
        if 'Reference field' in d:
            ref_m = re.search(r'of (\w+)', d)
            if ref_m:
                ref = ref_m.group(1)
                # Move reference field away
                start, end = find_footprint_block(text, ref)
                if start is None: continue
                block = text[start:end]
                
                # Find reference field
                for pat in [f'(property "Reference" "{ref}"', f'(fp_text reference "{ref}"']:
                    prop_idx = block.find(pat)
                    if prop_idx >= 0: break
                else:
                    continue
                
                # Find the (at ...) within this property
                depth = 0; j = prop_idx
                while j < len(block):
                    if block[j] == '(': depth += 1
                    elif block[j] == ')':
                        depth -= 1
                        if depth == 0: break
                    j += 1
                prop_text = block[prop_idx:j+1]
                
                at_m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', prop_text)
                if at_m:
                    rx, ry = float(at_m.group(1)), float(at_m.group(2))
                    # Move 2mm upward (negative Y in local coords)
                    new_ry = ry - 2.0
                    new_prop = prop_text.replace(
                        f'(at {at_m.group(1)} {at_m.group(2)}',
                        f'(at {rx:.4f} {new_ry:.4f}')
                    # Replace in block, then in text
                    new_block = block[:prop_idx] + new_prop + block[j+1:]
                    text = text[:start] + new_block + text[end:]
                    print(f"  {ref}: moved ref y {ry:.1f} -> {new_ry:.1f}")


# ────────────────────────────────────────────────────────────
# Fix 3: silk_overlap — reposition overlapping reference fields
# ────────────────────────────────────────────────────────────

print("\n=== Fix silk_overlap ===")

overlap_violations = [v for v in drc['violations'] if v['type'] == 'silk_overlap']

# Collect all refs involved in overlaps, with their positions
overlap_refs = {}
for v in overlap_violations:
    items = v.get('items', [])
    for it in items:
        d = it.get('description', '')
        # Reference field of Xxx
        if 'Reference field' in d:
            ref_m = re.search(r'of (\w+)', d)
            if ref_m:
                ref = ref_m.group(1)
                pos = it.get('pos', {})
                overlap_refs.setdefault(ref, []).append(pos)
        # Footprint text of Xxx (${REFERENCE} or similar)
        elif 'Footprint text' in d:
            ref_m = re.search(r'of (\w+)', d)
            if ref_m:
                ref = ref_m.group(1)
                overlap_refs.setdefault(ref, []).append(it.get('pos', {}))

print(f"  {len(overlap_refs)} references involved in overlaps")

# For each overlapping reference, try to move it to a non-overlapping position
# Strategy: shift the reference field by small amounts until it doesn't overlap
# Simple approach: move reference 1.5mm in a direction based on its relative position

moved = 0
for ref in sorted(overlap_refs.keys()):
    start, end = find_footprint_block(text, ref)
    if start is None:
        continue
    block = text[start:end]
    
    # Find reference field
    for pat in [f'(property "Reference" "{ref}"', f'(fp_text reference "{ref}"']:
        prop_idx = block.find(pat)
        if prop_idx >= 0: break
    else:
        continue
    
    depth = 0; j = prop_idx
    while j < len(block):
        if block[j] == '(': depth += 1
        elif block[j] == ')':
            depth -= 1
            if depth == 0: break
        j += 1
    prop_text = block[prop_idx:j+1]
    
    at_m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', prop_text)
    if not at_m:
        continue
    
    rx, ry = float(at_m.group(1)), float(at_m.group(2))
    
    # Determine shift direction based on component type
    # For small components (R, C): shift Y by -1.5mm
    # For ICs (U): shift Y by -2mm
    # For connectors (J): shift Y by -2mm
    if ref.startswith('U'):
        shift_y = -2.0
    elif ref.startswith('J'):
        shift_y = -2.0
    elif ref.startswith('C') and ref != 'C79':
        shift_y = -1.5
    elif ref.startswith('R'):
        shift_y = -1.5
    elif ref.startswith('FB'):
        shift_y = -1.5
    else:
        shift_y = -1.5
    
    new_ry = ry + shift_y
    new_prop = prop_text.replace(
        f'(at {at_m.group(1)} {at_m.group(2)}',
        f'(at {rx:.4f} {new_ry:.4f}')
    new_block = block[:prop_idx] + new_prop + block[j+1:]
    text = text[:start] + new_block + text[end:]
    moved += 1

print(f"  Moved {moved} reference fields")


# ────────────────────────────────────────────────────────────
# Also fix U1 duplicate fp_text issue (Footprint text of U1 * overlaps itself)
# ────────────────────────────────────────────────────────────

# U1 has fp_text reference and fp_text user "${REFERENCE}" at the same position
# Move the user text slightly
start, end = find_footprint_block(text, 'U1')
if start is not None:
    block = text[start:end]
    # Find fp_text user "${REFERENCE}" and move it
    user_ref_idx = block.find('(fp_text user "${REFERENCE}"')
    if user_ref_idx >= 0:
        # Find its (at ...) and modify
        at_search = block[user_ref_idx:user_ref_idx+200]
        at_m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', at_search)
        if at_m:
            old_at = f'(at {at_m.group(1)} {at_m.group(2)}'
            new_at = f'(at {float(at_m.group(1)):.4f} {float(at_m.group(2)) + 2:.4f}'
            new_block = block[:user_ref_idx] + block[user_ref_idx:].replace(old_at, new_at, 1)
            text = text[:start] + new_block + text[end:]
            print(f"\n  U1: moved user ${{REFERENCE}} text to avoid self-overlap")


# ────────────────────────────────────────────────────────────
# Validate and write
# ────────────────────────────────────────────────────────────

depth = 0
for ch in text:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: depth={depth}"
print(f"\nBracket balance: OK")

with open(PCB_FILE, 'w') as f:
    f.write(text)
print(f"Written: {len(text)} bytes")
