---
name: kicad-schematic
description: "KiCad 9 schematic & PCB manipulation via Python scripts and kicad-cli. USE FOR: editing .kicad_sch files, adding/moving/wiring components, lib_symbols cache management, pin position calculation, ERC/netlist validation, S-expression format manipulation, quality gate checks. TRIGGERS: kicad, schematic, symbol, footprint, wire, net, ERC, DRC, pcb layout, routing, S-expression, lib_symbols, pin position."
argument-hint: "Describe what schematic change or validation you need"
---

# KiCad Schematic & PCB Manipulation

## When to Use

- Editing `.kicad_sch` or `.kicad_pcb` files
- Adding, modifying, or wiring components
- Managing lib_symbols cache entries
- Calculating pin positions for wire routing
- Running ERC/DRC/netlist validation
- Quality gate checks before fabrication
- Any S-expression file manipulation

## Critical Rules (NEVER VIOLATE)

### 1. Terminal — Kein Inline-Python

zsh im Copilot-Terminal korrumpiert heredocs und inline Python.

- **IMMER** `.py`-Datei schreiben → `python3 datei.py` ausführen
- **NIE** `python3 -c "..."` oder `cat << 'EOF'` verwenden
- **NIE** mehrzeiligen Python-Code im Terminal ausführen

### 2. S-Expression — Klammer-Balance

Nach JEDER Dateiänderung muss die Klammer-Balance geprüft werden:

```python
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Klammer-Balance: {depth}"
```

### 3. lib_symbols Cache — Sub-Symbol-Naming

Beim Hinzufügen neuer Symbole zur `lib_symbols`-Sektion:

- **Hauptsymbol**: MIT Library-Prefix → `(symbol "Connector_Audio:AudioJack2" ...)`
- **Sub-Symbole**: OHNE Library-Prefix → `(symbol "AudioJack2_0_1" ...)`
- **NIEMALS**: `(symbol "Connector_Audio:AudioJack2_0_1" ...)` — crasht kicad-cli!

### 4. Regex — Keine Cross-Symbol-Suche

`.search(r'lib_id "X".*?Reference.*?J14', text, DOTALL)` matcht über Symbol-Grenzen hinweg.
**Immer** Balanced-Paren-Block zuerst extrahieren, dann darin suchen.
Siehe [S-Expression Reference](./references/s-expression-format.md).

### 5. Validierung — Dreistufig nach jeder Änderung

1. Klammer-Balance prüfen (Python)
2. `kicad-cli sch export netlist` (testet Parser)
3. `kicad-cli sch erc --severity-all` (Baseline-Vergleich)

## Workflow: Schematic-Änderung

```
1. Backup erstellen (.bak_pre_<aktion>)
2. Änderung via Python-Skript
3. Klammer-Balance prüfen
4. kicad-cli Netlist-Export testen
5. kicad-cli ERC ausführen (Baseline: 115 Errors)
6. Netz-Verbindungen im Netlist verifizieren
7. Ergebnis zusammenfassen
```

### Backup-Konvention

```bash
cp aurora-dsp-icepower-booster.kicad_sch aurora-dsp-icepower-booster.kicad_sch.bak_pre_<aktion>
```

## Workflow: Neues Symbol in Schematic einfügen

1. Symbol aus KiCad System-Library extrahieren:
   ```
   /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/<Library>.kicad_sym
   ```
2. Hauptsymbol-Block mit Balanced-Paren-Extraktion lesen
3. Sub-Symbol-Naming korrigieren (Library-Prefix entfernen)
4. In lib_symbols-Sektion der .kicad_sch einfügen
5. Symbol-Instanz mit korrekten Properties einfügen
6. Wires und Labels hinzufügen
7. Validierung durchführen

Details: [S-Expression Format Reference](./references/s-expression-format.md)

## Workflow: Wire-Routing

1. Pin-Positionen berechnen (siehe [Pin-Kalkulation](./references/pin-calculation.md))
2. Wire-Segmente als S-Expression erzeugen
3. Labels an Endpunkten platzieren
4. Junctions an Kreuzungspunkten einfügen
5. Validierung via Netlist

## Workflow: Validierung / Quality Gate

Nutze [validate_schematic.py](./scripts/validate_schematic.py) als Basis:

```bash
python3 .github/skills/kicad-schematic/scripts/validate_schematic.py
```

Prüft automatisch:

- Klammer-Balance
- kicad-cli Netlist-Export
- kicad-cli ERC (Baseline-Vergleich)
- Netz-Verbindungen (konfigurierbar)
- Footprint-Existenz
- lib_symbols-Cache-Integrität

## Pin-Naming nach Bibliothek

| Library                      | Pin-Format | Beispiele               |
| ---------------------------- | ---------- | ----------------------- |
| Device:R, Device:C           | Nummern    | "1", "2"                |
| Connector_Audio:AudioJack2   | Buchstaben | "T" (Tip), "S" (Sleeve) |
| Connector_Audio:XLR3         | Mixed      | "1", "2", "3", "G"      |
| Connector:Barrel_Jack        | Nummern    | "1", "2"                |
| Amplifier_Operational:LM4562 | Nummern    | "1"-"8"                 |

**Regex für Pin-Matching**: Immer `[^"]+` statt `\d+` verwenden!

## MCP Server — Wann nutzen, wann nicht

| Geeignet                               | Nicht geeignet                   |
| -------------------------------------- | -------------------------------- |
| `open_project`, `get_project_info`     | Bulk-Verdrahtung (>10 Wires)     |
| `search_symbols`, `search_footprints`  | Multi-Unit-Symbole (extends-Bug) |
| `get_board_info`, `get_component_list` | Zuverlässiges Wire-Routing       |
| `export_gerber`, `export_bom`          | Schaltpläne >50 Bauteile         |
| `sync_schematic_to_board`              | Rotation von Bauteilen           |

Für alles Komplexe: Python-Skripte + kicad-cli.

## Dateipfade

| Was                 | Pfad                                                                          |
| ------------------- | ----------------------------------------------------------------------------- |
| Projekt             | `/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/` |
| kicad-cli           | `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`                      |
| Symbol-Libraries    | `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/`               |
| Footprint-Libraries | `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/`            |
| Custom Symbols      | `aurora-dsp-icepower-booster.kicad_sym`                                       |

## ERC Baseline

- **0 Errors** (runterreduziert von 115→66→0)
- **805 Warnings** — Aufschlüsselung:
  - 799 endpoint_off_grid (kosmetisch, MCP-Server 1mm-Raster vs. KiCad 1.27mm — Grid-Snap nicht sicher möglich wegen 25 2D-Kollisionen)
  - 6 label_multiple_wires (SUMNODE T-Kreuzungen — Labels für Netz-Konnektivität nötig, nicht entfernbar)
- **52 echte Warnungen eliminiert** (890→805): 39 isolierte Label-Stubs gelöscht, 6 ???-Stubs mit korrektem XLR-Pin verbunden, 1 Footprint korrigiert
- Neue Änderungen dürfen die Error-Zahl NICHT erhöhen
- Behobene Kategorien: missing_power_pin (12→0), pin_not_connected (19→0), label_dangling (12→0), pin_to_pin (6→0), wire_dangling (66→0), multiple_net_names (6→0), lib_symbol_mismatch (194→0), footprint_link_issues (18→0), unconnected_wire_endpoint (45→0)
- multiple_net_names Fix: CHx_HOT_RAW → CHx_OUT_COLD umbenannt (12 Labels)
- lib_symbols Fix: Device:R, Device:C, Device:D Cache von KiCad 9 Library aktualisiert
- Footprint Fix: XLR-F/M → Neutrik NC3FBH2/NC3MBH, DIP Switch → korrekter Name, TEL5-2422 → Package_DIP:DIP-24_W15.24mm
- Stub Fix: 39 isolierte V+/V-/GND/OUT_COLD Label-Stubs gelöscht (komplett isoliert, keine Konnektivitätsänderung), 6 XLR-Cold-Stubs mit Pin 2 der XLR-Eingangsbuchsen verbunden (MCP-Server Y-Vorzeichen-Fehler korrigiert)
- Neue Netze pro Kanal: INV_IN, SW_OUT_1/2/3, BUF_DRIVE, GAIN_FB, OUT_DRIVE, OUT_PROT_HOT/COLD, EMI_HOT/COLD

## Audio-PCB-Design-Regeln

Vollständige Regeln in [copilot-instructions.md](../../../.github/copilot-instructions.md).
Kurzfassung:

- Ungeteilte GND-Fläche auf B.Cu
- Audio-Traces auf Top-Layer, keine Vias im Signalpfad
- Kein X7R/X5R im Audio-Signalpfad (Mikrofonie!)
- Entkopplung: 100nF C0G direkt am IC + 10µF dahinter
- Schaltregler ≥ 20mm von Audio-Eingangsstufe
- Guard-Traces um empfindliche Audio-Eingänge
