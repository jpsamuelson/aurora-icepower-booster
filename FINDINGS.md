# Aurora DSP IcePower Booster — Schaltplan-Review & Fehlerdokumentation

**Datum:** 2025-07-27 (aktualisiert, ersetzt Version 2025-07-25)
**Schaltplan-Stand:** ~263 Bauteile, 130 Netze, ~5233 Zeilen in `.kicad_sch`
**ERC-Status:** 0 Errors, 911 Warnings (910× endpoint_off_grid, 1× multiple_net_names)
**PCB-Status:** Vollständig geroutet (Freerouting), Production-Files exportiert — **ABER basierend auf fehlerhaftem Schaltplan!**
**Git HEAD:** d022139 (main)
**Analyse-Methode:** Netlist-Export + Python-Skripte + Datenblatt-Vergleich + manuelle Pin-Level-Verifikation

---

## 1. Projektziel & Beschreibung

### Zweck

Der **Aurora DSP IcePower Booster** ist ein professionelles 6-Kanal Balanced Audio Interface Board. Es sitzt zwischen einem DSP-Prozessor (Aurora DSP) und ICEpower Class-D Verstärkermodulen. Das Board hat folgende Aufgaben:

1. **Balanced-zu-Single-Ended-Wandlung** (Differenzieller Receiver) des DSP-Ausgangssignals
2. **Einstellbare Verstärkung** (0 dB bis +11.3 dB) über DIP-Switches pro Kanal
3. **Re-Balancierung** des Signals (Balanced Driver) für die ICEpower-Module
4. **Schutzschaltungen**: ESD (TVS-Dioden), EMI-Filter, DC-Blocking, Zobel-Netzwerke
5. **Muting-Schaltung**: Einschaltverzögerung via BSS138 MOSFET + LDO-Enable
6. **Saubere Spannungsversorgung**: 24V DC → DC/DC ±12V → LDO ±11V (Low-Noise)

### Hardware-Spezifikationen

| Parameter | Wert |
|-----------|------|
| Kanäle | 6 (identisch) |
| Eingang | 6× XLR Female (Balanced, Pin 2 = Hot) |
| Ausgang | 6× XLR Male (Balanced, Pin 2 = Hot) |
| Versorgung | 24V DC Steckernetzteil (Barrel Jack) |
| Gain-Bereich | 0 dB bis +11.3 dB (8 Stufen, DIP-Switch) |
| Max. Ausgangspegel | +25.2 dBu (balanced) |
| Op-Amp | LM4562 (12 Stück, Dual) |
| SNR-Ziel | > 100 dB |
| THD+N-Ziel | < 0.01% @ 1 kHz |
| Fertigung | JLCPCB, 2-Layer, FR-4, HASL |
| Board-Größe | 200 × 200 mm, abgerundete Ecken |

### Signalkette (pro Kanal, 6× identisch)

```
XLR Female In (J3–J8)
  │ Pin 1 (GND), Pin 2 (Hot), Pin 3 (Cold)
  ▼
[ESD-Schutz] — 2× PESD5V0S1BL (TVS, SOD-323)
  ▼
[EMI-Filter] — 2× 47Ω + 2× 100pF C0G (fc = 33.9 MHz)
  ▼
[DC-Blocking] — 2× 2.2µF C0G (f-3dB = 7.2 Hz)
  ▼
[Stufe 1: Differenzieller Receiver] — LM4562 OPA-A (z.B. U2A), G = 1
  4× 10kΩ 0.1% Metallfilm → CMRR ~62 dB
  ▼ Single-Ended (CHx_RX_OUT)
[Stufe 2: Gain-Stufe] — LM4562 OPA-B (z.B. U2B), invertierend
  Rf = 10kΩ, Rin_base = 10kΩ
  3× DIP-Switch-Widerstände (30k, 15k, 7.5k) parallel zu Rin
  → Gain: 0 dB bis +11.3 dB (8 Stufen)
  ▼ Invertiert (CHx_GAIN_OUT)
[Muting] — BSS138 MOSFET (Q2–Q7), Source → GND, Drain → CHx_GAIN_OUT
  ▼
[Stufe 3: Balanced Driver] — separater LM4562 (U7–U12)
  OPA-A: Non-inverting Buffer G = +1 → CHx_OUT_COLD → 47Ω → XLR Pin 3
  OPA-B: Inverting G = −1 → CHx_OUT_HOT → 47Ω → XLR Pin 2
  ▼
[Zobel-Netzwerk] — 10Ω + 100nF (pro Ausgangspin)
  ▼
[Ausgangs-Schutz] — 2× PESD5V0S1BL (TVS)
  ▼
XLR Male Out (J9–J14)
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

### Spannungsversorgung

```
24V DC Steckernetzteil → J13 (DC-Buchse)
  ▼
TEL 5-2422 (U1) — DC/DC Isolierter Wandler, DIP-24
  ├── +12V (250 mA) → C35 (100µF), C25 (100nF)
  └── −12V (250 mA) → C36 (100µF), C26 (100nF)
       ▼                              ▼
ADP7118ARDZ-11 (U14) — pos. LDO   ADP7182AUJZ-11 (U15) — neg. LDO
  +12V → +11V, SOIC-8                −12V → −11V, SOT-23-5
  C25 (100nF in), C37 (10µF out)     C26 (100nF in), C38 (10µF out)
  SS-Pin → C81 (100nF)               NR-Pin → C82 (100nF)
       ▼                              ▼
     V+ Rail (+11V)                 V− Rail (−11V)
  → alle 12× LM4562 Pin 8          → alle 12× LM4562 Pin 4
  → je 100nF C0G Entkopplung       → je 100nF C0G Entkopplung
```

### REMOTE / Enable-Steuerung

```
REMOTE Jack (J14, 3.5mm) → D25 (SMBJ15CA TVS) → R105 (10k) → C79 (100nF)
  → SW7 (SPDT: ALWAYS / REMOTE) → EN_CTRL → U14.EN + U15.EN
  → R79 (100k Pullup zu +12V), R80 (100k Pullup zu -12V)
```

### Muting-Schaltung (BSS138 MOSFETs)

```
Q1: Gate = MUTE_CTRL, Source = GND, Drain = /MUTE (Master-Mute-Netz)
Q2–Q7: Gate = MUTE (via Netz), Source = GND, Drain = CHx_GAIN_OUT
```

Wenn MUTE = LOW (LDOs noch nicht aktiv): Q2–Q7 sperren, Gain-Ausgang wird nicht belastet.
Wenn MUTE = HIGH (LDOs aktiv, Einschaltverzögerung abgelaufen): Q2–Q7 leiten, Audio fließt.

### Bauteil-Inventar (validiert)

| Typ | Anzahl | Details |
|-----|--------|---------|
| LM4562 (Dual Op-Amp) | 12 | U2–U13, SOIC-8 |
| TEL5-2422 (DC/DC) | 1 | U1, DIP-24 |
| ADP7118ARDZ-11 (pos. LDO) | 1 | U14, SOIC-8 |
| ADP7182AUJZ-11 (neg. LDO) | 1 | U15, SOT-23-5 |
| BSS138 (N-MOSFET) | 7 | Q1–Q7, SOT-23 |
| PESD5V0S1BL (TVS) | 24 | D2–D25, SOD-323 |
| SMBJ15CA (TVS, REMOTE) | 1 | D1, SMB |
| BLM18PG221 (Ferrite Bead) | 2 | FB1–FB2 |
| SW_DIP_x03 | 6 | SW1–SW6 |
| SW_SPDT | 1 | SW7 (ALWAYS/REMOTE) |
| XLR Female (Eingang) | 6 | J3–J8 |
| XLR Male (Ausgang) | 6 | J9–J14 |
| Barrel Jack (24V) | 1 | J13 |
| AudioJack2 (REMOTE) | 1 | J14 |
| 10kΩ 0.1% (Metallfilm) | 36 | Diff-Receiver |
| 10kΩ | 20 | Gain, Driver, Pullups |
| 47Ω | 24 | Ausgangs-Serien-R, EMI-Filter |
| 10Ω | 12 | Zobel-Netzwerk |
| 30kΩ | 6 | DIP-Switch SW1 |
| 15kΩ | 6 | DIP-Switch SW2 |
| 7.5kΩ | 6 | DIP-Switch SW3 |
| 100kΩ | 3 | Pullups (REMOTE, EN) |
| 100nF C0G | 43 | Entkopplung, Filter |
| 100pF C0G | 12 | EMI-Filter |
| 2.2µF C0G | 12 | DC-Blocking |
| 10µF X5R | 8 | Bulk-Entkopplung |
| 100µF Elko | 4 | PSU Bulk |
| **Gesamt** | **~263** | |

---

## 2. KRITISCHE FEHLER — Schaltplan-Review (2025-07-27)

### Zusammenfassung

| ID | Schwere | Fehler | Auswirkung | Fix-Abhängigkeit |
|----|---------|--------|------------|-----------------|
| **F1** | 🔴 KRITISCH | GND und CH1_OUT_COLD sind dasselbe Netz (189 Pins) | Gesamtes Board funktionsunfähig | Root Cause für F2, F3, F7, F8 |
| **F2** | 🔴 KRITISCH | XLR-Eingang Pin 2 (Hot) auf GND für alle 6 Kanäle | Audio-Eingang kurzgeschlossen | Folge von F1 |
| **F3** | 🔴 KRITISCH | XLR-Ausgang Pin 3 (Cold) auf GND für alle 6 Kanäle | Balanced-Ausgang kaputt, CH2–6_OUT_COLD fehlen | Folge von F1 |
| **F4** | 🔴 KRITISCH | Diff-Receiver hat Positives Feedback | Oszillation statt Verstärkung | Unabhängig von F1 |
| **F5** | 🟠 MITTEL | R2.Pin1 unverbunden (CH1 Rgnd) | Dangling-Widerstand | Unabhängig |
| **F6** | 🟠 MITTEL | R4/R6/R8/R10/R12 beide Pins auf HOT_IN (CH2–6) | 0Ω Kurzschluss (Rgnd) | Unabhängig |
| **F7** | 🟠 MITTEL | Zobel Cold-Seite auf GND statt CHx_OUT_COLD | Zobel-Netzwerk unwirksam (Cold-Arm) | Folge von F1 |
| **F8** | 🟠 MITTEL | Ausgangs-47Ω R58–R63 (Cold) → GND statt CHx_OUT_COLD | Ausgangspuffer kurzgeschlossen (Cold) | Folge von F1 |
| **F9** | 🟡 KOSMETISCH | ADP7118 lib_id = ACPZN, Value = ARDZ-11 | Keine funktionale Auswirkung, Pinout identisch | Unabhängig |

### F1: GND = /CH1_OUT_COLD Netz-Merge (ROOT CAUSE) 🔴

**ERC-Meldung:** `Both CH1_OUT_COLD and GND are attached to the same items; CH1_OUT_COLD will be used in the netlist`

**Symptom:** Im exportierten Netlist hat `/CH1_OUT_COLD` **189 Pins** — das gesamte GND-Netz. `/GND` hat **0 Pins**. Die Netze `CH2_OUT_COLD` bis `CH6_OUT_COLD` existieren im Netlist **gar nicht**, obwohl 6 Labels pro Kanal im Schaltplan vorhanden sind.

**Root Cause — BSS138 Muting-Transistoren:**

Die BSS138 MOSFETs (Q1–Q7) haben ihren Source-Pin (Pin 2) an Drähten, die sowohl ein "GND"-Label als auch ein "CH1_OUT_COLD"-Label tragen. KiCad merged zwei Netze, wenn verschiedene Labels auf demselben Draht oder derselben Wire-Chain liegen. Da "CH1_OUT_COLD" alphabetisch vor "GND" kommt, gewinnt es als Netzname.

```
Netlist-Analyse (Q1–Q7):
  Q1: Gate = Net-(Q1-G),  Source = /CH1_OUT_COLD (= GND!),  Drain = /MUTE
  Q2: Gate = Net-(Q2-G),  Source = /CH1_OUT_COLD (= GND!),  Drain = /CH1_GAIN_OUT
  Q3: Gate = Net-(Q3-G),  Source = /CH1_OUT_COLD (= GND!),  Drain = /CH2_GAIN_OUT
  Q4: Gate = Net-(Q4-G),  Source = /CH1_OUT_COLD (= GND!),  Drain = /CH3_GAIN_OUT
  Q5: Gate = Net-(Q5-G),  Source = /CH1_OUT_COLD (= GND!),  Drain = /CH4_GAIN_OUT
  Q6: Gate = Net-(Q6-G),  Source = /CH1_OUT_COLD (= GND!),  Drain = /CH5_GAIN_OUT
  Q7: Gate = Net-(Q7-G),  Source = /CH1_OUT_COLD (= GND!),  Drain = /CH6_GAIN_OUT
```

**Wichtig:** Im Schaltplan gibt es **0 power:GND Symbole**. Alle 143 GND-Verbindungen nutzen reguläre Labels (`net_class_flag`), keine Power-Symbole. Das verschärft das Problem, weil KiCad bei regulären Labels keinen Vorrang für Power-Netze hat.

**Kaskaden-Effekt von F1:**
- F2: XLR-Eingang Pin 2 (Hot) landet auf CH1_OUT_COLD = GND → Audio Eingang kurzgeschlossen
- F3: XLR-Ausgang Pin 3 (Cold) landet auf CH1_OUT_COLD = GND → Balanced-Ausgang nur Hot
- F7: Zobel Cold-Pin → auf GND statt auf echtem Cold-Signal
- F8: Ausgangs-47Ω Cold → auf GND statt auf Balanced-Driver-Ausgang
- CH2–6_OUT_COLD Labels existieren im Schaltplan, aber ihre Netze werden ebenfalls in den GND-Merge gezogen

**Fix-Strategie (F1):**
1. Die Wire-Chain, die GND und CH1_OUT_COLD verbindet, muss physisch getrennt werden
2. BSS138 Source-Pins müssen auf einem eigenen GND-Draht liegen, der NICHT mit CH1_OUT_COLD-Drähten verbunden ist
3. Idealerweise: Power-GND-Symbole (`power:GND`) statt regulärer Labels verwenden, damit KiCad die Netz-Hierarchie korrekt auflöst
4. Nach dem Fix: Alle CHx_OUT_COLD Netze müssen als eigenständige Netze im Netlist erscheinen

### F2: XLR-Eingang Pin 2 (Hot) auf GND 🔴

**Befund (alle 6 Kanäle):**

| Kanal | XLR | Pin 1 (GND) | Pin 2 (Hot) | Pin 3 (Cold) | Pin G (Shell) |
|-------|-----|-------------|-------------|--------------|---------------|
| CH1 | J3 | GND ✅ | GND ❌ (soll: CH1_HOT_IN) | CH1_COLD_RAW ✅ | GND ✅ |
| CH2 | J4 | GND ✅ | GND ❌ (soll: CH2_HOT_IN) | CH2_COLD_RAW ✅ | GND ✅ |
| CH3 | J5 | GND ✅ | GND ❌ (soll: CH3_HOT_IN) | CH3_COLD_RAW ✅ | GND ✅ |
| CH4 | J6 | GND ✅ | GND ❌ (soll: CH4_HOT_IN) | CH4_COLD_RAW ✅ | GND ✅ |
| CH5 | J7 | GND ✅ | GND ❌ (soll: CH5_HOT_IN) | CH5_COLD_RAW ✅ | GND ✅ |
| CH6 | J8 | GND ✅ | GND ❌ (soll: CH6_HOT_IN) | CH6_COLD_RAW ✅ | GND ✅ |

**Auswirkung:** Das Hot-Signal vom DSP wird direkt auf GND kurzgeschlossen. Kein Audio-Signal gelangt in den Diff-Receiver.

**Ursache:** Folge von F1 — das Wire-Netz, das Pin 2 mit dem EMI-Filter verbindet, trägt ein Label, das im gemergten CH1_OUT_COLD/GND-Netz landet.

### F3: XLR-Ausgang Pin 3 (Cold) auf GND 🔴

**Befund (alle 6 Kanäle):**

| Kanal | XLR | Pin 1 (GND) | Pin 2 (Hot) | Pin 3 (Cold) |
|-------|-----|-------------|-------------|--------------|
| CH1 | J9  | GND ✅ | CH1_OUT_HOT ✅ | GND ❌ (soll: CH1_OUT_COLD) |
| CH2 | J10 | GND ✅ | CH2_OUT_HOT ✅ | GND ❌ (soll: CH2_OUT_COLD) |
| CH3 | J11 | GND ✅ | CH3_OUT_HOT ✅ | GND ❌ (soll: CH3_OUT_COLD) |
| CH4 | J12 | GND ✅ | CH4_OUT_HOT ✅ | GND ❌ (soll: CH4_OUT_COLD) |
| CH5 | J13 | GND ✅ | CH5_OUT_HOT ✅ | GND ❌ (soll: CH5_OUT_COLD) |
| CH6 | J14 | GND ✅ | CH6_OUT_HOT ✅ | GND ❌ (soll: CH6_OUT_COLD) |

**Auswirkung:** Der Balanced-Ausgang hat nur den Hot-Arm. Cold ist auf GND → unbalanced Ausgang, 6 dB weniger Pegel, keine Gleichtaktunterdrückung.

### F4: Differenzieller Receiver — Positives Feedback 🔴

**Soll-Topologie (Standard-Diff-Receiver):**
```
               Rf (10k, 0.1%)
          ┌─────────────────────┐
          │                     │
Hot ──[Rin]──┤(−) INV           │
              │     LM4562  OUT├──┤── CHx_RX_OUT
Cold ──[Rin]──┤(+) NINV        │
              │                │
         [Rgnd]                │
              │                │
             GND               │
                               │
              Rf geht von OUT nach (−) INV = NEGATIVES Feedback ✅
```

**Ist-Zustand im Schaltplan (CH1, U2):**
```
               R20 (10k, 0.1%)
          ┌─────────────────────┐
          │                     │
Hot ──[R14]──┤(+) NINV          │    ← R20 geht von (+) nach OUT!
              │     LM4562  OUT├──┤── CH1_RX_OUT
Cold ──[R15]──┤(−) INV         │
              │                │
         [R2]                  │
              │                │
             GND (dangling!)   │
                               │
              R20 geht von HOT_IN(+) nach OUT = POSITIVES Feedback ❌
```

**Das gleiche Problem in CH2–CH6** (R21–R25 statt R20).

**Auswirkung:** Positives Feedback → der Op-Amp wird als Komparator arbeiten und sofort an die Rail sättigen. Kein Audio-Signal, nur DC am Ausgang.

**Fix:** Die Feedback-Widerstände R20–R25 müssen von INV_IN(−) nach RX_OUT gehen, nicht von HOT_IN(+) nach RX_OUT.

### F5: R2.Pin1 unverbunden (CH1 Rgnd) 🟠

**Befund:** Im Netlist hat R2 nur einen Pin verbunden (Pin 2). Pin 1 ist `unconnected` / floating.

R2 ist der Rgnd-Widerstand im Diff-Receiver von CH1 (10kΩ, von NINV(+) nach GND). Wenn Pin 1 unverbunden ist, hat der nicht-invertierende Eingang keinen definierten DC-Pfad → Offset-Drift.

**Fix:** R2.Pin1 korrekt mit dem NINV(+)-Knoten verbinden.

### F6: R4/R6/R8/R10/R12 — Beide Pins auf HOT_IN (CH2–CH6 Rgnd) 🟠

**Befund:**
- CH2: R4 Pin 1 = CH2_HOT_IN, Pin 2 = CH2_HOT_IN → 0Ω Kurzschluss
- CH3: R6 Pin 1 = CH3_HOT_IN, Pin 2 = CH3_HOT_IN → 0Ω Kurzschluss
- CH4: R8 Pin 1 = CH4_HOT_IN, Pin 2 = CH4_HOT_IN → 0Ω Kurzschluss
- CH5: R10 Pin 1 = CH5_HOT_IN, Pin 2 = CH5_HOT_IN → 0Ω Kurzschluss
- CH6: R12 Pin 1 = CH6_HOT_IN, Pin 2 = CH6_HOT_IN → 0Ω Kurzschluss

Es sind Rgnd-Widerstände (10kΩ, NINV(+) → GND). Ein Pin sollte am NINV(+)-Knoten sein, der andere an GND.

**Fix:** Jeweils ein Pin muss auf GND gehen, der andere auf den NINV(+)-Knoten des Diff-Receivers.

### F7: Zobel Cold-Seite auf GND 🟠

Die Zobel-Netzwerke am Cold-Ausgang (10Ω + 100nF in Serie, Shunt nach GND) wären im aktuellen Zustand am GND-Netz statt am echten CHx_OUT_COLD-Signal angeschlossen. Wird automatisch behoben wenn F1 gelöst ist.

### F8: Output-47Ω R58–R63 Cold → GND 🟠

Die 47Ω Serien-Widerstände am Cold-Ausgang der Balanced Driver gehen aktuell ins GND-Netz statt zu den XLR-Ausgangs-Pins. Wird automatisch behoben wenn F1 gelöst ist.

### F9: ADP7118 Symbol ACPZN vs. ARDZ (Kosmetisch) 🟡

**Befund:**
- lib_id im Schaltplan: `Regulator_Linear:ADP7118ACPZN` (4-pin LFCSP Variante)
- Value-Feld: `ADP7118ARDZ-11` (8-pin SOIC Variante)
- Footprint: `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` (korrekt für ARDZ)

**Bewertung:** Beide Varianten (ACPZN und ARDZ) haben **identisches Pinout** (1=VOUT, 2=SENSE, 3=GND, 4=EN, 5=SS, 6=VIN, 7=GND). Der Unterschied ist nur das Package. Da der Footprint korrekt als SOIC-8 zugewiesen ist, hat dies **keine funktionale Auswirkung**. Es ist ein rein kosmetisches Problem im Schaltplan.

---

## 3. IC-Pinout-Validierung (gegen Datenblätter)

Alle verwendeten ICs wurden Pin-für-Pin gegen ihre Datenblätter geprüft:

### LM4562 (TI, Dual Op-Amp, SOIC-8) ✅

| Pin | Funktion | Schaltplan | Status |
|-----|----------|-----------|--------|
| 1 | Output A | OUT_A | ✅ |
| 2 | Inverting Input A | IN_A(-) | ✅ |
| 3 | Non-Inverting Input A | IN_A(+) | ✅ |
| 4 | V- | V- | ✅ |
| 5 | Non-Inverting Input B | IN_B(+) | ✅ |
| 6 | Inverting Input B | IN_B(-) | ✅ |
| 7 | Output B | OUT_B | ✅ |
| 8 | V+ | V+ | ✅ |

### TEL5-2422 (TRACO, DC/DC Isoliert, DIP-24) ✅

| Pin | Funktion | Schaltplan | Status |
|-----|----------|-----------|--------|
| 1 | +VIN | +24V_IN | ✅ |
| 7 | -VIN | GND | ✅ |
| 14 | -VOUT | -12V | ✅ |
| 18 | COM | GND | ✅ |
| 24 | +VOUT | +12V | ✅ |

### ADP7118 (ADI, pos. LDO, SOIC-8) ✅

| Pin | Funktion | Schaltplan | Status |
|-----|----------|-----------|--------|
| 1 | VOUT | V+ | ✅ |
| 2 | SENSE | V+ (tied) | ✅ |
| 3 | GND | GND | ✅ |
| 4 | EN | EN_CTRL | ✅ |
| 5 | SS | SS_U14 (100nF) | ✅ |
| 6 | VIN | +12V | ✅ |
| 7 | GND | GND | ✅ |

### ADP7182 (ADI, neg. LDO, SOT-23-5) ✅

| Pin | Funktion | Schaltplan | Status |
|-----|----------|-----------|--------|
| 1 | GND | GND | ✅ |
| 2 | VIN | -12V | ✅ |
| 3 | EN | EN_CTRL | ✅ |
| 4 | ADJ/NR | NR_U15 (100nF) | ✅ |
| 5 | VOUT | V- | ✅ |

### BSS138 (ON Semi, N-MOSFET, SOT-23) ✅

| Pin | Funktion | Schaltplan | Status |
|-----|----------|-----------|--------|
| 1 | Gate | MUTE / Qx-G | ✅ |
| 2 | Source | GND (SOLL) | ❌ auf CH1_OUT_COLD (→ F1) |
| 3 | Drain | MUTE / CHx_GAIN_OUT | ✅ |

---

## 4. Validierte Teilschaltungen (OK)

### Entkopplung ✅
- 12× 100nF C0G am V+ Pin (Pin 8) jedes LM4562
- 12× 100nF C0G am V- Pin (Pin 4) jedes LM4562
- Bulk: 100µF + 100nF am DC/DC, 10µF + 100nF an jedem LDO

### Gain-Stufe ✅
- Invertierende Topologie: Rf = 10kΩ, Rin = 10kΩ (Basis-Gain = 0 dB)
- DIP-Switch Widerstände korrekt parallel zu Rin
- Gain-Bereich 0 dB bis +11.3 dB bestätigt

### ESD-Schutz ✅
- 24× PESD5V0S1BL an allen XLR-Audio-Pins (12 Ein + 12 Aus)
- 1× SMBJ15CA am REMOTE-Eingang
- Parasitäre Kapazität 0.35 pF — vernachlässigbar im Audioband

### EMI-Filter ✅ (aber Hot-Pfad durch F1 auf GND)
- 2× 47Ω + 2× 100pF pro Kanal
- fc = 33.9 MHz — weit über Audioband

### DC-Blocking ✅
- 12× 2.2µF C0G
- f-3dB = 7.2 Hz — vernachlässigbar

### Zobel-Netzwerk ✅ (Hot-Seite korrekt, Cold-Seite durch F1 auf GND)
- 10Ω + 100nF pro Ausgangspin

---

## 5. Fix-Priorisierung & Reihenfolge

```
Fix-Reihenfolge:
═══════════════

1. F1 → GND/CH1_OUT_COLD Netz-Merge trennen (ZUERST!)
   │     ├── BSS138 Source-Drähte von CH1_OUT_COLD-Wire-Chain trennen
   │     ├── Power:GND Symbole statt regulärer Labels verwenden
   │     └── Verifizieren: 6 eigenständige CHx_OUT_COLD Netze im Netlist
   │
   ├── F2 löst sich automatisch (XLR Hot nicht mehr auf GND)
   ├── F3 löst sich automatisch (XLR Cold bekommt CHx_OUT_COLD)
   ├── F7 löst sich automatisch (Zobel Cold korrekt)
   └── F8 löst sich automatisch (Output 47Ω Cold korrekt)

2. F4 → Diff-Receiver Feedback korrigieren
   │     ├── R20–R25: Von HOT_IN(+) → RX_OUT  umverdrahten auf  INV_IN(-) → RX_OUT
   │     └── Prüfen: Negative Feedback Schleife → Gain = 1 (Unity)
   │
3. F5 → R2.Pin1 verbinden (CH1 Rgnd)
   │
4. F6 → R4/R6/R8/R10/R12 korrigieren (CH2–6 Rgnd)
   │     └── Jeweils ein Pin auf GND, anderer auf NINV(+)-Knoten
   │
5. F9 → ADP7118 Symbol-Name (optional, kosmetisch)

Nach allen Fixes:
  → ERC erneut ausführen (Ziel: 0 Errors, <911 Warnings)
  → Netlist exportieren und verifizieren
  → PCB "Update from Schematic" ausführen
  → Komplett neu routen (Freerouting) — bisheriges Routing ist ungültig
  → DRC erneut ausführen
  → Production-Files neu exportieren
```

---

## 6. Headroom-Analyse (unverändert gültig nach Fix)

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

### Stromverbrauch

| Abschnitt | Strom |
|-----------|-------|
| 12× LM4562 (Quiescent) | 66 mA |
| Signal-Strom (max. 6 Kanäle) | ~30 mA |
| PSU + LDO Eigenverbrauch | ~15 mA |
| **Gesamt** | **~111 mA pro Rail** |
| TEL 5-2422 Kapazität | 250 mA pro Rail |
| **Reserve** | **~139 mA (56%)** ✅ |

---

## 7. PCB-Layout-Status

**Aktueller Zustand:** Vollständig geroutet und Production-Files exportiert (Commit d022139).

**WARNUNG:** Das PCB basiert auf dem fehlerhaften Schaltplan. Nach Fix der Schaltplan-Fehler F1–F8 muss das PCB **komplett neu synchronisiert und neu geroutet** werden. Die existierenden Production-Files (Gerber, BOM, Position) sind **UNGÜLTIG** und dürfen nicht zur Fertigung verwendet werden.

### Board-Daten (Referenz)

| Parameter | Wert |
|-----------|------|
| Dimension | 200 × 200 mm |
| Layer | 2 (F.Cu + B.Cu) |
| Footprints | 269 |
| Trace Segments | 1543 |
| Vias | 743 |
| DRC | 0 Errors, 0 Unconnected, 195 Warnings |

---

## 8. Analyse-Skripte (zur Referenz)

Die folgenden Analyse-Skripte wurden während des Reviews erstellt und können bei Bedarf erneut ausgeführt werden:

| Skript | Zweck |
|--------|-------|
| `/tmp/netlist_analysis.py` | Netlist parsen, alle Netze + Pin-Zuordnungen anzeigen |
| `/tmp/full_validation.py` | BSS138 Muting, XLR Pins, IC Pinout, Passive Counts |
| `/tmp/detailed_validation.py` | Diff-Receiver Topologie, Gain/Buffer/Output Stufen, Entkopplung, Zobel |
| `/tmp/extract_lib_symbols.py` | Alle 26 lib_symbol Pin-Definitionen extrahieren |
| `/tmp/check_out_cold.py` | GND-Symbole vs Labels prüfen (0 power:GND bestätigt) |

**Hinweis:** Diese Skripte liegen in `/tmp/` und überleben keinen Neustart. Bei Bedarf neu erstellen.

---

## 9. Git-Historie (relevant)

```
d022139  Production: Gerber, Drill, BOM, Position Files
56dceab  PCB: Fertigungsvorbereitung - Dangling Vias, Silkscreen
bf62bd0  PCB: F.Cu Zone auf Solid-Connect, Zone Refill via pcbnew
84ccfa1  PCB: Zone Fill nach Freerouting
31b9dca  PCB: Freerouting autoroute + Netzklassen + Design Rules
0345eaa  PCB: GND-Via cleanup, F.Cu zone, courtyard fixes
ed28379  PCB: MCP-Routing entfernt + Platzierung korrigiert (sauberes Board)
99568f2  PCB: 26 Footprints + 10 Netze + Netzklassen + GND-Via-Stitching
176f876  FB1/FB2: Symbol von Device:L auf Device:FerriteBead geändert
d7fbc73  Schaltplan-Review: 4 Phasen implementiert
```

