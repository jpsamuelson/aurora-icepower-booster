# Through-Hole Präzisionsbauteile — Research Report

**Projekt:** Aurora DSP IcePower Booster  
**Datum:** 2026-03-12  
**Zweck:** Beschaffungsrecherche für THT-Präzisionswiderstände (0.1%) und Kondensatoren für Audio-Differenzverstärker (DIY)

---

## Zusammenfassung (TL;DR)

| Kategorie | Empfehlung | Preis (1 Stk.) | Verfügbarkeit |
|-----------|-----------|----------------|---------------|
| **0.1% 10kΩ Widerstand** | YAGEO MFP-25BRD52-10K | ~$0.60 | ✅ DigiKey 26k+ Stk. |
| **0.1% 10kΩ (Alternative)** | TE YR1B10KCC (Neohm) | ~$0.79 | ✅ DigiKey 77k+ Stk. |
| **0.1% 10kΩ (LCSC)** | Vishay CMF5510K000BEEB | ~$1.40 | ⚠️ LCSC 197 Stk. |
| **100nF C0G THT** | ❌ Existiert praktisch nicht | — | ❌ |
| **100nF Film (Ersatz)** | WIMA MKS2D031001A00JSSD | ~$0.57 | ⚠️ LCSC 12 Stk. |
| **10µF Elko THT** | Nichicon/Panasonic Standard | ~$0.10–0.30 | ✅ Massenverfügbar |
| **100µF Elko THT** | Nichicon/Panasonic Standard | ~$0.10–0.50 | ✅ Massenverfügbar |
| **47Ω 1% Widerstand** | YAGEO MFR-25FRF52-47R | ~$0.10 | ✅ DigiKey 100k+ Stk. |

**Kernaussage:** 0.1% THT-Widerstände sind gut verfügbar und bezahlbar ($0.60–$1.40). 100nF C0G in THT existiert nicht — verwende Polyester-Film (WIMA MKS2) oder SMD C0G auf Adapter.

---

## 1. Through-Hole 0.1% Präzisionswiderstände (Axial)

### 1.1 Übersicht der Serien

| Serie | Hersteller | Toleranz | Tempco | Leistung | Baugröße (D×L) | Preis (1 Stk.) |
|-------|-----------|----------|--------|---------|-----------------|----------------|
| **CMF55** | Vishay/Dale | 0.1% (B) | ±25 ppm/°C (E) | 500 mW | 2.3×6.1 mm | $0.29–$1.40 |
| **MFP-25** | YAGEO | 0.1% | ±25 ppm/°C | 250 mW | 2.4×6.3 mm | ~$0.60 |
| **RNF14** | Stackpole | 0.1% | ±25 ppm/°C | 250 mW | 2.35×6.35 mm | ~$0.62 |
| **YR (Neohm)** | TE Connectivity | 0.1% | **±15 ppm/°C** | 250 mW | 2.3×6.3 mm | ~$0.79 |
| **MRS25** | Vishay | 0.1% | ±25–50 ppm/°C | 250 mW | 2.3×6.3 mm | ~$0.50–$1.00 |

> **Alle Baugößen sind Standard-1/4W-Axial** — identisch mit billigen Kohleschichtwiderständen. Passen problemlos auf Standard-PCBs mit 2.54mm-Raster (Pitch 7.6–10.2 mm typisch).

### 1.2 Detaillierte Teilenummern & Verfügbarkeit

#### Vishay CMF55 (Der Klassiker)

Die CMF55-Bestellnummer kodiert alle Parameter:
`CMF55` `10K000` `B` `E` `EB`

- **B** = ±0.1% Toleranz (C=0.25%, D=0.5%, F=1%)
- **E** = ±25 ppm/°C TK (H=±50ppm, K=±100ppm)
- **EB** = Verpackungs-/Spec-Code

| Teilenummer | Wert | Tol. | TK | LCSC Stock | LCSC Preis | DigiKey/Mouser |
|------------|------|------|-----|-----------|-----------|----------------|
| **CMF5510K000BEEB** | 10kΩ | 0.1% | ±25ppm | **197 Stk.** | **$1.40** (1+) / $0.80 (1k+) | Verfügbar |
| CMF5510K000BHEA | 10kΩ | 0.1% | ±50ppm | 0 (bestellbar) | $0.28 (1+) | — |
| CMF5510K000BEEA | 10kΩ | 0.1% | ±25ppm | 0 (bestellbar) | $0.29 (1+) | — |
| CMF5510K000BERE | 10kΩ | 0.1% | ±25ppm | 0 (bestellbar) | $0.40 (1+) | — |
| CMF5510K000BHBF | 10kΩ | 0.1% | ±50ppm | 0 (bestellbar) | $0.97 (1+) | — |

**Bewertung CMF55:** Gold-Standard für Audio-Precision. Problem: Bei LCSC sehr geringe Lagerbestände für 0.1%-Varianten. Große Mengen müssen bestellt werden (MOQ oft 200–1000 Stk. für Pre/New-Listings).

#### YAGEO MFP-25 (Beste Verfügbarkeit bei 0.1%)

| Teilenummer | Wert | Tol. | TK | DigiKey Stock | DigiKey Preis |
|------------|------|------|-----|--------------|--------------|
| **MFP-25BRD52-10K** | 10kΩ | 0.1% | ±25ppm | **26.676 Stk.** | **$0.60** (1+) / $0.16 (5k+) |
| **MFP-25BRD52-20K** | 20kΩ | 0.1% | ±25ppm | Hoch (verfügbar) | ~$0.60 |
| **MFP-25BRD52-4K70** | 4.7kΩ | 0.1% | ±25ppm | Hoch (verfügbar) | ~$0.60 |
| **MFP-25BRD52-100R** | 100Ω | 0.1% | ±25ppm | **4.958 Stk.** | **$0.60** (1+) |

**Bewertung YAGEO MFP-25:** ⭐ **KLARE EMPFEHLUNG für DIY.** Hervorragende Verfügbarkeit bei DigiKey, günstiger Preis, alle relevanten Werte verfügbar. Standardgröße 1/4W axial.

#### Stackpole RNF14 (Gute Alternative)

| Teilenummer | Wert | Tol. | TK | DigiKey Stock | DigiKey Preis |
|------------|------|------|-----|--------------|--------------|
| **RNF14BTE10K0** | 10kΩ | 0.1% | ±25ppm | **20.424 Stk.** | **$0.62** (1+) / $0.16 (5k+) |
| RNF14FTD10K0 | 10kΩ | 1% | ±100ppm | 144.666 Stk. | $0.10 (1+) |

**Bewertung Stackpole RNF14:** Solide Alternative, leicht teurer. Flame-Retardant-Beschichtung und Safety-Zertifizierung — mehr als nötig für DIY, aber solide.

#### TE Connectivity YR (Neohm) — Premium

| Teilenummer | Wert | Tol. | TK | DigiKey Stock | DigiKey Preis |
|------------|------|------|-----|--------------|--------------|
| **YR1B10KCC** | 10kΩ | 0.1% | **±15ppm** | **77.291 Stk.** | **$0.79** (1+) / $0.25 (1k+) |
| **YR1B20RCC** | 20Ω | 0.1% | ±15ppm | 33.065 Stk. | $0.65 (1+) |
| **YR1B1K0CC** | 1kΩ | 0.1% | ±15ppm | 8.838 Stk. | $0.83 (1+) |
| **YR1B1M0CC** | 1MΩ | 0.1% | ±15ppm | 11.306 Stk. | $0.61 (1+) |

**Bewertung TE YR Neohm:** ⭐ **Bester TK (±15 ppm/°C)** aller verfügbaren Serien. Wenn Temperaturstabilität kritisch ist (z.B. Gain-Setting in Feedback-Netzwerken), ist diese Serie die beste Wahl. Sehr gute Verfügbarkeit. Hinweis: Für 4.7kΩ, 20kΩ, 47Ω müssen Verfügbarkeiten einzeln geprüft werden — nicht alle E96-Werte werden geführt.

### 1.3 Preisvergleich: 0.1% vs. 1% vs. 5%

| Toleranz | Beispiel (10kΩ) | Preis (1 Stk.) | Preis (100+) |
|----------|-----------------|----------------|-------------|
| 5% Carbon Film | CF14JT10K0 | $0.10 | $0.008 |
| 1% Metal Film | MFR-25FRF52-10K (YAGEO) | $0.10 | $0.013 |
| **0.1% Metal Film** | **MFP-25BRD52-10K (YAGEO)** | **$0.60** | **$0.16** |
| 0.1% + ±15ppm TK | YR1B10KCC (TE Neohm) | $0.79 | $0.25 |

**Ergebnis:** 0.1% kostet 6× mehr als 1%, aber in absoluten Zahlen immer noch sehr günstig ($0.60/Stk.). Für einen Differenzverstärker mit 8–16 Widerständen sind das nur ~$5–$13 Mehrkosten.

### 1.4 Widerstandsnetzwerke (SIP/DIP) — 0.1%

**Ergebnis: Praktisch nicht verfügbar.**

- Standard-SIP/DIP-Netzwerke (Bourns, CTS) gibt es typisch nur in 2% oder 1%
- 0.1%-Netzwerke existieren als Spezialteile (Vishay Bulk Metal Foil, z.B. NOMC-Serie), aber:
  - Extrem teuer ($10–$50+/Stk.)
  - Sehr eingeschränkte Wertekombinationen
  - Lange Lieferzeiten

**Empfehlung:** Einzelwiderstände verwenden. Der Vorteil von Netzwerken (garantiertes Matching) wird bei 0.1%-Einzelwiderständen weitgehend irrelevant — zwei 0.1%-Widerstände aus dem gleichen Reel sind typisch innerhalb von 0.02% gematcht.

> **Tipp für bestes Matching:** 10+ Stück des gleichen Werts bestellen (aus Tape & Reel), mit DMM messen, und die am besten passenden Paare bilden. Bei 0.1%-Nenntoleranz erreicht man so typisch <0.01% Matching.

---

## 2. Through-Hole Kondensatoren

### 2.1 100nF C0G/NP0 — Through-Hole

#### ❌ EXISTIERT PRAKTISCH NICHT IN THT

**Warum?**

- C0G/NP0 hat eine sehr niedrige Dielektrizitätskonstante (~30 vs. ~3000 bei X7R)
- 100nF in C0G erfordert daher **große physische Abmessungen**
- Als SMD erst ab **1206** verfügbar (3.2×1.6 mm) — schon das ist groß für SMD
- THT-Keramikkondensatoren (Disc-Typ) mit C0G existieren nur bis ca. **10nF** (10.000pF)
- Darüber hinaus werden THT-Keramiken typisch als X7R oder Y5V angeboten

**Verfügbarkeit 100nF C0G auf LCSC/DigiKey:**

- Alle gefundenen 100nF C0G sind **SMD** (1206, 1210, 1812, 2220)
- TDK CGA-Serie: 100nF C0G 50V ab 1206, Preis $0.18–$0.49 (SMD)
- Kein einziger THT-C0G-Kondensator mit 100nF gefunden

### 2.2 Alternativen für 100nF Entkopplung (THT)

#### Option A: WIMA MKS2 — Polyester-Filmkondensator ⭐ EMPFEHLUNG

| Teilenummer | Wert | Tol. | Spannung | Pitch | LCSC Stock | Preis |
|------------|------|------|----------|-------|-----------|-------|
| **MKS2D031001A00JSSD** | 100nF | ±5% | 100V | 5 mm | **12 Stk.** | **$0.57** |
| MKS2C031001A00KSSD | 100nF | ±10% | 63V | 5 mm | 18 Stk. | $0.44 |
| MKS2G031001K00JSSD | 100nF | ±5% | 400V | 5 mm | 0 (bestellbar) | $0.57 |

**Eigenschaften:**

- Metallisierter Polyester (PET) — **kein Mikrofonie-Effekt** (im Gegensatz zu X7R-Keramik)
- Baugröße ca. 7.2×2.5×6.5 mm bei 5mm Pitch — kompakt genug für PCB
- Verlustfaktor (tan δ) ca. 0.008–0.01 @ 1 kHz
- Nicht so gut wie C0G (tan δ < 0.001), aber für Entkopplung mehr als ausreichend
- **Audio-Standard** — wird seit Jahrzehnten in Studio-Equipment eingesetzt

**Problem bei LCSC:** Sehr geringe Lagerbestände (12–18 Stk.). Für JLCPCB-Bestückung problematisch. Besser bei Mouser/DigiKey bestellen.

#### Option B: Epcos/TDK B32529 — Polyester-Film

Ähnlich wie WIMA MKS2, oft günstiger. Verfügbarkeit bei LCSC ebenfalls eingeschränkt für THT-Varianten.

#### Option C: WIMA MKP2 — Polypropylen (PP) — Premium-Audio

- Polypropylen hat den **niedrigsten Verlustfaktor** aller Filmtypen (tan δ < 0.0005)
- Ideal für Audio-Signalpfad (Koppelkondensatoren)
- 100nF ist verfügbar, aber größere Baugröße als MKS2
- Preis höher (~$1.00–$2.00)
- **Empfehlung:** Für Entkopplung reicht MKS2 (Polyester). MKP2 (Polypropylen) nur im Signalpfad verwenden.

#### Option D: SMD C0G auf THT-Adapter

Wenn C0G zwingend erforderlich:

- SMD-C0G 100nF in 1206 auf Adapter-Platine (1206-zu-THT)
- Oder: 100nF C0G 1206 direkt auf Unterseite der Hauptplatine löten (Dead-Bug-Stil)
- Pragmatisch, aber nicht elegant

### 2.3 Empfehlung für Entkopplung (3 Stufen, THT)

| Stufe | Funktion | Typ | Empfehlung |
|-------|----------|-----|------------|
| **HF-Entkopplung** | Direkt am IC | Keramik oder Film | WIMA MKS2 100nF (5mm Pitch) |
| **Lokale Entkopplung** | Pro Versorgungsinsel | Elko oder Film | 10µF Elko (Nichicon UKL/Panasonic FC) |
| **Bulk** | Am Versorgungseingang | Elko | 100µF+ Elko (Nichicon/Panasonic) |

> **Hinweis:** Für einen DIY THT-Aufbau ist WIMA MKS2 100nF die pragmatische Lösung. Der Verlustfaktor-Unterschied zu C0G (0.008 vs. 0.001) ist für Entkopplung vollkommen irrelevant — es geht um die Bereitstellung von Ladung, nicht um Signaltreue. Im Audio-**Signal**pfad (Koppelkondensatoren) sollte MKP (Polypropylen) verwendet werden.

### 2.4 Elektrolytkondensatoren (THT) — Bulk-Entkopplung

| Wert | Serie | Preis (LCSC/DigiKey) | Lager | Hinweis |
|------|-------|---------------------|-------|---------|
| 10µF 50V | Nichicon UKL, Panasonic FC | $0.05–$0.15 | ✅ Massenware | Low-ESR für Audio |
| 10µF 50V | Nichicon KA (Audio) | $0.20–$0.50 | ✅ Verfügbar | Audio-Grade, Gold-Standard |
| 100µF 50V | Nichicon UKL, Panasonic FC | $0.10–$0.30 | ✅ Massenware | Standard-Bulk |
| 100µF 25V | Nichicon MUSE (KZ) | $0.50–$2.00 | ✅ DigiKey | Audio-Spezial, bipolar |
| 1000µF 50V | Nichicon/Panasonic | $0.30–$1.00 | ✅ Massenware | Nezteil-Bulk |

**Empfehlung für Audio:**

- **Nichicon KA** (MUSE Standard) oder **Panasonic FC** für lokale Entkopplung
- Für den Signalpfad (Kopplung): lieber **Filmkondensatoren** verwenden
- Elektrolytkondensatoren sind **keine Engpassteile** — massenhaft verfügbar und günstig

---

## 3. 47Ω Serien-Ausgangswiderstände

### 3.1 Verfügbare Optionen

| Teilenummer | Serie | Tol. | TK | Leistung | DigiKey Preis | Stock |
|------------|-------|------|-----|---------|--------------|-------|
| **MFR-25FRF52-47R** | YAGEO MFR | 1% | ±100ppm | 1/4W | **$0.10** | 100k+ |
| RNF14FTD47R0 | Stackpole RNF | 1% | ±100ppm | 1/4W | $0.10 | 100k+ |
| CF14JT47R0 | Stackpole CF | 5% | 0/-400ppm | 1/4W | $0.10 | 100k+ |

**Empfehlung:** YAGEO MFR-25FRF52-47R (1% Metal Film, $0.10). Für 47Ω-Ausgangswiderstände ist 0.1% weder nötig noch sinnvoll — der Wert ist unkritisch (dient nur der HF-Entkopplung/Lastabschluss).

---

## 4. Gotchas & Praktische Hinweise für THT-Präzisionsbauteile (2026)

### 4.1 Verfügbarkeit

- **THT wird zunehmend Nische.** Die meisten neuen Designs sind SMD. THT-Precision-Widerstände sind aber dank Audio-/Messtechnik-Markt weiterhin gut verfügbar.
- **LCSC/JLCPCB:** Sehr eingeschränkte Auswahl bei THT-Precision. JLCPCB-Handbestückung von THT-Teilen kostet extra (~$0.02–$0.05/Lötstelle). Am günstigsten: THT-Teile selbst bestücken.
- **DigiKey/Mouser:** Beste Quelle für THT-Precision. Versand nach DE/EU ~$12–$20, aber für Einzelprojekte lohnend.

### 4.2 PCB-Footprint-Größen

| Bauteil | Körper (D×L) | Empfohlener Pitch | Footprint |
|---------|-------------|-------------------|-----------|
| 1/4W Axial-Widerstand | 2.4×6.3 mm | 7.62–10.16 mm | Standard THT 0207 |
| WIMA MKS2 100nF | 7.2×2.5×6.5 mm | 5.0 mm | Radial_P5.0mm |
| Elko 10µF (6.3mm) | Ø5×11 mm | 2.0–2.5 mm | Radial_D5.0mm_P2.5mm |
| Elko 100µF (10mm) | Ø6.3–8×11 mm | 2.5–3.5 mm | Radial_D6.3mm_P2.5mm |

### 4.3 Audio-Qualitäts-Hinweise

1. **0.1% Matching ist wichtiger als absolute Genauigkeit** — Bei Differenzverstärkern bestimmt das Widerstandsverhältnis die CMRR. Zwei Widerstände mit 10.005kΩ und 10.008kΩ sind perfekt, solange sie gleich sind.

2. **Tempco-Matching ebenfalls kritisch** — TE Neohm YR (±15 ppm/°C) hat den Vorteil, dass sich alle Widerstände bei Temperaturänderung ungefähr gleich verschieben → CMRR bleibt stabil.

3. **Kein Kohleschicht (Carbon Film) im Signalpfad** — Spannungskoeffizient erzeugt nichtlineare Verzerrung. Nur Metal Film verwenden.

4. **Film vs. Keramik für 100nF:** Für Audio kein Nachteil von Film. Im Gegenteil — Film hat kein Mikrofonie-Problem (X7R-Keramik kann bei Vibration Spannung erzeugen). WIMA MKS2 ist in Studio-Equipment Standard seit 40+ Jahren.

---

## 5. Einkaufsliste — Vorschlag

### Für Differenzverstärker (z.B. THAT1240-Ersatz mit LM4562)

| Menge | Bauteil | Teilenummer | Bezugsquelle | Stückpreis |
|-------|---------|------------|-------------|-----------|
| 8× | 10kΩ 0.1% | **MFP-25BRD52-10K** (YAGEO) | DigiKey | $0.60 |
| 4× | 20kΩ 0.1% | **MFP-25BRD52-20K** (YAGEO) | DigiKey | $0.60 |
| 4× | 4.7kΩ 0.1% (wenn benötigt) | **MFP-25BRD52-4K70** (YAGEO) | DigiKey | $0.60 |
| 4× | 47Ω 1% | **MFR-25FRF52-47R** (YAGEO) | DigiKey | $0.10 |
| 8× | 100nF Film | **WIMA MKS2D031001A00JSSD** | Mouser/DigiKey | ~$0.40 |
| 4× | 10µF 50V Elko | Nichicon UKL1H100MDD | DigiKey/LCSC | ~$0.10 |
| 2× | 100µF 50V Elko | Nichicon UKL1H101MED | DigiKey/LCSC | ~$0.25 |
| | | | **Gesamt ca.:** | **~$14–$18** |

### Alternative: Premium-Setup (TE Neohm, bester TK)

| Menge | Bauteil | Teilenummer | Stückpreis |
|-------|---------|------------|-----------|
| 8× | 10kΩ 0.1% ±15ppm | **YR1B10KCC** (TE) | $0.79 |
| 4× | 20kΩ 0.1% ±15ppm | YR1B20KCC (TE) | ~$0.79 |

Mehrkosten: ~$3–$5 für deutlich bessere Temperaturdrift.

---

## 6. Fazit

### ✅ Widerstände: Kein Problem

- 0.1% THT Axialwiderstände sind **gut verfügbar und bezahlbar** ($0.60–$0.80/Stk.)
- YAGEO MFP-25 ist die pragmatische Empfehlung (Preis/Verfügbarkeit)
- TE YR Neohm ist die Premium-Wahl (bester Tempco)
- Vishay CMF55 ist der Audiophile-Klassiker, aber bei LCSC schwer beschaffbar

### ⚠️ 100nF C0G in THT: Nicht machbar

- C0G-Keramik in THT existiert nur bis ~10nF
- **Film (WIMA MKS2) ist der korrekte Ersatz** und klanglich sogar bevorzugt
- Für Entkopplung ist der Verlustfaktor-Unterschied zu C0G irrelevant

### ✅ Elektrolytkondensatoren: Kein Engpass

- Massenware, trivial beschaffbar

### ✅ 47Ω Ausgangswiderstände: Trivial

- Standard 1% Metal Film, $0.10/Stk., überall verfügbar

### Bezugsquellen-Empfehlung für THT-DIY

1. **DigiKey/Mouser** für Präzisionswiderstände und WIMA-Kondensatoren
2. **LCSC/JLCPCB** nur für Standardteile (Elkos, 1%-Widerstände) — THT-Precision-Auswahl ist dort stark limitiert
