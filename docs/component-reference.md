# Component Reference

[← Back to README](../README.md) | [Signal Chain](signal-chain.md) | [Schematic Rebuild Guide](schematic-rebuild-guide.md)

---

## Op-Amps: LM4562 (U2–U13)

12× Dual op-amp SOIC-8. Each LM4562 contains **Unit A** and **Unit B** (1 op-amp each).

| Ref | Unit A Function | Unit B Function | V+ on | V− on |
|-----|----------------|----------------|-------|-------|
| U2 | CH1 Diff Receiver | CH1 Gain Stage | /V+ | /V− |
| U3 | CH2 Diff Receiver | CH2 Gain Stage | /V+ | /V− |
| U4 | CH3 Diff Receiver | CH3 Gain Stage | /V+ | /V− |
| U5 | CH4 Diff Receiver | CH4 Gain Stage | /V+ | /V− |
| U6 | CH5 Diff Receiver | CH5 Gain Stage | /V+ | /V− |
| U7 | CH6 Diff Receiver | CH6 Gain Stage | /V+ | /V− |
| U8 | CH1 HOT Buffer | CH1 COLD Inverter | /V+ | /V− |
| U9 | CH2 HOT Buffer | CH2 COLD Inverter | /V+ | /V− |
| U10 | CH3 HOT Buffer | CH3 COLD Inverter | /V+ | /V− |
| U11 | CH4 HOT Buffer | CH4 COLD Inverter | /V+ | /V− |
| U12 | CH5 HOT Buffer | CH5 COLD Inverter | /V+ | /V− |
| U13 | CH6 HOT Buffer | CH6 COLD Inverter | /V+ | /V− |

**LM4562 SOIC-8 Pinout** (per TI datasheet):

```
        ┌───────────┐
OUT_A ──┤ 1       8 ├── V+
IN−_A ──┤ 2       7 ├── OUT_B
IN+_A ──┤ 3       6 ├── IN−_B
   V− ──┤ 4       5 ├── IN+_B
        └───────────┘
```

> Pin 5 = **IN+_B** (not IN-_B!) and Pin 6 = **IN-_B** — common point of confusion on the LM4562!

---

## Resistors (R)

### Diff Receiver Network (4 resistors per channel, 0.1% metal film)

| CH | Rin+ (GND→IN+_A) | Rg- (COLD→INV) | Rref- (GND→INV) | Rf (RX_OUT→INV) |
|----|--------------------|--------------------|-------------------|-------------------|
| 1 | R2 | R3 | R14 | R20 |
| 2 | R4 | R5 | R15 | R21 |
| 3 | R6 | R7 | R16 | R22 |
| 4 | R8 | R9 | R17 | R23 |
| 5 | R10 | R11 | R18 | R24 |
| 6 | R12 | R13 | R19 | R25 |

All: **10kΩ 0.1% metal film**

### Gain Network (per channel)

| CH | Rin (RX→SUMNODE) | Rf (GAIN_OUT→SUMNODE) | R_30k (SW Pos3) | R_15k (SW Pos2) | R_7.5k (SW Pos1) |
|----|-----------------|----------------------|----------------|----------------|------------------|
| 1 | R26 | R50 | R27 | R28 | R29 |
| 2 | R30 | R51 | R31 | R32 | R33 |
| 3 | R34 | R52 | R35 | R36 | R37 |
| 4 | R38 | R53 | R39 | R40 | R41 |
| 5 | R42 | R54 | R43 | R44 | R45 |
| 6 | R46 | R55 | R47 | R48 | R49 |

Rin and Rf: **10kΩ 0.1%**; Gain resistors: 30k / 15k / 7.5k (1%)

### Driver Stage (per channel)

| CH | Rin Inv (GAIN_OUT→GAIN_FB) | Rf Inv (OUT_DRIVE→GAIN_FB) | R_COLD 47Ω (BUF→COLD) | R_HOT 47Ω (DRIVE→HOT) |
|----|--------------------------|--------------------------|----------------------|---------------------|
| 1 | R64 | R70 | R58 | R76 |
| 2 | R65 | R71 | R59 | R77 |
| 3 | R66 | R72 | R60 | R78 |
| 4 | R67 | R73 | R61 | R79 |
| 5 | R68 | R74 | R62 | R80 |
| 6 | R69 | R75 | R63 | R81 |

### Zobel Network — Output Series Resistors (10Ω)

| CH | R_Zobel_HOT | R_Zobel_COLD |
|----|-------------|-------------|
| 1 | R82 | R88 |
| 2 | R83 | R89 |
| 3 | R84 | R90 |
| 4 | R85 | R91 |
| 5 | R86 | R92 |
| 6 | R87 | R93 |

### EMI Input Filter — Series Resistors (47Ω)

| CH | R_EMI_HOT | R_EMI_COLD |
|----|-----------|------------|
| 1 | R94 | R95 |
| 2 | R96 | R97 |
| 3 | R98 | R99 |
| 4 | R100 | R101 |
| 5 | R102 | R103 |
| 6 | R104 | R105 |

### Other Resistors

| Ref | Value | Function | Connection |
|-----|-------|----------|------------|
| R1 | 10kΩ | Remote RC filter | /REMOTE_IN → /REMOTE_FILT |
| R56 | 100kΩ | Pullup EN_CTRL | /V+ → /EN_CTRL |
| R57 | 100kΩ | Pulldown EN_CTRL | /EN_CTRL → GND |
| R106 | 10kΩ | Q1 gate charge R | /V+ → Net-(Q1-G) |
| R107 | 100kΩ | /MUTE pullup | /V+ → /MUTE |
| R108–R113 | 10kΩ each | Gate Rs Q2–Q7 | /MUTE → Net-(Qx-G) |

---

## Capacitors (C)

### DC Blocking (2.2µF C0G, 2 per channel = 12 total)

| CH | C_HOT | C_COLD |
|----|-------|--------|
| 1 | C62 | C63 |
| 2 | C64 | C65 |
| 3 | C66 | C67 |
| 4 | C68 | C69 |
| 5 | C70 | C71 |
| 6 | C72 | C73 |

### EMI HF Filter (100pF C0G, 2 per channel = 12 total)

| CH | C_HOT | C_COLD |
|----|-------|--------|
| 1 | C50 | C51 |
| 2 | C52 | C53 |
| 3 | C54 | C55 |
| 4 | C56 | C57 |
| 5 | C58 | C59 |
| 6 | C60 | C61 |

### Zobel Capacitors (100nF C0G, output filter)

| CH | C_Zobel_HOT | C_Zobel_COLD |
|----|-------------|-------------|
| 1 | C38 | C44 |
| 2 | C39 | C45 |
| 3 | C40 | C46 |
| 4 | C41 | C47 |
| 5 | C42 | C48 |
| 6 | C43 | C49 |

### Supply Bulk & Filter

| Ref | Value | Function | Net |
|-----|-------|----------|-----|
| C1 | 100nF C0G | Remote RC filter | /REMOTE_FILT → GND |
| C14 | 100nF C0G | +12V_RAW bypass | /+12V_RAW → GND |
| C15 | 100nF C0G | −12V_RAW bypass | /-12V_RAW → GND |
| C16 | 100µF/25V | +12V_RAW bulk | /+12V_RAW → GND |
| C17 | 100µF/25V | −12V_RAW bulk | /-12V_RAW → GND |
| C18 | 100nF C0G | /+12V bypass after FB1 | /+12V → GND |
| C19 | 100nF C0G | /-12V bypass after FB2 | /-12V → GND |
| C20 | 100µF | V+ board bulk | /V+ → GND |
| C21 | 100µF | V− board bulk | /V- → GND |
| C22 | 100nF C0G | U14 VOUT bypass | /V+ → GND |
| C23 | 100nF C0G | U15 NR pin | /NR_U15 → GND |
| C24 | 10µF X5R | U14 VOUT bulk | /V+ → GND |
| C25 | 10µF X5R | U15 VOUT bulk | /V- → GND |
| C74–C79 | 10µF X5R | V+/V− bulk driver ICs | alternating /V+ and /V- |
| C80 | 10µF | Q1 gate RC timing | Net-(Q1-G) → GND |
| C81 | 22nF C0G | U14 soft-start | /SS_U14 → GND |

---

## Diodes (D)

### ESD Protection — Signal Lines (24 + 1 = 25 diodes)

**D1 (SMBJ15CA):** Bidirectional TVS 15V at remote input. Pin1=/REMOTE_IN, Pin2=GND.

**D2–D25 (PESD5V0S1BL):** ESD protection on all signal inputs/outputs. A=GND, K=signal net.

Per-channel assignment:

| CH | D_HOT_RAW | D_COLD_RAW | D_OUT_HOT | D_OUT_COLD |
|----|-----------|-----------|----------|------------|
| 1 | D8 | D10 | D2 | D9 |
| 2 | D11 | D13 | D3 | D12 |
| 3 | D14 | D16 | D4 | D15 |
| 4 | D17 | D19 | D5 | D18 |
| 5 | D20 | D22 | D6 | D21 |
| 6 | D23 | D25 | D7 | D24 |

> D_HOT/COLD_RAW: at XLR input (before EMI filter)
> D_OUT_HOT/COLD: at output node (before Zobel, after 47Ω series R)

**PESD5V0S1BL Pinout (SOD-323):**

```
  GND ─── A │SOD-323│ K ─── Signal net
```

---

## Connectors (J)

| Ref | Value | Type | Function | Pins |
|-----|-------|------|----------|------|
| J1 | 24V DC | Barrel Jack | Power input | Pin1=/+24V_IN, Pin2=GND |
| J2 | REMOTE 3.5mm IN | KH-PJ-320EA-5P-SMT | Remote input (FreeDSP) | PinT=/REMOTE_IN, PinS=GND |
| J15 | REMOTE 3.5mm OUT | KH-PJ-320EA-5P-SMT | Remote passthrough | PinT=/REMOTE_IN, PinS=GND |
| J3 | XLR_IN_1 | XLR-F 3-pin | Input CH1 | Pin1=GND, Pin2=/CH1_HOT_RAW, Pin3=/CH1_COLD_RAW, PinG=GND |
| J4 | XLR_IN_2 | XLR-F 3-pin | Input CH2 | Pin1=GND, Pin2=/CH2_HOT_RAW, Pin3=/CH2_COLD_RAW, PinG=GND |
| J5 | XLR_IN_3 | XLR-F 3-pin | Input CH3 | Pin1=GND, Pin2=/CH3_HOT_RAW, Pin3=/CH3_COLD_RAW, PinG=GND |
| J6 | XLR_IN_4 | XLR-F 3-pin | Input CH4 | Pin1=GND, Pin2=/CH4_HOT_RAW, Pin3=/CH4_COLD_RAW, PinG=GND |
| J7 | XLR_IN_5 | XLR-F 3-pin | Input CH5 | Pin1=GND, Pin2=/CH5_HOT_RAW, Pin3=/CH5_COLD_RAW, PinG=GND |
| J8 | XLR_IN_6 | XLR-F 3-pin | Input CH6 | Pin1=GND, Pin2=/CH6_HOT_RAW, Pin3=/CH6_COLD_RAW, PinG=GND |
| J9 | XLR3_OUT | XLR-M 3-pin | Output CH1 | Pin1=GND, Pin2=/CH1_OUT_HOT, Pin3=/CH1_OUT_COLD |
| J10 | XLR3_OUT | XLR-M 3-pin | Output CH2 | Pin1=GND, Pin2=/CH2_OUT_HOT, Pin3=/CH2_OUT_COLD |
| J11 | XLR3_OUT | XLR-M 3-pin | Output CH3 | Pin1=GND, Pin2=/CH3_OUT_HOT, Pin3=/CH3_OUT_COLD |
| J12 | XLR3_OUT | XLR-M 3-pin | Output CH4 | Pin1=GND, Pin2=/CH4_OUT_HOT, Pin3=/CH4_OUT_COLD |
| J13 | XLR3_OUT | XLR-M 3-pin | Output CH5 | Pin1=GND, Pin2=/CH5_OUT_HOT, Pin3=/CH5_OUT_COLD |
| J14 | XLR3_OUT | XLR-M 3-pin | Output CH6 | Pin1=GND, Pin2=/CH6_OUT_HOT, Pin3=/CH6_OUT_COLD |

---

## Switches (SW)

| Ref | Value | Type | Function |
|-----|-------|------|----------|
| SW1 | ALWAYS/REMOTE | SW_SPDT | Operating mode EN_CTRL: Pin1=/+12V, Pin2=/EN_CTRL, Pin3=/REMOTE_FILT |
| SW2 | Gain CH1 | SW_DIP_x03 | Gain select CH1 (3-bit) |
| SW3 | Gain CH2 | SW_DIP_x03 | Gain select CH2 |
| SW4 | Gain CH3 | SW_DIP_x03 | Gain select CH3 |
| SW5 | Gain CH4 | SW_DIP_x03 | Gain select CH4 |
| SW6 | Gain CH5 | SW_DIP_x03 | Gain select CH5 |
| SW7 | Gain CH6 | SW_DIP_x03 | Gain select CH6 |

---

## MOSFETs (Q)

All BSS138, N-channel, SOT-23. **Pinout:** Pin 1 = Gate, Pin 2 = Source, Pin 3 = Drain

| Ref | Function | Gate | Source | Drain |
|-----|----------|------|--------|-------|
| Q1 | Master mute MOSFET | Net-(Q1-G) via R106+C80 | GND | /MUTE |
| Q2 | Mute CH1 | Net-(Q2-G) via R108 | GND | /CH1_GAIN_OUT |
| Q3 | Mute CH2 | Net-(Q3-G) via R109 | GND | /CH2_GAIN_OUT |
| Q4 | Mute CH3 | Net-(Q4-G) via R110 | GND | /CH3_GAIN_OUT |
| Q5 | Mute CH4 | Net-(Q5-G) via R111 | GND | /CH4_GAIN_OUT |
| Q6 | Mute CH5 | Net-(Q6-G) via R112 | GND | /CH5_GAIN_OUT |
| Q7 | Mute CH6 | Net-(Q7-G) via R113 | GND | /CH6_GAIN_OUT |
