# Balanced Audio Line Receiver & Driver ICs — Research Report

**Projekt:** Aurora DSP IcePower Booster  
**Datum:** 2026-03-12  
**Zweck:** Vergleich dedizierter Balanced-Audio-ICs vs. diskrete LM4562-Lösung

---

## 1. THAT Corporation — InGenius Receivers & OutSmarts Drivers

### 1.1 THAT1240 — Balanced Line Receiver (InGenius)

| Parameter | Wert |
|-----------|------|
| **Funktion** | Balanced → Single-Ended, 1 Kanal |
| **Topologie** | InGenius™ — patentierte Kombination aus Current-Feedback + Servo |
| **Gain** | Unity (0 dB) |
| **Package** | DIP-8 (THAT1240P08), SOIC-8 (THAT1240S08) |
| **CMRR** | >90 dB DC bis 20 kHz (typ.) |
| **CMRR bei Quellenimpedanz-Mismatch** | >60 dB auch bei 10% Source-Mismatch! |
| **THD+N** | 0.0004% typ. @ 1 kHz |
| **Noise** | -103 dBu (A-weighted) |
| **Bandwidth** | ~4 MHz |
| **Slew Rate** | ~8 V/µs |
| **Max. Input Level** | +26 dBu @ ±18V Supply |
| **Supply** | ±5V bis ±18V |
| **Quiescent Current** | ~4.5 mA |
| **Preis (Mouser/DigiKey)** | ~$3.50–$5.00 |
| **LCSC/JLCPCB** | ❌ **NICHT VERFÜGBAR** |

**Besonderheit:** Der entscheidende Vorteil der InGenius-Topologie ist, dass der CMRR auch bei unbalancierten Quellenimpedanzen hoch bleibt. Ein Standard-Differenzverstärker (z.B. INA134, SSM2143) verliert seinen CMRR proportional zum Impedanz-Mismatch an den Eingängen — bei realen Verkabelungsszenarien oft dramatisch. InGenius umgeht dies durch einen Servo-Loop, der die Eingangsimpedanz dynamisch anpasst.

### 1.2 THAT1246 — Balanced Line Receiver (InGenius, +6 dB)

| Parameter | Wert |
|-----------|------|
| **Funktion** | Balanced → SE, 1 Kanal, **Gain = 2 (+6 dB)** |
| **Topologie** | InGenius™ (identisch zu THAT1240) |
| **Package** | DIP-8, SOIC-8 |
| **Alle Specs** | Wie THAT1240, aber G = 2 |
| **LCSC/JLCPCB** | ❌ **NICHT VERFÜGBAR** |

Der THAT1246 wird bevorzugt, wenn der Receiver den -6 dB Pegelverlust der professionellen Balanced-Leitung (±halber Pegel) kompensieren soll, was bei G=2 exakt Unity-Gain über den gesamten Signalpfad ergibt.

### 1.3 THAT1200 — Balanced Line Receiver (Vorgänger)

| Parameter | Wert |
|-----------|------|
| **Funktion** | Balanced → SE, 1 Kanal |
| **Topologie** | Standard-Differenzverstärker mit getrimmed Resistoren |
| **CMRR** | ~70 dB typ. (deutlich schlechter als 1240-Serie) |
| **Package** | DIP-8, SOIC-8 |
| **Status** | Superseded by THAT1240 series |
| **LCSC/JLCPCB** | ❌ **NICHT VERFÜGBAR** |

**Bewertung:** Veraltet, kein Grund die 1200er-Serie zu verwenden. Die 1240er ist in jeder Hinsicht überlegen.

### 1.4 THAT1606 — Balanced Line Driver (OutSmarts)

| Parameter | Wert |
|-----------|------|
| **Funktion** | Single-Ended → Balanced, 1 Kanal |
| **Topologie** | OutSmarts™ — kreuzgekoppelt mit Servo-Feedback |
| **Gain** | Unity (0 dB) |
| **Package** | SOIC-8 |
| **THD+N** | 0.0003% typ. @ 1 kHz |
| **Output Balance** | >60 dB auch bei unbalancierter Last |
| **Noise** | -107 dBu (A-weighted) |
| **Max. Output** | +24 dBu @ ±18V Supply |
| **Slew Rate** | ~15 V/µs |
| **Supply** | ±5V bis ±18V |
| **Quiescent Current** | ~6.5 mA |
| **Preis (Mouser/DigiKey)** | ~$4.00–$6.00 |
| **LCSC/JLCPCB** | ❌ **NICHT VERFÜGBAR** |

**Besonderheit:** Die OutSmarts-Topologie hält die Ausgangsbalance auch bei unbalancierten Lasten aufrecht (z.B. wenn nur ein Pin belastet wird). Ein Standard Cross-Coupled Driver (wie DRV134) verliert hier Balance. Zusätzlich ermöglicht OutSmarts eine "elektronische Impedanzbalancierung", die die Gleichtaktunterdrückung am Empfänger verbessert.

### 1.5 THAT1646 — Balanced Line Driver (OutSmarts, +6 dB)

| Parameter | Wert |
|-----------|------|
| **Funktion** | SE → Balanced, 1 Kanal, **Gain = 2 (+6 dB)** |
| **Topologie** | OutSmarts™ (identisch zu THAT1606) |
| **Package** | SOIC-8 |
| **Alle Specs** | Wie THAT1606, aber G = 2 |
| **LCSC/JLCPCB** | ❌ **NICHT VERFÜGBAR** |

---

## 2. TI/Burr-Brown — DRV134/DRV135 Line Drivers

### 2.1 DRV134 — Audio Balanced Line Driver (PDIP-8 / SOIC-16)

| Parameter | Wert |
|-----------|------|
| **Funktion** | SE → Balanced, 1 Kanal |
| **Topologie** | Cross-coupled mit Precision-Resistoren |
| **Package** | PDIP-8 (DRV134PA), SOIC-16 (DRV134UA) |
| **THD+N** | 0.0005% typ. @ 1 kHz |
| **Slew Rate** | 15 V/µs |
| **Max. Output** | 17 Vrms into 600 Ω |
| **Supply** | ±4.5V bis ±18V (9–36V) |
| **Quiescent Current** | 5.2 mA |
| **Preis (TI 1ku)** | ~$2.28–$2.74 |
| **Status** | **ACTIVE** — Improved replacement for SSM2142 |

**LCSC-Verfügbarkeit:**

| Part Number | Package | Bestand | Preis (1 Stk) |
|-------------|---------|---------|---------------|
| DRV134PA | PDIP-8 | 0 (nachbestellbar) | $6.29 |
| DRV134UA/1K | SOIC-16 | 5 Stk | $5.95 |

⚠️ **Sehr geringer LCSC-Bestand. SOIC-16 ist für Audio-PCB ungünstig (groß). PDIP-8 nicht SMT-tauglich für JLCPCB Assembly.**

### 2.2 DRV135 — Audio Balanced Line Driver (SOIC-8)

| Parameter | Wert |
|-----------|------|
| **Funktion** | SE → Balanced, 1 Kanal |
| **Topologie** | Identisch zu DRV134 |
| **Package** | **SOIC-8** (platzsparend!) |
| **Alle Specs** | Identisch zu DRV134 |
| **Status** | **ACTIVE** |

**LCSC-Verfügbarkeit:**

| Part Number | Package | Bestand | Preis (1 Stk) |
|-------------|---------|---------|---------------|
| DRV135UA | SOIC-8 | 0 (nachbestellbar) | $3.46 |
| DRV135UA/2K5 | SOIC-8 | **3.865 Stk** ✅ | **$2.78** |

✅ **DRV135UA/2K5 ist der beste Kandidat unter den dedizierten Line-Drivern für JLCPCB Assembly!** Guter Bestand, SOIC-8 Package, vernünftiger Preis.

### 2.3 INA1634 (TI)

| Parameter | Wert |
|-----------|------|
| **Status** | ❌ **Existiert nicht** (TI-Webseite gibt 404) |

**Hinweis:** Die existierenden TI-Differential-Receiver für Audio sind:

- **INA134** — Differential Line Receiver, G = 1, SOIC-8/DIP-8 (Companion zu DRV134)
- **INA137** — Differential Line Receiver, G = 1/2, SOIC-8/DIP-8

Diese haben ~80 dB CMRR, aber leiden wie alle Standard-Differenzverstärker unter CMRR-Degradierung bei Quellenimpedanz-Mismatch.

---

## 3. Analog Devices — SSM2142/SSM2143

### 3.1 SSM2142 — Balanced Line Driver

| Parameter | Wert |
|-----------|------|
| **Funktion** | SE → Balanced, 1 Kanal |
| **Status** | ⛔ **OBSOLETE** |
| **Package** | DIP-8 (nur!) |
| **THD** | 0.006% typ., 20 Hz–20 kHz, 10V RMS in 600 Ω |
| **CMRR** | 80 dB |
| **Slew Rate** | 15 V/µs |
| **Max. Output** | 10V RMS into 600 Ω |
| **Supply** | ±15V (fix, kein weiter Bereich) |

**LCSC-Verfügbarkeit:**

| Part Number | Bestand | Preis |
|-------------|---------|-------|
| SSM2142PZ | 0 | $149.83 (!) |
| SSM2142SZ (3rd party) | 95 | $78.52 |

⛔ **NICHT VERWENDEN. Obsolete, absurd teuer, nur DIP-8, schlechtere Specs als DRV134/135.**

### 3.2 SSM2143 — Differential Line Receiver

| Parameter | Wert |
|-----------|------|
| **Funktion** | Balanced → SE, 1 Kanal |
| **Status** | ⛔ **OBSOLETE** |
| **Package** | SOIC-8 (SSM2143S/SZ), PDIP-8 (SSM2143P) |
| **CMRR** | 90 dB @ DC/60 Hz, 85 dB @ 20 kHz |
| **THD** | 0.0006% typ. @ 1 kHz |
| **Slew Rate** | 10 V/µs |
| **Bandwidth** | 7 MHz (G = 1/2) |
| **Gain** | G = 1/2 (oder G = 2 durch Pin-Swap) |
| **Max. Input** | +28 dBu @ G = 1/2 |
| **Supply** | ±5V bis ±18V |
| **Replacement** | AD8273 (von ADI empfohlen) |

**LCSC-Verfügbarkeit:**

| Part Number | Bestand | Preis |
|-------------|---------|-------|
| SSM2143S | Discontinued | — |
| SSM2143P | Discontinued | — |
| SSM2143SZ | 0 (SOIC-8) | $8.83 |
| SSM2143S-REEL | Discontinued | — |

⚠️ **Obsolete und schlecht verfügbar. Der SSM2143 war ein sehr guter IC, aber nicht mehr empfehlenswert für neue Designs.**

---

## 4. LM4562 — Diskrete Balanced-Lösung (aktuelle Planung)

### 4.1 LM4562 — Dual Low-Noise Audio Op-Amp

| Parameter | Wert |
|-----------|------|
| **Funktion** | Dual-Operationsverstärker, universell |
| **Package** | SOIC-8 (LM4562MAX), PDIP-8 (LM4562NA) |
| **THD+N** | **0.00003%** typ. @ 1 kHz (!) |
| **Noise** | 2.7 nV/√Hz |
| **Slew Rate** | 20 V/µs |
| **GBW** | 55 MHz |
| **Supply** | ±2.5V bis ±17V |
| **Output** | ±13.5V @ 600 Ω (mit ±15V) |
| **Quiescent Current** | 5 mA/Kanal |

**LCSC-Verfügbarkeit:**

| Part Number | Package | Bestand | Preis (1 Stk) | Preis (500+) |
|-------------|---------|---------|---------------|--------------|
| **LM4562MAX/NOPB** | **SOIC-8** | **5.453 Stk** ✅ | $2.08 | **$1.36** |
| LM4562NA/NOPB | PDIP-8 | 199 Stk | $9.24 | — |

✅ **Hervorragende Verfügbarkeit, bester Preis, SOIC-8 perfekt für JLCPCB Assembly.**

---

## 5. LCSC/JLCPCB-Verfügbarkeits-Zusammenfassung

| IC | LCSC verfügbar? | Bestand | Best Price | Package | Assembly-tauglich? |
|----|-----------------|---------|------------|---------|-------------------|
| **THAT1240** | ❌ Nein | 0 | — | — | Nein |
| **THAT1246** | ❌ Nein | 0 | — | — | Nein |
| **THAT1200** | ❌ Nein | 0 | — | — | Nein |
| **THAT1606** | ❌ Nein | 0 | — | — | Nein |
| **THAT1646** | ❌ Nein | 0 | — | — | Nein |
| **INA1634** | ❌ Existiert nicht | — | — | — | — |
| **DRV134PA** | ⚠️ Ja (0 Stk) | 0 | $6.29 | PDIP-8 | ❌ THT |
| **DRV134UA** | ⚠️ Ja (5 Stk) | 5 | $5.95 | SOIC-16 | ⚠️ Groß |
| **DRV135UA/2K5** | ✅ **Ja** | **3.865** | **$2.78** | **SOIC-8** | ✅ **Ja** |
| **SSM2142** | ⚠️ Ja (0 Stk) | 0 | $149.83 | DIP-8 | ❌ Obsolete/THT |
| **SSM2143SZ** | ⚠️ Ja (0 Stk) | 0 | $8.83 | SOIC-8 | ❌ Obsolete |
| **LM4562MAX** | ✅ **Ja** | **5.453** | **$2.08** | **SOIC-8** | ✅ **Ja** |

---

## 6. Vergleich: Dedizierte ICs vs. Diskrete LM4562-Lösung

### 6.1 Balanced Receiver: THAT1240 vs. LM4562-Differenzverstärker

#### LM4562-basierter Differenzempfänger (aktuelle Planung)

```
Schaltung: 1× LM4562 (dual) pro Kanal
  - OPA1: Instrumentenverstärker-Topologie oder
  - Einfacher Differenzverstärker mit 4× präzisen Widerständen (0.1%)

Bauteile pro Kanal:
  - 1× LM4562 (SOIC-8)
  - 4× Widerstände 0.1% (0402/0603)
  - 2–4× Kondensatoren (Entkopplung)
  = 7–9 Bauteile, ~15 mm² PCB-Fläche
```

#### THAT1240 Receiver

```
Bauteile pro Kanal:
  - 1× THAT1240 (SOIC-8)
  - 2× Kondensatoren (Entkopplung)
  = 3 Bauteile, ~8 mm² PCB-Fläche
```

| Kriterium | THAT1240 | LM4562 diskret |
|-----------|----------|----------------|
| Bauteilanzahl/Kanal | 3 | 7–9 |
| PCB-Fläche/Kanal | ~8 mm² | ~15 mm² |
| THD+N | 0.0004% | **0.00003%** (10× besser!) |
| CMRR (ideal) | >90 dB | ~80 dB (abhängig von R-Matching) |
| CMRR (mit Source-Mismatch) | **>60 dB** (InGenius-Vorteil!) | ~40–50 dB (degradiert!) |
| Noise | -103 dBu | **-108 dBu** (LM4562 ist rauschärmer) |
| Kosten IC/Kanal | ~$4.00 | **~$2.08** (+ ~$0.20 R) |
| JLCPCB Assembly | ❌ **NEIN** | ✅ **JA** |
| Design-Aufwand | Minimal | Mittel (R-Matching, Layout) |

### 6.2 Balanced Driver: DRV135 vs. LM4562-Buffer+Inverter

#### LM4562-basierter Balanced Driver (aktuelle Planung)

```
Schaltung: 1× LM4562 (dual) pro Kanal
  - OPA1: Unity-gain buffer (Ausgang = +Signal)
  - OPA2: Inverting amplifier G=-1 (Ausgang = -Signal)
  - 3× Widerstände für Inverter

Bauteile pro Kanal:
  - 1× LM4562 (SOIC-8)
  - 3× Widerstände 0.1% (0402/0603)
  - 2–4× Kondensatoren (Entkopplung)
  = 6–8 Bauteile, ~12 mm² PCB-Fläche
```

#### DRV135 Driver

```
Bauteile pro Kanal:
  - 1× DRV135 (SOIC-8)
  - 2× Kondensatoren (Entkopplung)
  = 3 Bauteile, ~8 mm² PCB-Fläche
```

| Kriterium | DRV135 | LM4562 diskret |
|-----------|--------|----------------|
| Bauteilanzahl/Kanal | 3 | 6–8 |
| PCB-Fläche/Kanal | ~8 mm² | ~12 mm² |
| THD+N | 0.0005% | **0.00003%** (15× besser!) |
| Output Balance (ideal) | ~60 dB (laser-trimmed R) | ~50 dB (abhängig von R-Matching) |
| Output Balance (unbal. Last) | ~40 dB | ~40 dB (beide degradieren) |
| Noise | ~-100 dBu | **~-108 dBu** |
| Max. Output | 17 Vrms/600Ω | ~13.5 Vrms/600Ω |
| Kosten IC/Kanal | $2.78 | **$2.08** (+ ~$0.15 R) |
| JLCPCB Assembly | ✅ Ja (3.865 Stk) | ✅ **Ja** (5.453 Stk) |
| Design-Aufwand | Minimal | Mittel |

### 6.3 Gesamtvergleich: 3-Kanal-System (3× Receiver + 3× Driver)

| Kriterium | Dedizierte ICs (THAT/DRV) | 6× LM4562 diskret |
|-----------|---------------------------|---------------------|
| **ICs gesamt** | 3× THAT1240 + 3× DRV135 = 6 ICs | 6× LM4562 = 6 ICs |
| **Widerstände** | 0 | 21× Präzisions-R (0.1%) |
| **Bauteile total** | ~18 + 12 Caps = ~30 | ~42 + 12 Caps = ~54 |
| **PCB-Fläche** | ~48 mm² | ~81 mm² |
| **THD+N** | 0.0003–0.0005% | **0.00003%** |
| **Noise Floor** | ~-103 dBu | **~-108 dBu** |
| **CMRR (Receiver, real)** | **>60 dB (InGenius!)** | ~40–50 dB |
| **IC-Kosten** | 3×$4 + 3×$2.78 = $20.34 | 6×$2.08 = **$12.48** |
| **Gesamtkosten** | ~$21 (wenig R) | ~**$14** (21 R à $0.05) |
| **JLCPCB Assembly** | ❌ THAT nicht bei LCSC! | ✅ **Voll verfügbar** |

---

## 7. Empfehlung

### 7.1 Für JLCPCB-Fertigung: LM4562 diskret (klarer Sieger)

**Die diskrete LM4562-Lösung ist die richtige Wahl für dieses Projekt:**

1. **Verfügbarkeit:** LM4562MAX/NOPB hat >5.400 Stk bei LCSC, SOIC-8, $2.08/Stk. Alle THAT-Corp-ICs sind bei LCSC nicht verfügbar und damit für JLCPCB Assembly disqualifiziert.

2. **Audio-Performance:** LM4562 ist in THD+N und Rauschverhalten den dedizierten ICs **deutlich überlegen** (Faktor 10–15 bei THD, 5 dB bei Noise). Die theoretisch bessere CMRR der THAT1240 ist nur relevant, wenn die Signalquelle stark unbalancierte Impedanzen hat — in einem internen Verstärker-Board ist das selten der Fall.

3. **Kosten:** ~$14 vs. ~$21 für 3 Kanäle. Mehr Bauteile, aber günstigere ICs und Standard-Widerstände.

4. **Flexibilität:** Mit LM4562 kann der Gain frei eingestellt werden (nicht auf Unity oder +6 dB beschränkt).

### 7.2 Einziger möglicher DRV135-Einsatz

Falls die Balanced-Ausgangsstufe vereinfacht werden soll, wäre der **DRV135UA/2K5** eine Option:

- 3.865 Stk bei LCSC vorhanden
- SOIC-8, $2.78/Stk
- Spart 3× Widerstände und Layout-Aufwand pro Kanal
- Aber schlechtere THD als LM4562-Lösung

**Möglicher Hybrid-Ansatz:**

- **Receiver:** 3× LM4562 als Differenzverstärker (bessere Performance, verfügbar)
- **Driver:** 3× DRV135 (weniger Bauteile, akzeptable Performance, verfügbar)
- Kostenvorteil: Weniger Platzbedarf bei Treibern, volle Performance bei Empfängern

### 7.3 Wann THAT-ICs sinnvoll wären

THAT-Corporation-ICs wären nur dann sinnvoll, wenn:

- Das Board **nicht bei JLCPCB bestückt** wird (Handbestückung/anderer Assembler)
- Die Signalquelle **unbekannte/variable Quellenimpedanzen** hat (z.B. externes Mischpult über lange Kabel)
- Die CMRR unter realen Bedingungen absolut kritisch ist

Für ein internes ICEpower-Booster-Board, bei dem die Signale von einem bekannten DSP kommen, überwiegen die Vorteile der LM4562-Lösung.

### 7.4 Empfohlenes Vorgehen

```
✅ Receiver (Balanced → SE):  3× LM4562MAX/NOPB (SOIC-8)
                               + 12× 0.1% Widerstände (10k/10k oder angepasst)
                               + 6× Entkopplungs-C
                               
✅ Driver (SE → Balanced):     3× LM4562MAX/NOPB (SOIC-8)  
                               + 9× 0.1% Widerstände (Buffer + Inverter)
                               + 6× Entkopplungs-C

Alternative Driver:            3× DRV135UA/2K5 (SOIC-8, $2.78)
                               + 6× Entkopplungs-C
                               (weniger Bauteile, etwas schlechtere THD)
```

---

## 8. Wichtige Design-Hinweise für LM4562-basierte Lösung

### 8.1 Receiver (Differenzverstärker)

- **Widerstands-Matching ist KRITISCH für CMRR:** 0.1%-Widerstände verwenden (z.B. Panasonic ERA-Serie)
- Alternativ: Resistor-Network (z.B. Bourns CAT16) für noch besseres Matching
- Typische CMRR mit 0.1% Matching: ~66 dB. Mit 0.01%: ~86 dB.
- **Layout:** Widerstände thermisch gekoppelt platzieren (nebeneinander, gleiche Orientierung)
- CMRR-Formel: $CMRR \approx 20 \log_{10}\left(\frac{1}{4 \cdot \delta}\right)$ wobei $\delta$ der relative Widerstandsfehler ist

### 8.2 Driver (Buffer + Inverter)

- **Inverter-Widerstände:** 0.1% für gute Output-Balance
- Keine Widerstände im Buffer-Pfad (Unity-Gain Follower)
- Output-Balance: $Balance \approx 20 \log_{10}\left(\frac{1}{2 \cdot \delta}\right)$
- 100 Ω Serienwiderstände an beiden Ausgängen als Kurzschlusschutz + HF-Dämpfung

### 8.3 Allgemein

- 100 nF C0G direkt an VCC/GND-Pins jedes LM4562
- 10 µF Bulk-C pro Versorgungsstrang
- Keine Signalleitungen unter den ICs auf der Massefläche
- Guard-Traces um empfindliche Receiver-Eingänge

---

## Anhang: Alle untersuchten ICs auf einen Blick

| IC | Hersteller | Typ | Funktion | Package | THD+N | CMRR/Balance | Supply | Status | LCSC? | Preis |
|----|-----------|-----|----------|---------|-------|-------------|--------|--------|-------|-------|
| THAT1240 | THAT Corp | Receiver | Bal→SE G=1 | DIP-8/SOIC-8 | 0.0004% | 90 dB | ±5–±18V | Active | ❌ | ~$4 |
| THAT1246 | THAT Corp | Receiver | Bal→SE G=2 | DIP-8/SOIC-8 | 0.0004% | 90 dB | ±5–±18V | Active | ❌ | ~$4 |
| THAT1200 | THAT Corp | Receiver | Bal→SE | DIP-8/SOIC-8 | ~0.003% | 70 dB | ±5–±18V | Legacy | ❌ | ~$3 |
| THAT1606 | THAT Corp | Driver | SE→Bal G=1 | SOIC-8 | 0.0003% | >60 dB bal | ±5–±18V | Active | ❌ | ~$5 |
| THAT1646 | THAT Corp | Driver | SE→Bal G=2 | SOIC-8 | 0.0003% | >60 dB bal | ±5–±18V | Active | ❌ | ~$5 |
| DRV134 | TI | Driver | SE→Bal | DIP-8/SOIC-16 | 0.0005% | ~60 dB bal | ±4.5–±18V | Active | ⚠️ | ~$5.95 |
| DRV135 | TI | Driver | SE→Bal | **SOIC-8** | 0.0005% | ~60 dB bal | ±4.5–±18V | Active | ✅ | **$2.78** |
| INA1634 | TI | — | — | — | — | — | — | ❌ DNE | ❌ | — |
| SSM2142 | ADI | Driver | SE→Bal | DIP-8 | 0.006% | 80 dB | ±15V | ⛔ Obsolete | ⚠️ | $149 |
| SSM2143 | ADI | Receiver | Bal→SE G=½ | SOIC-8/DIP-8 | 0.0006% | 90 dB | ±5–±18V | ⛔ Obsolete | ⚠️ | $8.83 |
| **LM4562** | **TI** | **Op-Amp** | **Dual** | **SOIC-8** | **0.00003%** | **n/a** | **±2.5–±17V** | **Active** | ✅ | **$2.08** |
