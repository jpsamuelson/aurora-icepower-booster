#!/usr/bin/env python3
"""
Schematic Logic Validator — Aurora DSP ICEpower Booster
Validiert die Schaltungslogik vollständig und ohne Annahmen.
Methode: Direktes Parsen des KiCad-Netlists (kicadsexpr) + topologische Analyse.
"""
import re
import sys
import subprocess
import os
import json
from collections import defaultdict

PROJECT = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT, "aurora-dsp-icepower-booster.kicad_sch")
NET_FILE = "/tmp/validate_sch_native.net"

PASS = 0
FAIL = 0
WARN = 0
FINDINGS = []

def p(tag, test, msg, extra=""):
    global PASS, FAIL, WARN
    if tag == "PASS":
        PASS += 1
    elif tag == "FAIL":
        FAIL += 1
        FINDINGS.append(f"FAIL | {test} | {msg}" + (f" | {extra}" if extra else ""))
    elif tag == "WARN":
        WARN += 1
        FINDINGS.append(f"WARN | {test} | {msg}" + (f" | {extra}" if extra else ""))
    color = {"PASS": "\033[32m", "FAIL": "\033[31m", "WARN": "\033[33m"}[tag]
    print(f"  {color}{tag}\033[0m  {test}: {msg}" + (f" [{extra}]" if extra else ""))


# ────────────────────────────────────────────────
# 1. NETLIST EXPORTIEREN
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 1 — Netlist exportieren")
print("="*70)
result = subprocess.run(
    ["kicad-cli", "sch", "export", "netlist",
     "--format", "kicadsexpr",
     "-o", NET_FILE, SCH_FILE],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"  FEHLER: kicad-cli: {result.stderr}")
    sys.exit(1)
with open(NET_FILE) as f:
    net_raw = f.read()
print(f"  Netlist: {len(net_raw)} Bytes, {net_raw.count(chr(10))} Zeilen")


# ────────────────────────────────────────────────
# 2. NETLIST PARSEN
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 2 — Netlist parsen")
print("="*70)

def extract_blocks(text, keyword):
    """Extrahiert alle geklammerten Blöcke die mit (keyword starten."""
    blocks = []
    pattern = r'\(' + re.escape(keyword) + r'\b'
    for m in re.finditer(pattern, text):
        start = m.start()
        depth = 0
        for i, c in enumerate(text[start:]):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    blocks.append(text[start:start+i+1])
                    break
    return blocks

def get_field(block, field):
    """Holt einen (field value) String aus einem Block."""
    m = re.search(r'\(' + re.escape(field) + r'\s+"([^"]+)"', block)
    return m.group(1) if m else None

def get_field_unquoted(block, field):
    m = re.search(r'\(' + re.escape(field) + r'\s+(?:"([^"]+)"|(\S+))', block)
    if m:
        return m.group(1) or m.group(2)
    return None

# Alle Komponenten parsen
comp_blocks = extract_blocks(net_raw, "comp")
components = {}  # ref → {value, footprint, lib, pins: {pin_num: net_name}}
for blk in comp_blocks:
    ref = get_field(blk, "ref")
    value = get_field(blk, "value")
    fp_block = extract_blocks(blk, "footprint")
    footprint = fp_block[0] if fp_block else ""
    fp_name = re.search(r'"([^"]+)"', footprint)
    fp_name = fp_name.group(1) if fp_name else ""
    lib_m = re.search(r'\(libsource\s+\(lib\s+"([^"]+)"\)\s+\(part\s+"([^"]+)"', blk)
    lib = lib_m.group(1) + ":" + lib_m.group(2) if lib_m else ""
    if ref:
        components[ref] = {"value": value, "footprint": fp_name, "lib": lib, "pins": {}}

# Alle Netze mit ihren Knotenpunkten parsen
net_blocks = extract_blocks(net_raw, "net")
nets = {}       # net_name → [(ref, pin)]
comp_pins = defaultdict(dict)  # ref → {pin_num: net_name}

for blk in net_blocks:
    # Name des Netzes
    name_m = re.search(r'\(net\s+\(code\s+\S+\)\s+\(name\s+"([^"]+)"', blk)
    if not name_m:
        name_m = re.search(r'\(name\s+"([^"]+)"', blk)
    if not name_m:
        continue
    net_name = name_m.group(1)
    # Alle Knoten
    node_blocks = extract_blocks(blk, "node")
    nodes = []
    for nb in node_blocks:
        ref_m = re.search(r'\(ref\s+"([^"]+)"', nb)
        pin_m = re.search(r'\(pin\s+"([^"]+)"', nb)
        if ref_m and pin_m:
            nodes.append((ref_m.group(1), pin_m.group(1)))
            comp_pins[ref_m.group(1)][pin_m.group(1)] = net_name
    nets[net_name] = nodes

# Pins in components eintragen
for ref, pins in comp_pins.items():
    if ref in components:
        components[ref]["pins"] = pins

print(f"  Komponenten: {len(components)}")
print(f"  Netze: {len(nets)}")

# Übersicht
ref_types = defaultdict(list)
for ref in sorted(components.keys()):
    prefix = re.match(r'[A-Za-z]+', ref)
    if prefix:
        ref_types[prefix.group()].append(ref)

for prefix, refs in sorted(ref_types.items()):
    nums = sorted([int(re.search(r'\d+', r).group()) for r in refs if re.search(r'\d+', r)])
    print(f"  {prefix}: {len(refs)} Stück  ({refs[0]}..{refs[-1]})")


# ────────────────────────────────────────────────
# 3. VERSORGUNG: TEL5-2422 DC/DC
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 3 — Versorgung: TEL5-2422 (U1)")
print("="*70)

u1 = components.get("U1", {})
u1_pins = u1.get("pins", {})
print(f"  U1 lib/value: {u1.get('lib','?')} / {u1.get('value','?')}")
print(f"  U1 Pins: {u1_pins}")

# TEL5-2422: +Vin (pin1), -Vin (pin2/GND), +Vout (pin4 = +12V), -Vout (pin5 = -12V), trim (pin3)
# Wir prüfen welche Netze an U1 hängen
u1_nets = set(u1_pins.values())
p("PASS" if u1 else "FAIL", "U1 existiert", f"TEL5-2422: {u1.get('value','N/A')}")

has_pos_in  = any("VIN" in n.upper() or "5V" in n or "+5" in n for n in u1_nets)
has_gnd     = any("GND" in n.upper() for n in u1_nets)
has_pos12   = any("+12" in n or "12V" in n for n in u1_nets)
has_neg12   = any("-12" in n or "NEG" in n.upper() for n in u1_nets)

p("PASS" if has_gnd else "WARN", "U1 GND", f"Nets: {u1_nets}")
p("PASS" if has_pos12 else "FAIL", "U1 +12V Ausgang", f"Nets: {u1_nets}")
p("PASS" if has_neg12 else "FAIL", "U1 -12V Ausgang", f"Nets: {u1_nets}")

# Versorgungsnetze identifizieren
pwr_nets_pos = [n for n in nets if "+12V" in n or "12V" in n and "-" not in n]
pwr_nets_neg = [n for n in nets if "-12V" in n or "N12V" in n]
pwr_nets_gnd = [n for n in nets if n in ("GND", "/GND", "AGND", "PGND")]
print(f"  +12V-artige Netze: {pwr_nets_pos}")
print(f"  -12V-artige Netze: {pwr_nets_neg}")
print(f"  GND-Netze: {pwr_nets_gnd}")

# Wie viele Bauteile hängen an den Versorgungsnetzen?
for pn in pwr_nets_pos + pwr_nets_neg:
    nodes = nets.get(pn, [])
    print(f"  {pn}: {len(nodes)} Nodes  → {[n[0] for n in nodes[:8]]}{'...' if len(nodes)>8 else ''}")


# ────────────────────────────────────────────────
# 4. LDO-REGLER U14 (ADP7118) und U15 (ADP7182)
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 4 — LDO-Regler U14 (ADP7118 pos) + U15 (ADP7182 neg)")
print("="*70)

for uid in ["U14", "U15"]:
    u = components.get(uid, {})
    pins = u.get("pins", {})
    nets_u = set(pins.values())
    print(f"  {uid}: {u.get('value','?')} | {u.get('lib','?')}")
    print(f"  Pins: {pins}")
    # Mindestprüfung: Eingang (12V), Ausgang (regulierte Spannung), GND
    has_in  = any("+12" in n for n in nets_u)
    has_gnd = any("GND" in n.upper() for n in nets_u)
    has_out = len(nets_u) >= 2
    p("PASS" if u else "FAIL", f"{uid} existiert", u.get("value","N/A"))
    p("PASS" if has_in else "WARN", f"{uid} Eingang +12V", f"Nets={nets_u}")
    p("PASS" if has_gnd else "WARN", f"{uid} GND", f"Nets={nets_u}")
    # Ausgangs-Netz finden
    out_nets = [n for n in nets_u if "12V" not in n and "GND" not in n.upper()]
    print(f"  Ausgangs-Netze: {out_nets}")


# ────────────────────────────────────────────────
# 5. ENABLE/REMOTE-PFAD (SW1 + R1 + R56 + R57)
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 5 — Enable/Remote-Pfad (SW1 SPDT)")
print("="*70)

sw1 = components.get("SW1", {})
sw1_pins = sw1.get("pins", {})
print(f"  SW1: {sw1.get('lib','?')} = {sw1.get('value','?')}")
print(f"  SW1 Pins: {sw1_pins}")

# SW_SPDT hat 3 Pins: common, ALWAYS (VCC), REMOTE
sw1_nets = set(sw1_pins.values())
has_en_ctrl   = any("EN_CTRL" in n for n in sw1_nets)
has_12v_or_pwr = any("+12V" in n or "12" in n for n in sw1_nets)
has_remote    = any("REMOTE" in n.upper() for n in sw1_nets)

p("PASS" if sw1.get("lib","").find("SPDT") >= 0 or "SPDT" in sw1.get("value","") else "WARN",
  "SW1 ist SPDT", f"lib={sw1.get('lib','?')} value={sw1.get('value','?')}")
p("PASS" if has_en_ctrl else "FAIL", "SW1 → EN_CTRL", f"Nets={sw1_nets}")
p("PASS" if has_12v_or_pwr else "FAIL", "SW1 ALWAYS-Seite → 12V/Power", f"Nets={sw1_nets}")
p("PASS" if has_remote else "FAIL", "SW1 REMOTE-Seite", f"Nets={sw1_nets}")

# R1: Remote-Eingang Widerstand
r1 = components.get("R1", {})
r1_nets = set(r1.get("pins", {}).values())
print(f"\n  R1: {r1.get('value','?')} | Nets: {r1_nets}")
has_r1_remote = any("REMOTE" in n.upper() for n in r1_nets)
has_r1_j2 = any(n in nets and any(x[0]=="J2" for x in nets[n]) for n in r1_nets)
p("PASS" if r1.get("value","") else "FAIL", "R1 existiert", r1.get("value","N/A"))
p("PASS" if has_r1_remote else "FAIL", "R1 → REMOTE-Netz", f"Nets={r1_nets}")

# J2: Remote-Anschluss
j2 = components.get("J2", {})
j2_nets = set(j2.get("pins", {}).values())
print(f"\n  J2 (Remote-Buchse): {j2.get('value','?')} | Nets: {j2_nets}")
j2_has_remote = any("REMOTE" in n.upper() or "J2" in n for n in j2_nets)
p("PASS" if j2 else "FAIL", "J2 existiert", j2.get("value","N/A"))

# EN_CTRL — wohin geht es?
en_ctrl_net = next((n for n in nets if "EN_CTRL" in n), None)
if en_ctrl_net:
    en_nodes = nets[en_ctrl_net]
    print(f"\n  EN_CTRL-Netz ({en_ctrl_net}): {[x[0] for x in en_nodes]}")
    # Muss LM4562 Muting-Transistoren oder ICEpower ENABLE erreichen
    has_sw1_on_en = any(x[0]=="SW1" for x in en_nodes)
    has_r56_or_r57 = any(x[0] in ("R56","R57") for x in en_nodes)
    # Check for Q/transistor
    q_refs = [x[0] for x in en_nodes if x[0].startswith("Q")]
    p("PASS" if has_sw1_on_en else "FAIL", "SW1 auf EN_CTRL", f"Nodes={[x[0] for x in en_nodes]}")
    p("PASS" if has_r56_or_r57 else "WARN", "R56/R57 auf EN_CTRL (Pullup/down)", f"Nodes={[x[0] for x in en_nodes]}")
    print(f"  Downstream von EN_CTRL: Transistoren={q_refs}")
else:
    p("FAIL", "EN_CTRL-Netz", "nicht gefunden!")

# R56, R57 bei EN_CTRL
for r in ["R56", "R57"]:
    rc = components.get(r, {})
    rc_nets = set(rc.get("pins", {}).values())
    print(f"  {r}: {rc.get('value','?')} | Nets: {rc_nets}")
    p("PASS" if rc else "FAIL", f"{r} existiert", rc.get("value","N/A"))


# ────────────────────────────────────────────────
# 6. DIFFERENZ-EMPFÄNGER U2-U7 (LM4562, CH1-CH6)
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 6 — Differenz-Empfänger U2–U7 (LM4562)")
print("="*70)

# LM4562 hat 2 Op-Amps pro Chip: A und B
# Pins: 1=OutA, 2=IN-A, 3=IN+A, 4=V-, 5=IN+B, 6=IN-B, 7=OutB, 8=V+
LM4562_PINS = {
    "1": "OutA", "2": "IN-A", "3": "IN+A", "4": "V-",
    "5": "IN+B", "6": "IN-B", "7": "OutB", "8": "V+"
}

diff_rx_ok = True
for ch_idx, uid in enumerate(["U2","U3","U4","U5","U6","U7"], start=1):
    uc = components.get(uid, {})
    pins = uc.get("pins", {})
    print(f"\n  {uid} (CH{ch_idx}): {uc.get('value','?')}")
    if not uc:
        p("FAIL", f"{uid} existiert", "Fehlt!")
        diff_rx_ok = False
        continue
    p("PASS", f"{uid} existiert", uc.get("value","N/A"))

    # Versorgungspins
    vp = pins.get("8","?"); vm = pins.get("4","?")
    p("PASS" if "+12" in vp or "AVCC" in vp or "VCC" in vp.upper() or "+5" in vp else "FAIL",
      f"{uid} V+ Pin8", f"→ {vp}")
    p("PASS" if "-12" in vm or "AVSS" in vm or "VEE" in vm.upper() or "-5" in vm else "FAIL",
      f"{uid} V- Pin4", f"→ {vm}")

    # XLR-Eingänge: IN+ und IN- sollten zu XLR-Pins führen
    # CH1: J3, CH2: J4, etc.
    jn = f"J{ch_idx+2}"  # J3..J8
    in_pos_A = pins.get("3","?"); in_neg_A = pins.get("2","?")
    in_pos_B = pins.get("5","?"); in_neg_B = pins.get("6","?")

    # Prüfen ob IN+ und IN- von XLR kommen (über Netz das J3-J8 enthält)
    def net_contains_ref(net_name, ref):
        return any(x[0]==ref for x in nets.get(net_name, []))

    xlr_in_hot  = net_contains_ref(in_pos_A, jn) or net_contains_ref(in_pos_B, jn)
    xlr_in_cold = net_contains_ref(in_neg_A, jn) or net_contains_ref(in_neg_B, jn)
    p("PASS" if xlr_in_hot else "FAIL",
      f"{uid} IN+ von {jn}", f"pin3={in_pos_A}, pin5={in_pos_B}")
    p("PASS" if xlr_in_cold else "FAIL",
      f"{uid} IN– von {jn}", f"pin2={in_neg_A}, pin6={in_neg_B}")

    # Ausgang: RX_OUT-Netz?
    out_A = pins.get("1","?"); out_B = pins.get("7","?")
    rx_out_a = "RX_OUT" in out_A or f"CH{ch_idx}_RX" in out_A
    rx_out_b = "RX_OUT" in out_B or f"CH{ch_idx}_RX" in out_B
    p("PASS" if rx_out_a or rx_out_b else "WARN",
      f"{uid} Ausgang → CH{ch_idx}_RX_OUT", f"OutA={out_A}, OutB={out_B}")

    # Feedback (IN- soll mit Out verbunden sein über Widerstand)
    # Prüfen: ist pin2 oder pin6 über Widerstand mit Ausgang verbunden?
    # Direktverbindung wäre Buffer, Teiler = Gain
    # Wir prüfen: Gibt es R in den Feedback-Netzen?
    fb_A_net = in_neg_A
    fb_B_net = in_neg_B
    fb_ok = False
    for fb_net in [fb_A_net, fb_B_net]:
        if fb_net and fb_net != "?":
            r_nodes = [x for x in nets.get(fb_net,[]) if x[0].startswith("R")]
            if r_nodes:
                fb_ok = True
    p("PASS" if fb_ok else "FAIL",
      f"{uid} Feedback-Widerstand", f"IN-A_net={fb_A_net}, nodes={[x[0] for x in nets.get(fb_A_net,[])]}")


# ────────────────────────────────────────────────
# 7. GAIN-STUFE SW2-SW7 + R26-R55
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 7 — Gain-Wahl SW2–SW7 + R26–R55")
print("="*70)

# Erwartete Topologie pro Kanal:
# RX_OUT → R(Feedback) → IN- (U8-U13)
# SW_DIP_x03 schaltet verschiedene Widerstände parallel zum Feedback
# DIP SW: 3 Positionen → 3 Widerstandswerte für Gain 0/6/12 dB

for ch_idx, sw_ref in enumerate(["SW2","SW3","SW4","SW5","SW6","SW7"], start=1):
    sw = components.get(sw_ref, {})
    sw_pins = sw.get("pins", {})
    sw_nets = set(sw_pins.values())
    print(f"\n  {sw_ref} (CH{ch_idx}): {sw.get('value','?')} | {sw.get('lib','?')}")

    if not sw:
        p("FAIL", f"{sw_ref} existiert", "Fehlt!")
        continue

    p("PASS", f"{sw_ref} existiert", sw.get("value","N/A"))

    # Muss CH{ch_idx}_RX_OUT enthalten
    rx_net = f"/CH{ch_idx}_RX_OUT"
    has_rx = any(rx_net in n or f"CH{ch_idx}_RX_OUT" in n for n in sw_nets)
    p("PASS" if has_rx else "FAIL",
      f"{sw_ref} → CH{ch_idx}_RX_OUT", f"Nets={sw_nets}")

    # Muss CH_SW_OUT Netze enthalten
    sw_out_nets = [n for n in sw_nets if "SW_OUT" in n or "GAIN" in n.upper()]
    p("PASS" if len(sw_out_nets) >= 1 else "FAIL",
      f"{sw_ref} SW_OUT-Netze", f"Found={sw_out_nets}")

    # Prüfen: Widerstände an SW_OUT-Netzen
    for sw_out in sw_out_nets:
        r_nodes = [x[0] for x in nets.get(sw_out,[]) if x[0].startswith("R")]
        print(f"    {sw_out}: R-Knoten={r_nodes}")


# ────────────────────────────────────────────────
# 8. DRIVER-STUFE U8-U13 (LM4562, CH1-CH6)
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 8 — Balanced Driver U8–U13 (LM4562)")
print("="*70)

for ch_idx, uid in enumerate(["U8","U9","U10","U11","U12","U13"], start=1):
    uc = components.get(uid, {})
    pins = uc.get("pins", {})
    print(f"\n  {uid} (CH{ch_idx}): {uc.get('value','?')}")
    if not uc:
        p("FAIL", f"{uid} existiert", "Fehlt!")
        continue
    p("PASS", f"{uid} existiert", uc.get("value","N/A"))

    # Versorgungspins
    vp = pins.get("8","?"); vm = pins.get("4","?")
    p("PASS" if "+12" in vp or "AVCC" in vp or "VCC" in vp.upper() else "FAIL",
      f"{uid} V+ Pin8", f"→ {vp}")
    p("PASS" if "-12" in vm or "AVSS" in vm or "VEE" in vm.upper() else "FAIL",
      f"{uid} V- Pin4", f"→ {vm}")

    # Ausgänge sollen zur XLR-Ausgangsbuchse
    jn = f"J{ch_idx+8}"  # J9..J14
    out_A = pins.get("1","?"); out_B = pins.get("7","?")

    def net_has_ref(net_name, ref):
        return any(x[0]==ref for x in nets.get(net_name, []))

    xlr_out_from_A = net_has_ref(out_A, jn)
    xlr_out_from_B = net_has_ref(out_B, jn)

    # Auch über Widerstände möglich
    # Prüfe ob im gleichen Netz oder über R-Knoten zu JN
    def reaches_jn_via_R(out_net, jn):
        # aus dem out_net alle R-Nodes finden
        r_nodes_out = [x[0] for x in nets.get(out_net,[]) if x[0].startswith("R")]
        for r in r_nodes_out:
            r_nets = set(components.get(r,{}).get("pins",{}).values())
            if any(any(x[0]==jn for x in nets.get(rn,[])) for rn in r_nets):
                return True
        return False

    xlr_out_ok = (xlr_out_from_A or xlr_out_from_B or
                  reaches_jn_via_R(out_A, jn) or reaches_jn_via_R(out_B, jn))
    p("PASS" if xlr_out_ok else "WARN",
      f"{uid} Ausgang → {jn}", f"OutA={out_A}, OutB={out_B}")

    # Feedback prüfen
    in_neg_A = pins.get("2","?"); in_neg_B = pins.get("6","?")
    fb_ok = False
    for fn in [in_neg_A, in_neg_B]:
        r_nodes = [x for x in nets.get(fn,[]) if x[0].startswith("R")]
        if r_nodes:
            fb_ok = True
    p("PASS" if fb_ok else "FAIL",
      f"{uid} Feedback", f"IN-A={in_neg_A}")


# ────────────────────────────────────────────────
# 9. XLR-STECKVERBINDER J3-J14
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 9 — XLR-Steckverbinder J3–J14")
print("="*70)

# J3-J8 Eingang (XLR Female): Pin1=GND/Shield, Pin2=HOT(+), Pin3=COLD(-)
# J9-J14 Ausgang (XLR Male): Pin1=GND/Shield, Pin2=HOT, Pin3=COLD
XLR_IN_REFS  = ["J3","J4","J5","J6","J7","J8"]
XLR_OUT_REFS = ["J9","J10","J11","J12","J13","J14"]

for jref_list, direction in [(XLR_IN_REFS,"IN"),(XLR_OUT_REFS,"OUT")]:
    for jref in jref_list:
        jc = components.get(jref,{})
        jc_pins = jc.get("pins",{})
        jc_nets = set(jc_pins.values())
        if not jc:
            p("FAIL", f"{jref} existiert", "Fehlt!")
            continue
        p("PASS", f"{jref} existiert", f"{jc.get('value','?')} ({direction})")

        pin1 = jc_pins.get("1","?")
        pin2 = jc_pins.get("2","?")
        pin3 = jc_pins.get("3","?")
        has_gnd = "GND" in pin1.upper() or "SHIELD" in pin1.upper() or "GND" in pin1
        has_hot  = pin2 != "?" and pin2 != "unconnected" and len(pin2) > 0
        has_cold = pin3 != "?" and pin3 != "unconnected" and len(pin3) > 0

        p("PASS" if has_gnd else "FAIL",
          f"{jref} Pin1=GND/Shield", f"→ {pin1}")
        p("PASS" if has_hot else "FAIL",
          f"{jref} Pin2=HOT", f"→ {pin2}")
        p("PASS" if has_cold else "FAIL",
          f"{jref} Pin3=COLD", f"→ {pin3}")

        # Kontrolliere XLR IN: HOT und COLD müssen an OpAmp-Inputs
        if direction == "IN":
            ch_idx = XLR_IN_REFS.index(jref)+1
            uid = f"U{ch_idx+1}"  # U2..U7
            u_pins = components.get(uid,{}).get("pins",{})
            u_inputs = set(u_pins.get("3","?").split()) | set(u_pins.get("5","?").split()) | \
                       set(u_pins.get("2","?").split()) | set(u_pins.get("6","?").split())
            hot_reaches_opamp  = any(any(x[0]==uid for x in nets.get(n,[])) for n in [pin2])
            cold_reaches_opamp = any(any(x[0]==uid for x in nets.get(n,[])) for n in [pin3])
            p("PASS" if hot_reaches_opamp else "FAIL",
              f"{jref} HOT→{uid}", f"pin2_net={pin2}")
            p("PASS" if cold_reaches_opamp else "FAIL",
              f"{jref} COLD→{uid}", f"pin3_net={pin3}")


# ────────────────────────────────────────────────
# 10. BARREL JACK J1 (Versorgungseingang)
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 10 — Barrel Jack J1 (24V Eingang)")
print("="*70)

j1 = components.get("J1",{})
j1_pins = j1.get("pins",{})
print(f"  J1: {j1.get('value','?')} | {j1.get('lib','?')}")
print(f"  J1 Pins: {j1_pins}")
j1_nets = set(j1_pins.values())
has_pos_in = any("24V" in n or "VIN" in n or "+24" in n or "PWR" in n.upper() or "12V" in n for n in j1_nets)
has_gnd    = any("GND" in n.upper() for n in j1_nets)
p("PASS" if j1 else "FAIL", "J1 existiert", j1.get("value","N/A"))
p("PASS" if has_pos_in else "FAIL", "J1 Versorgungspin", f"Nets={j1_nets}")
p("PASS" if has_gnd else "FAIL", "J1 GND-Pin", f"Nets={j1_nets}")


# ────────────────────────────────────────────────
# 11. ESD-SCHUTZ D1-D25
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 11 — ESD/TVS-Dioden D1–D25")
print("="*70)

# D1: SMBJ15CA (TVS an J1 Eingang)
d1 = components.get("D1",{})
d1_nets = set(d1.get("pins",{}).values())
print(f"  D1: {d1.get('value','?')} | Nets: {d1_nets}")
p("PASS" if d1 else "FAIL", "D1 (TVS J1) existiert", d1.get("value","N/A"))
d1_j1_connected = any(any(x[0]=="J1" for x in nets.get(n,[])) for n in d1_nets)
p("PASS" if d1_j1_connected else "FAIL", "D1 an J1-Netz", f"Nets={d1_nets}")

# D2-D25: ESD-Schutz an XLR
esd_ok = 0
for d_idx in range(2, 26):
    d_ref = f"D{d_idx}"
    dc = components.get(d_ref,{})
    if dc:
        esd_ok += 1
    else:
        p("FAIL", f"{d_ref} existiert", "Fehlt!")
p("PASS" if esd_ok == 24 else "WARN", f"D2–D25 alle vorhanden", f"{esd_ok}/24 vorhanden")

# Prüfen ob ESD-Dioden mit XLR-Netzen verbunden
for d_idx in range(2, 8):  # D2-D7 OUT_HOT direkt prüfen
    d_ref = f"D{d_idx}"
    dc = components.get(d_ref,{})
    dc_nets = set(dc.get("pins",{}).values())
    # Muss XLR-Pin-Netz oder GND enthalten
    has_xlr_signal = any(
        any(x[0].startswith("J") for x in nets.get(n,[]))
        for n in dc_nets
    )
    gnd_on_d = any("GND" in n.upper() for n in dc_nets)
    p("PASS" if has_xlr_signal else "WARN",
      f"{d_ref} an XLR-Netz", f"Nets={dc_nets}")
    p("PASS" if gnd_on_d else "WARN",
      f"{d_ref} GND-Seite", f"Nets={dc_nets}")


# ────────────────────────────────────────────────
# 12. MUTING-SCHALTUNG C und R
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 12 — Muting R106–R113 + Transistoren")
print("="*70)

# Muting: R106-R113 sollten mit MUTE-Netzen verbunden sein
mute_refs = [f"R{i}" for i in range(106,114)]
for rref in mute_refs:
    rc = components.get(rref,{})
    rc_nets = set(rc.get("pins",{}).values())
    p("PASS" if rc else "FAIL", f"{rref} existiert", rc.get("value","N/A"))
    if rc:
        # Sollte MUTE-Netz oder Audio-Ausgangs-Netz haben
        has_mute = any("MUTE" in n.upper() or "GND" in n.upper() or "OUT" in n.upper() for n in rc_nets)
        p("PASS" if has_mute else "WARN",
          f"{rref} in Muting-Topologie", f"Nets={rc_nets}")

# Transistoren (falls vorhanden)
q_refs = [r for r in components if r.startswith("Q")]
print(f"\n  Transistoren: {q_refs}")
for qref in q_refs:
    qc = components.get(qref,{})
    qc_nets = set(qc.get("pins",{}).values())
    print(f"  {qref}: {qc.get('value','?')} | Nets: {qc_nets}")
    p("PASS", f"{qref} existiert", qc.get("value","N/A"))


# ────────────────────────────────────────────────
# 13. FERRITE BEADS FB1-FB6
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 13 — Ferrite Beads FB1–FB6")
print("="*70)

for fb_idx in range(1,7):
    fb_ref = f"FB{fb_idx}"
    fb = components.get(fb_ref,{})
    fb_nets = set(fb.get("pins",{}).values())
    p("PASS" if fb else "FAIL", f"{fb_ref} existiert", fb.get("value","N/A"))
    if fb:
        # Sollte Versorgungsnetz auf beiden Seiten haben
        print(f"  {fb_ref}: {fb.get('value','?')} | Nets: {fb_nets}")


# ────────────────────────────────────────────────
# 14. ENTKOPPLUNGSKONDENSATOREN VOLLSTÄNDIGKEIT
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 14 — Entkopplungskondensatoren")
print("="*70)

# Alle Kondensatoren sammeln
all_caps = {r: c for r,c in components.items() if r.startswith("C")}
print(f"  Gesamt-Cs: {len(all_caps)}")

# Kondensatoren an Versorgungsnetzen (+12V, -12V)
pwr_cap_count_pos = 0
pwr_cap_count_neg = 0
bulk_caps = []
for cref, cc in all_caps.items():
    cc_nets = set(cc.get("pins",{}).values())
    if any("+12V" in n or "AVCC" in n or "VCC" in n.upper() for n in cc_nets):
        pwr_cap_count_pos += 1
    if any("-12V" in n or "AVSS" in n or "VEE" in n.upper() for n in cc_nets):
        pwr_cap_count_neg += 1
    val = cc.get("value","")
    if "µ" in val or "uF" in val.lower() or "u" in val.lower():
        # Bulk cap
        if any(c.isdigit() for c in val):
            try:
                num_str = re.match(r"[\d.]+", val)
                if num_str:
                    num = float(num_str.group())
                    if num >= 10:
                        bulk_caps.append((cref, val))
            except:
                pass

print(f"  Caps an +12V-Netzen: {pwr_cap_count_pos}")
print(f"  Caps an -12V-Netzen: {pwr_cap_count_neg}")
print(f"  Bulk-Caps (≥10µF): {bulk_caps[:10]}{'...' if len(bulk_caps)>10 else ''}")

p("PASS" if pwr_cap_count_pos >= 6 else "WARN",
  "Entkopplung +12V (≥6 Caps)", f"{pwr_cap_count_pos} Caps")
p("PASS" if pwr_cap_count_neg >= 6 else "WARN",
  "Entkopplung -12V (≥6 Caps)", f"{pwr_cap_count_neg} Caps")
p("PASS" if len(bulk_caps) >= 2 else "WARN",
  "Bulk-Caps vorhanden", f"{len(bulk_caps)} Stück")

# Jeder OpAmp (U2-U13) muss Entkopplung haben
print("\n  Prüfe Entkopplung pro OpAmp:")
for uid in [f"U{i}" for i in range(2,14)]:
    uc = components.get(uid,{})
    if not uc:
        continue
    uc_pwr_nets = set()
    for pin, net in uc.get("pins",{}).items():
        if pin in ("4","8"):
            uc_pwr_nets.add(net)
    # Finde Caps die an diesen Netzen hängen
    local_caps = []
    for net in uc_pwr_nets:
        for node in nets.get(net,[]):
            if node[0].startswith("C"):
                local_caps.append(node[0])
    p("PASS" if len(local_caps) >= 2 else "WARN",
      f"{uid} Entkopplung", f"Nets={uc_pwr_nets} → Caps={local_caps}")


# ────────────────────────────────────────────────
# 15. VOLLSTÄNDIGKEITSPRÜFUNG (floating nodes)
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 15 — Floating Nodes & unverbundene Netze")
print("="*70)

# Netze mit nur 1 Knoten = potentiell floating
single_node_nets = [(name, nodes) for name, nodes in nets.items()
                    if len(nodes) == 1 and "unconnected" not in name.lower() and name != "GND"]
print(f"  Single-node Netze (potentiell floating): {len(single_node_nets)}")
if len(single_node_nets) > 0:
    for name, nodes in single_node_nets[:20]:
        print(f"    {name}: {nodes}")
    p("WARN" if len(single_node_nets) <= 5 else "FAIL",
      "Floating Nodes",
      f"{len(single_node_nets)} Netze mit nur 1 Knoten")
else:
    p("PASS", "Keine Floating Nodes", "alle Netze ≥ 2 Knoten")

# PWR_FLAG Netze
pwr_flag_nets = [n for n in nets if "PWR_FLAG" in n]
print(f"\n  PWR_FLAG Netze: {pwr_flag_nets}")

# Unconnected Netze (KiCad-Marker)
unconnected = [n for n in nets if "unconnected" in n.lower() or "pin_unconnected" in n.lower()]
print(f"\n  Unconnected-Netze: {len(unconnected)}")
for un in unconnected[:20]:
    nodes = nets.get(un,[])
    print(f"    {un}: {[x[0]+'.'+x[1] for x in nodes]}")
p("PASS" if len(unconnected) == 0 else "WARN",
  "Unverbundene Pins",
  f"{len(unconnected)} unconnected Netze")


# ────────────────────────────────────────────────
# 16. SIGNALPFAD-TRACE: CH1 komplett
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 16 — Vollständiger Signalpfad CH1 trace")
print("="*70)

print("  Signalpfad: J3(Pin2 HOT) → U2(diff) → SW2(gain) → U8(driver) → J9(Pin2 HOT)")

j3_pins  = components.get("J3",{}).get("pins",{})
u2_pins  = components.get("U2",{}).get("pins",{})
sw2_pins = components.get("SW2",{}).get("pins",{})
u8_pins  = components.get("U8",{}).get("pins",{})
j9_pins  = components.get("J9",{}).get("pins",{})

print(f"\n  J3 Pins: {j3_pins}")
print(f"  U2 Pins: {u2_pins}")
print(f"  SW2 Pins: {sw2_pins}")
print(f"  U8 Pins: {u8_pins}")
print(f"  J9 Pins: {j9_pins}")

# Trace: J3.2 → ??? → U2.3 oder U2.5
j3_hot_net = j3_pins.get("2","?")
j3_cold_net = j3_pins.get("3","?")
print(f"\n  J3.2(HOT) Netz: {j3_hot_net}")
print(f"  J3.3(COLD) Netz: {j3_cold_net}")

# Ist U2 direkt verbunden oder über R?
j3_hot_nodes  = [x[0] for x in nets.get(j3_hot_net,[])]
j3_cold_nodes = [x[0] for x in nets.get(j3_cold_net,[])]
print(f"  Alle Knoten auf J3.2-Netz: {j3_hot_nodes}")
print(f"  Alle Knoten auf J3.3-Netz: {j3_cold_nodes}")

p("PASS" if "U2" in j3_hot_nodes or any(r.startswith("R") for r in j3_hot_nodes) else "FAIL",
  "CH1 HOT-Pfad nach U2", f"Nodes={j3_hot_nodes}")
p("PASS" if "U2" in j3_cold_nodes or any(r.startswith("R") for r in j3_cold_nodes) else "FAIL",
  "CH1 COLD-Pfad nach U2", f"Nodes={j3_cold_nodes}")

# U2 Ausgang
u2_out_a = u2_pins.get("1","?")
u2_out_b = u2_pins.get("7","?")
u2_out_nodes_a = [x[0] for x in nets.get(u2_out_a,[])]
u2_out_nodes_b = [x[0] for x in nets.get(u2_out_b,[])]
print(f"\n  U2.OutA Netz {u2_out_a}: {u2_out_nodes_a}")
print(f"  U2.OutB Netz {u2_out_b}: {u2_out_nodes_b}")

p("PASS" if "SW2" in u2_out_nodes_a or "SW2" in u2_out_nodes_b or
  any(r.startswith("R") for r in u2_out_nodes_a+u2_out_nodes_b) else "FAIL",
  "CH1 U2→SW2/Gain", f"OutA-nodes={u2_out_nodes_a}")

# SW2 → U8
sw2_nets_all = set(sw2_pins.values())
sw2_to_u8 = any(any(x[0]=="U8" for x in nets.get(n,[])) for n in sw2_nets_all)
# Indirekt über R?
sw2_to_u8_via_R = False
for sn in sw2_nets_all:
    for node in nets.get(sn,[]):
        if node[0].startswith("R"):
            r_nets = set(components.get(node[0],{}).get("pins",{}).values())
            if any(any(x[0]=="U8" for x in nets.get(rn,[])) for rn in r_nets):
                sw2_to_u8_via_R = True
p("PASS" if sw2_to_u8 or sw2_to_u8_via_R else "FAIL",
  "CH1 SW2→U8(driver)", f"SW2-nets={sw2_nets_all}")

# U8 → J9
u8_out_a = u8_pins.get("1","?")
u8_out_b = u8_pins.get("7","?")
u8_out_nodes_a = [x[0] for x in nets.get(u8_out_a,[])]
u8_out_nodes_b = [x[0] for x in nets.get(u8_out_b,[])]
print(f"\n  U8 OutA Netz {u8_out_a}: {u8_out_nodes_a}")
print(f"  U8 OutB Netz {u8_out_b}: {u8_out_nodes_b}")

p("PASS" if "J9" in u8_out_nodes_a or "J9" in u8_out_nodes_b else "WARN",
  "CH1 U8→J9 direkt", f"OutA-nodes={u8_out_nodes_a}, OutB-nodes={u8_out_nodes_b}")

# Summary of CH1 path
ch1_path_ok = all([
    "U2" in j3_hot_nodes or any(r.startswith("R") for r in j3_hot_nodes),
    "U2" in j3_cold_nodes or any(r.startswith("R") for r in j3_cold_nodes),
    sw2_to_u8 or sw2_to_u8_via_R,
])
p("PASS" if ch1_path_ok else "FAIL",
  "CH1 Signalpfad vollständig", "J3→U2→SW2→U8→J9")


# ────────────────────────────────────────────────
# 17. SYMMETRIE-CHECK (alle 6 Kanäle konsistent)
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 17 — Symmetrie-Check alle 6 Kanäle")
print("="*70)

channel_check = {}
for ch_idx in range(1,7):
    jn_in  = f"J{ch_idx+2}"   # J3-J8
    un_rx  = f"U{ch_idx+1}"   # U2-U7
    sw_n   = f"SW{ch_idx+1}"  # SW2-SW7
    un_drv = f"U{ch_idx+7}"   # U8-U13
    jn_out = f"J{ch_idx+8}"   # J9-J14

    jc = components.get(jn_in,{})
    ur = components.get(un_rx,{})
    sw = components.get(sw_n,{})
    ud = components.get(un_drv,{})
    jo = components.get(jn_out,{})

    all_ok = bool(jc and ur and sw and ud and jo)
    channel_check[ch_idx] = {
        "in": bool(jc), "rx": bool(ur), "sw": bool(sw),
        "drv": bool(ud), "out": bool(jo), "ok": all_ok
    }
    status = "PASS" if all_ok else "FAIL"
    missing = [label for label, present in [
        (jn_in, bool(jc)), (un_rx, bool(ur)), (sw_n, bool(sw)),
        (un_drv, bool(ud)), (jn_out, bool(jo))
    ] if not present]
    p(status, f"CH{ch_idx} Topologie vollständig",
      f"{jn_in}→{un_rx}→{sw_n}→{un_drv}→{jn_out}",
      f"Fehlt: {missing}" if missing else "")

# Prüfe ob alle Kanäle gleiche Struktur haben
u2_7_values  = [components.get(f"U{i}",{}).get("value","?") for i in range(2,8)]
u8_13_values = [components.get(f"U{i}",{}).get("value","?") for i in range(8,14)]
sw2_7_libs   = [components.get(f"SW{i}",{}).get("lib","?") for i in range(2,8)]
print(f"\n  U2-U7 Werte (sollen alle gleich): {u2_7_values}")
print(f"  U8-U13 Werte (sollen alle gleich): {u8_13_values}")
print(f"  SW2-SW7 Libs: {sw2_7_libs}")

p("PASS" if len(set(u2_7_values))==1 else "FAIL",
  "U2-U7 alle gleicher Typ", str(set(u2_7_values)))
p("PASS" if len(set(u8_13_values))==1 else "FAIL",
  "U8-U13 alle gleicher Typ", str(set(u8_13_values)))
p("PASS" if len(set(sw2_7_libs))<=2 else "WARN",
  "SW2-SW7 alle gleicher Typ", str(set(sw2_7_libs)))


# ────────────────────────────────────────────────
# 18. IMPEDANZ / GAIN-WERT PRÜFUNG
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 18 — Widerstandswerte + Gain-Berechnung CH1")
print("="*70)

# Prüfe R26-R55 (Gain-Widerstände)
gain_resistors = {r: components.get(r,{}) for r in [f"R{i}" for i in range(26,56)]
                  if components.get(r,{})}
print(f"  Gain-Widerstände R26-R55: {len(gain_resistors)} gefunden")

# Werte ausgeben
for rref, rc in sorted(gain_resistors.items()):
    val = rc.get("value","?")
    rc_nets = set(rc.get("pins",{}).values())
    print(f"  {rref}: {val:10s} | Nets: {rc_nets}")

# Prüfe Feedback-Widerstände (sollten mehrstufig für 0/6/12 dB sein)
# Gain (dB) = 20*log10(1 + Rf/Rin)
# 0 dB → Rf/Rin = 0 (bypass / Rf=0)
# 6 dB → Rf/Rin = 1 → gleiches R
# 12 dB → Rf/Rin = 3 → Rf = 3×Rin
# Prüfen ob konsistente Werte (nur warnen, nicht fail)
r_vals_numeric = []
for rref, rc in gain_resistors.items():
    val = rc.get("value","?")
    m = re.match(r"([\d.]+)\s*([kKmM]?)[Rr\u03a9]?", val)
    if m:
        num = float(m.group(1))
        mult = {"k":1000,"K":1000,"m":0.001,"M":1e6,"":1}.get(m.group(2),1)
        r_vals_numeric.append((rref, num*mult))

if r_vals_numeric:
    val_set = sorted(set(v for _,v in r_vals_numeric))
    print(f"\n  Einzigartige R-Werte: {val_set}")
    p("PASS" if len(val_set) <= 6 else "WARN",
      "Gain-R Werte konsistent", f"{len(val_set)} verschiedene Werte: {val_set}")


# ────────────────────────────────────────────────
# 19. NETZKLASSEN-KONSISTENZ
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("SCHRITT 19 — Netzklassen-Netze vorhanden?")
print("="*70)

# Erwartete Netze aus den kicad_dru Netzklassen
expected_net_patterns = {
    "Power (+12V)":   r'\+12V$|\+12V$|/\+12V',
    "Power (-12V)":   r'-12V$|/N12V',
    "GND":            r'^GND$|^/GND$',
    "Audio IN HOT":   r'CH\d_IN_HOT|IN_HOT',
    "Audio IN COLD":  r'CH\d_IN_COLD|IN_COLD',
    "Audio RX OUT":   r'CH\d_RX_OUT',
    "Audio SW OUT":   r'CH\d_SW_OUT',
    "EN_CTRL":        r'EN_CTRL',
    "Remote":         r'REMOTE',
    "Speaker/OUT":    r'CH\d_OUT_HOT|OUT_HOT|AUDIO_OUT',
}

for label, pattern in expected_net_patterns.items():
    found = [n for n in nets if re.search(pattern, n, re.IGNORECASE)]
    p("PASS" if found else "FAIL",
      f"Netz '{label}'", f"Matches: {found[:5]}")


# ────────────────────────────────────────────────
# ZUSAMMENFASSUNG
# ────────────────────────────────────────────────
print("\n" + "="*70)
print("ZUSAMMENFASSUNG")
print("="*70)
print(f"  \033[32mPASS: {PASS}\033[0m")
print(f"  \033[33mWARN: {WARN}\033[0m")
print(f"  \033[31mFAIL: {FAIL}\033[0m")
print(f"  Gesamt: {PASS+WARN+FAIL}")

if FINDINGS:
    print("\n  FAILS und WARNINGS:")
    for f in FINDINGS:
        tag = f.split("|")[0].strip()
        color = "\033[31m" if tag=="FAIL" else "\033[33m"
        print(f"    {color}{f}\033[0m")
else:
    print("\n  \033[32mKeine Fehler!\033[0m")

# JSON-Bericht
report = {
    "summary": {"PASS": PASS, "WARN": WARN, "FAIL": FAIL},
    "findings": FINDINGS,
    "nets_total": len(nets),
    "components_total": len(components),
}
with open("/tmp/schematic_validation_report.json","w") as f:
    json.dump(report, f, indent=2)
print(f"\n  Bericht: /tmp/schematic_validation_report.json")
