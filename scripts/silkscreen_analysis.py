#!/usr/bin/env python3
"""
Silkscreen-Analyse: Welche Bauteil-Referenzen sind sichtbar/versteckt?
Analysiert Positionen, Größen, Überlappungen und Layer.
"""
import re, math, json
from collections import defaultdict, Counter

PCB = "aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    pcb = f.read()

# ============================================================
# 1. Parse ALL footprints with their reference properties
# ============================================================

# We need to parse each footprint block carefully
# Strategy: find each footprint, then find its reference property

def extract_balanced(text, start):
    """Extract balanced parentheses block starting at position start (which should be '(')."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
        i += 1
    return None

footprints = []

# Find all footprint starts
fp_starts = [m.start() for m in re.finditer(r'\(footprint "', pcb)]

for fp_start in fp_starts:
    fp_block = extract_balanced(pcb, fp_start)
    if not fp_block:
        continue

    # Footprint name
    fp_name_m = re.match(r'\(footprint "([^"]+)"', fp_block)
    fp_name = fp_name_m.group(1) if fp_name_m else "?"

    # Footprint position
    fp_at_m = re.search(r'^\(footprint "[^"]+"\s+\(layer "[^"]+"\)\s+\(uuid "[^"]+"\)\s+\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block)
    if not fp_at_m:
        # Try alternate parse
        fp_at_m = re.search(r'\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block)
    
    fp_x = float(fp_at_m.group(1)) if fp_at_m else 0
    fp_y = float(fp_at_m.group(2)) if fp_at_m else 0
    fp_angle = float(fp_at_m.group(3)) if fp_at_m and fp_at_m.group(3) else 0

    # Footprint layer
    fp_layer_m = re.search(r'\(layer "([^"]+)"\)', fp_block[:200])
    fp_layer = fp_layer_m.group(1) if fp_layer_m else "?"

    # Reference property
    ref_m = re.search(r'\(property "Reference" "([^"]+)"(.*?)\)\s*\(property', fp_block, re.DOTALL)
    if not ref_m:
        # Try to find it without lookahead
        ref_m = re.search(r'\(property "Reference" "([^"]+)"[^)]*\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)[^)]*\(layer "([^"]+)"\)', fp_block)
    
    ref_name = "?"
    ref_x, ref_y, ref_angle = fp_x, fp_y, 0
    ref_layer = "F.Silkscreen"
    ref_hidden = False
    ref_font_h = 1.0
    ref_font_w = 1.0
    ref_thickness = 0.15
    
    if ref_m:
        ref_name = ref_m.group(1)
        # Parse the full reference property block
        # Find the property block start
        ref_prop_start = fp_block.find(f'(property "Reference" "{ref_name}"')
        if ref_prop_start >= 0:
            ref_prop_block = extract_balanced(fp_block, ref_prop_start)
            if ref_prop_block:
                # Position (relative to footprint)
                at_m = re.search(r'\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', ref_prop_block)
                if at_m:
                    ref_x = float(at_m.group(1))
                    ref_y = float(at_m.group(2))
                    ref_angle = float(at_m.group(3)) if at_m.group(3) else 0

                # Layer
                layer_m = re.search(r'\(layer "([^"]+)"\)', ref_prop_block)
                if layer_m:
                    ref_layer = layer_m.group(1)

                # Hidden?
                ref_hidden = 'hide yes' in ref_prop_block or '(hide yes)' in ref_prop_block

                # Font size
                font_m = re.search(r'\(font\s+\(size ([\d.]+) ([\d.]+)\)(?:\s+\(thickness ([\d.]+)\))?', ref_prop_block)
                if font_m:
                    ref_font_h = float(font_m.group(1))
                    ref_font_w = float(font_m.group(2))
                    ref_thickness = float(font_m.group(3)) if font_m.group(3) else 0.15

    # Also check Value property for reference
    if ref_name == "?":
        val_ref_m = re.search(r'\(property "Reference" "([^"]+)"', fp_block)
        if val_ref_m:
            ref_name = val_ref_m.group(1)

    # Value property
    val_m = re.search(r'\(property "Value" "([^"]+)"', fp_block)
    val_name = val_m.group(1) if val_m else "?"

    footprints.append({
        "ref": ref_name,
        "value": val_name,
        "fp_name": fp_name,
        "fp_x": fp_x, "fp_y": fp_y, "fp_angle": fp_angle,
        "fp_layer": fp_layer,
        "ref_x": ref_x, "ref_y": ref_y, "ref_angle": ref_angle,
        "ref_layer": ref_layer,
        "ref_hidden": ref_hidden,
        "font_h": ref_font_h, "font_w": ref_font_w,
        "thickness": ref_thickness,
    })

# ============================================================
# 2. Statistics
# ============================================================
print("=" * 70)
print("SILKSCREEN-ANALYSE: Bauteil-Referenzen")
print("=" * 70)

total = len(footprints)
visible = [f for f in footprints if not f["ref_hidden"]]
hidden = [f for f in footprints if f["ref_hidden"]]

print(f"\n  Gesamt Footprints: {total}")
print(f"  Sichtbar:          {len(visible)}")
print(f"  Versteckt:         {len(hidden)}")

# By type
print(f"\n  --- Versteckte Referenzen nach Typ ---")
hidden_types = Counter()
for f in hidden:
    prefix = re.match(r'([A-Z]+)', f["ref"])
    hidden_types[prefix.group(1) if prefix else "?"] += 1
for typ, count in hidden_types.most_common():
    refs = sorted([f["ref"] for f in hidden if f["ref"].startswith(typ)])
    print(f"    {typ}: {count}  → {refs}")

print(f"\n  --- Sichtbare Referenzen nach Typ ---")
visible_types = Counter()
for f in visible:
    prefix = re.match(r'([A-Z]+)', f["ref"])
    visible_types[prefix.group(1) if prefix else "?"] += 1
for typ, count in visible_types.most_common():
    print(f"    {typ}: {count}")

# ============================================================
# 3. Layer distribution
# ============================================================
print(f"\n  --- Layer-Verteilung (Referenz-Texte) ---")
layer_dist = Counter(f["ref_layer"] for f in footprints)
for layer, count in layer_dist.most_common():
    print(f"    {layer}: {count}")

# ============================================================
# 4. Font sizes
# ============================================================
print(f"\n  --- Font-Größen (sichtbare Referenzen) ---")
font_dist = Counter((f["font_h"], f["font_w"]) for f in visible)
for (h, w), count in font_dist.most_common():
    print(f"    {h}×{w}mm: {count}")

# ============================================================
# 5. Overlap analysis for visible references
# ============================================================
print(f"\n  --- Überlappungs-Analyse (sichtbare Referenzen) ---")

def text_bbox(fp):
    """Estimate bounding box of reference text in board coordinates."""
    # Text width ~ len(ref) * font_w * 0.7 (approx char width ratio)
    text_len = len(fp["ref"])
    tw = text_len * fp["font_w"] * 0.7
    th = fp["font_h"]
    
    # Position is relative to footprint for newer KiCad
    # The ref_x/ref_y in property is relative to footprint origin
    cx = fp["fp_x"] + fp["ref_x"]  
    cy = fp["fp_y"] + fp["ref_y"]
    
    angle = fp["ref_angle"] + fp["fp_angle"]
    
    # Simple bbox (no rotation for now - conservative)
    if abs(angle % 180) > 45:
        # Rotated ~90° - swap w/h
        hw, hh = th/2, tw/2
    else:
        hw, hh = tw/2, th/2
    
    return (cx - hw, cy - hh, cx + hw, cy + hh)

def boxes_overlap(b1, b2, margin=0.2):
    """Check if two bboxes overlap with given margin."""
    return not (b1[2] + margin < b2[0] or b2[2] + margin < b1[0] or
                b1[3] + margin < b2[1] or b2[3] + margin < b1[1])

# Only check visible refs on same layer
vis_by_layer = defaultdict(list)
for f in visible:
    vis_by_layer[f["ref_layer"]].append(f)

overlaps = []
for layer, fps in vis_by_layer.items():
    for i in range(len(fps)):
        for j in range(i+1, len(fps)):
            b1 = text_bbox(fps[i])
            b2 = text_bbox(fps[j])
            if boxes_overlap(b1, b2):
                overlaps.append((fps[i]["ref"], fps[j]["ref"], layer))

print(f"  Potentielle Überlappungen: {len(overlaps)}")
if overlaps:
    for r1, r2, layer in overlaps[:20]:
        print(f"    {r1} ↔ {r2} ({layer})")
    if len(overlaps) > 20:
        print(f"    ... und {len(overlaps)-20} weitere")

# ============================================================
# 6. Space analysis - where is room for hidden refs?
# ============================================================
print(f"\n  --- Platz-Analyse für versteckte Referenzen ---")

# Board boundaries
board_x1, board_y1 = 0.0, 0.0
board_x2, board_y2 = 145.554, 200.0

# Group hidden refs by area (top/bottom/left/right based on fp position)
for f in hidden:
    area_x = "links" if f["fp_x"] < board_x2/3 else ("mitte" if f["fp_x"] < 2*board_x2/3 else "rechts")
    area_y = "oben" if f["fp_y"] < board_y2/3 else ("mitte" if f["fp_y"] < 2*board_y2/3 else "unten")
    f["area"] = f"{area_y}-{area_x}"

area_counts = Counter(f["area"] for f in hidden)
print(f"  Versteckte Refs nach Board-Bereich:")
for area, count in area_counts.most_common():
    refs = sorted([f["ref"] for f in hidden if f["area"] == area])
    suffix = '...' if len(refs) > 10 else ''
    print(f"    {area:15s}: {count:3d}  ({', '.join(refs[:10])}{suffix})")

# ============================================================
# 7. Detailed list of ALL hidden references with positions
# ============================================================
print(f"\n{'='*70}")
print("VERSTECKTE REFERENZEN — Detail-Liste")
print("=" * 70)
print(f"  {'Ref':8s} {'Value':18s} {'Footprint':35s} {'X':>7s} {'Y':>7s} {'Layer':12s}")
print(f"  {'-'*8} {'-'*18} {'-'*35} {'-'*7} {'-'*7} {'-'*12}")

for f in sorted(hidden, key=lambda x: x["ref"]):
    fp_short = f["fp_name"].split(":")[-1] if ":" in f["fp_name"] else f["fp_name"]
    print(f"  {f['ref']:8s} {f['value'][:18]:18s} {fp_short[:35]:35s} {f['fp_x']:7.1f} {f['fp_y']:7.1f} {f['fp_layer']:12s}")

# ============================================================
# 8. Existing board texts (gr_text) that might conflict
# ============================================================
print(f"\n{'='*70}")
print("BOARD-LEVEL TEXTE (gr_text) - potentielle Konflikte")
print("=" * 70)

for m in re.finditer(r'\(gr_text "([^"]*)"[^)]*\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)[^)]*\(layer "([^"]+)"\)', pcb):
    text = m.group(1)
    x, y = float(m.group(2)), float(m.group(3))
    layer = m.group(5)
    print(f"  \"{text[:30]}\" @ ({x:.1f}, {y:.1f}) [{layer}]")

# ============================================================
# 9. Summary / Recommendations
# ============================================================
print(f"\n{'='*70}")
print("ZUSAMMENFASSUNG & EMPFEHLUNGEN")
print("=" * 70)

print(f"""
  PROBLEM: {len(hidden)} von {total} Bauteil-Referenzen sind versteckt (hide yes).
  
  STRATEGIE für vollständige Beschriftung:
  1. Font-Größe: 0.8×0.8mm (JLCPCB Min) mit 0.15mm Strichstärke
  2. Referenzen direkt neben/über dem Bauteil platzieren
  3. Bei Platzkonflikt: 45°/90° Rotation nutzen
  4. B.Silkscreen für Bauteile auf B.Cu verwenden
  5. Gruppierte Bauteile (z.B. CH1-CH6 Widerstände): einheitliche Ausrichtung
  
  NÄCHSTER SCHRITT: Python-Skript das alle versteckten Referenzen 
  sichtbar macht und kollisionsfrei platziert.
""")
