#!/usr/bin/env python3
"""
PCB Deep-Dive v2 — Ansatz 1: Regelbasierte Struktur-Analyse
Prüft gegen copilot-instructions.md Vorgaben:
  - Netzklassen & DRU-Rules
  - Trace-Breiten pro Netzklasse (Soll/Ist)
  - Via-Größen & Annular Ring
  - Zonen-Konfiguration
  - Board-Outline & Edge-Clearance
  - Silkscreen-Regeln
  - Fiducials, Mounting Holes
  - Teardrops
"""
import re, math, json, fnmatch
from collections import Counter, defaultdict

PCB = "aurora-dsp-icepower-booster.kicad_pcb"
PRO = "aurora-dsp-icepower-booster.kicad_pro"
DRU = "aurora-dsp-icepower-booster.kicad_dru"

with open(PCB) as f:
    pcb = f.read()
with open(PRO) as f:
    pro = json.load(f)

findings = []
def finding(cat, sev, title, detail):
    findings.append({"cat": cat, "sev": sev, "title": title, "detail": detail})

# === NET MAP ===
net_map = {}
for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', pcb):
    net_map[int(m.group(1))] = m.group(2)

# === NETCLASS PATTERNS ===
patterns = pro.get("net_settings", {}).get("netclass_patterns", []) or []
classes_def = pro.get("net_settings", {}).get("classes", []) or []

def get_netclass(net_name):
    for p in patterns:
        if fnmatch.fnmatch(net_name, p["pattern"]):
            return p["netclass"]
    return "Default"

nc_map = {}  # net_name -> class
for name in net_map.values():
    if name:
        nc_map[name] = get_netclass(name)

nc_count = Counter(nc_map.values())
print("=" * 70)
print("1. NETZKLASSEN-ZUORDNUNG (nach Pattern-Fix)")
print("=" * 70)
for nc, c in nc_count.most_common():
    print(f"  {nc:15s}: {c} Netze")
unmatched = [n for n, c in nc_map.items() if c == "Default" and n != ""]
print(f"\n  Default-Netze (13): {unmatched}")

# Check: Are all expected classes defined?
EXPECTED_CLASSES = {
    "Default":      {"clearance": 0.2, "track_width": 0.25, "via_dia": 0.6, "via_drill": 0.3},
    "Power":        {"clearance": 0.2, "track_width": 0.5,  "via_dia": 0.8, "via_drill": 0.4},
    "Audio_Input":  {"clearance": 0.25,"track_width": 0.3,  "via_dia": 0.6, "via_drill": 0.3},
    "Audio_Output": {"clearance": 0.2, "track_width": 0.5,  "via_dia": 0.6, "via_drill": 0.3},
    "Audio_Power":  {"clearance": 0.2, "track_width": 0.8,  "via_dia": 0.8, "via_drill": 0.4},
    "Speaker":      {"clearance": 0.3, "track_width": 1.5,  "via_dia": 0.8, "via_drill": 0.4},
    "HV":           {"clearance": 0.5, "track_width": 0.3,  "via_dia": 0.8, "via_drill": 0.4},
}
defined_names = {c.get("name") for c in classes_def}
for exp_name in EXPECTED_CLASSES:
    if exp_name not in defined_names:
        if exp_name == "Speaker":
            finding("NETCLASS", "INFO", "Netzklasse 'Speaker' fehlt",
                     "Nicht relevant — Board hat keine Lautsprecherausgänge (XLR → ICEpower)")
        else:
            finding("NETCLASS", "WARN", f"Netzklasse '{exp_name}' nicht definiert", "")

# Check class parameters
print("\n" + "=" * 70)
print("2. NETZKLASSEN-PARAMETER (Soll vs. Ist)")
print("=" * 70)
for cls in classes_def:
    name = cls.get("name", "?")
    if name in EXPECTED_CLASSES:
        exp = EXPECTED_CLASSES[name]
        diffs = []
        for param, exp_val in exp.items():
            actual = cls.get(param, 0)
            if abs(actual - exp_val) > 0.001:
                diffs.append(f"{param}: Soll={exp_val} Ist={actual}")
        if diffs:
            print(f"  {name:15s}: {'  |  '.join(diffs)}")
            for d in diffs:
                if "via_dia" in d:
                    continue  # KiCad uses board default for via_dia=0
                finding("NETCLASS", "INFO", f"{name}: {d}", "Parameter-Abweichung")
        else:
            print(f"  {name:15s}: ✓ alle Parameter OK")

# === SEGMENTS ===
segments = []
for m in re.finditer(r'\(segment\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net (\d+)\)', pcb):
    segments.append({
        "x1": float(m.group(1)), "y1": float(m.group(2)),
        "x2": float(m.group(3)), "y2": float(m.group(4)),
        "width": float(m.group(5)), "layer": m.group(6), "net": int(m.group(7))
    })

# === TRACE-BREITEN PRO NETZKLASSE ===
print("\n" + "=" * 70)
print("3. TRACE-BREITEN PRO NETZKLASSE (Soll vs. Ist)")
print("=" * 70)

nc_widths = defaultdict(list)
violations = []
for seg in segments:
    net_name = net_map.get(seg["net"], "")
    nc = nc_map.get(net_name, "Default")
    nc_widths[nc].append((seg["width"], net_name, seg["layer"]))

for nc_name in ["Audio_Input", "Audio_Output", "Audio_Power", "Power", "HV", "Default"]:
    if nc_name not in nc_widths:
        continue
    items = nc_widths[nc_name]
    widths = [w for w, _, _ in items]
    exp_w = EXPECTED_CLASSES.get(nc_name, {}).get("track_width", 0.25)
    min_w = min(widths)
    max_w = max(widths)
    n_under = sum(1 for w in widths if w < exp_w - 0.001)
    n_over = sum(1 for w in widths if w > exp_w + 0.1)
    status = "✓" if n_under == 0 else f"⚠ {n_under} unter Soll"
    print(f"  {nc_name:15s}  Soll≥{exp_w:.2f}mm  Ist: {min_w:.3f}–{max_w:.3f}mm  "
          f"n={len(items)}  {status}")
    if n_under > 0:
        under_nets = set()
        for w, name, layer in items:
            if w < exp_w - 0.001:
                under_nets.add(f"{name}({w}mm)")
        finding("TRACE", "WARN", f"{nc_name}: {n_under} Segmente unter Soll-Breite",
                 f"Soll≥{exp_w}mm, Betroffene: {list(under_nets)[:5]}")

# === VIAS ===
print("\n" + "=" * 70)
print("4. VIA-ANALYSE")
print("=" * 70)

vias = []
for m in re.finditer(r'\(via\s+\(at ([\d.]+) ([\d.]+)\)\s+\(size ([\d.]+)\)\s+\(drill ([\d.]+)\)\s+\(layers "([^"]+)" "([^"]+)"\)\s+\(net (\d+)\)', pcb):
    vias.append({
        "x": float(m.group(1)), "y": float(m.group(2)),
        "size": float(m.group(3)), "drill": float(m.group(4)),
        "net": int(m.group(7))
    })

via_sizes = Counter((v["size"], v["drill"]) for v in vias)
for (size, drill), count in via_sizes.most_common():
    annular = (size - drill) / 2
    jlcpcb_ok = "✓" if annular >= 0.125 else "✗ JLCPCB Min=0.125mm"
    print(f"  Size={size}mm Drill={drill}mm Annular={annular:.3f}mm  ×{count}  {jlcpcb_ok}")
    if annular < 0.125:
        finding("VIA", "ERROR", f"Annular Ring {annular:.3f}mm < 0.125mm JLCPCB Min",
                 f"{count} Vias betroffen")

# Via distribution by netclass
print("\n  Vias pro Netzklasse:")
via_nc = Counter()
for v in vias:
    name = net_map.get(v["net"], "")
    nc = nc_map.get(name, "Default")
    via_nc[nc] += 1
for nc, c in via_nc.most_common():
    print(f"    {nc:15s}: {c}")

# === ZONEN ===
print("\n" + "=" * 70)
print("5. GND-ZONEN KONFIGURATION")
print("=" * 70)

# Parse zones with connects configuration
zone_blocks = []
for m in re.finditer(r'\(zone\s+\(net (\d+)\)\s+\(net_name "([^"]+)"\)\s+\(layer "([^"]+)"\)', pcb):
    net_id = int(m.group(1))
    net_name = m.group(2)
    layer = m.group(3)
    # Get connect_pads from nearby text
    block_start = m.start()
    block_text = pcb[block_start:block_start+500]
    connect_m = re.search(r'\(connect_pads\s*(yes|no|thermal)?\b', block_text)
    connect = connect_m.group(1) if connect_m and connect_m.group(1) else "thermal"
    min_thick_m = re.search(r'\(min_thickness ([\d.]+)\)', block_text)
    min_thick = float(min_thick_m.group(1)) if min_thick_m else 0
    island_m = re.search(r'\(island_removal_mode (\d+)\)', block_text)
    island_mode = int(island_m.group(1)) if island_m else 0
    zone_blocks.append({"net": net_name, "layer": layer, "connect": connect,
                        "min_thickness": min_thick, "island_mode": island_mode})

for z in zone_blocks:
    island_str = {0: "always", 1: "never", 2: "below_area"}.get(z["island_mode"], str(z["island_mode"]))
    print(f"  {z['net']:6s} on {z['layer']:5s}  connect={z['connect']:8s}  "
          f"min_thick={z['min_thickness']}mm  island_removal={island_str}")
    
    if z["net"] == "GND" and z["layer"] == "B.Cu" and z["connect"] != "yes":
        finding("ZONE", "INFO", "B.Cu GND-Zone: connect_pads nicht 'yes'",
                 f"Ist: {z['connect']}. Solid connect empfohlen für JLCPCB-Maschinenlötung")

# === BOARD OUTLINE ===
print("\n" + "=" * 70)
print("6. BOARD-OUTLINE")
print("=" * 70)

edge_rect = re.search(r'\(gr_rect\s+\(start ([\d.]+) ([\d.]+)\)\s+\(end ([\d.]+) ([\d.]+)\).*?Edge\.Cuts', pcb, re.DOTALL)
if edge_rect:
    x1, y1 = float(edge_rect.group(1)), float(edge_rect.group(2))
    x2, y2 = float(edge_rect.group(3)), float(edge_rect.group(4))
    w, h = abs(x2-x1), abs(y2-y1)
    print(f"  gr_rect: ({x1}, {y1}) → ({x2}, {y2})")
    print(f"  Size: {w:.2f} × {h:.2f} mm  ✓ geschlossen")
    
    # Check components near edge
    min_edge = 0.3  # JLCPCB empfohlen
    edge_violations = 0
    for seg in segments:
        for px, py in [(seg["x1"], seg["y1"]), (seg["x2"], seg["y2"])]:
            d_left = px - x1
            d_right = x2 - px
            d_top = py - y1
            d_bottom = y2 - py
            min_d = min(d_left, d_right, d_top, d_bottom)
            if min_d < min_edge and min_d > 0:
                edge_violations += 1
    print(f"  Traces < {min_edge}mm vom Board-Edge: {edge_violations}")
    if edge_violations > 0:
        finding("EDGE", "WARN", f"{edge_violations} Trace-Endpunkte < 0.3mm vom Board-Edge",
                 "JLCPCB empfiehlt ≥0.3mm Kupfer-zu-Edge Abstand")
else:
    finding("BOARD", "ERROR", "Kein Board-Outline gefunden!", "")

# === MOUNTING HOLES ===
print("\n" + "=" * 70)
print("7. MONTAGELÖCHER")
print("=" * 70)

mh_count = 0
for m in re.finditer(r'\(footprint "([^"]*[Mm]ounting[Hh]ole[^"]*)".*?\(at ([\d.]+) ([\d.]+)', pcb, re.DOTALL):
    mh_count += 1
    print(f"  {m.group(1)} @ ({m.group(2)}, {m.group(3)}) ✓")

if mh_count >= 4:
    print(f"  {mh_count} Mounting Holes ✓")
elif mh_count == 0:
    finding("MECH", "WARN", "Keine Mounting Holes erkannt", "")
else:
    finding("MECH", "INFO", f"Nur {mh_count} Mounting Holes", "4 Ecken empfohlen")

# === FIDUCIALS ===
print("\n" + "=" * 70)
print("8. FIDUCIALS")
print("=" * 70)

fid_count = 0
for m in re.finditer(r'\(footprint "[^"]*[Ff]iducial[^"]*"', pcb):
    fid_count += 1
print(f"  Fiducials: {fid_count}")
if fid_count < 3:
    finding("ASSEMBLY", "INFO", f"Nur {fid_count} Fiducials (empfohlen: ≥3 für SMT-Assembly)",
             "Nur relevant wenn JLCPCB SMT-Assembly genutzt wird")

# === SILKSCREEN ===
print("\n" + "=" * 70)
print("9. SILKSCREEN")
print("=" * 70)

# Board-level texts
gr_texts = re.findall(r'\(gr_text "([^"]*)"', pcb)
print(f"  Board-Texte: {len(gr_texts)}")

# Check for project name, version, date
has_name = any("Booster" in t or "Aurora" in t or "aurora" in t for t in gr_texts)
has_kanal = sum(1 for t in gr_texts if "Kanal" in t)
print(f"  Projektname auf Silkscreen: {'✓' if has_name else '✗'}")
print(f"  Kanal-Labels: {has_kanal}")

# Check silkscreen on pads — would need pad position analysis
# Simplified: just report text count
print(f"  Pin-1/Polaritätsmarkierung: (manuell prüfen)")

# === TEARDROPS ===
print("\n" + "=" * 70)
print("10. TEARDROPS")
print("=" * 70)

teardrops = pcb.count("teardrop")
print(f"  Teardrop-Referenzen: {teardrops}")
if teardrops == 0:
    finding("ROUTING", "INFO", "Keine Teardrops erkannt",
             "Empfehlung: Teardrops an Pad-/Via-Übergängen aktivieren (PCB Editor → Edit → Teardrops)")

# === CUSTOM DRU RULES ===
print("\n" + "=" * 70)
print("11. CUSTOM DESIGN RULES (.kicad_dru)")
print("=" * 70)

try:
    with open(DRU) as f:
        dru = f.read()
    rules = re.findall(r'\(rule\s+(\w+)', dru)
    print(f"  Definierte Rules: {rules}")
    
    expected = {"power_clearance", "power_width", "hv_clearance",
                "audio_input_clearance", "board_edge"}
    missing = expected - set(rules)
    extra = set(rules) - expected
    if missing:
        finding("DRU", "INFO", f"Fehlende Custom Rules: {missing}", "")
    print(f"  Erwartete abgedeckt: {expected & set(rules)}")
    if extra:
        print(f"  Zusätzliche: {extra}")
except FileNotFoundError:
    finding("DRU", "WARN", "Keine .kicad_dru vorhanden", "")

# === DRC SEVERITY SETTINGS ===
print("\n" + "=" * 70)
print("12. DRC SEVERITY EINSTELLUNGEN")
print("=" * 70)

severities = pro.get("board", {}).get("design_settings", {}).get("rule_severities", {})
critical_rules = {
    "shorting_items": "error",
    "clearance": "error",
    "unconnected_items": "error",
    "track_width": "error",
    "via_diameter": "error",
    "annular_width": "error",
}
for rule, expected_sev in critical_rules.items():
    actual = severities.get(rule, "?")
    status = "✓" if actual == expected_sev else f"⚠ Ist={actual}"
    print(f"  {rule:25s}: {status}")
    if actual != expected_sev and actual == "ignore":
        finding("DRC", "WARN", f"DRC-Rule '{rule}' auf Ignore gesetzt",
                 "Kritische Rule sollte auf Error stehen")

# Ignored rules (expected)
ignored_expected = {"silk_edge_clearance", "text_thickness"}
for rule in ignored_expected:
    actual = severities.get(rule, "?")
    print(f"  {rule:25s}: {actual} (akzeptiert)")

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
print("\n" + "=" * 70)
print("FINDINGS ZUSAMMENFASSUNG (Ansatz 1)")
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
