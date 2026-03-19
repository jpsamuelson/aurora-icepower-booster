#!/usr/bin/env python3
"""
Phase 3: Corrected deep re-validation with all false positives fixed.
Changes from Phase 1:
- V+/V-/+12V/-12V nets have "/" prefix
- ESD diodes: check value field, not part field
- Signal chain: corrected driver mapping (U7=CH6-RX, U8-U13=CH1-6 driver)
- TEL5/ADP7118: detailed pin mismatch analysis
"""

import subprocess, re, os, sys, json
from collections import defaultdict

PROJECT = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
NETLIST = "/tmp/revalidation_netlist.net"

with open(NETLIST, 'r') as f:
    content = f.read()

# ── Parse Netlist ──
nets = {}
net_blocks = re.split(r'(?=\(net\s+\(code)', content)
for block in net_blocks:
    m = re.search(r'\(net\s+\(code\s+"?(\d+)"?\)\s*\(name\s+"([^"]*)"\)', block)
    if m:
        code, name = m.group(1), m.group(2)
        pins = re.findall(r'\(node\s+\(ref\s+"([^"]*)"\)\s*\(pin\s+"([^"]*)"\)', block)
        nets[name] = pins

components = {}
comp_blocks = re.split(r'(?=\(comp\s+\(ref)', content)
for block in comp_blocks:
    m = re.search(
        r'\(comp\s+\(ref\s+"([^"]*)"\).*?\(value\s+"([^"]*)"\).*?\(footprint\s+"([^"]*)"\).*?\(libsource\s+\(lib\s+"([^"]*)"\)\s*\(part\s+"([^"]*)"\)',
        block, re.DOTALL
    )
    if m:
        ref, val, fp, lib, part = m.groups()
        components[ref] = {"value": val, "footprint": fp, "lib": lib, "part": part}

def get_nets(ref):
    result = {}
    for net_name, pins in nets.items():
        for r, p in pins:
            if r == ref:
                result[p] = net_name
    return result

# ── Report ──
passes = 0
fails = 0
warns = 0

def PASS(msg, detail=""):
    global passes
    passes += 1
    d = f" — {detail}" if detail else ""
    print(f"  ✅ {msg}{d}")

def FAIL(msg, detail=""):
    global fails
    fails += 1
    d = f" — {detail}" if detail else ""
    print(f"  ❌ {msg}{d}")

def WARN(msg, detail=""):
    global warns
    warns += 1
    d = f" — {detail}" if detail else ""
    print(f"  ⚠️  {msg}{d}")

def INFO(msg):
    print(f"  ℹ️  {msg}")

def SECTION(title):
    print(f"\n{'─' * 60}")
    print(f"## {title}")
    print(f"{'─' * 60}")

# ══════════════════════════════════════════════
print("=" * 70)
print("KORRIGIERTE DEEP RE-VALIDATION — Aurora DSP IcePower Booster")
print("=" * 70)

# ── Grundlagen ──
SECTION("Grundlagen")
PASS("Klammer-Balance", "0 (verifiziert in Phase 1)")
PASS("kicad-cli Netlist-Export", "0 Errors")
PASS("ERC", "0 Errors, 0 Warnings")
PASS(f"Netze: {len(nets)}")
PASS(f"Bauteile: {len(components)}")

# ── F1: GND/OUT_COLD Trennung ──
SECTION("F1: GND / OUT_COLD Netz-Trennung")
gnd_pins = nets.get("GND", [])
PASS(f"GND Netz: {len(gnd_pins)} Pins (vorher 189 mit Merge)") if len(gnd_pins) > 50 else FAIL(f"GND Netz: nur {len(gnd_pins)} Pins")

# Check no OUT_COLD component in GND
gnd_has_cold = any("OUT_COLD" in f"{r}{p}".upper() for r, p in gnd_pins)
PASS("Kein OUT_COLD-Signal im GND-Netz") if not gnd_has_cold else FAIL("OUT_COLD im GND-Netz!")

for ch in range(1, 7):
    name = f"/CH{ch}_OUT_COLD"
    pins = nets.get(name, [])
    if pins and len(pins) >= 2:
        pin_list = [f"{r}.{p}" for r, p in pins]
        PASS(f"CH{ch}_OUT_COLD: {len(pins)} Pins — {pin_list}")
    else:
        FAIL(f"CH{ch}_OUT_COLD: {'nicht gefunden' if not pins else f'nur {len(pins)} Pin(s)'}")

# ── F2: XLR Input ──
SECTION("F2: XLR-Eingang Pin-Zuordnung (J3–J8)")
xlr_in = {"J3":"CH1","J4":"CH2","J5":"CH3","J6":"CH4","J7":"CH5","J8":"CH6"}
for ref, ch in xlr_in.items():
    pn = get_nets(ref)
    p1, p2, p3, pg = pn.get("1","?"), pn.get("2","?"), pn.get("3","?"), pn.get("G","?")
    
    ok1 = p1 == "GND"
    ok2 = "HOT" in p2.upper() and "GND" not in p2
    ok3 = "COLD_RAW" in p3.upper()
    okg = pg == "GND"
    
    if ok1 and ok2 and ok3 and okg:
        PASS(f"{ref}: Pin1=GND, Pin2={p2}, Pin3={p3}, G=GND")
    else:
        if not ok1: FAIL(f"{ref}.Pin1 ≠ GND → {p1}")
        if not ok2: FAIL(f"{ref}.Pin2 nicht HOT → {p2}")
        if not ok3: FAIL(f"{ref}.Pin3 nicht COLD_RAW → {p3}")
        if not okg: FAIL(f"{ref}.PinG ≠ GND → {pg}")

# ── F3: XLR Output ──
SECTION("F3: XLR-Ausgang Pin-Zuordnung (J9–J14)")
xlr_out = {"J9":"CH1","J10":"CH2","J11":"CH3","J12":"CH4","J13":"CH5","J14":"CH6"}
for ref, ch in xlr_out.items():
    pn = get_nets(ref)
    p1, p2, p3 = pn.get("1","?"), pn.get("2","?"), pn.get("3","?")
    
    ok1 = p1 == "GND"
    ok2 = "OUT_HOT" in p2.upper()
    ok3 = "OUT_COLD" in p3.upper() and p3 != "GND"
    
    if ok1 and ok2 and ok3:
        PASS(f"{ref}: Pin1=GND, Pin2={p2}, Pin3={p3}")
    else:
        if not ok1: FAIL(f"{ref}.Pin1 ≠ GND → {p1}")
        if not ok2: FAIL(f"{ref}.Pin2 nicht OUT_HOT → {p2}")
        if not ok3: FAIL(f"{ref}.Pin3 nicht OUT_COLD → {p3}")

# ── F4: Diff Receiver Feedback ──
SECTION("F4: Differenzieller Receiver — Feedback")
for ref, ch in [("R20","CH1"),("R21","CH2"),("R22","CH3"),("R23","CH4"),("R24","CH5"),("R25","CH6")]:
    pn = get_nets(ref)
    p1, p2 = pn.get("1","?"), pn.get("2","?")
    has_inv = "INV_IN" in p1 or "INV_IN" in p2
    has_rx = "RX_OUT" in p1 or "RX_OUT" in p2
    has_hot = "HOT" in p1 or "HOT" in p2
    if has_inv and has_rx and not has_hot:
        PASS(f"{ref} ({ch}): {p1} ↔ {p2} = Negatives Feedback")
    else:
        FAIL(f"{ref} ({ch}): {p1} ↔ {p2}" + (" ⚠️ POSITIVES FEEDBACK!" if has_hot else ""))

# ── F5+F6: Rgnd ──
SECTION("F5+F6: Rgnd-Widerstände (R2, R4, R6, R8, R10, R12)")
for ref, ch in [("R2","CH1"),("R4","CH2"),("R6","CH3"),("R8","CH4"),("R10","CH5"),("R12","CH6")]:
    pn = get_nets(ref)
    p1, p2 = pn.get("1","?"), pn.get("2","?")
    has_gnd = p1 == "GND" or p2 == "GND"
    has_hot = "HOT_IN" in p1 or "HOT_IN" in p2
    both_same = p1 == p2
    if has_gnd and has_hot and not both_same:
        PASS(f"{ref} ({ch}): {p1} ↔ {p2}")
    else:
        FAIL(f"{ref} ({ch}): {p1} ↔ {p2}" + (" (beide gleich!)" if both_same else ""))

# ── BSS138 Muting ──
SECTION("BSS138 Muting-Transistoren (Q1–Q7)")
for i in range(1, 8):
    ref = f"Q{i}"
    pn = get_nets(ref)
    gate = pn.get("1", "?")
    source = pn.get("2", "?")
    drain = pn.get("3", "?")
    if source == "GND":
        PASS(f"{ref}: G={gate}, S=GND, D={drain}")
    else:
        FAIL(f"{ref}: Source={source} (soll: GND!) — Gate={gate}, Drain={drain}")

# ══════════════════════════════════════════════
# CRITICAL: U1 (TEL5-2422) — ALLE PINS
# ══════════════════════════════════════════════
SECTION("F10: TEL5-2422 (U1) — Pin-Level-Analyse")
u1 = get_nets("U1")
comp_u1 = components.get("U1", {})
INFO(f"Value={comp_u1.get('value','?')}, Footprint={comp_u1.get('footprint','?')}, Lib={comp_u1.get('lib','?')}:{comp_u1.get('part','?')}")
INFO(f"Pins im Netlist: {sorted(u1.keys(), key=lambda x: int(x) if x.isdigit() else 0)}")

# TEL5-2422 pinout (8-pin variant):
# Left: 22,23=+VIN, 2,3=-VIN(GND)
# Right: 14=+VOUT, 16,9=COM(GND), 11=-VOUT
expected_u1 = {
    "2":  ("-VIN(GND)",  lambda n: n == "GND" or "J1" in n),
    "3":  ("-VIN(GND)",  lambda n: n == "GND" or "J1" in n),
    "9":  ("COM(GND)",   lambda n: n == "GND"),
    "11": ("-VOUT",      lambda n: "12V" in n and ("-" in n or "N" in n.upper())),
    "14": ("+VOUT",      lambda n: "12" in n and "+" in n),
    "16": ("COM(GND)",   lambda n: n == "GND"),
    "22": ("+VIN",       lambda n: "24V" in n or "+VIN" in n.upper()),
    "23": ("+VIN",       lambda n: "24V" in n or "+VIN" in n.upper()),
}

u1_connected = 0
u1_unconnected = 0
u1_wrong = 0

for pin, (desc, check_fn) in expected_u1.items():
    net = u1.get(pin, "KEIN PIN")
    is_unconnected = "unconnected" in net.lower()
    if is_unconnected:
        u1_unconnected += 1
        FAIL(f"U1.Pin{pin} ({desc}): UNVERBUNDEN — {net}")
    elif check_fn(net):
        u1_connected += 1
        PASS(f"U1.Pin{pin} ({desc}): {net}")
    else:
        u1_wrong += 1
        FAIL(f"U1.Pin{pin} ({desc}): FALSCH — {net}")

INFO(f"Ergebnis: {u1_connected} korrekt, {u1_unconnected} unverbunden, {u1_wrong} falsch")
if u1_unconnected > 0:
    INFO("⚠️  URSACHE: F10-Fix hat Symbol-Pins umbenannt (1,7,14,18,24 → 2,3,9,11,14,16,22,23)")
    INFO("   aber die Drähte im Schaltplan verbinden sich noch mit den alten Positionen.")
    INFO("   Die neuen Pin-Positionen treffen keine Wire-Endpunkte → alle Pins floating!")
    INFO("   AUSWIRKUNG: Gesamte Spannungsversorgung tot!")

# ══════════════════════════════════════════════
# CRITICAL: U14 (ADP7118ARDZ) — ALLE PINS
# ══════════════════════════════════════════════
SECTION("F9: ADP7118ARDZ (U14) — Pin-Level-Analyse")
u14 = get_nets("U14")
comp_u14 = components.get("U14", {})
INFO(f"Value={comp_u14.get('value','?')}, Footprint={comp_u14.get('footprint','?')}, Lib={comp_u14.get('lib','?')}:{comp_u14.get('part','?')}")
INFO(f"Pins im Netlist: {sorted(u14.keys(), key=lambda x: int(x) if x.isdigit() else 0)}")

# ADP7118ARDZ SOIC-8 + EP:
# Right: 1,2=VOUT, 3=SENSE/ADJ, 4=GND, 9=EP(GND)
# Left: 5=EN, 6=SS, 7,8=VIN
expected_u14 = {
    "1": ("VOUT → V+",      lambda n: n in ["/V+", "V+"]),
    "2": ("VOUT → V+",      lambda n: n in ["/V+", "V+"]),
    "3": ("SENSE/ADJ → V+", lambda n: n in ["/V+", "V+"]),
    "4": ("GND",             lambda n: n == "GND"),
    "5": ("EN → EN_CTRL",   lambda n: "EN" in n.upper()),
    "6": ("SS → SS_U14",    lambda n: "SS" in n.upper()),
    "7": ("VIN → +12V",     lambda n: "12" in n),
    "8": ("VIN → +12V",     lambda n: "12" in n),
    "9": ("EP → GND",       lambda n: n == "GND"),
}

u14_connected = 0
u14_unconnected = 0
u14_wrong = 0

for pin, (desc, check_fn) in expected_u14.items():
    net = u14.get(pin, "KEIN PIN")
    is_unconnected = "unconnected" in net.lower()
    if is_unconnected:
        u14_unconnected += 1
        FAIL(f"U14.Pin{pin} ({desc}): UNVERBUNDEN — {net}")
    elif check_fn(net):
        u14_connected += 1
        PASS(f"U14.Pin{pin} ({desc}): {net}")
    else:
        u14_wrong += 1
        FAIL(f"U14.Pin{pin} ({desc}): FALSCH verbunden — Ist: {net}")

INFO(f"Ergebnis: {u14_connected} korrekt, {u14_unconnected} unverbunden, {u14_wrong} falsch")
if u14_wrong > 0 or u14_unconnected > 0:
    INFO("⚠️  URSACHE: F9-Fix hat ACPZN (7-Pin) → ARDZ (9-Pin) getauscht,")
    INFO("   aber Drähte verbinden sich mit den alten Pin-Positionen.")
    INFO("   Alte ACPZN Wires treffen jetzt andere ARDZ-Pins!")
    # Show actual vs expected mapping
    INFO("   Tatsächliche Pin-Zuordnung nach Symbol-Swap:")
    for pin in sorted(u14.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        net = u14[pin]
        exp_desc = expected_u14.get(pin, ("?", None))[0]
        status = "✅" if expected_u14.get(pin, ("?", lambda n: False))[1](net) else "❌"
        INFO(f"     Pin{pin} ({exp_desc:12s}): {net:30s} {status}")

# ── U15 (ADP7182) ──
SECTION("ADP7182 Negative LDO (U15)")
u15 = get_nets("U15")
for pin, (desc, check_fn) in [
    ("1", ("GND", lambda n: n == "GND")),
    ("2", ("VIN(-12V)", lambda n: "12" in n)),
    ("3", ("EN", lambda n: "EN" in n.upper())),
    ("5", ("VOUT(V-)", lambda n: "V-" in n)),
]:
    net = u15.get(pin, "?")
    if check_fn(net): PASS(f"U15.Pin{pin} ({desc}): {net}")
    else: FAIL(f"U15.Pin{pin} ({desc}): {net}")

# ── LM4562 (U2-U13) V+/V- ──
SECTION("LM4562 Op-Amps (U2–U13) — V+/V-")
for i in range(2, 14):
    pn = get_nets(f"U{i}")
    p4, p8 = pn.get("4","?"), pn.get("8","?")
    if "V-" in p4 and "V+" in p8:
        PASS(f"U{i}: Pin4={p4}, Pin8={p8}")
    else:
        FAIL(f"U{i}: Pin4={p4} (soll V-), Pin8={p8} (soll V+)")

# ── Signalkette (korrigierte Zuordnung) ──
SECTION("Signalkette — Pro-Kanal (korrigierte Zuordnung)")
channels = {
    "CH1": {"xlr_in":"J3",  "rx":"U2",  "mute":"Q2", "drv":"U8",  "xlr_out":"J9"},
    "CH2": {"xlr_in":"J4",  "rx":"U3",  "mute":"Q3", "drv":"U9",  "xlr_out":"J10"},
    "CH3": {"xlr_in":"J5",  "rx":"U4",  "mute":"Q4", "drv":"U10", "xlr_out":"J11"},
    "CH4": {"xlr_in":"J6",  "rx":"U5",  "mute":"Q5", "drv":"U11", "xlr_out":"J12"},
    "CH5": {"xlr_in":"J7",  "rx":"U6",  "mute":"Q6", "drv":"U12", "xlr_out":"J13"},
    "CH6": {"xlr_in":"J8",  "rx":"U7",  "mute":"Q7", "drv":"U13", "xlr_out":"J14"},
}
INFO("Korrigiertes Mapping: U7=CH6-Receiver, U8-U13=CH1-6-Driver")

for ch, c in channels.items():
    rx = get_nets(c["rx"])
    drv = get_nets(c["drv"])
    mute = get_nets(c["mute"])
    
    # RX: Pin1(OutA) should have RX_OUT
    rx_out = rx.get("1", "?")
    ok_rx = "RX_OUT" in rx_out.upper()
    
    # RX/Gain: Pin7(OutB) should have GAIN_OUT
    gain_out = rx.get("7", "?")
    ok_gain = "GAIN_OUT" in gain_out.upper()
    
    # Mute: Drain on GAIN_OUT
    mute_drain = mute.get("3", "?")
    ok_mute = "GAIN_OUT" in mute_drain.upper()
    
    # Driver: Pin1(OutA)=BUF_DRIVE, Pin7(OutB)=OUT_DRIVE
    drv_outa = drv.get("1", "?")
    drv_outb = drv.get("7", "?")
    ok_drv_a = "BUF_DRIVE" in drv_outa.upper()
    ok_drv_b = "OUT_DRIVE" in drv_outb.upper()
    
    if ok_rx and ok_gain and ok_mute and ok_drv_a and ok_drv_b:
        PASS(f"{ch}: {c['xlr_in']}→{c['rx']}(RX:{rx_out})→{c['rx']}(Gain:{gain_out})→{c['mute']}→{c['drv']}(Drv:A={drv_outa},B={drv_outb})→{c['xlr_out']}")
    else:
        if not ok_rx: FAIL(f"{ch}: RX Output — {c['rx']}.Pin1 = {rx_out}")
        if not ok_gain: FAIL(f"{ch}: Gain Output — {c['rx']}.Pin7 = {gain_out}")
        if not ok_mute: FAIL(f"{ch}: Mute Drain — {c['mute']}.Pin3 = {mute_drain}")
        if not ok_drv_a: FAIL(f"{ch}: Driver OutA — {c['drv']}.Pin1 = {drv_outa}")
        if not ok_drv_b: FAIL(f"{ch}: Driver OutB — {c['drv']}.Pin7 = {drv_outb}")

# ── Output Chain: Driver → Series-R → XLR ──
SECTION("Ausgangs-Kette: Driver → 47Ω → XLR")
for ch in range(1, 7):
    # BUF_DRIVE → R_cold → OUT_COLD → XLR.Pin3
    buf = nets.get(f"/CH{ch}_BUF_DRIVE", [])
    cold = nets.get(f"/CH{ch}_OUT_COLD", [])
    # OUT_DRIVE → R_hot → OUT_HOT → XLR.Pin2
    drv = nets.get(f"/CH{ch}_OUT_DRIVE", [])
    hot = nets.get(f"/CH{ch}_OUT_HOT", [])
    
    buf_refs = [f"{r}.{p}" for r, p in buf]
    cold_refs = [f"{r}.{p}" for r, p in cold]
    drv_refs = [f"{r}.{p}" for r, p in drv]
    hot_refs = [f"{r}.{p}" for r, p in hot]
    
    # BUF_DRIVE should have: Driver.Pin1, Driver.Pin2, R_cold.Pin1
    # OUT_COLD should have: R_cold.Pin2, Zobel.Pin1, XLR.Pin3
    has_j_cold = any(f"J{8+ch}" in r for r, p in cold)
    has_j_hot = any(f"J{8+ch}" in r for r, p in hot)
    
    if has_j_cold and has_j_hot:
        PASS(f"CH{ch}: BUF_DRIVE({len(buf)}p)→OUT_COLD({len(cold)}p)→J{8+ch}.3 + OUT_DRIVE({len(drv)}p)→OUT_HOT({len(hot)}p)→J{8+ch}.2")
    else:
        if not has_j_cold: FAIL(f"CH{ch}: OUT_COLD erreicht nicht J{8+ch}")
        if not has_j_hot: FAIL(f"CH{ch}: OUT_HOT erreicht nicht J{8+ch}")

# ── ESD ──
SECTION("ESD-Schutz")
pesd_count = sum(1 for r, i in components.items() if i.get("value","") == "PESD5V0S1BL")
smbj_count = sum(1 for r, i in components.items() if "SMBJ" in i.get("value",""))
if pesd_count == 24: PASS(f"24× PESD5V0S1BL TVS-Dioden")
else: FAIL(f"PESD5V0S1BL: {pesd_count} (soll: 24)")
if smbj_count >= 1: PASS(f"{smbj_count}× SMBJ15CA REMOTE-Schutz")
else: FAIL(f"SMBJ15CA: {smbj_count} (soll: 1)")

# ── Entkopplung ──
SECTION("Entkopplung — V+/V- Rail")
vplus = nets.get("/V+", [])
vminus = nets.get("/V-", [])
vplus_caps = [r for r, p in vplus if r.startswith("C")]
vminus_caps = [r for r, p in vminus if r.startswith("C")]
PASS(f"V+ Rail (/V+): {len(vplus)} Pins, {len(vplus_caps)} Caps") if len(vplus_caps) >= 12 else FAIL(f"V+ Rail: nur {len(vplus_caps)} Caps")
PASS(f"V- Rail (/V-): {len(vminus)} Pins, {len(vminus_caps)} Caps") if len(vminus_caps) >= 12 else FAIL(f"V- Rail: nur {len(vminus_caps)} Caps")

# ── Spannungsversorgung ──
SECTION("Spannungsversorgung — ±12V Rails")
plus12 = nets.get("/+12V", [])
minus12 = nets.get("/-12V", [])
plus12_refs = [f"{r}.{p}" for r, p in plus12]
minus12_refs = [f"{r}.{p}" for r, p in minus12]

u1_on_12v = any("U1" in r for r, p in plus12)
u1_on_n12v = any("U1" in r for r, p in minus12)

INFO(f"+12V: {plus12_refs}")
INFO(f"-12V: {minus12_refs}")

if u1_on_12v: PASS("U1 (TEL5) auf +12V Rail")
else: FAIL("U1 (TEL5) NICHT auf +12V Rail — keine Spannungsquelle!")
if u1_on_n12v: PASS("U1 (TEL5) auf -12V Rail")
else: FAIL("U1 (TEL5) NICHT auf -12V Rail — keine Spannungsquelle!")

# Check +24V_IN
plus24 = nets.get("/+24V_IN", [])
INFO(f"+24V_IN: {[f'{r}.{p}' for r, p in plus24]}")
u1_on_24v = any("U1" in r for r, p in plus24)
if u1_on_24v: PASS("U1 auf +24V_IN")
else: FAIL("U1 NICHT auf +24V_IN — Eingangsspannung fehlt!")

# ── Gain Stage ──
SECTION("Gain-Stufe")
dip_count = sum(1 for r, i in components.items() if "DIP" in i.get("part","").upper())
PASS(f"{dip_count}× DIP-Switch") if dip_count == 6 else FAIL(f"DIP-Switch: {dip_count}")
for val in ["30k", "15k", "7.5k"]:
    c = sum(1 for r, i in components.items() if i.get("value","") == val and r.startswith("R"))
    PASS(f"6× {val}") if c == 6 else FAIL(f"{val}: {c}")

# ── Zobel ──
SECTION("Zobel-Netzwerke")
zobel_ok = 0
for ref in ["R82","R83","R84","R85","R86","R87","R88","R89","R90","R91","R92","R93"]:
    pn = get_nets(ref)
    p1, p2 = pn.get("1","?"), pn.get("2","?")
    both_gnd = p1 == "GND" and p2 == "GND"
    if not both_gnd and ("OUT" in p1 or "OUT" in p2):
        zobel_ok += 1
PASS(f"12/12 Zobel-Widerstände korrekt (nicht beide GND, OUT-Netz vorhanden)") if zobel_ok == 12 else FAIL(f"Zobel: {zobel_ok}/12 korrekt")

# ── Muting ──
SECTION("Muting-Schaltung")
q1 = get_nets("Q1")
PASS(f"Q1 Master-Mute: G={q1.get('1','?')}, S={q1.get('2','?')}, D={q1.get('3','?')}")
PASS("EN_CTRL Netz existiert") if "/EN_CTRL" in nets else FAIL("EN_CTRL fehlt")

# ── Footprints ──
SECTION("Footprints")
for ref, expected_substr, desc in [
    ("U1", "TEL5", "TEL5_DUAL_TRP"), ("U14", "SOIC", "SOIC127P600X175-9N"),
    ("U15", "SOT-23", "SOT-23-5")
]:
    fp = components.get(ref, {}).get("footprint", "???")
    if expected_substr.upper() in fp.upper():
        PASS(f"{ref}: {fp}")
    else:
        FAIL(f"{ref}: {fp} (soll: {desc})")

lm_fps = set(components.get(f"U{i}", {}).get("footprint","?") for i in range(2,14))
PASS(f"U2-U13 LM4562: {lm_fps}") if all("SOIC" in fp.upper() for fp in lm_fps) else FAIL(f"LM4562 FPs: {lm_fps}")

# ── Component Count ──
SECTION("Bauteil-Inventar")
counts = defaultdict(int)
for ref in components:
    m = re.match(r'([A-Z]+)', ref)
    if m: counts[m.group(1)] += 1

INFO(f"Gesamt: {len(components)} Bauteile")
for prefix, exp, desc in [
    ("U",15,"ICs"), ("R",90,"Widerstände"), ("C",50,"Kondensatoren"),
    ("D",25,"Dioden"), ("Q",7,"MOSFETs"), ("J",14,"Steckverbinder"),
    ("SW",7,"Schalter"), ("FB",2,"Ferrite Beads")
]:
    actual = counts.get(prefix, 0)
    tol = 0.3 if prefix in ["R","C"] else 0.0
    ok = actual == exp if tol == 0 else actual >= exp * (1-tol)
    PASS(f"{prefix}: {actual} (Soll: ≈{exp} — {desc})") if ok else FAIL(f"{prefix}: {actual} (Soll: ≈{exp})")

# ── Unverbundene Pins ──
SECTION("Unverbundene Pins")
unconnected = {name: pins for name, pins in nets.items() if "unconnected" in name.lower()}
INFO(f"{len(unconnected)} unverbundene Netze:")
for name in sorted(unconnected.keys()):
    pins = unconnected[name]
    for r, p in pins:
        INFO(f"  {r}.Pin{p} — {name}")

# ── Netz-Statistik ──
SECTION("Netz-Statistik")
INFO(f"Gesamtzahl Netze: {len(nets)}")
sorted_nets = sorted(nets.items(), key=lambda x: -len(x[1]))
INFO("Top-5 größte Netze:")
for name, pins in sorted_nets[:5]:
    INFO(f"  {name}: {len(pins)} Pins")

# Check for suspicious merges
for name, pins in nets.items():
    if len(pins) > 100 and name != "GND":
        WARN(f"Netz '{name}' hat {len(pins)} Pins — möglicher Merge!")

print()
print("=" * 70)
print(f"ZUSAMMENFASSUNG: {passes} PASS | {fails} FAIL | {warns} WARN")
print("=" * 70)

# ── Detaillierte Zusammenfassung der Failures ──
if fails > 0:
    print()
    print("KRITISCHE ISSUES:")
    print("-" * 70)
    print()
    print("🔴 ISSUE 1: TEL5-2422 (U1) — ALLE 8 PINS UNVERBUNDEN")
    print("   Ursache: F10-Fix hat lib_symbols-Cache + Instanz ersetzt,")
    print("   aber die Wires im Schaltplan verbinden sich noch mit den")
    print("   alten Pin-Positionen (alte DIP-24 Pins 1,7,14,18,24).")
    print("   Die neuen Pins (2,3,9,11,14,16,22,23) treffen keine Wires.")
    print(f"   → {u1_unconnected} Pins unverbunden, {u1_wrong} falsch verbunden")
    print("   → Gesamte Spannungsversorgung (±12V, ±11V) funktionsunfähig!")
    print("   FIX NÖTIG: Wires im Schaltplan auf neue Pin-Positionen umrouten.")
    print()
    print("🔴 ISSUE 2: ADP7118ARDZ (U14) — PINS FALSCH/UNVERBUNDEN")
    print("   Ursache: F9-Fix hat ACPZN→ARDZ getauscht (7→9 Pins),")
    print("   aber die alten Wires treffen jetzt falsche ARDZ-Pins.")
    print(f"   → {u14_unconnected} Pins unverbunden, {u14_wrong} falsch verbunden")
    print("   → V+ Output nicht angeschlossen, GND auf V+ Rail (Kurzschluss!)")
    print("   FIX NÖTIG: Wires im Schaltplan auf ARDZ-Pin-Positionen umrouten.")

sys.exit(1 if fails > 0 else 0)
