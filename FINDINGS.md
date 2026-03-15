# Aurora DSP IcePower Booster — Quality Gate & Implementierungsplan

**Datum:** 2025-07-25  
**Schaltplan-Stand:** 142 Bauteile, 343 Wires, ERC 0 Violations  
**Analyse-Methode:** Automatisierte Python-Skripte gegen `.kicad_sch` + manuelle Verifikation

---

## 1. Schaltungsübersicht

### Signalkette (pro Kanal, 6 identisch)

```
XLR Female In (J1–J6)
  │ Pin 2 (Hot), Pin 3 (Cold), Pin 1 (GND)
  ▼
[Stufe 1: Differenzieller Receiver] — LM4562 OPA-A, G = 1
  4× 10kΩ 0.1% → CMRR ~62 dB
  ▼ Single-Ended
[Stufe 2: Gain-Stufe] — LM4562 OPA-B, invertierend
  Rf = 10kΩ, Rin_base = 10kΩ
  3× DIP-Switch-Widerstände parallel zu Rin
  → Gain: 0 dB bis +11.3 dB (8 Stufen)
  ▼ Invertiert
[Stufe 3: Balanced Driver] — separater LM4562 (U7–U12)
  OPA-A: Buffer G = +1 → XLR Pin 3 (Cold)
  OPA-B: Inverter G = −1 → XLR Pin 2 (Hot)
  2× 47Ω Serien-R an Ausgängen
  ▼
XLR Male Out (J7–J12)
```

### DIP-Switch Gain-Tabelle

| SW3 | SW2 | SW1 | Rin_eff  | Gain   | dB       |
|-----|-----|-----|----------|--------|----------|
|  0  |  0  |  0  | 10.00 kΩ | 1.00×  |  0.0 dB  |
|  0  |  0  |  1  |  7.50 kΩ | 1.33×  | +2.5 dB  |
|  0  |  1  |  0  |  6.00 kΩ | 1.67×  | +4.4 dB  |
|  0  |  1  |  1  |  5.00 kΩ | 2.00×  | +6.0 dB  |
|  1  |  0  |  0  |  4.29 kΩ | 2.33×  | +7.4 dB  |
|  1  |  0  |  1  |  3.75 kΩ | 2.67×  | +8.5 dB  |
|  1  |  1  |  0  |  3.33 kΩ | 3.00×  | +9.5 dB  |
|  1  |  1  |  1  |  2.73 kΩ | 3.66×  | +11.3 dB |

**Topologie verifiziert:** DIP-Switch-Widerstände (R_SW1 = 30 kΩ, R_SW2 = 15 kΩ, R_SW3 = 7.5 kΩ) sind parallel zu Rin verbunden (net labels CH1_RX_OUT ↔ CH1_SUMNODE im DIP-Bereich bestätigen dies). Die Schaltung **verstärkt** — kein Abschwächer.

### Spannungsversorgung

```
24V DC Steckernetzteil → J13 (DC-Buchse)
  ▼
TEL 5-2422 (U13) — DC/DC Wandler
  ├── +12V (250 mA) → C25 (100nF), C35 (10µF)
  └── −12V (250 mA) → C26 (100nF), C36 (10µF)
       ▼                              ▼
ADP7118 (U14) — pos. LDO          ADP7182 (U15) — neg. LDO
  +12V → +11V                       −12V → −11V
  C37 (100nF in), C38 (10µF out)    C37/C38 (shared footprint IDs)
       ▼                              ▼
     V+ Rail                        V− Rail
  → alle LM4562 VCC+               → alle LM4562 VCC−
```

---

## 2. Quality Gate Ergebnisse

### ✅ Bestanden (15 Checks)

| # | Check | Ergebnis |
|---|-------|----------|
| 1 | Dateistruktur (.kicad_pro, .kicad_sch, .kicad_pcb) | ✅ Vorhanden |
| 2 | Bauteil-Referenzen (142 unique) | ✅ Vollständig |
| 3 | LM4562 Dual-Unit-Zuordnung (12 ICs × 2 Units) | ✅ Korrekt |
| 4 | 6 identische Kanäle | ✅ Validiert |
| 5 | Kanal-Netzlabels (CH1…CH6_RX_OUT, _SUMNODE, _GAIN_OUT) | ✅ Alle vorhanden |
| 6 | Power-Netze (V+, V−, GND, +12V, −12V, +24V) | ✅ Korrekt |
| 7 | Diff-Receiver-Widerstände (4× 10 kΩ 0.1%) | ✅ Pro Kanal |
| 8 | Gain-Widerstände (Rin = 10 kΩ, Rf = 10 kΩ) | ✅ Pro Kanal |
| 9 | DIP-Switch-Widerstände (30k, 15k, 7.5k) | ✅ Pro Kanal |
| 10 | Driver-Widerstände (3× 10 kΩ + 2× 47 Ω) | ✅ Pro Kanal |
| 11 | PSU-Topologie (TEL5-2422 + ADP7118 + ADP7182) | ✅ Korrekt |
| 12 | Bypass-Kondensatoren (100nF pro Versorgungspin) | ✅ Vorhanden |
| 13 | Wire-Integrität (343 Wires, keine offenen Enden) | ✅ OK |
| 14 | ERC (Electrical Rules Check) | ✅ 0 Violations |
| 15 | Bauteilwerte konsistent über alle Kanäle | ✅ Identisch |

### ⚠️ Warnungen (2)

| # | Check | Befund | Auswirkung |
|---|-------|--------|------------|
| H1 | Bypass-Cap-Wertstring | 12× "100n" statt "100nF C0G" | Fertigung: Dielektrikum nicht spezifiziert |
| H2 | Footprint-Zuweisung | 0 von 154 Instanzen zugewiesen | PCB-Layout nicht möglich |

### ❌ Fehlend (5)

| # | Check | Soll (lt. Design Rules) | Ist | Prio |
|---|-------|-------------------------|-----|------|
| F1 | Zobel-Netzwerk | 10 Ω + 100 nF am Verstärkerausgang | Fehlt komplett | 3 |
| F2 | TVS-Dioden | Bidirektional an allen XLR-Steckern | Fehlt komplett | 4 |
| F3 | DC-Koppelkondensatoren | ≥ 1 µF Film/C0G am Eingang | Fehlt komplett | 1 |
| F4 | EMI-Eingangsfilter | 47–100 Ω + 100 pF–1 nF pro Pin | Fehlt komplett | 5 |
| F5 | Muting-Schaltung | Einschalt-/Ausschalt-Muting | Fehlt komplett | 2 |

---

## 3. Headroom-Analyse

### Pegelberechnung bei +4 dBu Eingang (Pro-Line-Level)

| Stufe | Signal | Vpeak | Vclip | Headroom |
|-------|--------|-------|-------|----------|
| XLR-Eingang | +4 dBu (diff.) = 1.228 V RMS | 1.74 V | — | — |
| Nach Diff-Receiver (G=1) | +4 dBu (SE) = 1.228 V RMS | 1.74 V | ±10 V | 18.2 dB |
| Gain 0 dB | +4 dBu = 1.228 V RMS | 1.74 V | ±10 V | 18.2 dB |
| Gain +11.3 dB (max) | +15.3 dBu = 4.49 V RMS | 6.35 V | ±10 V | 3.9 dB |
| Balanced Driver (G=±1) | +15.3 dBu pro Arm | 6.35 V | ±10 V | 3.9 dB |
| Balanced Ausgang (diff.) | +21.3 dBu = 8.98 V RMS | — | +25.2 dBu | 3.9 dB |

**Clip-Punkt balanced:** +25.2 dBu (±10 V × 2 Arme = 14.14 V RMS diff.)

**Bewertung:**
- Bei 0 dB Gain: **18.2 dB Headroom** — exzellent
- Bei +11.3 dB Gain: **3.9 dB Headroom** — ausreichend, da DSP-Limiter im Aurora vorgeschaltet
- Bei +4 dBu Eingang clippt nichts bei keiner Gain-Einstellung ✅

### Stromverbrauch

| Abschnitt | Strom | Quelle |
|-----------|-------|--------|
| 12× LM4562 (Quiescent) | 12 × 5.5 mA = 66 mA | Datenblatt |
| Signal-Strom (max. 6 Kanäle) | ~30 mA | Berechnet |
| PSU + LDO Eigenverbrauch | ~15 mA | Datenblatt |
| **Gesamt** | **~111 mA** pro Rail | |
| TEL 5-2422 Kapazität | 250 mA pro Rail | Datenblatt |
| **Reserve** | **~139 mA (56%)** | ✅ Ausreichend |

---

## 4. Implementierungsplan

### Prio 1: DC-Koppelkondensatoren (Eingang)

**Zweck:** DC-Offset-Blockierung am Audio-Eingang. Verhindert, dass DC-Spannung von der Quelle in den Diff-Receiver gelangt und Offset-Probleme verursacht.

**Schaltung (pro Kanal, 2 Stück):**
```
XLR Pin 2 (Hot)  ──┤├── R1 (10kΩ) → Diff-Receiver +
XLR Pin 3 (Cold) ──┤├── R2 (10kΩ) → Diff-Receiver −
                  C_DC
                 2.2µF
```

**Bauteile:** 12× 2.2 µF, C0G oder Polypropylen-Film, ≥ 25V  
**Baugröße:** 0805 (C0G bei 2.2 µF evtl. 1206 nötig) oder Film THT  

**Spannungsabfall-Analyse:**
- $X_C$ bei 20 Hz: $\frac{1}{2\pi \times 20 \times 2.2\mu} = 3.62\,\Omega$
- Last: 10 kΩ (Diff-Receiver-Eingangsimpedanz pro Pin)
- Verlust: $20 \cdot \log_{10}\left(\frac{10000}{10000 + 3.62}\right) = -0.003\,\text{dB}$
- $f_{-3\text{dB}} = \frac{1}{2\pi \times 10000 \times 2.2\mu} = 7.2\,\text{Hz}$ (weit unter 20 Hz)
- **Signalverlust: vernachlässigbar** ✅

**Implementierung im Schaltplan:**
1. Neue Bauteil-Referenzen: C39–C50 (12 Stück, 2 pro Kanal)
2. Jeweils in Serie zwischen XLR-Pin und erstem Diff-Receiver-Widerstand einfügen
3. Neue Netzlabels: CHx_IN_HOT_AC, CHx_IN_COLD_AC (nach Koppelkondensator)

---

### Prio 2: Muting-Schaltung (Einschaltschutz)

**Zweck:** Unterdrückt Pop-/Klickgeräusche beim Ein-/Ausschalten. Beim Einschalten brauchen die LDOs und Op-Amps ~50 ms, bis die Arbeitspunkte stabil sind.

**Variante A: Ausgangs-Relay (empfohlen für Audio-Qualität)**
```
                    ┌──── V+ (über RC-Verzögerung)
                    │
                  [Relay]
                    │
Driver Out ────────┤NO├──── XLR Out
                    │
                   GND
```
- 1× Bistabiles Signal-Relay (z.B. Omron G6K-2F-Y) pro 2 Kanäle (DPDT)
- RC-Verzögerung: 100 kΩ + 100 µF = τ = 10 s → Relay schaltet ~1 s nach Power-On
- NPN-Transistor (BC847) als Relay-Treiber
- Freilaufdiode (1N4148) parallel zur Relayspule

**Variante B: LDO-Enable-Verzögerung (einfacher, weniger Bauteile)**
```
+24V ──[100kΩ]──┬── EN (ADP7118/ADP7182)
                 │
               [100µF]
                 │
                GND
```
- LDOs starten verzögert → Op-Amps erhalten Versorgung erst nach ~1 s
- Kein Signal-Relay nötig
- Nachteil: Kein aktives Muting beim Ausschalten (Cap-Entladung = undefinierbares Abschalten)

**Empfehlung: Variante B** — weniger Bauteile, ausreichend für DIY-Booster-Board. Die LDOs haben eingebautes Soft-Start. Zusätzliche RC-Verzögerung am EN-Pin reicht aus.

**Bauteile (Variante B):** 2× 100 kΩ, 2× 100 µF Keramik/Elektrolyt  
**Spannungsabfall:** Keiner — Muting greift nur beim Ein-/Ausschalten, nicht im Signalpfad ✅

**Implementierung:**
1. RC-Glied an EN-Pin von U14 (ADP7118) und U15 (ADP7182)
2. Neue Bauteile: R79–R80 (100 kΩ), C51–C52 (100 µF)

---

### Prio 3: Zobel-Netzwerk (Ausgangsstabilisierung)

**Zweck:** Stabilisiert den Op-Amp bei kapazitiver Last (lange Kabel, kapazitive Eingänge). Ohne Zobel kann der LM4562 bei >1 nF Lastkapazität schwingen.

**Schaltung (pro Ausgangspin, 12 Stück):**
```
Driver Out (nach 47Ω) ──┬── XLR Out
                         │
                      [10Ω]
                         │
                      [100nF]
                         │
                        GND
```

**Bauteile:** 12× 10 Ω (0805), 12× 100 nF C0G (0805)  
**Gesamt:** 24 neue Bauteile

**Spannungsabfall-Analyse:**
- Zobel ist ein **Shunt-Element** (parallel zur Last) — kein Serienwiderstand im Signalpfad
- Bei 20 kHz: $Z_{Zobel} = 10 + \frac{1}{2\pi \times 20000 \times 100n} = 10 + 79.6 = 89.6\,\Omega$
- Parallel zu typischer Last (10 kΩ): $Z_{parallel} = \frac{10000 \times 89.6}{10000 + 89.6} = 88.8\,\Omega$
- Strombelastung des Op-Amps steigt minimal (< 1 mA zusätzlich bei 20 kHz)
- **Signalverlust: 0 dB** (kein Serienelement) ✅

**Implementierung:**
1. Neue Referenzen: R81–R92 (10 Ω), C53–C64 (100 nF C0G)
2. Platzierung: Direkt am XLR-Ausgang, nach den 47 Ω Serienwiderständen
3. GND-Anbindung über kurze Traces + Via zur Massefläche

---

### Prio 4: TVS-Dioden (ESD-Schutz)

**Zweck:** Schutz gegen elektrostatische Entladung an den XLR-Steckern. Pro-Audio-Equipment wird regelmäßig ein-/ausgesteckt — ESD bis ±8 kV möglich.

**Schaltung (pro Audio-Pin, 24 Stück):**
```
XLR Pin 2/3 ──┬── [DC-Block] → Receiver
               │
            [TVS]
               │
              GND
```

**Bauteile:** 24× TVS-Diode, bidirektional  
- Empfehlung: **PESD5V0S1BL** (SOD-323) — $V_{WM}$ = 5 V, $C_j$ = 0.35 pF, $I_{PP}$ = 10.5 A
- Alternativ: **PRTR5V0U2X** (SOT-363) — 2-Kanal, spart Platz (12 Stück statt 24)

**Spannungsabfall-Analyse:**
- TVS ist ein **Shunt-Element** — leitet nur bei Überspannung
- Im Normalbetrieb: $I_{leak}$ < 1 µA → **0 dB Signalverlust**
- Parasitäre Kapazität 0.35 pF: Bei 20 kHz → $X_C = 22.7\,\text{MΩ}$ → vernachlässigbar
- **Signalverlust: 0 dB** ✅

**Implementierung:**
1. Neue Referenzen: D1–D24 (oder D1–D12 bei 2-Kanal-TVS)
2. Platzierung: So nah wie möglich am XLR-Stecker auf PCB
3. Kurze GND-Anbindung — separates GND-Via direkt am TVS-Pad

---

### Prio 5: EMI-Eingangsfilter

**Zweck:** Unterdrückt hochfrequente Störungen (Mobilfunk, WLAN, Schaltregler-EMI) am Audio-Eingang. Verhindert Demodulation in den Op-Amp-Eingangsstufen.

**Schaltung (pro XLR-Eingangspin, 12 Stück R + 12 Stück C):**
```
XLR Pin 2/3 ──[47Ω]──┬──[DC-Block]── R_diff → Receiver
                       │
                    [100pF]
                       │
                      GND
```

**Bauteile:** 12× 47 Ω (0805), 12× 100 pF C0G (0805)  
**Gesamt:** 24 neue Bauteile

**Spannungsabfall-Analyse:**
- RC-Tiefpass: $f_c = \frac{1}{2\pi \times 47 \times 100p} = 33.9\,\text{MHz}$ — weit über Audioband
- Serienwiderstand 47 Ω in 10 kΩ Last (pro Pin):
  - Verlust: $20 \cdot \log_{10}\left(\frac{10000}{10000 + 47}\right) = -0.041\,\text{dB}$
- Audio bei 20 kHz: $X_C(100\text{pF}) = 79.6\,\text{kΩ}$ → kein messbarer Shunt-Verlust
- CMRR-Einfluss: 47 Ω Mismatch (1% Toleranz = 0.47 Ω) → $\text{CMRR}_{R_{EMI}} = 20 \cdot \log_{10}\left(\frac{10000}{0.47}\right) = 86.6\,\text{dB}$ → besser als bestehende 62 dB durch Diff-Receiver-Matching
- **Signalverlust: −0.04 dB** (vernachlässigbar) ✅

**Implementierung:**
1. Neue Referenzen: R93–R104 (47 Ω), C65–C76 (100 pF C0G)
2. Platzierung: Direkt an XLR-Eingangs-Pads, vor DC-Koppelkondensator
3. Reihenfolge Signal: XLR → EMI-R → EMI-C nach GND → DC-Block → Diff-Receiver

---

### Prio 6: Bypass-Cap-Wertstrings korrigieren

**Zweck:** Korrekte Bauteilbezeichnung für Fertigung/BOM. Der Wert "100n" spezifiziert kein Dielektrikum — bei JLCPCB-Bestückung könnte ein X7R statt C0G gewählt werden.

**Änderung:** 12× Wertstring von `100n` auf `100nF C0G` ändern  
**Betroffene Bauteile:** C1, C2, C5, C6, C9, C10, C13, C14, C17, C18, C21, C22

**Spannungsabfall:** Keiner — reine Dokumentationsänderung ✅

**Implementierung:**
1. Python-Skript: Regex-Replace im `.kicad_sch`
2. Alle `(value "100n")` → `(value "100nF C0G")` für betroffene Referenzen

---

### Prio 7: Footprint-Zuweisung

**Zweck:** PCB-Layout erfordert physische Footprints für jede Bauteilinstanz.

**Zuweisung:**

| Bauteil | Footprint | Package |
|---------|-----------|---------|
| R (alle) | Resistor_SMD:R_0805_2012Metric | 0805 |
| C 100nF, 100pF | Capacitor_SMD:C_0805_2012Metric | 0805 |
| C 10µF | Capacitor_SMD:C_0805_2012Metric | 0805 (X5R) |
| C 2.2µF (DC-Block) | Capacitor_SMD:C_1206_3216Metric | 1206 (C0G/Film) |
| C 100µF (Muting) | Capacitor_SMD:C_1210_3225Metric | 1210 (Keramik) oder THT Elko |
| LM4562 | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm | SOIC-8 |
| TEL 5-2422 | Converter_DCDC:Converter_DCDC_TRACO_TEL5_DIP-24 | DIP-24 |
| ADP7118 | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm | SOIC-8 |
| ADP7182 | Package_TO_SOT_SMD:SOT-23-5 | TSOT-5 |
| XLR Female | Connector_Audio:XLR-F_Neutrik_NC3FBH2 | THT |
| XLR Male | Connector_Audio:XLR-M_Neutrik_NC3MBH | THT |
| DIP-Switch 3-Pos | Button_Switch_SMD:SW_DIP_SPSTx03_Slide_Omron_A6S-310x | SMD |
| TVS (PESD5V0S1BL) | Diode_SMD:D_SOD-323 | SOD-323 |
| DC-Buchse | Connector_BarrelJack:BarrelJack_Horizontal | THT |

**Spannungsabfall:** Keiner — reine Layout-Vorbereitung ✅

**Implementierung:**
1. KiCad-Schaltplaneditor → Footprint-Zuweisungstool
2. Oder: Python-Skript für Bulk-Zuweisung im `.kicad_sch`
3. Anschließend `sync_schematic_to_board()` ausführen

---

## 5. Quality Gate: Spannungsabfall-Gesamtanalyse

### Kompletter Signalpfad nach allen Modifikationen

```
XLR In → [EMI 47Ω] → [100pF→GND] → [DC-Block 2.2µF] → [Diff-Rx G=1]
  → [Gain 0..+11.3 dB] → [Balanced Driver G=±1] → [47Ω Serie]
  → [Zobel 10Ω+100nF→GND] → XLR Out
         ↑                                                   ↑
       [TVS→GND]                                          [TVS→GND]
```

### Serienverluste (Worst Case: 600 Ω Last)

| Element | Serien-Z | Last-Z | Verlust | Anmerkung |
|---------|----------|--------|---------|-----------|
| EMI-Filter (47 Ω × 2) | 94 Ω diff. | 20 kΩ | −0.04 dB | Diff-Receiver-Eingang |
| DC-Block (2.2 µF @ 20 Hz) | 3.62 Ω × 2 | 20 kΩ | −0.003 dB | Unter Audioband |
| 47 Ω Ausgangs-R (bestand) | 47 Ω × 2 | 600 Ω* | −1.17 dB | Worst Case 600 Ω |
| | | 10 kΩ | −0.08 dB | Typisch |

*600 Ω ist eine theoretische Worst-Case-Last. Typische Audio-Eingänge haben 10–47 kΩ Eingangsimpedanz.

### Shunt-Elemente (kein Serienverlust)

| Element | Typ | Verlust |
|---------|-----|---------|
| Zobel (10 Ω + 100 nF) | Shunt | 0 dB |
| TVS-Diode | Shunt (nur bei ESD) | 0 dB |
| EMI-C (100 pF) | Shunt | 0 dB bei Audio |

### Gesamtverlust durch neue Schutzbeschaltung

| Szenario | Zusätzlicher Verlust | Bemerkung |
|----------|---------------------|-----------|
| Typisch (10 kΩ Last) | **−0.05 dB** | EMI + DC-Block |
| Worst Case (600 Ω Last) | **−0.21 dB** | EMI + DC-Block (47 Ω Ausgangs-R war vorher schon da) |

### Ergebnis

| Parameter | Vor Modifikation | Nach Modifikation | Delta |
|-----------|------------------|-------------------|-------|
| Gain-Bereich | 0 bis +11.3 dB | 0 bis +11.3 dB | **±0 dB** |
| Max. Ausgang (balanced) | +25.2 dBu | +25.2 dBu | **±0 dB** |
| Headroom @ +4 dBu, G=0 dB | 18.2 dB | 18.2 dB | **±0 dB** |
| Headroom @ +4 dBu, G=+11.3 dB | 3.9 dB | 3.9 dB | **±0 dB** |
| Zusätzl. Serienverlust (10 kΩ) | — | −0.05 dB | Vernachlässigbar |
| Untere Grenzfrequenz (−3 dB) | DC | 7.2 Hz | Weit unter 20 Hz |

**Fazit: Die Booster-Funktion bleibt vollständig erhalten.** Die Schutzbeschaltung fügt maximal 0.05 dB Serienverlust hinzu (typisch), was messtechnisch nicht nachweisbar ist. Kein Gain geht verloren, kein Headroom wird reduziert.

---

## 6. Zusammenfassung der neuen Bauteile

### Stückliste Modifikationen

| Prio | Element | Neue Teile | Referenzen |
|------|---------|------------|------------|
| 1 | DC-Koppelkondensatoren | 12× 2.2 µF C0G/Film | C39–C50 |
| 2 | Muting (EN-Verzögerung) | 2× 100 kΩ, 2× 100 µF | R79–R80, C51–C52 |
| 3 | Zobel-Netzwerke | 12× 10 Ω, 12× 100 nF C0G | R81–R92, C53–C64 |
| 4 | TVS-Dioden | 24× PESD5V0S1BL | D1–D24 |
| 5 | EMI-Filter | 12× 47 Ω, 12× 100 pF C0G | R93–R104, C65–C76 |
| 6 | Cap-Value-Fix | 0 (nur Wertänderung) | — |
| 7 | Footprints | 0 (nur Zuweisung) | — |
| **Gesamt** | | **86 neue Bauteile** | |

### Neue Bauteilanzahl nach Modifikation

| Kategorie | Vorher | Nachher | Delta |
|-----------|--------|---------|-------|
| Widerstände | 78 | 104 | +26 |
| Kondensatoren | 38 | 64 | +26 |
| Dioden | 0 | 24 | +24 |
| ICs | 15 | 15 | ±0 |
| Steckverbinder | 13 | 13 | ±0 |
| Schalter | 6 | 6 | ±0 |
| Sonstiges | 4 | 14 | +10 |
| **Total** | **154** | **240** | **+86** |

---

## 7. Empfohlene Reihenfolge der Umsetzung

1. **Prio 6** — Cap-Values korrigieren (schnell, kein neues Bauteil)
2. **Prio 1** — DC-Koppelkondensatoren einfügen (Schaltplan-Änderung, neue Netze)
3. **Prio 5** — EMI-Filter einfügen (vor DC-Block, neue Netze)
4. **Prio 3** — Zobel-Netzwerke einfügen (am Ausgang, neue Netze)
5. **Prio 4** — TVS-Dioden einfügen (Shunt, einfach)
6. **Prio 2** — Muting-Schaltung (PSU-Bereich, EN-Pin-Beschaltung)
7. **Prio 7** — Footprint-Zuweisung (als letztes, braucht finale BOM)

Zwischen jedem Schritt: **ERC ausführen** und **Snapshot erstellen**.

---

*Generiert aus automatisierter Analyse der `.kicad_sch`-Datei. Alle Berechnungen basieren auf nominalen Bauteilwerten.*
