# KiCad PCB Design — Copilot Instructions

## Project: Aurora DSP IcePower Booster

- **Amplifier board** based on ICEpower modules
- **KiCad 9** project (schematic + PCB)
- **Target manufacturing**: JLCPCB (2-layer standard, HASL, FR-4)
- **Language**: English for all comments and explanations

---

## 1. KiCad MCP Server — Architecture & Tool Access

The KiCad MCP Server provides **64 tools**, organized using the **Router Pattern**:

- **~17 Direct Tools** — always visible, for frequent operations
- **~47 Routed Tools** — in 7 categories, accessible via router
- **4 Router Tools** — for discovery and execution

### Router Pattern (context-efficient, always use!)

```
1. list_tool_categories    → Show all 7 categories
2. get_category_tools      → List tools in a category
3. search_tools            → Find tools by keyword
4. execute_tool            → Execute a routed tool
```

### Direct Tools (usable without router)

| Tool                      | Function                                                   |
| ------------------------- | ---------------------------------------------------------- |
| `create_project`          | Create new KiCad project (.kicad_pro + .kicad_pcb + .kicad_sch) |
| `open_project`            | Load existing project                                      |
| `save_project`            | Save project                                               |
| `snapshot_project`        | Checkpoint with PDF rendering                              |
| `get_project_info`        | Project metadata                                           |
| `place_component`         | Place footprint on PCB                                     |
| `move_component`          | Reposition component                                       |
| `add_net`                 | Create new net                                             |
| `route_trace`             | Route trace (single layer)                                 |
| `set_board_size`          | Configure PCB dimensions                                   |
| `add_board_outline`       | Board outline (rectangle/circle/polygon/rounded)           |
| `get_board_info`          | Retrieve board properties                                  |
| `add_schematic_component` | Place symbol (~10,000 KiCad symbols)                       |
| `connect_passthrough`     | J1→J2 passthrough connection (all pins)                    |
| `connect_to_net`          | Connect pin to named net                                   |
| `add_schematic_net_label` | Net label in schematic                                     |
| `sync_schematic_to_board` | Schematic → PCB sync (F8)                                  |

### Routed Tool Categories

| Category      | Tools | Contents                                                           |
| ------------- | ----- | ------------------------------------------------------------------ |
| **BOARD**     | 9     | Layer management, mounting holes, zones, board text, 2D preview    |
| **COMPONENT** | 8     | Rotate, delete, edit, find, properties, group                      |
| **EXPORT**    | 8     | Gerber, PDF, SVG, 3D (STEP/STL), BOM, netlist, placement data     |
| **DRC**       | 8     | Design rules, DRC checks, net classes, constraints                 |
| **SCHEMATIC** | 9     | Edit/delete components, connections, netlist generation             |
| **LIBRARY**   | 11    | Browse, create, register footprint/symbol libraries                |
| **ROUTING**   | 2+    | Vias, copper pours, pad-to-pad routing                             |

---

## 2. Workflows

### 2.1 Schematic-First (Recommended!)

```
create_project(path, name)
  → add_schematic_component() × N       # Place components
  → add_schematic_connection() × M      # Connect pins
  → connect_to_net() × K                # Power nets (VCC, GND, +5V)
  → add_schematic_net_label()            # Signal labels
  → sync_schematic_to_board()            # Netlist → PCB (F8)
  → set_board_size() + add_board_outline()
  → place_component() × N               # Position footprints
  → route_trace() × M                   # Route traces
  → add_via()                            # Layer change
  → add_copper_pour()                    # GND plane
  → run_drc()                            # Verification
  → export_gerber()                      # Manufacturing
```

### 2.2 Quick-PCB (Bottom-Up, for simple boards)

```
create_project() → set_board_size() → add_board_outline()
  → place_component() × N → add_net() → route_trace() × N
  → add_copper_pour() → run_drc() → export_gerber()
```

### 2.3 Passthrough Workflow (Adapter boards, FFC/FPC)

```
connect_passthrough(J1→J2)           # Connect all pins 1:1
  → sync_schematic_to_board()        # Import nets
  → route_pad_to_pad() × N           # Auto-routing with vias
  → snapshot_project("v1", "ok")     # Checkpoint
```

### 2.4 Cost Optimization (JLCPCB)

```
export_bom()
  → download_jlcpcb_database()       # 2.5M+ parts, local
  → search_jlcpcb_parts() per part
  → suggest_jlcpcb_alternatives()    # Cheaper alternatives
  → enrich_datasheets()              # Link datasheets
```

---

## 3. Critical Rules for Tool Usage

### File Paths

- **Always use absolute paths** (e.g. `/Users/roroor/Documents/...`)
- Project must be **loaded** before board/schematic operations are possible

### Symbol Loading (Schematic)

- Format: `"library": "Device", "type": "R"` or `"library": "Amplifier_Operational", "type": "LM358"`
- Dynamic loading: access to **all ~10,000 KiCad symbols** without configuration
- Fallback templates for: R, C, L, LED, D, Q_NPN, Q_PNP, U, J, SW, F, Crystal, Transformer

### Pin Connections (Schematic)

- Pin positions are **automatically detected** (rotation-dependent: 0°, 90°, 180°, 270°)
- Routing options: `direct`, `orthogonal_h`, `orthogonal_v`
- Power symbols: VCC, GND, +3V3, +5V are treated as special symbols

### Routing (PCB)

- `route_trace()` is **single-layer** — for multi-layer use `route_pad_to_pad()`
- Configure trace widths and via sizes beforehand via `set_design_rules()`
- Always run `run_drc()` after routing

### Checkpoints

- Use `snapshot_project()` regularly — saves state + generates PDF
- Always create a snapshot before major changes

---

## 4. Schematic Design

### General Rules

- **Signal flow left → right**: inputs on the left, outputs on the right
- **Power symbols**: VCC/+V at top, GND at bottom — always consistent
- **One symbol per function**: no nested functions in a single symbol
- **Hierarchical sheets** for modular designs (e.g. one sheet per amplifier channel)

### Net Naming

- **Power nets**: `VCC`, `GND`, `+5V`, `+3V3`, `+12V`, `V_BAT`
- **Audio signals**: `AUDIO_IN_L`, `AUDIO_IN_R`, `AUDIO_OUT_L`, `AUDIO_OUT_R`, `AUDIO_GND`
- **Differential pairs**: suffix `_P`/`_N` or `+`/`-`

### Decoupling (3 stages)

1. **HF decoupling** (100nF C0G): directly at IC pin, shortest path to VCC and GND (<3mm)
2. **Local decoupling** (1–10µF ceramic X5R/X7R): per supply island, <20mm from IC
3. **Bulk capacitance** (10–100µF electrolytic): at board supply input

Placement from IC outward: 100nF directly at pin → 1µF behind it → 10µF at supply rail. Via directly from capacitor GND pad to ground plane. For audio ICs: place decoupling capacitors on B.Cu directly beneath the IC.

### Audio-Specific Schematic Rules

- **No X7R/X5R in the audio signal path** — microphonic effect! Use only C0G or film
- **Coupling capacitors**: film or C0G, $f_{-3dB} = \frac{1}{2\pi R C}$ — for 20 Hz at 10 kΩ load ≥ 0.8 µF
- **Feedback networks**: metal film resistors (±1%, ≤50 ppm/°C) for gain setting
- **Zobel network**: 10 Ω + 100 nF in series at amplifier output (load impedance stabilization)
- **Muting circuit**: power-on/power-off muting to prevent pop/click noise
- **EMI filter**: ferrite beads between digital and analog supply

### Component Selection for Audio Quality

#### Resistors

| Type                       | Application            | Characteristics                             |
| -------------------------- | ---------------------- | ------------------------------------------- |
| **Metal film (thin film)** | Gain setting, feedback | Lowest noise, ±1%, ≤50 ppm/°C              |
| **Metal glaze (thick film)** | General purpose      | Standard, acceptable                        |
| **Carbon film**            | ❌ Avoid               | Voltage-dependent → nonlinear distortion    |

In the audio signal path, choose resistor values as low as possible (1k–10 kΩ).

#### Capacitors

| Type                  | Application             | Notes                                    |
| --------------------- | ----------------------- | ---------------------------------------- |
| **C0G/NP0 MLCC**     | Decoupling, filter      | Ideal for audio — no microphonic effect  |
| **Polypropylene film** | Signal coupling, filter | Lowest dissipation factor, excellent     |
| **X7R/X5R MLCC**     | ⚠️ Decoupling only      | Microphonics + DC bias derating up to -80% |
| **Electrolytic**      | Bulk decoupling         | Supply only, not in signal path          |

#### Op-Amps

- **Low-noise**: $e_n$ < 5 nV/√Hz (e.g. OPA1612, NE5532, LME49710)
- **Slew rate**: ≥ 10 V/µs; **PSRR**: ≥ 80 dB at 1 kHz

#### Voltage Regulators

- **Low-noise LDO** for analog supply (< 10 µV RMS, e.g. TPS7A47, LT3045)
- **No switching regulators** directly for audio — if needed: switching regulator → LC filter → LDO

---

## 5. PCB Layout & Routing

### Ground Concept (most important rule!)

- **Unbroken GND plane on B.Cu** — NO physical split
- Separate analog, digital, and power return currents through **component placement**, not through slots
- Splits force return current detours → larger loop areas → more noise coupling
- **Star point**: all ground returns meet at one point (ideally at the supply input)
- **Route return current paths deliberately**: at low frequencies, return current flows on the path of least resistance; at HF, directly beneath the signal trace
- **No traces cutting through the ground plane under ICs**
- Power GND return currents must **not flow through the analog area**

### Component Placement

1. **Connectors** first — they define the board geometry
2. **ICEpower module / power components** — thermally correct, dedicated area
3. **Audio ICs** in a dedicated analog area, short connections
4. **Decoupling capacitors** directly at the associated IC
5. **Digital components** spatially separated from the analog area
6. **Passives, test points** in remaining areas

Additional rules:

- **Align components to 0.5mm / 1.27mm grid**
- **Same orientation** for R/C (facilitates assembly)
- **Keep heat sources** away from temperature-sensitive components

### Routing Guidelines

#### Trace Widths

| Application       | Recommended | Current (1oz Cu, 10°C ΔT) |
| ----------------- | ----------- | ------------------------- |
| Signal (standard) | 0.2–0.25mm  | ~0.3A                     |
| Audio signal      | 0.3mm       | —                         |
| Power (1A)        | 0.5mm       | ~1A                       |
| Power (3A+)       | 1.5mm+      | ~3A+                      |
| Speaker           | 1.5mm       | high current              |

#### Via Design

| Parameter    | JLCPCB Min | Standard |
| ------------ | ---------- | -------- |
| Via pad      | 0.45mm     | 0.6mm    |
| Via drill    | 0.2mm      | 0.3mm    |
| Annular ring | 0.125mm    | 0.15mm   |

#### Audio Signal Routing

- **Audio traces on top layer** (keep B.Cu free for unbroken ground plane)
- **No vias in the audio signal path** — every via is an impedance discontinuity
- **Guard traces**: GND traces on both sides of sensitive audio input signals, with vias to ground plane every 5 mm
- **Via stitching**: GND vias on both sides along audio traces (every 5–10 mm)
- **No crossings** — if unavoidable, cross at right angles (90°)
- **Audio traces never parallel to digital signals** (minimum spacing ≥ 3 mm, to power ≥ 5 mm)
- **Differential pairs**: equal length, equal spacing, route as a pair

#### General Routing Rules

- **45° angles** instead of 90° corners
- **No stubs** (open trace ends)
- **Ground plane**: GND pour on B.Cu, minimize interruptions
- **Via stitching**: distribute GND vias regularly
- **Teardrops** at pad/via transitions enabled

### Noise Source Management

- **Switching regulators ≥ 20 mm** from audio input stage; prefer shielded inductors
- **No switching regulator traces under audio ICs**
- **Clock sources far away** from audio inputs; series damping resistors (22–47 Ω) on clock lines
- **EMI filter** (π-filter: C-L-C) between switching regulator and audio supply

### Input and Output Protection

- **ESD**: TVS diodes (bidirectional) on all external audio connectors
- **DC blocking**: coupling capacitor (film/C0G, ≥ 1 µF) at input
- **EMI low-pass**: series resistor (47–100 Ω) + ceramic cap (100 pF–1 nF) to GND at input
- **Output**: Zobel network; for Class-D: LC output filter per datasheet

### Silkscreen

- Minimum **0.8 mm text height**, 0.15 mm stroke width
- **Pin 1 and polarity markings** on ICs, electrolytics, diodes
- **No silkscreen on pads**
- Board info: project name, version, date

---

## 6. ICEpower Module Integration

- **Follow datasheet pins exactly**: pinout varies between modules
- **Connector footprints**: choose exactly per module datasheet
- **Ground connection**: low-impedance, wide copper areas
- **Supply inputs**: adequately sized traces (consider current!)
- **Keep signal paths short**: audio inputs close to the module
- **Bypass capacitors**: directly at the module connector
- **ENABLE/MUTE pins**: circuit per datasheet (pull-up/pull-down + RC delay)
- **Sense lines**: Kelvin connection directly at speaker terminal (if required)

### Thermal Design

- **Thermal pads**: via array (minimum 5×5, drill 0.3 mm, pitch 1.0–1.2 mm)
- **Copper areas**: use top + bottom for heat dissipation
- **No components over hot spots**
- **Heatsink**: M3 screw mounting with thermal pad provision

---

## 7. JLCPCB Design Rules & Manufacturing

### Minimum Design Rules

| Rule               | Minimum | Recommended |
| ------------------ | ------- | ----------- |
| Trace width        | 0.1mm   | ≥ 0.15mm    |
| Trace clearance    | 0.1mm   | ≥ 0.15mm    |
| Annular ring       | 0.125mm | ≥ 0.15mm    |
| Drill (PTH)        | 0.2mm   | ≥ 0.3mm     |
| Pad size (min)     | 0.45mm  | ≥ 0.6mm     |
| Board edge to copper | 0.2mm | ≥ 0.3mm     |
| Silkscreen height  | 0.8mm   | ≥ 1.0mm     |

### Net Classes

| Net Class    | Clearance | Track Width | Via Size | Via Drill | Description                 |
| ------------ | --------- | ----------- | -------- | --------- | --------------------------- |
| Default      | 0.2mm     | 0.25mm      | 0.6mm    | 0.3mm     | Standard signals            |
| Power        | 0.2mm     | 0.5mm       | 0.8mm    | 0.4mm     | Supply, high current        |
| Audio_Input  | 0.25mm    | 0.3mm       | 0.6mm    | 0.3mm     | Sensitive audio inputs      |
| Audio_Output | 0.2mm     | 0.5mm       | 0.6mm    | 0.3mm     | Audio outputs               |
| Audio_Power  | 0.2mm     | 0.8mm       | 0.8mm    | 0.4mm     | Analog supply               |
| Speaker      | 0.3mm     | 1.5mm       | 0.8mm    | 0.4mm     | Speaker outputs             |
| HV           | 0.5mm     | 0.3mm       | 0.8mm    | 0.4mm     | > 50V signals               |

### Custom Design Rules (kicad_dru)

```
(version 1)

# Power
(rule power_clearance
    (condition "A.hasNetclass('Power')")
    (constraint clearance (min 0.25mm)))
(rule power_width
    (condition "A.hasNetclass('Power')")
    (constraint track_width (min 0.5mm)))

# HV (ICEpower)
(rule hv_clearance
    (condition "A.hasNetclass('HV')")
    (constraint clearance (min 0.5mm)))

# Audio
(rule audio_input_clearance
    (condition "A.hasNetclass('Audio_Input')")
    (constraint clearance (min 0.25mm)))
(rule audio_digital_separation
    (condition "A.hasNetclass('Audio_Input') && B.hasNetclass('Default')")
    (constraint clearance (min 0.5mm)))
(rule audio_power_width
    (condition "A.hasNetclass('Audio_Power')")
    (constraint track_width (min 0.5mm)))
(rule speaker_width
    (condition "A.hasNetclass('Speaker')")
    (constraint track_width (min 1.0mm)))

# Board-Edge
(rule board_edge
    (constraint edge_clearance (min 0.3mm)))
```

### Gerber Export

**Layers (2-layer):** F.Cu, B.Cu, F.Paste, B.Paste, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, Edge.Cuts

**Options:** Protel Extensions ✅ | Tent Vias ✅ | Subtract Soldermask from Silkscreen ✅ | Check Zone Fills ✅

**Drill:** Millimeters, Decimal, Absolute Origin

### SMT Assembly (JLCPCB)

- **Prefer Basic Parts** ($0 setup) — Extended Parts cost $3/unique part
- **Fiducials**: minimum 3 (1 mm pad, 2 mm opening) for SMT assembly
- Export: `export_bom` + `export_position_file`

---

## 8. Pre-Manufacturing Checklist

### Schematic

- [ ] ERC error-free (`run_erc`)
- [ ] No loose/unconnected components — all pins connected or `no_connect`
- [ ] Low-noise op-amps selected
- [ ] Decoupling: 100 nF C0G + 10 µF at every IC supply pin
- [ ] Feedback resistors: metal film, ±1%
- [ ] No X7R/X5R in the audio signal path
- [ ] Zobel network at amplifier output
- [ ] ESD protection on all external connectors
- [ ] Muting circuit present
- [ ] Analog and digital supply separately regulated

### PCB Layout

- [ ] DRC error-free (`run_drc`)
- [ ] No loose/unconnected footprints — 0 Unconnected Items
- [ ] All nets connected (no ratsnest lines)
- [ ] Ground plane unbroken under audio signal paths
- [ ] Audio traces on top layer, no unnecessary vias
- [ ] Guard traces around sensitive audio inputs
- [ ] Switching regulators ≥ 20 mm from audio input stage
- [ ] Star-point ground correctly implemented
- [ ] Decoupling capacitors directly at IC pins (< 3 mm)
- [ ] Thermal vias under thermal pads
- [ ] Via stitching along audio traces

### Manufacturing

- [ ] Board outline closed (Edge.Cuts)
- [ ] Vias tented
- [ ] Silkscreen not on pads
- [ ] Fiducials present (if SMT assembly)
- [ ] Gerber + drill exported and verified in viewer
- [ ] BOM + centroid exported
- [ ] JLCPCB Basic Parts preferred

### Audio Quality

- [ ] SNR target defined (> 100 dB)
- [ ] THD+N budget (< 0.01% at 1 kHz)
- [ ] Crosstalk between channels minimized (> 70 dB)
- [ ] No microphonic-sensitive components in signal path

---

## 9. Kern-Prinzipien — IMMER befolgen!

### Keine losen / unverbundenen Bauteile — NIEMALS!

- **Jedes elektrische Bauteil** im Schaltplan und auf dem PCB **muss vollständig verbunden** sein — keine offenen Pins, keine floating Components
- **Schaltplan**: Alle Pins eines Bauteils müssen entweder an ein Netz angeschlossen, explizit als `no_connect` markiert oder über Power-Flags versorgt sein
- **PCB**: Kein Footprint darf unverbundene Pads (Ratsnest-Linien) haben — alle Netze müssen geroutet sein
- **Validierung**: Nach jeder Änderung ERC/DRC ausführen und sicherstellen, dass 0 Unconnected Items existieren
- **Aufräumen**: Nicht mehr benötigte Bauteile sofort aus Schaltplan UND PCB entfernen — keine "Leichen" im Design belassen

### KEINE Annahmen — NIEMALS!

- **Keine Werte raten**: Pin-Belegungen, Spannungen, Ströme, Footprints, Bauteilwerte — IMMER aus Datenblatt oder Recherche ableiten
- **Keine Schaltungs-Annahmen**: Beschaltung, Pull-Up/Down-Werte, Filter-Dimensionierung — IMMER berechnen oder aus Datenblatt/Appnotes entnehmen
- **Keine Footprint-Annahmen**: Package-Maße, Pin-Pitch, Pad-Größen — IMMER Datenblatt prüfen
- **Keine Netz-Annahmen**: Pin-Funktionen, Netz-Zuordnungen — IMMER Datenblatt-Pinout lesen

### Recherche-Pflicht

1. **Datenblätter lesen** — vor jeder Bauteil-Entscheidung das Datenblatt konsultieren (fetch_webpage oder lokale Dateien in datasheets/)
2. **Application Notes prüfen** — Hersteller-Empfehlungen für Beschaltung haben Vorrang
3. **Berechnungen durchführen** — Filterwerte, Strombelastung, Wärmeableitung etc. immer nachrechnen
4. **Referenzdesigns suchen** — Evaluation-Boards und Referenzschaltungen als Basis nutzen

### Wenn Recherche nicht weiterkommt → FRAGEN!

- **Interaktiv nachfragen** statt raten — lieber einmal zu viel fragen als einmal falsch annehmen
- **Plan kommunizieren**: Was wurde recherchiert, was fehlt, welche Optionen gibt es
- **Entscheidungen explizit machen**: "Laut Datenblatt S.12 empfiehlt der Hersteller X" statt stillschweigend X einsetzen

### Arbeitsweise bei neuen Bauteilen/Schaltungen

1. Datenblatt beschaffen und relevante Seiten lesen
2. Typische Applikationsschaltung aus Datenblatt extrahieren
3. Werte berechnen/verifizieren (nicht blind aus Datenblatt kopieren wenn Randbedingungen anders sind)
4. Bei Unklarheiten: User fragen mit konkreten Optionen + Begründung
5. Erst nach Klärung implementieren

---

## 10. KiCad + AI — Learnings & Optimierungen

### MCP Server vs. Direkte Dateimanipulation

- MCP Server ist **für einfache Boards brauchbar**, für komplexe Projekte **unzuverlässig**
- Ab ~50+ Bauteile oder Multi-Unit-Symbolen häufen sich Bugs exponentiell
- **Bewährter Ansatz**: Python-Skripte die .kicad_sch direkt als S-Expression manipulieren + kicad-cli für ERC/Netlist
- MCP nützlich für: Schnelle Prototypen, Library-Suche, Footprint-Info, Einzelbauteil-Platzierung

### Wiederkehrende Probleme

#### Terminal-Heredoc-Korruption

- zsh korruptiert inline Python/heredoc in Copilot-Terminal
- **Fix**: IMMER .py-Datei schreiben → `python3 datei.py` ausführen
- Nie `python3 -c "..."` oder `cat << 'EOF'` verwenden

#### Greedy Regex über Symbol-Grenzen

- **Fix**: Balanced-Paren-Block zuerst extrahieren, dann innerhalb suchen

#### lib_symbols Cache Naming

- Sub-Symbole im Cache dürfen KEINEN Library-Prefix haben
- Falsch: `(symbol "Connector_Audio:AudioJack2_0_1")` → Richtig: `(symbol "AudioJack2_0_1")`

#### Pin-Position-Berechnung bei Rotation

- Formel: symbol_pos + rotate(local_pin_pos, symbol_rotation)
- KiCad Y-Achse invertiert: schematic_y = symbol_y - rotated_y
- **IMMER** lib_symbols-Cache lesen und Pin `(at x y angle)` extrahieren!

#### Single-Line S-Expression Format

- MCP erzeugt .kicad_sch als einzeilige Datei (kein \n)
- replace_string_in_file unzuverlässig → Python-Skripte verwenden
- Klammer-Balance-Check nach jeder Manipulation obligatorisch

#### Pin-Namen sind bibliotheksabhängig

- Device:R → Pins "1"/"2" (Nummern), AudioJack2 → "T"/"S", XLR3 → "1"/"2"/"3"/"G"
- Regex `\d+` matcht keine Buchstaben-Pins → `[^"]+` verwenden

#### Wire-Endpunkt-Regel (kritisch)

- KiCad eeschema verbindet Pins NUR an Wire-ENDPUNKTEN oder Junctions
- Pins mitten auf einem Wire-Segment werden NICHT verbunden
- kicad-cli ERC ist toleranter → **eeschema ERC ist maßgeblich!**
- **Fix**: Drähte an JEDEM Pin-Endpunkt aufteilen (Segmente statt ein langer Draht)

#### Koordinaten-Format in .kicad_sch

- Ganze Zahlen werden als `285.0` geschrieben (nicht `285`)
- Python fmt: `f"{v:.1f}"` für Integer-Werte

#### Einfügen in .kicad_sch: Scope-Problem

- `rfind('\n)')` findet NICHT den kicad_sch-Closer! → Bracket-Depth-Counting verwenden
- Validation: Depth am Einfügepunkt muss 1 sein (innerhalb kicad_sch)

#### Symbol instances-Sektion

- Jedes Symbol in KiCad 9 MUSS eine `(instances ...)` Sektion haben
- Symbole OHNE instances werden von eeschema als nicht-annotiert behandelt
- kicad-cli ERC erkennt diesen Fehler NICHT — nur eeschema GUI!

### Optimale Workflows

#### Schaltplan-Erstellung (komplexe Projekte)

1. MCP: Projekt erstellen, initiale Bauteile platzieren
2. Python-Skript: Kanäle replizieren, Bulk-Verdrahtung
3. kicad-cli: ERC + Netlist-Export nach jeder Änderung
4. Quality-Gate-Skript: Automatische Netz-Validierung

#### Validierung (nach jeder Änderung)

1. Klammer-Balance prüfen
2. kicad-cli Netlist-Export (testet Parser)
3. kicad-cli ERC (Baseline-Vergleich)
4. Netz-Verbindungen im Netlist prüfen

### PCB-Routing: Freerouting-Workflow (IMMER so machen!)

- Eigene Routing-Skripte funktionieren NICHT (Shorts mit GND-Zonen, keine Hinderniserkennung)

#### Schritt 1: Netzklassen zuweisen (.kicad_pro)

#### Schritt 2: Design Rules (.kicad_dru)

#### Schritt 3: Freerouting (Autorouter)

```bash
pcbnew.ExportSpecctraDSN(board, "/tmp/board.dsn")
java -jar /tmp/freerouting.jar -de /tmp/board.dsn -do /tmp/board.ses -mp 20 -mt 4
pcbnew.ImportSpecctraSES(board, "/tmp/board.ses")
pcbnew.SaveBoard("/tmp/board-routed.kicad_pcb", board)  # NUR auf temp!
```

#### Schritt 4: Text-Merge Routing in Original (Segments + Vias extrahieren, Net-IDs mappen)

#### Schritt 5: Zone-Fill via pcbnew + Text-Merge

#### Schritt 6: DRC via kicad-cli

### Zone-Probleme und Lösungen

- **starved_thermal** → Zone auf `connect_pads yes` (Solid) umstellen
- **pcbnew.SaveBoard()** korruptiert KiCad 9 Dateien — IMMER Text-Merge verwenden
- **kicad-cli füllt Zonen nicht** — pcbnew Python API nötig für Zone-Fill

### User-Präferenzen

- **NIEMALS** .bak-Kopien anlegen — git für Versionierung nutzen
- **Keine temporären Skripte in /tmp/** — Skripte in scripts/ ablegen

---

## 11. KiCad MCP Server Setup

### MCP Server

- Repo: ~/MCP/KiCAD-MCP-Server/
- Entry: dist/index.js (Node.js), Python backend: python/kicad_interface.py
- 64 tools: ~17 direct + ~47 routed (7 Kategorien) + 4 router tools
- Router-Pattern: list_tool_categories → get_category_tools → execute_tool

### Grid/Raster

- MCP-Server hat **KEIN Grid/Snap** — Koordinaten werden als rohe Floats durchgereicht
- **Regel**: Koordinaten IMMER als Vielfache von **1.27mm** (50mil) oder **2.54mm** (100mil)
- Pin-Offsets berücksichtigen: LM4562 Pins bei ±7.62mm (6×1.27) und ±2.54mm (2×1.27)

### PCB Text Manipulation — Kritische Regeln (KiCad 9)

- **NEVER** pcbnew.SaveBoard() auf die echte PCB-Datei — korruptiert KiCad 9 Dateien
- Footprint-Library-Prefix: pcbnew generiert `"R_0805_2012Metric"` → muss `"Resistor_SMD:R_0805_2012Metric"` sein
- Net-ID-Remapping nach pcbnew-Generierung obligatorisch
- GND Zone: `(connect_pads` (ohne Keyword) = thermal relief; `(connect_pads thermal` ist INVALID

### MCP API Kurzreferenz

| Tool                       | Wichtige Parameter                                                |
| -------------------------- | ----------------------------------------------------------------- |
| `add_schematic_component`  | library, type, reference, value, x, y, footprint — KEIN rotation! |
| `connect_to_net`           | reference, netName, **pinName** (nicht "pin"!)                    |
| `add_schematic_connection` | sourceRef, sourcePin, targetRef, targetPin, routing               |
| `add_schematic_net_label`  | netName, position=[x,y] (Array!), labelType, orientation          |

### Pin-Referenz Schlüssel-Symbole

| Symbol        | Pins                                       |
| ------------- | ------------------------------------------ |
| LM4562 Unit 1 | 1=Out, 2=−In, 3=+In                        |
| LM4562 Unit 2 | 5=+In, 6=−In, 7=Out                        |
| LM4562 Unit 3 | 4=V−, 8=V+                                 |
| XLR3_Ground   | Pins: 1, 2, 3, G (Namen alle `~`)          |
| TEL5-2422     | 1=+VIN, 7=−VIN, 24=+VOUT, 18=COM, 14=−VOUT |
| ADP7118       | 8=VIN, 2=VOUT, 1=EN, 4=GND                 |

### Bekannte Bugs & Fixes

- **Issue #52**: `extends`-basierte Symbole brechen alles — Fix: PR #53 merged
- **Issue #40**: `add_schematic_component` korrumpiert .kicad_sch — Fix: merged
- **PinLocator Cache Bug**: Lokal gefixt — `invalidate_cache()` hinzugefügt

---

## 12. Projekt-Status

### Schaltplan-Status

- **242 Symbole**: 104 R, 64+4 C, 24 D (TVS), 15 U, 13 J, 6 SW
- **143 Netze**, Schaltplan exportiert sauber
- **ERC**: 0 Fehler (von 115→66→0 reduziert), 890 Warnungen (838 off-grid, akzeptabel)
- Alle Fixes (F1-F10) verifiziert und bestanden

### PCB Routing-Status (Commit bf62bd0)

- **0 Errors, 0 Unconnected, 198 Warnings** (alle akzeptabel)
- 1543 Trace-Segments + 476 Vias via Freerouting v2.0.1
- 2 GND-Zonen: F.Cu (solid connect) + B.Cu (thermal)
- 269 Footprints, 135 Nets in 5 Klassen

#### DRC Breakdown (198 Warnings)

- 138× holes_co_located, 27× silk_edge_clearance, 11× silk_overlap
- 10× silk_over_copper, 9× hole_to_hole, 3× via_dangling

#### Netzklassen

| Klasse       | Nets | Track  | Clearance |
| ------------ | ---- | ------ | --------- |
| Default      | 62   | 0.25mm | 0.2mm     |
| Audio_Input  | 30   | 0.3mm  | 0.25mm    |
| Audio_Output | 36   | 0.5mm  | 0.2mm     |
| Audio_Power  | 0    | 0.8mm  | 0.2mm     |
| Power        | 7    | 0.5mm  | 0.2mm     |

### Nächste Schritte

1. Dangling Vias entfernen (3 Stück)
2. Gerber + Drill exportieren
3. BOM + Bestückungsdaten exportieren
4. Visuelle Prüfung in KiCad

### Wire-Dangling-Fix Referenz

- Wire-to-pin-Verbindungen funktionieren NUR zuverlässig mit mindestens einem Net-Label
- Fix: `(label "NET_NAME" (at x y 0) ...)` an jedem Dangling-Endpunkt hinzufügen

### Kanal-Netnamen (11 Netze × 6 Kanäle = 66)

CHn_INV_IN, CHn_SW_OUT_1/2/3, CHn_BUF_DRIVE, CHn_GAIN_FB, CHn_OUT_DRIVE, CHn_OUT_PROT_HOT, CHn_OUT_PROT_COLD, CHn_EMI_HOT, CHn_EMI_COLD

### Schlüssel-Koordinaten

- Kanäle: CY = 110 + (ch-1) × 80, für ch=1..6
- Input-Protection: X_PROT = 280
- Output-Zobel HOT: X=265, COLD: X=280

### S-Expression Templates

```
Symbol: (symbol (lib_id "LIB") (at X Y A) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "UUID") (property "Reference" ...) ...)
Wire:   (wire (pts (xy X1 Y1) (xy X2 Y2)) (stroke (width 0) (type default)) (uuid "UUID"))
Label:  (label "NAME" (at X Y A) (fields_autoplaced yes) (effects ...) (uuid "UUID"))
```
