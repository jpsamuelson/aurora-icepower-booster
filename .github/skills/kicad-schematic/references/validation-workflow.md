# Validation Workflow Reference

## Dreistufige Validierung (nach JEDER Änderung)

### Stufe 1: Datei-Integrität
```python
# Klammer-Balance
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0

# Dateigröße plausibel (280-350KB für dieses Projekt)
import os
size = os.path.getsize(sch_file)
assert 280000 < size < 350000
```

### Stufe 2: kicad-cli Parser-Test
```bash
/opt/homebrew/bin/kicad-cli sch export netlist --output /tmp/test.net aurora-dsp-icepower-booster.kicad_sch
# Exit code 0 = Parser OK
# "Failed to load schematic" = lib_symbols Cache defekt
```

### Stufe 3: ERC Regression
```bash
/opt/homebrew/bin/kicad-cli sch erc --output /tmp/erc.rpt --severity-all aurora-dsp-icepower-booster.kicad_sch
# Parse: "ERC messages: TOTAL Errors ERRORS Warnings WARNINGS"
# Baseline: 115 Errors — DARF NICHT STEIGEN
```

## Netlist-Verbindungen prüfen

### Balanced-Paren Netlist-Parser
```python
def extract_nets(netlist_text):
    """Parst Netze aus KiCad-Netlist (multi-line Format)."""
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
```

### Erwartete Netz-Verbindungen (PSU/REMOTE)

```python
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
```

## Signal-Vertauschungs-Check

Immer prüfen, dass Signale nicht versehentlich vertauscht sind:
```python
# J14.T (Tip/Signal) darf NICHT auf GND sein
assert ("J14", "T") not in gnd_nodes
# J14.S (Sleeve/GND) darf NICHT auf REMOTE_IN sein
assert ("J14", "S") not in remote_in_nodes
```

## Quality Gate Kategorien

| ID | Kategorie | Prüft |
|----|-----------|-------|
| INT-1..3 | Integrität | Balance, kicad-cli Parse, Dateigröße |
| SYM-1..3 | Symbole | lib_id, Footprint, Value korrekt |
| NET-1..6 | Netze | Verbindungen, keine Vertauschung |
| ERC-1 | ERC | Baseline nicht überschritten |
| FP-1..2 | Footprints | Existenz, Pad-Namen |
| CACHE-1..2 | Cache | Sub-Symbol-Naming, Pin-Vollständigkeit |

## Automatisierung

Für wiederkehrende Validierung das quality_gate-Skript verwenden:
```bash
python3 quality_gate_psu_remote.py
# Ergebnis: N PASS, M FAIL, K WARN
```

Oder das generische Validierungsskript:
```bash
python3 .github/skills/kicad-schematic/scripts/validate_schematic.py
```
