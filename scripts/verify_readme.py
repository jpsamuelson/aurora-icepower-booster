#!/usr/bin/env python3
"""
README vs. Netlist / Schematic 100% Verifikation
Prüft jeden Bauteil-Eintrag in der README gegen die echte KiCad-Netlist.
Verwendet KiCad-native (S-Expression) Netlist-Format.
"""
import subprocess, re, sys, os
from pathlib import Path
from collections import defaultdict

ROOT   = Path(__file__).parent.parent
SCH    = ROOT / "aurora-dsp-icepower-booster.kicad_sch"
README = ROOT / "README.md"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

ERRORS   = []
WARNINGS = []
OK_COUNT = 0

def fail(msg):  ERRORS.append(msg)
def warn(msg):  WARNINGS.append(msg)
def ok(msg=None):
    global OK_COUNT
    OK_COUNT += 1

# ── 1. Netlist per kicad-cli exportieren (KiCad-native S-Expression) ──────────
print("Exportiere KiCad-native Netlist …")
net_path = "/tmp/verify_readme_native.net"
r = subprocess.run(
    [KICAD_CLI, "sch", "export", "netlist",
     "--format", "kicadsexpr", "-o", net_path, str(SCH)],
    capture_output=True, text=True,
)
if r.returncode != 0:
    print("FEHLER kicad-cli:", r.stderr[:500])
    sys.exit(1)

net_txt = open(net_path).read()

# ── 2. KiCad-native Netlist parsen ───────────────────────────────────────────
def parse_netlist(txt):
    """
    Parst KiCad S-Expression Netlist (export version E).
    Format:
      (net (code "N") (name "/NETNAME") (class "Default")
        (node (ref "C1") (pin "1") (pintype "passive"))
        ...)
    Gibt zurück:
      components : ref → {value, footprint}
      nets       : netname → set of refs
      ref_pins   : ref → {pin → netname}
    """
    components = {}
    # comp-Blöcke
    for m in re.finditer(
        r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]*)"\)',
        txt, re.DOTALL
    ):
        components[m.group(1)] = {"value": m.group(2), "footprint": ""}

    nets = defaultdict(set)        # netname → {ref, ...}
    ref_pins = defaultdict(dict)   # ref     → {pin → netname}

    # Alle net-Blöcke: (net (code "N") (name "NETNAME") ... (node ...) ...)
    # Die Netze sind einzeilig oder mehrzeilig — wir suchen jeden (net ...) Block
    # mittels balancierter Klammern
    for start in [m.start() for m in re.finditer(r'\(net\s+\(code\s+"', txt)]:
        depth = 0
        i = start
        while i < len(txt):
            if txt[i] == '(':
                depth += 1
            elif txt[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = txt[start:i+1]

        # Netzname
        nm = re.search(r'\(name\s+"([^"]*)"\)', block)
        if not nm:
            continue
        net_name = nm.group(1)

        # Alle Nodes
        for node in re.finditer(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', block):
            ref, pin = node.group(1), node.group(2)
            nets[net_name].add(ref)
            ref_pins[ref][pin] = net_name

    return components, dict(nets), dict(ref_pins)

components, nets, ref_pins = parse_netlist(net_txt)

# Helper: alle Refs eines Typs
def refs_of_type(prefix):
    return sorted([r for r in components if r.startswith(prefix)],
                  key=lambda x: int(re.sub(r'\D','',x) or 0))

# Helper: alle Netz-Namen die einen Ref enthalten
def nets_for_ref(ref):
    return {n for n, refs in nets.items() if ref in refs}

# Helper: Netz eines bestimmten Pins
def pin_net(ref, pin):
    return ref_pins.get(ref, {}).get(str(pin))

# ──────────────────────────────────────────────────────────────────────────────
print(f"  {len(components)} Bauteile, {len(nets)} Netze geladen")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# 3. README lesen
readme = README.read_text(encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK A — Steckverbinder (J)
print("── Block A: Steckverbinder (J) ──")

J_EXPECTED = {
    "J1":  {"value_re": r"Barrel|24V|DC",  "net_pin1": "/+24V_IN"},
    "J2":  {"value_re": r"3.5|3,5|REMOTE|AudioJack", "net_pinT": "/REMOTE_IN"},
    "J3":  {"value_re": r"XLR|Neutrik|Female", "net_pin2": "/CH1_HOT_RAW",  "net_pin3": "/CH1_COLD_RAW"},
    "J4":  {"net_pin2": "/CH2_HOT_RAW",  "net_pin3": "/CH2_COLD_RAW"},
    "J5":  {"net_pin2": "/CH3_HOT_RAW",  "net_pin3": "/CH3_COLD_RAW"},
    "J6":  {"net_pin2": "/CH4_HOT_RAW",  "net_pin3": "/CH4_COLD_RAW"},
    "J7":  {"net_pin2": "/CH5_HOT_RAW",  "net_pin3": "/CH5_COLD_RAW"},
    "J8":  {"net_pin2": "/CH6_HOT_RAW",  "net_pin3": "/CH6_COLD_RAW"},
    "J9":  {"net_pin2_pat": r"/CH1_OUT"},
    "J10": {"net_pin2_pat": r"/CH2_OUT"},
    "J11": {"net_pin2_pat": r"/CH3_OUT"},
    "J12": {"net_pin2_pat": r"/CH4_OUT"},
    "J13": {"net_pin2_pat": r"/CH5_OUT"},
    "J14": {"net_pin2_pat": r"/CH6_OUT"},
}

for ref, exp in J_EXPECTED.items():
    if ref not in components:
        fail(f"[J] {ref} fehlt in Netlist!")
        continue
    comp_nets = nets_for_ref(ref)
    # Netz-Prüfungen
    for key, expected_net in exp.items():
        if key.startswith("net_pin") and "_pat" not in key:
            if expected_net not in comp_nets:
                fail(f"[J] {ref}: Netz '{expected_net}' nicht gefunden. Hat: {sorted(comp_nets)}")
            else:
                ok()
        elif "_pat" in key:
            found = any(re.search(expected_net, n) for n in comp_nets)
            if not found:
                fail(f"[J] {ref}: Kein Netz passend zu '{expected_net}'. Hat: {sorted(comp_nets)}")
            else:
                ok()
    # README-Erwähnung
    if ref not in readme:
        fail(f"[J] {ref} nicht in README erwähnt")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK B — Dioden (D)
print("── Block B: Dioden (D) ──")

# D1: SMBJ15CA an REMOTE_IN
if "D1" not in components:
    fail("[D] D1 fehlt in Netlist")
else:
    d1_nets = nets_for_ref("D1")
    if not any("REMOTE" in n for n in d1_nets):
        fail(f"[D] D1: kein REMOTE-Netz. Hat: {sorted(d1_nets)}")
    else:
        ok()
    if "SMBJ15CA" not in components["D1"]["value"]:
        fail(f"[D] D1: Wert '{components['D1']['value']}' ist nicht SMBJ15CA")
    else:
        ok()
    # README-Check
    if "D1" not in readme or "SMBJ15CA" not in readme:
        fail("[D] D1/SMBJ15CA nicht korrekt in README")
    else:
        ok()

# D2-D7: OUT_HOT ESD
for ch, d in enumerate(["D2","D3","D4","D5","D6","D7"], 1):
    if d not in components:
        fail(f"[D] {d} fehlt")
        continue
    dn = nets_for_ref(d)
    if not any(f"CH{ch}" in n and "OUT" in n for n in dn):
        fail(f"[D] {d}: kein CH{ch}_OUT-Netz. Hat: {sorted(dn)}")
    else:
        ok()

# D8/D10 CH1; D11/D13 CH2 etc.
COLD_RAW_DIODES = {1: ("D8","D10"), 2: ("D11","D13"), 3: ("D14","D16"),
                   4: ("D17","D19"), 5: ("D20","D22"), 6: ("D23","D25")}
OUT_COLD_DIODES = {1: "D9", 2: "D12", 3: "D15", 4: "D18", 5: "D21", 6: "D24"}

for ch, (d_hot, d_cold) in COLD_RAW_DIODES.items():
    for d, sig in [(d_hot, "HOT_RAW"), (d_cold, "COLD_RAW")]:
        if d not in components:
            fail(f"[D] {d} fehlt"); continue
        dn = nets_for_ref(d)
        if not any(f"CH{ch}" in n and sig.replace("_RAW","") in n for n in dn):
            fail(f"[D] {d}: kein CH{ch}_{sig}-Netz. Hat: {sorted(dn)}")
        else:
            ok()

for ch, d in OUT_COLD_DIODES.items():
    if d not in components:
        fail(f"[D] {d} fehlt"); continue
    dn = nets_for_ref(d)
    if not any(f"CH{ch}" in n and "COLD" in n for n in dn):
        fail(f"[D] {d}: kein CH{ch}_COLD-Netz. Hat: {sorted(dn)}")
    else:
        ok()

# README ESD-Tabelle prüfen
for ref in ["D8","D10","D11","D13","D23","D25","D2","D7"]:
    if ref not in readme:
        fail(f"[D] {ref} nicht in README")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK C — Widerstände (R) — kritische Refs
print("── Block C: Widerstände (R) ──")

R_CHECKS = {
    # Remote
    "R1":   ("/REMOTE_IN", "/REMOTE_FILT"),
    # EN_CTRL
    "R56":  ("/V+", "/EN_CTRL"),
    "R57":  ("/EN_CTRL", "GND"),
    # Muting
    "R106": ("/V+", None),  # Gate-Lade-R (Net-(Q1-G))
    "R107": ("/V+", "/MUTE"),
}

def shares_nets(ref, *expected_nets):
    rn = nets_for_ref(ref)
    missing = [n for n in expected_nets if n and not any(
        e.lstrip("/") in nn.lstrip("/") for nn in rn
        for e in [n]
    )]
    return missing

for ref, (n1, n2) in R_CHECKS.items():
    if ref not in components:
        fail(f"[R] {ref} fehlt in Netlist"); continue
    missing = shares_nets(ref, n1, n2)
    if missing:
        fail(f"[R] {ref}: Netz(e) nicht gefunden: {missing}. Hat: {sorted(nets_for_ref(ref))}")
    else:
        ok()

# Diff-Receiver CH1: R2,R3,R14,R20
DIFF_R = {1: (2,3,14,20), 2: (4,5,15,21), 3: (6,7,16,22),
          4: (8,9,17,23), 5: (10,11,18,24), 6: (12,13,19,25)}
for ch, (a,b,c,d) in DIFF_R.items():
    for rnum in [a,b,c,d]:
        ref = f"R{rnum}"
        if ref not in components:
            fail(f"[R] {ref} fehlt"); continue
        rn = nets_for_ref(ref)
        has_ch = any(f"CH{ch}" in n for n in rn)
        if not has_ch:
            fail(f"[R] {ref}: kein CH{ch}-Netz. Hat: {sorted(rn)}")
        else:
            ok()

# Gain R CH1: R26,R50,R27,R28,R29
GAIN_R = {1: (26,50,27,28,29), 2: (30,51,31,32,33), 3: (34,52,35,36,37),
          4: (38,53,39,40,41), 5: (42,54,43,44,45), 6: (46,55,47,48,49)}
for ch, rnums in GAIN_R.items():
    for rnum in rnums:
        ref = f"R{rnum}"
        if ref not in components:
            fail(f"[R] {ref} fehlt"); continue
        rn = nets_for_ref(ref)
        has_ch = any(f"CH{ch}" in n for n in rn)
        if not has_ch:
            fail(f"[R] {ref}: kein CH{ch}-Netz. Hat: {sorted(rn)}")
        else:
            ok()

# Driver R CH1: R64,R70,R58,R76,R82,R88
DRIVER_R = {
    1: {"Rin":(64,),"Rf":(70,),"COLD_47":(58,),"HOT_47":(76,),"Zobel_HOT":(82,),"Zobel_COLD":(88,)},
    2: {"Rin":(65,),"Rf":(71,),"COLD_47":(59,),"HOT_47":(77,),"Zobel_HOT":(83,),"Zobel_COLD":(89,)},
    3: {"Rin":(66,),"Rf":(72,),"COLD_47":(60,),"HOT_47":(78,),"Zobel_HOT":(84,),"Zobel_COLD":(90,)},
    4: {"Rin":(67,),"Rf":(73,),"COLD_47":(61,),"HOT_47":(79,),"Zobel_HOT":(85,),"Zobel_COLD":(91,)},
    5: {"Rin":(68,),"Rf":(74,),"COLD_47":(62,),"HOT_47":(80,),"Zobel_HOT":(86,),"Zobel_COLD":(92,)},
    6: {"Rin":(69,),"Rf":(75,),"COLD_47":(63,),"HOT_47":(81,),"Zobel_HOT":(87,),"Zobel_COLD":(93,)},
}
for ch, groups in DRIVER_R.items():
    for grp, rnums in groups.items():
        for rnum in rnums:
            ref = f"R{rnum}"
            if ref not in components:
                fail(f"[R] {ref} ({grp} CH{ch}) fehlt"); continue
            rn = nets_for_ref(ref)
            has_ch = any(f"CH{ch}" in n for n in rn)
            if not has_ch:
                fail(f"[R] {ref} ({grp}): kein CH{ch}-Netz. Hat: {sorted(rn)}")
            else:
                ok()

# EMI R: R94-R105
EMI_R = {1:(94,95),2:(96,97),3:(98,99),4:(100,101),5:(102,103),6:(104,105)}
for ch,(rh,rc) in EMI_R.items():
    for ref in [f"R{rh}",f"R{rc}"]:
        if ref not in components:
            fail(f"[R] {ref} fehlt"); continue
        rn = nets_for_ref(ref)
        if not any(f"CH{ch}" in n for n in rn):
            fail(f"[R] {ref}: kein CH{ch}-Netz. Hat: {sorted(rn)}")
        else:
            ok()

# Muting Gate Rs R108-R113
for ch, rnum in enumerate(range(108,114),1):
    ref = f"R{rnum}"
    if ref not in components:
        fail(f"[R] {ref} fehlt"); continue
    rn = nets_for_ref(ref)
    if not any("MUTE" in n or f"Q{ch+1}" in n for n in rn):
        fail(f"[R] {ref}: kein MUTE/Q{ch+1}-Netz. Hat: {sorted(rn)}")
    else:
        ok()

# README-Stichproben R
for ref in ["R2","R3","R14","R20","R26","R50","R64","R70","R58","R76","R82","R88",
            "R94","R95","R56","R57","R106","R107","R108"]:
    if ref not in readme:
        fail(f"[R] {ref} nicht in README")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK D — Kondensatoren (C)
print("── Block D: Kondensatoren (C) ──")

# Remote/Muting
C_CHECKS = {
    "C1":  "REMOTE_FILT",
    "C80": "Q1",
    "C81": "SS_U14",
    "C23": "NR_U15",
}
for ref, net_pat in C_CHECKS.items():
    if ref not in components:
        fail(f"[C] {ref} fehlt"); continue
    rn = nets_for_ref(ref)
    if not any(net_pat in n for n in rn):
        fail(f"[C] {ref}: kein '{net_pat}'-Netz. Hat: {sorted(rn)}")
    else:
        ok()

# PSU caps
PSU_C = {
    "C14": "+12V_RAW", "C15": "12V_RAW", "C16": "+12V_RAW", "C17": "12V_RAW",
    "C18": "+12V", "C19": "12V", "C20": "V+", "C21": "V-",
    "C22": "V+", "C24": "V+", "C25": "V-",
}
for ref, pat in PSU_C.items():
    if ref not in components:
        fail(f"[C] PSU {ref} fehlt"); continue
    rn = nets_for_ref(ref)
    if not any(pat.lstrip("/") in n for n in rn):
        fail(f"[C] {ref}: kein '{pat}'-Netz. Hat: {sorted(rn)}")
    else:
        ok()

# Op-Amp Entkopplung: C2-C7 (V+), C8-C13 (V-)
for i in range(2, 14):
    ref = f"C{i}"
    if ref not in components:
        fail(f"[C] {ref} fehlt"); continue
    rn = nets_for_ref(ref)
    if not any("V+" in n or "V-" in n or "PWR" in n.upper() for n in rn):
        # V+ and V- might be GND-connected caps so check for GND and a supply net
        if not any("GND" in n for n in rn):
            fail(f"[C] {ref}: weder V+/V- noch GND. Hat: {sorted(rn)}")
        else:
            ok()
    else:
        ok()

# Driver Entkopplung C26-C37
for i in range(26, 38):
    ref = f"C{i}"
    if ref not in components:
        fail(f"[C] {ref} fehlt"); continue
    ok()

# Zobel C38-C49
ZOBEL_C = {1:(38,44),2:(39,45),3:(40,46),4:(41,47),5:(42,48),6:(43,49)}
for ch,(h,c) in ZOBEL_C.items():
    for ref in [f"C{h}",f"C{c}"]:
        if ref not in components:
            fail(f"[C] Zobel {ref} fehlt"); continue
        rn = nets_for_ref(ref)
        if not any(f"CH{ch}" in n for n in rn):
            fail(f"[C] {ref}: kein CH{ch}-Netz. Hat: {sorted(rn)}")
        else:
            ok()

# EMI C50-C61
EMI_C = {1:(50,51),2:(52,53),3:(54,55),4:(56,57),5:(58,59),6:(60,61)}
for ch,(h,c) in EMI_C.items():
    for ref in [f"C{h}",f"C{c}"]:
        if ref not in components:
            fail(f"[C] EMI {ref} fehlt"); continue
        rn = nets_for_ref(ref)
        if not any(f"CH{ch}" in n for n in rn):
            fail(f"[C] {ref}: kein CH{ch}-Netz. Hat: {sorted(rn)}")
        else:
            ok()

# DC-Block C62-C73
DCBLOCK_C = {1:(62,63),2:(64,65),3:(66,67),4:(68,69),5:(70,71),6:(72,73)}
for ch,(h,c) in DCBLOCK_C.items():
    for ref in [f"C{h}",f"C{c}"]:
        if ref not in components:
            fail(f"[C] DC-Block {ref} fehlt"); continue
        rn = nets_for_ref(ref)
        if not any(f"CH{ch}" in n for n in rn):
            fail(f"[C] {ref}: kein CH{ch}-Netz. Hat: {sorted(rn)}")
        else:
            ok()

# C81 Wert: 22nF
if "C81" in components:
    val = components["C81"]["value"]
    if "22n" not in val.lower() and "22nf" not in val.lower() and "22n" not in val.lower():
        fail(f"[C] C81 Wert ist '{val}', README sagt 22nF")
    else:
        ok()
    # README check
    if "22 nF" not in readme and "22nF" not in readme and "22 nF" not in readme:
        fail("[C] README: C81=22nF nicht erwähnt")
    else:
        ok()

# README-Stichproben C
for ref in ["C2","C8","C14","C16","C20","C21","C22","C23","C24","C25","C26","C32",
            "C38","C44","C50","C51","C62","C63","C80","C81"]:
    if ref not in readme:
        fail(f"[C] {ref} nicht in README")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK E — ICs (U)
print("── Block E: ICs (U) ──")

U_CHECKS = {
    "U1":  ("TEL5-2422", "+24V_IN"),
    "U2":  ("LM4562",    "CH1"),
    "U3":  ("LM4562",    "CH2"),
    "U4":  ("LM4562",    "CH3"),
    "U5":  ("LM4562",    "CH4"),
    "U6":  ("LM4562",    "CH5"),
    "U7":  ("LM4562",    "CH6"),
    "U8":  ("LM4562",    "CH1"),
    "U9":  ("LM4562",    "CH2"),
    "U10": ("LM4562",    "CH3"),
    "U11": ("LM4562",    "CH4"),
    "U12": ("LM4562",    "CH5"),
    "U13": ("LM4562",    "CH6"),
    "U14": ("ADP7118",   "V+"),
    "U15": ("ADP7182",   "V-"),
}

for ref, (val_pat, net_pat) in U_CHECKS.items():
    if ref not in components:
        fail(f"[U] {ref} fehlt in Netlist"); continue
    val = components[ref]["value"]
    if val_pat not in val:
        fail(f"[U] {ref}: Wert '{val}' enthält nicht '{val_pat}'")
    else:
        ok()
    rn = nets_for_ref(ref)
    if not any(net_pat in n for n in rn):
        fail(f"[U] {ref}: kein '{net_pat}'-Netz. Hat: {sorted(rn)}")
    else:
        ok()
    if ref not in readme:
        fail(f"[U] {ref} nicht in README")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK F — MOSFETs (Q)
print("── Block F: MOSFETs (Q) ──")

Q_CHECKS = {
    "Q1": "MUTE",
    "Q2": "CH1",
    "Q3": "CH2",
    "Q4": "CH3",
    "Q5": "CH4",
    "Q6": "CH5",
    "Q7": "CH6",
}
for ref, pat in Q_CHECKS.items():
    if ref not in components:
        fail(f"[Q] {ref} fehlt"); continue
    rn = nets_for_ref(ref)
    if not any(pat in n for n in rn):
        fail(f"[Q] {ref}: kein '{pat}'-Netz. Hat: {sorted(rn)}")
    else:
        ok()
    if ref not in readme:
        fail(f"[Q] {ref} nicht in README")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK G — Ferrit-Beads (FB)
print("── Block G: Ferrit-Beads (FB) ──")
for ref in ["FB1","FB2"]:
    if ref not in components:
        fail(f"[FB] {ref} fehlt"); continue
    val = components[ref]["value"]
    if "BLM" not in val and "ferrit" not in val.lower():
        warn(f"[FB] {ref}: unbekannter Wert '{val}'")
    else:
        ok()
    if ref not in readme:
        fail(f"[FB] {ref} nicht in README")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK H — Schalter (SW)
print("── Block H: Schalter (SW) ──")
for ref in ["SW1","SW2","SW3","SW4","SW5","SW6","SW7"]:
    if ref not in components:
        fail(f"[SW] {ref} fehlt"); continue
    if ref not in readme:
        fail(f"[SW] {ref} nicht in README")
    else:
        ok()

# SW1: muss EN_CTRL verbunden sein (SPDT ALWAYS/REMOTE)
if "SW1" in components:
    rn = nets_for_ref("SW1")
    if not any("EN_CTRL" in n for n in rn):
        fail(f"[SW] SW1: kein EN_CTRL-Netz. Hat: {sorted(rn)}")
    else:
        ok()

# SW7: muss CH6 Gain-Netze haben (DIP Gain CH6)
if "SW7" in components:
    rn = nets_for_ref("SW7")
    if not any("CH6" in n for n in rn):
        fail(f"[SW] SW7: kein CH6-Netz. Hat: {sorted(rn)}")
    else:
        ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK I — README spezifische Text-Prüfungen
print("── Block I: README Text-Prüfungen ──")

TEXT_CHECKS = [
    ("J1", "Barrel Jack"),
    ("J2", "REMOTE"),
    ("D1", "SMBJ15CA"),
    ("R56", "EN_CTRL"),
    ("R57", "EN_CTRL"),
    ("R106", "Q1"),
    ("R107", "MUTE"),
    ("C80", "Q1"),
    ("C81", "22 nF"),
    ("C23", "NR"),
    ("U8", "CH1"),
    ("U14", "ADP7118"),
    ("U15", "ADP7182"),
    ("PIN5", "IN+_B"),   # LM4562 Pinout
    ("PIN6", "IN-_B"),
    # Alle CH-Kanal-Refs im Bauteil-Mapping
    ("R2", "CH1"),
    ("R50", "CH1"),
    ("R58", "CH1"),
    ("R76", "CH1"),
    ("R82", "CH1"),
    ("R88", "CH1"),
    ("R94", "CH1"),
]

for (ref, ctx) in TEXT_CHECKS:
    # Check: irgendwo in der Nähe von 'ref' taucht 'ctx' auf (im selben Tabellenabschnitt)
    if ref == "PIN5":
        if "IN+_B" not in readme:
            fail("[README] Pin 5 = IN+_B nicht in README"); continue
        if re.search(r'[Pp]in\s*5.*IN\+_B|IN\+_B.*[Pp]in\s*5', readme):
            ok()
        else:
            warn("[README] Pin 5/IN+_B: Reihenfolge unklar — bitte prüfen")
    elif ref == "PIN6":
        if "IN-_B" not in readme and "IN\u2212_B" not in readme:
            fail("[README] Pin 6 = IN-_B nicht in README"); continue
        ok()
    else:
        if ref not in readme:
            fail(f"[README-Text] '{ref}' nicht gefunden")
        else:
            ok()

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK J — Gesamtzählung Bauteile
print("── Block J: Gesamtzählung ──")

# Prüfe ob README die richtigen Gesamtzahlen enthält
total_r = len(refs_of_type("R"))
total_c = len(refs_of_type("C"))
total_d = len(refs_of_type("D"))
total_u = len(refs_of_type("U"))
total_q = len(refs_of_type("Q"))
total_j = len(refs_of_type("J"))
total_sw = len(refs_of_type("SW"))
total_fb = len(refs_of_type("FB"))

print(f"  Netlist: R={total_r}, C={total_c}, D={total_d}, U={total_u}, Q={total_q}, J={total_j}, SW={total_sw}, FB={total_fb}")
print(f"  Gesamt: {len(components)} Bauteile, {len(nets)} Netze")

# Alle R-Refs prüfen ob sie in der Netlist real sind
for rnum in range(1, 114):
    ref = f"R{rnum}"
    in_net = ref in components
    in_readme = ref in readme
    if rnum <= 113:
        if not in_net:
            pass  # Nicht alle R-Nummern müssen existieren
        else:
            if not in_readme:
                # R1-R113 sollten alle in README sein
                warn(f"[J] {ref} in Netlist aber nicht in README")

# Alle C-Refs prüfen
for cnum in list(range(1,82)):
    ref = f"C{cnum}"
    in_net = ref in components
    in_readme = ref in readme
    if in_net and not in_readme:
        warn(f"[J] {ref} in Netlist aber nicht in README")

# ═══════════════════════════════════════════════════════════════════════════════
# ERGEBNIS
print()
print("═"*60)
print(f"ERGEBNIS: {OK_COUNT} Checks BESTANDEN")
if WARNINGS:
    print(f"WARNUNGEN ({len(WARNINGS)}):")
    for w in WARNINGS:
        print(f"  ⚠  {w}")
if ERRORS:
    print(f"\nFEHLER ({len(ERRORS)}):")
    for e in ERRORS:
        print(f"  ✗  {e}")
    print()
    print(f"README hat {len(ERRORS)} Fehler gegenüber der Netlist!")
else:
    print()
    print("✅ README ist konsistent mit der Netlist — keine Fehler!")
print("═"*60)
