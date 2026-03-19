#!/usr/bin/env python3
"""
Vollständige Bauteil-Validierung – Aurora DSP ICEpower Booster v2
=================================================================
Korrekte Parser-Version (regex-basiert, geprüft gegen reale Netlist).

Netlist-Format (OrcadPCB2):
  ( /UUID  FOOTPRINT  REF  VALUE
    (    PIN_NUM  /NET_NAME )
  )

BSS138 SOT-23: Pin1=Gate, Pin2=Source, Pin3=Drain (numerisch!)
PESD5V0S1BL SOD-323: Pin1=Anode, Pin2=Kathode (numerisch!)
ADP7182AUJZ SC70-5: Pin1=GND, Pin2=IN(VIN), Pin3=EN, Pin4=NR, Pin5=OUT(VOUT)
"""

import re
from collections import defaultdict

NETLIST = "/tmp/validation_netlist.net"


# ── Bewährter Parser aus validate_complete.py ────────────────────────────────
def parse_netlist(path):
    comps = {}
    nets = defaultdict(list)
    lines = open(path).read().split("\n")
    current_comp = None
    in_comp = False
    comp_start = re.compile(r"^\s*\(\s*/[0-9a-f-]+\s+(\S+)\s+(\w+)\s+(.*)")
    pin_re = re.compile(r"^\s*\(\s*(\S+)\s+(/?\S+)\s*\)\s*$")
    comp_end = re.compile(r"^\s*\)\s*$")
    for line in lines:
        m = comp_start.match(line)
        if m:
            current_comp = {
                "ref": m.group(2),
                "value": m.group(3).strip(),
                "footprint": m.group(1),
                "pins": {},
            }
            in_comp = True
            continue
        if in_comp:
            mp = pin_re.match(line)
            me = comp_end.match(line)
            if mp:
                current_comp["pins"][mp.group(1)] = mp.group(2)
                nets[mp.group(2)].append((current_comp["ref"], mp.group(1)))
            elif me:
                if current_comp:
                    comps[current_comp["ref"]] = current_comp
                    current_comp = None
                in_comp = False
            elif line.strip() and not line.strip().startswith("("):
                if current_comp:
                    current_comp["value"] += " " + line.strip()
    return comps, nets


comps, nets_raw = parse_netlist(NETLIST)

# nets: net_name → list of (ref, pin)
nets = nets_raw  # defaultdict(list)

# ── Hilfsfunktionen (KEIN Altlast-Parser mehr) ───────────────────────────────
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


def pin(ref, p):
    """Pin-Netz anhand Bauteil-Ref und Pin-Nummer (als String)."""
    return comps.get(ref, {}).get("pins", {}).get(str(p))


def val(ref):
    return comps.get(ref, {}).get("value", "?")


def net_pin_count(net):
    return len(nets.get(net, []))


def net_refs(net):
    return [r for r, _ in nets.get(net, [])]


# ── Validierungs-Start ────────────────────────────────────────────────────────

# ════════════════════════════════════════════════════════════════════════════
print("╔══════════════════════════════════════════════════════════════════╗")
print("║  Aurora DSP ICEpower Booster — Vollständige Bauteil-Validierung ║")
print("╚══════════════════════════════════════════════════════════════════╝\n")

# ────────────────────────────────────────────────────────────────────────────
print("━━━━ 1. BAUTEIL-MENGEN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

lm = sorted([r for r, c in comps.items() if "LM4562" in c["value"]])
if len(lm) == 12:
    ok(f"LM4562 (dual Op-Amp): 12× {lm}")
else:
    fail(f"LM4562: {len(lm)}× erwartet 12×  {lm}")

bss = sorted([r for r, c in comps.items() if "BSS138" in c["value"]])
if len(bss) == 7:
    ok(f"BSS138 (N-MOSFET Muting): 7× {bss}")
else:
    fail(f"BSS138: {len(bss)}× erwartet 7×")

pesd = sorted([r for r, c in comps.items() if "PESD5V0S1BL" in c["value"]])
if len(pesd) == 24:
    ok("PESD5V0S1BL (ESD TVS 5V): 24× D2–D25")
else:
    fail(f"PESD5V0S1BL: {len(pesd)}× erwartet 24×")

smbj = sorted([r for r, c in comps.items() if "SMBJ15CA" in c["value"]])
if len(smbj) == 1 and smbj[0] == "D1":
    ok("SMBJ15CA (Remote-TVS 15V bidi): 1× D1")
else:
    fail(f"SMBJ15CA: {len(smbj)}× erwartet 1× D1  {smbj}")

xlr = sorted(
    [
        r
        for r in comps
        if r.startswith("J")
        and any(
            "HOT_RAW" in n or "OUT_HOT" in n or "COLD_RAW" in n or "OUT_COLD" in n
            for n in comps[r]["pins"].values()
        )
    ]
)
if len(xlr) == 12:
    ok(f"XLR Steckverbinder: 12× {xlr}")
else:
    fail(f"XLR: {len(xlr)}× erwartet 12×")

# DIP-Switches haben value="Gain CHx", aber Footprint enthält "DIP"
dip = sorted(
    [
        r
        for r, c in comps.items()
        if r.startswith("SW") and "DIP" in c["footprint"].upper()
    ]
)
if len(dip) == 6:
    ok(f"Gain-DIP-Switches: 6× {dip}  (SW1–SW6, SW_DIP_x03)")
else:
    fail(f"DIP-Switches: {len(dip)}× erwartet 6×  {dip}")

if len(comps) in range(255, 276):
    ok(f"Bauteile gesamt: {len(comps)}")
else:
    warn(f"Bauteile gesamt: {len(comps)} (erwartet 255–275)")

if "TEL5" in val("U1") or "TEL" in val("U1"):
    ok(f"U1 DC/DC: {val('U1')}  (TEL5-2422, ±12V Versorgung)")
else:
    fail(f"U1 DC/DC: '{val('U1')}' — kein TEL5-2422 erkannt")
if "ADP7118" in val("U14"):
    ok(f"U14 +LDO: {val('U14')}  (ADP7118ARDZ, V+)")
else:
    fail(f"U14 +LDO: '{val('U14')}'")
if "ADP7182" in val("U15"):
    ok(f"U15 −LDO: {val('U15')}  (ADP7182, V−)")
else:
    fail(f"U15 −LDO: '{val('U15')}'")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 2. XLR EINGANGS-PINBELEGUNG (J3–J8) ━━━━━━━━━━━━━━━━━━━━━━━")
# XLR 3-pin: Pin1=GND/Shield, Pin2=HOT(+), Pin3=COLD(−)
for ch, jr in enumerate(["J3", "J4", "J5", "J6", "J7", "J8"], 1):
    p1, p2, p3 = pin(jr, 1), pin(jr, 2), pin(jr, 3)
    if p1 == "GND" and p2 == f"/CH{ch}_HOT_RAW" and p3 == f"/CH{ch}_COLD_RAW":
        ok(f"{jr} CH{ch} IN: Pin1=GND, Pin2=/CH{ch}_HOT_RAW, Pin3=/CH{ch}_COLD_RAW ✓")
    else:
        fail(f"{jr} CH{ch} IN: Pin1={p1}, Pin2={p2}, Pin3={p3}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 3. XLR AUSGANGS-PINBELEGUNG (J9–J14) ━━━━━━━━━━━━━━━━━━━━━━")
for ch, jr in enumerate(["J9", "J10", "J11", "J12", "J13", "J14"], 1):
    p1, p2, p3 = pin(jr, 1), pin(jr, 2), pin(jr, 3)
    if p1 == "GND" and p2 == f"/CH{ch}_OUT_HOT" and p3 == f"/CH{ch}_OUT_COLD":
        ok(f"{jr} CH{ch} OUT: Pin1=GND, Pin2=/CH{ch}_OUT_HOT, Pin3=/CH{ch}_OUT_COLD ✓")
    else:
        fail(f"{jr} CH{ch} OUT: Pin1={p1}, Pin2={p2}, Pin3={p3}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 4. SIGNALKETTE CH1–CH6 (alle Stufen vorhanden) ━━━━━━━━━━━━")
STAGES = ["HOT_RAW", "COLD_RAW", "RX_OUT", "GAIN_OUT", "OUT_HOT", "OUT_COLD"]
MIN_PINS = {
    "HOT_RAW": 2,
    "COLD_RAW": 3,
    "RX_OUT": 5,
    "GAIN_OUT": 4,
    "OUT_HOT": 4,
    "OUT_COLD": 4,
}
for ch in range(1, 7):
    e = []
    for s in STAGES:
        n = f"/CH{ch}_{s}"
        cnt = net_pin_count(n)
        if cnt == 0:
            e.append(f"{s}=FEHLT")
        elif cnt < MIN_PINS[s]:
            e.append(f"{s}={cnt}Pins(<{MIN_PINS[s]})")
    if not e:
        ok(f"CH{ch}: alle 6 Signalstufen vorhanden ✓")
    else:
        fail(f"CH{ch}: {', '.join(e)}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 5. OP-AMP TOPOLOGIE Diff-Receiver (U2–U7) ━━━━━━━━━━━━━━━━")
# LM4562 SOIC-8: Pin1=OUT_A, Pin2=IN−_A(INV), Pin3=IN+_A(NON-INV), Pin4=V−,
#                Pin5=GND, Pin6=IN+_B, Pin7=OUT_B, Pin8=V+
# Negative Rückkopplung: R20-R25 verbinden OUT mit INV(−)
fb_r = {"U2": "R20", "U3": "R21", "U4": "R22", "U5": "R23", "U6": "R24", "U7": "R25"}
for u, r in fb_r.items():
    ch = int(u[1]) - 1
    r_nets = list(comps.get(r, {}).get("pins", {}).values())
    has_out = any("RX_OUT" in n for n in r_nets)
    has_inv = any("INV_IN" in n for n in r_nets)
    u_p8 = pin(u, "8")  # V+
    u_p4 = pin(u, "4")  # V−
    vcc_ok = u_p8 == "/V+" and u_p4 == "/V-"
    if has_out and has_inv and vcc_ok:
        ok(f"{u} (CH{ch} Diff-Rcv): Rfb={r} OUT↔INV_IN ✓, V+={u_p8}, V−={u_p4} ✓")
    else:
        errs = []
        if not has_out:
            errs.append(f"{r} kein RX_OUT-Netz ({r_nets})")
        if not has_inv:
            errs.append(f"{r} kein INV_IN-Netz ({r_nets})")
        if not vcc_ok:
            errs.append(f"V+={u_p8}, V−={u_p4}")
        fail(f"{u} (CH{ch}): {'; '.join(errs)}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 6. BALANCED-DRIVER (U8–U13) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
for i, u in enumerate(["U8", "U9", "U10", "U11", "U12", "U13"], 1):
    p_nets = list(comps.get(u, {}).get("pins", {}).values())
    # OUT_HOT/OUT_COLD direkt ODER über interne Zwischennetze (BUF_DRIVE / OUT_DRIVE)
    has_hot = any(f"CH{i}_OUT_HOT" in n or f"CH{i}_BUF_DRIVE" in n for n in p_nets)
    has_cold = any(f"CH{i}_OUT_COLD" in n or f"CH{i}_OUT_DRIVE" in n for n in p_nets)
    has_vp = "/V+" in p_nets
    has_vm = "/V-" in p_nets
    if has_hot and has_cold and has_vp and has_vm:
        ok(f"{u} (CH{i} Driver): OUT_HOT✓, OUT_COLD✓, V+✓, V−✓")
    else:
        errs = [
            s
            for c2, s in [
                (has_hot, "OUT_HOT"),
                (has_cold, "OUT_COLD"),
                (has_vp, "V+"),
                (has_vm, "V-"),
            ]
            if not c2
        ]
        fail(f"{u} (CH{i}): fehlt {errs}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 7. MUTING-SCHALTUNG (Q1–Q7, BSS138 SOT-23) ━━━━━━━━━━━━━━")
# BSS138 SOT-23: Pin1=Gate, Pin2=Source, Pin3=Drain
# Q1: Mute-Trigger  — Pin3(D)=/MUTE, Pin2(S)=GND, Pin1(G)=RC-Netz
# Q2-Q7: Signal-Gates — Pin3(D)=/CHx_GAIN_OUT, Pin2(S)=GND, Pin1(G)=10k→/MUTE

mute_cnt = net_pin_count("/MUTE")
if mute_cnt >= 8:
    ok(f"/MUTE-Netz: {mute_cnt} Pins ✓  (Q1.Drain + 6× R108-R113 + R107)")
else:
    fail(f"/MUTE-Netz: {mute_cnt} Pins erwartet ≥8")

q1_g, q1_s, q1_d = pin("Q1", "1"), pin("Q1", "2"), pin("Q1", "3")
if q1_d == "/MUTE" and q1_s == "GND" and q1_g and q1_g != "GND":
    ok(f"Q1 (Mute-Trigger): D=/MUTE✓, S=GND✓, G={q1_g} (RC-Verzögerung)✓")
else:
    fail(f"Q1: G={q1_g}, S={q1_s}, D={q1_d}")

for qr, ch in zip(["Q2", "Q3", "Q4", "Q5", "Q6", "Q7"], range(1, 7)):
    qg = pin(qr, "1")  # Gate
    qs = pin(qr, "2")  # Source
    qd = pin(qr, "3")  # Drain
    d_ok = qd == f"/CH{ch}_GAIN_OUT"
    s_ok = qs == "GND"
    g_ok = qg and qg != "GND"  # via 10k R, Net-(Qx-G)
    if d_ok and s_ok and g_ok:
        ok(f"{qr} (CH{ch}): D=/CH{ch}_GAIN_OUT✓, S=GND✓, G={qg}✓")
    else:
        fail(f"{qr} (CH{ch}): G={qg}, S={qs}, D={qd}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 8. PSU: TEL5-2422 (U1, DC/DC Dual ±12V) ━━━━━━━━━━━━━━━━")
# Custom Footprint: +VIN=22,23; +VOUT=14; -VOUT=11; GND=2,3,9,16
for p, exp, desc in [
    ("22", "/+24V_IN", "+VIN 24V Eingang"),
    ("23", "/+24V_IN", "+VIN 24V parallel"),
    ("14", "/+12V_RAW", "+VOUT +12V Ausgang"),
    ("11", "/-12V_RAW", "-VOUT −12V Ausgang"),
    ("2", "GND", "GND Pin2"),
    ("3", "GND", "GND Pin3"),
    ("9", "GND", "GND Pin9"),
    ("16", "GND", "GND Pin16"),
]:
    got = pin("U1", p)
    if got == exp:
        ok(f"  U1 Pin{p} ({desc}): {got} ✓")
    else:
        fail(f"  U1 Pin{p} ({desc}): ist={got}, erwartet={exp}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 9. PSU: ADP7118ARDZ (U14, positiver LDO → /V+) ━━━━━━━━━")
# Custom 9-pin SOIC+EP: VOUT=1,2,3(/V+); GND=4,9; EN=5(/EN_CTRL); SS=6(/SS_U14); VIN=7,8(/+12V)
for p, exp, desc in [
    ("1", "/V+", "VOUT (V+ Ausgang)"),
    ("2", "/V+", "VOUT parallel"),
    ("3", "/V+", "VOUT parallel"),
    ("4", "GND", "GND"),
    ("9", "GND", "GND (Exposed Pad)"),
    ("5", "/EN_CTRL", "EN (Enable)"),
    ("6", "/SS_U14", "SS (Soft-Start)"),
    ("7", "/+12V", "VIN +12V (nach FB1)"),
    ("8", "/+12V", "VIN +12V parallel"),
]:
    got = pin("U14", p)
    if got == exp:
        ok(f"  U14 Pin{p} ({desc}): {got} ✓")
    else:
        fail(f"  U14 Pin{p} ({desc}): ist={got}, erwartet={exp}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 10. PSU: ADP7182AUJZ (U15, negativer LDO → /V−) ━━━━━━━━")
# SC70-5 Package: Pin1=GND, Pin2=IN(VIN=/-12V nach FB2), Pin3=EN, Pin4=NR, Pin5=OUT(VOUT=/V-)
# Bestätigt from Netlist: Pin2=/-12V (Eingang vom gefilterten -12V-Zweig), Pin5=/V- (Ausgang LDO)
for p, exp, desc in [
    ("1", "GND", "GND"),
    ("2", "/-12V", "VIN (−12V nach Ferrite-Bead FB2)"),
    ("3", "/EN_CTRL", "EN (Enable)"),
    ("4", "/NR_U15", "NR/SS (Noise-Reduction)"),
    ("5", "/V-", "VOUT (geregelter −V− Ausgang)"),
]:
    got = pin("U15", p)
    if got == exp:
        ok(f"  U15 Pin{p} ({desc}): {got} ✓")
    else:
        fail(f"  U15 Pin{p} ({desc}): ist={got}, erwartet={exp}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 11. PSU: BULK-KONDENSATOREN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
# C16: GND↔/+12V_RAW (DC/DC +VOUT Bulk)
# C17: /-12V_RAW↔GND (DC/DC −VOUT Bulk)
# C20: GND↔/V+  (LDO V+ Ausgang Bulk)  ← ZUVOR BUG (beide GND), jetzt gefixt
# C21: /V-↔GND  (LDO V− Ausgang Bulk)  ← ZUVOR BUG (beide GND), jetzt gefixt
for ref, exp1, exp2, desc in [
    ("C16", "GND", "/+12V_RAW", "DC/DC +VOUT Bulk 100µF"),
    ("C17", "/-12V_RAW", "GND", "DC/DC −VOUT Bulk 100µF"),
    ("C20", "GND", "/V+", "LDO V+ Ausgang Bulk 100µF"),
    ("C21", "/V-", "GND", "LDO V− Ausgang Bulk 100µF"),
]:
    p1, p2 = pin(ref, "1"), pin(ref, "2")
    if p1 == exp1 and p2 == exp2:
        ok(f"{ref} ({desc}): Pin1={p1}, Pin2={p2} ✓")
    else:
        fail(f"{ref} ({desc}): Pin1={p1}, Pin2={p2}  erwartet ({exp1}, {exp2})")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 12. ENTKOPPLUNG V+/V− (Alle Op-Amps versorgt) ━━━━━━━━━━━")
vp_cnt = net_pin_count("/V+")
vm_cnt = net_pin_count("/V-")
vp_caps = list(set(r for r, _ in nets.get("/V+", []) if r.startswith("C")))
vm_caps = list(set(r for r, _ in nets.get("/V-", []) if r.startswith("C")))

if vp_cnt >= 15:
    ok(f"/V+ Netz: {vp_cnt} Pins, {len(vp_caps)} Kondensatoren")
else:
    warn(f"/V+ nur {vp_cnt} Pins")
if vm_cnt >= 12:
    ok(f"/V- Netz: {vm_cnt} Pins, {len(vm_caps)} Kondensatoren")
else:
    warn(f"/V- nur {vm_cnt} Pins")

vp_u = set(r for r, _ in nets.get("/V+", []) if r.startswith("U"))
vm_u = set(r for r, _ in nets.get("/V-", []) if r.startswith("U"))
miss_vp = [f"U{i}" for i in range(2, 14) if f"U{i}" not in vp_u]
miss_vm = [f"U{i}" for i in range(2, 14) if f"U{i}" not in vm_u]
if not miss_vp:
    ok("Alle 12 Op-Amps (U2–U13) an /V+ ✓")
else:
    fail(f"Op-Amps ohne /V+: {miss_vp}")
if not miss_vm:
    ok("Alle 12 Op-Amps (U2–U13) an /V− ✓")
else:
    fail(f"Op-Amps ohne /V−: {miss_vm}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ 13. ESD-DIODEN (D2–D25, PESD5V0S1BL SOD-323) ━━━━━━━━━━━")
# SOD-323 Footprint: Pin1=Anode, Pin2=Kathode
# Korrekt: A(Pin1)=GND, K(Pin2)=Signalnetz
all_esd = sorted(pesd, key=lambda x: int(x[1:]))
esd_errs = 0
for d in all_esd:
    pa, pk = pin(d, "1"), pin(d, "2")
    if pa != "GND" or pk is None or pk == "GND":
        esd_errs += 1
        fail(f"{d}: A={pa}, K={pk} — Polarität falsch!")
if esd_errs == 0:
    ok(f"Alle {len(all_esd)} ESD-Dioden D2–D25: A(Pin1)=GND✓, K(Pin2)=Signalnetz✓")

# Pro Kanal: alle 4 Signale geschützt
for ch in range(1, 7):
    needed = {
        f"/CH{ch}_HOT_RAW",
        f"/CH{ch}_COLD_RAW",
        f"/CH{ch}_OUT_HOT",
        f"/CH{ch}_OUT_COLD",
    }
    covered = {pin(d, "2") for d in all_esd if pin(d, "2") in needed}
    miss = needed - covered
    if not miss:
        ok(f"CH{ch}: alle 4 Signale ESD-geschützt ✓")
    else:
        fail(f"CH{ch}: kein ESD-Schutz für {[n.split('_',1)[1] for n in miss]}")

# ────────────────────────────────────────────────────────────────────────────
print("\n━━━━ ZUSAMMENFASSUNG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
total = PASS + FAIL + WARN
print(
    f"\n  {total} Prüfungen  |  ✅ {PASS} OK  |  ❌ {FAIL} Fehler  |  ⚠️  {WARN} Warnungen"
)

if FAIL == 0 and WARN == 0:
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║  ✅ ALLE PRÜFUNGEN BESTANDEN          ║")
    print("  ╚══════════════════════════════════════╝")
elif FAIL == 0:
    print(f"\n  ⚠️  Keine Fehler, aber {WARN} Warnung(en)")
else:
    print(f"\n  ❌ {FAIL} Fehler gefunden!")
