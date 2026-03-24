# KiCad PCB Design — Copilot Instructions

## Project: Aurora DSP IcePower Booster

- **Amplifier board** based on ICEpower modules
- **KiCad 9** project (schematic + PCB)
- **Target manufacturing**: JLCPCB (2-layer standard, HASL, FR-4)
- **Language**: English for all comments and explanations

---

## 1. Core Principles — ALWAYS follow!

### No Loose / Unconnected Components — NEVER!

- **Every electrical component** in the schematic and on the PCB **must be fully connected** — no open pins, no floating components
- **Schematic**: all pins of a component must be either connected to a net, explicitly marked as `no_connect`, or supplied via power flags
- **PCB**: no footprint may have unconnected pads (ratsnest lines) — all nets must be routed
- **Validation**: run ERC/DRC after every change and ensure 0 Unconnected Items
- **Cleanup**: remove unused components from schematic AND PCB immediately — no "dead" parts in the design

### NO Assumptions — NEVER!

- **Never guess values**: pinouts, voltages, currents, footprints, component values — ALWAYS derive from datasheet or research
- **No circuit assumptions**: peripheral circuits, pull-up/pull-down values, filter dimensioning — ALWAYS calculate or take from datasheet/appnotes
- **No footprint assumptions**: package dimensions, pin pitch, pad sizes — ALWAYS verify against datasheet
- **No net assumptions**: pin functions, net assignments — ALWAYS read the datasheet pinout

### Mandatory Research

1. **Read datasheets** — consult the datasheet before every component decision (fetch_webpage or local files in datasheets/)
2. **Check application notes** — manufacturer recommendations for circuit design take priority
3. **Perform calculations** — filter values, current capacity, thermal dissipation etc. must always be calculated
4. **Search reference designs** — use evaluation boards and reference schematics as a basis

### When Research Hits a Dead End → ASK!

- **Ask interactively** instead of guessing — better to ask once too many than to assume once incorrectly
- **Communicate the plan**: what was researched, what is missing, what options exist
- **Make decisions explicit**: "Per datasheet p.12, the manufacturer recommends X" instead of silently using X

### Process for New Components/Circuits

1. Obtain the datasheet and read the relevant pages
2. Extract the typical application circuit from the datasheet
3. Calculate/verify values (do not blindly copy from datasheet if operating conditions differ)
4. If uncertain: ask the user with concrete options + rationale
5. Only implement after clarification

---

## 2. Schematic Design

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

| Type                         | Application            | Characteristics                          |
| ---------------------------- | ---------------------- | ---------------------------------------- |
| **Metal film (thin film)**   | Gain setting, feedback | Lowest noise, ±1%, ≤50 ppm/°C            |
| **Metal glaze (thick film)** | General purpose        | Standard, acceptable                     |
| **Carbon film**              | ❌ Avoid               | Voltage-dependent → nonlinear distortion |

In the audio signal path, choose resistor values as low as possible (1k–10 kΩ).

#### Capacitors

| Type                   | Application             | Notes                                      |
| ---------------------- | ----------------------- | ------------------------------------------ |
| **C0G/NP0 MLCC**       | Decoupling, filter      | Ideal for audio — no microphonic effect    |
| **Polypropylene film** | Signal coupling, filter | Lowest dissipation factor, excellent       |
| **X7R/X5R MLCC**       | ⚠️ Decoupling only      | Microphonics + DC bias derating up to -80% |
| **Electrolytic**       | Bulk decoupling         | Supply only, not in signal path            |

#### Op-Amps

- **Low-noise**: $e_n$ < 5 nV/√Hz (e.g. OPA1612, NE5532, LME49710)
- **Slew rate**: ≥ 10 V/µs; **PSRR**: ≥ 80 dB at 1 kHz

#### Voltage Regulators

- **Low-noise LDO** for analog supply (< 10 µV RMS, e.g. TPS7A47, LT3045)
- **No switching regulators** directly for audio — if needed: switching regulator → LC filter → LDO

---

## 3. PCB Layout & Routing

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

### ICEpower Module Integration

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

## 4. JLCPCB Manufacturing

### Minimum Design Rules

| Rule                 | Minimum | Recommended |
| -------------------- | ------- | ----------- |
| Trace width          | 0.1mm   | ≥ 0.15mm    |
| Trace clearance      | 0.1mm   | ≥ 0.15mm    |
| Annular ring         | 0.125mm | ≥ 0.15mm    |
| Drill (PTH)          | 0.2mm   | ≥ 0.3mm     |
| Pad size (min)       | 0.45mm  | ≥ 0.6mm     |
| Board edge to copper | 0.2mm   | ≥ 0.3mm     |
| Silkscreen height    | 0.8mm   | ≥ 1.0mm     |

### Net Classes

| Net Class    | Clearance | Track Width | Via Size | Via Drill | Description            |
| ------------ | --------- | ----------- | -------- | --------- | ---------------------- |
| Default      | 0.2mm     | 0.25mm      | 0.6mm    | 0.3mm     | Standard signals       |
| Power        | 0.2mm     | 0.5mm       | 0.8mm    | 0.4mm     | Supply, high current   |
| Audio_Input  | 0.25mm    | 0.3mm       | 0.6mm    | 0.3mm     | Sensitive audio inputs |
| Audio_Output | 0.2mm     | 0.5mm       | 0.6mm    | 0.3mm     | Audio outputs          |
| Audio_Power  | 0.2mm     | 0.8mm       | 0.8mm    | 0.4mm     | Analog supply          |
| Speaker      | 0.3mm     | 1.5mm       | 0.8mm    | 0.4mm     | Speaker outputs        |
| HV           | 0.5mm     | 0.3mm       | 0.8mm    | 0.4mm     | > 50V signals          |

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

### SMT Assembly

- **Prefer Basic Parts** ($0 setup) — Extended Parts cost $3/unique part
- **Fiducials**: minimum 3 (1 mm pad, 2 mm opening) for SMT assembly
- Export: `export_bom` + `export_position_file`

### Pre-Manufacturing Checklist

#### Schematic

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

#### PCB Layout

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

#### Manufacturing

- [ ] Board outline closed (Edge.Cuts)
- [ ] Vias tented
- [ ] Silkscreen not on pads
- [ ] Fiducials present (if SMT assembly)
- [ ] Gerber + drill exported and verified in viewer
- [ ] BOM + centroid exported
- [ ] JLCPCB Basic Parts preferred

#### Audio Quality

- [ ] SNR target defined (> 100 dB)
- [ ] THD+N budget (< 0.01% at 1 kHz)
- [ ] Crosstalk between channels minimized (> 70 dB)
- [ ] No microphonic-sensitive components in signal path

---

## 5. KiCad MCP Server

### Architecture

The KiCad MCP Server provides **64 tools**, organized using the **Router Pattern**:

- **~17 Direct Tools** — always visible, for frequent operations
- **~47 Routed Tools** — in 7 categories, accessible via router
- **4 Router Tools** — for discovery and execution

### Server Setup

- Repo: ~/MCP/KiCAD-MCP-Server/
- Entry: dist/index.js (Node.js), Python backend: python/kicad_interface.py
- Router pattern: list_tool_categories → get_category_tools → execute_tool

### Critical Rules

#### File Paths

- **Always use absolute paths** (e.g. `/Users/roroor/Documents/...`)
- Project must be **loaded** before board/schematic operations are possible

#### Grid/Snap

- MCP Server has **NO grid/snap** — coordinates are passed through as raw floats
- **Rule**: coordinates ALWAYS as multiples of **1.27mm** (50mil) or **2.54mm** (100mil)
- Account for pin offsets: LM4562 pins at ±7.62mm (6×1.27) and ±2.54mm (2×1.27)

#### Symbol Loading (Schematic)

- Format: `"library": "Device", "type": "R"` or `"library": "Amplifier_Operational", "type": "LM358"`
- Dynamic loading: access to **all ~10,000 KiCad symbols** without configuration
- Fallback templates for: R, C, L, LED, D, Q_NPN, Q_PNP, U, J, SW, F, Crystal, Transformer

#### Pin Connections (Schematic)

- Pin positions are **automatically detected** (rotation-dependent: 0°, 90°, 180°, 270°)
- Routing options: `direct`, `orthogonal_h`, `orthogonal_v`
- Power symbols: VCC, GND, +3V3, +5V are treated as special symbols

#### Routing (PCB)

- `route_trace()` is **single-layer** — for multi-layer use `route_pad_to_pad()`
- Configure trace widths and via sizes beforehand via `set_design_rules()`
- Always run `run_drc()` after routing

#### PCB Text Manipulation (KiCad 9)

- **NEVER** pcbnew.SaveBoard() on the real PCB file — corrupts KiCad 9 files
- Footprint library prefix: pcbnew generates `"R_0805_2012Metric"` → must be `"Resistor_SMD:R_0805_2012Metric"`
- Net ID remapping after pcbnew generation is mandatory
- GND Zone: `(connect_pads` (without keyword) = thermal relief; `(connect_pads thermal` is INVALID

#### Checkpoints

- Use `snapshot_project()` regularly — saves state + generates PDF
- Always create a snapshot before major changes

### Router Pattern

```
1. list_tool_categories    → Show all 7 categories
2. get_category_tools      → List tools in a category
3. search_tools            → Find tools by keyword
4. execute_tool            → Execute a routed tool
```

### Direct Tools

| Tool                      | Function                                                        |
| ------------------------- | --------------------------------------------------------------- |
| `create_project`          | Create new KiCad project (.kicad_pro + .kicad_pcb + .kicad_sch) |
| `open_project`            | Load existing project                                           |
| `save_project`            | Save project                                                    |
| `snapshot_project`        | Checkpoint with PDF rendering                                   |
| `get_project_info`        | Project metadata                                                |
| `place_component`         | Place footprint on PCB                                          |
| `move_component`          | Reposition component                                            |
| `add_net`                 | Create new net                                                  |
| `route_trace`             | Route trace (single layer)                                      |
| `set_board_size`          | Configure PCB dimensions                                        |
| `add_board_outline`       | Board outline (rectangle/circle/polygon/rounded)                |
| `get_board_info`          | Retrieve board properties                                       |
| `add_schematic_component` | Place symbol (~10,000 KiCad symbols)                            |
| `connect_passthrough`     | J1→J2 passthrough connection (all pins)                         |
| `connect_to_net`          | Connect pin to named net                                        |
| `add_schematic_net_label` | Net label in schematic                                          |
| `sync_schematic_to_board` | Schematic → PCB sync (F8)                                       |

### Routed Tool Categories

| Category      | Tools | Contents                                                        |
| ------------- | ----- | --------------------------------------------------------------- |
| **BOARD**     | 9     | Layer management, mounting holes, zones, board text, 2D preview |
| **COMPONENT** | 8     | Rotate, delete, edit, find, properties, group                   |
| **EXPORT**    | 8     | Gerber, PDF, SVG, 3D (STEP/STL), BOM, netlist, placement data   |
| **DRC**       | 8     | Design rules, DRC checks, net classes, constraints              |
| **SCHEMATIC** | 9     | Edit/delete components, connections, netlist generation         |
| **LIBRARY**   | 11    | Browse, create, register footprint/symbol libraries             |
| **ROUTING**   | 2+    | Vias, copper pours, pad-to-pad routing                          |

### API Quick Reference

| Tool                       | Key Parameters                                                  |
| -------------------------- | --------------------------------------------------------------- |
| `add_schematic_component`  | library, type, reference, value, x, y, footprint — NO rotation! |
| `connect_to_net`           | reference, netName, **pinName** (not "pin"!)                    |
| `add_schematic_connection` | sourceRef, sourcePin, targetRef, targetPin, routing             |
| `add_schematic_net_label`  | netName, position=[x,y] (array!), labelType, orientation        |

### Pin Reference — Key Symbols

| Symbol        | Pins                                       |
| ------------- | ------------------------------------------ |
| LM4562 Unit 1 | 1=Out, 2=−In, 3=+In                        |
| LM4562 Unit 2 | 5=+In, 6=−In, 7=Out                        |
| LM4562 Unit 3 | 4=V−, 8=V+                                 |
| XLR3_Ground   | Pins: 1, 2, 3, G (names all `~`)           |
| TEL5-2422     | 1=+VIN, 7=−VIN, 24=+VOUT, 18=COM, 14=−VOUT |
| ADP7118       | 8=VIN, 2=VOUT, 1=EN, 4=GND                 |

### Known Bugs & Fixes

- **Issue #52**: `extends`-based symbols break everything — Fix: PR #53 merged
- **Issue #40**: `add_schematic_component` corrupts .kicad_sch — Fix: merged
- **PinLocator Cache Bug**: fixed locally — `invalidate_cache()` added

---

## 6. Workflows

### 6.1 Schematic-First (Recommended!)

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

### 6.2 Quick-PCB (Bottom-Up, for simple boards)

```
create_project() → set_board_size() → add_board_outline()
  → place_component() × N → add_net() → route_trace() × N
  → add_copper_pour() → run_drc() → export_gerber()
```

### 6.3 Passthrough Workflow (Adapter boards, FFC/FPC)

```
connect_passthrough(J1→J2)           # Connect all pins 1:1
  → sync_schematic_to_board()        # Import nets
  → route_pad_to_pad() × N           # Auto-routing with vias
  → snapshot_project("v1", "ok")     # Checkpoint
```

### 6.4 Cost Optimization (JLCPCB)

```
export_bom()
  → download_jlcpcb_database()       # 2.5M+ parts, local
  → search_jlcpcb_parts() per part
  → suggest_jlcpcb_alternatives()    # Cheaper alternatives
  → enrich_datasheets()              # Link datasheets
```

---

## 7. KiCad + AI — Learnings & Optimizations

### MCP Server vs. Direct File Manipulation

- MCP Server is **usable for simple boards**, for complex projects **unreliable**
- Beyond ~50+ components or multi-unit symbols, bugs increase exponentially
- **Proven approach**: Python scripts that manipulate .kicad_sch directly as S-Expressions + kicad-cli for ERC/netlist
- MCP useful for: quick prototypes, library search, footprint info, single-component placement

### Recurring Issues

#### Terminal Heredoc Corruption

- zsh corrupts inline Python/heredoc in Copilot terminal
- **Fix**: ALWAYS write a .py file → run `python3 file.py`
- Never use `python3 -c "..."` or `cat << 'EOF'`

#### Greedy Regex Across Symbol Boundaries

- **Fix**: extract balanced-paren block first, then search within it

#### lib_symbols Cache Naming

- Sub-symbols in cache must NOT have a library prefix
- Wrong: `(symbol "Connector_Audio:AudioJack2_0_1")` → Correct: `(symbol "AudioJack2_0_1")`

#### Pin Position Calculation with Rotation

- Formula: symbol_pos + rotate(local_pin_pos, symbol_rotation)
- KiCad Y-axis inverted: schematic_y = symbol_y - rotated_y
- **ALWAYS** read lib_symbols cache and extract pin `(at x y angle)`!

#### Single-Line S-Expression Format

- MCP generates .kicad_sch as single-line file (no \n)
- replace_string_in_file unreliable → use Python scripts
- Bracket balance check mandatory after every manipulation

#### Pin Names Are Library-Dependent

- Device:R → Pins "1"/"2" (numbers), AudioJack2 → "T"/"S", XLR3 → "1"/"2"/"3"/"G"
- Regex `\d+` doesn't match letter pins → use `[^"]+`

#### Wire Endpoint Rule (critical)

- KiCad eeschema connects pins ONLY at wire ENDPOINTS or junctions
- Pins in the middle of a wire segment are NOT connected
- kicad-cli ERC is more tolerant → **eeschema ERC is authoritative!**
- **Fix**: split wires at EVERY pin endpoint (segments instead of one long wire)

#### Coordinate Format in .kicad_sch

- Integer values are written as `285.0` (not `285`)
- Python fmt: `f"{v:.1f}"` for integer values

#### Insertion in .kicad_sch: Scope Issue

- `rfind('\n)')` does NOT find the kicad_sch closer! → use bracket-depth counting
- Validation: depth at insertion point must be 1 (inside kicad_sch)

#### Symbol Instances Section

- Every symbol in KiCad 9 MUST have an `(instances ...)` section
- Symbols WITHOUT instances are treated as unannotated by eeschema
- kicad-cli ERC does NOT detect this error — only eeschema GUI!

### Optimal Workflows

#### Schematic Creation (complex projects)

1. MCP: create project, place initial components
2. Python script: replicate channels, bulk wiring
3. kicad-cli: ERC + netlist export after every change
4. Quality gate script: automatic net validation

#### Validation (after every change)

1. Check bracket balance
2. kicad-cli netlist export (tests parser)
3. kicad-cli ERC (baseline comparison)
4. Verify net connections in netlist

### PCB Routing: Freerouting Workflow (ALWAYS do it this way!)

- Custom routing scripts DO NOT WORK (shorts with GND zones, no obstacle detection)

#### Step 1: Assign net classes (.kicad_pro)

#### Step 2: Design Rules (.kicad_dru)

#### Step 3: Freerouting (Autorouter)

```bash
pcbnew.ExportSpecctraDSN(board, "/tmp/board.dsn")
java -jar /tmp/freerouting.jar -de /tmp/board.dsn -do /tmp/board.ses -mp 20 -mt 4
pcbnew.ImportSpecctraSES(board, "/tmp/board.ses")
pcbnew.SaveBoard("/tmp/board-routed.kicad_pcb", board)  # ONLY to temp!
```

#### Step 4: Text-Merge Routing into Original (extract segments + vias, remap net IDs)

#### Step 5: Zone Fill via pcbnew + Text-Merge

#### Step 6: DRC via kicad-cli

### Zone Issues and Solutions

- **starved_thermal** → switch zone to `connect_pads yes` (Solid)
- **pcbnew.SaveBoard()** corrupts KiCad 9 files — ALWAYS use text-merge
- **kicad-cli does not fill zones** — pcbnew Python API required for zone fill

### User Preferences

- **NEVER** create .bak copies — use git for versioning
- **No temporary scripts in /tmp/** — place scripts in scripts/

---

## 8. Project Status

> Volatile data maintained separately — see [docs/project-status.md](../docs/project-status.md)
