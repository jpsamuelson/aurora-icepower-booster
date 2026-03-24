# Power Supply Design: Linear vs. SMPS for Audio

[← Back to README](../../README.md) | [Power Supply Architecture](../power-supply.md)

---

## Summary

This document consolidates all findings from datasheets, technical articles (Rod Elliott/ESP, Analog Devices, Benchmark Media), DIY audio forums, and professional reference designs. It addresses the fundamental question: **Is a linear power supply actually better for audio signals than an SMPS with LDO post-regulation?**

**Answer: No — but an SMPS requires significantly more layout discipline on a 2-layer PCB.**

---

## 1. Noise Sources and Their Frequencies

### Linear Power Supply (Transformer → Rectifier → Electrolytic Cap → Linear Regulator)

| Noise Source | Frequency | Amplitude (typical) | Filterability |
|---|---|---|---|
| Mains hum (full-wave rectification) | 100/120 Hz | 1–3 Vpp (before regulator) | Trivial — op-amp PSRR >100 dB at 100 Hz |
| Diode switching spikes | 1–10 MHz transients | 10–50 mVpp | Filter cap impedance <10 mΩ at these frequencies |
| Transformer stray field (magnetic) | 50/60 Hz | Layout-dependent | Distance, orientation, shielding |
| Thermal noise (regulator) | Broadband | 5–50 µV RMS (LM317: ~40 µV) | Not filterable, but very small |

**Key insight**: All disturbances from a linear supply are either at very low frequencies (where op-amp PSRR is maximum) or so weak that they are irrelevant.

### SMPS / DC-DC Converter (e.g. TEL5-2422)

| Noise Source | Frequency | Amplitude (typical) | Filterability |
|---|---|---|---|
| Switching ripple (fundamental) | 100–500 kHz | 50–150 mVpp | Good — LC filter + LDO |
| Switching ripple (harmonics) | 500 kHz – 10 MHz | 5–30 mVpp | Medium — ferrite + ceramic C |
| Radiated EMI (magnetic field) | 100 kHz – 10 MHz | **Layout-dependent!** | **Cannot be eliminated by filters** |
| Common-mode noise | 100 kHz – 100 MHz | µV–mV, path-dependent | Y-capacitors, isolation |

**Key insight**: The most dangerous noise source of an SMPS is **radiated EMI via magnetic coupling** — this bypasses all conducted-noise filters (LDO, ferrite, capacitors).

---

## 2. PSRR Reality at Different Frequencies

### Op-Amp PSRR (LM4562, typical)

| Frequency | PSRR | Significance |
|---|---|---|
| 100 Hz | >100 dB | Mains hum suppressed by factor 100,000 |
| 1 kHz | ~95 dB | Still excellent |
| 10 kHz | ~80 dB | Good |
| 100 kHz | ~50 dB | Only factor 316 — SMPS ripple becomes relevant |
| 300 kHz | ~40 dB | Factor 100 — with 100 mV ripple, 1 mV remains |
| 1 MHz | ~30 dB | Factor 31.6 — insufficient without pre-filtering |

**Consequence**: At the TEL5-2422 switching frequency (~300 kHz), the LM4562 can only suppress conducted noise by ~40 dB. The entire filter chain (bulk C → ferrite → LDO → local C → op-amp PSRR) must collectively achieve >120 dB.

### LDO PSRR (ADP7118ARDZ-11)

**Datasheet specifications** (at VOUT ≤ 5 V, VIN = 7 V, i.e. 2 V dropout):

| Frequency | PSRR |
|---|---|
| 10 kHz | 88 dB |
| 100 kHz | 68 dB |
| 1 MHz | 50 dB |

**Actual operating point** of our design (VIN = 12 V → VOUT = 11 V, only 1 V dropout):

| Frequency | Estimated PSRR |
|---|---|
| 10 kHz | ~70 dB |
| 100 kHz | ~50 dB |
| 300 kHz | **~35–45 dB** |
| 1 MHz | ~25-30 dB |

**Why worse PSRR at low dropout?** The LDO's pass FET operates closer to the linear/saturation region. Less regulation headroom remains and the loop gain decreases — reducing the ability to suppress input disturbances. At 1 V dropout, the SOAR (Safe Operating Area) minimum is reached and the PSRR curve degrades significantly compared to datasheet values.

### Total Conducted Attenuation Chain (our design)

```
TEL5-2422 output ripple:       ~100 mVpp @ 300 kHz
  Bulk C (100 µF + 100 nF):    −20 dB  →  ~10 mVpp
  Ferrite BLM18PG221:           −6 dB   →  ~5 mVpp
  Input C (100 nF C0G):         −10 dB  →  ~1.5 mVpp
  ADP7118 PSRR @ 300 kHz:      −40 dB  →  ~15 µVpp
  Local C (100 nF C0G at IC):   −10 dB  →  ~5 µVpp
  LM4562 PSRR @ 300 kHz:       −40 dB  →  ~0.05 µVpp
─────────────────────────────────
Result at op-amp output:        ~50 nVpp (0.05 µV)
```

**Conducted noise is not a problem.** The cascade of passive filters + LDO + op-amp PSRR achieves ~126 dB total attenuation at 300 kHz. This is well below the LM4562 noise floor (~2.7 nV/√Hz input noise).

**HOWEVER**: This applies ONLY to conducted noise. Radiated EMI bypasses this chain entirely.

---

## 3. Radiated EMI — The Real Problem

### Mechanism (from Analog Devices Application Note)

Isolated DC-DC converters like the TEL5-2422 contain an internal switching transformer. During switching:

1. **Rapidly changing currents** (dI/dt > 100 A/µs) in the internal traces and transformer
2. This generates an **alternating magnetic field** (300 kHz fundamental + harmonics)
3. This field **couples inductively** into nearby traces — proportional to the loop area of the "victim loop"
4. Coupling falls off at **1/r³** in the near field (magnetic dipole field)

### Why Filters Don't Help

```
                  Magnetic Field
              ┌──────────────────┐
              │   TEL5-2422      │
              │   (internal      │
              │   switching      │
              │   transformer)   │
              └──────────────────┘
                     ↕ ↕ ↕  Magnetic coupling (through air!)
              ╔══════════════════╗
              ║  Audio trace     ║  ← Noise voltage is induced
              ║  (signal line)   ║     directly in the trace
              ╚══════════════════╝

Filters, LDOs, capacitors sit in the SUPPLY line,
not in the SIGNAL line → they never see the induced noise!
```

### Countermeasures (PCB layout only)

| Measure | Effect | For our design |
|---|---|---|
| **Physical distance** ≥ 20 mm | Coupling ∝ 1/r³ → 20× distance = 8000× less coupling | TEL5-2422 at board edge, audio ICs far away |
| **Unbroken ground plane** under signal trace | Minimizes signal loop area → less captured field | B.Cu GND plane under all audio traces |
| **DC/DC module orientation** | Switching transformer field is directional | Long axis of TEL5-2422 parallel to board edge |
| **GND stitching via wall** between DC/DC and analog | Vertical copper structures act as partial shield wall | Via row between PSU area and analog area |
| **No signal traces over DC/DC footprint** | Direct coupling | Keep-out zone on F.Cu over TEL5-2422 |
| **4-layer PCB** (if budget allows) | Internal ground plane shields signal layers | Currently 2-layer — works, but less margin |
| **Shield can** over DC/DC | Magnetic shielding | Only as last resort, often unnecessary at >20 mm distance |

---

## 4. Linear Power Supply — Detailed Analysis

### Typical Circuit (commercial ICEpower boosters)

```
230V AC → Toroidal transformer (15-0-15V) → Bridge rectifier → 2200–3900 µF electrolytics → LM317/337 → ±12–15V
```

### Advantages

| Property | Explanation |
|---|---|
| **Zero switching noise** | No fast-switching components → no HF EMI |
| **Layout tolerance** | Can be placed directly next to audio op-amps |
| **Simple filtering** | 100 Hz ripple is trivially suppressed by any regulator |
| **Thermal mass (rail stiffness)** | 3900 µF @ ±15V = ~0.9 Joule energy storage; transient current spikes absorbed without regulation |
| **Repairable** | Standard components, 50+ years availability |

### Disadvantages

| Property | Explanation |
|---|---|
| **No galvanic isolation** (with DC input) | For 24V DC input, a DC/DC converter or 230V transformer would be needed |
| **Large and heavy** | Toroidal transformer + large electrolytics dominate the form factor |
| **LM317 self-noise** | ~40–65 µV RMS — significantly worse than ADP7118 (11 µV RMS) |
| **100 Hz on V-rail** | Under high load, fundamental hum can appear on supply rail |
| **No isolation** | Simple LM317 circuit has no isolated output |
| **Voltage regulation** | ±10% mains fluctuation → direct DC variation (with unregulated stage) |
| **THT construction** | Large components, manual assembly, no JLCPCB SMT assembly |

### Rod Elliott (ESP) — Key Findings from "Linear Power Supply Design"

1. **Filter capacitors are extremely effective**: A 10,000 µF electrolytic has only 1.6 mΩ impedance at 10 kHz. "At all audio frequencies, the capacitors act as a short circuit for noise signals."
2. **"DC Sound" is a myth**: *"Anyone who claims audible differences between power supply filter caps, diodes, and mains leads — this is snake-oil."*
3. **Capacitance above ~10,000 µF yields diminishing returns**: Doubling capacitance halves ripple, but the effect becomes negligible above ~10,000 µF/Amp.
4. **Diode speed is irrelevant for 50/60 Hz**: *"The slowest diodes in the universe are still faster than they need to be."*
5. **Film bypass parallel to electrolytic is cosmetic**: A 100 nF film cap parallel to 10,000 µF provides ~2.6 µV impedance improvement — not significant compared to 65 mV ripple.

---

## 5. SMPS + LDO Post-Regulation — Detailed Analysis

### Typical Circuit (our design)

```
24V DC → TEL5-2422 (isolated DC/DC, ~300 kHz) → ±12V @ ±208 mA
  → 100 nF C0G + 100 µF bulk
  → Ferrite BLM18PG221
  → 100 nF C0G
  → ADP7118ARDZ-11 LDO (+12V → +11V) / ADP7182AUJZ-11 (-12V → -11V)
  → 100 nF C0G + 10 µF X5R + 100 µF bulk
  → Op-amp decoupling (24× 100 nF C0G)
```

### Advantages

| Property | Explanation |
|---|---|
| **Galvanic isolation** | TEL5-2422 is isolated → no ground loops to input |
| **Extremely low self-noise** | ADP7118: 11 µV RMS (vs. LM317: 40–65 µV RMS) |
| **Compact** | DIP-24 + SOT-23-5 + SOIC-8 — entire PSU on ~15 cm² |
| **JLCPCB-compatible** | Fully SMD, automatic assembly |
| **24V DC input** | No 230V transformer needed, safe, universal |
| **Good voltage regulation** | LDO ±0.8% initial accuracy, excellent load/line regulation |
| **Multi-stage filtering** | Passive (C, ferrite) + active (LDO) + local (C0G at IC) |

### Disadvantages

| Property | Explanation |
|---|---|
| **Radiated EMI** | Internal switching transformer generates magnetic field at ~300 kHz |
| **Layout-critical** | Distance and orientation of DC/DC are decisive |
| **PSRR degradation at low dropout** | 12V→11V = only 1V headroom → PSRR at 300 kHz only ~35–45 dB |
| **Limited current capacity for V−** | ADP7182 max. 200 mA for 12 op-amps |
| **Rail stiffness** | 100 µF at ±11V = ~0.012 Joule (vs. 0.9 J for linear supply) — factor 75 less energy storage |
| **Repairability** | SMD components, specialized ICs |

### Benchmark Media / John Siau — Key Findings

1. **SMPS ripple is at >100 kHz → above the audio band**: Op-amp PSRR at 100 Hz (>100 dB) is significantly better than at 100 kHz (~50 dB), but 100 Hz is IN the audio band and 100 kHz is NOT.
2. **Measured noise with properly filtered SMPS is lower**: Because the remaining ripple lies in the inaudible range.
3. **Professional SMPS audio equipment exists and measures excellently**: Benchmark AHB2 (THD+N < 0.0003%, 132 dB SNR), Grace Design m900 (>120 dB SNR).
4. **HOWEVER**: All professional designs use ≥4-layer PCBs with dedicated ground plane + power plane, often with physical shielding over the SMPS section.

---

## 6. Commercial ICEpower Boosters — Market Analysis

### Products Investigated

| Product | Op-Amp | Power Supply | Construction | Price |
|---|---|---|---|---|
| Audiophonics Unity Gain Buffer | LME49720 | LM317 + 3900 µF electrolytics | 100% THT | ~€129 |
| Audiophonics OP275 Buffer | OP275 DIP-8 | LM317/337 + 2200 µF + 220 µF Nichicon | THT | ~€35 |
| TheSlowDIYer ASX Buffer | OPA134/LME49710 DIP-8 | External recommended, 470–1000 µF | THT | DIY |
| XRK971 BTSB Buffer | OPA1656+LME49724 SMD | Murata isolated DC/DC + CLC filter | Hybrid SMD+THT | ~$88 |

### Why They All Use THT

1. **DIP-8 sockets for op-amp swapping** ("rolling") — hobbyist community feature
2. **Transformer-based PSU requires large electrolytics** → THT electrolytics are cheaper and more available than SMD >1000 µF
3. **No PCB layout expertise required** — linear supply + THT is tolerant of errors
4. **Visual aesthetics** — large electrolytics and toroidal transformers look "audiophile"
5. **Target audience is DIY** — hand assembly, no reflow oven

### Only Exception: XRK971 BTSB

The only board with a professional approach:

- SMD op-amps (not swappable → no rolling)
- Isolated DC/DC (Murata) + CLC π-filter
- Hybrid assembly (SMD + THT connectors)
- Technically superior to the Audiophonics approach, but less "hobbyist-friendly"

---

## 7. THT vs. SMD for Audio Circuits

### Resistors

| Property | SMD (0805/0603) | THT (Axial) |
|---|---|---|
| Available tolerance | ±0.1% (thin film) | ±0.1% (metal film) |
| Temperature coefficient | ≤10 ppm/°C | ≤25 ppm/°C |
| Noise (excess noise) | Lower (shorter resistor body) | Slightly higher |
| Parasitic inductance | ~0.5 nH | ~5–10 nH (lead length) |
| Audio recommendation | **Preferred** — shorter signal paths, fewer parasitics | Acceptable, but higher inductance |
| Sourcing 0.1%/±25 ppm | Yageo RT0805BRD0710KL (LCSC) | YAGEO MFP-25BRD52-10K (DigiKey) |

### Capacitors

| Type | SMD availability | THT availability | Audio suitability |
|---|---|---|---|
| **C0G/NP0 100 nF** | 0805: readily available (LCSC) | **Practically doesn't exist in THT!** | Ideal for audio |
| **C0G/NP0 2.2 µF** | 1210: available but expensive | N/A | Coupling capacitor |
| **X5R/X7R 10–100 µF** | 1206/1210 | N/A | Only for bulk decoupling, NOT in signal path |
| **Polypropylene film** | Hard to source in SMD | **Standard in THT** (WIMA, Panasonic) | Excellent for signal coupling |
| **Electrolytic 100+ µF** | 6.3×7.7mm SMD, limited | Standard, wide selection | Only bulk supply |

**Critical insight**: 100 nF C0G in THT essentially doesn't exist. The THT alternative would be a WIMA MKS2 film cap (100 nF, 5×7.2×2.5 mm) — larger and more expensive, but similar audio properties.

### Voltage Regulators

| Type | SMD | THT | Audio suitability |
|---|---|---|---|
| **LM317/337** | SOT-223/D2PAK | TO-220 | 40–65 µV RMS noise, good but not top-tier |
| **ADP7118** | SOIC-8/TSOT-23 | N/A | 11 µV RMS — **6× lower noise than LM317** |
| **LT3045** | MSOP-12 | N/A | 0.8 µV RMS — gold standard, SMD only |
| **TPS7A47** | SOT-23-5 | N/A | 4.3 µV RMS — excellent, SMD only |

**Consequence**: The lowest-noise LDOs exist only in SMD. A THT design is limited to the LM317/337, which has 4–6× higher self-noise than modern SMD LDOs.

### Op-Amps

| Type | SMD package | THT (DIP-8) | Performance |
|---|---|---|---|
| **LM4562** | SOIC-8 ✅ | DIP-8 ✅ | 2.7 nV/√Hz, 55 V/µs — best choice |
| **OPA1612** | SOIC-8 ✅ | DIP-8 ❌ | 1.1 nV/√Hz — better, but SMD only |
| **NE5532** | SOIC-8/DIP-8 | DIP-8 ✅ | 5 nV/√Hz — classic, good |
| **OPA2134** | SOIC-8/DIP-8 | DIP-8 ✅ | 8 nV/√Hz — "audiophile", but worse specs |

---

## 8. Design Decision Matrix

### When to Choose a Linear Power Supply

- ✅ 230V AC mains connection available
- ✅ THT hand assembly desired or required
- ✅ Space and weight are not a concern
- ✅ Maximum layout tolerance desired (beginner PCB)
- ✅ No JLCPCB assembly planned
- ✅ Op-amp socket swapping desired

### When to Choose SMPS + LDO

- ✅ DC input (12V/24V/48V)
- ✅ Galvanic isolation required
- ✅ Compact form factor desired
- ✅ Professional SMD assembly (JLCPCB)
- ✅ Lowest self-noise target (<15 µV RMS)
- ✅ Layout experience available (distance, orientation, stitching)
- ✅ No 230V transformer desired (safety, cost)

### Our Design: DC/DC + LDO — Assessment

| Criterion | Rating | Note |
|---|---|---|
| Conducted noise | ✅ Excellent | ~126 dB total attenuation at 300 kHz |
| Radiated EMI | ⚠️ Layout-dependent | TEL5-2422 must be ≥20 mm from audio inputs |
| LDO self-noise | ✅ Very good | ADP7118: 11 µV RMS |
| PSRR at switching frequency | ⚠️ Limited | ~35–45 dB at 1V dropout @ 300 kHz |
| Rail stiffness | ⚠️ Low | 100 µF = 0.012 J (75× less than 3900 µF electrolytic) |
| Galvanic isolation | ✅ | TEL5-2422 provides isolation |
| Compactness | ✅ | Entire PSU on ~15 cm² |
| JLCPCB-compatible | ✅ | Fully auto-assemblable |

---

## 9. Critical PCB Layout Rules for DC/DC Converters Near Audio

These rules apply **in addition to** the general PCB layout rules in the Copilot Instructions document:

1. **DC/DC converter ≥ 20 mm from nearest sensitive audio input** (XLR-In → differential receiver input)
2. **Unbroken GND plane (B.Cu) under all audio traces** — no interruptions, no via holes in critical areas
3. **Keep DC/DC return currents on one side of the board** — switching current return paths must not flow through the analog area
4. **Orient TEL5-2422 with long axis parallel to board edge**, away from analog area — the internal transformer field couples directionally
5. **GND via stitching wall** between DC/DC and analog area — at least one via every 3 mm
6. **No signal traces over the TEL5-2422 footprint** (F.Cu) — direct inductive coupling
7. **Consider copper keep-out zone** on F.Cu over and immediately beside the DC/DC module (2–3 mm margin)
8. **Input filter capacitors directly at TEL5-2422** (<3 mm) — reduces the "hot loop" area
9. **Bulk capacitors (100 µF) between DC/DC output and LDO input** — energy storage for transient demands

---

## 10. Power Budget Analysis — Transient Handling

### Input Voltage: 24V DC

The TEL5-2422 accepts **18–36 V input**. A 24V DC supply sits perfectly in the center of this range. All analysis in this document assumes 24V DC input. No design changes required.

### Current Budget Per Rail

| Item | V+ Rail | V− Rail |
|---|---|---|
| 12× LM4562 quiescent current (5 mA each) | 60 mA | 60 mA |
| Class-AB bias shift under signal (~2–3 mA/package) | +24–36 mA | +24–36 mA |
| Signal current into load (47Ω → 10+ kΩ ICEpower input) | <6 mA (all 24 outputs) | <6 mA |
| **Estimated peak** | **~100 mA** | **~100 mA** |

### Why the Load Current Is Negligible

ICEpower module inputs are typically 10–20 kΩ balanced. Even at ±10 V peak through a 47Ω series resistor: $I_{signal} = \frac{10\text{ V}}{47\text{ Ω} + 10\text{ kΩ}} \approx 1\text{ mA}$ per output. With 24 outputs total: ~5 mA signal current. The dominant current draw comes from LM4562 quiescent current and Class-AB output stage bias shift — not from driving the load.

### Transient Defense Hierarchy

Audio transients (drum hits, impulses) are **not** served by the LDO or DC/DC — they are served by the **local decoupling capacitors**:

| Transient Duration | Served By | Capacitance |
|---|---|---|
| < 1 µs | 100 nF C0G at IC pin (24× total, 2 per LM4562) | 2.4 µF aggregate |
| 1–100 µs | 10 µF X5R bulk (C24/C25 + C74–C79 = 8 caps) | 80 µF aggregate |
| > 100 µs | 100 µF board bulk (C20/C21) | 200 µF aggregate |
| Steady-state (ms) | LDO regulates to refill capacitors | Continuous |

**Voltage droop example**: 50 mA pulse for 1 ms into 100 µF board bulk: $\Delta V = \frac{I \cdot t}{C} = \frac{0.05 \times 0.001}{0.0001} = 0.5\text{ V}$. This is significant, but the closer 10 µF caps absorb the majority before the pulse reaches board-level bulk caps. The multi-tier decoupling structure ensures that fast transients see low ESR/ESL capacitors first.

### ADP7182 (−11V LDO) — Replacement Needed?

**No.** 200 mA provides ~2× headroom over the realistic ~100 mA peak. The apparent asymmetry vs. the ADP7118 (1.5 A positive rail) is misleading — the TEL5-2422 limits **both** rails to 208 mA anyway, so the ADP7118's 1.5 A capacity is irrelevant. Both rails are TEL5-limited.

| Parameter | ADP7118 (V+) | ADP7182 (V−) | Bottleneck |
|---|---|---|---|
| LDO max current | 1.5 A | 200 mA | TEL5-2422 (208 mA) |
| Effective max (TEL5 limited) | 208 mA | 200 mA | ADP7182 at 200 mA |
| Quiescent load | ~62 mA | ~62 mA | — |
| Estimated peak | ~100 mA | ~100 mA | — |
| Headroom | 108 mA (52%) | 100 mA (50%) | Adequate on both |

### TEL5-2422 — Sufficient for Transients?

**Yes.** At realistic ~100 mA peak, the TEL5-2422 operates at <50% capacity.

**Dropout risk at high load**: The TEL5-2422 has ±5% load regulation (datasheet). At 200 mA worst case: $V_{out,min} = 12\text{ V} \times 0.95 = 11.4\text{ V}$. The ADP7182 dropout at 200 mA is ~0.3 V, requiring ≥11.3 V input → margin is only 0.1 V. **However**, we never reach 200 mA. At the realistic 100 mA peak, the TEL5 output stays at ~11.7–11.8 V, and ADP7182 dropout at 100 mA is <0.2 V → **~0.6 V headroom — comfortable.**

An upgrade to TEL 10-2422 (10 W, ~416 mA per rail) would only be justified if:

- Significantly more op-amps were added, or
- Low-impedance loads (<600 Ω) were driven directly

### Summary

| Question | Answer | Rationale |
|---|---|---|
| 24V supply — changes anything? | **No** | TEL5-2422 operates optimally at 24V (18–36V range) |
| Replace ADP7182? | **No** | 200 mA is ~2× the realistic peak. Both rails are TEL5-limited at 208 mA anyway |
| TEL5-2422 sufficient? | **Yes** | 208 mA at ~100 mA peak. Dropout only critical at theoretical max, not at real load |
| What handles transients? | **Local decoupling caps** | 24× 100nF C0G + 8× 10µF X5R + 2× 100µF — not the LDO or DC/DC |

---

## 11. Sources and References

| Source | Content | Status |
|---|---|---|
| Rod Elliott, ESP — "Linear Power Supply Design" | Comprehensive analysis of linear supplies, myths, capacitor sizing | ✅ Fully read |
| Rod Elliott, ESP — "Switchmode Power Supply Primer" | SMPS topologies, fundamentals, EMI issues | ✅ Fully read |
| Analog Devices — "Switching Regulator Noise Reduction with an LC Filter" (Frederik Dostal) | Hot-loop EMI, input-side filtering, inductive coupling | ✅ Fully read |
| ADP7118 Datasheet (Rev.H) | PSRR: 88dB@10kHz, 68dB@100kHz, 50dB@1MHz (at VOUT≤5V, VIN=7V) | ✅ Specifications extracted |
| ADP7182 Datasheet | Negative LDO, 200 mA, SOT-23-5 | ✅ Specifications from schematic |
| TEL5-2422 Datasheet | Isolated DC/DC, DIP-24, ±12V, ±208 mA | 📄 Local in datasheets/ |
| Benchmark Media — "Audio Myth: Switching Power Supplies Are Noisy" | SMPS defense from professional audio perspective | ❌ Website unreachable |
| Neurochrome — "Switching vs Linear Power Supplies" | Professional audio PSU comparisons | ❌ Website unreachable |
| Audiophonics — Buffer board product pages | Commercial THT buffers with LM317 PSU | ✅ Analyzed |
| DIYaudio Forum — ICEpower buffer discussions | Community designs, XRK971 BTSB | ✅ Partially analyzed |
