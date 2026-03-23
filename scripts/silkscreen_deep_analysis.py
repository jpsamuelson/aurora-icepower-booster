#!/usr/bin/env python3
"""
Silkscreen Deep-Dive: Welche Referenzen auf Fab vs. Silkscreen?
Detaillierte Analyse mit Pad-/Courtyard-Bounding-Boxes für Platzierungsplan.
"""
import re, math, json
from collections import defaultdict, Counter

PCB = "aurora-dsp-icepower-booster.kicad_pcb"
with open(PCB) as f:
    pcb = f.read()

def extract_balanced(text, start):
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

# ============================================================
# Parse footprints with full detail
# ============================================================
footprints = []
fp_starts = [m.start() for m in re.finditer(r'\(footprint "', pcb)]

for fp_start in fp_starts:
    fp_block = extract_balanced(pcb, fp_start)
    if not fp_block or len(fp_block) < 50:
        continue

    fp_name_m = re.match(r'\(footprint "([^"]+)"', fp_block)
    fp_name = fp_name_m.group(1) if fp_name_m else "?"

    fp_layer_m = re.search(r'\(layer "([^"]+)"\)', fp_block[:200])
    fp_layer = fp_layer_m.group(1) if fp_layer_m else "?"

    fp_at_m = re.search(r'\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', fp_block[:300])
    fp_x = float(fp_at_m.group(1)) if fp_at_m else 0
    fp_y = float(fp_at_m.group(2)) if fp_at_m else 0
    fp_angle = float(fp_at_m.group(3)) if fp_at_m and fp_at_m.group(3) else 0

    # Reference property
    ref_prop_start = fp_block.find('(property "Reference"')
    ref_name = "?"
    ref_rel_x, ref_rel_y, ref_angle = 0, 0, 0
    ref_layer = "?"
    ref_font_h, ref_font_w = 1.0, 1.0
    ref_hidden = False

    if ref_prop_start >= 0:
        ref_block = extract_balanced(fp_block, ref_prop_start)
        if ref_block:
            nm = re.search(r'"Reference" "([^"]+)"', ref_block)
            ref_name = nm.group(1) if nm else "?"
            at_m = re.search(r'\(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\)', ref_block)
            if at_m:
                ref_rel_x = float(at_m.group(1))
                ref_rel_y = float(at_m.group(2))
                ref_angle = float(at_m.group(3)) if at_m.group(3) else 0
            layer_m = re.search(r'\(layer "([^"]+)"\)', ref_block)
            if layer_m:
                ref_layer = layer_m.group(1)
            ref_hidden = '(hide yes)' in ref_block or 'hide yes' in ref_block
            font_m = re.search(r'\(font\s+\(size ([\d.]+) ([\d.]+)\)', ref_block)
            if font_m:
                ref_font_h = float(font_m.group(1))
                ref_font_w = float(font_m.group(2))

    # Value property
    val_prop_start = fp_block.find('(property "Value"')
    val_name = "?"
    if val_prop_start >= 0:
        val_block = extract_balanced(fp_block, val_prop_start)
        if val_block:
            vm = re.search(r'"Value" "([^"]+)"', val_block)
            val_name = vm.group(1) if vm else "?"

    # Pads - find bounding box of all pads
    pad_positions = []
    for pm in re.finditer(r'\(pad "[^"]*" \w+ \w+ \(at ([\d.-]+) ([\d.-]+)', fp_block):
        pad_positions.append((float(pm.group(1)), float(pm.group(2))))
    
    # Approximate footprint bounding box from pads
    if pad_positions:
        pad_min_x = min(p[0] for p in pad_positions) - 0.5
        pad_max_x = max(p[0] for p in pad_positions) + 0.5
        pad_min_y = min(p[1] for p in pad_positions) - 0.5
        pad_max_y = max(p[1] for p in pad_positions) + 0.5
    else:
        pad_min_x, pad_max_x = -1, 1
        pad_min_y, pad_max_y = -1, 1

    footprints.append({
        "ref": ref_name, "value": val_name, "fp_name": fp_name,
        "fp_x": fp_x, "fp_y": fp_y, "fp_angle": fp_angle,
        "fp_layer": fp_layer,
        "ref_rel_x": ref_rel_x, "ref_rel_y": ref_rel_y, "ref_angle": ref_angle,
        "ref_layer": ref_layer, "ref_hidden": ref_hidden,
        "font_h": ref_font_h, "font_w": ref_font_w,
        "pad_bbox_rel": (pad_min_x, pad_min_y, pad_max_x, pad_max_y),
    })

# ============================================================
# Analysis
# ============================================================
on_fab = [f for f in footprints if f["ref_layer"] == "F.Fab"]
on_silk = [f for f in footprints if "Silk" in f["ref_layer"]]
on_other = [f for f in footprints if f["ref_layer"] not in ("F.Fab",) and "Silk" not in f["ref_layer"]]

print("=" * 80)
print("SILKSCREEN DEEP-DIVE: Layer-Zuordnung aller Referenzen")
print("=" * 80)

print(f"\n  Gesamt: {len(footprints)} Footprints")
print(f"  Auf F.Fab (nicht sichtbar!): {len(on_fab)}")
print(f"  Auf Silkscreen (sichtbar):   {len(on_silk)}")
print(f"  Andere Layer:                {len(on_other)}")

# Detailed layer breakdown
layer_detail = Counter(f["ref_layer"] for f in footprints)
for layer, count in layer_detail.most_common():
    silk = "← SICHTBAR" if "Silk" in layer else "← NICHT SICHTBAR" if layer == "F.Fab" else ""
    print(f"    {layer:20s}: {count:4d}  {silk}")

# ============================================================
# Referenzen auf F.Fab nach Typ
# ============================================================
print(f"\n{'='*80}")
print("REFERENZEN AUF F.Fab (müssen auf Silkscreen verschoben werden)")
print("=" * 80)

fab_by_type = defaultdict(list)
for f in on_fab:
    prefix = re.match(r'([A-Z]+)', f["ref"])
    typ = prefix.group(1) if prefix else "?"
    fab_by_type[typ].append(f)

for typ in sorted(fab_by_type.keys()):
    fps = fab_by_type[typ]
    refs = sorted([f["ref"] for f in fps], key=lambda r: int(re.sub(r'[^0-9]', '', r) or '0'))
    print(f"\n  {typ} ({len(fps)} Stück):")
    # Show in rows of ~10
    for i in range(0, len(refs), 12):
        print(f"    {', '.join(refs[i:i+12])}")

# ============================================================
# Referenzen auf Silkscreen (bereits sichtbar)
# ============================================================
print(f"\n{'='*80}")
print("REFERENZEN AUF SILKSCREEN (bereits sichtbar)")
print("=" * 80)

silk_by_type = defaultdict(list)
for f in on_silk:
    prefix = re.match(r'([A-Z]+)', f["ref"])
    typ = prefix.group(1) if prefix else "?"
    silk_by_type[typ].append(f)

for typ in sorted(silk_by_type.keys()):
    fps = silk_by_type[typ]
    refs = sorted([f["ref"] for f in fps], key=lambda r: int(re.sub(r'[^0-9]', '', r) or '0'))
    print(f"  {typ} ({len(fps)}): {', '.join(refs)}")

# ============================================================
# Footprint size analysis for placement planning
# ============================================================
print(f"\n{'='*80}")
print("BAUTEIL-GEOMETRIE (für Platzierungsplanung)")
print("=" * 80)

# Group by footprint type for understanding available space
fp_types = Counter(f["fp_name"].split(":")[-1] if ":" in f["fp_name"] else f["fp_name"] for f in on_fab)
print(f"\n  Footprint-Typen auf F.Fab:")
for fp_type, count in fp_types.most_common():
    sample = next(f for f in on_fab if fp_type in f["fp_name"])
    bbox = sample["pad_bbox_rel"]
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    print(f"    {fp_type[:40]:40s} ×{count:3d}  ~{w:.1f}×{h:.1f}mm")

# ============================================================
# Kanal-Struktur: Wiederholungsmuster erkennen
# ============================================================
print(f"\n{'='*80}")
print("KANAL-STRUKTUR (repetitive Muster)")
print("=" * 80)

# Group all components by channel
channel_map = defaultdict(list)
for f in footprints:
    # Try to identify channel from position
    y = f["fp_y"]
    if 30 < y < 60:
        ch = 1
    elif 58 < y < 86:
        ch = 2
    elif 86 < y < 114:
        ch = 3
    elif 114 < y < 142:
        ch = 4
    elif 142 < y < 170:
        ch = 5
    elif 170 < y < 198:
        ch = 6
    else:
        ch = 0  # Power/control area
    channel_map[ch].append(f)

for ch in range(0, 7):
    fps = channel_map[ch]
    on_f = [f for f in fps if f["ref_layer"] == "F.Fab"]
    on_s = [f for f in fps if "Silk" in f["ref_layer"]]
    label = f"Kanal {ch}" if ch > 0 else "Power/Control"
    if fps:
        y_min = min(f["fp_y"] for f in fps)
        y_max = max(f["fp_y"] for f in fps)
        print(f"  {label:15s} (y={y_min:.0f}–{y_max:.0f}mm): "
              f"{len(fps)} Bauteile, {len(on_f)} auf Fab, {len(on_s)} auf Silk")

# ============================================================
# Space availability: regions with no components
# ============================================================
print(f"\n{'='*80}")
print("PLATZ-VERFÜGBARKEIT (Dichte-Karte)")
print("=" * 80)

# Grid-based density analysis
GRID = 10  # mm
for gy in range(0, 200, GRID):
    row = ""
    for gx in range(0, 146, GRID):
        count = sum(1 for f in footprints 
                    if gx <= f["fp_x"] < gx+GRID and gy <= f["fp_y"] < gy+GRID)
        if count == 0:
            row += "·"
        elif count <= 2:
            row += "░"
        elif count <= 5:
            row += "▒"
        elif count <= 10:
            row += "▓"
        else:
            row += "█"
    print(f"  y={gy:3d} |{row}|")

print(f"         ·=0  ░=1-2  ▒=3-5  ▓=6-10  █=>10")

# ============================================================
# PLAN: Specific placement strategy per type
# ============================================================
print(f"\n{'='*80}")
print("PLATZIERUNGS-STRATEGIE")
print("=" * 80)

print("""
  FONT: 0.8×0.8mm, Strichstärke 0.15mm (JLCPCB Minimum)
  TEXT-BBOX bei 0.8mm Font: ~0.56mm pro Zeichen Breite × 0.8mm Höhe
  
  Typische Referenz-Längen:
    R1–R113 : 2-4 Zeichen → 1.1–2.2mm breit
    C1–C81  : 2-3 Zeichen → 1.1–1.7mm breit
    D1–D25  : 2-3 Zeichen → 1.1–1.7mm breit
    U1–U15  : 2-3 Zeichen → 1.1–1.7mm breit
    J1–J15  : 2-3 Zeichen → 1.1–1.7mm breit
    SW1–SW7 : 3-4 Zeichen → 1.7–2.2mm breit
    Q1–Q7   : 2-3 Zeichen → 1.1–1.7mm breit
    MH1–MH4 : 3-4 Zeichen → 1.7–2.2mm breit
    FB1–FB2 : 3 Zeichen → 1.7mm breit
""")

# For each F.Fab ref: suggest position offset based on footprint type
print("  PLATZIERUNGS-OFFSETS nach Footprint-Typ:")
print("  (relativ zum Bauteil-Zentrum)")
print()

offset_rules = {}
for f in on_fab:
    fp_short = f["fp_name"].split(":")[-1] if ":" in f["fp_name"] else f["fp_name"]
    bbox = f["pad_bbox_rel"]
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    # Determine best position based on footprint dimensions and orientation
    if "0805" in fp_short or "0603" in fp_short or "0402" in fp_short:
        # Small SMD: place above or below
        if f["fp_angle"] in (0, 180):
            offset = (0, -1.2)  # above
            orient = 0
        else:
            offset = (1.2, 0)   # right
            orient = 90
    elif "SOT-23" in fp_short or "SOT-223" in fp_short:
        offset = (0, -1.5)
        orient = 0
    elif "SOIC" in fp_short or "SOP" in fp_short:
        offset = (0, -3.0)
        orient = 0
    elif "MountingHole" in fp_short:
        offset = (2.5, 0)
        orient = 0
    elif "DPAK" in fp_short or "TO-252" in fp_short:
        offset = (0, -2.5)
        orient = 0
    else:
        offset = (0, -(h/2 + 0.8))
        orient = 0
    
    key = fp_short[:30]
    if key not in offset_rules:
        offset_rules[key] = {"offset": offset, "orient": orient, "w": w, "h": h, "count": 0}
    offset_rules[key]["count"] += 1

for fp_type, rule in sorted(offset_rules.items(), key=lambda x: -x[1]["count"]):
    ox, oy = rule["offset"]
    print(f"    {fp_type[:35]:35s} ×{rule['count']:3d}  "
          f"body={rule['w']:.1f}×{rule['h']:.1f}mm  "
          f"offset=({ox:+.1f},{oy:+.1f})  rot={rule['orient']}°")
