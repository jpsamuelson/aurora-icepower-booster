#!/usr/bin/env python3
"""
Ansatz 1: Strukturelle PCB-Analyse
Prüft Trace-Breiten, Via-Größen, Zonen, Abstände, Silkscreen, Board-Edge
gegen die Vorgaben aus copilot-instructions.md
"""
import re, math, json
from collections import Counter, defaultdict

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB, "r") as f:
    text = f.read()

findings = []

def finding(category, severity, title, detail):
    findings.append({"cat": category, "sev": severity, "title": title, "detail": detail})

# ============================================================
# 1. NET CLASS DEFINITIONS (aus .kicad_pro)
# ============================================================
PRO = PCB.replace(".kicad_pcb", ".kicad_pro")
with open(PRO, "r") as f:
    pro = json.load(f)

net_settings = pro.get("net_settings", {})
classes = net_settings.get("classes", [])
net_assignments = {}
print("=" * 70)
print("1. NETZKLASSEN-KONFIGURATION")
print("=" * 70)
for cls in classes:
    name = cls.get("name", "?")
    track = cls.get("track_width", 0)
    clear = cls.get("clearance", 0)
    via_dia = cls.get("via_dia", 0)
    via_drill = cls.get("via_drill", 0)
    nets = cls.get("nets", [])
    print(f"  {name:15s}  track={track}mm  clear={clear}mm  via={via_dia}/{via_drill}mm  nets={len(nets)}")
    for n in nets:
        net_assignments[n] = name

# Soll-Werte aus copilot-instructions.md
EXPECTED_CLASSES = {
    "Default":      {"clearance": 0.2, "track_width": 0.25, "via_dia": 0.6, "via_drill": 0.3},
    "Power":        {"clearance": 0.2, "track_width": 0.5,  "via_dia": 0.8, "via_drill": 0.4},
    "Audio_Input":  {"clearance": 0.25,"track_width": 0.3,  "via_dia": 0.6, "via_drill": 0.3},
    "Audio_Output": {"clearance": 0.2, "track_width": 0.5,  "via_dia": 0.6, "via_drill": 0.3},
    "Audio_Power":  {"clearance": 0.2, "track_width": 0.8,  "via_dia": 0.8, "via_drill": 0.4},
    "Speaker":      {"clearance": 0.3, "track_width": 1.5,  "via_dia": 0.8, "via_drill": 0.4},
    "HV":           {"clearance": 0.5, "track_width": 0.3,  "via_dia": 0.8, "via_drill": 0.4},
}

for cls in classes:
    name = cls.get("name", "?")
    if name in EXPECTED_CLASSES:
        exp = EXPECTED_CLASSES[name]
        for param, exp_val in exp.items():
            actual = cls.get(param, 0)
            if abs(actual - exp_val) > 0.001:
                finding("NETCLASS", "WARN", f"{name}.{param} weicht ab",
                         f"Soll={exp_val}mm, Ist={actual}mm")

missing_classes = set(EXPECTED_CLASSES.keys()) - {c.get("name") for c in classes}
for mc in missing_classes:
    finding("NETCLASS", "INFO", f"Netzklasse '{mc}' fehlt", "Aus copilot-instructions empfohlen")

# ============================================================
# 2. TRACE-BREITEN-ANALYSE
# ============================================================
print("\n" + "=" * 70)
print("2. TRACE-BREITEN")
print("=" * 70)

# Build net-id to net-name mapping
net_map = {}
for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', text):
    net_map[int(m.group(1))] = m.group(2)

# Parse all segments
segments = []
for m in re.finditer(r'\(segment\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net (\d+)\)', text):
    segments.append({
        "x1": float(m.group(1)), "y1": float(m.group(2)),
        "x2": float(m.group(3)), "y2": float(m.group(4)),
        "width": float(m.group(5)), "layer": m.group(6), "net": int(m.group(7))
    })

print(f"  Gesamt: {len(segments)} Segmente")

# Group by net class
width_by_class = defaultdict(list)
width_by_net = defaultdict(list)
for seg in segments:
    net_name = net_map.get(seg["net"], f"net_{seg['net']}")
    net_class = net_assignments.get(net_name, "Default")
    width_by_class[net_class].append(seg["width"])
    width_by_net[net_name].append(seg)

for cls_name, widths in sorted(width_by_class.items()):
    min_w = min(widths)
    max_w = max(widths)
    avg_w = sum(widths) / len(widths)
    print(f"  {cls_name:15s}  n={len(widths):4d}  min={min_w:.3f}  max={max_w:.3f}  avg={avg_w:.3f}mm")

# Check: Audio_Input traces should be >= 0.3mm
for net_name, segs in width_by_net.items():
    nc = net_assignments.get(net_name, "Default")
    for seg in segs:
        if nc == "Audio_Input" and seg["width"] < 0.29:
            finding("TRACE", "WARN", f"Audio_Input zu schmal: {net_name}",
                     f"width={seg['width']}mm < 0.3mm Soll, layer={seg['layer']}")
            break
        if nc == "Power" and seg["width"] < 0.49:
            finding("TRACE", "WARN", f"Power-Trace zu schmal: {net_name}",
                     f"width={seg['width']}mm < 0.5mm Soll, layer={seg['layer']}")
            break
        if nc == "Speaker" and seg["width"] < 1.49:
            finding("TRACE", "WARN", f"Speaker-Trace zu schmal: {net_name}",
                     f"width={seg['width']}mm < 1.5mm Soll, layer={seg['layer']}")
            break

# ============================================================
# 3. VIA-ANALYSE
# ============================================================
print("\n" + "=" * 70)
print("3. VIAS")
print("=" * 70)

vias = []
for m in re.finditer(r'\(via\s+\(at ([\d.]+) ([\d.]+)\)\s+\(size ([\d.]+)\)\s+\(drill ([\d.]+)\)\s+\(layers "([^"]+)" "([^"]+)"\)\s+\(net (\d+)\)', text):
    vias.append({
        "x": float(m.group(1)), "y": float(m.group(2)),
        "size": float(m.group(3)), "drill": float(m.group(4)),
        "layer1": m.group(5), "layer2": m.group(6), "net": int(m.group(7))
    })

print(f"  Gesamt: {len(vias)} Vias")

via_sizes = Counter((v["size"], v["drill"]) for v in vias)
for (size, drill), count in via_sizes.most_common():
    annular = (size - drill) / 2
    print(f"  Size={size}mm Drill={drill}mm Annular={annular:.3f}mm  ×{count}")
    if annular < 0.125:
        finding("VIA", "ERROR", f"Annular Ring zu klein: {annular:.3f}mm",
                 f"JLCPCB Min=0.125mm, Size={size}, Drill={drill}")

# Vias im Audio-Signalpfad
audio_via_nets = []
for v in vias:
    net_name = net_map.get(v["net"], "")
    nc = net_assignments.get(net_name, "Default")
    if nc == "Audio_Input":
        audio_via_nets.append(net_name)

audio_via_count = Counter(audio_via_nets)
if audio_via_count:
    finding("AUDIO", "WARN", f"Vias im Audio_Input-Signalpfad: {len(audio_via_nets)}",
             f"Netze: {dict(audio_via_count.most_common(10))}")
    print(f"  ⚠ Vias in Audio_Input: {len(audio_via_nets)}")
    for net, cnt in audio_via_count.most_common(5):
        print(f"    {net}: {cnt} Vias")

# ============================================================
# 4. AUDIO-TRACES LAYER-CHECK
# ============================================================
print("\n" + "=" * 70)
print("4. AUDIO-SIGNAL LAYER-PRÜFUNG")
print("=" * 70)

audio_layers = defaultdict(lambda: Counter())
for net_name, segs in width_by_net.items():
    nc = net_assignments.get(net_name, "Default")
    if nc in ("Audio_Input", "Audio_Output"):
        for seg in segs:
            audio_layers[nc][seg["layer"]] += 1

for nc, layers in audio_layers.items():
    total = sum(layers.values())
    print(f"  {nc}:")
    for layer, count in layers.most_common():
        pct = count / total * 100
        print(f"    {layer}: {count} ({pct:.0f}%)")
    if "B.Cu" in layers:
        bcu_pct = layers["B.Cu"] / total * 100
        if bcu_pct > 5:
            finding("AUDIO", "WARN", f"{nc}: {bcu_pct:.0f}% auf B.Cu",
                     "Empfehlung: Audio-Traces auf F.Cu für ununterbrochene Massefläche auf B.Cu")

# ============================================================
# 5. ZONEN-ANALYSE
# ============================================================
print("\n" + "=" * 70)
print("5. GND-ZONEN")
print("=" * 70)

# Parse zones
zone_pattern = r'\(zone\s+\(net (\d+)\)\s+\(net_name "([^"]+)"\)\s+\(layer "([^"]+)"\)'
zones = []
for m in re.finditer(zone_pattern, text):
    zones.append({"net": int(m.group(1)), "name": m.group(2), "layer": m.group(3)})

for z in zones:
    print(f"  Zone: {z['name']} on {z['layer']}")

gnd_zones = [z for z in zones if z["name"] == "GND"]
gnd_layers = {z["layer"] for z in gnd_zones}
print(f"  GND-Zonen auf: {gnd_layers}")

if "B.Cu" not in gnd_layers:
    finding("ZONE", "ERROR", "Keine GND-Zone auf B.Cu!", "Massefläche auf B.Cu ist Pflicht")
if "F.Cu" not in gnd_layers:
    finding("ZONE", "INFO", "Keine GND-Zone auf F.Cu", "Optional, aber empfohlen für Via-Stitching")

# Zone connect_pads
for m in re.finditer(r'\(zone\s+\(net \d+\)\s+\(net_name "GND"\)\s+\(layer "([^"]+)"\).*?\(connect_pads\s*(yes|no|thermal)?', text):
    layer = m.group(1)
    connect = m.group(2) if m.group(2) else "thermal"
    print(f"  GND Zone {layer}: connect_pads={connect}")

# ============================================================
# 6. BOARD-EDGE CLEARANCE
# ============================================================
print("\n" + "=" * 70)
print("6. BOARD-EDGE")
print("=" * 70)

# Find board outline
edge_lines = []
for m in re.finditer(r'\(gr_line\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\).*?\(layer "Edge\.Cuts"\)', text):
    edge_lines.append({
        "x1": float(m.group(1)), "y1": float(m.group(2)),
        "x2": float(m.group(3)), "y2": float(m.group(4))
    })

if edge_lines:
    xs = [e["x1"] for e in edge_lines] + [e["x2"] for e in edge_lines]
    ys = [e["y1"] for e in edge_lines] + [e["y2"] for e in edge_lines]
    print(f"  Board-Outline: ({min(xs):.2f}, {min(ys):.2f}) → ({max(xs):.2f}, {max(ys):.2f})")
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    print(f"  Größe: {w:.2f} × {h:.2f} mm")
    
    # Check if board outline is closed
    print(f"  Edge-Segmente: {len(edge_lines)}")
else:
    # Check for gr_rect
    rect_match = re.search(r'\(gr_rect\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\).*?\(layer "Edge\.Cuts"\)', text)
    if rect_match:
        print(f"  Board-Outline (Rect): ({rect_match.group(1)}, {rect_match.group(2)}) → ({rect_match.group(3)}, {rect_match.group(4)})")
    else:
        finding("BOARD", "ERROR", "Kein Board-Outline gefunden!", "Edge.Cuts Layer ist leer")

# ============================================================
# 7. SILKSCREEN-PRÜFUNG
# ============================================================
print("\n" + "=" * 70)
print("7. SILKSCREEN")
print("=" * 70)

# gr_text elements
gr_texts = []
for m in re.finditer(r'\(gr_text "([^"]*)"[^)]*\(at ([\d.]+) ([\d.]+)', text):
    gr_texts.append({"text": m.group(1)[:30], "x": float(m.group(2)), "y": float(m.group(3))})

print(f"  Board-Texte: {len(gr_texts)}")
for t in gr_texts[:10]:
    print(f"    '{t['text']}' @ ({t['x']:.1f}, {t['y']:.1f})")

# Check text heights in footprints - sample check
small_texts = 0
for m in re.finditer(r'\(fp_text\s+reference\s+"([^"]+)".*?\(size ([\d.]+) ([\d.]+)\).*?\(thickness ([\d.]+)\)', text):
    ref = m.group(1)
    h = float(m.group(2))
    thickness = float(m.group(4))
    if h < 0.8:
        small_texts += 1

if small_texts > 0:
    finding("SILK", "WARN", f"{small_texts} Reference-Texte < 0.8mm Höhe",
             "JLCPCB empfiehlt min 0.8mm Texthöhe")
print(f"  References < 0.8mm Höhe: {small_texts}")

# ============================================================
# 8. FOOTPRINT-ANALYSE
# ============================================================
print("\n" + "=" * 70)
print("8. FOOTPRINTS")
print("=" * 70)

# Count footprints
fp_count = text.count("(footprint ")
print(f"  Gesamt: {fp_count} Footprints")

# Extract footprint references and types
footprints = []
for m in re.finditer(r'\(footprint "([^"]+)".*?\(at ([\d.]+) ([\d.]+)(?:\s+([\d.]+))?\)', text):
    footprints.append({
        "fp": m.group(1), "x": float(m.group(2)), "y": float(m.group(3)),
        "angle": float(m.group(4)) if m.group(4) else 0
    })

# Check for fiducials
fiducials = [f for f in footprints if "Fiducial" in f["fp"]]
print(f"  Fiducials: {len(fiducials)}")
if len(fiducials) < 3:
    finding("ASSEMBLY", "WARN", f"Nur {len(fiducials)} Fiducials",
             "JLCPCB SMT Assembly empfiehlt mindestens 3 Fiducials")

# Check for mounting holes
mounting_holes = [f for f in footprints if "MountingHole" in f["fp"]]
print(f"  Mounting Holes: {len(mounting_holes)}")

# ============================================================
# 9. VIA-STITCHING PRÜFUNG
# ============================================================
print("\n" + "=" * 70)
print("9. VIA-STITCHING (GND)")
print("=" * 70)

gnd_net_id = None
for nid, name in net_map.items():
    if name == "GND":
        gnd_net_id = nid
        break

gnd_vias = [v for v in vias if v["net"] == gnd_net_id] if gnd_net_id else []
print(f"  GND-Vias: {len(gnd_vias)}")

if gnd_vias:
    xs = [v["x"] for v in gnd_vias]
    ys = [v["y"] for v in gnd_vias]
    print(f"  X-Bereich: {min(xs):.1f} - {max(xs):.1f}mm")
    print(f"  Y-Bereich: {min(ys):.1f} - {max(ys):.1f}mm")
    
    # Estimate average spacing
    if len(gnd_vias) > 2:
        from itertools import combinations
        # Sample nearest-neighbor distance for first 50 vias
        sample = gnd_vias[:50]
        min_dists = []
        for i, v1 in enumerate(sample):
            min_d = float('inf')
            for j, v2 in enumerate(sample):
                if i != j:
                    d = math.sqrt((v1["x"]-v2["x"])**2 + (v1["y"]-v2["y"])**2)
                    min_d = min(min_d, d)
            min_dists.append(min_d)
        avg_nn = sum(min_dists) / len(min_dists)
        print(f"  Avg Nearest-Neighbor: {avg_nn:.2f}mm")
        if avg_nn > 10:
            finding("VIA_STITCH", "INFO", f"GND-Via-Abstand ~{avg_nn:.1f}mm",
                     "Empfehlung: max 5-10mm für Audio-Bereiche")

# ============================================================
# 10. MOUNTING HOLE ANALYSE
# ============================================================
print("\n" + "=" * 70)
print("10. MONTAGELÖCHER")
print("=" * 70)

for mh in mounting_holes:
    print(f"  {mh['fp']} @ ({mh['x']:.1f}, {mh['y']:.1f})")

# ============================================================
# 11. DRC RULES (.kicad_dru)
# ============================================================
print("\n" + "=" * 70)
print("11. CUSTOM DESIGN RULES (.kicad_dru)")
print("=" * 70)

DRU = PCB.replace(".kicad_pcb", ".kicad_dru")
try:
    with open(DRU, "r") as f:
        dru = f.read()
    print(f"  Datei: {len(dru)} Bytes")
    rules = re.findall(r'\(rule\s+(\w+)', dru)
    print(f"  Rules: {rules}")
    
    expected_rules = ["power_clearance", "power_width", "hv_clearance", 
                      "audio_input_clearance", "audio_digital_separation",
                      "audio_power_width", "speaker_width", "board_edge"]
    missing_rules = set(expected_rules) - set(rules)
    if missing_rules:
        finding("DRU", "WARN", f"Fehlende Custom Rules: {missing_rules}",
                 "Empfohlen in copilot-instructions.md Abschnitt 7")
except FileNotFoundError:
    finding("DRU", "WARN", "Keine .kicad_dru Datei", "Custom Design Rules empfohlen")
    print("  NICHT VORHANDEN")

# ============================================================
# 12. NET-ZUORDNUNGEN PRÜFEN
# ============================================================
print("\n" + "=" * 70)
print("12. NETZ-ZUORDNUNGEN (Stichprobe)")
print("=" * 70)

# Check if audio nets are correctly classified
audio_keywords = ["AUDIO", "CH1_", "CH2_", "CH3_", "CH4_", "CH5_", "CH6_", 
                   "INV_IN", "BUF_DRIVE", "GAIN_FB", "OUT_DRIVE", "EMI_"]
power_keywords = ["VCC", "+5V", "+3V3", "+12V", "-12V", "V_BAT", "V+", "V-"]

misclassified = []
for net_name, nc in net_assignments.items():
    is_audio = any(kw in net_name.upper() for kw in audio_keywords)
    is_power = any(kw in net_name.upper() for kw in power_keywords)
    if is_audio and nc == "Default":
        misclassified.append((net_name, "Audio-Netz in Default"))
    if is_power and nc == "Default":
        misclassified.append((net_name, "Power-Netz in Default"))

if misclassified:
    for net, reason in misclassified[:10]:
        print(f"  ⚠ {net}: {reason}")
    finding("NETCLASS", "INFO", f"{len(misclassified)} potentiell falsch klassifizierte Netze",
             f"Beispiele: {[m[0] for m in misclassified[:5]]}")

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
print("\n" + "=" * 70)
print("FINDINGS ZUSAMMENFASSUNG")
print("=" * 70)

for sev in ["ERROR", "WARN", "INFO"]:
    items = [f for f in findings if f["sev"] == sev]
    if items:
        print(f"\n{'🔴' if sev=='ERROR' else '🟡' if sev=='WARN' else '🔵'} {sev} ({len(items)}):")
        for f in items:
            print(f"  [{f['cat']}] {f['title']}")
            print(f"    → {f['detail']}")

print(f"\nGesamt: {len(findings)} Findings "
      f"({len([f for f in findings if f['sev']=='ERROR'])} ERROR, "
      f"{len([f for f in findings if f['sev']=='WARN'])} WARN, "
      f"{len([f for f in findings if f['sev']=='INFO'])} INFO)")
