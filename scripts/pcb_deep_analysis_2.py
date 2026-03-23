#!/usr/bin/env python3
"""
Ansatz 2: Geometrische + Audio-Design-Analyse
Prüft Platzierung, Abstände, Entkopplung, Signalführung, thermische Aspekte
"""
import re, math, json
from collections import Counter, defaultdict

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB, "r") as f:
    text = f.read()

findings = []
def finding(cat, sev, title, detail):
    findings.append({"cat": cat, "sev": sev, "title": title, "detail": detail})

# ============================================================
# Parse all footprints with reference, value, position
# ============================================================
footprints = {}
# Use a balanced-paren parser to extract footprints
def extract_top_level_parens(text, keyword):
    """Extract all top-level (keyword ...) blocks."""
    results = []
    search_str = f"({keyword} "
    idx = 0
    while True:
        start = text.find(search_str, idx)
        if start == -1:
            break
        depth = 0
        i = start
        while i < len(text):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    results.append(text[start:i+1])
                    idx = i + 1
                    break
            i += 1
        else:
            break
    return results

fp_blocks = extract_top_level_parens(text, "footprint")

for block in fp_blocks:
    ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
    val_m = re.search(r'\(property "Value" "([^"]+)"', block)
    fp_m = re.match(r'\(footprint "([^"]+)"', block)
    at_m = re.search(r'^\(footprint "[^"]+"\s+\(layer "[^"]+"\)\s+\(uuid "[^"]+"\)\s+\(at ([\d.]+) ([\d.]+)(?:\s+([\d.-]+))?\)', block)
    
    if ref_m and at_m:
        ref = ref_m.group(1)
        footprints[ref] = {
            "ref": ref,
            "value": val_m.group(1) if val_m else "?",
            "fp": fp_m.group(1) if fp_m else "?",
            "x": float(at_m.group(1)),
            "y": float(at_m.group(2)),
            "angle": float(at_m.group(3)) if at_m.group(3) else 0,
            "block": block
        }

print(f"Parsed {len(footprints)} Footprints mit Referenz")

# Build net map
net_map = {}
for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', text):
    net_map[int(m.group(1))] = m.group(2)

# Parse segments
segments = []
for m in re.finditer(r'\(segment\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net (\d+)\)', text):
    segments.append({
        "x1": float(m.group(1)), "y1": float(m.group(2)),
        "x2": float(m.group(3)), "y2": float(m.group(4)),
        "width": float(m.group(5)), "layer": m.group(6), "net": int(m.group(7))
    })

# Parse vias
vias = []
for m in re.finditer(r'\(via\s+\(at ([\d.]+) ([\d.]+)\)\s+\(size ([\d.]+)\)\s+\(drill ([\d.]+)\)\s+\(layers "([^"]+)" "([^"]+)"\)\s+\(net (\d+)\)', text):
    vias.append({
        "x": float(m.group(1)), "y": float(m.group(2)),
        "size": float(m.group(3)), "drill": float(m.group(4)),
        "net": int(m.group(7))
    })

def dist(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

# ============================================================
# 1. IC-ENTKOPPLUNG: Abstand Bypass-Cap zu IC
# ============================================================
print("\n" + "=" * 70)
print("1. IC-ENTKOPPLUNGS-ANALYSE (Cap-zu-IC Abstand)")
print("=" * 70)

# Find ICs (U references)
ics = {r: f for r, f in footprints.items() if r.startswith("U")}
# Find capacitors (C references)
caps = {r: f for r, f in footprints.items() if r.startswith("C") and not r.startswith("CH")}

print(f"  ICs: {len(ics)}, Kondensatoren: {len(caps)}")

# For each IC, find nearest caps
for ic_ref, ic in sorted(ics.items()):
    nearest_caps = []
    for cap_ref, cap in caps.items():
        d = dist(ic["x"], ic["y"], cap["x"], cap["y"])
        nearest_caps.append((d, cap_ref, cap["value"]))
    nearest_caps.sort()
    
    # Check: should have at least one cap within 3mm
    near_3mm = [c for c in nearest_caps if c[0] <= 3.0]
    near_5mm = [c for c in nearest_caps if c[0] <= 5.0]
    
    status = "OK" if near_3mm else ("~" if near_5mm else "⚠")
    closest = nearest_caps[0] if nearest_caps else (999, "?", "?")
    print(f"  {ic_ref:6s} ({ic['value']:12s}) @ ({ic['x']:6.1f}, {ic['y']:6.1f})  "
          f"nearest_cap={closest[1]} ({closest[2]}) d={closest[0]:.1f}mm  "
          f"[{len(near_3mm)} ≤3mm, {len(near_5mm)} ≤5mm] {status}")
    
    if not near_3mm:
        finding("DECOUPLING", "WARN", f"{ic_ref}: Kein Bypass-Cap ≤ 3mm",
                 f"Nächster Cap: {closest[1]} ({closest[2]}) @ {closest[0]:.1f}mm. "
                 f"Empfehlung: 100nF C0G direkt am IC-Pin")

# ============================================================
# 2. AUDIO-SIGNAL vs DIGITAL-ABSTAND
# ============================================================
print("\n" + "=" * 70)
print("2. AUDIO-DIGITAL SEPARATION")
print("=" * 70)

# Categorize nets
PRO = PCB.replace(".kicad_pcb", ".kicad_pro")
with open(PRO, "r") as f:
    pro = json.load(f)

net_settings = pro.get("net_settings", {})
classes = net_settings.get("classes", [])
net_to_class = {}
for cls in classes:
    for n in cls.get("nets", []):
        net_to_class[n] = cls.get("name", "Default")

# Separate audio segments from digital
audio_segs = [s for s in segments if net_to_class.get(net_map.get(s["net"], ""), "Default") in ("Audio_Input", "Audio_Output")]
digital_segs = [s for s in segments if net_to_class.get(net_map.get(s["net"], ""), "Default") == "Default"]

print(f"  Audio-Segmente: {len(audio_segs)}")
print(f"  Default-Segmente: {len(digital_segs)}")
print(f"  (Audio/Default Separation nur relevant wenn Default digitale Signale enthält)")

# ============================================================
# 3. KANALBEREICHE ANALYSIEREN
# ============================================================
print("\n" + "=" * 70)
print("3. KANAL-PLATZIERUNG (6 Kanäle)")
print("=" * 70)

# Group components by channel
channels = defaultdict(list)
for ref, fp in footprints.items():
    # Detect channel from reference patterns or Y-position
    # Channel spacing is ~28mm starting from Y~37.8
    pass

# Detect channel Y-ranges from Kanal labels
kanal_ys = {}
for m in re.finditer(r'\(gr_text "Kanal (\d)".*?\(at ([\d.]+) ([\d.]+)', text):
    kanal_ys[int(m.group(1))] = float(m.group(3))

for ch, y in sorted(kanal_ys.items()):
    print(f"  Kanal {ch}: Y={y:.1f}mm")

if len(kanal_ys) >= 2:
    ys = sorted(kanal_ys.values())
    spacings = [ys[i+1] - ys[i] for i in range(len(ys)-1)]
    avg_spacing = sum(spacings) / len(spacings)
    print(f"  Durchschn. Kanal-Abstand: {avg_spacing:.1f}mm")

# ============================================================
# 4. COMPONENT-ORIENTIERUNG (R/C Konsistenz)
# ============================================================
print("\n" + "=" * 70)
print("4. BAUTEIL-ORIENTIERUNG (R/C)")
print("=" * 70)

resistors = {r: f for r, f in footprints.items() if r.startswith("R") and r[1:].isdigit()}
capacitors = {r: f for r, f in footprints.items() if r.startswith("C") and r[1:].isdigit()}

r_angles = Counter(int(f["angle"]) % 360 for f in resistors.values())
c_angles = Counter(int(f["angle"]) % 360 for f in capacitors.values())

print(f"  Widerstände ({len(resistors)}): Winkel = {dict(r_angles.most_common())}")
print(f"  Kondensatoren ({len(capacitors)}): Winkel = {dict(c_angles.most_common())}")

# Check consistency
for comp_type, angles, name in [(r_angles, resistors, "R"), (c_angles, capacitors, "C")]:
    total = sum(comp_type.values())
    dominant = comp_type.most_common(1)[0][1] if comp_type else 0
    if total > 5 and dominant / total < 0.7:
        finding("PLACEMENT", "INFO", f"{name}-Orientierung inkonsistent",
                 f"Verteilung: {dict(comp_type.most_common())} — "
                 f"Gleiche Orientierung erleichtert Bestückung")

# ============================================================
# 5. THERMISCHE ANALYSE
# ============================================================
print("\n" + "=" * 70)
print("5. THERMISCHE ANALYSE")
print("=" * 70)

# Check for thermal pads (exposed pads) in IC footprints
thermal_pad_ics = []
for ic_ref, ic in ics.items():
    block = ic["block"]
    # Look for pad with type thru_hole or smd that's larger than normal
    exposed_pads = re.findall(r'\(pad ""\s+smd\s+rect.*?\(size ([\d.]+) ([\d.]+)\)', block)
    thermal_pads = re.findall(r'\(pad "\d*"\s+smd\s+rect.*?\(size ([\d.]+) ([\d.]+)\)', block)
    
    # Check for pads > 2mm (likely thermal)
    for padlist in [exposed_pads, thermal_pads]:
        for pw, ph in padlist:
            if float(pw) > 2 or float(ph) > 2:
                thermal_pad_ics.append(ic_ref)
                break

# Check for thermal vias near these ICs
for ic_ref in set(thermal_pad_ics):
    ic = ics[ic_ref]
    gnd_net = None
    for nid, name in net_map.items():
        if name == "GND":
            gnd_net = nid
            break
    
    nearby_gnd_vias = [v for v in vias if v["net"] == gnd_net and dist(v["x"], v["y"], ic["x"], ic["y"]) < 5]
    print(f"  {ic_ref} ({ic['value']}): Thermal Pad erkannt, {len(nearby_gnd_vias)} GND-Vias ≤5mm")
    if len(nearby_gnd_vias) < 5:
        finding("THERMAL", "WARN", f"{ic_ref}: Wenige Thermal-Vias ({len(nearby_gnd_vias)})",
                 "Empfehlung: mind. 5×5 Via-Array unter Thermal Pad (0.3mm Drill, 1.0-1.2mm Raster)")

# ============================================================
# 6. STECKVERBINDER-POSITION (Board-Rand)
# ============================================================
print("\n" + "=" * 70)
print("6. STECKVERBINDER-POSITIONEN")
print("=" * 70)

connectors = {r: f for r, f in footprints.items() if r.startswith("J")}
for ref, conn in sorted(connectors.items()):
    print(f"  {ref:5s} ({conn['value']:20s}) @ ({conn['x']:7.2f}, {conn['y']:7.2f}) angle={conn['angle']:.0f}°")

# ============================================================
# 7. TRACE-ROUTING WINKEL (45° Check)
# ============================================================
print("\n" + "=" * 70)
print("7. TRACE-WINKEL-ANALYSE")
print("=" * 70)

angles = []
right_angles = 0
n45 = 0
for seg in segments:
    dx = seg["x2"] - seg["x1"]
    dy = seg["y2"] - seg["y1"]
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        continue
    angle = math.degrees(math.atan2(dy, dx)) % 180
    angles.append(angle)
    # 90° angles (exact horizontal or vertical are fine)
    if abs(angle) < 0.1 or abs(angle - 90) < 0.1 or abs(angle - 180) < 0.1:
        right_angles += 1
    elif abs(angle - 45) < 0.1 or abs(angle - 135) < 0.1:
        n45 += 1

# Check for any odd angles (not 0, 45, 90, 135)
odd_angles = 0
for a in angles:
    normalized = a % 45
    if normalized > 1 and normalized < 44:
        odd_angles += 1

print(f"  Gesamt Segmente mit Richtung: {len(angles)}")
print(f"  0°/90° (ortho): {right_angles} ({right_angles/max(len(angles),1)*100:.0f}%)")
print(f"  45°/135°: {n45} ({n45/max(len(angles),1)*100:.0f}%)")
print(f"  Andere Winkel: {odd_angles} ({odd_angles/max(len(angles),1)*100:.0f}%)")

if odd_angles > 0:
    finding("ROUTING", "INFO", f"{odd_angles} Traces mit ungewöhnlichem Winkel",
             "Empfehlung: 45°-Winkel statt willkürliche Winkel")

# ============================================================
# 8. GUARD-TRACES PRÜFUNG
# ============================================================
print("\n" + "=" * 70)
print("8. GUARD-TRACE ANALYSE (Audio-Eingänge)")
print("=" * 70)

# Check if there are GND traces running parallel to audio input traces
gnd_net_id = None
for nid, name in net_map.items():
    if name == "GND":
        gnd_net_id = nid
        break

gnd_segs = [s for s in segments if s["net"] == gnd_net_id]
print(f"  GND-Segmente (potentielle Guards): {len(gnd_segs)}")
print(f"  Audio_Input Segmente: {len(audio_segs)}")

if len(audio_segs) > 0 and len(gnd_segs) == 0:
    finding("AUDIO", "WARN", "Keine GND-Guard-Traces erkannt",
             "Empfehlung: GND-Leiterbahnen beidseitig um empfindliche Audio-Eingangssignale")

# ============================================================
# 9. ESD-SCHUTZ / TVS-DIODEN
# ============================================================
print("\n" + "=" * 70)
print("9. ESD-SCHUTZ (TVS-Dioden)")
print("=" * 70)

diodes = {r: f for r, f in footprints.items() if r.startswith("D")}
tvs_diodes = {r: f for r, f in diodes.items() if "TVS" in f.get("value", "").upper() or "SMBJ" in f.get("value", "").upper() or "PESD" in f.get("value", "").upper() or "CDSOD" in f.get("value", "").upper() or "ESD" in f.get("value", "").upper()}

print(f"  Dioden gesamt: {len(diodes)}")
print(f"  TVS/ESD-Dioden: {len(tvs_diodes)}")

# Check: TVS near each connector
for conn_ref, conn in connectors.items():
    nearest_tvs = None
    min_d = float('inf')
    for tvs_ref, tvs in tvs_diodes.items():
        d = dist(conn["x"], conn["y"], tvs["x"], tvs["y"])
        if d < min_d:
            min_d = d
            nearest_tvs = tvs_ref
    if min_d < 15:
        print(f"  {conn_ref} ({conn['value'][:15]}): Nächste TVS = {nearest_tvs} @ {min_d:.1f}mm ✓")
    else:
        print(f"  {conn_ref} ({conn['value'][:15]}): Keine TVS in der Nähe ⚠ (min={min_d:.1f}mm)")

# ============================================================
# 10. ZOBEL-NETZWERK CHECK
# ============================================================
print("\n" + "=" * 70)
print("10. ZOBEL-NETZWERK / OUTPUT-SCHUTZ")
print("=" * 70)

# Look for series R+C combinations at outputs (10Ω + 100nF typical)
zobel_rs = {r: f for r, f in footprints.items() if r.startswith("R") and f.get("value", "") in ("10", "10R", "10Ω")}
print(f"  10Ω Widerstände (Zobel-Kandidaten): {len(zobel_rs)}")
for ref, fp in zobel_rs.items():
    print(f"    {ref}: ({fp['x']:.1f}, {fp['y']:.1f})")

# ============================================================
# 11. POWER-TRACE ANALYSE (Strombelastbarkeit)
# ============================================================
print("\n" + "=" * 70)
print("11. POWER-TRACE BREITEN")
print("=" * 70)

power_nets = {}
for nid, name in net_map.items():
    if any(kw in name.upper() for kw in ["VCC", "+5V", "+3V3", "+12V", "-12V", "V_BAT", "V+", "V-"]):
        power_nets[nid] = name

for nid, name in sorted(power_nets.items(), key=lambda x: x[1]):
    pwr_segs = [s for s in segments if s["net"] == nid]
    if pwr_segs:
        widths = [s["width"] for s in pwr_segs]
        layers = Counter(s["layer"] for s in pwr_segs)
        print(f"  {name:12s}: {len(pwr_segs)} segs, width={min(widths):.2f}-{max(widths):.2f}mm, layers={dict(layers)}")
        if min(widths) < 0.5:
            finding("POWER", "WARN", f"Power-Trace '{name}' zu schmal",
                     f"min={min(widths):.2f}mm < 0.5mm Empfehlung für Power-Netze")

# ============================================================
# 12. BOARD-OUTLINE ANALYSE (nach gr_rect oder gr_poly)
# ============================================================
print("\n" + "=" * 70)
print("12. BOARD-OUTLINE")
print("=" * 70)

# Check all Edge.Cuts elements
edge_rects = re.findall(r'\(gr_rect\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\).*?\(layer "Edge\.Cuts"\)', text)
edge_lines = re.findall(r'\(gr_line\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\).*?\(layer "Edge\.Cuts"\)', text)
edge_arcs = re.findall(r'\(gr_arc.*?\(layer "Edge\.Cuts"\)', text)

print(f"  Rect: {len(edge_rects)}, Lines: {len(edge_lines)}, Arcs: {len(edge_arcs)}")

for r in edge_rects:
    print(f"  Rect: ({r[0]}, {r[1]}) → ({r[2]}, {r[3]})")
    w = abs(float(r[2]) - float(r[0]))
    h = abs(float(r[3]) - float(r[1]))
    print(f"  Size: {w:.2f} × {h:.2f} mm")

# ============================================================
# 13. DANGLING VIAS / STUBS
# ============================================================
print("\n" + "=" * 70)
print("13. DANGLING VIAS / STUBS")
print("=" * 70)

# A via is "dangling" if no segment connects to it on at least one layer
via_positions = defaultdict(lambda: {"F.Cu": False, "B.Cu": False})
for v in vias:
    key = (round(v["x"], 4), round(v["y"], 4))
    via_positions[key]["net"] = v["net"]

# Check segment endpoints
for seg in segments:
    for px, py in [(seg["x1"], seg["y1"]), (seg["x2"], seg["y2"])]:
        key = (round(px, 4), round(py, 4))
        if key in via_positions:
            via_positions[key][seg["layer"]] = True

# Also check if via is within a pad of a footprint (harder to detect)
dangling_count = 0
for pos, info in via_positions.items():
    if not info.get("F.Cu") and not info.get("B.Cu"):
        # Via with no traces on either layer - might be in a pad or zone-only
        dangling_count += 1

print(f"  Vias ohne Trace-Anbindung: {dangling_count} (können Pad- oder Zone-angebunden sein)")

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
print("\n" + "=" * 70)
print("FINDINGS ZUSAMMENFASSUNG (Ansatz 2)")
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
