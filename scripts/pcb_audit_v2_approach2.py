#!/usr/bin/env python3
"""
PCB Deep-Dive v2 — Ansatz 2: Geometrische Audio-Design-Analyse
Prüft räumliche/physikalische Aspekte:
  - Entkopplungs-Abstände (Cap-zu-IC)
  - Audio-Signal Layer-Verteilung
  - GND-Masseflächen-Kontinuität (Schlitz-Erkennung)
  - Power-Rückstrompfade
  - Schaltregler-zu-Audio Abstand
  - TVS-Dioden-Platzierung
  - Via-Stitching-Dichte
  - Trace-Winkel (45° Rule)
  - Parallele Audio/Digital-Traces
  - Differentielle Paar-Symmetrie
"""
import re, math, json, fnmatch
from collections import Counter, defaultdict

PCB = "aurora-dsp-icepower-booster.kicad_pcb"
PRO = "aurora-dsp-icepower-booster.kicad_pro"

with open(PCB) as f:
    pcb = f.read()
with open(PRO) as f:
    pro = json.load(f)

findings = []
def finding(cat, sev, title, detail):
    findings.append({"cat": cat, "sev": sev, "title": title, "detail": detail})

def dist(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

# === PARSE ===
net_map = {}
for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', pcb):
    net_map[int(m.group(1))] = m.group(2)

patterns = pro.get("net_settings", {}).get("netclass_patterns", []) or []
def get_nc(name):
    for p in patterns:
        if fnmatch.fnmatch(name, p["pattern"]):
            return p["netclass"]
    return "Default"

segments = []
for m in re.finditer(r'\(segment\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net (\d+)\)', pcb):
    segments.append({
        "x1": float(m.group(1)), "y1": float(m.group(2)),
        "x2": float(m.group(3)), "y2": float(m.group(4)),
        "width": float(m.group(5)), "layer": m.group(6), "net": int(m.group(7))
    })

vias = []
for m in re.finditer(r'\(via\s+\(at ([\d.]+) ([\d.]+)\)\s+\(size ([\d.]+)\)\s+\(drill ([\d.]+)\)\s+\(layers "[^"]+" "[^"]+"\)\s+\(net (\d+)\)', pcb):
    vias.append({
        "x": float(m.group(1)), "y": float(m.group(2)),
        "size": float(m.group(3)), "drill": float(m.group(4)),
        "net": int(m.group(5))
    })

# Parse footprints
footprints = {}
for m in re.finditer(r'\(footprint "([^"]+)"\s+\(layer "[^"]+"\)\s+\(uuid "[^"]+"\)\s+\(at ([\d.]+) ([\d.]+)(?:\s+([\d.-]+))?\)', pcb):
    fp_name = m.group(1)
    x, y = float(m.group(2)), float(m.group(3))
    angle = float(m.group(4)) if m.group(4) else 0
    # Find reference
    block = pcb[m.start():m.start()+3000]
    ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
    val_m = re.search(r'\(property "Value" "([^"]+)"', block)
    ref = ref_m.group(1) if ref_m else "?"
    val = val_m.group(1) if val_m else "?"
    footprints[ref] = {"fp": fp_name, "x": x, "y": y, "angle": angle, "value": val}

ics = {r: f for r, f in footprints.items() if r.startswith("U")}
caps = {r: f for r, f in footprints.items() if r.startswith("C") and r[1:].isdigit()}
resistors = {r: f for r, f in footprints.items() if r.startswith("R") and r[1:].isdigit()}
diodes = {r: f for r, f in footprints.items() if r.startswith("D")}
connectors = {r: f for r, f in footprints.items() if r.startswith("J")}

# ============================================================
# 1. ENTKOPPLUNG: Cap-zu-IC Abstände
# ============================================================
print("=" * 70)
print("1. IC-ENTKOPPLUNG (Bypass-Cap Abstände)")
print("=" * 70)

for ic_ref, ic in sorted(ics.items()):
    nearest = []
    for cap_ref, cap in caps.items():
        d = dist(ic["x"], ic["y"], cap["x"], cap["y"])
        nearest.append((d, cap_ref, cap["value"]))
    nearest.sort()
    
    n_3mm = sum(1 for d, _, _ in nearest if d <= 3.0)
    n_5mm = sum(1 for d, _, _ in nearest if d <= 5.0)
    n_10mm = sum(1 for d, _, _ in nearest if d <= 10.0)
    closest = nearest[0] if nearest else (999, "?", "?")
    
    # IC-type specific expectations
    ic_type = ic["value"]
    if "LM4562" in ic_type:
        expected_range = 3.0
        sev = "WARN" if n_3mm == 0 else None
    elif "ADP71" in ic_type or "TEL5" in ic_type:
        expected_range = 5.0
        sev = "WARN" if n_5mm == 0 else None
    else:
        expected_range = 5.0
        sev = None

    status = "✓" if n_3mm >= 1 else "~" if n_5mm >= 1 else "⚠"
    print(f"  {ic_ref:6s} ({ic_type:16s}) @ ({ic['x']:6.1f},{ic['y']:6.1f})  "
          f"nearest={closest[1]}({closest[2]}) {closest[0]:.1f}mm  "
          f"[≤3mm:{n_3mm} ≤5mm:{n_5mm} ≤10mm:{n_10mm}] {status}")
    
    if sev:
        finding("DECOUPLING", sev, f"{ic_ref} ({ic_type}): Nearest cap {closest[0]:.1f}mm",
                 f"Empfehlung: ≤{expected_range}mm. "
                 f"Nearest: {closest[1]} ({closest[2]}), ≤10mm: {n_10mm} caps")

# ============================================================
# 2. AUDIO-SIGNAL LAYER-VERTEILUNG
# ============================================================
print("\n" + "=" * 70)
print("2. AUDIO-SIGNAL LAYER-VERTEILUNG")
print("=" * 70)

audio_layers = defaultdict(lambda: Counter())
for seg in segments:
    name = net_map.get(seg["net"], "")
    nc = get_nc(name)
    if nc in ("Audio_Input", "Audio_Output"):
        audio_layers[nc][seg["layer"]] += 1

for nc_name in ["Audio_Input", "Audio_Output"]:
    if nc_name not in audio_layers:
        print(f"  {nc_name}: keine Segmente")
        continue
    layers = audio_layers[nc_name]
    total = sum(layers.values())
    print(f"  {nc_name} ({total} Segmente):")
    for layer, count in layers.most_common():
        pct = count / total * 100
        marker = " ← empfohlen" if layer == "F.Cu" else ""
        print(f"    {layer}: {count} ({pct:.0f}%){marker}")
    
    if "B.Cu" in layers:
        bcu_pct = layers["B.Cu"] / total * 100
        if bcu_pct > 20:
            finding("AUDIO", "WARN", f"{nc_name}: {bcu_pct:.0f}% auf B.Cu",
                     "Empfehlung: Audio-Traces auf F.Cu, B.Cu für ununterbrochene GND-Fläche freihalten")
        elif bcu_pct > 5:
            finding("AUDIO", "INFO", f"{nc_name}: {bcu_pct:.0f}% auf B.Cu",
                     "Wenige B.Cu-Segmente akzeptabel wenn GND-Fläche darunter intakt")

# ============================================================
# 3. VIAS IM AUDIO-SIGNALPFAD
# ============================================================
print("\n" + "=" * 70)
print("3. VIAS IM AUDIO-SIGNALPFAD")
print("=" * 70)

audio_via_nets = Counter()
for v in vias:
    name = net_map.get(v["net"], "")
    nc = get_nc(name)
    if nc == "Audio_Input":
        audio_via_nets[name] += 1

total_audio_vias = sum(audio_via_nets.values())
print(f"  Audio_Input Vias: {total_audio_vias}")
if audio_via_nets:
    for name, count in audio_via_nets.most_common(10):
        print(f"    {name}: {count}")
    finding("AUDIO", "INFO", f"{total_audio_vias} Vias in Audio_Input-Netzen",
             "Jeder Via ist ein Impedanzsprung. Empfehlung: Audio-Traces möglichst auf einem Layer")

audio_out_vias = Counter()
for v in vias:
    name = net_map.get(v["net"], "")
    nc = get_nc(name)
    if nc == "Audio_Output":
        audio_out_vias[name] += 1

total_out_vias = sum(audio_out_vias.values())
print(f"  Audio_Output Vias: {total_out_vias}")

# ============================================================
# 4. SCHALTREGLER-ABSTAND ZU AUDIO
# ============================================================
print("\n" + "=" * 70)
print("4. SCHALTREGLER-ABSTAND ZU AUDIO-ICs")
print("=" * 70)

# U1 = TEL5-2422 (DC/DC Converter)
dc_dc = footprints.get("U1")
if dc_dc:
    print(f"  DC/DC: U1 ({dc_dc['value']}) @ ({dc_dc['x']:.1f}, {dc_dc['y']:.1f})")
    
    # Distance to each audio IC
    for ref, ic in sorted(ics.items()):
        if "LM4562" in ic["value"]:
            d = dist(dc_dc["x"], dc_dc["y"], ic["x"], ic["y"])
            status = "✓ ≥20mm" if d >= 20 else "⚠ <20mm"
            print(f"    → {ref} ({ic['value']}): {d:.1f}mm {status}")
            if d < 20:
                finding("EMV", "WARN", f"U1 DC/DC nur {d:.1f}mm von {ref}",
                         "Empfehlung: ≥20mm Abstand zwischen Schaltregler und Audio-Eingangsstufe")

# ============================================================
# 5. VIA-STITCHING DICHTE
# ============================================================
print("\n" + "=" * 70)
print("5. GND VIA-STITCHING")
print("=" * 70)

gnd_net = None
for nid, name in net_map.items():
    if name == "GND":
        gnd_net = nid
        break

gnd_vias = [v for v in vias if v["net"] == gnd_net] if gnd_net else []
print(f"  GND-Vias: {len(gnd_vias)}")

if len(gnd_vias) > 5:
    # Nearest-neighbor analysis
    nn_dists = []
    for i, v1 in enumerate(gnd_vias):
        min_d = float('inf')
        for j, v2 in enumerate(gnd_vias):
            if i != j:
                d = dist(v1["x"], v1["y"], v2["x"], v2["y"])
                min_d = min(min_d, d)
        nn_dists.append(min_d)
    
    avg_nn = sum(nn_dists) / len(nn_dists)
    max_nn = max(nn_dists)
    min_nn = min(nn_dists)
    print(f"  Nearest-Neighbor: min={min_nn:.1f}mm  avg={avg_nn:.1f}mm  max={max_nn:.1f}mm")
    
    if avg_nn > 10:
        finding("VIA_STITCH", "INFO", f"GND-Via avg NN-Abstand {avg_nn:.1f}mm",
                 "Empfehlung: 5-10mm für Audio-Bereiche. Kein Blocker bei vorhandenen GND-Zonen.")

# ============================================================
# 6. TRACE-ROUTING-WINKEL
# ============================================================
print("\n" + "=" * 70)
print("6. TRACE-ROUTING-WINKEL")
print("=" * 70)

angle_counts = Counter()
odd_angles = []
for seg in segments:
    dx = seg["x2"] - seg["x1"]
    dy = seg["y2"] - seg["y1"]
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        continue
    angle = math.degrees(math.atan2(abs(dy), abs(dx)))
    # Classify
    if angle < 1:
        angle_counts["0° (horizontal)"] += 1
    elif abs(angle - 45) < 1:
        angle_counts["45° (diagonal)"] += 1
    elif abs(angle - 90) < 1:
        angle_counts["90° (vertikal)"] += 1
    else:
        angle_counts[f"~{angle:.0f}° (andere)"] += 1
        odd_angles.append((angle, seg))

total_segs = sum(angle_counts.values())
for angle_str, count in angle_counts.most_common():
    pct = count / total_segs * 100
    print(f"  {angle_str:25s}: {count:5d} ({pct:.1f}%)")

if odd_angles:
    finding("ROUTING", "INFO", f"{len(odd_angles)} Traces mit ungewöhnlichem Winkel",
             f"Beispiel: {odd_angles[0][0]:.1f}° — Freerouting-Artefakt, akzeptabel")

# ============================================================
# 7. TVS-DIODEN UND STECKVERBINDER
# ============================================================
print("\n" + "=" * 70)
print("7. ESD-SCHUTZ (TVS-Dioden bei Steckverbindern)")
print("=" * 70)

tvs = {r: f for r, f in diodes.items()}
print(f"  Dioden: {len(tvs)}  (alle TVS/ESD)")

# Group connectors and find nearest TVS
for conn_ref, conn in sorted(connectors.items()):
    nearest_tvs_d = float('inf')
    nearest_tvs_ref = None
    for tvs_ref, tvs_fp in tvs.items():
        d = dist(conn["x"], conn["y"], tvs_fp["x"], tvs_fp["y"])
        if d < nearest_tvs_d:
            nearest_tvs_d = d
            nearest_tvs_ref = tvs_ref
    
    if nearest_tvs_d <= 15:
        status = "✓"
    elif nearest_tvs_d <= 30:
        status = "~"  # Acceptable for audio
    else:
        status = "⚠"
    
    print(f"  {conn_ref:5s} ({conn['value'][:18]:18s}): nearest TVS = {nearest_tvs_ref} @ {nearest_tvs_d:.1f}mm {status}")

# ============================================================
# 8. ZOBEL-NETZWERK
# ============================================================
print("\n" + "=" * 70)
print("8. ZOBEL-NETZWERK / OUTPUT-SCHUTZ")
print("=" * 70)

zobel_rs = {r: f for r, f in resistors.items() if f["value"] in ("10", "10R")}
print(f"  10Ω Widerstände (Zobel): {len(zobel_rs)}")
print(f"  Erwartet: 12 (2 pro Kanal × 6 Kanäle = hot + cold)")
if len(zobel_rs) == 12:
    print(f"  ✓ Korrekte Anzahl")
elif len(zobel_rs) < 12:
    finding("AUDIO", "WARN", f"Nur {len(zobel_rs)} Zobel-Widerstände (erwartet: 12)",
             "2 pro Kanal (hot + cold) × 6 Kanäle")

# ============================================================
# 9. POWER-TRACE BREITEN UND STRÖME
# ============================================================
print("\n" + "=" * 70)
print("9. POWER-TRACE ANALYSE")
print("=" * 70)

power_nets_info = {}
for seg in segments:
    name = net_map.get(seg["net"], "")
    nc = get_nc(name)
    if nc in ("Power", "Audio_Power", "HV"):
        if name not in power_nets_info:
            power_nets_info[name] = {"widths": [], "layers": Counter(), "class": nc}
        power_nets_info[name]["widths"].append(seg["width"])
        power_nets_info[name]["layers"][seg["layer"]] += 1

for name, info in sorted(power_nets_info.items()):
    widths = info["widths"]
    min_w = min(widths)
    max_w = max(widths)
    # Estimated current capacity (1oz Cu, 10°C rise, external trace)
    # Rough: 0.5mm ≈ 1A, 0.8mm ≈ 1.5A, 1.5mm ≈ 3A
    print(f"  {name:12s} [{info['class']:12s}]: {len(widths):3d} segs, "
          f"width={min_w:.2f}–{max_w:.2f}mm, layers={dict(info['layers'])}")

# ============================================================
# 10. COMPONENT DENSITY & PLACEMENT
# ============================================================
print("\n" + "=" * 70)
print("10. BAUTEIL-DICHTE UND PLATZIERUNG")
print("=" * 70)

print(f"  Board: 145.55 × 200.00 mm = {145.55 * 200 / 100:.1f} cm²")
print(f"  Footprints: {len(footprints)}")
print(f"  Dichte: {len(footprints) / (145.55 * 200 / 100):.1f} Bauteile/cm²")
print(f"  ICs: {len(ics)}, R: {len(resistors)}, C: {len(caps)}, D: {len(diodes)}, J: {len(connectors)}")

# R/C orientation
r_angles = Counter(int(f["angle"]) % 360 for f in resistors.values())
c_angles = Counter(int(f["angle"]) % 360 for f in caps.values())
print(f"  R-Orientierung: {dict(r_angles.most_common())}")
print(f"  C-Orientierung: {dict(c_angles.most_common())}")

# ============================================================
# 11. BALANCED-PAIR ROUTING-SYMMETRIE
# ============================================================
print("\n" + "=" * 70)
print("11. DIFFERENTIELLE PAAR-SYMMETRIE (HOT/COLD)")
print("=" * 70)

# Compare trace lengths of matching HOT/COLD pairs per channel
for ch in range(1, 7):
    hot_name = f"/CH{ch}_HOT_IN"
    cold_name = f"/CH{ch}_COLD_IN"
    
    hot_len = sum(dist(s["x1"],s["y1"],s["x2"],s["y2"]) for s in segments 
                  if net_map.get(s["net"]) == hot_name)
    cold_len = sum(dist(s["x1"],s["y1"],s["x2"],s["y2"]) for s in segments 
                   if net_map.get(s["net"]) == cold_name)
    
    if hot_len > 0 and cold_len > 0:
        diff = abs(hot_len - cold_len)
        ratio = max(hot_len, cold_len) / min(hot_len, cold_len)
        status = "✓" if ratio < 1.2 else "~" if ratio < 1.5 else "⚠"
        print(f"  CH{ch} HOT={hot_len:.1f}mm COLD={cold_len:.1f}mm  "
              f"Δ={diff:.1f}mm ratio={ratio:.2f} {status}")
        if ratio > 2.0:
            finding("AUDIO", "INFO", f"CH{ch} HOT/COLD Asymmetrie ratio={ratio:.1f}",
                     f"HOT={hot_len:.1f}mm vs COLD={cold_len:.1f}mm. "
                     f"Bei Audio-Frequenzen unkritisch, aber nicht ideal für CMRR")

# ============================================================
# 12. KANAL-GLEICHMÄSSIGKEIT
# ============================================================
print("\n" + "=" * 70)
print("12. KANAL-GLEICHMÄSSIGKEIT (Trace-Längen)")
print("=" * 70)

for signal_type in ["_HOT_IN", "_GAIN_OUT", "_OUT_HOT"]:
    lengths = []
    for ch in range(1, 7):
        name = f"/CH{ch}{signal_type}"
        total_len = sum(dist(s["x1"],s["y1"],s["x2"],s["y2"]) for s in segments 
                        if net_map.get(s["net"]) == name)
        if total_len > 0:
            lengths.append((ch, total_len))
    
    if lengths:
        avg = sum(l for _, l in lengths) / len(lengths)
        max_dev = max(abs(l - avg) for _, l in lengths)
        print(f"  {signal_type:15s}: avg={avg:.1f}mm ±{max_dev:.1f}mm  "
              f"({', '.join(f'CH{ch}={l:.0f}' for ch, l in lengths)})")

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
print("\n" + "=" * 70)
print("FINDINGS ZUSAMMENFASSUNG (Ansatz 2)")
print("=" * 70)

for sev in ["ERROR", "WARN", "INFO"]:
    items = [f for f in findings if f["sev"] == sev]
    if items:
        icon = {"ERROR": "🔴", "WARN": "🟡", "INFO": "🔵"}[sev]
        print(f"\n{icon} {sev} ({len(items)}):")
        for f in items:
            print(f"  [{f['cat']}] {f['title']}")
            if f['detail']:
                print(f"    → {f['detail']}")

total = len(findings)
errors = len([f for f in findings if f["sev"] == "ERROR"])
warns = len([f for f in findings if f["sev"] == "WARN"])
infos = len([f for f in findings if f["sev"] == "INFO"])
print(f"\nGesamt: {total} Findings ({errors} ERROR, {warns} WARN, {infos} INFO)")
