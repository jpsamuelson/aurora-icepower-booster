# Balanced Audio Line Receiver & Driver ICs — Research Report

**Project:** Aurora DSP ICEpower Booster
**Date:** 2026-03-12
**Purpose:** Comparison of dedicated balanced audio ICs vs. discrete LM4562 solution

---

## 1. THAT Corporation — InGenius Receivers & OutSmarts Drivers

### 1.1 THAT1240 — Balanced Line Receiver (InGenius)

| Parameter | Value |
|-----------|-------|
| **Function** | Balanced → Single-Ended, 1 channel |
| **Topology** | InGenius™ — patented combination of current feedback + servo |
| **Gain** | Unity (0 dB) |
| **Package** | DIP-8 (THAT1240P08), SOIC-8 (THAT1240S08) |
| **CMRR** | >90 dB DC to 20 kHz (typ.) |
| **CMRR with source impedance mismatch** | >60 dB even at 10% source mismatch! |
| **THD+N** | 0.0004% typ. @ 1 kHz |
| **Noise** | -103 dBu (A-weighted) |
| **Bandwidth** | ~4 MHz |
| **Slew Rate** | ~8 V/µs |
| **Max Input Level** | +26 dBu @ ±18V supply |
| **Supply** | ±5V to ±18V |
| **Quiescent Current** | ~4.5 mA |
| **Price (Mouser/DigiKey)** | ~$3.50–$5.00 |
| **LCSC/JLCPCB** | ❌ **NOT AVAILABLE** |

**Key feature:** The decisive advantage of the InGenius topology is that CMRR remains high even with unbalanced source impedances. A standard differential amplifier (e.g., INA134, SSM2143) loses its CMRR proportionally to the impedance mismatch at the inputs — often dramatically in real-world cabling scenarios. InGenius circumvents this through a servo loop that dynamically adapts the input impedance.

### 1.2 THAT1246 — Balanced Line Receiver (InGenius, +6 dB)

| Parameter | Value |
|-----------|-------|
| **Function** | Balanced → SE, 1 channel, **Gain = 2 (+6 dB)** |
| **Topology** | InGenius™ (identical to THAT1240) |
| **Package** | DIP-8, SOIC-8 |
| **All specs** | Same as THAT1240, but G = 2 |
| **LCSC/JLCPCB** | ❌ **NOT AVAILABLE** |

The THAT1246 is preferred when the receiver needs to compensate for the -6 dB level loss of the professional balanced line (±half level), which at G=2 yields exactly unity gain across the entire signal path.

### 1.3 THAT1200 — Balanced Line Receiver (predecessor)

| Parameter | Value |
|-----------|-------|
| **Function** | Balanced → SE, 1 channel |
| **Topology** | Standard differential amplifier with trimmed resistors |
| **CMRR** | ~70 dB typ. (significantly worse than 1240 series) |
| **Package** | DIP-8, SOIC-8 |
| **Status** | Superseded by THAT1240 series |
| **LCSC/JLCPCB** | ❌ **NOT AVAILABLE** |

**Assessment:** Obsolete, no reason to use the 1200 series. The 1240 is superior in every regard.

### 1.4 THAT1606 — Balanced Line Driver (OutSmarts)

| Parameter | Value |
|-----------|-------|
| **Function** | Single-Ended → Balanced, 1 channel |
| **Topology** | OutSmarts™ — cross-coupled with servo feedback |
| **Gain** | Unity (0 dB) |
| **Package** | SOIC-8 |
| **THD+N** | 0.0003% typ. @ 1 kHz |
| **Output Balance** | >60 dB even with unbalanced load |
| **Noise** | -107 dBu (A-weighted) |
| **Max Output** | +24 dBu @ ±18V supply |
| **Slew Rate** | ~15 V/µs |
| **Supply** | ±5V to ±18V |
| **Quiescent Current** | ~6.5 mA |
| **Price (Mouser/DigiKey)** | ~$4.00–$6.00 |
| **LCSC/JLCPCB** | ❌ **NOT AVAILABLE** |

**Key feature:** The OutSmarts topology maintains output balance even with unbalanced loads (e.g., when only one pin is loaded). A standard cross-coupled driver (like DRV134) loses balance here. Additionally, OutSmarts enables "electronic impedance balancing" that improves common-mode rejection at the receiver.

### 1.5 THAT1646 — Balanced Line Driver (OutSmarts, +6 dB)

| Parameter | Value |
|-----------|-------|
| **Function** | SE → Balanced, 1 channel, **Gain = 2 (+6 dB)** |
| **Topology** | OutSmarts™ (identical to THAT1606) |
| **Package** | SOIC-8 |
| **All specs** | Same as THAT1606, but G = 2 |
| **LCSC/JLCPCB** | ❌ **NOT AVAILABLE** |

---

## 2. TI/Burr-Brown — DRV134/DRV135 Line Drivers

### 2.1 DRV134 — Audio Balanced Line Driver (PDIP-8 / SOIC-16)

| Parameter | Value |
|-----------|-------|
| **Function** | SE → Balanced, 1 channel |
| **Topology** | Cross-coupled with precision resistors |
| **Package** | PDIP-8 (DRV134PA), SOIC-16 (DRV134UA) |
| **THD+N** | 0.0005% typ. @ 1 kHz |
| **Slew Rate** | 15 V/µs |
| **Max Output** | 17 Vrms into 600Ω |
| **Supply** | ±4.5V to ±18V (9–36V) |
| **Quiescent Current** | 5.2 mA |
| **Price (TI 1ku)** | ~$2.28–$2.74 |
| **Status** | **ACTIVE** — Improved replacement for SSM2142 |

**LCSC Availability:**

| Part Number | Package | Stock | Price (1 pc) |
|-------------|---------|-------|-------------|
| DRV134PA | PDIP-8 | 0 (back-order) | $6.29 |
| DRV134UA/1K | SOIC-16 | 5 pcs | $5.95 |

⚠️ **Very low LCSC stock. SOIC-16 is inconvenient for audio PCBs (large). PDIP-8 not SMT-compatible for JLCPCB assembly.**

### 2.2 DRV135 — Audio Balanced Line Driver (SOIC-8)

| Parameter | Value |
|-----------|-------|
| **Function** | SE → Balanced, 1 channel |
| **Topology** | Identical to DRV134 |
| **Package** | **SOIC-8** (space-efficient!) |
| **All specs** | Identical to DRV134 |
| **Status** | **ACTIVE** |

**LCSC Availability:**

| Part Number | Package | Stock | Price (1 pc) |
|-------------|---------|-------|-------------|
| DRV135UA | SOIC-8 | 0 (back-order) | $3.46 |
| DRV135UA/2K5 | SOIC-8 | **3,865 pcs** ✅ | **$2.78** |

✅ **DRV135UA/2K5 is the best candidate among dedicated line drivers for JLCPCB assembly!** Good stock, SOIC-8 package, reasonable price.

### 2.3 INA1634 (TI)

| Parameter | Value |
|-----------|-------|
| **Status** | ❌ **Does not exist** (TI website returns 404) |

**Note:** The existing TI differential receivers for audio are:

- **INA134** — Differential Line Receiver, G = 1, SOIC-8/DIP-8 (companion to DRV134)
- **INA137** — Differential Line Receiver, G = 1/2, SOIC-8/DIP-8

These have ~80 dB CMRR but suffer like all standard differential amplifiers from CMRR degradation with source impedance mismatch.

---

## 3. Analog Devices — SSM2142/SSM2143

### 3.1 SSM2142 — Balanced Line Driver

| Parameter | Value |
|-----------|-------|
| **Function** | SE → Balanced, 1 channel |
| **Status** | ⛔ **OBSOLETE** |
| **Package** | DIP-8 (only!) |
| **THD** | 0.006% typ., 20 Hz–20 kHz, 10V RMS into 600Ω |
| **CMRR** | 80 dB |
| **Slew Rate** | 15 V/µs |
| **Max Output** | 10V RMS into 600Ω |
| **Supply** | ±15V (fixed, no wide range) |

**LCSC Availability:**

| Part Number | Stock | Price |
|-------------|-------|-------|
| SSM2142PZ | 0 | $149.83 (!) |
| SSM2142SZ (3rd party) | 95 | $78.52 |

⛔ **DO NOT USE. Obsolete, absurdly expensive, DIP-8 only, worse specs than DRV134/135.**

### 3.2 SSM2143 — Differential Line Receiver

| Parameter | Value |
|-----------|-------|
| **Function** | Balanced → SE, 1 channel |
| **Status** | ⛔ **OBSOLETE** |
| **Package** | SOIC-8 (SSM2143S/SZ), PDIP-8 (SSM2143P) |
| **CMRR** | 90 dB @ DC/60 Hz, 85 dB @ 20 kHz |
| **THD** | 0.0006% typ. @ 1 kHz |
| **Slew Rate** | 10 V/µs |
| **Bandwidth** | 7 MHz (G = 1/2) |
| **Gain** | G = 1/2 (or G = 2 via pin swap) |
| **Max Input** | +28 dBu @ G = 1/2 |
| **Supply** | ±5V to ±18V |
| **Replacement** | AD8273 (recommended by ADI) |

**LCSC Availability:**

| Part Number | Stock | Price |
|-------------|-------|-------|
| SSM2143S | Discontinued | — |
| SSM2143P | Discontinued | — |
| SSM2143SZ | 0 (SOIC-8) | $8.83 |
| SSM2143S-REEL | Discontinued | — |

⚠️ **Obsolete and poorly available. The SSM2143 was a very good IC, but no longer recommended for new designs.**

---

## 4. LM4562 — Discrete Balanced Solution (current design)

### 4.1 LM4562 — Dual Low-Noise Audio Op-Amp

| Parameter | Value |
|-----------|-------|
| **Function** | Dual operational amplifier, general purpose |
| **Package** | SOIC-8 (LM4562MAX), PDIP-8 (LM4562NA) |
| **THD+N** | **0.00003%** typ. @ 1 kHz (!) |
| **Noise** | 2.7 nV/√Hz |
| **Slew Rate** | 20 V/µs |
| **GBW** | 55 MHz |
| **Supply** | ±2.5V to ±17V |
| **Output** | ±13.5V @ 600Ω (with ±15V) |
| **Quiescent Current** | 5 mA/channel |

**LCSC Availability:**

| Part Number | Package | Stock | Price (1 pc) | Price (500+) |
|-------------|---------|-------|-------------|-------------|
| **LM4562MAX/NOPB** | **SOIC-8** | **5,453 pcs** ✅ | $2.08 | **$1.36** |
| LM4562NA/NOPB | PDIP-8 | 199 pcs | $9.24 | — |

✅ **Excellent availability, best price, SOIC-8 perfect for JLCPCB assembly.**

---

## 5. LCSC/JLCPCB Availability Summary

| IC | LCSC available? | Stock | Best Price | Package | Assembly-ready? |
|----|-----------------|-------|------------|---------|----------------|
| **THAT1240** | ❌ No | 0 | — | — | No |
| **THAT1246** | ❌ No | 0 | — | — | No |
| **THAT1200** | ❌ No | 0 | — | — | No |
| **THAT1606** | ❌ No | 0 | — | — | No |
| **THAT1646** | ❌ No | 0 | — | — | No |
| **INA1634** | ❌ Does not exist | — | — | — | — |
| **DRV134PA** | ⚠️ Yes (0 pcs) | 0 | $6.29 | PDIP-8 | ❌ THT |
| **DRV134UA** | ⚠️ Yes (5 pcs) | 5 | $5.95 | SOIC-16 | ⚠️ Large |
| **DRV135UA/2K5** | ✅ **Yes** | **3,865** | **$2.78** | **SOIC-8** | ✅ **Yes** |
| **SSM2142** | ⚠️ Yes (0 pcs) | 0 | $149.83 | DIP-8 | ❌ Obsolete/THT |
| **SSM2143SZ** | ⚠️ Yes (0 pcs) | 0 | $8.83 | SOIC-8 | ❌ Obsolete |
| **LM4562MAX** | ✅ **Yes** | **5,453** | **$2.08** | **SOIC-8** | ✅ **Yes** |

---

## 6. Comparison: Dedicated ICs vs. Discrete LM4562 Solution

### 6.1 Balanced Receiver: THAT1240 vs. LM4562 Differential Amplifier

#### LM4562-based Differential Receiver (current design)

```
Circuit: 1× LM4562 (dual) per channel
  - OPA1: Instrumentation amplifier topology or
  - Simple differential amplifier with 4× precision resistors (0.1%)

Components per channel:
  - 1× LM4562 (SOIC-8)
  - 4× resistors 0.1% (0402/0603)
  - 2–4× capacitors (decoupling)
  = 7–9 components, ~15 mm² PCB area
```

#### THAT1240 Receiver

```
Components per channel:
  - 1× THAT1240 (SOIC-8)
  - 2× capacitors (decoupling)
  = 3 components, ~8 mm² PCB area
```

| Criterion | THAT1240 | LM4562 discrete |
|-----------|----------|----------------|
| Component count/channel | 3 | 7–9 |
| PCB area/channel | ~8 mm² | ~15 mm² |
| THD+N | 0.0004% | **0.00003%** (10× better!) |
| CMRR (ideal) | >90 dB | ~80 dB (depends on R matching) |
| CMRR (with source mismatch) | **>60 dB** (InGenius advantage!) | ~40–50 dB (degrades!) |
| Noise | -103 dBu | **-108 dBu** (LM4562 is quieter) |
| IC cost/channel | ~$4.00 | **~$2.08** (+ ~$0.20 R) |
| JLCPCB Assembly | ❌ **NO** | ✅ **YES** |
| Design effort | Minimal | Medium (R matching, layout) |

### 6.2 Balanced Driver: DRV135 vs. LM4562 Buffer+Inverter

#### LM4562-based Balanced Driver (current design)

```
Circuit: 1× LM4562 (dual) per channel
  - OPA1: Unity-gain buffer (output = +signal)
  - OPA2: Inverting amplifier G=-1 (output = -signal)
  - 3× resistors for inverter

Components per channel:
  - 1× LM4562 (SOIC-8)
  - 3× resistors 0.1% (0402/0603)
  - 2–4× capacitors (decoupling)
  = 6–8 components, ~12 mm² PCB area
```

#### DRV135 Driver

```
Components per channel:
  - 1× DRV135 (SOIC-8)
  - 2× capacitors (decoupling)
  = 3 components, ~8 mm² PCB area
```

| Criterion | DRV135 | LM4562 discrete |
|-----------|--------|----------------|
| Component count/channel | 3 | 6–8 |
| PCB area/channel | ~8 mm² | ~12 mm² |
| THD+N | 0.0005% | **0.00003%** (15× better!) |
| Output balance (ideal) | ~60 dB (laser-trimmed R) | ~50 dB (depends on R matching) |
| Output balance (unbal. load) | ~40 dB | ~40 dB (both degrade) |
| Noise | ~-100 dBu | **~-108 dBu** |
| Max output | 17 Vrms/600Ω | ~13.5 Vrms/600Ω |
| IC cost/channel | $2.78 | **$2.08** (+ ~$0.15 R) |
| JLCPCB Assembly | ✅ Yes (3,865 pcs) | ✅ **Yes** (5,453 pcs) |
| Design effort | Minimal | Medium |

### 6.3 Overall Comparison: 3-Channel System (3× Receiver + 3× Driver)

| Criterion | Dedicated ICs (THAT/DRV) | 6× LM4562 discrete |
|-----------|---------------------------|---------------------|
| **Total ICs** | 3× THAT1240 + 3× DRV135 = 6 ICs | 6× LM4562 = 6 ICs |
| **Resistors** | 0 | 21× precision R (0.1%) |
| **Total components** | ~18 + 12 caps = ~30 | ~42 + 12 caps = ~54 |
| **PCB area** | ~48 mm² | ~81 mm² |
| **THD+N** | 0.0003–0.0005% | **0.00003%** |
| **Noise floor** | ~-103 dBu | **~-108 dBu** |
| **CMRR (receiver, real)** | **>60 dB (InGenius!)** | ~40–50 dB |
| **IC cost** | 3×$4 + 3×$2.78 = $20.34 | 6×$2.08 = **$12.48** |
| **Total cost** | ~$21 (few R) | ~**$14** (21 R @ $0.05) |
| **JLCPCB Assembly** | ❌ THAT not on LCSC! | ✅ **Fully available** |

---

## 7. Recommendation

### 7.1 For JLCPCB Manufacturing: LM4562 Discrete (clear winner)

**The discrete LM4562 solution is the right choice for this project:**

1. **Availability:** LM4562MAX/NOPB has >5,400 pcs at LCSC, SOIC-8, $2.08/pc. All THAT Corp ICs are not available at LCSC and are therefore disqualified for JLCPCB assembly.

2. **Audio Performance:** LM4562 is **significantly superior** to the dedicated ICs in THD+N and noise performance (factor 10–15 in THD, 5 dB in noise). The theoretically better CMRR of the THAT1240 is only relevant when the signal source has strongly unbalanced impedances — rarely the case in an internal amplifier board.

3. **Cost:** ~$14 vs. ~$21 for 3 channels. More components, but cheaper ICs and standard resistors.

4. **Flexibility:** With LM4562, gain can be freely adjusted (not limited to unity or +6 dB).

### 7.2 Only Possible DRV135 Use Case

If the balanced output stage should be simplified, the **DRV135UA/2K5** would be an option:

- 3,865 pcs available at LCSC
- SOIC-8, $2.78/pc
- Saves 3× resistors and layout effort per channel
- But worse THD than LM4562 solution

**Possible hybrid approach:**

- **Receiver:** 3× LM4562 as differential amplifier (better performance, available)
- **Driver:** 3× DRV135 (fewer components, acceptable performance, available)
- Cost advantage: Less PCB area for drivers, full performance for receivers

### 7.3 When THAT ICs Would Make Sense

THAT Corporation ICs would only be justified when:

- The board is **not assembled at JLCPCB** (hand assembly / different assembler)
- The signal source has **unknown/variable source impedances** (e.g., external mixer over long cables)
- CMRR under real-world conditions is absolutely critical

For an internal ICEpower booster board where signals come from a known DSP, the advantages of the LM4562 solution outweigh.

### 7.4 Recommended Approach

```
✅ Receiver (Balanced → SE):  3× LM4562MAX/NOPB (SOIC-8)
                               + 12× 0.1% resistors (10k/10k or adjusted)
                               + 6× decoupling caps

✅ Driver (SE → Balanced):     3× LM4562MAX/NOPB (SOIC-8)
                               + 9× 0.1% resistors (buffer + inverter)
                               + 6× decoupling caps

Alternative Driver:            3× DRV135UA/2K5 (SOIC-8, $2.78)
                               + 6× decoupling caps
                               (fewer components, slightly worse THD)
```

---

## 8. Design Notes for LM4562-Based Solution

### 8.1 Receiver (Differential Amplifier)

- **Resistor matching is CRITICAL for CMRR:** Use 0.1% resistors (e.g., Panasonic ERA series)
- Alternatively: Resistor networks (e.g., Bourns CAT16) for even better matching
- Typical CMRR with 0.1% matching: ~66 dB. With 0.01%: ~86 dB.
- **Layout:** Place resistors thermally coupled (adjacent, same orientation)
- CMRR formula: $CMRR \approx 20 \log_{10}\left(\frac{1}{4 \cdot \delta}\right)$ where $\delta$ is the relative resistor error

### 8.2 Driver (Buffer + Inverter)

- **Inverter resistors:** 0.1% for good output balance
- No resistors in the buffer path (unity-gain follower)
- Output balance: $Balance \approx 20 \log_{10}\left(\frac{1}{2 \cdot \delta}\right)$
- 100Ω series resistors at both outputs for short-circuit protection + HF damping

### 8.3 General

- 100nF C0G directly at VCC/GND pins of each LM4562
- 10µF bulk cap per supply rail
- No signal traces under ICs on the ground plane
- Guard traces around sensitive receiver inputs

---

## Appendix: All Investigated ICs at a Glance

| IC | Manufacturer | Type | Function | Package | THD+N | CMRR/Balance | Supply | Status | LCSC? | Price |
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
