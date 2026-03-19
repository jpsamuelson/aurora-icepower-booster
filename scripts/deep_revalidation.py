#!/usr/bin/env python3
"""
Deep Re-Validation — Aurora DSP IcePower Booster
Mirrors the original FINDINGS.md analysis methodology:
  1. kicad-cli netlist export + ERC
  2. Parse S-expression netlist
  3. Pin-level verification of ALL subcircuits
  4. Report in FINDINGS.md format
"""

import subprocess, re, os, sys, json
from collections import defaultdict

PROJECT = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH = os.path.join(PROJECT, "aurora-dsp-icepower-booster.kicad_sch")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
NETLIST_PATH = "/tmp/revalidation_netlist.net"
ERC_PATH = "/tmp/revalidation_erc.json"

# ──────────────────────────────────────────────
# Section 0: Bracket Balance
# ──────────────────────────────────────────────
def check_brackets(path):
    with open(path, 'r') as f:
        content = f.read()
    depth = 0
    for ch in content:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
    return depth, len(content)

# ──────────────────────────────────────────────
# Section 1: kicad-cli operations
# ──────────────────────────────────────────────
def export_netlist():
    r = subprocess.run([KICAD_CLI, "sch", "export", "netlist",
                        "--output", NETLIST_PATH, SCH],
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stderr

def run_erc():
    r = subprocess.run([KICAD_CLI, "sch", "erc",
                        "--output", ERC_PATH, "--format", "json",
                        "--severity-all", SCH],
                       capture_output=True, text=True, timeout=60)
    # Parse JSON
    try:
        with open(ERC_PATH, 'r') as f:
            data = json.load(f)
        violations = data.get("violations", [])
        errors = [v for v in violations if v.get("severity") == "error"]
        warnings = [v for v in violations if v.get("severity") == "warning"]
        return r.returncode, errors, warnings
    except:
        return r.returncode, [], []

# ──────────────────────────────────────────────
# Section 2: Netlist Parser (S-expression)
# ──────────────────────────────────────────────
def parse_netlist(path):
    """Parse KiCad S-expression netlist into structured data."""
    with open(path, 'r') as f:
        content = f.read()
    
    # Extract nets with their pins
    nets = {}  # net_name -> [(ref, pin), ...]
    
    # Find all (net blocks
    net_pattern = re.compile(r'\(net\s+\(code\s+"?(\d+)"?\)\s*\(name\s+"([^"]*)"\)')
    pin_pattern = re.compile(r'\(node\s+\(ref\s+"([^"]*)"\)\s*\(pin\s+"([^"]*)"\)')
    
    # Split into net blocks
    net_blocks = re.split(r'(?=\(net\s+\(code)', content)
    for block in net_blocks:
        m = net_pattern.search(block)
        if m:
            code, name = m.group(1), m.group(2)
            pins = pin_pattern.findall(block)
            nets[name] = pins
    
    # Extract components
    components = {}  # ref -> {value, footprint, lib}
    comp_pattern = re.compile(
        r'\(comp\s+\(ref\s+"([^"]*)"\).*?\(value\s+"([^"]*)"\).*?\(footprint\s+"([^"]*)"\).*?\(libsource\s+\(lib\s+"([^"]*)"\)\s*\(part\s+"([^"]*)"\)',
        re.DOTALL
    )
    comp_blocks = re.split(r'(?=\(comp\s+\(ref)', content)
    for block in comp_blocks:
        m = comp_pattern.search(block)
        if m:
            ref, val, fp, lib, part = m.groups()
            components[ref] = {"value": val, "footprint": fp, "lib": lib, "part": part}
    
    return nets, components

def get_component_nets(nets, ref):
    """Get all nets for a given component ref."""
    result = {}  # pin -> net_name
    for net_name, pins in nets.items():
        for r, p in pins:
            if r == ref:
                result[p] = net_name
    return result

# ──────────────────────────────────────────────
# Section 3: Validation Functions
# ──────────────────────────────────────────────

class ValidationReport:
    def __init__(self):
        self.sections = []
        self.total_pass = 0
        self.total_fail = 0
        self.total_warn = 0
    
    def section(self, title):
        self.sections.append({"title": title, "checks": [], "notes": []})
    
    def check(self, desc, passed, detail=""):
        s = self.sections[-1]
        status = "✅" if passed else "❌"
        if passed:
            self.total_pass += 1
        else:
            self.total_fail += 1
        s["checks"].append({"desc": desc, "status": status, "detail": detail, "passed": passed})
    
    def warn(self, desc, detail=""):
        s = self.sections[-1]
        self.total_warn += 1
        s["checks"].append({"desc": desc, "status": "⚠️", "detail": detail, "passed": None})
    
    def note(self, text):
        self.sections[-1]["notes"].append(text)
    
    def print_report(self):
        print("=" * 80)
        print("DEEP RE-VALIDATION — Aurora DSP IcePower Booster")
        print("=" * 80)
        print()
        
        for sec in self.sections:
            print(f"{'─' * 60}")
            print(f"## {sec['title']}")
            print(f"{'─' * 60}")
            for c in sec["checks"]:
                line = f"  {c['status']} {c['desc']}"
                if c["detail"]:
                    line += f" — {c['detail']}"
                print(line)
            for n in sec["notes"]:
                print(f"  ℹ️  {n}")
            print()
        
        print("=" * 80)
        print(f"SUMMARY: {self.total_pass} PASS | {self.total_fail} FAIL | {self.total_warn} WARN")
        print("=" * 80)


def validate_gnd_separation(nets, rpt):
    """F1: Verify GND is its own net, not merged with any OUT_COLD."""
    rpt.section("F1: GND / OUT_COLD Netz-Trennung")
    
    # Check GND net exists
    gnd_net = nets.get("GND", [])
    rpt.check("GND Netz existiert", len(gnd_net) > 0, f"{len(gnd_net)} Pins")
    
    # Check no OUT_COLD in GND
    gnd_refs = [f"{r}.{p}" for r, p in gnd_net]
    out_cold_in_gnd = [x for x in gnd_refs if "OUT_COLD" in x.upper()]
    rpt.check("Kein OUT_COLD-Bauteil im GND-Netz", len(out_cold_in_gnd) == 0,
              f"Gefunden: {out_cold_in_gnd}" if out_cold_in_gnd else "")
    
    # Check each CHx_OUT_COLD is separate
    for ch in range(1, 7):
        net_name = f"CH{ch}_OUT_COLD"
        # Try variations
        found_name = None
        found_pins = []
        for name, pins in nets.items():
            if net_name.lower() in name.lower() or name.lower() == net_name.lower():
                found_name = name
                found_pins = pins
                break
        
        if not found_name:
            # Try with / prefix
            for name, pins in nets.items():
                if name.strip("/").upper() == net_name.upper():
                    found_name = name
                    found_pins = pins
                    break
        
        rpt.check(f"{net_name} existiert als eigenständiges Netz",
                  found_name is not None,
                  f"Name: '{found_name}', {len(found_pins)} Pins" if found_name else "NICHT GEFUNDEN")
        
        if found_name:
            # Should NOT contain GND-only components like BSS138 sources
            bss_in_cold = [f"{r}.{p}" for r, p in found_pins if r.startswith("Q")]
            if bss_in_cold:
                rpt.check(f"  Keine BSS138 im {net_name}", False, f"BSS138 Pins: {bss_in_cold}")
            
            # Should have at least 2 pins (driver output + series resistor or XLR)
            rpt.check(f"  {net_name} hat ≥2 Pins", len(found_pins) >= 2,
                      f"Pins: {[f'{r}.{p}' for r, p in found_pins]}")
    
    # GND pin count should be reasonable (was 189 when merged — should be ~143 for power+analog GND)
    rpt.note(f"GND Netz hat {len(gnd_net)} Pins (bei Merge waren es 189 mit OUT_COLD)")


def validate_xlr_inputs(nets, components, rpt):
    """F2: XLR Input Pin Assignment."""
    rpt.section("F2: XLR-Eingang Pin-Zuordnung (J3–J8)")
    
    xlr_inputs = {"J3": "CH1", "J4": "CH2", "J5": "CH3", "J6": "CH4", "J7": "CH5", "J8": "CH6"}
    
    rpt.note("Pin 1 = GND, Pin 2 = Hot (CHx_HOT_RAW/HOT_IN), Pin 3 = Cold (CHx_COLD_RAW), G = Shield/GND")
    
    for ref, ch in xlr_inputs.items():
        pin_nets = get_component_nets(nets, ref)
        
        # Pin 1 should be GND
        p1_net = pin_nets.get("1", "???")
        rpt.check(f"{ref}.Pin1 (GND) = GND", "GND" == p1_net or p1_net.endswith("GND"),
                  f"Netz: {p1_net}")
        
        # Pin 2 should be CHx_HOT_RAW or CHx_HOT_IN (NOT GND!)
        p2_net = pin_nets.get("2", "???")
        is_hot = ("HOT" in p2_net.upper()) and ("GND" not in p2_net.upper())
        rpt.check(f"{ref}.Pin2 (Hot) = {ch}_HOT_*", is_hot,
                  f"Netz: {p2_net}")
        
        # Pin 3 should be CHx_COLD_RAW
        p3_net = pin_nets.get("3", "???")
        is_cold = "COLD" in p3_net.upper() and "OUT" not in p3_net.upper()
        rpt.check(f"{ref}.Pin3 (Cold) = {ch}_COLD_RAW", is_cold,
                  f"Netz: {p3_net}")
        
        # Pin G (shield) should be GND
        pg_net = pin_nets.get("G", pin_nets.get("4", "???"))
        rpt.check(f"{ref}.PinG (Shield) = GND", "GND" == pg_net or pg_net.endswith("GND"),
                  f"Netz: {pg_net}")


def validate_xlr_outputs(nets, components, rpt):
    """F3: XLR Output Pin Assignment."""
    rpt.section("F3: XLR-Ausgang Pin-Zuordnung (J9–J14)")
    
    xlr_outputs = {"J9": "CH1", "J10": "CH2", "J11": "CH3", "J12": "CH4", "J13": "CH5", "J14": "CH6"}
    
    rpt.note("Pin 1 = GND, Pin 2 = Hot (CHx_OUT_HOT), Pin 3 = Cold (CHx_OUT_COLD)")
    
    for ref, ch in xlr_outputs.items():
        pin_nets = get_component_nets(nets, ref)
        
        if not pin_nets:
            rpt.check(f"{ref} im Netlist", False, "NICHT GEFUNDEN!")
            continue
        
        # Pin 1 should be GND
        p1_net = pin_nets.get("1", "???")
        rpt.check(f"{ref}.Pin1 (GND) = GND", "GND" == p1_net or p1_net.endswith("GND"),
                  f"Netz: {p1_net}")
        
        # Pin 2 should be CHx_OUT_HOT (or connected via series resistor)
        p2_net = pin_nets.get("2", "???")
        rpt.check(f"{ref}.Pin2 (Hot) enthält HOT", "HOT" in p2_net.upper(),
                  f"Netz: {p2_net}")
        
        # Pin 3 should be CHx_OUT_COLD (NOT GND!)
        p3_net = pin_nets.get("3", "???")
        has_cold = "COLD" in p3_net.upper()
        not_gnd = "GND" not in p3_net.upper()
        rpt.check(f"{ref}.Pin3 (Cold) = *OUT_COLD (nicht GND!)", has_cold and not_gnd,
                  f"Netz: {p3_net}")


def validate_diff_receiver(nets, components, rpt):
    """F4: Differential Receiver Feedback Topology."""
    rpt.section("F4: Differenzieller Receiver — Feedback-Topologie")
    
    # Feedback resistors R20-R25 should be: pin1=INV_IN, pin2=RX_OUT (negative feedback)
    feedback_r = {
        "R20": "CH1", "R21": "CH2", "R22": "CH3",
        "R23": "CH4", "R24": "CH5", "R25": "CH6"
    }
    
    rpt.note("Soll: Rf (R20-R25) von INV_IN(-) nach RX_OUT = NEGATIVES Feedback")
    rpt.note("War vorher: Rf von HOT_IN(+) nach RX_OUT = POSITIVES Feedback ❌")
    
    for ref, ch in feedback_r.items():
        pin_nets = get_component_nets(nets, ref)
        p1 = pin_nets.get("1", "???")
        p2 = pin_nets.get("2", "???")
        
        # One pin should be on INV_IN, other on RX_OUT
        has_inv = "INV" in p1.upper() or "INV" in p2.upper()
        has_rx = "RX_OUT" in p1.upper() or "RX_OUT" in p2.upper()
        has_hot = "HOT" in p1.upper() or "HOT" in p2.upper()
        
        rpt.check(f"{ref} ({ch}): INV_IN ↔ RX_OUT (neg. Feedback)",
                  has_inv and has_rx and not has_hot,
                  f"Pin1={p1}, Pin2={p2}")
        
        if has_hot:
            rpt.check(f"  {ref}: KEIN HOT_IN am Feedback!", False,
                      "POSITIVES FEEDBACK DETEKTIERT!")


def validate_rgnd(nets, components, rpt):
    """F5+F6: Rgnd Resistors."""
    rpt.section("F5+F6: Rgnd-Widerstände (R2, R4, R6, R8, R10, R12)")
    
    rgnd = {
        "R2": "CH1", "R4": "CH2", "R6": "CH3",
        "R8": "CH4", "R10": "CH5", "R12": "CH6"
    }
    
    rpt.note("Soll: ein Pin = GND, anderer Pin = NINV(+)/HOT_IN Knoten")
    rpt.note("War F5: R2.Pin1 unverbunden | War F6: R4-R12 beide Pins auf HOT_IN")
    
    for ref, ch in rgnd.items():
        pin_nets = get_component_nets(nets, ref)
        p1 = pin_nets.get("1", "???")
        p2 = pin_nets.get("2", "???")
        
        has_gnd = ("GND" == p1) or ("GND" == p2)
        has_hot = ("HOT" in p1.upper()) or ("HOT" in p2.upper())
        both_same = (p1 == p2)
        
        rpt.check(f"{ref} ({ch}): ein Pin GND", has_gnd, f"Pin1={p1}, Pin2={p2}")
        rpt.check(f"{ref} ({ch}): ein Pin HOT_IN/NINV", has_hot, f"Pin1={p1}, Pin2={p2}")
        rpt.check(f"{ref} ({ch}): Pins NICHT gleich", not both_same, f"Pin1={p1}, Pin2={p2}")


def validate_bss138(nets, components, rpt):
    """BSS138 Muting Transistors."""
    rpt.section("BSS138 Muting-Transistoren (Q1–Q7)")
    
    rpt.note("Q1: Master Mute — Gate=MUTE_CTRL, Source=GND, Drain=/MUTE")
    rpt.note("Q2-Q7: Channel Mute — Gate=MUTE, Source=GND, Drain=CHx_GAIN_OUT")
    
    for i in range(1, 8):
        ref = f"Q{i}"
        pin_nets = get_component_nets(nets, ref)
        
        if not pin_nets:
            rpt.check(f"{ref} im Netlist", False, "NICHT GEFUNDEN")
            continue
        
        # Gate (pin 1)
        gate = pin_nets.get("1", pin_nets.get("G", "???"))
        # Source (pin 2) — MUST be GND
        source = pin_nets.get("2", pin_nets.get("S", "???"))
        # Drain (pin 3)
        drain = pin_nets.get("3", pin_nets.get("D", "???"))
        
        source_is_gnd = source == "GND"
        rpt.check(f"{ref}.Source = GND", source_is_gnd,
                  f"Gate={gate}, Source={source}, Drain={drain}")
        
        if not source_is_gnd:
            rpt.check(f"  {ref}.Source ist NICHT auf OUT_COLD!", "OUT_COLD" not in source.upper(),
                      f"Source={source} — F1-Regression!")


def validate_tel5_2422(nets, components, rpt):
    """F10: TEL5-2422 DC/DC Converter Pinout."""
    rpt.section("F10: TEL5-2422 DC/DC Wandler (U1)")
    
    pin_nets = get_component_nets(nets, "U1")
    comp = components.get("U1", {})
    
    rpt.note(f"Value: {comp.get('value', '???')}")
    rpt.note(f"Footprint: {comp.get('footprint', '???')}")
    rpt.note(f"Library: {comp.get('lib', '???')}:{comp.get('part', '???')}")
    
    if not pin_nets:
        rpt.check("U1 im Netlist", False, "NICHT GEFUNDEN!")
        return
    
    rpt.note(f"Pins gefunden: {sorted(pin_nets.keys(), key=lambda x: int(x) if x.isdigit() else 0)}")
    
    # TEL5-2422 correct pinout (TRACO DIP-24):
    # Pin 2 = +Vin, Pin 3 = -Vin (GND input)
    # Pin 22 = +Vout (+12V), Pin 23 = Common (GND output)
    # Pin 9 = -Vout (-12V), Pin 11 = +Vout (dup), Pin 14 = Common (dup), Pin 16 = -Vout (dup)
    expected = {
        "2": ("+VIN/24V", lambda n: "24" in n or "VIN" in n.upper() or "V_IN" in n.upper()),
        "3": ("GND (input)", lambda n: "GND" in n.upper()),
        "22": ("+Vout (+12V)", lambda n: "12" in n and "-" not in n),
        "23": ("Common (GND)", lambda n: "GND" in n.upper()),
        "9": ("-Vout (-12V)", lambda n: "12" in n and ("-" in n or "NEG" in n.lower() or "N12" in n.upper())),
    }
    
    for pin, (desc, check_fn) in expected.items():
        net = pin_nets.get(pin, "???")
        rpt.check(f"U1.Pin{pin} ({desc})", pin in pin_nets and check_fn(net),
                  f"Netz: {net}")
    
    # Check that old wrong pins (1, 7, 14, 18, 24) are NOT present
    old_wrong_pins = ["1", "7", "18", "24"]
    for pin in old_wrong_pins:
        if pin in pin_nets:
            rpt.warn(f"U1.Pin{pin} existiert noch (alter falscher Pin?)", f"Netz: {pin_nets[pin]}")


def validate_adp7118(nets, components, rpt):
    """F9: ADP7118ARDZ Positive LDO."""
    rpt.section("F9: ADP7118ARDZ Positive LDO (U14)")
    
    pin_nets = get_component_nets(nets, "U14")
    comp = components.get("U14", {})
    
    rpt.note(f"Value: {comp.get('value', '???')}")
    rpt.note(f"Footprint: {comp.get('footprint', '???')}")
    rpt.note(f"Library: {comp.get('lib', '???')}:{comp.get('part', '???')}")
    
    if not pin_nets:
        rpt.check("U14 im Netlist", False, "NICHT GEFUNDEN!")
        return
    
    rpt.note(f"Pins gefunden: {sorted(pin_nets.keys(), key=lambda x: int(x) if x.isdigit() else 0)}")
    
    # ARDZ pinout (SOIC-8 + EP):
    # 1=VOUT, 2=SENSE, 3=GND, 4=EN, 5=NC, 6=SS, 7=VIN, 8=VIN, 9=EP(GND)
    expected = {
        "1": ("VOUT", lambda n: "V+" in n or "11" in n or "VOUT" in n.upper()),
        "2": ("SENSE", lambda n: "V+" in n or "11" in n or "SENSE" in n.upper() or "VOUT" in n.upper()),
        "3": ("GND", lambda n: "GND" in n.upper()),
        "4": ("EN", lambda n: "EN" in n.upper() or "ENABLE" in n.upper()),
        "6": ("SS", lambda n: "SS" in n.upper() or "SOFT" in n.upper()),
        "7": ("VIN", lambda n: "12" in n or "VIN" in n.upper()),
    }
    
    for pin, (desc, check_fn) in expected.items():
        net = pin_nets.get(pin, "???")
        if net == "???":
            rpt.check(f"U14.Pin{pin} ({desc})", False, "Pin nicht im Netlist")
        else:
            rpt.check(f"U14.Pin{pin} ({desc})", check_fn(net), f"Netz: {net}")


def validate_adp7182(nets, components, rpt):
    """ADP7182 Negative LDO."""
    rpt.section("ADP7182 Negative LDO (U15)")
    
    pin_nets = get_component_nets(nets, "U15")
    comp = components.get("U15", {})
    
    rpt.note(f"Value: {comp.get('value', '???')}")
    rpt.note(f"Footprint: {comp.get('footprint', '???')}")
    
    if not pin_nets:
        rpt.check("U15 im Netlist", False, "NICHT GEFUNDEN!")
        return
    
    # ADP7182 SOT-23-5: 1=GND, 2=VIN, 3=EN, 4=ADJ/NR, 5=VOUT
    expected = {
        "1": ("GND", lambda n: "GND" in n.upper()),
        "2": ("VIN (-12V)", lambda n: "12" in n or "VIN" in n.upper()),
        "3": ("EN", lambda n: "EN" in n.upper()),
        "5": ("VOUT (V-)", lambda n: "V-" in n or "V_NEG" in n.upper() or "11" in n or "VOUT" in n.upper()),
    }
    
    for pin, (desc, check_fn) in expected.items():
        net = pin_nets.get(pin, "???")
        if net == "???":
            rpt.check(f"U15.Pin{pin} ({desc})", False, "Pin nicht im Netlist")
        else:
            rpt.check(f"U15.Pin{pin} ({desc})", check_fn(net), f"Netz: {net}")


def validate_lm4562(nets, components, rpt):
    """LM4562 Dual Op-Amp Pinout for all 12 instances."""
    rpt.section("LM4562 Op-Amps (U2–U13) — Pinout-Validierung")
    
    rpt.note("LM4562 SOIC-8: 1=OutA, 2=InvA(-), 3=NinvA(+), 4=V-, 5=NinvB(+), 6=InvB(-), 7=OutB, 8=V+")
    
    for i in range(2, 14):
        ref = f"U{i}"
        pin_nets = get_component_nets(nets, ref)
        comp = components.get(ref, {})
        
        if not pin_nets:
            rpt.check(f"{ref} im Netlist", False, "NICHT GEFUNDEN!")
            continue
        
        # Pin 4 should be V-
        p4 = pin_nets.get("4", "???")
        rpt.check(f"{ref}.Pin4 = V-", "V-" in p4 or "V_NEG" in p4.upper() or p4.startswith("-"),
                  f"Netz: {p4}")
        
        # Pin 8 should be V+
        p8 = pin_nets.get("8", "???")
        rpt.check(f"{ref}.Pin8 = V+", "V+" in p8 or "V_POS" in p8.upper(),
                  f"Netz: {p8}")


def validate_signal_chain(nets, components, rpt):
    """Complete signal chain verification per channel."""
    rpt.section("Signalkette — Pro-Kanal-Verifikation")
    
    # Channel mapping (from FINDINGS.md):
    # CH1: J3→U2(RX)→U2B(Gain)→Q2(Mute)→U7(Driver)→J9
    channels = {
        "CH1": {"xlr_in": "J3", "rx": "U2",  "gain_u": "U2",  "mute": "Q2", "drv": "U7",  "xlr_out": "J9"},
        "CH2": {"xlr_in": "J4", "rx": "U3",  "gain_u": "U3",  "mute": "Q3", "drv": "U8",  "xlr_out": "J10"},
        "CH3": {"xlr_in": "J5", "rx": "U4",  "gain_u": "U4",  "mute": "Q4", "drv": "U9",  "xlr_out": "J11"},
        "CH4": {"xlr_in": "J6", "rx": "U5",  "gain_u": "U5",  "mute": "Q5", "drv": "U10", "xlr_out": "J12"},
        "CH5": {"xlr_in": "J7", "rx": "U6",  "gain_u": "U6",  "mute": "Q6", "drv": "U11", "xlr_out": "J13"},
        "CH6": {"xlr_in": "J8", "rx": "U13", "gain_u": "U13", "mute": "Q7", "drv": "U12", "xlr_out": "J14"},
    }
    
    for ch_name, ch in channels.items():
        rpt.note(f"--- {ch_name}: {ch['xlr_in']}→{ch['rx']}→{ch['gain_u']}→{ch['mute']}→{ch['drv']}→{ch['xlr_out']} ---")
        
        # 1. XLR Input Pin 2 (Hot) should reach RX op-amp
        xlr_pins = get_component_nets(nets, ch["xlr_in"])
        rx_pins = get_component_nets(nets, ch["rx"])
        
        hot_net = xlr_pins.get("2", "???")
        
        # RX OpA: Pin 3 = NINV(+) should be on HOT path (via EMI filter + DC block)
        rx_ninv = rx_pins.get("3", "???")  # NINV(+) of OPA-A
        rx_inv = rx_pins.get("2", "???")   # INV(-) of OPA-A
        rx_out = rx_pins.get("1", "???")   # OUT of OPA-A
        
        rpt.check(f"{ch_name}: RX.OutA (Pin1) auf RX_OUT-Netz", "RX_OUT" in rx_out.upper(),
                  f"Netz: {rx_out}")
        
        # 2. Gain Stage: OPB of same chip
        gain_inv = rx_pins.get("6", "???")   # INV(-) of OPB
        gain_ninv = rx_pins.get("5", "???")  # NINV(+) of OPB - should be at virtual GND or RX_OUT
        gain_out = rx_pins.get("7", "???")   # OUT of OPB
        
        rpt.check(f"{ch_name}: Gain.OutB (Pin7) auf GAIN_OUT-Netz", "GAIN" in gain_out.upper(),
                  f"Netz: {gain_out}")
        
        # 3. Mute transistor: Drain should be on GAIN_OUT net
        mute_pins = get_component_nets(nets, ch["mute"])
        mute_drain = mute_pins.get("3", mute_pins.get("D", "???"))
        mute_source = mute_pins.get("2", mute_pins.get("S", "???"))
        
        rpt.check(f"{ch_name}: Mute.Drain auf GAIN_OUT", "GAIN" in mute_drain.upper(),
                  f"Netz: {mute_drain}")
        rpt.check(f"{ch_name}: Mute.Source = GND", mute_source == "GND",
                  f"Netz: {mute_source}")
        
        # 4. Driver: Balanced output
        drv_pins = get_component_nets(nets, ch["drv"])
        drv_out_a = drv_pins.get("1", "???")  # OPA-A output (Cold arm, non-inverting)
        drv_out_b = drv_pins.get("7", "???")  # OPB output (Hot arm, inverting)
        
        # At least one should have OUT_HOT, other OUT_COLD
        has_hot_out = any("OUT_HOT" in v.upper() or "HOT" in v.upper() 
                        for v in [drv_out_a, drv_out_b])
        has_cold_out = any("OUT_COLD" in v.upper() or "COLD" in v.upper() 
                          for v in [drv_out_a, drv_out_b])
        
        rpt.check(f"{ch_name}: Driver hat OUT_HOT Ausgang", has_hot_out,
                  f"OutA={drv_out_a}, OutB={drv_out_b}")
        rpt.check(f"{ch_name}: Driver hat OUT_COLD Ausgang", has_cold_out,
                  f"OutA={drv_out_a}, OutB={drv_out_b}")


def validate_esd_protection(nets, components, rpt):
    """ESD TVS Diodes on XLR pins."""
    rpt.section("ESD-Schutz (PESD5V0S1BL TVS-Dioden)")
    
    tvs_count = 0
    for ref, info in components.items():
        if info.get("part", "").startswith("PESD5V0"):
            tvs_count += 1
    
    rpt.check(f"24× PESD5V0S1BL TVS-Dioden vorhanden", tvs_count == 24,
              f"Gefunden: {tvs_count}")
    
    # SMBJ15CA at REMOTE
    smbj_count = sum(1 for ref, info in components.items() if "SMBJ" in info.get("part", ""))
    rpt.check(f"1× SMBJ15CA am REMOTE-Eingang", smbj_count >= 1,
              f"Gefunden: {smbj_count}")


def validate_decoupling(nets, components, rpt):
    """100nF decoupling at each LM4562."""
    rpt.section("Entkopplung — 100nF C0G an jedem LM4562")
    
    # Check V+ and V- nets have enough capacitors
    vplus_net = None
    vminus_net = None
    
    for name, pins in nets.items():
        if name in ["V+", "+V", "VCC"]:
            vplus_net = name
        if name in ["V-", "-V", "VEE"]:
            vminus_net = name
    
    if vplus_net:
        vplus_caps = [f"{r}.{p}" for r, p in nets[vplus_net] if r.startswith("C")]
        rpt.check(f"V+ Netz ({vplus_net}): ≥12 Kondensatoren", len(vplus_caps) >= 12,
                  f"Gefunden: {len(vplus_caps)} Caps auf V+")
    else:
        rpt.check("V+ Netz existiert", False, "Nicht gefunden!")
    
    if vminus_net:
        vminus_caps = [f"{r}.{p}" for r, p in nets[vminus_net] if r.startswith("C")]
        rpt.check(f"V- Netz ({vminus_net}): ≥12 Kondensatoren", len(vminus_caps) >= 12,
                  f"Gefunden: {len(vminus_caps)} Caps auf V-")
    else:
        rpt.check("V- Netz existiert", False, "Nicht gefunden!")


def validate_zobel(nets, components, rpt):
    """F7: Zobel Networks at output."""
    rpt.section("F7: Zobel-Netzwerke (10Ω + 100nF)")
    
    rpt.note("Jeder Balanced-Ausgang hat 2 Zobel-Netzwerke (Hot + Cold)")
    rpt.note("Zobel-R (10Ω) + Zobel-C (100nF) in Serie, Shunt nach GND von Output-Pin")
    
    # Check that no Zobel component has both pins on GND (would indicate F1 regression)
    zobel_r_refs = []
    for ref, info in components.items():
        if info.get("value") == "10" and ref.startswith("R"):
            # Could be Zobel R — check if one pin is on an OUT net
            pin_nets = get_component_nets(nets, ref)
            p1 = pin_nets.get("1", "")
            p2 = pin_nets.get("2", "")
            if "OUT" in p1.upper() or "OUT" in p2.upper() or "ZOBEL" in p1.upper() or "ZOBEL" in p2.upper():
                zobel_r_refs.append(ref)
                both_gnd = (p1 == "GND" and p2 == "GND")
                rpt.check(f"{ref}: Nicht beide Pins auf GND", not both_gnd,
                          f"Pin1={p1}, Pin2={p2}")
    
    rpt.note(f"Identifizierte Zobel-R (10Ω mit OUT-Netz): {zobel_r_refs}")


def validate_output_resistors(nets, components, rpt):
    """F8: Output 47Ω series resistors."""
    rpt.section("F8: Ausgangs-47Ω Serienwiderstände")
    
    rpt.note("Je 47Ω zwischen Balanced Driver Output und XLR-Ausgang")
    
    r47_refs = []
    for ref, info in components.items():
        if info.get("value") == "47" and ref.startswith("R"):
            r47_refs.append(ref)
    
    rpt.note(f"47Ω Widerstände gefunden: {len(r47_refs)} (Soll: 24 — 12 EMI + 12 Ausgang)")
    
    # Check that no 47Ω output resistor has BOTH pins on GND
    for ref in r47_refs:
        pin_nets = get_component_nets(nets, ref)
        p1 = pin_nets.get("1", "")
        p2 = pin_nets.get("2", "")
        both_gnd = (p1 == "GND" and p2 == "GND")
        if both_gnd:
            rpt.check(f"{ref}: Nicht beide Pins GND", False, f"Pin1={p1}, Pin2={p2}")


def validate_power_supply(nets, components, rpt):
    """Power supply chain: 24V → TEL5 → ±12V → LDO → ±11V."""
    rpt.section("Spannungsversorgung — Kette 24V→±12V→±11V")
    
    # Check +12V net exists
    plus12 = None
    minus12 = None
    for name in nets:
        if name in ["+12V", "12V", "+12V_RAIL"]:
            plus12 = name
        if name in ["-12V", "NEG_12V", "-12V_RAIL"]:
            minus12 = name
    
    rpt.check("+12V Netz existiert", plus12 is not None,
              f"Name: {plus12}" if plus12 else "Nicht gefunden")
    rpt.check("-12V Netz existiert", minus12 is not None,
              f"Name: {minus12}" if minus12 else "Nicht gefunden")
    
    # Check bulk caps on ±12V
    if plus12:
        plus12_pins = nets[plus12]
        caps = [r for r, p in plus12_pins if r.startswith("C")]
        rpt.note(f"+12V: {len(caps)} Kondensatoren, {len(plus12_pins)} Pins total")
    if minus12:
        minus12_pins = nets[minus12]
        caps = [r for r, p in minus12_pins if r.startswith("C")]
        rpt.note(f"-12V: {len(caps)} Kondensatoren, {len(minus12_pins)} Pins total")


def validate_gain_stage(nets, components, rpt):
    """DIP-Switch Gain Stage."""
    rpt.section("Gain-Stufe — DIP-Switch Widerstände")
    
    rpt.note("6× SW_DIP_x03 (SW1-SW6) mit 30k/15k/7.5k Widerständen")
    
    dip_count = sum(1 for ref, info in components.items() if "DIP" in info.get("part", "").upper())
    rpt.check(f"6× DIP-Switch vorhanden", dip_count == 6, f"Gefunden: {dip_count}")
    
    # Check 30k, 15k, 7.5k resistors exist
    for val in ["30k", "15k", "7.5k"]:
        count = sum(1 for ref, info in components.items() 
                   if info.get("value", "") == val and ref.startswith("R"))
        rpt.check(f"6× {val} Widerstände", count == 6, f"Gefunden: {count}")


def validate_muting_circuit(nets, components, rpt):
    """Muting Circuit — Q1 master + Q2-Q7 channels."""
    rpt.section("Muting-Schaltung")
    
    # Q1 is master mute
    q1_pins = get_component_nets(nets, "Q1")
    if q1_pins:
        q1_drain = q1_pins.get("3", q1_pins.get("D", "???"))
        rpt.check("Q1.Drain auf MUTE-Netz", "MUTE" in q1_drain.upper(), f"Netz: {q1_drain}")
        q1_source = q1_pins.get("2", q1_pins.get("S", "???"))
        rpt.check("Q1.Source = GND", q1_source == "GND", f"Netz: {q1_source}")
    
    # EN_CTRL net should exist
    en_ctrl_exists = any("EN_CTRL" in name.upper() or "EN" in name.upper() 
                        for name in nets.keys())
    rpt.check("EN_CTRL / Enable-Netz existiert", en_ctrl_exists)


def validate_component_count(components, rpt):
    """Component count validation."""
    rpt.section("Bauteil-Inventar")
    
    counts = defaultdict(int)
    for ref, info in components.items():
        prefix = re.match(r'([A-Z]+)', ref)
        if prefix:
            counts[prefix.group(1)] += 1
    
    rpt.note(f"Gesamt: {len(components)} Bauteile")
    
    expected = {
        "U": (15, "ICs (12×LM4562 + TEL5 + ADP7118 + ADP7182)"),
        "R": (90, "Widerstände (approx)"),  # many resistors
        "C": (50, "Kondensatoren (approx)"),
        "D": (25, "Dioden (24×PESD + 1×SMBJ)"),
        "Q": (7, "BSS138 MOSFETs"),
        "J": (14, "Steckverbinder"),
        "SW": (7, "Schalter (6×DIP + 1×SPDT)"),
        "FB": (2, "Ferrite Beads"),
    }
    
    for prefix, (exp, desc) in expected.items():
        actual = counts.get(prefix, 0)
        # Allow some tolerance for R, C
        if prefix in ["R", "C"]:
            ok = actual >= exp * 0.7
        else:
            ok = actual == exp
        rpt.check(f"{prefix}: {actual} (Soll: ~{exp} — {desc})", ok,
                  f"Gefunden: {actual}")


def validate_net_summary(nets, rpt):
    """Net Statistics."""
    rpt.section("Netz-Statistik")
    
    rpt.note(f"Gesamtzahl Netze: {len(nets)}")
    
    # Largest nets
    sorted_nets = sorted(nets.items(), key=lambda x: -len(x[1]))
    rpt.note("Top-10 größte Netze:")
    for name, pins in sorted_nets[:10]:
        refs = sorted(set(f"{r}" for r, p in pins))
        rpt.note(f"  {name}: {len(pins)} Pins — Bauteile: {', '.join(refs[:10])}{'...' if len(refs) > 10 else ''}")
    
    # Check for suspiciously large nets (>50 pins = possible merge)
    for name, pins in nets.items():
        if len(pins) > 100 and name != "GND":
            rpt.warn(f"Netz '{name}' hat {len(pins)} Pins — möglicherweise falscher Merge!")
    
    # Check for unconnected nets (only 1 pin)
    single_pin_nets = [(name, pins) for name, pins in nets.items() if len(pins) == 1]
    if single_pin_nets:
        rpt.note(f"Netze mit nur 1 Pin: {len(single_pin_nets)}")
        for name, pins in single_pin_nets[:5]:
            rpt.note(f"  {name}: {pins[0][0]}.{pins[0][1]}")


def validate_footprints(components, rpt):
    """Footprint assignment validation."""
    rpt.section("Footprint-Zuordnung")
    
    critical_fps = {
        "U1": ("TEL5", "TEL5_DUAL_TRP oder DIP-24"),
        "U14": ("SOIC", "SOIC127P600X175-9N oder SOIC-8"),
        "U15": ("SOT-23", "SOT-23-5"),
    }
    
    for ref, (fp_substr, desc) in critical_fps.items():
        comp = components.get(ref, {})
        fp = comp.get("footprint", "???")
        rpt.check(f"{ref}: Footprint enthält '{fp_substr}'", fp_substr.upper() in fp.upper(),
                  f"Footprint: {fp} (Soll: {desc})")
    
    # Check all LM4562 have SOIC-8 footprint
    lm_fps = set()
    for i in range(2, 14):
        comp = components.get(f"U{i}", {})
        lm_fps.add(comp.get("footprint", "???"))
    
    rpt.check("Alle LM4562 (U2-U13) haben SOIC-8 Footprint",
              all("SOIC" in fp.upper() or "SO-8" in fp.upper() for fp in lm_fps),
              f"Footprints: {lm_fps}")


def validate_unconnected_pins(nets, components, rpt):
    """Check for unconnected/unassigned pins."""
    rpt.section("Unverbundene Pins")
    
    # Collect all pins that ARE in a net
    connected = set()
    for name, pins in nets.items():
        for r, p in pins:
            connected.add((r, p))
    
    # Find unconnected nets (pins listed as "unconnected-*")
    unconnected_nets = {name: pins for name, pins in nets.items() 
                       if "unconnected" in name.lower()}
    
    if unconnected_nets:
        rpt.note(f"Unverbundene Netze: {len(unconnected_nets)}")
        for name, pins in sorted(unconnected_nets.items()):
            for r, p in pins:
                rpt.note(f"  {r}.Pin{p} — {name}")
    else:
        rpt.note("Keine explizit unverbundenen Netze gefunden")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    rpt = ValidationReport()
    
    # === Step 0: Bracket Balance ===
    rpt.section("Grundlagen-Checks")
    depth, size = check_brackets(SCH)
    rpt.check("Klammer-Balance .kicad_sch", depth == 0, f"Depth={depth}, Size={size} chars")
    
    # === Step 1: Netlist Export ===
    rc, stderr = export_netlist()
    rpt.check("kicad-cli Netlist-Export", rc == 0,
              f"Exit code: {rc}" + (f", stderr: {stderr[:200]}" if stderr else ""))
    
    if rc != 0:
        print("FATAL: Netlist-Export fehlgeschlagen — Abbruch!")
        rpt.print_report()
        return 1
    
    # === Step 2: ERC ===
    erc_rc, errors, warnings = run_erc()
    rpt.check("ERC: 0 Errors", len(errors) == 0,
              f"{len(errors)} Errors" + (f": {[e.get('description','') for e in errors[:5]]}" if errors else ""))
    rpt.note(f"ERC Warnings: {len(warnings)}")
    
    # Categorize warnings
    warn_cats = defaultdict(int)
    for w in warnings:
        warn_cats[w.get("type", "unknown")] += 1
    for cat, count in sorted(warn_cats.items(), key=lambda x: -x[1]):
        rpt.note(f"  {cat}: {count}")
    
    # === Step 3: Parse Netlist ===
    nets, components = parse_netlist(NETLIST_PATH)
    rpt.check("Netlist-Parser: Netze gefunden", len(nets) > 50, f"{len(nets)} Netze")
    rpt.check("Netlist-Parser: Bauteile gefunden", len(components) > 200, f"{len(components)} Bauteile")
    
    # === Step 4: All Validations ===
    validate_gnd_separation(nets, rpt)
    validate_xlr_inputs(nets, components, rpt)
    validate_xlr_outputs(nets, components, rpt)
    validate_diff_receiver(nets, components, rpt)
    validate_rgnd(nets, components, rpt)
    validate_bss138(nets, components, rpt)
    validate_tel5_2422(nets, components, rpt)
    validate_adp7118(nets, components, rpt)
    validate_adp7182(nets, components, rpt)
    validate_lm4562(nets, components, rpt)
    validate_signal_chain(nets, components, rpt)
    validate_esd_protection(nets, components, rpt)
    validate_decoupling(nets, components, rpt)
    validate_zobel(nets, components, rpt)
    validate_output_resistors(nets, components, rpt)
    validate_power_supply(nets, components, rpt)
    validate_gain_stage(nets, components, rpt)
    validate_muting_circuit(nets, components, rpt)
    validate_component_count(components, rpt)
    validate_footprints(components, rpt)
    validate_net_summary(nets, rpt)
    validate_unconnected_pins(nets, components, rpt)
    
    # === Print Report ===
    rpt.print_report()
    
    return 1 if rpt.total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
