#!/usr/bin/env python3
"""
Generisches KiCad Schematic Validierungsskript.
Prueft Datei-Integritaet, kicad-cli Kompatibilitaet, ERC und Netz-Verbindungen.

Verwendung:
    python3 validate_schematic.py [schematic.kicad_sch]
    
Ohne Argument wird aurora-dsp-icepower-booster.kicad_sch verwendet.
"""
import re
import os
import sys
import subprocess
import uuid as uuid_mod

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
ERC_ERROR_BASELINE = 0  # Erwartete ERC-Fehleranzahl (darf nicht steigen)

# Erwartete Netz-Verbindungen: {Netzname: [(Ref, Pin), ...]}
# Anpassen pro Projekt!
EXPECTED_NETS = {
    "/REMOTE_IN":   [("J14", "T"), ("D25", "1"), ("R105", "1")],
    "/REMOTE_FILT": [("C79", "1"), ("R105", "2"), ("SW7", "3")],
    "/EN_CTRL":     [("R79", "1"), ("R80", "1"), ("SW7", "2"), ("U14", "4"), ("U15", "3")],
    "/SS_U14":      [("C81", "1"), ("U14", "5")],
    "/NR_U15":      [("C82", "1"), ("U15", "4")],
    "/+24V_IN":     [("J13", "1"), ("U13", "1")],
    "/+12V":        [("U13", "24"), ("U14", "6"), ("SW7", "1")],
    "/-12V":        [("U13", "14"), ("U15", "2")],
    "/GND":         [("J14", "S"), ("D25", "2"), ("C79", "2"), ("J13", "2")],
}

# Signal-Vertauschungs-Checks: [(Ref, Pin) darf NICHT auf Netz sein]
ANTI_CONNECTIONS = [
    (("J14", "T"), "/GND",       "J14.T (Tip/Signal) darf nicht auf GND sein"),
    (("J14", "S"), "/REMOTE_IN", "J14.S (Sleeve/GND) darf nicht auf REMOTE_IN sein"),
]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def extract_block(text, start_idx):
    """Extrahiert einen balancierten Klammer-Block ab start_idx."""
    depth = 0
    for i in range(start_idx, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start_idx:i+1]
    return None


def find_symbol_by_reference(sch_text, reference):
    """Findet lib_id und Block fuer eine bestimmte Reference."""
    for m in re.finditer(r'\(symbol \(lib_id "([^"]+)"\)\s*\(at', sch_text):
        block = extract_block(sch_text, m.start())
        if block and f'"Reference" "{reference}"' in block:
            return m.group(1), block
    return None, None


def extract_nets(netlist_text):
    """Parst alle Netze aus einer KiCad-Netlist."""
    nets = {}
    i = 0
    while True:
        idx = netlist_text.find("(net (code", i)
        if idx == -1:
            break
        depth = 0
        start = idx
        for j in range(idx, len(netlist_text)):
            if netlist_text[j] == '(':
                depth += 1
            elif netlist_text[j] == ')':
                depth -= 1
                if depth == 0:
                    block = netlist_text[start:j+1]
                    name_m = re.search(r'\(name "?([^")\s]+)"?\)', block)
                    if name_m:
                        net_name = name_m.group(1)
                        nodes = re.findall(
                            r'\(node \(ref "?(\w+)"?\)\s*\(pin "?([^")\s]+)"?\)',
                            block
                        )
                        nets[net_name] = nodes
                    i = j + 1
                    break
        else:
            break
    return nets


# ---------------------------------------------------------------------------
# Validierungs-Checks
# ---------------------------------------------------------------------------
class Validator:
    def __init__(self, sch_path):
        self.sch_path = sch_path
        self.passes = []
        self.fails = []
        self.warns = []
        
        with open(sch_path) as f:
            self.sch = f.read()

    def check_paren_balance(self):
        """Prueft Klammer-Balance."""
        depth = 0
        for ch in self.sch:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
        if depth == 0:
            self.passes.append(f"Klammer-Balance: 0")
        else:
            self.fails.append(f"Klammer-Balance: {depth} (NICHT 0!)")

    def check_file_size(self, min_size=100000, max_size=500000):
        """Prueft ob Dateigroesse plausibel ist."""
        size = os.path.getsize(self.sch_path)
        if min_size < size < max_size:
            self.passes.append(f"Dateigroesse: {size} Bytes")
        else:
            self.warns.append(f"Dateigroesse {size} ausserhalb {min_size}-{max_size}")

    def check_kicad_cli_netlist(self):
        """Prueft ob kicad-cli die Datei laden kann."""
        tmp_net = f"/tmp/validate_{uuid_mod.uuid4().hex[:8]}.net"
        try:
            result = subprocess.run(
                [KICAD_CLI, "sch", "export", "netlist", "--output", tmp_net, self.sch_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.passes.append("kicad-cli Netlist-Export OK")
                # Netlist fuer spaetere Checks speichern
                if os.path.exists(tmp_net):
                    with open(tmp_net) as f:
                        self.netlist_text = f.read()
                    os.unlink(tmp_net)
                return True
            else:
                self.fails.append(f"kicad-cli Netlist fehlgeschlagen: {result.stderr[:200]}")
                return False
        except Exception as e:
            self.fails.append(f"kicad-cli Ausfuehrung: {e}")
            return False

    def check_erc(self):
        """Fuehrt ERC durch und vergleicht mit Baseline."""
        tmp_rpt = f"/tmp/validate_erc_{uuid_mod.uuid4().hex[:8]}.rpt"
        try:
            subprocess.run(
                [KICAD_CLI, "sch", "erc", "--output", tmp_rpt, "--severity-all", self.sch_path],
                capture_output=True, text=True, timeout=60
            )
            if os.path.exists(tmp_rpt):
                with open(tmp_rpt) as f:
                    erc = f.read()
                os.unlink(tmp_rpt)
                m = re.search(r'ERC messages:\s*(\d+)\s*Errors\s*(\d+)\s*Warnings\s*(\d+)', erc)
                if m:
                    errs = int(m.group(2))
                    warns = int(m.group(3))
                    if errs <= ERC_ERROR_BASELINE:
                        self.passes.append(f"ERC: {errs} Errors (Baseline: {ERC_ERROR_BASELINE})")
                    else:
                        self.fails.append(f"ERC: {errs} Errors > Baseline {ERC_ERROR_BASELINE} (+{errs - ERC_ERROR_BASELINE})")
                    return errs, warns
                else:
                    self.warns.append("ERC Summary nicht parsebar")
            else:
                self.warns.append("ERC Report nicht erstellt")
        except Exception as e:
            self.warns.append(f"ERC: {e}")
        return None, None

    def check_net_connections(self):
        """Prueft erwartete Netz-Verbindungen in der Netlist."""
        if not hasattr(self, 'netlist_text'):
            self.warns.append("Keine Netlist fuer Netz-Check verfuegbar")
            return
        
        nets = extract_nets(self.netlist_text)
        
        for net_name, expected_nodes in EXPECTED_NETS.items():
            if net_name in nets:
                actual = set((ref, pin) for ref, pin in nets[net_name])
                missing = [f"{ref}.{pin}" for ref, pin in expected_nodes if (ref, pin) not in actual]
                if missing:
                    self.fails.append(f"Netz {net_name}: fehlend: {missing}")
                else:
                    self.passes.append(f"Netz {net_name}: OK ({len(nets[net_name])} Nodes)")
            else:
                self.fails.append(f"Netz {net_name} nicht gefunden!")

        # Signal-Vertauschungs-Checks
        for (ref, pin), net_name, msg in ANTI_CONNECTIONS:
            if net_name in nets:
                nodes = set((r, p) for r, p in nets[net_name])
                if (ref, pin) in nodes:
                    self.fails.append(f"KRITISCH: {msg}")
                else:
                    self.passes.append(f"Keine Vertauschung: {ref}.{pin} nicht auf {net_name}")

    def check_lib_symbols_cache(self):
        """Prueft lib_symbols Cache auf korrekte Sub-Symbol-Naming."""
        cache_start = self.sch.find('(lib_symbols')
        if cache_start < 0:
            self.fails.append("lib_symbols Sektion nicht gefunden!")
            return
        
        cache_block = extract_block(self.sch, cache_start)
        if not cache_block:
            self.fails.append("lib_symbols Block nicht extrahierbar!")
            return
        
        # Finde alle Sub-Symbole
        sub_syms = re.findall(r'\(symbol "([^"]+_\d+_\d+)"', cache_block)
        bad = [s for s in sub_syms if ":" in s]
        if bad:
            self.fails.append(f"Sub-Symbole mit Library-Prefix: {bad[:5]}")
        else:
            self.passes.append(f"lib_symbols Cache: {len(sub_syms)} Sub-Symbole OK")

    def check_symbol(self, reference, expected_lib_id=None, expected_footprint=None):
        """Prueft ein bestimmtes Symbol."""
        lib_id, block = find_symbol_by_reference(self.sch, reference)
        if not lib_id:
            self.fails.append(f"{reference}: nicht gefunden!")
            return
        
        if expected_lib_id and lib_id != expected_lib_id:
            self.fails.append(f"{reference}: lib_id={lib_id} (erwartet: {expected_lib_id})")
        elif expected_lib_id:
            self.passes.append(f"{reference}: lib_id={expected_lib_id}")
        
        if expected_footprint and block:
            fp_m = re.search(r'"Footprint" "([^"]+)"', block)
            if fp_m:
                fp = fp_m.group(1)
                if fp == expected_footprint:
                    self.passes.append(f"{reference}: Footprint OK")
                else:
                    self.fails.append(f"{reference}: Footprint={fp} (erwartet: {expected_footprint})")

    def run_all(self):
        """Fuehrt alle Checks aus."""
        print("=" * 60)
        print("KICAD SCHEMATIC VALIDIERUNG")
        print("=" * 60)

        print("\n[1] Datei-Integritaet...")
        self.check_paren_balance()
        self.check_file_size()

        print("[2] kicad-cli Netlist-Export...")
        cli_ok = self.check_kicad_cli_netlist()

        print("[3] ERC...")
        self.check_erc()

        print("[4] lib_symbols Cache...")
        self.check_lib_symbols_cache()

        print("[5] Netz-Verbindungen...")
        if cli_ok:
            self.check_net_connections()

        print("[6] Symbol-Checks...")
        self.check_symbol("J14", "Connector_Audio:AudioJack2",
                         "Connector_Audio:Jack_3.5mm_Lumberg_1503_02_Horizontal")
        self.check_symbol("J13", "Connector:Barrel_Jack")

        # Zusammenfassung
        print("\n" + "=" * 60)
        print("ERGEBNIS")
        print("=" * 60)
        print(f"\n  PASS: {len(self.passes)}  |  FAIL: {len(self.fails)}  |  WARN: {len(self.warns)}")

        if self.fails:
            print("\n  FEHLER:")
            for f in self.fails:
                print(f"    [FAIL] {f}")
        if self.warns:
            print("\n  WARNUNGEN:")
            for w in self.warns:
                print(f"    [WARN] {w}")
        if self.passes:
            print("\n  BESTANDEN:")
            for p in self.passes:
                print(f"    [PASS] {p}")

        if not self.fails:
            print("\n  >>> ALLE PRUEFUNGEN BESTANDEN <<<")
        else:
            print(f"\n  >>> {len(self.fails)} FEHLER GEFUNDEN <<<")
        
        return len(self.fails) == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sch_path = sys.argv[1] if len(sys.argv) > 1 else "aurora-dsp-icepower-booster.kicad_sch"
    
    if not os.path.exists(sch_path):
        print(f"Datei nicht gefunden: {sch_path}")
        sys.exit(1)
    
    validator = Validator(sch_path)
    success = validator.run_all()
    sys.exit(0 if success else 1)
