# Schematic Rebuild Guide

[← Back to README](../README.md) | [Signal Chain](signal-chain.md) | [Component Reference](component-reference.md)

This guide describes the minimal connections needed to rebuild the schematic from scratch. **All 6 channels are identical** — build CH1 completely, then repeat for CH2–CH6 with the corresponding component numbers.

---

## Step 1 — Power Supply

```
1.  Place U1 (TEL5-2422, DIP-24)
    Pin 22, 23 → /+24V_IN (Barrel Jack J1 positive)
    Pin 14     → /+12V_RAW
    Pin 11     → /−12V_RAW
    Pin 2,3,9,16 → GND

2.  C14 (100nF C0G) + C16 (100µF) between /+12V_RAW and GND
    C15 (100nF C0G) + C17 (100µF) between /−12V_RAW and GND

3.  FB1 (Ferrite BLM18PG221) in series: /+12V_RAW → /+12V
    FB2 (Ferrite BLM18PG221) in series: /−12V_RAW → /−12V
    C18 (100nF C0G) between /+12V and GND
    C19 (100nF C0G) between /−12V and GND

4.  U14 (ADP7118ARDZ, SOIC-8+EP)
    Pin 7,8 (VIN) → /+12V
    Pin 1,2,3 (VOUT) → /V+
    Pin 4,9 (GND) → GND
    Pin 5 (EN) → /EN_CTRL
    Pin 6 (SS) → C81 (22nF C0G) → GND

5.  U15 (ADP7182AUJZ, SOT-23-5)
    Pin 2 (VIN) → /−12V
    Pin 5 (VOUT) → /V−
    Pin 1 (GND) → GND
    Pin 3 (EN) → /EN_CTRL
    Pin 4 (NR) → C23 (100nF C0G) → GND

6.  C22 (100nF C0G) + C24 (10µF X5R): /V+ → GND (U14 output)
    C25 (10µF X5R): /V− → GND (U15 output)
    C20 (100µF) /V+ → GND (board bulk)
    C21 (100µF) /V− → GND
```

## Step 2 — Enable & Muting

```
7.  R56 (100kΩ): /V+ → /EN_CTRL  (pullup)
    R57 (100kΩ): /EN_CTRL → GND  (pulldown)

8.  SW1 (SPDT):
    - Pin1 → /+12V (ALWAYS connection)
    - Pin2 (COM) → /EN_CTRL
    - Pin3 → /REMOTE_FILT (remote mode)
    - (ALWAYS: SW1 connects /+12V to /EN_CTRL → LDOs always active)

9.  J2 (3.5mm audio jack): PinT=/REMOTE_IN, PinS=GND
    D1 (SMBJ15CA): A=/REMOTE_IN, K=GND (bidirectional ESD)
    /REMOTE_IN → R1 (10kΩ) → /REMOTE_FILT
    /REMOTE_FILT → C1 (100nF C0G) → GND

10. Q1 (BSS138): Source=GND, Drain=/MUTE
    R106 (10kΩ): /V+ → Net-(Q1-G)
    C80 (10µF): Net-(Q1-G) → GND  → 100ms power-on delay
    R107 (100kΩ): /V+ → /MUTE  (pullup, MUTE active-low)

11. Q2–Q7 (BSS138): Source=GND, Drain=/CH#_GAIN_OUT
    R108–R113 (10kΩ each): /MUTE → Net-(Q#-G)
```

## Step 3 — Input Protection CH1 (repeat for CH2–CH6)

```
12. J3 (XLR Female, CH1):
    Pin 1 → GND
    Pin 2 → /CH1_HOT_RAW
    Pin 3 → /CH1_COLD_RAW
    PinG → GND

13. D8 (PESD5V0S1BL): A=GND, K=/CH1_HOT_RAW   ← ESD input HOT
    D10 (PESD5V0S1BL): A=GND, K=/CH1_COLD_RAW  ← ESD input COLD

14. R94 (47Ω): /CH1_HOT_RAW → /CH1_EMI_HOT         ← EMI series R HOT
    C50 (100pF C0G): /CH1_EMI_HOT → GND             ← HF low-pass (fc ≈ 33 MHz)
    C62 (2.2µF C0G): /CH1_EMI_HOT → /CH1_HOT_IN    ← DC blocking HOT

    R95 (47Ω): /CH1_COLD_RAW → /CH1_EMI_COLD        ← EMI series R COLD
    C51 (100pF C0G): /CH1_EMI_COLD → GND            ← HF low-pass
    C63 (2.2µF C0G): /CH1_EMI_COLD → /CH1_COLD_IN  ← DC blocking COLD
```

## Step 4 — Differential Receiver CH1 (U2 Unit A)

```
15. Standard differential amplifier (all 4 resistors 10kΩ 0.1%)

    Non-inverting input:
    /CH1_HOT_IN → directly → IN+_A (Pin 3 U2)
    R2 (10kΩ 0.1%): GND → IN+_A  ← Reference resistor (matching)

    Inverting input:
    R3 (10kΩ 0.1%): /CH1_COLD_IN → IN−_A (Pin 2 U2)
    R14 (10kΩ 0.1%): GND → IN−_A  ← Common-mode reference resistor
    R20 (10kΩ 0.1%): OUT_A (Pin 1) → IN−_A  ← Feedback

    U2 Pin 8 (V+) → /V+,  Pin 4 (V−) → /V−
    Decoupling: C2 (100nF C0G) Pin 8 → GND, C8 (100nF C0G) Pin 4 → GND

    OUT_A (Pin 1) = /CH1_RX_OUT
    Transfer function: V_out = (V_HOT − V_COLD) × 1
```

## Step 5 — Gain Stage CH1 (U2 Unit B)

```
16. Inverting summing amplifier (U2 Unit B)

    R26 (10kΩ 0.1%): /CH1_RX_OUT → /CH1_SUMNODE
    R50 (10kΩ 0.1%): /CH1_GAIN_OUT → /CH1_SUMNODE  ← Feedback
    /CH1_SUMNODE = IN−_B (Pin 6 U2) = inverting input
    IN+_B (Pin 5 U2) → GND

    SW2 (DIP 3-pos, CH1) — Gain resistors (connect SW output to SUMNODE):
      SW2-Pos1 (30kΩ):  R27 → /CH1_SUMNODE  → Gain ×1.33 (+2.5dB) alone
      SW2-Pos2 (15kΩ):  R28 → /CH1_SUMNODE  → Gain ×1.67 (+4.4dB) alone
      SW2-Pos3 (7.5kΩ): R29 → /CH1_SUMNODE  → Gain ×2.33 (+7.4dB) alone
    (Multiple positions can be combined, max. ×3.66 = +11.3dB with all ON)

    OUT_B (Pin 7 U2) = /CH1_GAIN_OUT
```

## Step 6 — Muting CH1

```
17. Q2 (BSS138):
    R108 (10kΩ): /MUTE → Gate (Pin 1)  ← Gate protection resistor
    Source (Pin 2) → GND
    Drain (Pin 3) → /CH1_GAIN_OUT
    (When /MUTE HIGH: Q2 conducts → /CH1_GAIN_OUT pulled to GND → silence)
```

## Step 7 — Balanced Driver CH1 (U8)

```
18. U8 Unit A (COLD buffer, non-inverting):
    IN+_A (Pin 3) ← /CH1_GAIN_OUT
    IN−_A (Pin 2) ← OUT_A (Pin 1)  ← Unity feedback (voltage follower)
    OUT_A (Pin 1) = /CH1_BUF_DRIVE

19. U8 Unit B (HOT inverter, inverting):
    IN+_B (Pin 5) = GND
    R64 (10kΩ): /CH1_GAIN_OUT → IN−_B (Pin 6) = /CH1_GAIN_FB  ← Input
    R70 (10kΩ): OUT_B (Pin 7) → IN−_B  ← Feedback (Gain = −1)
    OUT_B (Pin 7) = /CH1_OUT_DRIVE

    U8 Pin 8 (V+) → /V+, C26 (100nF) → GND
    U8 Pin 4 (V−) → /V−, C32 (100nF) → GND
```

## Step 8 — Output CH1

```
20. COLD signal path (from BUF_DRIVE → output XLR Pin 3):
    R58 (47Ω): /CH1_BUF_DRIVE → /CH1_OUT_COLD     ← Series resistor
    D9 (PESD5V0S1BL): A=GND, K=/CH1_OUT_COLD  ← ESD
    R88 (10Ω) + C44 (100nF C0G): Zobel /CH1_OUT_COLD → GND

21. HOT signal path (from OUT_DRIVE → output XLR Pin 2):
    R76 (47Ω): /CH1_OUT_DRIVE → /CH1_OUT_HOT      ← Series resistor
    D2 (PESD5V0S1BL): A=GND, K=/CH1_OUT_HOT   ← ESD
    R82 (10Ω) + C38 (100nF C0G): Zobel /CH1_OUT_HOT → GND

22. J9 (XLR Male, CH1):
    Pin 1 → GND
    Pin 2 → /CH1_OUT_HOT   (same net as D2 K and R82 Pin1)
    Pin 3 → /CH1_OUT_COLD  (same net as D9 K and R88 Pin1)
    Note: R82+C38 and R88+C44 are Zobel snubbers (parallel to GND)
          /CH1_OUT_PROT_HOT = net between R82 and C38 (internal only)
```

---

## Component Mapping — All 6 Channels

| Components | CH1 | CH2 | CH3 | CH4 | CH5 | CH6 |
|----------|-----|-----|-----|-----|-----|-----|
| **XLR IN (J-Female)** | J3 | J4 | J5 | J6 | J7 | J8 |
| **XLR OUT (J-Male)** | J9 | J10 | J11 | J12 | J13 | J14 |
| **ESD Input HOT** | D8 | D11 | D14 | D17 | D20 | D23 |
| **ESD Input COLD** | D10 | D13 | D16 | D19 | D22 | D25 |
| **ESD Output HOT** | D2 | D3 | D4 | D5 | D6 | D7 |
| **ESD Output COLD** | D9 | D12 | D15 | D18 | D21 | D24 |
| **EMI R Input HOT** | R94 | R96 | R98 | R100 | R102 | R104 |
| **EMI R Input COLD** | R95 | R97 | R99 | R101 | R103 | R105 |
| **EMI C Input HOT** | C50 | C52 | C54 | C56 | C58 | C60 |
| **EMI C Input COLD** | C51 | C53 | C55 | C57 | C59 | C61 |
| **DC Block HOT** | C62 | C64 | C66 | C68 | C70 | C72 |
| **DC Block COLD** | C63 | C65 | C67 | C69 | C71 | C73 |
| **Diff/Gain IC** | U2 | U3 | U4 | U5 | U6 | U7 |
| **Driver IC** | U8 | U9 | U10 | U11 | U12 | U13 |
| **Muting MOSFET** | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 |
| **Muting Gate R** | R108 | R109 | R110 | R111 | R112 | R113 |
| **DIP Switch** | SW2 | SW3 | SW4 | SW5 | SW6 | SW7 |
| **Rin+ (GND→IN+_A)** | R2 | R4 | R6 | R8 | R10 | R12 |
| **Rg- (COLD→IN-_A)** | R3 | R5 | R7 | R9 | R11 | R13 |
| **Rref- (GND→IN-_A)** | R14 | R15 | R16 | R17 | R18 | R19 |
| **Rf (OUT_A→IN-_A)** | R20 | R21 | R22 | R23 | R24 | R25 |
| **Rin_gain (RX→SUM)** | R26 | R30 | R34 | R38 | R42 | R46 |
| **Rf_gain (OUT→SUM)** | R50 | R51 | R52 | R53 | R54 | R55 |
| **R_30k (DIP SW pos1)** | R27 | R31 | R35 | R39 | R43 | R47 |
| **R_15k (DIP SW pos2)** | R28 | R32 | R36 | R40 | R44 | R48 |
| **R_7.5k (DIP SW pos3)** | R29 | R33 | R37 | R41 | R45 | R49 |
| **Rin_inv (Driver)** | R64 | R65 | R66 | R67 | R68 | R69 |
| **Rf_inv (Driver)** | R70 | R71 | R72 | R73 | R74 | R75 |
| **R_47Ω COLD (BUF→OUT)** | R58 | R59 | R60 | R61 | R62 | R63 |
| **R_47Ω HOT (DRV→OUT)** | R76 | R77 | R78 | R79 | R80 | R81 |
| **R_10Ω Zobel HOT** | R82 | R83 | R84 | R85 | R86 | R87 |
| **R_10Ω Zobel COLD** | R88 | R89 | R90 | R91 | R92 | R93 |
| **C_Zobel HOT (100nF)** | C38 | C39 | C40 | C41 | C42 | C43 |
| **C_Zobel COLD (100nF)** | C44 | C45 | C46 | C47 | C48 | C49 |
| **V+ Decoupling** | C2 | C3 | C4 | C5 | C6 | C7 |
| **V− Decoupling** | C8 | C9 | C10 | C11 | C12 | C13 |
| **V+ Driver Decoupling** | C26 | C27 | C28 | C29 | C30 | C31 |
| **V− Driver Decoupling** | C32 | C33 | C34 | C35 | C36 | C37 |
