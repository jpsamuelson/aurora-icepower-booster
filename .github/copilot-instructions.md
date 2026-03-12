# KiCad PCB Design — Copilot Instructions

## Projekt: Aurora DSP IcePower Booster

- **Verstärker-Board** auf Basis von ICEpower-Modulen
- **KiCad 9** Projekt (Schaltplan + PCB)
- **Ziel-Fertigung**: JLCPCB (2-Layer Standard, HASL, FR-4)
- **Sprache**: Deutsch bevorzugt für Kommentare und Erklärungen

---

## 1. KiCAD MCP Server — Architektur & Tool-Zugang

Der KiCAD MCP Server stellt **64 Tools** bereit, organisiert nach dem **Router Pattern**:

- **~17 Direkte Tools** — immer sichtbar, für häufige Operationen
- **~47 Geroutete Tools** — in 7 Kategorien, über Router abrufbar
- **4 Router Tools** — zur Entdeckung und Ausführung

### Router Pattern (Context-sparend, immer nutzen!)

```
1. list_tool_categories    → Alle 7 Kategorien anzeigen
2. get_category_tools      → Tools einer Kategorie auflisten
3. search_tools            → Tools per Stichwort finden
4. execute_tool            → Ein geroutetes Tool ausführen
```

### Direkte Tools (ohne Router nutzbar)

| Tool                      | Funktion                                                   |
| ------------------------- | ---------------------------------------------------------- |
| `create_project`          | Neues KiCad-Projekt (.kicad_pro + .kicad_pcb + .kicad_sch) |
| `open_project`            | Bestehendes Projekt laden                                  |
| `save_project`            | Projekt speichern                                          |
| `snapshot_project`        | Checkpoint mit PDF-Rendering                               |
| `get_project_info`        | Projekt-Metadaten                                          |
| `place_component`         | Footprint auf PCB platzieren                               |
| `move_component`          | Bauteil repositionieren                                    |
| `add_net`                 | Neues Netz erstellen                                       |
| `route_trace`             | Leiterbahn routen (single layer)                           |
| `set_board_size`          | PCB-Dimensionen konfigurieren                              |
| `add_board_outline`       | Board-Umriss (Rechteck/Kreis/Polygon/abgerundet)           |
| `get_board_info`          | Board-Eigenschaften abrufen                                |
| `add_schematic_component` | Symbol platzieren (~10.000 KiCad-Symbole)                  |
| `connect_passthrough`     | J1→J2 Durchverbindung (alle Pins)                          |
| `connect_to_net`          | Pin an benanntes Netz anschließen                          |
| `add_schematic_net_label` | Netzlabel im Schaltplan                                    |
| `sync_schematic_to_board` | Schaltplan → PCB synchronisieren (F8)                      |

### Geroutete Tool-Kategorien

| Kategorie     | Tools | Inhalt                                                              |
| ------------- | ----- | ------------------------------------------------------------------- |
| **BOARD**     | 9     | Layer-Management, Montagelöcher, Zonen, Board-Text, 2D-Preview      |
| **COMPONENT** | 8     | Rotieren, Löschen, Bearbeiten, Finden, Eigenschaften, Gruppieren    |
| **EXPORT**    | 8     | Gerber, PDF, SVG, 3D (STEP/STL), BOM, Netlist, Bestückungsdaten     |
| **DRC**       | 8     | Design Rules, DRC-Checks, Netzklassen, Constraints                  |
| **SCHEMATIC** | 9     | Bauteile bearbeiten/löschen, Verbindungen, Netlist-Generierung      |
| **LIBRARY**   | 11    | Footprint-/Symbol-Bibliotheken durchsuchen, erstellen, registrieren |
| **ROUTING**   | 2+    | Vias, Kupferflächen, Pad-to-Pad-Routing                             |

---

## 2. Workflows

### 2.1 Schaltplan-First (Empfohlen!)

```
create_project(path, name)
  → add_schematic_component() × N       # Bauteile platzieren
  → add_schematic_connection() × M      # Pins verbinden
  → connect_to_net() × K                # Power-Netze (VCC, GND, +5V)
  → add_schematic_net_label()            # Signal-Labels
  → sync_schematic_to_board()            # Netlist → PCB (F8)
  → set_board_size() + add_board_outline()
  → place_component() × N               # Footprints positionieren
  → route_trace() × M                   # Leiterbahnen
  → add_via()                            # Lagenwechsel
  → add_copper_pour()                    # GND-Fläche
  → run_drc()                            # Prüfung
  → export_gerber()                      # Fertigung
```

### 2.2 Quick-PCB (Bottom-Up, für einfache Boards)

```
create_project() → set_board_size() → add_board_outline()
  → place_component() × N → add_net() → route_trace() × N
  → add_copper_pour() → run_drc() → export_gerber()
```

### 2.3 Passthrough-Workflow (Adapter-Boards, FFC/FPC)

```
connect_passthrough(J1→J2)           # Alle Pins 1:1 verbinden
  → sync_schematic_to_board()        # Netze importieren
  → route_pad_to_pad() × N           # Auto-Routing mit Vias
  → snapshot_project("v1", "ok")     # Checkpoint
```

### 2.4 Kostenoptimierung (JLCPCB)

```
export_bom()
  → download_jlcpcb_database()       # 2.5M+ Teile, lokal
  → search_jlcpcb_parts() per Bauteil
  → suggest_jlcpcb_alternatives()    # Günstigere Alternativen
  → enrich_datasheets()              # Datenblätter verlinken
```

---

## 3. Kritische Regeln für Tool-Nutzung

### Dateipfade

- **Immer absolute Pfade** verwenden (z.B. `/Users/roroor/Documents/...`)
- Projekt muss **geladen** sein bevor Board/Schematic-Operationen möglich sind

### Symbol-Loading (Schaltplan)

- Format: `"library": "Device", "type": "R"` oder `"library": "Amplifier_Operational", "type": "LM358"`
- Dynamisches Loading: Zugriff auf **alle ~10.000 KiCad-Symbole** ohne Konfiguration
- Fallback-Templates für: R, C, L, LED, D, Q_NPN, Q_PNP, U, J, SW, F, Crystal, Transformer

### Pin-Verbindungen (Schaltplan)

- Pin-Positionen werden **automatisch erkannt** (rotationsabhängig: 0°, 90°, 180°, 270°)
- Routing-Optionen: `direct`, `orthogonal_h`, `orthogonal_v`
- Power-Symbole: VCC, GND, +3V3, +5V werden als spezielle Symbole behandelt

### Routing (PCB)

- `route_trace()` ist **Single-Layer** — für Multi-Layer `route_pad_to_pad()` verwenden
- Trace-Breiten und Via-Größen vorher über `set_design_rules()` konfigurieren
- Nach dem Routing immer `run_drc()` ausführen

### Checkpoints

- `snapshot_project()` regelmäßig nutzen — speichert Zustand + generiert PDF
- Vor größeren Änderungen immer Snapshot erstellen

---

## 4. KiCad Design-Richtlinien & Best Practices

### 4.1 Schaltplan-Design

#### Allgemeine Regeln

- **Signalfluss links → rechts**: Eingänge links, Ausgänge rechts
- **Power-Symbole**: VCC/+V oben, GND unten — immer konsistent
- **Ein Symbol pro Funktion**: Keine verschachtelten Funktionen in einem Symbol
- **Hierarchische Blätter** für modulare Designs (z.B. ein Blatt pro Verstärkerkanal)

#### Referenz-Designatoren (nach IEC 60617 / IEEE 315)

| Prefix | Bauteiltyp                    | Beispiel |
| ------ | ----------------------------- | -------- |
| R      | Widerstand                    | R1, R2   |
| C      | Kondensator                   | C1, C2   |
| L      | Induktivität/Spule            | L1       |
| D      | Diode                         | D1       |
| Q      | Transistor (BJT, MOSFET)      | Q1       |
| U      | IC (Integrierter Schaltkreis) | U1       |
| J      | Steckverbinder                | J1, J2   |
| SW     | Schalter/Taster               | SW1      |
| F      | Sicherung                     | F1       |
| FB     | Ferrite Bead                  | FB1      |
| Y      | Quarz/Oszillator              | Y1       |
| TP     | Testpunkt                     | TP1      |
| RN     | Widerstandsnetzwerk           | RN1      |
| LED    | Leuchtdiode                   | LED1     |

#### Netz-Benennung

- **Power-Netze**: `VCC`, `GND`, `+5V`, `+3V3`, `+12V`, `V_BAT`
- **Signal-Netze**: Beschreibend, z.B. `AUDIO_IN_L`, `AUDIO_OUT_R`, `I2C_SDA`, `SPI_MOSI`
- **Differentielle Paare**: Suffix `_P`/`_N` oder `+`/`-` (z.B. `USB_D+`, `USB_D-` oder `USB_DP`, `USB_DN`)
- **Bus-Signale**: Mit Index, z.B. `DATA[0..7]`, `ADDR[0..15]`

#### Entkopplungskondensatoren

- **100nF** Keramik (MLCC) direkt an jedem IC-Versorgungspin
- **10µF** Elektrolyt/Tantal an jedem Spannungsregler-Eingang/Ausgang
- **1µF** Keramik als Bulk-Kapazitanz pro Versorgungsinsel
- Platzierung: **So nah wie möglich** am IC, kürzeste Leiterbahn zu VCC und GND

#### Audio-spezifische Schaltplan-Regeln (für dieses Projekt)

- **Analoge und digitale Masse trennen** (AGND, DGND) — am Sternpunkt verbinden
- **Signal-Integrität**: Differentielle Signalführung bei Audio-Pfaden bevorzugen
- **Entkopplung**: Parallele Kondensatoren (100nF || 10µF) an Versorgungspins von Audio-ICs
- **EMV-Filter**: Ferrite Beads zwischen Digital- und Analog-Versorgung
- **Eingangs-Koppelkondensatoren**: DC-Blocking am Audio-Eingang (10µF–100µF Film/Elektrolyt)
- **Ausgangs-Schutz**: Zobel-Netzwerk (R + C in Serie) am Verstärkerausgang zur Lastimpedanz-Stabilisierung
- **Feedback-Netzwerke**: Präzisionswiderstände (1% Metallfilm, ±50ppm/°C) für Gain-Setting
- **Audio-Netz-Labels**: Konsistente Benennung: `AUDIO_IN_L`, `AUDIO_IN_R`, `AUDIO_OUT_L`, `AUDIO_OUT_R`, `AUDIO_GND`
- **Muting-Schaltung**: Einschalt-/Ausschalt-Muting vorsehen gegen Pop-/Klick-Geräusche
- **DC-Servo oder Offset-Trimm**: Bei DC-gekoppelten Designs Offset-Kompensation vorsehen

### 4.2 PCB-Layout

#### Board-Aufbau (2-Layer Standard für JLCPCB)

- **Top (F.Cu)**: Signale, Bauteile
- **Bottom (B.Cu)**: Massefläche (GND-Pour), sekundäre Signale
- **Board-Dicke**: 1.6mm Standard (FR-4)
- **Kupferstärke**: 1oz (35µm) Standard, 2oz für Leistungspfade

#### Bauteil-Platzierung (Prioritätenreihenfolge)

1. **Steckverbinder** zuerst — definieren die Board-Geometrie
2. **Leistungsbauteile** (Regler, MOSFETs) — Wärmeableitung beachten
3. **ICs** mit kurzen Verbindungen zu kritischen Bauteilen
4. **Entkopplungskondensatoren** direkt am zugehörigen IC
5. **Passive Bauteile** in den verbleibenden Raum
6. **Testpunkte** an zugänglichen Stellen

#### Platzierung-Richtlinien

- **Bauteile an Raster ausrichten**: 0.5mm oder 1.27mm (50mil) Raster
- **Gleiche Orientierung**: Alle Widerstände/Kondensatoren gleich ausrichten (erleichtert Bestückung)
- **Polarisierte Bauteile**: Konsistente Orientierung (Anode/Kathode immer gleiche Richtung)
- **Courtyard-Abstände einhalten**: Mindestens 0.25mm zwischen Courtyard-Grenzen
- **Wärmequellen**: Von temperatursensitiven Bauteilen fernhalten
- **Höhenprofil beachten**: Hohe Bauteile nicht vor niedrigen platzieren (Lötzugang)

### 4.3 Routing-Richtlinien

#### Leiterbahn-Breiten (Trace Width)

| Anwendung           | Breite (min) | Empfohlen  | Strom (bei 1oz Cu, 10°C ΔT) |
| ------------------- | ------------ | ---------- | --------------------------- |
| Signal (Standard)   | 0.15mm       | 0.2–0.25mm | ~0.3A                       |
| Signal (Fine-Pitch) | 0.1mm        | 0.127mm    | ~0.2A                       |
| Power (1A)          | 0.3mm        | 0.5mm      | ~1A                         |
| Power (2A)          | 0.5mm        | 0.8mm      | ~2A                         |
| Power (3A+)         | 1.0mm        | 1.5mm+     | ~3A+                        |
| Audio-Signal        | 0.2mm        | 0.3mm      | —                           |

#### Clearance (Abstände)

| Abstand              | JLCPCB Min | Empfohlen  | Beschreibung                              |
| -------------------- | ---------- | ---------- | ----------------------------------------- |
| Trace-to-Trace       | 0.1mm      | 0.15–0.2mm | Zwischen Leiterbahnen verschiedener Netze |
| Trace-to-Pad         | 0.1mm      | 0.15mm     | Leiterbahn zu Pad                         |
| Pad-to-Pad           | 0.1mm      | 0.2mm      | Zwischen Pads verschiedener Netze         |
| Trace-to-Board-Edge  | 0.2mm      | 0.3mm      | Leiterbahn zum Board-Rand                 |
| Kupfer-to-Board-Edge | 0.2mm      | 0.3mm      | Jedes Kupfer zum Rand                     |

#### Via-Design

| Parameter             | JLCPCB Min | Standard | Beschreibung              |
| --------------------- | ---------- | -------- | ------------------------- |
| Via-Durchmesser (Pad) | 0.45mm     | 0.6mm    | Äußerer Durchmesser       |
| Via-Bohrung           | 0.2mm      | 0.3mm    | Bohrdurchmesser           |
| Via-Annular-Ring      | 0.125mm    | 0.15mm   | Kupferring um Bohrung     |
| Via-to-Via            | 0.254mm    | 0.3mm    | Abstand zwischen Vias     |
| Via-to-Track          | 0.1mm      | 0.15mm   | Abstand Via zu Leiterbahn |

#### Routing-Patterns & Techniken

- **45°-Winkel**: Immer 45° statt 90° Ecken verwenden (reduziert Reflexionen, verbessert Fertigung)
- **Keine Stummel** (Stubs): Leiterbahnen sauber beenden, keine offenen Enden lassen
- **Sternförmige Versorgung**: Power von einem Punkt sternförmig verteilen, nicht in Reihe
- **Massefläche**: Mindestens eine komplette GND-Fläche (B.Cu) — möglichst wenige Unterbrechungen
- **Via-Stitching**: GND-Vias regelmäßig verteilen für niedrige Impedanz zwischen Top und Bottom GND
- **Thermische Vias**: Unter Thermal Pads mindestens 5–9 Vias (0.3mm Bohrung) im Raster
- **Teardrops**: An Pad-/Via-Übergängen aktivieren (verbessert Fertigbarkeit)

#### Differentielle Paare (für USB, Audio)

- **Konstanter Abstand** zwischen den Leitern (Gap = Regelwert der Netzklasse)
- **Gleiche Länge** beider Leiter (Skew minimieren)
- **Symmetrisch routen**: Beide Leiter gleichzeitig, keine einzelnen Knicke
- Netz-Benennung: `USB_D+`/`USB_D-` oder `USB_DP`/`USB_DN`

### 4.4 Power-Design

#### Masseflächen-Strategie

- **Ungeteilte GND-Fläche auf B.Cu** — wichtigste Regel!
- Analoge und digitale Masse auf **derselben Fläche**, aber räumlich getrennt (Rückstrompfade beachten)
- Masse nur am **Sternpunkt** verbinden wenn separate Flächen nötig
- Keine Leiterbahnen die die Massefläche **unter ICs zerschneiden**

#### Spannungsversorgung

- **Breite Leiterbahnen** für Versorgungsleitungen (mindestens 0.5mm für 1A)
- **Kupferflächen** für hohe Ströme statt einzelner Leiterbahnen
- **Eingangsfilter**: Ferrite Bead + 100nF + 10µF am Board-Eingang
- **Spannungsregler**: Eingangs- und Ausgangskondensatoren lt. Datenblatt

### 4.5 EMV & Signal-Integrität

- **Kurze Leiterbahnen** für Hochfrequenz-Signale (Taktsignale, schnelle Daten)
- **Rückstrompfad**: Leiterbahn immer direkt über intakter Massefläche führen
- **Guard Traces**: Für empfindliche Analog-Signale — GND-Leiterbahnen parallel führen
- **Abschirmung**: Kritische Bereiche mit Massefläche umschließen
- **Ferrite Beads**: Zwischen Analog- und Digital-Versorgung (z.B. BLM18AG601)
- **ESD-Schutz**: TVS-Dioden an allen externen Steckverbindern

### 4.6 Silkscreen & Beschriftung

- **Alle Bauteile beschriften**: Referenz-Designator auf Silkscreen (F.Silkscreen)
- **Lesbare Größe**: Mindestens 0.8mm Texthöhe, 0.15mm Strichstärke
- **Pin-1-Markierung**: Bei ICs und Steckverbindern deutlich markieren
- **Polaritätsmarkierung**: Bei Elkos, Dioden, LEDs
- **Testpunkt-Beschriftung**: TP1, TP2, ... mit zugehörigem Netznamen
- **Board-Info**: Projektname, Version, Datum auf Silkscreen
- **Kein Silkscreen auf Pads**: Silkscreen von Löt-Pads fernhalten (Subtract soldermask from silkscreen)

---

## 5. JLCPCB Fertigungsregeln (Design for Manufacturing)

### 5.1 PCB-Spezifikationen (Standard 2-Layer)

| Parameter         | Wert                                       |
| ----------------- | ------------------------------------------ |
| Layer             | 1–32 (Standard: 2)                         |
| Material          | FR-4                                       |
| Dicke             | 0.4–4.5mm (Standard: 1.6mm)                |
| Min. Abmessung    | 3×3mm                                      |
| Max. Abmessung    | 670×600mm (2L: bis 1020×600mm)             |
| Kupferdicke außen | 1oz / 2oz (Standard: 1oz = 35µm)           |
| Lötstopplack      | Grün, Lila, Rot, Gelb, Blau, Weiß, Schwarz |
| Oberfläche        | HASL (blei/bleifrei), ENIG, OSP            |

### 5.2 Minimale Design-Regeln (JLCPCB)

| Regel                | Minimum        | Empfehlung |
| -------------------- | -------------- | ---------- |
| Leiterbahnbreite     | 0.1mm (3.5mil) | ≥0.15mm    |
| Leiterbahnabstand    | 0.1mm (3.5mil) | ≥0.15mm    |
| Annular Ring         | 0.125mm        | ≥0.15mm    |
| Bohrung (PTH)        | 0.2mm          | ≥0.3mm     |
| Bohrung (NPTH)       | 0.5mm          | ≥0.8mm     |
| Pad-Größe (min)      | 0.45mm         | ≥0.6mm     |
| Silkscreen-Breite    | 0.1mm          | ≥0.15mm    |
| Silkscreen-Höhe      | 0.8mm          | ≥1.0mm     |
| Board-Edge zu Kupfer | 0.2mm          | ≥0.3mm     |

### 5.3 Board Setup für JLCPCB (in KiCad)

```
Board Setup → Design Rules → Constraints:
  Minimum Track Width:           0.15mm
  Minimum Clearance:             0.15mm
  Minimum Via Diameter:          0.45mm
  Minimum Via Drill:             0.2mm
  Minimum Through Hole:          0.2mm
  Minimum Annular Width:         0.125mm
  Copper to Edge Clearance:      0.3mm
  Minimum Connection Width:      0.15mm

Board Setup → Design Rules → Net Classes:
  Default:
    Clearance:     0.2mm
    Track Width:   0.25mm
    Via Size:      0.6mm
    Via Drill:     0.3mm
  Power:
    Clearance:     0.2mm
    Track Width:   0.5mm
    Via Size:      0.8mm
    Via Drill:     0.4mm
  Audio:
    Clearance:     0.2mm
    Track Width:   0.3mm
    Via Size:      0.6mm
    Via Drill:     0.3mm
```

### 5.4 Gerber-Export für JLCPCB

**Layer-Auswahl (2-Layer):**

- F.Cu, B.Cu, F.Paste, B.Paste, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, Edge.Cuts

**Gerber-Optionen:**

- ✅ Plot reference designators
- ✅ Plot footprint text
- ✅ Check zone fills before plotting
- ✅ Tent vias
- ✅ Use Protel filename extensions
- ✅ Subtract soldermask from silkscreen

**Drill-Optionen:**

- Oval Holes: Use alternate drill mode
- Origin: Absolute
- Units: Millimeters
- Zeros Format: Decimal

### 5.5 JLCPCB-Bauteilauswahl (SMT Assembly)

- **Basic Parts bevorzugen**: Keine Bestückungsgebühr ($0 setup pro unique part)
- **Extended Parts**: $3 Setup-Gebühr pro unique part
- **Packaging**: Tape & Reel bevorzugt (besser für SMT)
- `search_jlcpcb_parts` → filtere nach `"basic": true`
- `suggest_jlcpcb_alternatives` → findet günstigere kompatible Bauteile

### 5.6 Bestückungs-relevante Regeln

- **Pad-Größe für SMD**: Mindestens 0.25mm größer als Bauteilpin auf jeder Seite
- **Fiducial Marks**: Bei SMT-Bestückung mindestens 3 Fiducials (1mm Pad, 2mm Öffnung)
- **BOM & Centroid**: Über KiCad exportierbar (`export_bom`, `export_position_file`)
- **Bauteil-Orientierung**: 0° = Pin 1 oben-links (JLCPCB Standard)

---

## 6. Netzklassen (Net Classes) — Empfohlene Konfiguration

| Netzklasse        | Clearance | Track Width | Via Size | Via Drill | Beschreibung            |
| ----------------- | --------- | ----------- | -------- | --------- | ----------------------- |
| Default           | 0.2mm     | 0.25mm      | 0.6mm    | 0.3mm     | Standard-Signale        |
| Power             | 0.2mm     | 0.5mm       | 0.8mm    | 0.4mm     | Versorgung, hohe Ströme |
| Audio             | 0.2mm     | 0.3mm       | 0.6mm    | 0.3mm     | Audio-Signale           |
| HV (Hochspannung) | 0.5mm     | 0.3mm       | 0.8mm    | 0.4mm     | >50V Signale            |
| USB               | 0.15mm    | 0.2mm       | 0.45mm   | 0.2mm     | USB Diff. Pair          |

---

## 7. Custom Design Rules (kicad_dru) — Beispiele

```
(version 1)

# Mindest-Clearance für Leistungsnetze
(rule power_clearance
    (condition "A.hasNetclass('Power')")
    (constraint clearance (min 0.25mm)))

# Breitere Traces für Power
(rule power_width
    (condition "A.hasNetclass('Power')")
    (constraint track_width (min 0.5mm)))

# HV-Clearance (ICEpower Module)
(rule hv_clearance
    (condition "A.hasNetclass('HV')")
    (constraint clearance (min 0.5mm)))

# Thermische Reliefs für Power-Pads
(rule thermal_power
    (constraint thermal_relief_gap (min 0.25mm))
    (constraint thermal_spoke_width (min 0.3mm))
    (condition "A.hasNetclass('Power')"))

# Board-Edge Clearance
(rule board_edge
    (constraint edge_clearance (min 0.3mm)))
```

---

## 8. Checkliste vor Fertigung

### Design Review

- [ ] Schaltplan ERC fehlerfrei (`run_erc`)
- [ ] PCB DRC fehlerfrei (`run_drc`)
- [ ] Alle Netze verbunden (keine offenen Ratsnest-Linien)
- [ ] Entkopplungskondensatoren an allen IC-Versorgungspins
- [ ] Massefläche intakt (keine großen Unterbrechungen)
- [ ] Thermische Vias unter Thermal Pads
- [ ] Montagelöcher vorhanden (M3 = 3.2mm Bohrung)

### Fertigung

- [ ] Board-Outline geschlossen (Edge.Cuts)
- [ ] Mindest-Abstände eingehalten (JLCPCB Specs)
- [ ] Vias getented (Lötstopplack über Vias)
- [ ] Silkscreen nicht auf Pads
- [ ] Fiducials vorhanden (wenn SMT Assembly)
- [ ] Gerber mit Protel-Extensions exportiert
- [ ] Drill-Files in Excellon-Format
- [ ] Gerber in Viewer verifiziert

### BOM & Bestückung

- [ ] BOM exportiert (CSV/JSON)
- [ ] Centroid/Position-File exportiert
- [ ] JLCPCB Basic Parts bevorzugt
- [ ] Alle Bauteile verfügbar (Stock ≥ Stückzahl)

---

## 9. Footprint-Auswahl (häufig benötigt)

### SMD-Widerstände & Kondensatoren

| Package | KiCad Footprint                  | Größe (mm) | Empfehlung                     |
| ------- | -------------------------------- | ---------- | ------------------------------ |
| 0402    | `Resistor_SMD:R_0402_1005Metric` | 1.0×0.5    | Nur wenn nötig (schwer lötbar) |
| 0603    | `Resistor_SMD:R_0603_1608Metric` | 1.6×0.8    | **Standard für neue Designs**  |
| 0805    | `Resistor_SMD:R_0805_2012Metric` | 2.0×1.25   | Gut für Handlötung             |
| 1206    | `Resistor_SMD:R_1206_3216Metric` | 3.2×1.6    | Leistungswiderstände           |

### Elektrolyt-Kondensatoren

| Package | KiCad Footprint             | Beschreibung     |
| ------- | --------------------------- | ---------------- |
| SMD     | `Capacitor_SMD:CP_Elec_*`   | SMD Elektrolyt   |
| THT     | `Capacitor_THT:CP_Radial_*` | Radial bedrahtet |

### ICs & Steckverbinder

- **SOIC-8**: `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`
- **TSSOP**: `Package_SO:TSSOP-*`
- **QFP**: `Package_QFP:*`
- **Pin Header**: `Connector_PinHeader_2.54mm:*`
- **JST**: `Connector_JST:JST_*`

---

## 10. Audio-Verstärker-spezifische Hinweise (ICEpower)

### ICEpower Module Integration

- **Datenblatt-Pins genau beachten**: Pin-Belegung variiert je nach Modul
- **Steckverbinder-Footprints**: Exakt nach Modul-Datenblatt wählen
- **Masse-Anbindung**: Niederohmig, breite Kupferflächen
- **Versorgungseingänge**: Ausreichend dimensionierte Leiterbahnen (Strom beachten!)
- **Signalpfade kurz halten**: Audio-Eingänge nah am Modul
- **Abblock-Kondensatoren**: Direkt am Modulanschluss
- **ENABLE/MUTE-Pins**: Korrekte Beschaltung lt. Datenblatt — Pullup/Pulldown + RC-Verzögerung
- **Feedback-Netzwerk**: Falls extern — Präzisionsbauteile, kurze symmetrische Pfade
- **Sense-Leitungen**: Kelvin-Verbindung direkt am Lautsprecheranschluss (falls vom Modul gefordert)

### Thermisches Design

- **Thermal Pads**: Via-Array unter Thermal Pads (mind. 5×5 Vias bei 0.3mm)
- **Kupferflächen**: Große Kupferflächen auf Top und Bottom für Wärmeableitung
- **Keine Bauteile über Hot-Spots**: Wärmequellen erkennen und Abstand halten
- **Lüftungslöcher**: Bei Bedarf im Board-Outline vorsehen
- **Thermische Vias in Raster**: 1.0–1.2mm Raster unter Thermal Pads
- **Kühlkörper-Anbindung**: Schraubbefestigung (M3) mit Wärmeleitpad vorsehen
- **Temperatur-Derating**: Leistungsbauteile bei 70°C Umgebung mindestens 50% deratieren

---

## 11. Audio-Design: Klangqualität & Low-Noise Best Practices

Dieses Kapitel enthält umfassende Richtlinien für hochwertige Audio-Schaltungen — speziell für Audio-Booster/Buffer-Designs mit dem Ziel niedriger Verzerrung (THD+N), geringem Rauschen und exzellenter Klangqualität.

### 11.1 Grundprinzipien Audio-PCB-Design

#### Rückstrompfad-Philosophie (wichtigste Regel!)

- **Jeder Signalstrom hat einen Rückstrompfad** — dieser muss bewusst geführt werden
- Bei niedrigen Frequenzen (<50 kHz) fließt der Rückstrom auf dem Weg des **geringsten Widerstands** (gerader Weg durch die Massefläche)
- Bei höheren Frequenzen fließt der Rückstrom auf dem Weg der **geringsten Impedanz** (direkt unter der Signalleiterbahn im Groundplane)
- **Keine Schlitze in der Massefläche unter Audio-Signalpfaden** — dies zwingt den Rückstrom auf Umwege und erzeugt Schleifenantennen
- Massefläche unter Audio-ICs und -Signalen immer **vollständig und ununterbrochen** halten
- Rückstrompfade verschiedener Signale dürfen sich **nicht überlappen** (Crosstalk-Vermeidung)

#### Signal-zu-Rausch-Verhältnis (SNR) maximieren

- **Kurze Signalwege**: Je kürzer die Leiterbahn, desto weniger induziertes Rauschen
- **Niedrige Impedanzen im Signalpfad**: Hohe Impedanzen sind anfällig für kapazitive Einkopplung
- **Abstand zu Störquellen**: Audio-Traces mindestens 5mm von Schaltregler-Induktivitäten, Taktsignalen, digitalen Bussen
- **Bandbreitenbegrenzung**: Ungenutztes Frequenzband filtern (Tiefpass am Audio-Eingang, z.B. 50–100 kHz)

### 11.2 Massekonzept für Audio (Grounding)

#### Sternpunkt-Masse (Star Ground)

- **Ein zentraler Sternpunkt** auf dem PCB, an dem alle Masserückführungen zusammenlaufen
- Reihenfolge der Masse-Anbindung am Sternpunkt:
  1. **Analog-GND** (empfindlichste Signale zuerst)
  2. **Digital-GND** (DSP, Mikrocontroller)
  3. **Power-GND** (Leistungsstufe, Netzteil)
- Der Sternpunkt liegt idealerweise **am Massepin des Eingangssteckverbinders** oder am Versorgungseingang

#### Masseflächen-Split vs. Unified Ground

- **Empfohlen für 2-Layer Audio**: Unifizierte (ungeteilte) Massefläche auf B.Cu
- **KEIN physischer Split** der Massefläche — stattdessen Bauteil-Platzierung und Routing so gestalten, dass analoge und digitale Rückströme **räumlich getrennt** fließen
- Splits erzwingen Umwege für den Rückstrom → größere Schleifenflächen → mehr Störeinkopplung
- Wenn Split unvermeidlich: **Nur ein einziger Verbindungspunkt** (Sternpunkt) und **keine Traces über den Split** routen

#### Masseführung in der Praxis

- **Analoge Bauteile** in einem Bereich des PCB gruppieren
- **Digitale Bauteile** räumlich getrennt davon platzieren
- **Leistungsstufe** (ICEpower-Modul) in eigenem Bereich
- Versorgungsleitungen und deren Rückstrom vom analogen Bereich **wegführen**
- Power-GND-Rückströme dürfen **nicht durch den Analog-Bereich** fließen
- Bei mehreren Verstärkerkanälen: Jeder Kanal bekommt **eigene lokale Masse-Anbindung**, alle treffen sich am Sternpunkt

### 11.3 Audio-Signalführung (Trace Routing)

#### Allgemeine Routing-Regeln für Audio

- **Direkte, kurze Pfade**: Audio-Traces so kurz und direkt wie möglich
- **Keine Stubs**: Offene Leiterbahn-Enden wirken als Antennen
- **45°-Winkel**: Immer 45° statt 90° Ecken (gilt generell, aber bei Audio besonders wichtig für einheitliche Impedanz)
- **Audio-Traces auf Top-Layer**: Alle Audio-Signale bevorzugt auf F.Cu routen (B.Cu für ununterbrochene Massefläche freihalten)
- **Keine Vias im Audio-Signalpfad**: Jeder Via ist ein Impedanzsprung und eine potenzielle Rauschquelle — nur wenn absolut unvermeidlich
- **Via-Stitching um Audio-Traces**: GND-Vias beidseitig entlang empfindlicher Audio-Traces (alle 5–10mm) verbessern die Masseanbindung

#### Guard Traces (Schirmung auf PCB-Ebene)

- **GND-Guard-Traces** parallel zu empfindlichen Audio-Eingangssignalen
- Beidseitig der Audio-Trace GND-Leiterbahnen führen, mit Vias zur Massefläche alle 5mm
- Guard-Trace-Abstand: 0.2–0.3mm zur Audio-Trace (mindestens 2× Trace-Breite)
- Guard Traces am Anfang und Ende an GND anschließen

#### Differentielle Audio-Signalführung

- **Impedanz-Matching**: Beide Leiter exakt gleich lang, gleicher Abstand zueinander
- **Symmetrisches Routing**: Beide Leiter als Paar routen, gemeinsam abknicken
- **Verdrillung nachbilden** (auf PCB): Leiter gelegentlich kreuzen lassen (nur bei langen Strecken >30mm relevant)
- **Balancierte Ein-/Ausgänge**: XLR/TRS mit symmetrischer Signalführung (Hot/Cold/Shield)

#### Kreuzungen vermeiden

- **Audio-Traces dürfen sich nicht kreuzen** — wenn unvermeidlich, rechtwinklig (90°) kreuzen für minimale Kopplung
- **Audio-Traces niemals parallel zu digitalen Signalen** routen
- **Mindestabstand**: Audio-Signals zu Digital-Signals ≥ 3mm, zu Power-Traces ≥ 5mm

### 11.4 Bauteilauswahl für Audio-Qualität

#### Widerstände

| Typ                          | Einsatz                     | Audio-Eigenschaften                                                               |
| ---------------------------- | --------------------------- | --------------------------------------------------------------------------------- |
| **Metallfilm (Dünnfilm)**    | Gain-Setting, Feedback      | Niedrigstes Rauschen, geringe nichtlineare Verzerrung, ±1% oder besser, ≤50ppm/°C |
| **Metallschicht (Dickfilm)** | Allgemein, unkritisch       | Standard, akzeptabel für die meisten Audio-Pfade                                  |
| **Kohleschicht**             | ❌ Vermeiden                | Höheres Rauschen, spannungsabhängiger Widerstand → nichtlineare Verzerrung        |
| **Drahtwiderstände**         | Emitter-/Source-Widerstände | Niedrigster Rauschbeitrag, aber induktiv → nur bei niedrigen Frequenzen           |

- **Thermisches Rauschen**: $V_n = \sqrt{4 k_B T R \Delta f}$ — niedrigere Widerstandswerte = weniger Rauschen
- Im Audio-Signalpfad **Widerstände so niedrig wie möglich** wählen (typisch 1k–10kΩ)
- Parallele Widerstände reduzieren Rauschen um $\sqrt{2}$
- **Kein Mischmasch** von Widerstandstypen im selben Signalpfad

#### Kondensatoren

| Typ                        | Einsatz im Audio                   | Eigenschaften                                                                            |
| -------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------- |
| **C0G/NP0 Keramik (MLCC)** | Entkopplung, Filter, Timing        | Kein Piezo-Effekt, kein Mikrofonie-Effekt, lineare Kapazität, ideal für Audio            |
| **Polypropylen (PP) Film** | Signal-Kopplung, Filter, Crossover | Niedrigster Verlustfaktor (tan δ), exzellent für Audio-Signalpfad                        |
| **Polyester (PET) Film**   | Signal-Kopplung (Budget)           | Akzeptabel, etwas höheres tan δ als PP                                                   |
| **X7R/X5R Keramik (MLCC)** | ⚠️ Nur für Entkopplung             | **Mikrofonie-Effekt!** Kapazität spannungsabhängig — NICHT im Audio-Signalpfad verwenden |
| **Elektrolyt (Aluminium)** | Bulk-Entkopplung, Power            | Hoher ESR, Alterung — nur für Versorgung, nicht direkt im Signalpfad                     |
| **Tantal**                 | ⚠️ Nur für Entkopplung             | Brandgefahr bei Überspannung, nicht im Signalpfad                                        |

- **Mikrofonie-Effekt bei MLCC**: X7R/X5R Keramikkondensatoren erzeugen bei Vibration elektrische Signale → hörbar als Mikrofonie
- **DC-Bias-Derating bei MLCC**: X7R verliert bis zu 80% Kapazität bei hoher DC-Spannung — bei Koppelkondensatoren C0G oder Film verwenden
- **Koppelkondensatoren**: Ausreichend groß wählen: $f_{-3dB} = \frac{1}{2\pi R C}$ — für 20Hz bei 10kΩ Last ≥ 0.8µF
- **Parallele Kondensatoren**: 100nF C0G || 10µF Elko für Entkopplung (Keramik für HF, Elko für NF)

#### Operationsverstärker / Audio-ICs

- **Low-Noise Op-Amps**: Spannungsrauschen $e_n$ < 5 nV/√Hz (z.B. OPA1612, OPA1656, NE5532, LME49710)
- **Low-Distortion**: THD+N < 0.0003% bei 1 kHz (z.B. OPA1612: typ. 0.000015%)
- **Ausreichend Slew Rate**: Mindestens $SR = 2\pi f V_{peak}$ — für 20 kHz bei ±15V → SR ≥ 2 V/µs — Empfehlung: ≥10 V/µs
- **GBW (Gain-Bandwidth)**: Ausreichend für gewünschte Verstärkung bei 20 kHz
- **PSRR (Power Supply Rejection)**: ≥ 80 dB bei 1 kHz — höher ist besser
- **CMRR (Common Mode Rejection)**: ≥ 80 dB für balancierte Eingänge

#### Spannungsregler für Audio

- **Low-Noise LDO bevorzugen**: Ausgangsrauschen < 10 µV RMS (z.B. TPS7A47, ADP7118, LT3045)
- **PSRR des Reglers**: ≥ 60 dB bei 100 Hz, ≥ 40 dB bei 100 kHz
- **Keine Schaltregler** direkt für analoge Audio-Versorgung (zu viel Schaltripple)
- **Wenn Schaltregler nötig**: Schaltregler → LC-Filter → LDO → Analog-Versorgung (zweistufige Filterung)
- **Getrennte Regler**: Separate LDOs für analoge und digitale Versorgung

### 11.5 Entkopplungs-Strategie für Audio-ICs

#### Hierarchische Entkopplung (3 Stufen)

1. **Bulk-Kapazität** (10–100µF Elektrolyt/Tantal): Am Versorgungseingang des Boards, liefert Energiereserve
2. **Lokale Entkopplung** (1–10µF Keramik X5R/X7R): Pro Versorgungsinsel, <20mm vom IC
3. **HF-Entkopplung** (100nF C0G): Direkt am IC-Pin, kürzeste Verbindung zu VCC und GND

#### Platzierungsregeln

- **Reihenfolge vom IC aus**: 100nF direkt am Pin → 1µF dahinter → 10µF am Versorgungsstrang
- **Vias für GND-Anbindung**: Via direkt am GND-Pad des Kondensators zur Massefläche
- **Keine langen Leiterbahnen** zwischen Entkopplungs-C und IC-Pin (max. 3mm)
- **Beidseitige Bestückung nutzen**: Entkopplungskondensatoren auf B.Cu direkt unter dem IC platzieren

### 11.6 Eingangs- und Ausgangsschutz

#### Eingangsschutz (Audio Input)

- **ESD-Schutz**: TVS-Dioden (bidirektional, z.B. PESD5V0S1BA) an allen externen Audio-Eingängen
- **DC-Blocking**: Koppelkondensator (Film oder C0G, ≥1µF) am Eingang
- **EMI-Filter**: Serienwiderstand (47–100Ω) + Keramikkondensator (100pF–1nF) gegen GND als Tiefpass
- **Strombegrenzung**: Serienwiderstand (100Ω–1kΩ) schützt Op-Amp-Eingangspin

#### Ausgangsschutz (Audio Output)

- **Zobel-Netzwerk**: 10Ω + 100nF in Serie, parallel zum Ausgang (stabilisiert Verstärker bei kapazitiver Last)
- **Schutzwiderstände**: 2.2–10Ω in Serie am Ausgang (bipolare Verstärker)
- **Kurzschlussschutz**: Strombegrenzung intern (bei ICEpower Modulen integriert)
- **Induktivitäts-Unterdrückung**: Bei Class-D: LC-Ausgangsfilter lt. Datenblatt

### 11.7 Störquellen-Management

#### Schaltregler-Störungen minimieren

- **Räumliche Trennung**: Schaltregler mindestens 20mm von Audio-Eingangsstufe entfernen
- **Schalt-Induktivität abschirmen**: Geschirmte Induktivitäten bevorzugen
- **Schaltfrequenz > 500 kHz**: Höhere Schaltfrequenz ist leichter zu filtern und liegt weiter vom Audioband
- **EMI-Filter**: π-Filter (C-L-C) zwischen Schaltregler und Audio-Versorgung
- **Keine Schaltregler-Traces unter Audio-ICs** routen

#### Taktsignale und Digitales

- **Taktquellen weit weg** von Audio-Eingängen platzieren
- **Clock-Traces**: So kurz wie möglich, direkt über intakter Massefläche
- **Seriendämpfungswiderstände** (22–47Ω) in Clock-Leitungen zur Reduzierung von Oberwellen
- **Spread-Spectrum Clocking** nutzen wenn verfügbar (verteilt Störenergie)

#### Mechanische Vibration (Mikrofonie)

- **Keramikkondensatoren (X7R/X5R)** nicht im Audio-Signalpfad — Piezo-Effekt erzeugt Mikrofonie
- **Bauteile mechanisch fixieren**: Bei Bedarf Klebstoff auf großen Bauteilen
- **Board-Mounting**: Gummipuffer/Entkoppler zwischen PCB und Gehäuse
- **Quarz/Oszillator**: Von empfindlichen Analog-Bauteilen entfernt platzieren

### 11.8 Steckverbinder und Interfaces

#### Audio-Steckverbinder

| Typ                            | Einsatz                    | Pins                                           | Besonderheiten                               |
| ------------------------------ | -------------------------- | ---------------------------------------------- | -------------------------------------------- |
| **XLR** (3-Pin)                | Professionell, symmetrisch | Pin 1: Shield, Pin 2: Hot (+), Pin 3: Cold (−) | Beste EMV-Immunität dank Symmetrie           |
| **TRS 6.3mm** (Klinkenstecker) | Symmetrisch/unsymmetrisch  | Tip: Hot, Ring: Cold/Return, Sleeve: GND       | Kompatibel mit symmetrisch und unsymmetrisch |
| **RCA/Cinch**                  | Consumer, unsymmetrisch    | Signal + GND                                   | Einfach, aber störempfindlicher              |
| **Speakon** (NL2/NL4)          | Lautsprecherausgang        | 1+/1−, (2+/2−)                                 | Verriegelnd, für hohe Ströme                 |

#### Steckverbinder-Layout

- **Massepin zuerst kontaktieren**: Bei der PCB-Platzierung Massepin näher am Board-Edge
- **Kurze GND-Anbindung**: Steckverbinder-GND direkt via breite Kupferfläche an Massefläche
- **Keine Signaltraces neben Steckverbinder-Montagepins**: Montagepins können Störungen einkoppeln
- **EMI-Filter direkt am Steckverbinder**: Schutzschaltung (TVS + RC-Filter) maximal 5mm vom Pin

### 11.9 Audio-Netzklassen — Erweiterte Konfiguration

```
Board Setup → Design Rules → Net Classes:
  Audio_Input:
    Clearance:     0.25mm
    Track Width:   0.3mm
    Via Size:      0.6mm
    Via Drill:     0.3mm
    Beschreibung:  Empfindliche Audio-Eingangssignale

  Audio_Output:
    Clearance:     0.2mm
    Track Width:   0.5mm
    Via Size:      0.6mm
    Via Drill:     0.3mm
    Beschreibung:  Audio-Ausgangssignale (höherer Strom)

  Audio_Power:
    Clearance:     0.2mm
    Track Width:   0.8mm
    Via Size:      0.8mm
    Via Drill:     0.4mm
    Beschreibung:  Analoge Versorgung für Audio-ICs

  Speaker:
    Clearance:     0.3mm
    Track Width:   1.5mm
    Via Size:      0.8mm
    Via Drill:     0.4mm
    Beschreibung:  Lautsprecherausgänge (hoher Strom, Class-D PWM)
```

### 11.10 Custom Design Rules für Audio (kicad_dru)

```
(version 1)

# Audio-Eingangs-Clearance (empfindliche Signale)
(rule audio_input_clearance
    (condition "A.hasNetclass('Audio_Input')")
    (constraint clearance (min 0.25mm)))

# Audio-Eingang: Mindestabstand zu Digital-Signalen
(rule audio_digital_separation
    (condition "A.hasNetclass('Audio_Input') && B.hasNetclass('Default')")
    (constraint clearance (min 0.5mm)))

# Speaker-Traces breit genug für Strom
(rule speaker_width
    (condition "A.hasNetclass('Speaker')")
    (constraint track_width (min 1.0mm)))

# Analoge Versorgung: Mindest-Tracebreite
(rule audio_power_width
    (condition "A.hasNetclass('Audio_Power')")
    (constraint track_width (min 0.5mm)))
```

### 11.11 Audio-Design-Checkliste

#### Schaltplan

- [ ] Low-Noise Op-Amps ausgewählt ($e_n$ < 5 nV/√Hz)
- [ ] Koppelkondensatoren dimensioniert ($f_{-3dB}$ < 5 Hz)
- [ ] Entkopplung: 100nF C0G + 10µF an jedem Audio-IC-Versorgungspin
- [ ] Feedback-Widerstände: Metallfilm, ±1%, ≤50 ppm/°C
- [ ] Keine X7R/X5R Keramik im Audio-Signalpfad
- [ ] Zobel-Netzwerk am Verstärkerausgang
- [ ] ESD-Schutz an allen externen Steckverbindern
- [ ] Muting-Schaltung für Ein-/Ausschalten vorhanden
- [ ] Analoge und digitale Versorgung getrennt geregelt

#### PCB-Layout

- [ ] Massefläche unter Audio-Signalpfaden ununterbrochen
- [ ] Audio-Traces auf Top-Layer, keine unnötigen Vias
- [ ] Guard-Traces um empfindliche Audio-Eingänge
- [ ] Schaltregler ≥ 20mm von Audio-Eingangsstufe
- [ ] Keine digitalen Traces parallel zu Audio-Traces
- [ ] Kreuzungen nur rechtwinklig (90°)
- [ ] Sternpunkt-Masse korrekt implementiert
- [ ] Entkopplungskondensatoren direkt an IC-Pins (<3mm)
- [ ] Steckverbinder-GND niederohmig an Massefläche
- [ ] Via-Stitching entlang Audio-Traces (alle 5–10mm)

#### Klangqualität

- [ ] SNR-Ziel definiert (typisch >100 dB für Hi-Fi)
- [ ] THD+N Budget berechnet (Ziel: <0.01% bei 1 kHz)
- [ ] Crosstalk zwischen Kanälen minimiert (>70 dB Trennung)
- [ ] Bandbreite begrenzt (Anti-Aliasing / EMI-Filter)
- [ ] Keine Mikrofonie-empfindlichen Bauteile im Signalpfad
