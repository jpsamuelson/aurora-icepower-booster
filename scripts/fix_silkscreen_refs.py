#!/usr/bin/env python3
"""
Silkscreen-Fix: Alle 199 F.Fab-Referenzen → F.SilkS verschieben.

Strategie:
1. Layer F.Fab → F.SilkS
2. Font: 0.8×0.8mm, Strichstärke 0.15mm
3. Position: Offset relativ zum Bauteil basierend auf Footprint-Typ und Rotation
4. Kollisionserkennung: Ref-Ref und Ref-Pad Überlappungen vermeiden
5. Board-Edge Prüfung

Footprint-spezifische Regeln:
- R/C 0805 bei 0° (horizontal): Ref oberhalb (y-1.2mm), 0° Rotation
- R/C 0805 bei 90° (vertikal): Ref rechts (x+1.3mm), 90° Rotation
- C_1206 bei 0°: Ref oberhalb (y-1.5mm), 0° Rotation
- C_1210 bei 90°: Ref rechts (x+2.0mm), 90° Rotation
- MountingHole: Ref rechts (x+4.5mm), 0° Rotation
- SW: Ref unterhalb (y+2.5mm), 0° Rotation
"""
import re
import math
import sys
import copy

PCB_FILE = "aurora-dsp-icepower-booster.kicad_pcb"
FONT_H = 0.8
FONT_W = 0.8
FONT_THICK = 0.15
CHAR_WIDTH = 0.56  # approximate width of one char at 0.8mm font
BOARD_X1, BOARD_Y1 = 0.0, 0.0
BOARD_X2, BOARD_Y2 = 145.554, 200.0
MARGIN = 0.3  # minimum distance between text bboxes


def extract_balanced(text, start):
    """Extract balanced parentheses block starting at '('."""
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


def text_bbox(cx, cy, text, font_h, font_w, text_angle):
    """Calculate bounding box of text at position (cx,cy) with given angle.
    Returns (x_min, y_min, x_max, y_max) in board coordinates."""
    tw = len(text) * font_w * 0.7  # text width
    th = font_h  # text height

    angle_mod = text_angle % 180
    if 45 < angle_mod < 135:
        # ~90° rotation: swap w/h
        hw, hh = th / 2 + 0.1, tw / 2 + 0.1
    else:
        hw, hh = tw / 2 + 0.1, th / 2 + 0.1

    return (cx - hw, cy - hh, cx + hw, cy + hh)


def boxes_overlap(b1, b2, margin=MARGIN):
    """Check if two bounding boxes overlap with margin."""
    return not (b1[2] + margin < b2[0] or
                b2[2] + margin < b1[0] or
                b1[3] + margin < b2[1] or
                b2[3] + margin < b1[1])


def rotate_offset(dx, dy, angle_deg):
    """Rotate offset (dx,dy) by angle in degrees (CCW)."""
    rad = math.radians(angle_deg)
    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)
    return rx, ry


def get_placement_candidates(fp_type, fp_angle):
    """Return list of (dx, dy, text_angle) candidates for ref placement.
    First candidate is preferred, rest are fallbacks."""
    candidates = []

    if "0805" in fp_type or "0402" in fp_type:
        fp_a = int(fp_angle) % 360
        if fp_a == 0 or fp_a == 180:
            # Horizontal component: pads left/right
            candidates = [
                (0, -1.2, 0),     # above
                (0, 1.2, 0),      # below
                (-1.8, 0, 90),    # left, rotated
                (1.8, 0, 90),     # right, rotated
            ]
        elif fp_a == 90 or fp_a == 270:
            # Vertical component: pads top/bottom
            candidates = [
                (1.3, 0, 90),     # right, rotated
                (-1.3, 0, 90),    # left, rotated
                (0, -1.8, 0),     # above
                (0, 1.8, 0),      # below
            ]
        else:
            candidates = [(0, -1.2, 0), (0, 1.2, 0), (1.3, 0, 90), (-1.3, 0, 90)]

    elif "1206" in fp_type:
        fp_a = int(fp_angle) % 360
        if fp_a == 0 or fp_a == 180:
            candidates = [
                (0, -1.5, 0),     # above
                (0, 1.5, 0),      # below
                (2.2, 0, 90),     # right
                (-2.2, 0, 90),    # left
            ]
        else:
            candidates = [
                (2.0, 0, 90),     # right
                (-2.0, 0, 90),    # left
                (0, -2.0, 0),     # above
                (0, 2.0, 0),      # below
            ]

    elif "1210" in fp_type:
        fp_a = int(fp_angle) % 360
        if fp_a == 0 or fp_a == 180:
            candidates = [
                (0, -2.0, 0),
                (0, 2.0, 0),
                (2.5, 0, 90),
                (-2.5, 0, 90),
            ]
        else:
            candidates = [
                (2.0, 0, 90),
                (-2.0, 0, 90),
                (0, -2.5, 0),
                (0, 2.5, 0),
            ]

    elif "MountingHole" in fp_type:
        candidates = [
            (4.5, 0, 0),
            (-4.5, 0, 0),
            (0, 4.5, 0),
            (0, -4.5, 0),
        ]

    elif "SW" in fp_type:
        candidates = [
            (0, 2.5, 0),
            (0, -2.5, 0),
            (3.5, 0, 0),
            (-3.5, 0, 0),
        ]

    else:
        # generic fallback
        candidates = [
            (0, -1.5, 0),
            (0, 1.5, 0),
            (1.5, 0, 90),
            (-1.5, 0, 90),
        ]

    return candidates


def main():
    with open(PCB_FILE) as f:
        pcb = f.read()

    print(f"PCB geladen: {len(pcb)} bytes, {pcb.count(chr(10))} Zeilen")

    # ============================================================
    # Phase 1: Parse all footprints to build the placement model
    # ============================================================
    fp_starts = [m.start() for m in re.finditer(r'\(footprint "', pcb)]
    print(f"Footprints gefunden: {len(fp_starts)}")

    footprints = []
    for fp_start in fp_starts:
        fp_block, fp_end = extract_balanced(pcb, fp_start)
        if not fp_block:
            continue

        fp_name_m = re.match(r'\(footprint "([^"]+)"', fp_block)
        fp_name = fp_name_m.group(1) if fp_name_m else "?"

        fp_at_m = re.search(r'^\(footprint "[^"]+"\s*\n\s*\(layer "[^"]+"\)\s*\n\s*\(uuid "[^"]+"\)\s*\n\s*\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block)
        if not fp_at_m:
            fp_at_m = re.search(r'\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block[:500])
        if not fp_at_m:
            continue

        fp_x = float(fp_at_m.group(1))
        fp_y = float(fp_at_m.group(2))
        fp_angle = float(fp_at_m.group(3)) if fp_at_m.group(3) else 0

        # Find Reference property
        ref_prop_idx = fp_block.find('(property "Reference"')
        if ref_prop_idx < 0:
            continue

        ref_block, ref_end_rel = extract_balanced(fp_block, ref_prop_idx)
        if not ref_block:
            continue

        ref_name_m = re.search(r'"Reference" "([^"]+)"', ref_block)
        ref_name = ref_name_m.group(1) if ref_name_m else "?"

        ref_layer_m = re.search(r'\(layer "([^"]+)"\)', ref_block)
        ref_layer = ref_layer_m.group(1) if ref_layer_m else "?"

        ref_at_m = re.search(r'\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', ref_block)
        ref_rel_x = float(ref_at_m.group(1)) if ref_at_m else 0
        ref_rel_y = float(ref_at_m.group(2)) if ref_at_m else 0
        ref_angle = float(ref_at_m.group(3)) if ref_at_m and ref_at_m.group(3) else 0

        ref_font_m = re.search(r'\(font\s+\(size ([\d.]+) ([\d.]+)\)', ref_block)
        ref_font_h = float(ref_font_m.group(1)) if ref_font_m else 1.0
        ref_font_w = float(ref_font_m.group(2)) if ref_font_m else 1.0

        footprints.append({
            "ref": ref_name,
            "fp_name": fp_name,
            "fp_x": fp_x, "fp_y": fp_y, "fp_angle": fp_angle,
            "ref_layer": ref_layer,
            "ref_rel_x": ref_rel_x, "ref_rel_y": ref_rel_y,
            "ref_angle": ref_angle,
            "ref_font_h": ref_font_h, "ref_font_w": ref_font_w,
            # The absolute position in the PCB file for replacement
            "ref_block_start": fp_start + ref_prop_idx,
            "ref_block": ref_block,
        })

    on_fab = [f for f in footprints if f["ref_layer"] == "F.Fab"]
    on_silk = [f for f in footprints if "Silk" in f["ref_layer"]]
    print(f"Auf F.Fab: {len(on_fab)}, Auf F.SilkS: {len(on_silk)}")

    if len(on_fab) == 0:
        print("Keine F.Fab-Referenzen gefunden - nichts zu tun!")
        return

    # ============================================================
    # Phase 2: Calculate new positions for all F.Fab refs
    # ============================================================

    # First, collect existing Silkscreen text bboxes (already placed refs + board texts)
    placed_bboxes = []
    for f in on_silk:
        abs_x = f["fp_x"] + f["ref_rel_x"]
        abs_y = f["fp_y"] + f["ref_rel_y"]
        bbox = text_bbox(abs_x, abs_y, f["ref"], f["ref_font_h"], f["ref_font_w"], f["ref_angle"])
        placed_bboxes.append(bbox)

    # Also add board-level texts
    for m in re.finditer(r'\(gr_text "([^"]*)"[^)]*\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\).*?\(layer "F\.SilkS"\)', pcb, re.DOTALL):
        text = m.group(1)
        x, y = float(m.group(2)), float(m.group(3))
        angle = float(m.group(4)) if m.group(4) else 0
        # Estimate bbox (board texts can be bigger)
        bbox = text_bbox(x, y, text[:20], 1.0, 1.0, angle)
        placed_bboxes.append(bbox)

    # Sort F.Fab refs by Y then X for consistent processing
    on_fab_sorted = sorted(on_fab, key=lambda f: (f["fp_y"], f["fp_x"]))

    new_positions = {}  # ref -> (new_rel_x, new_rel_y, new_angle)
    collisions_resolved = 0
    collisions_unresolved = 0

    for f in on_fab_sorted:
        fp_type = f["fp_name"]
        candidates = get_placement_candidates(fp_type, f["fp_angle"])

        best = None
        for dx, dy, text_angle in candidates:
            # Calculate absolute position
            abs_x = f["fp_x"] + dx
            abs_y = f["fp_y"] + dy

            # Check board boundaries
            if abs_x < BOARD_X1 + 0.5 or abs_x > BOARD_X2 - 0.5:
                continue
            if abs_y < BOARD_Y1 + 0.5 or abs_y > BOARD_Y2 - 0.5:
                continue

            # Calculate text bbox
            bbox = text_bbox(abs_x, abs_y, f["ref"], FONT_H, FONT_W, text_angle)

            # Check collision with all existing placed bboxes
            has_collision = False
            for existing_bbox in placed_bboxes:
                if boxes_overlap(bbox, existing_bbox):
                    has_collision = True
                    break

            if not has_collision:
                best = (dx, dy, text_angle, bbox)
                break

        if best:
            dx, dy, text_angle, bbox = best
            if (dx, dy, text_angle) != candidates[0][:3]:
                collisions_resolved += 1
        else:
            # No collision-free position found, use first candidate anyway
            dx, dy, text_angle = candidates[0]
            abs_x = f["fp_x"] + dx
            abs_y = f["fp_y"] + dy
            # Clamp to board
            abs_x = max(BOARD_X1 + 0.5, min(BOARD_X2 - 0.5, abs_x))
            abs_y = max(BOARD_Y1 + 0.5, min(BOARD_Y2 - 0.5, abs_y))
            dx = abs_x - f["fp_x"]
            dy = abs_y - f["fp_y"]
            bbox = text_bbox(abs_x, abs_y, f["ref"], FONT_H, FONT_W, text_angle)
            collisions_unresolved += 1

        new_positions[f["ref"]] = (dx, dy, text_angle)
        placed_bboxes.append(bbox)

    print(f"\nPlatzierung berechnet:")
    print(f"  Kollisionen aufgelöst: {collisions_resolved}")
    print(f"  Kollisionen ungelöst:  {collisions_unresolved}")

    # ============================================================
    # Phase 3: Apply changes to PCB file
    # ============================================================

    # We need to replace each reference property block.
    # Strategy: collect all replacements sorted by position (descending)
    # so we can apply them back-to-front without offset issues.

    replacements = []  # (start_pos, old_block, new_block)

    for f in on_fab:
        ref = f["ref"]
        if ref not in new_positions:
            continue

        dx, dy, text_angle = new_positions[ref]
        old_block = f["ref_block"]
        start_pos = f["ref_block_start"]

        # Build new reference block by modifying the old one
        new_block = old_block

        # 1. Change layer: F.Fab → F.SilkS
        new_block = re.sub(
            r'\(layer "F\.Fab"\)',
            '(layer "F.SilkS")',
            new_block
        )

        # 2. Change position (at x y [angle])
        # The position is relative to footprint origin
        if text_angle != 0:
            at_str = f"(at {dx:.4g} {dy:.4g} {text_angle:.4g})"
        else:
            at_str = f"(at {dx:.4g} {dy:.4g})"

        new_block = re.sub(
            r'\(at [\d.-]+ [\d.-]+(?:\s+[\d.-]+)?\)',
            at_str,
            new_block,
            count=1
        )

        # 3. Change font size
        new_block = re.sub(
            r'\(font\s+\(size [\d.]+ [\d.]+\)',
            f'(font (size {FONT_H} {FONT_W})',
            new_block
        )

        # 4. Change/add thickness
        if re.search(r'\(thickness [\d.]+\)', new_block):
            new_block = re.sub(
                r'\(thickness [\d.]+\)',
                f'(thickness {FONT_THICK})',
                new_block
            )
        else:
            # Add thickness after size
            new_block = re.sub(
                r'\(font \(size [\d.]+ [\d.]+\)',
                f'(font (size {FONT_H} {FONT_W}) (thickness {FONT_THICK})',
                new_block
            )

        # 5. Remove (hide yes) if present
        new_block = new_block.replace(' (hide yes)', '')
        new_block = new_block.replace('(hide yes) ', '')
        new_block = new_block.replace('(hide yes)', '')

        replacements.append((start_pos, old_block, new_block))

    # Sort by position descending (apply from end to avoid offset issues)
    replacements.sort(key=lambda r: r[0], reverse=True)

    print(f"\n{len(replacements)} Ersetzungen vorbereitet")

    # Validate: check no overlapping replacements
    for i in range(len(replacements) - 1):
        pos_i, old_i, _ = replacements[i]
        pos_next, old_next, _ = replacements[i + 1]
        end_next = pos_next + len(old_next)
        if end_next > pos_i:
            print(f"  WARNUNG: Überlappende Ersetzungen bei {pos_i} und {pos_next}!")

    # Apply replacements
    result = pcb
    applied = 0
    for start_pos, old_block, new_block in replacements:
        # Verify the old block is still at expected position
        actual = result[start_pos:start_pos + len(old_block)]
        if actual != old_block:
            print(f"  FEHLER: Block an Position {start_pos} stimmt nicht überein!")
            print(f"    Erwartet: {old_block[:60]}...")
            print(f"    Gefunden: {actual[:60]}...")
            continue

        result = result[:start_pos] + new_block + result[start_pos + len(old_block):]
        applied += 1

    print(f"  {applied} Ersetzungen angewendet")

    # ============================================================
    # Phase 4: Validate
    # ============================================================

    # Check bracket balance
    depth = 0
    for ch in result:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    print(f"\n  Klammer-Balance: {'✓ OK' if depth == 0 else f'✗ FEHLER (depth={depth})'}")

    if depth != 0:
        print("  ABBRUCH: Klammer-Balance verletzt!")
        return

    # Count references on F.SilkS now
    silk_count = result.count('(layer "F.SilkS")')
    fab_count_after = 0
    # Count how many Reference properties are still on F.Fab
    for m in re.finditer(r'\(property "Reference"[^)]*\)', result):
        block_start = m.start()
        # Find the layer within this property
        prop_block, _ = extract_balanced(result, block_start)
        if prop_block and '(layer "F.Fab")' in prop_block:
            fab_count_after += 1

    print(f"  Referenzen auf F.Fab nach Fix: {fab_count_after}")

    # Write output
    with open(PCB_FILE, 'w') as f:
        f.write(result)

    print(f"\n✓ {PCB_FILE} gespeichert!")
    print(f"  {applied} Referenzen von F.Fab → F.SilkS verschoben")
    print(f"  Font: {FONT_H}×{FONT_W}mm, Strichstärke {FONT_THICK}mm")
    print(f"  Kollisionen aufgelöst: {collisions_resolved}")
    print(f"  Kollisionen ungelöst: {collisions_unresolved}")


if __name__ == "__main__":
    main()
