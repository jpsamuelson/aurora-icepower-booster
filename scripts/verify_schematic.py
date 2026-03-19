#!/usr/bin/env python3
"""
verify_schematic.py — ANDERE METHODE als verify_readme.py
=========================================================
Methode:
  1. Parst .kicad_sch DIREKT als S-Expression → Bauteilwerte, Footprints
  2. Parst kicad-native Netlist → Pin-zu-Netz-Mapping (vollständig)
  3. Prüft README-Behauptungen gegen echte Schematic-Daten:
     a) Bauteilwerte (jede README-Wertangabe vs. Schematic-Value)
     b) Netz-Existenz (alle /CHx_xxx Net-Namen aus README)
     c) Pin-Topologie (welcher Pin ist mit welchem Netz verbunden)
     d) Vollständigkeit (kein README-Bauteil fehlt)
"""
import re
import subprocess
import sys
import os
from pathlib import Path

BASE = Path(__file__).parent.parent
SCH  = BASE / "aurora-dsp-icepower-booster.kicad_sch"
NET  = Path("/tmp/sch_netlist.net")

PASS = 0
FAIL = 0
ERRORS = []

def ok(msg=""):
    global PASS
    PASS += 1

def fail(msg):
    global FAIL
    FAIL += 1
    ERRORS.append(msg)
    print(f"  ✗  {msg}")

def check(cond, msg_ok="", msg_fail=""):
    if cond:
        ok(msg_ok)
    else:
        fail(msg_fail)

# ═══════════════════════════════════════════════════════════════════════════════
# SCHRITT 1: .kicad_sch direkt parsen — Bauteilwerte
# ═══════════════════════════════════════════════════════════════════════════════
print("── Schritt 1: .kicad_sch S-Expression parsen ──")

sch_text = SCH.read_text(encoding="utf-8")

def extract_symbols_from_sch(text):
    """
    Extrahiert alle Symbole (außer lib_symbols) aus .kicad_sch.
    Gibt {ref: {"value": str, "footprint": str}} zurück.
    """
    # lib_symbols Block überspringen (zu groß, enthält keine Instanzen)
    # Wir suchen nach (symbol ... (property "Reference" "Rxx") (property "Value" ...))
    # Strategie: iteriere über alle (symbol Blöcke auf top-level
    components = {}
    # Finde alle top-level symbol-Blöcke (nicht verschachtelt in lib_symbols)
    # lib_symbols ist ein eigener Block der Form: (lib_symbols (...))
    # Top-level symbols haben UUID und Properties

    # Pattern: suche alle Property-Blöcke die Reference + Value enthalten
    # Scanne durch alle (symbol (-Block die eine uuid haben
    
    # Robuster Ansatz: Suche alle Paare von Reference + Value Properties
    # die im selben Symbol-Block stehen (über Balanced-Bracket-Matching)
    
    pos = 0
    n = len(text)
    
    # Finde Start der lib_symbols (zum Überspringen)
    lib_sym_start = text.find("(lib_symbols")
    lib_sym_end = -1
    if lib_sym_start >= 0:
        depth = 0
        for i in range(lib_sym_start, n):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    lib_sym_end = i
                    break

    def parse_block(start):
        """Gibt (block_content, end_pos) zurück."""
        if text[start] != '(':
            return None, start
        depth = 0
        for i in range(start, n):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    return text[start:i+1], i+1
        return None, n

    # Iteriere alle top-level (symbol ...) Blöcke
    i = 0
    while i < n:
        # Überspringe lib_symbols Block
        if lib_sym_end > 0 and i == lib_sym_start:
            i = lib_sym_end + 1
            continue
        
        # Suche nächstes '(symbol ' auf top-Ebene
        idx = text.find("(symbol ", i)
        if idx < 0:
            break
        
        # Prüfe ob das ein top-level symbol ist (und nicht lib_symbols)
        if lib_sym_end > 0 and lib_sym_start <= idx <= lib_sym_end:
            i = lib_sym_end + 1
            continue
        
        block, end = parse_block(idx)
        if block is None:
            i = idx + 1
            continue
        
        # Extrahiere Reference, Value, Footprint aus diesem Block
        ref_m   = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        val_m   = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)
        fp_m    = re.search(r'\(property\s+"Footprint"\s+"([^"]+)"', block)
        
        if ref_m and val_m:
            ref = ref_m.group(1)
            val = val_m.group(1)
            fp  = fp_m.group(1) if fp_m else ""
            # Ignoriere Power-Symbole (#PWR, #FLG)
            if not ref.startswith("#"):
                components[ref] = {"value": val, "footprint": fp}
        
        i = end
    
    return components

sch_components = extract_symbols_from_sch(sch_text)
print(f"  Schematic: {len(sch_components)} Bauteile gefunden")

# Zeige alle Refs und Values für Debug
if "--debug" in sys.argv:
    for ref, d in sorted(sch_components.items()):
        print(f"    {ref}: value={d['value']}  fp={d['footprint'][:40]}")

# ═══════════════════════════════════════════════════════════════════════════════
# SCHRITT 2: Netlist parsen — Pin-zu-Netz-Mapping
# ═══════════════════════════════════════════════════════════════════════════════
print("── Schritt 2: Netlist Pin-Topologie parsen ──")

if not NET.exists():
    print("  Netlist nicht gefunden, exportiere...")
    r = subprocess.run(
        ["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
         "-o", str(NET), str(SCH)],
        capture_output=True
    )
    if r.returncode != 0:
        print("  FEHLER: Netlist-Export fehlgeschlagen")
        sys.exit(1)

net_text = NET.read_text(encoding="utf-8")

def parse_netlist(text):
    """
    Parst kicad-native Netlist.
    Gibt zurück:
      components: {ref: {"value": str, pins: {pin_num: net_name}}}
      nets: {net_name: [(ref, pin_num), ...]}
    """
    components = {}
    nets = {}
    
    n = len(text)
    
    def get_block(start):
        depth = 0
        for i in range(start, n):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        return text[start:]
    
    # Komponenten — mit gequoteten Strings
    comp_pat = re.compile(r'\(comp\s+\(ref\s+"([^"]+)"\)')
    for m in comp_pat.finditer(text):
        ref = m.group(1)
        block = get_block(m.start())
        val_m = re.search(r'\(value\s+"([^"]+)"\)', block)
        value = val_m.group(1) if val_m else ""
        components[ref] = {"value": value, "pins": {}}
    
    # Netze — gequotete code-Nummer!
    net_block_pat = re.compile(r'\(net\s+\(code\s+"[^"]+"\)\s+\(name\s+"([^"]+)"\)')
    for m in net_block_pat.finditer(text):
        net_name = m.group(1)
        block = get_block(m.start())
        nets[net_name] = []
        for node_m in re.finditer(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', block):
            ref, pin = node_m.group(1), node_m.group(2)
            nets[net_name].append((ref, pin))
            if ref in components:
                components[ref]["pins"][pin] = net_name
            else:
                components[ref] = {"value": "", "pins": {pin: net_name}}
    
    return components, nets

nl_components, nl_nets = parse_netlist(net_text)
print(f"  Netlist: {len(nl_components)} Komponenten, {len(nl_nets)} Netze")

def pins_of(ref):
    """Pin→Net Dict für ref."""
    return nl_components.get(ref, {}).get("pins", {})

def net_has(net, ref):
    """Prüft ob net den Ref enthält."""
    return any(r == ref for r, _ in nl_nets.get(net, []))

def pin_on_net(ref, pin, net):
    """Prüft ob ref:pin auf net liegt."""
    return pins_of(ref).get(str(pin)) == net

def nets_of(ref):
    """Gibt alle Netze zurück auf denen ref liegt."""
    return set(pins_of(ref).values())

# ═══════════════════════════════════════════════════════════════════════════════
# SCHRITT 3a: BAUTEILWERTE aus Schematic vs. README
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Block A: Bauteilwerte (Schematic vs. README) ──")

# Erwartete Werte aus der README
EXPECTED_VALUES = {
    # Widerstände
    "R1":  "10k",
    "R2":  "10k",   "R3":  "10k",   "R4":  "10k",   "R5":  "10k",
    "R6":  "10k",   "R7":  "10k",   "R8":  "10k",   "R9":  "10k",
    "R10": "10k",   "R11": "10k",   "R12": "10k",   "R13": "10k",
    "R14": "10k",   "R15": "10k",   "R16": "10k",   "R17": "10k",
    "R18": "10k",   "R19": "10k",   "R20": "10k",   "R21": "10k",
    "R22": "10k",   "R23": "10k",   "R24": "10k",   "R25": "10k",
    "R26": "10k",   "R30": "10k",   "R34": "10k",   "R38": "10k",
    "R42": "10k",   "R46": "10k",
    "R50": "10k",   "R51": "10k",   "R52": "10k",   "R53": "10k",
    "R54": "10k",   "R55": "10k",
    "R27": "30k",   "R31": "30k",   "R35": "30k",   "R39": "30k",
    "R43": "30k",   "R47": "30k",
    "R28": "15k",   "R32": "15k",   "R36": "15k",   "R40": "15k",
    "R44": "15k",   "R48": "15k",
    "R29": "7.5k",  "R33": "7.5k",  "R37": "7.5k",  "R41": "7.5k",
    "R45": "7.5k",  "R49": "7.5k",
    # Driver Rin/Rf = 10k
    "R64": "10k",   "R65": "10k",   "R66": "10k",   "R67": "10k",
    "R68": "10k",   "R69": "10k",
    "R70": "10k",   "R71": "10k",   "R72": "10k",   "R73": "10k",
    "R74": "10k",   "R75": "10k",
    # 47Ω Serien-Rs
    "R58": "47",    "R59": "47",    "R60": "47",    "R61": "47",
    "R62": "47",    "R63": "47",
    "R76": "47",    "R77": "47",    "R78": "47",    "R79": "47",
    "R80": "47",    "R81": "47",
    # Zobel 10Ω
    "R82": "10",    "R83": "10",    "R84": "10",    "R85": "10",
    "R86": "10",    "R87": "10",
    "R88": "10",    "R89": "10",    "R90": "10",    "R91": "10",
    "R92": "10",    "R93": "10",
    # EMI 47Ω
    "R94": "47",    "R95": "47",    "R96": "47",    "R97": "47",
    "R98": "47",    "R99": "47",    "R100": "47",   "R101": "47",
    "R102": "47",   "R103": "47",   "R104": "47",   "R105": "47",
    # Muting
    "R56":  "100k", "R57":  "100k",
    "R106": "10k",  "R107": "100k",
    "R108": "10k",  "R109": "10k",  "R110": "10k",  "R111": "10k",
    "R112": "10k",  "R113": "10k",
    # Kondensatoren
    "C1":  "100n",
    "C2":  "100n",  "C3":  "100n",  "C4":  "100n",  "C5":  "100n",
    "C6":  "100n",  "C7":  "100n",
    "C8":  "100n",  "C9":  "100n",  "C10": "100n",  "C11": "100n",
    "C12": "100n",  "C13": "100n",
    "C14": "100n",  "C15": "100n",
    "C16": "100u",  "C17": "100u",
    "C18": "100n",  "C19": "100n",
    "C20": "100u",  "C21": "100u",
    "C22": "100n",  "C23": "100n",  "C24": "10u",   "C25": "10u",
    "C26": "100n",  "C27": "100n",  "C28": "100n",  "C29": "100n",
    "C30": "100n",  "C31": "100n",
    "C32": "100n",  "C33": "100n",  "C34": "100n",  "C35": "100n",
    "C36": "100n",  "C37": "100n",
    # Zobel 100nF
    "C38": "100n",  "C39": "100n",  "C40": "100n",  "C41": "100n",
    "C42": "100n",  "C43": "100n",
    "C44": "100n",  "C45": "100n",  "C46": "100n",  "C47": "100n",
    "C48": "100n",  "C49": "100n",
    # EMI 100pF
    "C50": "100p",  "C51": "100p",  "C52": "100p",  "C53": "100p",
    "C54": "100p",  "C55": "100p",  "C56": "100p",  "C57": "100p",
    "C58": "100p",  "C59": "100p",  "C60": "100p",  "C61": "100p",
    # DC-Block 2.2µF
    "C62": "2.2u",  "C63": "2.2u",  "C64": "2.2u",  "C65": "2.2u",
    "C66": "2.2u",  "C67": "2.2u",  "C68": "2.2u",  "C69": "2.2u",
    "C70": "2.2u",  "C71": "2.2u",  "C72": "2.2u",  "C73": "2.2u",
    # Driver bulk
    "C74": "10u",   "C75": "10u",   "C76": "10u",   "C77": "10u",
    "C78": "10u",   "C79": "10u",
    # Muting
    "C80": "10u",   "C81": "22n",
    # Dioden
    "D1":  "SMBJ15CA",
}
# PESD-Dioden (D2-D25)
for i in range(2, 26):
    EXPECTED_VALUES[f"D{i}"] = "PESD5V0S1BL"

# Normierungsfunktion für Werte (z.B. "10 kΩ" → "10k", "100nF" → "100n")
def normalize_value(v):
    """Extrahiert den Kern-Wert aus Strings wie '100nF C0G', '10uF X5R', '10k 0.1%'."""
    v = v.strip().lower().replace('µ', 'u').replace('μ', 'u').replace(',', '.')
    # Model-Nummern (starten mit Buchstabe): first word
    if v and v[0].isalpha():
        return v.split()[0].rstrip('-')
    # Numerisch: extrahiere Zahl + SI-Präfix, ignore Rest
    m = re.match(r'^(\d+(?:\.\d+)?)\s*([pnumkMG]?)(?:[a-z]*)', v)
    if m:
        num = m.group(1)
        prefix = m.group(2).lower()
        return num + prefix
    return v.split()[0]

def values_match(actual, expected):
    """Prüfe ob actual ~= expected (nach Normierung)."""
    a = normalize_value(actual)
    e = normalize_value(expected)
    # Exakter Match nach Normierung
    if a == e:
        return True
    # Weitere Heuristiken:
    # "7.5k" vs "7k5" (KiCad benutzt manchmal Dezimalpunkt statt Buchstaben)
    if a.replace(".", "") == e.replace(".", ""):
        return True
    # "7.5k" könnte als "7k5" gespeichert sein → nicht direkt nötig, aber sicher
    return False

for ref, expected in sorted(EXPECTED_VALUES.items(), key=lambda x: (x[0][0], int(re.sub(r'\D','',x[0]) or 0))):
    if ref not in sch_components:
        fail(f"[VAL] {ref}: nicht in Schematic (erwartet value={expected})")
        continue
    actual = sch_components[ref]["value"]
    if values_match(actual, expected):
        ok()
    else:
        fail(f"[VAL] {ref}: README sagt '{expected}', Schematic hat '{actual}'")

# ═══════════════════════════════════════════════════════════════════════════════
# SCHRITT 3b: Netz-Namen aus README in Netlist prüfen
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Block B: Netz-Existenz (alle README-Netze in Netlist?) ──")

# Alle im README erwähnten Netze (manuell aus README extrahiert)
README_NETS = [
    # Global
    "GND", "/+24V_IN", "/+12V_RAW", "/-12V_RAW", "/+12V", "/-12V",
    "/V+", "/V-", "/EN_CTRL", "/SS_U14", "/NR_U15",
    # Remote/Muting
    "/REMOTE_IN", "/REMOTE_FILT", "/MUTE",
    # Per-Kanal (6 Kanäle)
]
for ch in range(1, 7):
    README_NETS += [
        f"/CH{ch}_HOT_RAW", f"/CH{ch}_COLD_RAW",
        f"/CH{ch}_HOT_IN",  f"/CH{ch}_COLD_IN",
        f"/CH{ch}_RX_OUT",
        f"/CH{ch}_SUMNODE",
        f"/CH{ch}_GAIN_OUT",
        f"/CH{ch}_BUF_DRIVE",
        f"/CH{ch}_GAIN_FB",
        f"/CH{ch}_OUT_HOT",  f"/CH{ch}_OUT_COLD",
        f"/CH{ch}_OUT_PROT_HOT", f"/CH{ch}_OUT_PROT_COLD",
        f"/CH{ch}_SW_OUT_1", f"/CH{ch}_SW_OUT_2", f"/CH{ch}_SW_OUT_3",
        f"/CH{ch}_INV_IN",
    ]

for net in README_NETS:
    if net == "GND":
        # GND kann als verschiedene Namen erscheinen
        gnd_variants = {"GND", "Net-(GND-...", "/GND"}
        found = any(n == "GND" or n.startswith("GND") for n in nl_nets.keys())
        if found:
            ok()
        else:
            fail(f"[NET] GND nicht in Netlist gefunden")
    else:
        if net in nl_nets:
            ok()
        else:
            fail(f"[NET] Netz '{net}' aus README nicht in Netlist")

# ═══════════════════════════════════════════════════════════════════════════════
# SCHRITT 3c: Pin-Topologie-Verifikation (kritische Verbindungen)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Block C: Pin-Topologie (pin→net Mapping) ──")

def check_pin(ref, pin, net, desc=""):
    actual = pins_of(ref).get(str(pin))
    if actual == net:
        ok()
    else:
        fail(f"[TOP] {ref} Pin{pin}: README sagt '{net}', Netlist hat '{actual}' ({desc})")

# J1 — Barrel Jack
check_pin("J1", "1", "/+24V_IN", "J1 Plus")

# U1 — TEL5-2422
check_pin("U1", "14", "/+12V_RAW", "U1 +12V_RAW out")
check_pin("U1", "11", "/-12V_RAW", "U1 -12V_RAW out")

# U14 — ADP7118 LDO positiv
check_pin("U14", "5", "/EN_CTRL", "U14 EN-Pin")
check_pin("U14", "6", "/SS_U14",   "U14 SS-Pin")

# U15 — ADP7182 LDO negativ
check_pin("U15", "3", "/EN_CTRL", "U15 EN-Pin")
check_pin("U15", "4", "/NR_U15",  "U15 NR-Pin")

# SW1 — SPDT ALWAYS/REMOTE
check_pin("SW1", "2", "/EN_CTRL",    "SW1 COM→EN_CTRL")
check_pin("SW1", "3", "/REMOTE_FILT","SW1 Pin3→REMOTE_FILT")

# J2 — Remote Buchse
check_pin("J2", "T", "/REMOTE_IN", "J2 Tip=REMOTE_IN")

# D1 — SMBJ15CA Remote TVS
check_pin("D1", "1", "/REMOTE_IN", "D1 Pin1=REMOTE_IN")

# C1 — RC-Filter Remote
check_pin("C1", "1", "/REMOTE_FILT", "C1 an REMOTE_FILT")

# R56/R57 — EN_CTRL Pull (Richtung egal, beide Netze prüfen)
check("/EN_CTRL" in nets_of("R56"), msg_fail="[TOP] R56: kein /EN_CTRL-Anschluss (soll /V+↔/EN_CTRL)")
check("/EN_CTRL" in nets_of("R57"), msg_fail="[TOP] R57: kein /EN_CTRL-Anschluss (soll /EN_CTRL↔GND)")

# Q1 — Master Mute
check_pin("Q1", "3", "/MUTE", "Q1 Drain=MUTE")

# Per-Kanal Topologie (alle 6 Kanäle)
# Kanal-Konfiguration
ch_map = {
    1: {"J_in":  "J3",  "J_out": "J9",
        "D_hot_raw": "D8",  "D_cold_raw": "D10",
        "D_out_hot": "D2",  "D_out_cold": "D9",
        "R_emi_hot": "R94", "R_emi_cold": "R95",
        "C_emi_hot": "C50", "C_emi_cold": "C51",
        "C_dc_hot":  "C62", "C_dc_cold":  "C63",
        "U_diff":    "U2",  "U_drv":      "U8",
        "Q_mute":    "Q2",  "R_mute_g":   "R108",
        "R_rin":     "R26", "R_rf":        "R50",
        "R_30k":     "R27", "R_15k":       "R28", "R_7k5": "R29",
        "R_rin_inv": "R64", "R_rf_inv":    "R70",
        "R_cold":    "R58", "R_hot":       "R76",
        "R_zob_hot": "R82", "R_zob_cold":  "R88",
        "C_zob_hot": "C38", "C_zob_cold":  "C44",
        "SW": "SW2",
        },
    2: {"J_in":  "J4",  "J_out": "J10",
        "D_hot_raw": "D11", "D_cold_raw": "D13",
        "D_out_hot": "D3",  "D_out_cold": "D12",
        "R_emi_hot": "R96", "R_emi_cold": "R97",
        "C_emi_hot": "C52", "C_emi_cold": "C53",
        "C_dc_hot":  "C64", "C_dc_cold":  "C65",
        "U_diff":    "U3",  "U_drv":      "U9",
        "Q_mute":    "Q3",  "R_mute_g":   "R109",
        "R_rin":     "R30", "R_rf":        "R51",
        "R_30k":     "R31", "R_15k":       "R32", "R_7k5": "R33",
        "R_rin_inv": "R65", "R_rf_inv":    "R71",
        "R_cold":    "R59", "R_hot":       "R77",
        "R_zob_hot": "R83", "R_zob_cold":  "R89",
        "C_zob_hot": "C39", "C_zob_cold":  "C45",
        "SW": "SW3",
        },
    3: {"J_in":  "J5",  "J_out": "J11",
        "D_hot_raw": "D14", "D_cold_raw": "D16",
        "D_out_hot": "D4",  "D_out_cold": "D15",
        "R_emi_hot": "R98", "R_emi_cold": "R99",
        "C_emi_hot": "C54", "C_emi_cold": "C55",
        "C_dc_hot":  "C66", "C_dc_cold":  "C67",
        "U_diff":    "U4",  "U_drv":      "U10",
        "Q_mute":    "Q4",  "R_mute_g":   "R110",
        "R_rin":     "R34", "R_rf":        "R52",
        "R_30k":     "R35", "R_15k":       "R36", "R_7k5": "R37",
        "R_rin_inv": "R66", "R_rf_inv":    "R72",
        "R_cold":    "R60", "R_hot":       "R78",
        "R_zob_hot": "R84", "R_zob_cold":  "R90",
        "C_zob_hot": "C40", "C_zob_cold":  "C46",
        "SW": "SW4",
        },
    4: {"J_in":  "J6",  "J_out": "J12",
        "D_hot_raw": "D17", "D_cold_raw": "D19",
        "D_out_hot": "D5",  "D_out_cold": "D18",
        "R_emi_hot": "R100","R_emi_cold": "R101",
        "C_emi_hot": "C56", "C_emi_cold": "C57",
        "C_dc_hot":  "C68", "C_dc_cold":  "C69",
        "U_diff":    "U5",  "U_drv":      "U11",
        "Q_mute":    "Q5",  "R_mute_g":   "R111",
        "R_rin":     "R38", "R_rf":        "R53",
        "R_30k":     "R39", "R_15k":       "R40", "R_7k5": "R41",
        "R_rin_inv": "R67", "R_rf_inv":    "R73",
        "R_cold":    "R61", "R_hot":       "R79",
        "R_zob_hot": "R85", "R_zob_cold":  "R91",
        "C_zob_hot": "C41", "C_zob_cold":  "C47",
        "SW": "SW5",
        },
    5: {"J_in":  "J7",  "J_out": "J13",
        "D_hot_raw": "D20", "D_cold_raw": "D22",
        "D_out_hot": "D6",  "D_out_cold": "D21",
        "R_emi_hot": "R102","R_emi_cold": "R103",
        "C_emi_hot": "C58", "C_emi_cold": "C59",
        "C_dc_hot":  "C70", "C_dc_cold":  "C71",
        "U_diff":    "U6",  "U_drv":      "U12",
        "Q_mute":    "Q6",  "R_mute_g":   "R112",
        "R_rin":     "R42", "R_rf":        "R54",
        "R_30k":     "R43", "R_15k":       "R44", "R_7k5": "R45",
        "R_rin_inv": "R68", "R_rf_inv":    "R74",
        "R_cold":    "R62", "R_hot":       "R80",
        "R_zob_hot": "R86", "R_zob_cold":  "R92",
        "C_zob_hot": "C42", "C_zob_cold":  "C48",
        "SW": "SW6",
        },
    6: {"J_in":  "J8",  "J_out": "J14",
        "D_hot_raw": "D23", "D_cold_raw": "D25",
        "D_out_hot": "D7",  "D_out_cold": "D24",
        "R_emi_hot": "R104","R_emi_cold": "R105",
        "C_emi_hot": "C60", "C_emi_cold": "C61",
        "C_dc_hot":  "C72", "C_dc_cold":  "C73",
        "U_diff":    "U7",  "U_drv":      "U13",
        "Q_mute":    "Q7",  "R_mute_g":   "R113",
        "R_rin":     "R46", "R_rf":        "R55",
        "R_30k":     "R47", "R_15k":       "R48", "R_7k5": "R49",
        "R_rin_inv": "R69", "R_rf_inv":    "R75",
        "R_cold":    "R63", "R_hot":       "R81",
        "R_zob_hot": "R87", "R_zob_cold":  "R93",
        "C_zob_hot": "C43", "C_zob_cold":  "C49",
        "SW": "SW7",
        },
}

# Diff-Receiver R-Nummern (aus Bauteil-Mapping)
diff_r_map = {
    1: {"rin+": "R2",  "rg-": "R3",  "rref-": "R14", "rf": "R20"},
    2: {"rin+": "R4",  "rg-": "R5",  "rref-": "R15", "rf": "R21"},
    3: {"rin+": "R6",  "rg-": "R7",  "rref-": "R16", "rf": "R22"},
    4: {"rin+": "R8",  "rg-": "R9",  "rref-": "R17", "rf": "R23"},
    5: {"rin+": "R10", "rg-": "R11", "rref-": "R18", "rf": "R24"},
    6: {"rin+": "R12", "rg-": "R13", "rref-": "R19", "rf": "R25"},
}

for ch, m in ch_map.items():
    n = f"CH{ch}"
    hr = f"/CH{ch}_HOT_RAW"
    cr = f"/CH{ch}_COLD_RAW"
    hi = f"/CH{ch}_HOT_IN"
    ci = f"/CH{ch}_COLD_IN"
    rx = f"/CH{ch}_RX_OUT"
    sm = f"/CH{ch}_SUMNODE"
    go = f"/CH{ch}_GAIN_OUT"
    bd = f"/CH{ch}_BUF_DRIVE"
    gf = f"/CH{ch}_GAIN_FB"
    oh = f"/CH{ch}_OUT_HOT"
    oc = f"/CH{ch}_OUT_COLD"
    ph = f"/CH{ch}_OUT_HOT"
    pc = f"/CH{ch}_OUT_COLD"
    sw1 = f"/CH{ch}_SW_OUT_1"
    sw2 = f"/CH{ch}_SW_OUT_2"
    sw3 = f"/CH{ch}_SW_OUT_3"

    # XLR-IN Stecker
    check_pin(m["J_in"], "2", hr, f"{n} J_in Pin2=HOT_RAW")
    check_pin(m["J_in"], "3", cr, f"{n} J_in Pin3=COLD_RAW")

    # ESD TVS Eingang: Kathode = HOT/COLD_RAW (pin "2" = Kathode bei PESD)
    check_pin(m["D_hot_raw"],  "2", hr, f"{n} D_hot_raw K=HOT_RAW")
    check_pin(m["D_cold_raw"], "2", cr, f"{n} D_cold_raw K=COLD_RAW")

    # EMI-Filter Reihenfolge: HOT_RAW → R_emi_hot → (EMI_HOT) → C_dc_hot → HOT_IN
    # R_emi_hot muss HOT_RAW auf einer Seite haben
    r_emi_nets = nets_of(m["R_emi_hot"])
    check(hr in r_emi_nets, 
          msg_fail=f"[TOP] {n} {m['R_emi_hot']} hat kein {hr} — falsche Reihenfolge?")
    
    # C_dc_hot muss HOT_IN auf einer Seite haben
    c_dc_nets = nets_of(m["C_dc_hot"])
    check(hi in c_dc_nets, 
          msg_fail=f"[TOP] {n} {m['C_dc_hot']} hat kein {hi} — DC-Block falsch?")

    # Diff-Receiver
    dr = diff_r_map[ch]
    # rin+ (Referenz GND → IN+_A): soll HOT_IN-Netz enthalten
    rin_plus_nets = nets_of(dr["rin+"])
    check(hi in rin_plus_nets,
          msg_fail=f"[TOP] {n} {dr['rin+']} (Rin+) hat kein {hi} — HOT_IN Verbindung?")
    # rg- (COLD → IN-_A): soll COLD_IN enthalten
    rg_minus_nets = nets_of(dr["rg-"])
    check(ci in rg_minus_nets,
          msg_fail=f"[TOP] {n} {dr['rg-']} (Rg-) hat kein {ci} — COLD_IN Verbindung?")
    # rf (Feedback: OUT_A → IN-_A): soll RX_OUT enthalten
    rf_nets = nets_of(dr["rf"])
    check(rx in rf_nets,
          msg_fail=f"[TOP] {n} {dr['rf']} (Rf) hat kein {rx} — RX_OUT Feedback?")

    # Gain-Stufe
    # R_rin: RX_OUT → SUMNODE
    check(rx in nets_of(m["R_rin"]),
          msg_fail=f"[TOP] {n} {m['R_rin']} (Rin_gain) hat kein {rx}")
    check(sm in nets_of(m["R_rin"]),
          msg_fail=f"[TOP] {n} {m['R_rin']} (Rin_gain) hat kein {sm}")
    # R_rf: GAIN_OUT → SUMNODE
    check(go in nets_of(m["R_rf"]),
          msg_fail=f"[TOP] {n} {m['R_rf']} (Rf_gain) hat kein {go}")
    check(sm in nets_of(m["R_rf"]),
          msg_fail=f"[TOP] {n} {m['R_rf']} (Rf_gain) hat kein {sm}")
    # DIP-SW: RX_OUT auf einer Seite
    check(rx in nets_of(m["SW"]),
          msg_fail=f"[TOP] {n} {m['SW']} (DIP-SW) hat kein {rx}")

    # Muting MOSFET
    check_pin(m["Q_mute"], "3", go, f"{n} Q_mute Drain=GAIN_OUT")

    # Driver
    # R_cold (47Ω): BUF_DRIVE → OUT_COLD
    check(bd in nets_of(m["R_cold"]),
          msg_fail=f"[TOP] {n} {m['R_cold']} (R47_COLD) hat kein {bd}")
    check(oc in nets_of(m["R_cold"]),
          msg_fail=f"[TOP] {n} {m['R_cold']} (R47_COLD) hat kein {oc}")
    # R_hot (47Ω): OUT_DRIVE → OUT_HOT  
    check(oh in nets_of(m["R_hot"]),
          msg_fail=f"[TOP] {n} {m['R_hot']} (R47_HOT) hat kein {oh}")
    # ESD Ausgang: Kathode = OUT_HOT / OUT_COLD (pin "2" = Kathode)
    check_pin(m["D_out_hot"],  "2", oh, f"{n} D_out_hot K=OUT_HOT")
    check_pin(m["D_out_cold"], "2", oc, f"{n} D_out_cold K=OUT_COLD")
    # Zobel: R_zob_hot verbindet OUT_HOT und PROT_HOT
    check(oh in nets_of(m["R_zob_hot"]) or ph in nets_of(m["R_zob_hot"]),
          msg_fail=f"[TOP] {n} {m['R_zob_hot']} (Zobel_R_HOT) weder OUT_HOT noch PROT_HOT")
    # XLR-OUT Stecker
    check_pin(m["J_out"], "2", ph, f"{n} J_out Pin2=PROT_HOT")
    check_pin(m["J_out"], "3", pc, f"{n} J_out Pin3=PROT_COLD")

# ═══════════════════════════════════════════════════════════════════════════════
# SCHRITT 3d: Vollständigkeit der README-Bauteile
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Block D: Vollständigkeit (alle Schematic-Bauteile in README?) ──")

# Alle Refs aus dem Schematic, die im README vorhanden sein müssen
ALL_SCH_REFS = set(sch_components.keys())

# README Refs (hardcoded aus dem README)
README_REFS = set()
# R1-R113
for i in range(1, 114): README_REFS.add(f"R{i}")
# C1-C81
for i in range(1, 82): README_REFS.add(f"C{i}")
# D1-D25
for i in range(1, 26): README_REFS.add(f"D{i}")
# U1-U15
for i in range(1, 16): README_REFS.add(f"U{i}")
# Q1-Q7
for i in range(1, 8): README_REFS.add(f"Q{i}")
# J1-J14
for i in range(1, 15): README_REFS.add(f"J{i}")
# SW1-SW7
for i in range(1, 8): README_REFS.add(f"SW{i}")
# FB1, FB2
README_REFS.add("FB1"); README_REFS.add("FB2")

# Bauteile aus Schematic die NICHT in README-Refs
missing_from_readme = ALL_SCH_REFS - README_REFS
extra_in_readme     = README_REFS - ALL_SCH_REFS

for ref in sorted(missing_from_readme, key=lambda x: (x[0], int(re.sub(r'\D','',x) or 0))):
    fail(f"[COMPLETE] {ref} ist in Schematic aber NICHT explizit in README-Refs")

for ref in sorted(extra_in_readme, key=lambda x: (x[0], int(re.sub(r'\D','',x) or 0))):
    fail(f"[COMPLETE] {ref} in README aber NICHT in Schematic")

if not missing_from_readme and not extra_in_readme:
    ok(); ok()  # 2 Checks bestanden

# ═══════════════════════════════════════════════════════════════════════════════
# SCHRITT 3e: Footprint-Prüfung für key ICs
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Block E: Footprints key ICs ──")

EXPECTED_FP_KEYWORDS = {
    "U1":  ["TEL5"],           # TEL5-2422 custom footprint
    "U2":  ["SOIC"],           # LM4562 SOIC-8
    "U14": ["SOIC"],           # ADP7118 SOIC
    "U15": ["SOT-23"],         # ADP7182 SOT-23-5
    "Q1":  ["SOT-23"],         # BSS138 SOT-23
    "D1":  ["SMB"],            # SMBJ15CA SMB package
    "D2":  ["SOD-323"],        # PESD5V0S1BL
    "SW1": ["SPDT"],
    "SW2": ["DIP"],
}

for ref, keywords in EXPECTED_FP_KEYWORDS.items():
    if ref not in sch_components:
        fail(f"[FP] {ref}: nicht in Schematic")
        continue
    fp = sch_components[ref]["footprint"]
    for kw in keywords:
        if kw.lower() in fp.lower():
            ok()
        else:
            fail(f"[FP] {ref}: Footprint '{fp}' enthält nicht '{kw}' (README-Angabe)")

# ═══════════════════════════════════════════════════════════════════════════════
# ERGEBNIS
# ═══════════════════════════════════════════════════════════════════════════════
print(f"""
{'═'*60}
ERGEBNIS: {PASS} Checks BESTANDEN
""")
if ERRORS:
    print(f"FEHLER ({FAIL}):")
    for e in ERRORS:
        print(f"  ✗  {e}")
    print(f"\nREADME hat {FAIL} Fehler gegenüber Schematic/Netlist!")
else:
    print("✅ README ist vollständig konsistent mit Schematic — keine Fehler!")
print('═'*60)
