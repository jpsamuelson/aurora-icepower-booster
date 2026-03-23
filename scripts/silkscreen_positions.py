#!/usr/bin/env python3
"""
Detaillierte Footprint-Geometrie + Position pro Kanal.
Erstellt konkreten Platzierungsplan für alle 199 Referenzen.
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

    # Reference
    ref_prop_start = fp_block.find('(property "Reference"')
    ref_name, ref_rel_x, ref_rel_y, ref_angle, ref_layer = "?", 0, 0, 0, "?"
    ref_font_h, ref_font_w = 1.0, 1.0
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
            font_m = re.search(r'\(font\s+\(size ([\d.]+) ([\d.]+)\)', ref_block)
            if font_m:
                ref_font_h = float(font_m.group(1))
                ref_font_w = float(font_m.group(2))

    # Value
    val_prop_start = fp_block.find('(property "Value"')
    val_name = "?"
    if val_prop_start >= 0:
        val_block = extract_balanced(fp_block, val_prop_start)
        if val_block:
            vm = re.search(r'"Value" "([^"]+)"', val_block)
            val_name = vm.group(1) if vm else "?"

    # Pads: get actual pad positions and sizes
    pads = []
    for pm in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+) \(at ([\d.-]+) ([\d.-]+)(?:\s+([\d.-]+))?\) \(size ([\d.]+) ([\d.]+)\)', fp_block):
        pads.append({
            "name": pm.group(1),
            "type": pm.group(2),  # smd, thru_hole
            "shape": pm.group(3),
            "x": float(pm.group(4)), "y": float(pm.group(5)),
            "sx": float(pm.group(7)), "sy": float(pm.group(8)),
        })

    # Calculate actual body bbox from pads (in local coords)
    if pads:
        pad_min_x = min(p["x"] - p["sx"]/2 for p in pads)
        pad_max_x = max(p["x"] + p["sx"]/2 for p in pads)
        pad_min_y = min(p["y"] - p["sy"]/2 for p in pads)
        pad_max_y = max(p["y"] + p["sy"]/2 for p in pads)
        body_w = pad_max_x - pad_min_x
        body_h = pad_max_y - pad_min_y
    else:
        pad_min_x, pad_max_x = -1, 1
        pad_min_y, pad_max_y = -1, 1
        body_w, body_h = 2, 2

    footprints.append({
        "ref": ref_name, "value": val_name, "fp_name": fp_name,
        "fp_x": fp_x, "fp_y": fp_y, "fp_angle": fp_angle,
        "fp_layer": fp_layer,
        "ref_rel_x": ref_rel_x, "ref_rel_y": ref_rel_y, "ref_angle": ref_angle,
        "ref_layer": ref_layer,
        "font_h": ref_font_h, "font_w": ref_font_w,
        "body_w": body_w, "body_h": body_h,
        "pad_bbox": (pad_min_x, pad_min_y, pad_max_x, pad_max_y),
        "n_pads": len(pads),
    })

# ============================================================
# Focus: 199 F.Fab references that need to move to Silkscreen
# ============================================================
on_fab = sorted([f for f in footprints if f["ref_layer"] == "F.Fab"],
                key=lambda f: (f["fp_y"], f["fp_x"]))

print("=" * 100)
print(f"199 REFERENZEN AUF F.Fab — Detail-Positionen und Platzierungsplan")
print("=" * 100)

# Useful: Show each component with its orientation, body size, and current ref offset
print(f"\n{'Ref':8s} {'Value':12s} {'FP-Typ':20s} {'FP_X':>6s} {'FP_Y':>6s} "
      f"{'Rot':>4s} {'Body':>10s} {'Ref@':>12s} {'RefAng':>6s}")
print("-" * 100)

# Categorize by Y-band (channel) 
channel_y_bands = [
    (0, 30, "Power/Ctrl"),
    (30, 60, "Kanal 1"),
    (60, 88, "Kanal 2"),
    (88, 116, "Kanal 3"),
    (116, 143, "Kanal 4"),
    (143, 171, "Kanal 5"),
    (171, 200, "Kanal 6"),
]

for y_min, y_max, label in channel_y_bands:
    band = [f for f in on_fab if y_min <= f["fp_y"] < y_max]
    if not band:
        continue
    print(f"\n  --- {label} (y={y_min}–{y_max}mm, {len(band)} Bauteile) ---")
    for f in sorted(band, key=lambda x: (x["fp_x"], x["fp_y"])):
        fp_short = f["fp_name"].split(":")[-1][:20] if ":" in f["fp_name"] else f["fp_name"][:20]
        body = f"{f['body_w']:.1f}×{f['body_h']:.1f}"
        ref_at = f"({f['ref_rel_x']:+.1f},{f['ref_rel_y']:+.1f})"
        print(f"  {f['ref']:8s} {f['value'][:12]:12s} {fp_short:20s} "
              f"{f['fp_x']:6.1f} {f['fp_y']:6.1f} {f['fp_angle']:4.0f}° "
              f"{body:>10s} {ref_at:>12s} {f['ref_angle']:5.0f}°")

# ============================================================
# Show the pattern for CH1 vs CH2 to verify repetition
# ============================================================
print(f"\n{'='*100}")
print("KANAL-VERGLEICH: CH1 vs CH2 (Verifikation der Wiederholung)")
print("=" * 100)

ch1 = sorted([f for f in on_fab if 30 <= f["fp_y"] < 60], key=lambda x: x["fp_x"])
ch2 = sorted([f for f in on_fab if 60 <= f["fp_y"] < 88], key=lambda x: x["fp_x"])

ch1_x = [f'{fp["fp_x"]:.1f}' for fp in ch1]
ch2_x = [f'{fp["fp_x"]:.1f}' for fp in ch2]
print(f"\n  CH1 ({len(ch1)} Bauteile):  X-Positionen: {ch1_x}")
print(f"  CH2 ({len(ch2)} Bauteile):  X-Positionen: {ch2_x}")

# Compare X positions (should be identical if channels are replicated)
if len(ch1) == len(ch2):
    x_diffs = [abs(ch1[i]["fp_x"] - ch2[i]["fp_x"]) for i in range(len(ch1))]
    y_shift = ch2[0]["fp_y"] - ch1[0]["fp_y"] if ch1 and ch2 else 0
    print(f"  Y-Shift CH1→CH2: {y_shift:.1f}mm")
    print(f"  X-Abweichungen: max={max(x_diffs):.1f}mm (0.0 = perfekte Wiederholung)")

# ============================================================
# Summary: Footprint orientations for placement strategy  
# ============================================================
print(f"\n{'='*100}")
print("ORIENTIERUNGS-ZUSAMMENFASSUNG (für Platzierungsstrategie)")
print("=" * 100)

for fp_type_prefix in ["R_0805", "C_0805", "C_1206", "C_1210"]:
    fps = [f for f in on_fab if fp_type_prefix in f["fp_name"]]
    if not fps:
        continue
    angles = Counter(int(f["fp_angle"]) for f in fps)
    print(f"\n  {fp_type_prefix}:")
    for angle, count in angles.most_common():
        refs = sorted([f["ref"] for f in fps if int(f["fp_angle"]) == angle], 
                      key=lambda r: int(re.sub(r'[^0-9]', '', r) or '0'))
        print(f"    {angle:4d}°: {count:3d} Stück → {', '.join(refs[:8])}{'...' if len(refs)>8 else ''}")
        
        # Show typical positions for this orientation group
        sample = [f for f in fps if int(f["fp_angle"]) == angle][:3]
        for s in sample:
            bbox = s["pad_bbox"]
            print(f"           {s['ref']:6s} @ ({s['fp_x']:6.1f}, {s['fp_y']:6.1f})  "
                  f"pads: ({bbox[0]:+.2f},{bbox[1]:+.2f})→({bbox[2]:+.2f},{bbox[3]:+.2f})  "
                  f"body={s['body_w']:.2f}×{s['body_h']:.2f}mm")
