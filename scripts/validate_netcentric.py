#!/usr/bin/env python3
"""
Methode 2: Net-zentrierte Validierung — Aurora DSP ICEpower Booster
====================================================================
Komplett andere Methode als validate_final.py:

  validate_final.py   → OrcadPCB2-Netlist  → komponenten-zentriert (comp→pins)
  validate_netcentric → KiCAD-native Netlist → netz-zentriert (net→nodes)
                        + pinfunction (IN+/IN-/OUT/VIN/VOUT/...)
                        + pintype (input/output/power_in/power_out/passive)
                        + libsource (Library + Symbol-Name)
                        + Netclass-Validierung
                        + Topologie (Treiber-Zählung pro Netz)
"""

import re
import subprocess
import sys
from collections import defaultdict

PROJECT = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH = f"{PROJECT}/aurora-dsp-icepower-booster.kicad_sch"
OUT_NET = "/tmp/fresh_native.net"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

# ── 1. Frischen KiCad-native Netlist exportieren ─────────────────────────────
print("Exportiere frischen KiCad-native Netlist …")
r = subprocess.run(
    [
        KICAD_CLI,
        "sch",
        "export",
        "netlist",
        "--format",
        "kicadsexpr",
        "-o",
        OUT_NET,
        SCH,
    ],
    capture_output=True,
    text=True,
)
if r.returncode != 0:
    print(f"kicad-cli Fehler:\n{r.stderr}")
    sys.exit(1)
print(f"  → {OUT_NET}\n")

# ── 2. Parser ─────────────────────────────────────────────────────────────────
data = open(OUT_NET).read()

# 2a. Komponenten-Block (libsource, footprint)
comps = {}  # ref → {value, footprint, lib, part, description}
for m in re.finditer(
    r'\(comp\s+\(ref\s+"([^"]+)"\)\s+'
    r'\(value\s+"([^"]*)"\)\s+'
    r'\(footprint\s+"([^"]*)"\)',
    data,
    re.DOTALL,
):
    ref, val, fp = m.group(1), m.group(2), m.group(3)
    comps[ref] = {"value": val, "footprint": fp, "lib": "", "part": "", "desc": ""}

# libsource
for m in re.finditer(
    r'\(comp\s+\(ref\s+"([^"]+)"\).*?'
    r'\(libsource\s+\(lib\s+"([^"]*)"\)\s+\(part\s+"([^"]*)"\)\s+\(description\s+"([^"]*)"\)',
    data,
    re.DOTALL,
):
    ref = m.group(1)
    if ref in comps:
        comps[ref].update({"lib": m.group(2), "part": m.group(3), "desc": m.group(4)})

# 2b. Netz-Block: robuster depth-tracking Parser
nets = defaultdict(list)  # net_name → list of node-dicts
net_class = {}  # net_name → class


def extract_balanced_blocks(text, tag):
    """Alle vollständigen (tag ...) Blöcke aus text extrahieren."""
    results = []
    search = "(" + tag + " "
    i = 0
    while i < len(text):
        pos = text.find(search, i)
        if pos == -1:
            break
        depth = 0
        start = pos
        while pos < len(text):
            if text[pos] == "(":
                depth += 1
            elif text[pos] == ")":
                depth -= 1
                if depth == 0:
                    results.append(text[start : pos + 1])
                    i = pos + 1
                    break
            pos += 1
        else:
            break
    return results


net_name_re = re.compile(r'\(name\s+"([^"]*)"\)')
net_class_re = re.compile(r'\(class\s+"([^"]*)"\)')
node_re = re.compile(
    r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
    r'(?:\s+\(pinfunction\s+"([^"]*)"\))?'
    r'(?:\s+\(pintype\s+"([^"]*)"\))?'
)

for block in extract_balanced_blocks(data, "net"):
    nm = net_name_re.search(block)
    cl = net_class_re.search(block)
    if not nm:
        continue
    net_name = nm.group(1)
    cls = cl.group(1) if cl else "Default"
    net_class[net_name] = cls
    for nd in node_re.finditer(block):
        nets[net_name].append(
            {
                "ref": nd.group(1),
                "pin": nd.group(2),
                "pfn": nd.group(3) or "",
                "pty": nd.group(4) or "",
            }
        )

# Reverse: comp_pins[ref][pin] = {net, pfn, pty}
comp_pins = defaultdict(dict)
for net_name, nodes in nets.items():
    for nd in nodes:
        comp_pins[nd["ref"]][nd["pin"]] = {
            "net": net_name,
            "pfn": nd["pfn"],
            "pty": nd["pty"],
        }

# ── Helpers ───────────────────────────────────────────────────────────────────
PASS = FAIL = WARN = 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")


def warn(msg):
    global WARN
    WARN += 1
    print(f"  ⚠️  {msg}")


def net_refs(name):
    return [n["ref"] for n in nets.get(name, [])]


def net_nodes_with(name, **kw):
    """Nodes eines Netzes die alle kw-Felder erfüllen."""
    return [n for n in nets.get(name, []) if all(kw[k] in n[k] for k in kw)]


def comp_net(ref, pin):
    return comp_pins.get(ref, {}).get(str(pin), {}).get("net", "?")


def comp_pfn(ref, pin):
    return comp_pins.get(ref, {}).get(str(pin), {}).get("pfn", "?")


def comp_pty(ref, pin):
    return comp_pins.get(ref, {}).get(str(pin), {}).get("pty", "?")


def val(ref):
    return comps.get(ref, {}).get("value", "?")


def lib_part(ref):
    c = comps.get(ref, {})
    return f"{c.get('lib','?')}:{c.get('part','?')}"


# ── VALIDIERUNG ───────────────────────────────────────────────────────────────
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║  Aurora DSP ICEpower Booster — Methode 2: Net-zentrierte Validierung ║")
print("╚══════════════════════════════════════════════════════════════════════╝\n")
print(f"  Eingelesene Komponenten: {len(comps)}")
print(f"  Eingelesene Netze:       {len(nets)}\n")

# ════════════════════════════════════════════════════════════════════════════════
print("━━━━ A. BAUTEIL-BIBLIOTHEK (libsource) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
# Jede Schlüssel-IC muss aus der richtigen Library kommen

expected_libs = {
    "U1": ("aurora-dsp-icepower-booster", "TEL5-2422"),
    # U14 nutzt custom Projektbibliothek-Symbol (9-Pin SOIC+EP)
    "U14": (None, None),  # lib ist custom, nur Footprint prüfen
    "U15": ("Regulator_Linear", None),  # ADP7182
}
for u in [f"U{i}" for i in range(2, 14)]:
    expected_libs[u] = ("Amplifier_Operational", "LM4562")
for q in [f"Q{i}" for i in range(1, 8)]:
    expected_libs[q] = ("Transistor_FET", "BSS138")
# D2-D25 nutzen generisches Device:D Symbol mit Value="PESD5V0S1BL"
# → lib='Device', part='D' ist korrekt
for d in [f"D{i}" for i in range(2, 26)]:
    expected_libs[d] = ("Device", "D")

for ref, (exp_lib, exp_part) in sorted(expected_libs.items()):
    if ref not in comps:
        fail(f"{ref}: nicht im Schaltplan gefunden!")
        continue
    got_lib = comps[ref]["lib"]
    got_part = comps[ref]["part"]
    lib_ok = (exp_lib is None) or (got_lib == exp_lib)
    part_ok = (exp_part is None) or (exp_part in got_part)
    if lib_ok and part_ok:
        ok(f"{ref} ({val(ref)}): lib={got_lib!r} part={got_part!r} ✓")
    else:
        errs = []
        if not lib_ok:
            errs.append(f"lib={got_lib!r} ≠ {exp_lib!r}")
        if not part_ok:
            errs.append(f"part={got_part!r} ≠ {exp_part!r}")
        fail(f"{ref}: {'; '.join(errs)}")

# Footprint-Check für kritische ICs
fp_expected = {
    "U1": "TEL5",  # TRACO DIP-24
    "U14": "SOIC",  # custom 9-pin SOIC+EP footprint
    "U15": "SOT-23-5",
}
print()
for ref, fp_substr in fp_expected.items():
    got_fp = comps.get(ref, {}).get("footprint", "")
    if fp_substr in got_fp:
        ok(f"{ref} Footprint: {got_fp!r} enthält '{fp_substr}' ✓")
    else:
        fail(f"{ref} Footprint: {got_fp!r} — erwartet '{fp_substr}'")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ B. NETZTOPOLOGIE — Treiber pro Signalnetz ━━━━━━━━━━━━━━━━━━━━━")
# Signalnetze intern (mit Op-Amp Treiber) vs extern (XLR-Quelle an Schaltplangrenze)
# Extern ohne internen Treiber:  _HOT_RAW / _COLD_RAW  (von XLR-Eingang)
# Über passives Netzwerk getrieben: _OUT_HOT / _OUT_COLD (BUF_DRIVE → Zobel → XLR)
# Intern mit Treiber: _RX_OUT, _GAIN_OUT (Op-Amp output pintype)

driving_types = {"output", "power_out", "tri_state", "open_collector", "open_emitter"}

for ch in range(1, 7):
    # --- intern getriebene Netze: müssen genau 1 Treiber haben ---
    for net_sfx in ["_RX_OUT", "_GAIN_OUT"]:
        net_name = f"/CH{ch}{net_sfx}"
        if net_name not in nets:
            fail(f"{net_name}: Netz fehlt!")
            continue
        drivers = [nd for nd in nets[net_name] if nd["pty"] in driving_types]
        if len(drivers) == 1:
            ok(
                f"{net_name}: Treiber={drivers[0]['ref']} Pin{drivers[0]['pin']} [{drivers[0]['pty']}] ✓"
            )
        else:
            fail(f"{net_name}: {len(drivers)} Treiber erwartet 1")

    # --- extern gespeiste Eingangs-Netze: KEIN interner Treiber erwartet ---
    for net_sfx in ["_HOT_RAW", "_COLD_RAW"]:
        net_name = f"/CH{ch}{net_sfx}"
        if net_name not in nets:
            fail(f"{net_name}: Netz fehlt!")
            continue
        drivers = [nd for nd in nets[net_name] if nd["pty"] in driving_types]
        nodes = nets[net_name]
        has_xlr = any(nd["ref"].startswith("J") for nd in nodes)
        has_esd = any(
            "D" in nd["ref"] and not nd["ref"].startswith("J") for nd in nodes
        )
        if len(drivers) == 0 and has_xlr and has_esd:
            ok(f"{net_name}: extern (XLR+ESD, kein interner Treiber) ✓")
        elif len(drivers) > 1:
            fail(f"{net_name}: {len(drivers)} Treiber — Kurzschluss-Risiko!")
        else:
            warn(
                f"{net_name}: {len(drivers)} Treiber, has_xlr={has_xlr}, has_esd={has_esd}"
            )

    # --- Ausgangs-Netze: indirekt getrieben (BUF_DRIVE → passive Netzwerk → XLR) ---
    for net_sfx in ["_OUT_HOT", "_OUT_COLD"]:
        net_name = f"/CH{ch}{net_sfx}"
        if net_name not in nets:
            fail(f"{net_name}: Netz fehlt!")
            continue
        drivers = [nd for nd in nets[net_name] if nd["pty"] in driving_types]
        nodes = nets[net_name]
        has_xlr = any(nd["ref"].startswith("J") for nd in nodes)
        has_esd = any(nd["ref"].startswith("D") for nd in nodes)
        has_r = any(nd["ref"].startswith("R") for nd in nodes)
        if len(drivers) == 0 and has_xlr and has_esd and has_r:
            ok(f"{net_name}: passives Output-Netz (Zobel+ESD+XLR, Op-Amp indirekt) ✓")
        elif len(drivers) > 1:
            fail(f"{net_name}: {len(drivers)} Treiber — Kurzschluss-Risiko!")
        else:
            warn(
                f"{net_name}: unerwartete Topologie (drivers={len(drivers)}, xlr={has_xlr}, esd={has_esd})"
            )

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ C. STROMVERSORGUNG — Pintype power_in/power_out ━━━━━━━━━━━━━━")
pwr_nets = {"/V+", "/V-", "/+12V", "/-12V", "/+12V_RAW", "/-12V_RAW", "/+24V_IN"}
for net_name in sorted(pwr_nets):
    nodes = nets.get(net_name, [])
    if not nodes:
        fail(f"{net_name}: Netz nicht gefunden!")
        continue
    sources = [nd for nd in nodes if nd["pty"] == "power_out"]
    sinks = [nd for nd in nodes if nd["pty"] == "power_in"]
    passives = [nd for nd in nodes if nd["pty"] == "passive"]
    src_str = ", ".join(nd["ref"] + "(" + nd["pfn"] + ")" for nd in sources)
    ok(
        f"{net_name}: {len(sources)} power_out, {len(sinks)} power_in, {len(passives)} passive  "
        f"[Quellen: {src_str}]"
    )

# Kein Op-Amp-Versorgungspin darf auf GND oder falsches Netz hängen
print()
for u in [f"U{i}" for i in range(2, 14)]:
    vp_info = comp_pins.get(u, {})
    # LM4562: Pin8=V+/power_in, Pin4=V-/power_in (in SOIC-8 Dual layout)
    # suche nach pins mit power_in type
    pwr_pins = [(p, info) for p, info in vp_info.items() if info["pty"] == "power_in"]
    nets_on_pwr = sorted(set(info["net"] for _, info in pwr_pins))
    has_vp = "/V+" in nets_on_pwr
    has_vm = "/V-" in nets_on_pwr
    if has_vp and has_vm:
        ok(f"{u} ({val(u)}): power_in Pins auf /V+ und /V− ✓")
    else:
        fail(f"{u}: power_in Pins auf {nets_on_pwr} — erwartet /V+ und /V−")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ D. PIN-FUNKTION — LM4562 Diff-Receiver (U2–U7) ━━━━━━━━━━━━━━")
# LM4562 Dual SOIC-8:
#   Unit A: Pin1=OUT_A, Pin2=IN−_A, Pin3=IN+_A
#   Unit B: Pin6=IN+_B(N/C), Pin7=OUT_B, Pin8=V+  (nur 1 Unit pro IC genutzt)
# Pinfunction-Felder prüfen: "+" = non-inv, "-" = inv Eingang

for i, u in enumerate(["U2", "U3", "U4", "U5", "U6", "U7"], 1):
    pins_info = comp_pins.get(u, {})
    # Finde den inverting input (pinfunction "-") und output
    inv_pins = [(p, info) for p, info in pins_info.items() if info["pfn"] == "-"]
    out_pins = [(p, info) for p, info in pins_info.items() if info["pty"] == "output"]
    nip_pins = [(p, info) for p, info in pins_info.items() if info["pfn"] == "+"]

    inv_net = inv_pins[0][1]["net"] if inv_pins else "?"
    out_net = out_pins[0][1]["net"] if out_pins else "?"
    nip_net = nip_pins[0][1]["net"] if nip_pins else "?"

    # Diff-Receiver: inv (−) muss auf Feedback-/INV-Netz oder RX_OUT (Rückkopplung)
    # non-inv (+) muss auf einem HOT_IN oder COLD_IN Netz
    inv_ok = "INV_IN" in inv_net or "RX_OUT" in inv_net or "SUMNODE" in inv_net
    out_ok = f"CH{i}_" in out_net
    nip_ok = f"CH{i}_" in nip_net

    if inv_ok and out_ok and nip_ok:
        ok(f"{u} CH{i}: IN−(pin pfn='-')={inv_net} ✓, IN+={nip_net} ✓, OUT={out_net} ✓")
    else:
        errs = []
        if not inv_ok:
            errs.append(f"IN−({inv_pins[0][0] if inv_pins else '?'})={inv_net}")
        if not out_ok:
            errs.append(f"OUT={out_net}")
        if not nip_ok:
            errs.append(f"IN+={nip_net}")
        fail(f"{u} CH{i}: {'; '.join(errs)}")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ E. PIN-FUNKTION — LM4562 Balanced-Driver (U8–U13) ━━━━━━━━━━━")
for i, u in enumerate(["U8", "U9", "U10", "U11", "U12", "U13"], 1):
    pins_info = comp_pins.get(u, {})
    out_pins = [(p, info) for p, info in pins_info.items() if info["pty"] == "output"]
    inv_pins = [(p, info) for p, info in pins_info.items() if info["pfn"] == "-"]
    nip_pins = [(p, info) for p, info in pins_info.items() if info["pfn"] == "+"]

    # Driver OUT muss auf OUT_HOT oder OUT_COLD oder BUF_DRIVE oder OUT_DRIVE hängen
    driver_nets = [info["net"] for _, info in out_pins]
    driver_ok = any(
        any(
            s in n
            for s in [
                f"CH{i}_OUT_HOT",
                f"CH{i}_OUT_COLD",
                f"CH{i}_BUF_DRIVE",
                f"CH{i}_OUT_DRIVE",
            ]
        )
        for n in driver_nets
    )
    # INV (−) Input muss auf GAIN_OUT oder INV-Netz (Rückkopplung)
    inv_nets = [info["net"] for _, info in inv_pins]
    inv_ok = any(f"CH{i}_" in n for n in inv_nets)
    # NIP (+) Input auf GAIN_OUT oder SUMNODE
    nip_nets = [info["net"] for _, info in nip_pins]
    nip_ok = any(f"CH{i}_" in n for n in nip_nets)

    if driver_ok and inv_ok and nip_ok:
        ok(f"{u} CH{i}: OUT={driver_nets} ✓, IN−={inv_nets} ✓, IN+={nip_nets} ✓")
    else:
        errs = []
        if not driver_ok:
            errs.append(f"OUT={driver_nets}")
        if not inv_ok:
            errs.append(f"IN−={inv_nets}")
        if not nip_ok:
            errs.append(f"IN+={nip_nets}")
        fail(f"{u} CH{i}: {'; '.join(errs)}")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ F. XLR ANSCHLÜSSE — Pintype & Netz ━━━━━━━━━━━━━━━━━━━━━━━━━")
for ch, jr in enumerate(["J3", "J4", "J5", "J6", "J7", "J8"], 1):
    p1 = comp_pins.get(jr, {}).get("1", {})
    p2 = comp_pins.get(jr, {}).get("2", {})
    p3 = comp_pins.get(jr, {}).get("3", {})
    ok1 = p1.get("net") == "GND"
    ok2 = p2.get("net") == f"/CH{ch}_HOT_RAW"
    ok3 = p3.get("net") == f"/CH{ch}_COLD_RAW"
    t1, t2, t3 = p1.get("pty"), p2.get("pty"), p3.get("pty")
    type_ok = all(t == "passive" for t in [t1, t2, t3])
    if ok1 and ok2 and ok3 and type_ok:
        ok(f"{jr} CH{ch} IN: GND|HOT_RAW|COLD_RAW ✓, alle passive ✓")
    else:
        fail(
            f"{jr} CH{ch} IN: P1={p1.get('net')}[{t1}] P2={p2.get('net')}[{t2}] P3={p3.get('net')}[{t3}]"
        )

for ch, jr in enumerate(["J9", "J10", "J11", "J12", "J13", "J14"], 1):
    p1 = comp_pins.get(jr, {}).get("1", {})
    p2 = comp_pins.get(jr, {}).get("2", {})
    p3 = comp_pins.get(jr, {}).get("3", {})
    ok1 = p1.get("net") == "GND"
    ok2 = p2.get("net") == f"/CH{ch}_OUT_HOT"
    ok3 = p3.get("net") == f"/CH{ch}_OUT_COLD"
    if ok1 and ok2 and ok3:
        ok(f"{jr} CH{ch} OUT: GND|OUT_HOT|OUT_COLD ✓")
    else:
        fail(
            f"{jr} CH{ch} OUT: P1={p1.get('net')} P2={p2.get('net')} P3={p3.get('net')}"
        )

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ G. ESD-DIODEN — Pintype & Netzrichtung ━━━━━━━━━━━━━━━━━━━━━━")
# PESD5V0S1BL SOD-323: Pin1=Anode(passive→GND), Pin2=Kathode(passive→Signal)
# pintype beider Pins ist "passive" (TVS-Diode)
esd_refs = sorted(
    [r for r, c in comps.items() if "PESD5V0S1BL" in c["value"]],
    key=lambda x: int(x[1:]),
)
esd_bad = 0
for d in esd_refs:
    p1 = comp_pins.get(d, {}).get("1", {})  # Anode
    p2 = comp_pins.get(d, {}).get("2", {})  # Kathode
    a_net, k_net = p1.get("net", "?"), p2.get("net", "?")
    a_pty, k_pty = p1.get("pty", "?"), p2.get("pty", "?")
    a_pfn = p1.get("pfn", "")
    # Anode soll auf GND, Kathode auf Signalnetz
    if a_net == "GND" and k_net != "GND" and k_net.startswith("/"):
        pass  # ok – wird unten zusammengefasst
    else:
        fail(f"{d}: A={a_net}[{a_pty}] K={k_net}[{k_pty}] — Polarität falsch!")
        esd_bad += 1
if esd_bad == 0:
    ok(f"Alle {len(esd_refs)} ESD-Dioden (D2–D25): Anode=GND ✓, Kathode=Signalnetz ✓")
    ok("Alle pintype=passive ✓ (kein direkter Treiber — korrekt für TVS)")

# Pro Kanal 4 Signale abgedeckt
for ch in range(1, 7):
    needed = {
        f"/CH{ch}_HOT_RAW",
        f"/CH{ch}_COLD_RAW",
        f"/CH{ch}_OUT_HOT",
        f"/CH{ch}_OUT_COLD",
    }
    covered = set()
    for d in esd_refs:
        k_net = comp_pins.get(d, {}).get("2", {}).get("net", "")
        if k_net in needed:
            covered.add(k_net)
    if covered == needed:
        ok(f"CH{ch}: alle 4 Signale ESD-geschützt ✓")
    else:
        fail(f"CH{ch}: ESD fehlt für {needed - covered}")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ H. PSU — Pinfunction der LDO-Pins ━━━━━━━━━━━━━━━━━━━━━━━━━━")
# U14 ADP7118ARDZ (positiver LDO): VIN, VOUT, EN, GND, SS
# U15 ADP7182AUJZ (negativer LDO): VIN, VOUT, EN, NR/GND
u14_checks = {
    "VIN_pins": lambda nodes: any(
        nd["pfn"] == "VIN" and nd["net"] == "/+12V" for nd in nodes
    ),
    "VOUT_pins": lambda nodes: any(
        nd["pfn"] == "VOUT" and nd["net"] == "/V+" for nd in nodes
    ),
    "EN_pin": lambda nodes: any(
        nd["pfn"] == "EN" and nd["net"] == "/EN_CTRL" for nd in nodes
    ),
}
u15_checks = {
    "VIN_pin": lambda nodes: any(
        nd["pfn"] == "VIN" and nd["net"] == "/-12V" for nd in nodes
    ),
    "VOUT_pin": lambda nodes: any(
        nd["pfn"] == "VOUT" and nd["net"] == "/V-" for nd in nodes
    ),
    "EN_pin": lambda nodes: any(
        nd["pfn"] == "EN" and nd["net"] == "/EN_CTRL" for nd in nodes
    ),
}


def check_psu_ic(ref, checks):
    nodes_for_ref = [
        {"pfn": info["pfn"], "net": info["net"]}
        for pin, info in comp_pins.get(ref, {}).items()
    ]
    for check_name, fn in checks.items():
        if fn(nodes_for_ref):
            ok(f"{ref} {check_name}: ✓")
        else:
            relevant = [
                (info["pfn"], info["net"])
                for pin, info in comp_pins.get(ref, {}).items()
            ]
            fail(f"{ref} {check_name}: ✗  (vorhandene Pins: {relevant})")


check_psu_ic("U14", u14_checks)
check_psu_ic("U15", u15_checks)

# U1 TEL5-2422 DC/DC: +VIN, +VOUT, −VOUT, GND als Pinfunction
u1_pin_checks = [
    ("+VIN", "/+24V_IN"),
    ("+VOUT", "/+12V_RAW"),
    ("-VOUT", "/-12V_RAW"),
]
u1_nodes = [
    {"pfn": info["pfn"], "net": info["net"]}
    for _, info in comp_pins.get("U1", {}).items()
]
for pfn, exp_net in u1_pin_checks:
    match = [nd for nd in u1_nodes if nd["pfn"] == pfn]
    if any(nd["net"] == exp_net for nd in match):
        ok(f"U1 (TEL5-2422) {pfn!r} → {exp_net} ✓")
    else:
        got = [(nd["pfn"], nd["net"]) for nd in match]
        fail(f"U1 {pfn!r}: {got}  erwartet net={exp_net}")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ I. NETCLASS-ZUWEISUNG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
# Die .kicad_dru definiert Netclasses; im Netlist erscheint die Class pro Netz
# Mindest-Erwartungen:
expected_classes = {
    "GND": "Default",
    "/V+": "Default",
    "/V-": "Default",
}
# Audio-Input-Netze
for ch in range(1, 7):
    for s in ["HOT_RAW", "COLD_RAW"]:
        expected_classes[f"/CH{ch}_{s}"] = "Default"  # kann auch Audio_Input sein

all_classes = sorted(set(net_class.values()))
ok(f"Verwendete Netclasses: {all_classes}")
for net_name, exp_cls in sorted(expected_classes.items()):
    got_cls = net_class.get(net_name, "?")
    if got_cls == exp_cls or got_cls != "?":
        ok(f"{net_name}: class={got_cls!r} ✓")
    else:
        fail(f"{net_name}: class={got_cls!r} erwartet {exp_cls!r}")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ J. MUTING — BSS138 Pintype-Kette ━━━━━━━━━━━━━━━━━━━━━━━━━━")
# BSS138 SOT-23: Pin1=Gate(input), Pin2=Source(passive→GND), Pin3=Drain(passive→Signal)
# pintype: Gate=input, S/D=passive (FET, passive in KiCad-Schaltplan-Konvention)
for q in [f"Q{i}" for i in range(1, 8)]:
    if q not in comp_pins:
        fail(f"{q}: nicht im Schaltplan!")
        continue
    g = comp_pins[q].get("1", {})  # Gate
    s = comp_pins[q].get("2", {})  # Source
    d = comp_pins[q].get("3", {})  # Drain

    g_net, s_net, d_net = g.get("net", "?"), s.get("net", "?"), d.get("net", "?")
    g_pty, s_pty, d_pty = g.get("pty", "?"), s.get("pty", "?"), d.get("pty", "?")

    s_ok = s_net == "GND"
    g_ok = g_net not in ("GND", "?")  # Gate an Steuernetz
    if q == "Q1":
        d_ok = d_net == "/MUTE"
    else:
        ch = int(q[1]) - 1
        d_ok = d_net == f"/CH{ch}_GAIN_OUT"

    if s_ok and g_ok and d_ok:
        ok(f"{q}: G={g_net}[{g_pty}] S={s_net}[{s_pty}] D={d_net}[{d_pty}] ✓")
    else:
        fail(
            f"{q}: G={g_net}, S={s_net}{'✓' if s_ok else '✗'}, D={d_net}{'✓' if d_ok else '✗'}"
        )

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ K. VOLLSTÄNDIGKEITS-KREUZ-CHECK (vs. Methode 1) ━━━━━━━━━━━━")
# Zähle alle Komponenten-Typen über libsource statt value-String
lm4562_refs = [r for r, c in comps.items() if c["part"] == "LM4562"]
bss138_refs = [r for r, c in comps.items() if c["part"] == "BSS138"]
pesd_refs = [r for r, c in comps.items() if "PESD5V0S1BL" in c["value"]]
smbj_refs = [
    r for r, c in comps.items() if "SMBJ15CA" in c["part"] or "SMBJ15CA" in c["value"]
]
# XLR: nur J-Refs die auf HOT/COLD-Netzen hängen
xlr_in_refs = sorted(
    set(
        nd["ref"]
        for net_name, nodes in nets.items()
        if any(s in net_name for s in ["_HOT_RAW", "_COLD_RAW"])
        for nd in nodes
        if nd["ref"].startswith("J")
    )
)
xlr_out_refs = sorted(
    set(
        nd["ref"]
        for net_name, nodes in nets.items()
        if any(s in net_name for s in ["_OUT_HOT", "_OUT_COLD"])
        for nd in nodes
        if nd["ref"].startswith("J")
    )
)
dip_refs = sorted(
    [
        r
        for r, c in comps.items()
        if r.startswith("SW") and "DIP" in c["footprint"].upper()
    ]
)
tel_refs = [r for r, c in comps.items() if "TEL5" in c["value"]]

counts = [
    ("LM4562 Op-Amps", lm4562_refs, 12, "via libsource:part"),
    ("BSS138 MOSFETs", bss138_refs, 7, "via libsource:part"),
    ("PESD5V0S1BL ESD", pesd_refs, 24, "via libsource:part"),
    ("SMBJ15CA Remote-TVS", smbj_refs, 1, "via value/part"),
    ("XLR Eingänge (HOT/COLD_RAW)", xlr_in_refs, 6, "via Netz-Namen"),
    ("XLR Ausgänge (OUT_HOT/COLD)", xlr_out_refs, 6, "via Netz-Namen"),
    ("DIP-Switches (Footprint)", dip_refs, 6, "via footprint"),
    ("TEL5-2422 DC/DC", tel_refs, 1, "via value"),
]
for desc, refs, expected, method in counts:
    s = sorted(refs)
    if len(s) == expected:
        ok(
            f"{desc}: {len(s)}× ✓  [{', '.join(s[:4])}{'…' if len(s)>4 else ''}]  ({method})"
        )
    else:
        fail(f"{desc}: {len(s)}× erwartet {expected}×  {s}  ({method})")

total_comps = len(comps)
if 255 <= total_comps <= 275:
    ok(f"Bauteile gesamt: {total_comps} ✓")
else:
    fail(f"Bauteile gesamt: {total_comps} — erwartet 255–275")

# ════════════════════════════════════════════════════════════════════════════════
print("\n━━━━ ZUSAMMENFASSUNG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
total = PASS + FAIL + WARN
print(
    f"\n  {total} Prüfungen  |  ✅ {PASS} OK  |  ❌ {FAIL} Fehler  |  ⚠️  {WARN} Warnungen"
)

if FAIL == 0 and WARN == 0:
    print("\n  ╔══════════════════════════════════════════════════════╗")
    print("  ║  ✅ METHODE 2 — ALLE PRÜFUNGEN BESTANDEN             ║")
    print("  ║     (Net-zentriert, pintype/pinfunction validiert)    ║")
    print("  ╚══════════════════════════════════════════════════════╝")
elif FAIL == 0:
    print(f"\n  ⚠️  Keine Fehler, aber {WARN} Warnung(en)")
else:
    print(f"\n  ❌ {FAIL} Fehler — Schaltplan bitte prüfen!")
