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

## 4. Schaltplan-Design

### Allgemeine Regeln

- **Signalfluss links → rechts**: Eingänge links, Ausgänge rechts
- **Power-Symbole**: VCC/+V oben, GND unten — immer konsistent
- **Ein Symbol pro Funktion**: Keine verschachtelten Funktionen in einem Symbol
- **Hierarchische Blätter** für modulare Designs (z.B. ein Blatt pro Verstärkerkanal)

### Netz-Benennung

- **Power-Netze**: `VCC`, `GND`, `+5V`, `+3V3`, `+12V`, `V_BAT`
- **Audio-Signale**: `AUDIO_IN_L`, `AUDIO_IN_R`, `AUDIO_OUT_L`, `AUDIO_OUT_R`, `AUDIO_GND`
- **Differentielle Paare**: Suffix `_P`/`_N` oder `+`/`-`

### Entkopplung (3 Stufen)

1. **HF-Entkopplung** (100nF C0G): Direkt am IC-Pin, kürzeste Verbindung zu VCC und GND (<3mm)
2. **Lokale Entkopplung** (1–10µF Keramik X5R/X7R): Pro Versorgungsinsel, <20mm vom IC
3. **Bulk-Kapazität** (10–100µF Elektrolyt): Am Versorgungseingang des Boards

Platzierung vom IC aus: 100nF direkt am Pin → 1µF dahinter → 10µF am Versorgungsstrang. Via direkt am GND-Pad des Kondensators zur Massefläche. Bei Audio-ICs: Entkopplungskondensatoren auf B.Cu direkt unter dem IC platzieren.

### Audio-spezifische Schaltplan-Regeln

- **Kein X7R/X5R im Audio-Signalpfad** — Mikrofonie-Effekt! Nur C0G oder Film verwenden
- **Koppelkondensatoren**: Film oder C0G, $f_{-3dB} = \frac{1}{2\pi R C}$ — für 20 Hz bei 10 kΩ Last ≥ 0.8 µF
- **Feedback-Netzwerke**: Metallfilm-Widerstände (±1%, ≤50 ppm/°C) für Gain-Setting
- **Zobel-Netzwerk**: 10 Ω + 100 nF in Serie am Verstärkerausgang (Lastimpedanz-Stabilisierung)
- **Muting-Schaltung**: Einschalt-/Ausschalt-Muting gegen Pop-/Klick-Geräusche
- **EMV-Filter**: Ferrite Beads zwischen Digital- und Analog-Versorgung

### Bauteilauswahl für Audio-Qualität

#### Widerstände

| Typ                          | Einsatz                | Eigenschaften                               |
| ---------------------------- | ---------------------- | ------------------------------------------- |
| **Metallfilm (Dünnfilm)**    | Gain-Setting, Feedback | Niedrigstes Rauschen, ±1%, ≤50 ppm/°C       |
| **Metallschicht (Dickfilm)** | Allgemein              | Standard, akzeptabel                        |
| **Kohleschicht**             | ❌ Vermeiden           | Spannungsabhängig → nichtlineare Verzerrung |

Im Audio-Signalpfad Widerstände so niedrig wie möglich wählen (1k–10 kΩ).

#### Kondensatoren

| Typ                   | Einsatz                 | Hinweis                                  |
| --------------------- | ----------------------- | ---------------------------------------- |
| **C0G/NP0 MLCC**      | Entkopplung, Filter     | Ideal für Audio — kein Mikrofonie-Effekt |
| **Polypropylen Film** | Signal-Kopplung, Filter | Niedrigster Verlustfaktor, exzellent     |
| **X7R/X5R MLCC**      | ⚠️ Nur Entkopplung      | Mikrofonie + DC-Bias-Derating bis -80%   |
| **Elektrolyt**        | Bulk-Entkopplung        | Nur Versorgung, nicht im Signalpfad      |

#### Op-Amps

- **Low-Noise**: $e_n$ < 5 nV/√Hz (z.B. OPA1612, NE5532, LME49710)
- **Slew Rate**: ≥ 10 V/µs; **PSRR**: ≥ 80 dB bei 1 kHz

#### Spannungsregler

- **Low-Noise LDO** für Analog-Versorgung (< 10 µV RMS, z.B. TPS7A47, LT3045)
- **Keine Schaltregler** direkt für Audio — wenn nötig: Schaltregler → LC-Filter → LDO

---

## 5. PCB-Layout & Routing

### Massekonzept (wichtigste Regel!)

- **Ungeteilte GND-Fläche auf B.Cu** — KEIN physischer Split
- Analoge, digitale und Power-Rückströme durch **Bauteil-Platzierung räumlich trennen**, nicht durch Schlitze
- Splits erzwingen Umwege für Rückstrom → größere Schleifenflächen → mehr Störeinkopplung
- **Sternpunkt**: Alle Masserückführungen treffen sich an einem Punkt (idealerweise am Versorgungseingang)
- **Rückstrompfade bewusst führen**: Bei NF fließt Rückstrom auf dem Weg des geringsten Widerstands, bei HF direkt unter der Signaltrace
- **Keine Leiterbahnen die die Massefläche unter ICs zerschneiden**
- Power-GND-Rückströme dürfen **nicht durch den Analog-Bereich** fließen

### Bauteil-Platzierung

1. **Steckverbinder** zuerst — definieren die Board-Geometrie
2. **ICEpower-Modul / Leistungsbauteile** — thermisch korrekt, eigener Bereich
3. **Audio-ICs** in eigenem Analog-Bereich, kurze Verbindungen
4. **Entkopplungskondensatoren** direkt am zugehörigen IC
5. **Digitale Bauteile** räumlich getrennt vom Analog-Bereich
6. **Passive, Testpunkte** in verbleibende Flächen

Weitere Regeln:

- **Bauteile an 0.5mm / 1.27mm Raster** ausrichten
- **Gleiche Orientierung** bei R/C (erleichtert Bestückung)
- **Wärmequellen** von temperatursensitiven Bauteilen fernhalten

### Routing-Richtlinien

#### Trace-Breiten

| Anwendung         | Empfohlen  | Strom (1oz Cu, 10°C ΔT) |
| ----------------- | ---------- | ----------------------- |
| Signal (Standard) | 0.2–0.25mm | ~0.3A                   |
| Audio-Signal      | 0.3mm      | —                       |
| Power (1A)        | 0.5mm      | ~1A                     |
| Power (3A+)       | 1.5mm+     | ~3A+                    |
| Speaker           | 1.5mm      | hoher Strom             |

#### Via-Design

| Parameter    | JLCPCB Min | Standard |
| ------------ | ---------- | -------- |
| Via-Pad      | 0.45mm     | 0.6mm    |
| Via-Bohrung  | 0.2mm      | 0.3mm    |
| Annular Ring | 0.125mm    | 0.15mm   |

#### Audio-Signalführung

- **Audio-Traces auf Top-Layer** (B.Cu für ununterbrochene Massefläche freihalten)
- **Keine Vias im Audio-Signalpfad** — jeder Via ist ein Impedanzsprung
- **Guard-Traces**: GND-Leiterbahnen beidseitig um empfindliche Audio-Eingangssignale, mit Vias zur Massefläche alle 5 mm
- **Via-Stitching**: GND-Vias beidseitig entlang Audio-Traces (alle 5–10 mm)
- **Keine Kreuzungen** — wenn unvermeidlich, rechtwinklig (90°) kreuzen
- **Audio-Traces niemals parallel zu digitalen Signalen** (Mindestabstand ≥ 3 mm, zu Power ≥ 5 mm)
- **Differentielle Paare**: Gleiche Länge, gleicher Abstand, als Paar routen

#### Allgemeine Routing-Regeln

- **45°-Winkel** statt 90° Ecken
- **Keine Stubs** (offene Leiterbahn-Enden)
- **Massefläche**: GND-Pour auf B.Cu, möglichst wenige Unterbrechungen
- **Via-Stitching**: GND-Vias regelmäßig verteilen
- **Teardrops** an Pad-/Via-Übergängen aktivieren

### Störquellen-Management

- **Schaltregler ≥ 20 mm** von Audio-Eingangsstufe; geschirmte Induktivitäten bevorzugen
- **Keine Schaltregler-Traces unter Audio-ICs**
- **Taktquellen weit weg** von Audio-Eingängen; Seriendämpfungswiderstände (22–47 Ω) in Clock-Leitungen
- **EMI-Filter** (π-Filter: C-L-C) zwischen Schaltregler und Audio-Versorgung

### Eingangs- und Ausgangsschutz

- **ESD**: TVS-Dioden (bidirektional) an allen externen Audio-Steckverbindern
- **DC-Blocking**: Koppelkondensator (Film/C0G, ≥ 1 µF) am Eingang
- **EMI-Tiefpass**: Serienwiderstand (47–100 Ω) + Keramik-C (100 pF–1 nF) gegen GND am Eingang
- **Ausgang**: Zobel-Netzwerk; bei Class-D: LC-Ausgangsfilter lt. Datenblatt

### Silkscreen

- Mindestens **0.8 mm Texthöhe**, 0.15 mm Strichstärke
- **Pin-1- und Polaritätsmarkierung** bei ICs, Elkos, Dioden
- **Kein Silkscreen auf Pads**
- Board-Info: Projektname, Version, Datum

---

## 6. ICEpower Module Integration

- **Datenblatt-Pins genau beachten**: Pin-Belegung variiert je nach Modul
- **Steckverbinder-Footprints**: Exakt nach Modul-Datenblatt wählen
- **Masse-Anbindung**: Niederohmig, breite Kupferflächen
- **Versorgungseingänge**: Ausreichend dimensionierte Leiterbahnen (Strom beachten!)
- **Signalpfade kurz halten**: Audio-Eingänge nah am Modul
- **Abblock-Kondensatoren**: Direkt am Modulanschluss
- **ENABLE/MUTE-Pins**: Beschaltung lt. Datenblatt (Pullup/Pulldown + RC-Verzögerung)
- **Sense-Leitungen**: Kelvin-Verbindung direkt am Lautsprecheranschluss (falls gefordert)

### Thermisches Design

- **Thermal Pads**: Via-Array (mind. 5×5, Bohrung 0.3 mm, Raster 1.0–1.2 mm)
- **Kupferflächen**: Top + Bottom für Wärmeableitung nutzen
- **Keine Bauteile über Hot-Spots**
- **Kühlkörper**: M3-Schraubbefestigung mit Wärmeleitpad vorsehen

---

## 7. JLCPCB Design Rules & Fertigung

### Minimale Design-Regeln

| Regel                | Minimum | Empfehlung |
| -------------------- | ------- | ---------- |
| Leiterbahnbreite     | 0.1mm   | ≥ 0.15mm   |
| Leiterbahnabstand    | 0.1mm   | ≥ 0.15mm   |
| Annular Ring         | 0.125mm | ≥ 0.15mm   |
| Bohrung (PTH)        | 0.2mm   | ≥ 0.3mm    |
| Pad-Größe (min)      | 0.45mm  | ≥ 0.6mm    |
| Board-Edge zu Kupfer | 0.2mm   | ≥ 0.3mm    |
| Silkscreen-Höhe      | 0.8mm   | ≥ 1.0mm    |

### Netzklassen

| Netzklasse   | Clearance | Track Width | Via Size | Via Drill | Beschreibung                |
| ------------ | --------- | ----------- | -------- | --------- | --------------------------- |
| Default      | 0.2mm     | 0.25mm      | 0.6mm    | 0.3mm     | Standard-Signale            |
| Power        | 0.2mm     | 0.5mm       | 0.8mm    | 0.4mm     | Versorgung, hohe Ströme     |
| Audio_Input  | 0.25mm    | 0.3mm       | 0.6mm    | 0.3mm     | Empfindliche Audio-Eingänge |
| Audio_Output | 0.2mm     | 0.5mm       | 0.6mm    | 0.3mm     | Audio-Ausgänge              |
| Audio_Power  | 0.2mm     | 0.8mm       | 0.8mm    | 0.4mm     | Analoge Versorgung          |
| Speaker      | 0.3mm     | 1.5mm       | 0.8mm    | 0.4mm     | Lautsprecherausgänge        |
| HV           | 0.5mm     | 0.3mm       | 0.8mm    | 0.4mm     | > 50V Signale               |

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

### Gerber-Export

**Layer (2-Layer):** F.Cu, B.Cu, F.Paste, B.Paste, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, Edge.Cuts

**Optionen:** Protel-Extensions ✅ | Tent Vias ✅ | Subtract Soldermask from Silkscreen ✅ | Check Zone Fills ✅

**Drill:** Millimeters, Decimal, Absolute Origin

### SMT Assembly (JLCPCB)

- **Basic Parts bevorzugen** ($0 Setup) — Extended Parts kosten $3/unique part
- **Fiducials**: Mindestens 3 Stück (1 mm Pad, 2 mm Öffnung) bei SMT-Bestückung
- Export: `export_bom` + `export_position_file`

---

## 8. Checkliste vor Fertigung

### Schaltplan

- [ ] ERC fehlerfrei (`run_erc`)
- [ ] Low-Noise Op-Amps ausgewählt
- [ ] Entkopplung: 100 nF C0G + 10 µF an jedem IC-Versorgungspin
- [ ] Feedback-Widerstände: Metallfilm, ±1%
- [ ] Kein X7R/X5R im Audio-Signalpfad
- [ ] Zobel-Netzwerk am Verstärkerausgang
- [ ] ESD-Schutz an allen externen Steckverbindern
- [ ] Muting-Schaltung vorhanden
- [ ] Analoge und digitale Versorgung getrennt geregelt

### PCB-Layout

- [ ] DRC fehlerfrei (`run_drc`)
- [ ] Alle Netze verbunden (keine Ratsnest-Linien)
- [ ] Massefläche unter Audio-Signalpfaden ununterbrochen
- [ ] Audio-Traces auf Top-Layer, keine unnötigen Vias
- [ ] Guard-Traces um empfindliche Audio-Eingänge
- [ ] Schaltregler ≥ 20 mm von Audio-Eingangsstufe
- [ ] Sternpunkt-Masse korrekt implementiert
- [ ] Entkopplungskondensatoren direkt an IC-Pins (< 3 mm)
- [ ] Thermal Vias unter Thermal Pads
- [ ] Via-Stitching entlang Audio-Traces

### Fertigung

- [ ] Board-Outline geschlossen (Edge.Cuts)
- [ ] Vias getented
- [ ] Silkscreen nicht auf Pads
- [ ] Fiducials vorhanden (wenn SMT Assembly)
- [ ] Gerber + Drill exportiert und im Viewer verifiziert
- [ ] BOM + Centroid exportiert
- [ ] JLCPCB Basic Parts bevorzugt

### Klangqualität

- [ ] SNR-Ziel definiert (> 100 dB)
- [ ] THD+N Budget (< 0.01% bei 1 kHz)
- [ ] Crosstalk zwischen Kanälen minimiert (> 70 dB)
- [ ] Keine Mikrofonie-empfindlichen Bauteile im Signalpfad

---

## 9. Kern-Prinzipien — IMMER befolgen!

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
