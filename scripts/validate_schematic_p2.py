#!/usr/bin/env python3
"""
Schematic Logic Validator — Pass 2 (Korrigierte Logik)
Prüft die tatsächlichen Verbindungen, nicht Pattern-Annahmen.
"""
import re, sys, subprocess, os, json, math
from collections import defaultdict

PROJECT = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT, "aurora-dsp-icepower-booster.kicad_sch")
NET_FILE = "/tmp/validate_sch_native.net"  # bereits vorhanden

PASS = 0; FAIL = 0; WARN = 0; FINDINGS = []
def p(tag, test, msg, extra=""):
    global PASS, FAIL, WARN
    if tag == "PASS": PASS += 1
    elif tag == "FAIL": FAIL += 1; FINDINGS.append(f"FAIL | {test} | {msg}" + (f" | {extra}" if extra else ""))
    elif tag == "WARN": WARN += 1; FINDINGS.append(f"WARN | {test} | {msg}" + (f" | {extra}" if extra else ""))
    col = {"PASS": "\033[32m", "FAIL": "\033[31m", "WARN": "\033[33m"}[tag]
    print(f"  {col}{tag}\033[0m  {test}: {msg}" + (f" [{extra}]" if extra else ""))

# ─── Netlist parsen (exakt wie Pass 1) ────────────────────────────────────────
with open(NET_FILE) as f:
    net_raw = f.read()

def extract_blocks(text, keyword):
    blocks = []
    for m in re.finditer(r'\(' + re.escape(keyword) + r'\b', text):
        start = m.start(); depth = 0
        for i, c in enumerate(text[start:]):
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: blocks.append(text[start:start+i+1]); break
    return blocks

def get_field(block, field):
    m = re.search(r'\(' + re.escape(field) + r'\s+"([^"]+)"', block)
    return m.group(1) if m else None

comp_blocks = extract_blocks(net_raw, "comp")
components = {}
for blk in comp_blocks:
    ref = get_field(blk, "ref"); value = get_field(blk, "value")
    lib_m = re.search(r'\(libsource\s+\(lib\s+"([^"]+)"\)\s+\(part\s+"([^"]+)"', blk)
    lib = lib_m.group(1) + ":" + lib_m.group(2) if lib_m else ""
    if ref: components[ref] = {"value": value, "lib": lib, "pins": {}}

net_blocks = extract_blocks(net_raw, "net")
nets = {}
comp_pins = defaultdict(dict)
for blk in net_blocks:
    name_m = re.search(r'\(name\s+"([^"]+)"', blk)
    if not name_m: continue
    net_name = name_m.group(1)
    node_blocks = extract_blocks(blk, "node")
    nodes = []
    for nb in node_blocks:
        ref_m = re.search(r'\(ref\s+"([^"]+)"', nb)
        pin_m = re.search(r'\(pin\s+"([^"]+)"', nb)
        if ref_m and pin_m:
            nodes.append((ref_m.group(1), pin_m.group(1)))
            comp_pins[ref_m.group(1)][pin_m.group(1)] = net_name
    nets[net_name] = nodes
for ref, pins in comp_pins.items():
    if ref in components: components[ref]["pins"] = pins

def get_pins(ref): return components.get(ref, {}).get("pins", {})
def pins_nets(ref): return set(get_pins(ref).values())
def nodes_on_net(net): return nets.get(net, [])
def refs_on_net(net): return [x[0] for x in nodes_on_net(net)]
def net_of_pin(ref, pin): return get_pins(ref).get(str(pin), "?")
def neighbors(ref):
    """Alle Bauteil-Refs die mit 'ref' über ein gemeinsames Netz verbunden sind."""
    connected = set()
    for net in pins_nets(ref):
        connected.update(r for r, _ in nodes_on_net(net) if r != ref)
    return connected

# ─── Parse Widerstandswerte ───────────────────────────────────────────────────
def parse_resistance(val_str):
    """Gibt None zurück wenn nicht parsebar."""
    v = str(val_str).strip().replace(' ','').replace(',','.')
    m = re.match(r'^([\d.]+)\s*([kKmMRrΩ]?)\s*(?:0\.1%|1%|%|\u03a9)?$', v)
    if not m: return None
    num = float(m.group(1))
    s = m.group(2).upper()
    mult = {'K': 1e3, 'M': 1e6, '': 1, 'R': 1}.get(s, None)
    return num * mult if mult is not None else None

# ─── Vollständige Netzliste aufbauen ─────────────────────────────────────────
print("="*70)
print("PASS 2 — Topologische und funktionale Analyse")
print("="*70)

# ─── Schritt A: Versorgungstopologie ─────────────────────────────────────────
print("\n[A] VERSORGUNGSKETTE: 24V → DC/DC → LDO → OpAmps")

# Tatsächliche Netznamen ermitteln
pos_raw = next((n for n in nets if "+12V_RAW" in n or "12V_RAW" in n and "N" not in n), None)
neg_raw = next((n for n in nets if "-12V_RAW" in n or "N12V_RAW" in n), None)
pos_reg = next((n for n in nets if n == "/+12V" or n == "+12V"), None)
neg_reg = next((n for n in nets if n == "/-12V" or n == "-12V"), None)
v_plus  = next((n for n in nets if n in ("/V+", "V+")), None)
v_minus = next((n for n in nets if n in ("/V-", "V-")), None)
gnd     = next((n for n in nets if n in ("GND", "/GND")), None)
vin_24  = next((n for n in nets if "24V_IN" in n or "+24V" in n), None)

print(f"  24V Eingang: {vin_24} → Nodes: {refs_on_net(vin_24)}")
print(f"  +12V_RAW:    {pos_raw} → Nodes: {refs_on_net(pos_raw)}")
print(f"  -12V_RAW:    {neg_raw} → Nodes: {refs_on_net(neg_raw)}")
print(f"  +12V (nach FB): {pos_reg} → Nodes: {refs_on_net(pos_reg)}")
print(f"  -12V (nach FB): {neg_reg} → Nodes: {refs_on_net(neg_reg)}")
print(f"  /V+ (LDO Aus): {v_plus} → Nodes: {refs_on_net(v_plus)[:8]}")
print(f"  /V- (LDO Aus): {v_minus} → Nodes: {refs_on_net(v_minus)[:8]}")

# Prüfe: U1 DC/DC: Eingang 24V, Ausgang +12V_RAW und -12V_RAW
u1_pins = get_pins("U1")
u1_input_ok  = vin_24 in u1_pins.values()
u1_out_p_ok  = pos_raw in u1_pins.values()
u1_out_n_ok  = neg_raw in u1_pins.values()
p("PASS" if u1_input_ok else "FAIL", "U1 24V-Eingang", f"pin-nets: {set(u1_pins.values())}")
p("PASS" if u1_out_p_ok else "FAIL", "U1 +12V_RAW Ausgang", f"pin-nets: {set(u1_pins.values())}")
p("PASS" if u1_out_n_ok else "FAIL", "U1 -12V_RAW Ausgang", f"pin-nets: {set(u1_pins.values())}")

# FB1: verbindet +12V_RAW mit +12V
fb1_ns = pins_nets("FB1"); fb2_ns = pins_nets("FB2")
fb1_ok = pos_raw in fb1_ns and pos_reg in fb1_ns
fb2_ok = neg_raw in fb2_ns and neg_reg in fb2_ns
p("PASS" if fb1_ok else "FAIL", "FB1: +12V_RAW → +12V", f"{fb1_ns}")
p("PASS" if fb2_ok else "FAIL", "FB2: -12V_RAW → -12V", f"{fb2_ns}")

# U14: ADP7118 pos LDO — Eingang pos_reg, Ausgang /V+
u14_pins = get_pins("U14")
u14_in_ok  = pos_reg in u14_pins.values()   # +12V → input
u14_out_ok = v_plus in u14_pins.values()     # /V+ = output
u14_en_ok  = "/EN_CTRL" in u14_pins.values()
p("PASS" if u14_in_ok else "FAIL", "U14 Eingang aus +12V", f"{set(u14_pins.values())}")
p("PASS" if u14_out_ok else "FAIL", "U14 Ausgang /V+", f"{set(u14_pins.values())}")
p("PASS" if u14_en_ok else "FAIL", "U14 EN_CTRL", f"{set(u14_pins.values())}")

# U15: ADP7182 neg LDO — Eingang neg_reg (/V- raw), Ausgang /V-
u15_pins = get_pins("U15")
u15_in_ok  = neg_reg in u15_pins.values()
u15_out_ok = v_minus in u15_pins.values()
u15_en_ok  = "/EN_CTRL" in u15_pins.values()
p("PASS" if u15_in_ok else "FAIL", "U15 Eingang aus -12V", f"{set(u15_pins.values())}")
p("PASS" if u15_out_ok else "FAIL", "U15 Ausgang /V-", f"{set(u15_pins.values())}")
p("PASS" if u15_en_ok else "FAIL", "U15 EN_CTRL", f"{set(u15_pins.values())}")

# Alle OpAmps erhalten /V+ / /V-
print("\n  Versorgung aller OpAmps (U2-U13):")
opamp_vcc_ok = True
for uid in [f"U{i}" for i in range(2, 14)]:
    up = get_pins(uid)
    vp = up.get("8","?"); vm = up.get("4","?")
    ok = (vp == v_plus) and (vm == v_minus)
    if not ok: opamp_vcc_ok = False
    p("PASS" if ok else "FAIL", f"{uid} V+/V-", f"pin8={vp}, pin4={vm}")
p("PASS" if opamp_vcc_ok else "FAIL", "Alle OpAmps richtig versorgt", f"/V+={v_plus}, /V-={v_minus}")


# ─── Schritt B: EN/REMOTE Signalpfad ─────────────────────────────────────────
print("\n[B] ENABLE / REMOTE PFAD")

en_ctrl = "/EN_CTRL"
sw1_pins = get_pins("SW1")
print(f"  SW1 (SPDT): {sw1_pins}")
p("PASS" if en_ctrl in sw1_pins.values() else "FAIL", "SW1→EN_CTRL", str(sw1_pins))
p("PASS" if pos_reg in sw1_pins.values() else "FAIL", "SW1 ALWAYS = +12V", str(sw1_pins))
remote_filt_net = next((n for n in sw1_pins.values() if "REMOTE" in n), None)
p("PASS" if remote_filt_net else "FAIL", "SW1 REMOTE-Seite", str(sw1_pins))

# R1: J2 (Remote-jack) → REMOTE_IN → R1 (Tiefpass) → REMOTE_FILT
r1_pins = get_pins("R1")
r1_has_remote_in   = "/REMOTE_IN" in r1_pins.values()
r1_has_remote_filt = remote_filt_net in r1_pins.values() if remote_filt_net else False
p("PASS" if r1_has_remote_in and r1_has_remote_filt else "FAIL",
  "R1 Tiefpassfilter REMOTE", f"{set(r1_pins.values())}")

# D1: TVS an J2/REMOTE_IN
d1_pins = get_pins("D1")
d1_ok = "/REMOTE_IN" in d1_pins.values() and gnd in d1_pins.values()
p("PASS" if d1_ok else "FAIL", "D1 TVS an REMOTE_IN", f"{set(d1_pins.values())}")

# R56: pull-up /V+ → EN_CTRL
r56_ok = "/EN_CTRL" in pins_nets("R56") and v_plus in pins_nets("R56")
r57_ok = "/EN_CTRL" in pins_nets("R57") and gnd in pins_nets("R57")
p("PASS" if r56_ok else "FAIL", "R56 Pull-up /V+ → EN_CTRL", str(pins_nets("R56")))
p("PASS" if r57_ok else "FAIL", "R57 Pull-down EN_CTRL → GND", str(pins_nets("R57")))

# EN_CTRL → U14.EN und U15.EN
u14_en_net = net_of_pin("U14", "5")
u15_en_net = net_of_pin("U15", "3")
p("PASS" if u14_en_net == en_ctrl else "FAIL", "EN_CTRL → U14.EN", f"{u14_en_net}")
p("PASS" if u15_en_net == en_ctrl else "FAIL", "EN_CTRL → U15.EN", f"{u15_en_net}")


# ─── Schritt C: Muting-Analyse ────────────────────────────────────────────────
print("\n[C] MUTING-SCHALTUNG (Q1-Q7, BSS138)")

mute_net = next((n for n in nets if "/MUTE" == n or "MUTE" == n), None)
print(f"  MUTE-Netz: {mute_net} → Nodes: {refs_on_net(mute_net)}")

# R107: Pull-up /V+ → MUTE
r107_ok = mute_net in pins_nets("R107") and v_plus in pins_nets("R107")
p("PASS" if r107_ok else "FAIL", "R107 Pull-up /V+ → MUTE", str(pins_nets("R107")))

# Q1: Steuert den MUTE-Pegel (BSS138 N-FET)
q1_pins = get_pins("Q1")
print(f"  Q1 Pins: {q1_pins}")
q1_gate  = next((n for n in q1_pins.values() if "Q1-G" in n or "Gate" in n.upper()), None)
# BSS138 SOT-23: pin1=Gate, pin2=Source, pin3=Drain
q1_gate_net  = q1_pins.get("1", "?")   # Gate
q1_source_net = q1_pins.get("2", "?")  # Source
q1_drain_net  = q1_pins.get("3", "?")  # Drain

# Muss MUTE steuern
q1_drain_is_mute = q1_drain_net == mute_net
q1_source_is_gnd = q1_source_net == gnd
print(f"  Q1: Gate={q1_gate_net}, Source={q1_source_net}, Drain={q1_drain_net}")
p("PASS" if q1_source_is_gnd else "FAIL", "Q1 Source→GND (N-FET low-side)", str(q1_source_net))
p("PASS" if q1_drain_is_mute else "FAIL", "Q1 Drain→MUTE", str(q1_drain_net))

# R106: Was treibt Q1-Gate?
r106_pins = get_pins("R106")
print(f"  R106 Nets: {set(r106_pins.values())} (sollte Q1-Gate + Steuersignal)")
q1_gate_drivers = refs_on_net(q1_gate_net)
print(f"  Q1-Gate-Netz ({q1_gate_net}): Nodes = {q1_gate_drivers}")
# Hat Q1-Gate einen Timing-Kondensator?
q1_gate_caps = [r for r in q1_gate_drivers if r.startswith("C")]
q1_gate_has_cap = len(q1_gate_caps) > 0
p("WARN" if not q1_gate_has_cap else "PASS",
  "Q1-Gate: Timing-Cap vorhanden?",
  f"Gate-Nodes={q1_gate_drivers}" + (" — kein C → kein Soft-Start" if not q1_gate_has_cap else ""))

# Q2-Q7: schalten CH_GAIN_OUT auf GND wenn MUTE high
print("\n  Q2-Q7 Muting-FETs:")
for qi, ch in [(f"Q{i}", i-1) for i in range(2,8)]:
    qp = get_pins(qi)
    q_gate  = qp.get("1","?"); q_src = qp.get("2","?"); q_drn = qp.get("3","?")
    # Check: is there an R on the gate net whose other side connects to /MUTE?
    gate_ok = any("/MUTE" in pins_nets(r) for r in refs_on_net(q_gate) if r.startswith("R"))
    src_ok  = q_src == gnd
    drn_ok  = f"CH{ch}_GAIN_OUT" in q_drn or "GAIN_OUT" in q_drn
    # Prüfe R in Gate-Pfad
    gate_r = [r for r in refs_on_net(q_gate) if r.startswith("R")]
    print(f"  {qi} CH{ch}: Gate={q_gate}→{refs_on_net(q_gate)}, Src={q_src}, Drn={q_drn}")
    p("PASS" if gate_ok else "FAIL", f"{qi} Gate aus MUTE", f"gate_net={q_gate}")
    p("PASS" if src_ok else "FAIL", f"{qi} Source=GND", f"{q_src}")
    p("PASS" if drn_ok else "FAIL", f"{qi} Drain=CH{ch}_GAIN_OUT", f"{q_drn}")

# Logische Überprüfung der Muting-Logik
print("\n  Muting-Logik Summary:")
mute_logic = """
  Q1: Gate <-- R106 <-- (was ist da?)
  Wenn EN_CTRL HIGH:
    U14/U15 aktiviert → /V+ erscheint
    R56 zieht EN_CTRL leicht hoch, R57 zieht runter
    Q1 Gate wie?
  Wenn MUTE HIGH → Q2-Q7 ON → CH_GAIN_OUT kurzgeschlossen → Muted
  Wenn MUTE LOW  → Q2-Q7 OFF → Signal läuft durch
  R107 Pull-up /V+ → MUTE → MUTE normalerweise HIGH
  Q1 zieht MUTE runter wenn ON
  """
print(mute_logic)

# Welches Netz treibt R106?
r106_other_net = [n for n in pins_nets("R106") if "Q1-G" not in n and "Gate" not in n.upper()]
print(f"  R106 anderes Netz (Treiber): {r106_other_net}")
r106_driven_by_vplus = v_plus in r106_other_net
r106_driven_by_en = "/EN_CTRL" in r106_other_net
p("PASS" if r106_driven_by_vplus else "WARN",
  "R106 Treiber = /V+ (Q1 immer ON wenn V+ da)",
  str(r106_other_net))

# Soft-Start via U14 SS-Pin
u14_ss_net = net_of_pin("U14", "6")
ss_cap = [r for r in refs_on_net(u14_ss_net) if r.startswith("C")]
print(f"  U14 SS/NR Pin6 Netz ({u14_ss_net}): Nodes={refs_on_net(u14_ss_net)}")
p("PASS" if ss_cap else "WARN", "U14 Soft-Start Cap (SS-Pin)", f"Caps={ss_cap}")

u15_nr_net = net_of_pin("U15", "4")
nr_cap = [r for r in refs_on_net(u15_nr_net) if r.startswith("C")]
print(f"  U15 NR Pin4 Netz ({u15_nr_net}): Nodes={refs_on_net(u15_nr_net)}")
p("PASS" if nr_cap else "WARN", "U15 Noise-Reduction Cap", f"Caps={nr_cap}")


# ─── Schritt D: Diff-Empfänger-Topologie (CH1 vollständig) ───────────────────
print("\n[D] DIFF-EMPFÄNGER CH1 (U2) — vollständige Topologie")

# XLR → EMI-Filter → OpAmp
j3_hot_raw  = net_of_pin("J3", "2")
j3_cold_raw = net_of_pin("J3", "3")
print(f"  J3 HOT_RAW: {j3_hot_raw}, COLD_RAW: {j3_cold_raw}")

# Zwischennetze nach EMI-Filter
j3_hot_raw_nodes  = refs_on_net(j3_hot_raw)
j3_cold_raw_nodes = refs_on_net(j3_cold_raw)
print(f"  {j3_hot_raw} Nodes: {j3_hot_raw_nodes}")
print(f"  {j3_cold_raw} Nodes: {j3_cold_raw_nodes}")

# EMI-R: R94,R95
r94_nets = pins_nets("R94"); r95_nets = pins_nets("R95")
r94_out = [n for n in r94_nets if j3_hot_raw not in n][0] if len(r94_nets) > 1 else "?"
r95_out = [n for n in r95_nets if j3_cold_raw not in n][0] if len(r95_nets) > 1 else "?"
print(f"  R94 (EMI HOT): {j3_hot_raw} → {r94_out}")
print(f"  R95 (EMI COLD): {j3_cold_raw} → {r95_out}")

# U2 IN+ = pin3, IN- = pin2
u2_inp = net_of_pin("U2", "3")
u2_inn = net_of_pin("U2", "2")
print(f"  U2 IN+A (pin3): {u2_inp}")
print(f"  U2 IN-A (pin2): {u2_inn}")

# Prüfe: r94_out = u2_inp?
p("PASS" if r94_out and r94_out == u2_inp else "FAIL",
  "R94 → U2.IN+ (HOT nach EMI)", f"R94_out={r94_out}, U2_IN+={u2_inp}")

# U2 IN-A kommt von R_feedback und COLD-Seite
u2_inn_nodes = refs_on_net(u2_inn)
print(f"  U2 IN-A Netz ({u2_inn}) Nodes: {u2_inn_nodes}")
# Muss R (feedback) und R (COLD-Input) sein
r_inn_nodes = [r for r in u2_inn_nodes if r.startswith("R")]
p("PASS" if len(r_inn_nodes) >= 2 else "FAIL",
  "U2.IN-A hat ≥2 Widerstände (COLD-In + Feedback)", f"R-Nodes={r_inn_nodes}")

# U2 OpAmp B (Gain): pin5=IN+B, pin6=IN-B, pin7=OutB
u2_b_inp = net_of_pin("U2", "5")
u2_b_inn = net_of_pin("U2", "6")
u2_b_out = net_of_pin("U2", "7")
print(f"\n  U2 OpAmpB: IN+B(p5)={u2_b_inp}, IN-B(p6)={u2_b_inn}, OutB(p7)={u2_b_out}")

# IN+B soll GND sein (inverting amp)
p("PASS" if u2_b_inp == gnd else "FAIL",
  "U2.IN+B = GND (inverting Konfig)", f"{u2_b_inp}")

# IN-B = SUMNODE, OutB = GAIN_OUT
sumnode_ch1 = u2_b_inn
gainout_ch1 = u2_b_out
print(f"  CH1 SUMNODE: {sumnode_ch1}")
print(f"  CH1 GAIN_OUT: {gainout_ch1}")

# SUMNODE-Verbindungen: RX_OUT (via R26), SW_OUTs (via R27-R29), GAIN_OUT (Feedback via R50)
sumnode_nodes = refs_on_net(sumnode_ch1)
print(f"  SUMNODE Nodes: {sumnode_nodes}")
# R26: RX_OUT ↔ SUMNODE
r26_nets = pins_nets("R26")
r26_ok = sumnode_ch1 in r26_nets and net_of_pin("U2","1") in r26_nets
# R50: SUMNODE ↔ GAIN_OUT (Feedback)
r50_nets = pins_nets("R50")
r50_ok = sumnode_ch1 in r50_nets and gainout_ch1 in r50_nets
p("PASS" if r26_ok else "FAIL", "R26: RX_OUT ↔ SUMNODE", f"{r26_nets}")
p("PASS" if r50_ok else "FAIL", "R50: SUMNODE ↔ GAIN_OUT (Feedback)", f"{r50_nets}")

# Gain-Berechnung für CH1
print("\n  Gain-Berechnung CH1 (inverting inverter):")
r_vals = {}
for rr in ["R26","R27","R28","R29","R50"]:
    val = components.get(rr,{}).get("value","?")
    r_v = parse_resistance(val)
    r_vals[rr] = r_v
    print(f"  {rr}: {val} = {r_v}Ω")

if all(r_vals.get(r) for r in ["R26","R50"]):
    base_gain_db = 20 * math.log10(r_vals["R50"] / r_vals["R26"])
    print(f"  Basis-Gain (nur R26+R50, kein DIP): {base_gain_db:.2f} dB")

    # Je nach DIP-Position: R27/R28/R29 werden parallel zu R26
    print("  DIP-Gain-Stufen (inverting summing amp):")
    for name, active_rs in [
        ("Kein DIP", []),
        ("DIP Pos1 (R27)", ["R27"]),
        ("DIP Pos2 (R28)", ["R28"]),
        ("DIP Pos3 (R29)", ["R29"]),
        ("DIP Pos1+2", ["R27","R28"]),
        ("DIP Pos1+3", ["R27","R29"]),
        ("DIP Pos2+3", ["R28","R29"]),
        ("DIP 1+2+3", ["R27","R28","R29"]),
    ]:
        # Rin_eff = parallel combination of R26 and all active Rs
        inv_sum = 1.0 / r_vals["R26"]
        valid = True
        for ar in active_rs:
            if r_vals.get(ar):
                inv_sum += 1.0 / r_vals[ar]
            else:
                valid = False
        if valid:
            rin_eff = 1.0 / inv_sum
            gain = r_vals["R50"] / rin_eff
            gain_db = 20 * math.log10(gain)
            print(f"    {name:20s}: Rin_eff={rin_eff:.0f}Ω → Gain={gain:.3f} ({gain_db:+.2f} dB)")

p("PASS" if r_vals.get("R26") and r_vals.get("R50") else "FAIL",
  "Gain-Berechnung möglich", str(r_vals))


# ─── Schritt E: Driver-Stufe CH1 (U8) ────────────────────────────────────────
print("\n[E] BALANCED DRIVER CH1 (U8)")

# U8 OpAmpA: Buffer (HOT Ausgang)
# U8 OpAmpB: Inverting (COLD Ausgang)
u8_p = get_pins("U8")
u8_a_inp = u8_p.get("3","?")  # IN+A
u8_a_inn = u8_p.get("2","?")  # IN-A
u8_a_out = u8_p.get("1","?")  # OutA
u8_b_inp = u8_p.get("5","?")  # IN+B
u8_b_inn = u8_p.get("6","?")  # IN-B
u8_b_out = u8_p.get("7","?")  # OutB
print(f"  U8 OpAmpA: IN+(p3)={u8_a_inp}, IN-(p2)={u8_a_inn}, Out(p1)={u8_a_out}")
print(f"  U8 OpAmpB: IN+(p5)={u8_b_inp}, IN-(p6)={u8_b_inn}, Out(p7)={u8_b_out}")

# OpAmpA: Buffer-Konfiguration? IN- = Out (direktes Feedback)
p("PASS" if u8_a_inn == u8_a_out else "FAIL",
  "U8.OpAmpA Buffer (IN- = Out)", f"IN-={u8_a_inn}, Out={u8_a_out}")

# OpAmpA Eingang = GAIN_OUT
p("PASS" if u8_a_inp == gainout_ch1 else "FAIL",
  "U8.OpAmpA Eingang = CH1_GAIN_OUT", f"IN+={u8_a_inp}, GAIN_OUT={gainout_ch1}")

# OpAmpB: Inverting
p("PASS" if u8_b_inp == gnd else "FAIL",
  "U8.OpAmpB IN+ = GND (inverting)", f"IN+B={u8_b_inp}")

# Feedback-R für OpAmpB: IN-B Netz
u8_b_inn_nodes = refs_on_net(u8_b_inn)
r_u8b = [r for r in u8_b_inn_nodes if r.startswith("R")]
print(f"  U8.OpAmpB IN-B Netz ({u8_b_inn}): {u8_b_inn_nodes}")
p("PASS" if len(r_u8b) >= 2 else "FAIL",
  "U8.OpAmpB hat Feedback + Input R", f"R-Nodes={r_u8b}")

# OpAmpB Eingang: kommt von GAIN_OUT (über R)
gain_out_on_b_path = any(
    gainout_ch1 in pins_nets(r) for r in r_u8b
)
p("PASS" if gain_out_on_b_path else "FAIL",
  "U8.OpAmpB Input aus GAIN_OUT (COLD inverter)", f"Prüfe Rs: {r_u8b}")

# Ausgänge → XLR J9
j9_hot  = net_of_pin("J9", "2")  # /CH1_OUT_HOT
j9_cold = net_of_pin("J9", "3")  # /CH1_OUT_COLD
print(f"\n  J9 HOT={j9_hot}, COLD={j9_cold}")

# Weg von U8.OutA (BUF_DRIVE) zu J9.HOT
def trace_to(start_net, target_net, max_hops=5):
    """BFS: Kann man von start_net über beliebige passive Bauteile target_net erreichen?"""
    visited = set([start_net])
    frontier = [start_net]
    for hop in range(max_hops):
        next_frontier = []
        for net in frontier:
            for ref, _ in nodes_on_net(net):
                # Passiv: R, C, L, FB, D (kein OpAmp/IC mit Gain)
                if not re.match(r'^[RCLDFB]', ref): continue
                for other_net in pins_nets(ref):
                    if other_net == target_net:
                        return True, hop+1
                    if other_net not in visited:
                        visited.add(other_net)
                        next_frontier.append(other_net)
        frontier = next_frontier
    return False, -1

hot_ok, hot_hops   = trace_to(u8_a_out, j9_hot)
cold_ok, cold_hops = trace_to(u8_b_out, j9_cold)
p("PASS" if hot_ok else "FAIL",
  f"U8.OutA → J9.HOT ({j9_hot})", f"Hops={hot_hops}")
p("PASS" if cold_ok else "FAIL",
  f"U8.OutB → J9.COLD ({j9_cold})", f"Hops={cold_hops}")


# ─── Schritt F: Alle 6 Kanäle vollständig ────────────────────────────────────
print("\n[F] ALLE 6 KANÄLE — Vollständigkeit und Symmetrie")

all_ch_ok = True
for ch in range(1, 7):
    jn_in   = f"J{ch+2}"
    u_rx    = f"U{ch+1}"
    sw      = f"SW{ch+1}"
    u_drv   = f"U{ch+7}"
    jn_out  = f"J{ch+8}"

    # Prüfe dass alle existieren
    ok_exist = all(c in components for c in [jn_in, u_rx, sw, u_drv, jn_out])

    # Prüfe V+/V- für rx und drv
    rx_vcc  = net_of_pin(u_rx, "8") == v_plus and net_of_pin(u_rx, "4") == v_minus
    drv_vcc = net_of_pin(u_drv, "8") == v_plus and net_of_pin(u_drv, "4") == v_minus

    # Prüfe CH_RX_OUT Netz
    rx_out_net = f"/CH{ch}_RX_OUT"
    sw_has_rx  = rx_out_net in pins_nets(sw)
    rx_has_out = rx_out_net in pins_nets(u_rx)

    # Prüfe CH_GAIN_OUT: verbindet U_rx.OutB mit U_drv.IN+A
    gain_out_net = f"/CH{ch}_GAIN_OUT"
    rx_gain_ok  = gain_out_net in pins_nets(u_rx)
    drv_gain_ok = gain_out_net in pins_nets(u_drv)

    # XLR Ausgang
    out_hot  = net_of_pin(jn_out, "2")
    out_cold = net_of_pin(jn_out, "3")
    drv_out_a = net_of_pin(u_drv, "1")
    drv_out_b = net_of_pin(u_drv, "7")
    hot_reach,_  = trace_to(drv_out_a, out_hot)
    cold_reach,_ = trace_to(drv_out_b, out_cold)

    ch_ok = ok_exist and rx_vcc and drv_vcc and sw_has_rx and rx_has_out and \
            rx_gain_ok and drv_gain_ok and hot_reach and cold_reach
    all_ch_ok = all_ch_ok and ch_ok

    status = "PASS" if ch_ok else "FAIL"
    if not ch_ok:
        issues = []
        if not ok_exist: issues.append("Fehlt")
        if not rx_vcc: issues.append(f"{u_rx}:no-VCC")
        if not drv_vcc: issues.append(f"{u_drv}:no-VCC")
        if not sw_has_rx: issues.append(f"{sw}:no-RX_OUT")
        if not rx_gain_ok or not drv_gain_ok: issues.append("GAIN_OUT broken")
        if not hot_reach: issues.append(f"{jn_out}.HOT unreachable")
        if not cold_reach: issues.append(f"{jn_out}.COLD unreachable")
        p(status, f"CH{ch} Komplett: {jn_in}→{u_rx}→{sw}→{u_drv}→{jn_out}",
          f"Issues={issues}")
    else:
        p(status, f"CH{ch} Komplett: {jn_in}→{u_rx}→{sw}→{u_drv}→{jn_out}",
          f"V+/V-✓ RX_OUT✓ GAIN_OUT✓ XLR-OUT✓")

p("PASS" if all_ch_ok else "FAIL", "Alle 6 Kanäle vollständig", "")


# ─── Schritt G: ESD-Schutz-Topologie ─────────────────────────────────────────
print("\n[G] ESD-SCHUTZ-TOPOLOGIE")

# D1: TVS an REMOTE_IN/GND ✓ (bereits geprüft)
# D2-D7: an XLR-OUT HOT
for d_idx in range(2,8):
    d = f"D{d_idx}"; expected_net = f"/CH{d_idx-1}_OUT_HOT"
    d_ns = pins_nets(d)
    ok = expected_net in d_ns and gnd in d_ns
    p("PASS" if ok else "FAIL", f"{d} ESD OUT_HOT CH{d_idx-1}", f"{d_ns}")

# D8-D25: per-Channel ESD
# Erwartung: je CH gibt es ESD-Dioden auf HOT_RAW und COLD_RAW
print("\n  Per-Channel ESD (D8-D25):")
for ch in range(1, 7):
    hot_raw  = f"/CH{ch}_HOT_RAW"
    cold_raw = f"/CH{ch}_COLD_RAW"
    hot_esd  = [d for d, _ in nodes_on_net(hot_raw) if d.startswith("D")]
    cold_esd = [d for d, _ in nodes_on_net(cold_raw) if d.startswith("D")]
    p("PASS" if hot_esd else "FAIL", f"CH{ch} ESD auf HOT_RAW", f"D={hot_esd}")
    p("PASS" if cold_esd else "FAIL", f"CH{ch} ESD auf COLD_RAW", f"D={cold_esd}")


# ─── Schritt H: Entkopplung pro Versorgungsknoten ────────────────────────────
print("\n[H] ENTKOPPLUNG")

def count_caps_on_net(net):
    return len([r for r, _ in nodes_on_net(net) if r.startswith("C")])

c_vplus  = count_caps_on_net(v_plus)
c_vminus = count_caps_on_net(v_minus)
c_pos12  = count_caps_on_net(pos_reg)
c_neg12  = count_caps_on_net(neg_reg)
c_posraw = count_caps_on_net(pos_raw)
c_negraw = count_caps_on_net(neg_raw)
c_vin    = count_caps_on_net(vin_24)

print(f"  Caps an {vin_24}: {c_vin}")
print(f"  Caps an {pos_raw}: {c_posraw}")
print(f"  Caps an {neg_raw}: {c_negraw}")
print(f"  Caps an {pos_reg}: {c_pos12}")
print(f"  Caps an {neg_reg}: {c_neg12}")
print(f"  Caps an {v_plus}:  {c_vplus}")
print(f"  Caps an {v_minus}: {c_vminus}")

p("PASS" if c_vin >= 1 else "FAIL", "24V-Eingang: Eingangs-Cap", f"{c_vin} Caps")
p("PASS" if c_posraw >= 2 else "WARN", "+12V_RAW: Caps", f"{c_posraw}")
p("PASS" if c_negraw >= 2 else "WARN", "-12V_RAW: Caps", f"{c_negraw}")
p("PASS" if c_vplus >= 10 else "WARN", "/V+ Entkopplung (≥10 Cs für 12 OpAmps)", f"{c_vplus}")
p("PASS" if c_vminus >= 10 else "WARN", "/V- Entkopplung",  f"{c_vminus}")

# Prüfe ob jeder OpAmp seinen eigenen 100nF hat
print("\n  100nF Entkopplung pro OpAmp auf /V+:")
for uid in [f"U{i}" for i in range(2,14)]:
    vplus_caps = [c for c,_ in nodes_on_net(v_plus) if c.startswith("C")]
    # 100nF caps (0.1uF NP0/C0G)
    local_100nF = [c for c in vplus_caps
                   if "100n" in components.get(c,{}).get("value","").lower()
                   or "0.1u" in components.get(c,{}).get("value","").lower()
                   or "100nF" in components.get(c,{}).get("value","")
                   or "100N" in components.get(c,{}).get("value","").upper()]
    # Wir können nicht pro-OpAmp zuordnen ohne Layout-Info, also nur Gesamtzahl
    break  # Nur einmal
print(f"  100nF Caps auf /V+ gesamt: {len(local_100nF)}")
p("PASS" if len(local_100nF) >= 12 else "WARN",
  "100nF-Caps auf V+ (≥12 für 12 OpAmps)", f"{len(local_100nF)} Stück")


# ─── Schritt I: Impedanz-Check Diff-Empfänger ────────────────────────────────
print("\n[I] IMPEDANZ-CHECK Diff-Empfänger CH1 (U2.OpAmpA)")
# Standard-Diff-Amp: alle 4 R gleich für CMRR
# R2: J3_HOT_IN → U2.IN+
# R3: J3_COLD_IN → U2.IN-
# R14: GND → U2.IN+ (Spannungsteiler-R)
# R20: U2.OUT_A → U2.IN- (Feedback)
# Für Diff-Amp: R2=R3=R14=R20 für CMRR=∞

# Finde die 4 R am U2.OpAmpA
u2_inp_net = net_of_pin("U2", "3")
u2_inn_net = net_of_pin("U2", "2")
u2_outa_net = net_of_pin("U2", "1")

r_on_inp = [r for r,_ in nodes_on_net(u2_inp_net) if r.startswith("R")]
r_on_inn = [r for r,_ in nodes_on_net(u2_inn_net) if r.startswith("R")]
print(f"  U2.IN+ ({u2_inp_net}): R-Nodes={r_on_inp}")
print(f"  U2.IN- ({u2_inn_net}): R-Nodes={r_on_inn}")

# Werte prüfen
def print_r_network(refs):
    for r in refs:
        val = components.get(r,{}).get("value","?")
        nets_r = pins_nets(r)
        print(f"    {r}: {val} | Nets: {nets_r}")

print_r_network(r_on_inp)
print_r_network(r_on_inn)

# Prüfe Gleichheit
r_inp_vals = [parse_resistance(components.get(r,{}).get("value","")) for r in r_on_inp]
r_inn_vals = [parse_resistance(components.get(r,{}).get("value","")) for r in r_on_inn]
print(f"  R-Werte IN+: {list(zip(r_on_inp, r_inp_vals))}")
print(f"  R-Werte IN-: {list(zip(r_on_inn, r_inn_vals))}")


# ─── Schritt J: Floating Nodes und Netz-Vollständigkeit ──────────────────────
print("\n[J] NETZ-INTEGRITÄT")

single_nodes = [(n,v) for n,v in nets.items()
                if len(v)==1 and "unconnected" not in n.lower()]
p("PASS" if not single_nodes else "WARN",
  "Keine Floating Nodes (1-Knoten Netze)", f"{len(single_nodes)} Singles: {[x[0] for x in single_nodes[:5]]}")

unconnected = [n for n in nets if "unconnected" in n.lower()]
p("PASS" if not unconnected else "WARN",
  "Keine Unconnected-Netze", f"{len(unconnected)}: {unconnected[:5]}")

# PWR_FLAG
pwr_flags = [n for n in nets if "PWR_FLAG" in n]
print(f"  PWR_FLAG Netze: {pwr_flags}")
p("WARN" if not pwr_flags else "PASS",
  "PWR_FLAG Netze definiert",
  "Keine PWR_FLAGs — ERC kann PWR-Pin-Fehler zeigen" if not pwr_flags else str(pwr_flags))

# Netze mit nur 2 Knoten (eventuell fehlende Verbindungen)
two_node_nets = [(n,v) for n,v in nets.items() if len(v)==2
                 and not any(x in n for x in ["GND","PWR","24V","12V","FLT","raw","RAW"])]
print(f"\n  Netze mit exakt 2 Knoten (könnten unvollständig sein): {len(two_node_nets)}")
for n, v in two_node_nets[:15]:
    print(f"    {n}: {[x[0]+'.'+x[1] for x in v]}")


# ─── ZUSAMMENFASSUNG ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("ZUSAMMENFASSUNG PASS 2")
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
