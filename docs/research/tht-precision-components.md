# Through-Hole Precision Components — Research Report

**Project:** Aurora DSP ICEpower Booster
**Date:** 2026-03-12
**Purpose:** Sourcing research for THT precision resistors (0.1%) and capacitors for audio differential amplifier (DIY)

---

## Summary (TL;DR)

| Category | Recommendation | Price (1 pc) | Availability |
|----------|---------------|-------------|-------------|
| **0.1% 10kΩ Resistor** | YAGEO MFP-25BRD52-10K | ~$0.60 | ✅ DigiKey 26k+ pcs |
| **0.1% 10kΩ (Alternative)** | TE YR1B10KCC (Neohm) | ~$0.79 | ✅ DigiKey 77k+ pcs |
| **0.1% 10kΩ (LCSC)** | Vishay CMF5510K000BEEB | ~$1.40 | ⚠️ LCSC 197 pcs |
| **100nF C0G THT** | ❌ Practically does not exist | — | ❌ |
| **100nF Film (substitute)** | WIMA MKS2D031001A00JSSD | ~$0.57 | ⚠️ LCSC 12 pcs |
| **10µF Electrolytic THT** | Nichicon/Panasonic standard | ~$0.10–0.30 | ✅ Mass available |
| **100µF Electrolytic THT** | Nichicon/Panasonic standard | ~$0.10–0.50 | ✅ Mass available |
| **47Ω 1% Resistor** | YAGEO MFR-25FRF52-47R | ~$0.10 | ✅ DigiKey 100k+ pcs |

**Key takeaway:** 0.1% THT resistors are well available and affordable ($0.60–$1.40). 100nF C0G in THT does not exist — use polyester film (WIMA MKS2) or SMD C0G on adapter.

---

## 1. Through-Hole 0.1% Precision Resistors (Axial)

### 1.1 Series Overview

| Series | Manufacturer | Tolerance | Tempco | Power | Size (D×L) | Price (1 pc) |
|--------|-------------|----------|--------|-------|------------|-------------|
| **CMF55** | Vishay/Dale | 0.1% (B) | ±25 ppm/°C (E) | 500 mW | 2.3×6.1 mm | $0.29–$1.40 |
| **MFP-25** | YAGEO | 0.1% | ±25 ppm/°C | 250 mW | 2.4×6.3 mm | ~$0.60 |
| **RNF14** | Stackpole | 0.1% | ±25 ppm/°C | 250 mW | 2.35×6.35 mm | ~$0.62 |
| **YR (Neohm)** | TE Connectivity | 0.1% | **±15 ppm/°C** | 250 mW | 2.3×6.3 mm | ~$0.79 |
| **MRS25** | Vishay | 0.1% | ±25–50 ppm/°C | 250 mW | 2.3×6.3 mm | ~$0.50–$1.00 |

> **All form factors are standard 1/4W axial** — identical to cheap carbon film resistors. Fit standard PCBs with 2.54mm grid (pitch 7.6–10.2 mm typical).

### 1.2 Detailed Part Numbers & Availability

#### Vishay CMF55 (The Classic)

The CMF55 part number encodes all parameters:
`CMF55` `10K000` `B` `E` `EB`

- **B** = ±0.1% tolerance (C=0.25%, D=0.5%, F=1%)
- **E** = ±25 ppm/°C tempco (H=±50ppm, K=±100ppm)
- **EB** = Packaging/spec code

| Part Number | Value | Tol. | Tempco | LCSC Stock | LCSC Price | DigiKey/Mouser |
|------------|------|------|--------|-----------|-----------|----------------|
| **CMF5510K000BEEB** | 10kΩ | 0.1% | ±25ppm | **197 pcs** | **$1.40** (1+) / $0.80 (1k+) | Available |
| CMF5510K000BHEA | 10kΩ | 0.1% | ±50ppm | 0 (orderable) | $0.28 (1+) | — |
| CMF5510K000BEEA | 10kΩ | 0.1% | ±25ppm | 0 (orderable) | $0.29 (1+) | — |
| CMF5510K000BERE | 10kΩ | 0.1% | ±25ppm | 0 (orderable) | $0.40 (1+) | — |
| CMF5510K000BHBF | 10kΩ | 0.1% | ±50ppm | 0 (orderable) | $0.97 (1+) | — |

**Assessment CMF55:** Gold standard for audio precision. Problem: Very low LCSC stock for 0.1% variants. Large quantities must be ordered (MOQ often 200–1000 pcs for pre/new listings).

#### YAGEO MFP-25 (Best Availability at 0.1%)

| Part Number | Value | Tol. | Tempco | DigiKey Stock | DigiKey Price |
|------------|------|------|--------|--------------|--------------|
| **MFP-25BRD52-10K** | 10kΩ | 0.1% | ±25ppm | **26,676 pcs** | **$0.60** (1+) / $0.16 (5k+) |
| **MFP-25BRD52-20K** | 20kΩ | 0.1% | ±25ppm | High (available) | ~$0.60 |
| **MFP-25BRD52-4K70** | 4.7kΩ | 0.1% | ±25ppm | High (available) | ~$0.60 |
| **MFP-25BRD52-100R** | 100Ω | 0.1% | ±25ppm | **4,958 pcs** | **$0.60** (1+) |

**Assessment YAGEO MFP-25:** ⭐ **CLEAR RECOMMENDATION for DIY.** Excellent availability at DigiKey, affordable price, all relevant values available. Standard 1/4W axial form factor.

#### Stackpole RNF14 (Good Alternative)

| Part Number | Value | Tol. | Tempco | DigiKey Stock | DigiKey Price |
|------------|------|------|--------|--------------|--------------|
| **RNF14BTE10K0** | 10kΩ | 0.1% | ±25ppm | **20,424 pcs** | **$0.62** (1+) / $0.16 (5k+) |
| RNF14FTD10K0 | 10kΩ | 1% | ±100ppm | 144,666 pcs | $0.10 (1+) |

**Assessment Stackpole RNF14:** Solid alternative, slightly more expensive. Flame-retardant coating and safety certification — more than needed for DIY, but solid.

#### TE Connectivity YR (Neohm) — Premium

| Part Number | Value | Tol. | Tempco | DigiKey Stock | DigiKey Price |
|------------|------|------|--------|--------------|--------------|
| **YR1B10KCC** | 10kΩ | 0.1% | **±15ppm** | **77,291 pcs** | **$0.79** (1+) / $0.25 (1k+) |
| **YR1B20RCC** | 20Ω | 0.1% | ±15ppm | 33,065 pcs | $0.65 (1+) |
| **YR1B1K0CC** | 1kΩ | 0.1% | ±15ppm | 8,838 pcs | $0.83 (1+) |
| **YR1B1M0CC** | 1MΩ | 0.1% | ±15ppm | 11,306 pcs | $0.61 (1+) |

**Assessment TE YR Neohm:** ⭐ **Best tempco (±15 ppm/°C)** of all available series. When temperature stability is critical (e.g., gain-setting in feedback networks), this series is the best choice. Very good availability. Note: For 4.7kΩ, 20kΩ, 47Ω, availability must be checked individually — not all E96 values are stocked.

### 1.3 Price Comparison: 0.1% vs. 1% vs. 5%

| Tolerance | Example (10kΩ) | Price (1 pc) | Price (100+) |
|----------|-----------------|-------------|-------------|
| 5% Carbon Film | CF14JT10K0 | $0.10 | $0.008 |
| 1% Metal Film | MFR-25FRF52-10K (YAGEO) | $0.10 | $0.013 |
| **0.1% Metal Film** | **MFP-25BRD52-10K (YAGEO)** | **$0.60** | **$0.16** |
| 0.1% + ±15ppm Tempco | YR1B10KCC (TE Neohm) | $0.79 | $0.25 |

**Result:** 0.1% costs 6× more than 1%, but in absolute terms still very affordable ($0.60/pc). For a differential amplifier with 8–16 resistors, that's only ~$5–$13 extra cost.

### 1.4 Resistor Networks (SIP/DIP) — 0.1%

**Result: Practically unavailable.**

- Standard SIP/DIP networks (Bourns, CTS) are typically only available in 2% or 1%
- 0.1% networks exist as specialty parts (Vishay Bulk Metal Foil, e.g., NOMC series), but:
  - Extremely expensive ($10–$50+/pc)
  - Very limited value combinations
  - Long lead times

**Recommendation:** Use individual resistors. The advantage of networks (guaranteed matching) becomes largely irrelevant with 0.1% individual resistors — two 0.1% resistors from the same reel are typically matched within 0.02%.

> **Tip for best matching:** Order 10+ pieces of the same value (from tape & reel), measure with DMM, and form the best-matched pairs. With 0.1% nominal tolerance, you can typically achieve <0.01% matching.

---

## 2. Through-Hole Capacitors

### 2.1 100nF C0G/NP0 — Through-Hole

#### ❌ PRACTICALLY DOES NOT EXIST IN THT

**Why?**

- C0G/NP0 has a very low dielectric constant (~30 vs. ~3000 for X7R)
- 100nF in C0G therefore requires **large physical dimensions**
- Available as SMD only starting at **1206** (3.2×1.6 mm) — already large for SMD
- THT ceramic capacitors (disc type) with C0G only exist up to approx. **10nF** (10,000pF)
- Beyond that, THT ceramics are typically offered as X7R or Y5V

**Availability 100nF C0G at LCSC/DigiKey:**

- All 100nF C0G found are **SMD** (1206, 1210, 1812, 2220)
- TDK CGA series: 100nF C0G 50V starting at 1206, price $0.18–$0.49 (SMD)
- No single THT C0G capacitor with 100nF found

### 2.2 Alternatives for 100nF Decoupling (THT)

#### Option A: WIMA MKS2 — Polyester Film Capacitor ⭐ RECOMMENDATION

| Part Number | Value | Tol. | Voltage | Pitch | LCSC Stock | Price |
|------------|------|------|---------|-------|-----------|-------|
| **MKS2D031001A00JSSD** | 100nF | ±5% | 100V | 5 mm | **12 pcs** | **$0.57** |
| MKS2C031001A00KSSD | 100nF | ±10% | 63V | 5 mm | 18 pcs | $0.44 |
| MKS2G031001K00JSSD | 100nF | ±5% | 400V | 5 mm | 0 (orderable) | $0.57 |

**Properties:**

- Metallized polyester (PET) — **no microphonic effect** (unlike X7R ceramic)
- Size approx. 7.2×2.5×6.5 mm at 5mm pitch — compact enough for PCB
- Dissipation factor (tan δ) approx. 0.008–0.01 @ 1 kHz
- Not as good as C0G (tan δ < 0.001), but more than sufficient for decoupling
- **Audio standard** — used in studio equipment for decades

**Problem at LCSC:** Very low stock (12–18 pcs). Problematic for JLCPCB assembly. Better ordered from Mouser/DigiKey.

#### Option B: Epcos/TDK B32529 — Polyester Film

Similar to WIMA MKS2, often cheaper. Availability at LCSC also limited for THT variants.

#### Option C: WIMA MKP2 — Polypropylene (PP) — Premium Audio

- Polypropylene has the **lowest dissipation factor** of all film types (tan δ < 0.0005)
- Ideal for audio signal path (coupling capacitors)
- 100nF is available, but larger form factor than MKS2
- Higher price (~$1.00–$2.00)
- **Recommendation:** For decoupling, MKS2 (polyester) is sufficient. MKP2 (polypropylene) should only be used in the signal path.

#### Option D: SMD C0G on THT Adapter

If C0G is absolutely required:

- SMD C0G 100nF in 1206 on adapter PCB (1206-to-THT)
- Or: 100nF C0G 1206 soldered directly on the bottom side of the main PCB (dead-bug style)
- Pragmatic but not elegant

### 2.3 Recommended Decoupling (3 tiers, THT)

| Tier | Function | Type | Recommendation |
|------|----------|------|---------------|
| **HF Decoupling** | Directly at IC | Ceramic or film | WIMA MKS2 100nF (5mm pitch) |
| **Local Decoupling** | Per supply island | Electrolytic or film | 10µF electrolytic (Nichicon UKL/Panasonic FC) |
| **Bulk** | At supply input | Electrolytic | 100µF+ electrolytic (Nichicon/Panasonic) |

> **Note:** For a DIY THT build, WIMA MKS2 100nF is the pragmatic solution. The dissipation factor difference to C0G (0.008 vs. 0.001) is completely irrelevant for decoupling — it's about providing charge, not signal fidelity. In the audio **signal** path (coupling capacitors), MKP (polypropylene) should be used.

### 2.4 Electrolytic Capacitors (THT) — Bulk Decoupling

| Value | Series | Price (LCSC/DigiKey) | Stock | Notes |
|-------|--------|---------------------|-------|-------|
| 10µF 50V | Nichicon UKL, Panasonic FC | $0.05–$0.15 | ✅ Mass product | Low-ESR for audio |
| 10µF 50V | Nichicon KA (Audio) | $0.20–$0.50 | ✅ Available | Audio-grade, gold standard |
| 100µF 50V | Nichicon UKL, Panasonic FC | $0.10–$0.30 | ✅ Mass product | Standard bulk |
| 100µF 25V | Nichicon MUSE (KZ) | $0.50–$2.00 | ✅ DigiKey | Audio specialty, bipolar |
| 1000µF 50V | Nichicon/Panasonic | $0.30–$1.00 | ✅ Mass product | PSU bulk |

**Recommendation for audio:**

- **Nichicon KA** (MUSE Standard) or **Panasonic FC** for local decoupling
- For signal path (coupling): prefer **film capacitors**
- Electrolytic capacitors are **not a bottleneck** — mass available and cheap

---

## 3. 47Ω Output Series Resistors

### 3.1 Available Options

| Part Number | Series | Tol. | Tempco | Power | DigiKey Price | Stock |
|------------|-------|------|--------|-------|--------------|-------|
| **MFR-25FRF52-47R** | YAGEO MFR | 1% | ±100ppm | 1/4W | **$0.10** | 100k+ |
| RNF14FTD47R0 | Stackpole RNF | 1% | ±100ppm | 1/4W | $0.10 | 100k+ |
| CF14JT47R0 | Stackpole CF | 5% | 0/-400ppm | 1/4W | $0.10 | 100k+ |

**Recommendation:** YAGEO MFR-25FRF52-47R (1% metal film, $0.10). For 47Ω output resistors, 0.1% is neither necessary nor sensible — the value is non-critical (serves only HF decoupling/load termination).

---

## 4. Gotchas & Practical Notes for THT Precision Components (2026)

### 4.1 Availability

- **THT is increasingly niche.** Most new designs are SMD. THT precision resistors remain well available thanks to the audio/test equipment market.
- **LCSC/JLCPCB:** Very limited selection for THT precision. JLCPCB hand assembly of THT parts costs extra (~$0.02–$0.05/solder joint). Most economical: assemble THT parts yourself.
- **DigiKey/Mouser:** Best source for THT precision. Shipping to DE/EU ~$12–$20, but worthwhile for individual projects.

### 4.2 PCB Footprint Sizes

| Component | Body (D×L) | Recommended Pitch | Footprint |
|---------|-------------|-------------------|-----------|
| 1/4W Axial Resistor | 2.4×6.3 mm | 7.62–10.16 mm | Standard THT 0207 |
| WIMA MKS2 100nF | 7.2×2.5×6.5 mm | 5.0 mm | Radial_P5.0mm |
| Electrolytic 10µF (6.3mm) | Ø5×11 mm | 2.0–2.5 mm | Radial_D5.0mm_P2.5mm |
| Electrolytic 100µF (10mm) | Ø6.3–8×11 mm | 2.5–3.5 mm | Radial_D6.3mm_P2.5mm |

### 4.3 Audio Quality Notes

1. **0.1% matching is more important than absolute accuracy** — In differential amplifiers, the resistor ratio determines CMRR. Two resistors at 10.005kΩ and 10.008kΩ are perfect, as long as they're equal.

2. **Tempco matching also critical** — TE Neohm YR (±15 ppm/°C) has the advantage that all resistors shift approximately equally with temperature changes → CMRR remains stable.

3. **No carbon film in the signal path** — Voltage coefficient causes nonlinear distortion. Use metal film only.

4. **Film vs. ceramic for 100nF:** No disadvantage of film for audio. On the contrary — film has no microphony problem (X7R ceramic can generate voltage under vibration). WIMA MKS2 has been standard in studio equipment for 40+ years.

---

## 5. Shopping List — Suggested

### For Differential Amplifier (e.g., THAT1240 replacement with LM4562)

| Qty | Component | Part Number | Source | Unit Price |
|-----|---------|------------|--------|-----------|
| 8× | 10kΩ 0.1% | **MFP-25BRD52-10K** (YAGEO) | DigiKey | $0.60 |
| 4× | 20kΩ 0.1% | **MFP-25BRD52-20K** (YAGEO) | DigiKey | $0.60 |
| 4× | 4.7kΩ 0.1% (if needed) | **MFP-25BRD52-4K70** (YAGEO) | DigiKey | $0.60 |
| 4× | 47Ω 1% | **MFR-25FRF52-47R** (YAGEO) | DigiKey | $0.10 |
| 8× | 100nF Film | **WIMA MKS2D031001A00JSSD** | Mouser/DigiKey | ~$0.40 |
| 4× | 10µF 50V Electrolytic | Nichicon UKL1H100MDD | DigiKey/LCSC | ~$0.10 |
| 2× | 100µF 50V Electrolytic | Nichicon UKL1H101MED | DigiKey/LCSC | ~$0.25 |
| | | | **Total approx.:** | **~$14–$18** |

### Alternative: Premium Setup (TE Neohm, best tempco)

| Qty | Component | Part Number | Unit Price |
|-----|---------|------------|-----------|
| 8× | 10kΩ 0.1% ±15ppm | **YR1B10KCC** (TE) | $0.79 |
| 4× | 20kΩ 0.1% ±15ppm | YR1B20KCC (TE) | ~$0.79 |

Extra cost: ~$3–$5 for significantly better temperature drift.

---

## 6. Conclusion

### ✅ Resistors: No Problem

- 0.1% THT axial resistors are **well available and affordable** ($0.60–$0.80/pc)
- YAGEO MFP-25 is the pragmatic recommendation (price/availability)
- TE YR Neohm is the premium choice (best tempco)
- Vishay CMF55 is the audiophile classic, but hard to source at LCSC

### ⚠️ 100nF C0G in THT: Not Feasible

- C0G ceramic in THT only exists up to ~10nF
- **Film (WIMA MKS2) is the correct replacement** and sonically even preferred
- For decoupling, the dissipation factor difference to C0G is irrelevant

### ✅ Electrolytic Capacitors: No Bottleneck

- Mass product, trivially available

### ✅ 47Ω Output Resistors: Trivial

- Standard 1% metal film, $0.10/pc, available everywhere

### Recommended Suppliers for THT DIY

1. **DigiKey/Mouser** for precision resistors and WIMA capacitors
2. **LCSC/JLCPCB** only for standard parts (electrolytics, 1% resistors) — THT precision selection is severely limited there
