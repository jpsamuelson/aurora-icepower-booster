# Placement-Analyse & Plan — Aurora DSP IcePower Booster

## Kurzfassung der Probleme

Nach Auswertung der kompletten Netlist (233 Komponenten, 59 Netze) und dem aktuellen
PCB-Zustand wurden **7 kritische Fehler** in der generierten Platzierung gefunden:

```
Aktuell: 182 auf dem Board, 82 im Fallback-Bereich (y>200)
Nötige Korrekturen: ~50 Bewegungen + 82 Platzierungen
```

---

## 1. Kritische Fehler (Muss korrigiert werden)

### 1.1 Doppeltes Phantom-U13 (TeL5-2422)
| | Position | Footprint |
|---|---|---|
| **Korrekt** (REF** → U13) | x=88.7, y=34.6 | TEL5_DUAL_TRP |
| **Phantom** (falsch) | x=130, y=183 | SOIC-8 (LM4562-Footprint!) |

**Problem**: Der Builder-Script platzierte U13 als SOIC-8 im CH6-Kanal-Strip. Das DC/DC-Konverter-IC kann nicht in einem op-amp footprint sitzen.  
**Fix**: SOIC-8 U13 bei (130,183) **entfernen** / als unverwendet markieren.

### 1.2 Falsche Referenzen REF** für Power-ICs
| PCB-Ref | Footprint | Aktuelle Pos | Gewünschte Ref |
|---|---|---|---|
| REF** | TEL5_DUAL_TRP | x=88.7, y=34.6 | **U13** |
| REF** | SOIC127P600X175-9N | x=91.8, y=41.3 | **U14** |

**Fix**: Reference-Properties in den Footprints korrigieren.

### 1.3 U7 (CH1 Driver) an falscher Position
- **Aktuell**: x=75, y=183 (Rx-Position in CH6-Row)
- **Netlist**: U7 = CH1 Driver LM4562 (hängt an /CH1_GAIN_OUT)
- **Soll**: x=132, y=53 (Driver-Position, CH1-Strip)

### 1.4 U1 (CH1 Dual Rx/Gain LM4562) fehlt komplett
- Kein U1-SOIC-8 im CH1-Strip vorhanden
- Im CH1-Strip bei y=48-58 fehlt das Haupt-IC
- **Soll**: x=77, y=53 (CH1-Strip, Rx-Position)

### 1.5 Op-Amp Entkoppel-Kondensatoren C14–C24 in falscher Zone
Diese 11 Kondensatoren (100nF auf V+/V-) liegen im Power-Bereich (y=10–33),
gehören aber zu den **Driver-Amps U7–U12** und müssen direkt bei diesen sitzen:

| Kondensator | Net | Aktuell | Soll (bei welchem IC) |
|---|---|---|---|
| C13 | V+ | Fallback (5, 205) | x=136, y=49 (bei U7/CH1) |
| C14 | V- | x=107, y=10 | x=136, y=57 (bei U7/CH1) |
| C15 | V+ | x=107, y=30 | x=136, y=75 (bei U8/CH2) |
| C16 | V- | x=100, y=13 | x=136, y=83 (bei U8/CH2) |
| C17 | V+ | x=100, y=27 | x=136, y=101 (bei U9/CH3) |
| C18 | V- | x=130, y=9 | x=136, y=109 (bei U9/CH3) |
| C19 | V+ | x=130, y=17 | x=136, y=127 (bei U10/CH4) |
| C20 | V- | x=155, y=9 | x=136, y=135 (bei U10/CH4) |
| C21 | V+ | x=155, y=17 | x=136, y=153 (bei U11/CH5) |
| C22 | V- | x=130, y=33 | x=136, y=161 (bei U11/CH5) |
| C23 | V+ | x=135, y=33 | x=136, y=179 (bei U12/CH6) |
| C24 | V- | x=140, y=33 | x=136, y=187 (bei U12/CH6) |

### 1.6 Power-Entkoppel-Kondensatoren C26, C35, C36 in Kanal-Strips
Diese Kondensatoren gehören auf die **rohen DC/DC-Ausgangsschienen** (±12V vor LDO):

| Kondensator | Net | Aktuell | Soll |
|---|---|---|---|
| C26 | -12V/GND | x=135, y=58 (CH1-Strip!) | x=118, y=27 (Power-Zone bei U15/FB2) |
| C35 | +12V/GND | x=135, y=178 (CH6-Strip!) | x=118, y=13 (Power-Zone bei U14/FB1) |
| C36 | -12V/GND | x=135, y=188 (CH6-Strip!) | x=122, y=27 (Power-Zone) |

### 1.7 C81 (SS_U14 Soft-Start) an Position (0,0)
- Muss direkt am ADP7118 SS-Pin sitzen
- **Fix**: x=88, y=36 (near REF**/U14)

---

## 2. Power Zone — Fertige Positionen

```
Board Top Edge (y=0)
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  J2(30.5,5.1)  SW1(53.9,6.8)           J1(70.9,10.8)                           │
│  [Remote 3.5]  [ALWAYS/REMOTE]          [+24V Barrel]                           │
│                                                                                  │
│  R106(46,17)                            FB1(112,13)   C35→(118,13)  C77→(122,13)│
│  C81→(88,36)   U13**(88.7,34.6)         U14**(91.8,28)              C25(145,33) │
│  D1(55,20)                             FB2(112,27)   C36→(118,27)  C78→(122,27) │
│  C80(46,25.5)  R56(56,26)  R57→KANAL   U15(155,27)                 C79→(48,35) │
│  Q1(50,33)     R79→(48,36) R80→(52,36)                                          │
│  R1→CH1  R2→CH1                         C26→(118,27) C77→(122,13)              │
│  C82→(152,32) [near U15 NR]                                                     │
└──────────────────────────────────────────────────────────────────────────────────┘ y=42
```

> **(88.7,34.6) = REF** → Referenz korrigieren zu U13**  
> **(91.8,28) = REF** → zu U14 + Y von 41.3 auf 28 anpassen, da U14 aktuell am Rand**

Power Zone Komponenten (Endpositionen):
| Ref | Funktion | X | Y | Änderung |
|---|---|---|---|---|
| J1 | 24V Barrel | 70.9 | 10.8 | FIXED |
| J2 | Remote 3.5mm | 30.5 | 5.1 | FIXED |
| SW1 | ALWAYS/REMOTE | 53.9 | 6.8 | FIXED |
| U13 | TEL5-2422 | 88.7 | 34.6 | Ref REF**→U13 |
| U14 | ADP7118 LDO | 91.8 | 28.0 | Ref REF**→U14, Y=41.3→28 |
| U15 | ADP7182 LDO | 155.0 | 27.0 | ✓ OK |
| D1 | SMBJ15CA TVS | 55.0 | 20.0 | ✓ OK (Eingangsschutz 24V) |
| Q1 | BSS138 FET | 50.0 | 33.0 | ✓ OK |
| FB1 | Ferrit +12V | 112.0 | 13.0 | ✓ OK |
| FB2 | Ferrit -12V | 112.0 | 27.0 | ✓ OK |
| C80 | 10µF Remote-Filt | 46.0 | 25.5 | ✓ OK |
| C81 | 22nF SS_U14 | 0.0 → **88.0** | 0.0 → **36.0** | BEWEGEN |
| C82 | NR_U15 | ??? | ??? | FEHLT — bei x=152, y=32 |
| C25 | +12V 100nF | 145.0 | 33.0 | ✓ OK |
| C26 | -12V 100nF | 135→**118** | 58→**27** | BEWEGEN |
| C35 | +12V 100nF | 135→**118** | 178→**13** | BEWEGEN |
| C36 | -12V 100nF | 135→**122** | 188→**27** | BEWEGEN |
| C77 | +12V 100nF | Fallback→**122** | 205→**13** | PLATZIEREN |
| C78 | -12V 100nF | Fallback→**126** | 205→**27** | PLATZIEREN |
| C79 | 22nF REMOTE_FILT | Fallback→**48** | 205→**35** | PLATZIEREN |
| R56 | GND (enable) | 56.0 | 26.0 | ✓ OK |
| R79 | EN_CTRL GND | Fallback→**44** | 229→**38** | PLATZIEREN |
| R80 | EN_CTRL GND | Fallback→**50** | 229→**38** | PLATZIEREN |
| R105 | REMOTE filter | Fallback→**38** | 205→**8** | PLATZIEREN near J2 |
| R106 | 10k (enable) | 46.0 | 17.0 | ✓ OK |
| C37 | V+ 100nF (bulk) | Fallback→**158** | 205→**22** | PLATZIEREN near U15 |
| C38 | V- 100nF (bulk) | 148→**158** | 56→**28** | BEWEGEN |
| C74 | GND bypass | Fallback→**163** | 205→**15** | PLATZIEREN |
| C75 | GND bypass | Fallback→**163** | 213→**22** | PLATZIEREN |
| C76 | GND bypass | Fallback→**163** | 213→**29** | PLATZIEREN |

---

## 3. Kanal-Strips — Layout-Konzept

```
Signalfluss links → rechts:
                                                                   Richtung
     x= 12.6  28   40   50   58   65   77   82  97  113  132  136  148  155  162.3
          │    │    │    │    │    │    │    │   │   │    │    │    │    │    │
J3/J9 XLR─┤ TVS ┤DCblk┤EMI  ┤ Rin ┤ Rxamp┤dec│gain│mute│ drv ┤dec ┤ Rout┤ TVS ┤XLR
 y_ch │ fix    │ D   │  C  │ C   │ R   │    U  C │ SW │ Q  │    U  C │  R  │ D  │ fix
      │        │ SoD │1206 │0805 │0805 │   SOIC  │DIP │SOT │   SOIC  │0805 │SoD │
```

**Kanal Y-Zentren** (abgeleitet von XLR-Positionen):
| Kanal | XLR-Y (oben) | Strip-Y-Zentrum | XLR-Y (unten) |
|---|---|---|---|
| CH1 | J3=44.5 / J9=44.5 | **53** | J4=72.1 |
| CH2 | J4=72.1 / J10=72.1 | **79** | J5=99.8 |
| CH3 | J5=99.8 / J11=99.8 | **105** | J6=127.6 |
| CH4 | J6=127.6 / J12=127.5 | **131** | J7=155.4 |
| CH5 | J7=155.4 / J13=155.4 | **157** | J8=183.2 |
| CH6 | J8=183.2 / J14=183.1 | **183** | — |

---

## 4. Vollständige Positionstabelle — alle 6 Kanäle

### Kanal-Nomenklatur
Jeder Kanal hat folgende Signalnetze:
- `CHx_HOT_RAW`, `CHx_COLD_RAW` → direkt am XLR-Pin (nach J3-J8)
- `CHx_HOT_IN`, `CHx_COLD_IN` → nach DC-Blocking
- `CHx_RX_OUT`, `CHx_SUMNODE`, `CHx_GAIN_OUT` → um den Rx/Gain Op-Amp
- `CHx_OUT_HOT` → nach dem Driver, zu J9-J14

### CH1 (y_center=53)

| Ref | Net | Funktion | X | Y | Rot | Status |
|---|---|---|---|---|---|---|
| D1 | CH1_HOT_RAW | Input TVS HOT | 28 | 50 | 0 | BEWEGEN von (55,20) |
| D2 | CH1_COLD_RAW | Input TVS COLD | 28 | 56 | 180 | ✓ korrekt (34,49.5) → X=28 |
| D14 | CH1_HOT_RAW | Input TVS 2 | 28 | 50 | 180 | Prüfen: aktuell (155,49.5) |
| C39 | CH1_HOT_IN | DC Block HOT | 42 | 50 | 90 | BEWEGEN von (148,82) |
| C40 | CH1_COLD_IN | DC Block COLD | 42 | 56 | 90 | BEWEGEN von (148,108) |
| C62 | GND | EMI Filter HOT | 52 | 50 | 90 | ✓ (49,49.5) — NEIN, C62=GND nur |
| C63 | GND | EMI Filter COLD | 52 | 56 | 90 | ✓ (49,56.5) |
| C50 | CH6_COLD_IN! | DC Block CH6 | FALSCH pos | — | — | Netz-Fehler, zu CH6 |
| R1 | CH1_HOT_IN | Input R HOT 1 | 63 | 49 | 90 | BEWEGEN von (44,28) |
| R2 | CH1_HOT_IN | Input R HOT 2 | 63 | 51 | 90 | BEWEGEN von (44,33) |
| R3 | CH1_COLD_IN | Input R COLD | 63 | 56 | 90 | PLATZIEREN (Fallback) |
| R4 | GND | Com Mode R | 63 | 54 | 90 | PLATZIEREN (Fallback) |
| U1 | CH1_HOT_IN etc | LM4562 Rx+Gain | 77 | 53 | 0 | FEHLT — muss hinzugefügt |
| C1 | V+ | Dekopplung V+ | 82 | 49 | 0 | ✓ (80,48) — X 80→82 |
| C2 | V- | Dekopplung V- | 82 | 57 | 0 | ✓ (80,58) — X 80→82 |
| R5 | CH1_RX_OUT+SUM | Sumnode R | 70 | 49 | 90 | PLATZIEREN (Fallback) |
| R6 | CH1_GAIN_OUT+SUM | Gain FB R | 70 | 56 | 90 | PLATZIEREN (Fallback) |
| R7 | CH1_SUMNODE | Sumnode R | 67 | 52 | 90 | PLATZIEREN (Fallback) |
| R8 | CH1_SUMNODE | Sumnode R | 67 | 54 | 90 | PLATZIEREN (Fallback) |
| R9 | CH1_SUMNODE | Sumnode R | 67 | 56 | 90 | PLATZIEREN (Fallback) |
| SW1* | CH1_RX_OUT | Gain-Switch CH1 | 97 | 53 | 0 | ⚠ KONFLIKT mit FIXED SW1 |
| Q2 | — | Mute FET | 113 | 53 | 0 | ✓ (112,53) |
| U7 | CH1_GAIN_OUT | LM4562 Driver | 132 | 53 | 0 | BEWEGEN von (75,183) |
| C13 | V+ | Driver Dekopplung + | 136 | 49 | 0 | PLATZIEREN (Fallback) |
| C14 | V- | Driver Dekopplung - | 136 | 57 | 0 | BEWEGEN von (107,10) |
| R10 | CH1_GAIN_OUT | Gain FB R | 136 | 51 | 90 | PLATZIEREN (Fallback) |
| R12 | CH1_OUT_HOT | Output Serie R | 148 | 50 | 90 | PLATZIEREN (Fallback) |
| R81 | CH1_OUT_HOT | Output Serie R 2 | 148 | 56 | 90 | PLATZIEREN (Fallback) |
| D13 | CH1_OUT_HOT | Output TVS | 155 | 50 | 0 | ✓ (155,49.5) |
| R13 | CH1_HOT_RAW | EMI/Serie R | 33 | 50 | 90 | PLATZIEREN (Fallback) |
| R82 | CH1_HOT_RAW | EMI/Serie R 2 | 33 | 52 | 90 | PLATZIEREN (Fallback) |
| R93 | CH1_HOT_RAW | EMI/Serie R 3 | 33 | 50 | 0 | PLATZIEREN (Fallback) |
| R94 | CH1_COLD_RAW | EMI Serie COLD | 33 | 56 | 90 | PLATZIEREN (Fallback) |

> ⚠ **SW1 Konflikt**: Der Netlist-Knoten SW1 (CH1_RX_OUT) müsste kanalnahe platziert sein.
> Da SW1 (EG1224 SPDT) vom User fixiert ist, wird angenommen:
> - Der **EG1224 SPDT bei (53.9, 6.8)** ist tatsächlich der **ALWAYS/REMOTE Schalter** 
>   (entspricht Netlist SW7 → EN_CTRL/REMOTE_FILT)
> - Der **CH1 Gain-DIP** entspricht im PCB dem DIP an x=97, y=53 → im PCB ist das **SW2**
> - Es gibt eine Verschiebung um 1: Netlist-SW1=PCB-SW2, Netlist-SW7=PCB-SW1(EG1224)

### CH2 (y_center=79) — Hauptsächlich korrekt

| Ref | Net | Funktion | X | Y | Rot | Status |
|---|---|---|---|---|---|---|
| D3 | CH2_HOT_RAW | Input TVS HOT | 28 | 76 | 0 | Prüfen (34,75.5) |
| D4 | CH2_COLD_RAW | Input TVS COLD | 28 | 82 | 180 | (34,75.5) — falsch? |
| C41 | CH2_HOT_IN | DC Block HOT | 42 | 76 | 90 | Prüfen aktuell |
| C42 | CH2_COLD_IN | DC Block COLD | 42 | 82 | 90 | (148,134) → BEWEGEN |
| R14 | CH2_HOT_IN | Input R HOT 1 | 63 | 75 | 90 | ✓ (65,48) — aber y=48 nicht 75! |
| R15 | CH2_HOT_IN | Input R HOT 2 | 63 | 77 | 90 | ✓ aktuell prüfen |
| R16 | CH2_COLD_IN | Input R COLD | 63 | 82 | 90 | ✓ (65,55.5) |
| R17 | GND | Com Mode R | 63 | 79 | 90 | ✓ (65,58) |
| U2 | CH2_HOT_IN etc | LM4562 Rx+Gain | 77 | 79 | 0 | ✓ (75,53) — y=53 statt 79! |
| C3 | V+ | Dekopplung V+ | 82 | 75 | 0 | ✓ (80,74) |
| C4 | V- | Dekopplung V- | 82 | 83 | 0 | ✓ (80,84) |
| R18 | CH2_RX+SUMNODE | Sumnode R | 70 | 75 | 90 | PLATZIEREN (Fallback) |
| R19 | CH2_GAIN+SUMNODE | Gain FB R | 70 | 82 | 90 | PLATZIEREN (Fallback) |
| R20 | CH2_SUMNODE | Sumnode R | 67 | 77 | 90 | ✓ (65,74) |
| R21 | CH2_SUMNODE | Sumnode R | 67 | 79 | 90 | ✓ (65,76.5) |
| R22 | CH2_SUMNODE | Sumnode R | 67 | 81 | 90 | ✓ (65,81.5) |
| R23 | CH2_GAIN_OUT | Gain FB R | 136 | 75 | 90 | ✓ (65,84) — x=65 statt 136! |
| SW2 | CH2_RX_OUT | Gain-Switch CH2 | 97 | 79 | 0 | ✓ (96,53) — y Versatz |
| Q3 | — | Mute FET | 113 | 79 | 0 | ✓ (112,79) |
| U8 | CH2_GAIN_OUT | LM4562 Driver | 132 | 79 | 0 | ✓ (130,53) — y Versatz |
| C15 | V+ | Driver Dekopplung + | 136 | 75 | 0 | BEWEGEN von (107,30) |
| C16 | V- | Driver Dekopplung - | 136 | 83 | 0 | BEWEGEN von (100,13) |
| R25 | CH2_OUT_HOT | Output Serie R | 148 | 76 | 90 | PLATZIEREN (Fallback) |
| R83 | CH2_OUT_HOT | Output Serie R 2 | 148 | 82 | 90 | PLATZIEREN (Fallback) |
| D15 | CH2_OUT_HOT | Output TVS | 155 | 76 | 0 | ✓ (155,56.5) — y falsch? |
| R26 | CH2_HOT_RAW | EMI R | 33 | 76 | 90 | ✓ (65,100) — position falsch |
| R84 | CH2_HOT_RAW | EMI R 2 | 33 | 78 | 0 | PLATZIEREN (Fallback) |
| R95 | CH2_HOT_RAW | EMI R 3 | 33 | 76 | 0 | PLATZIEREN (Fallback) |
| R96 | CH2_COLD_RAW | EMI COLD | 33 | 82 | 90 | PLATZIEREN (Fallback) |

> **Beobachtung CH2**: R14, R15, R16, R17 sind korrekt platziert bei x=65, aber in CH1-Y-Row (48-58 statt 75-82). Die ICs U2, U8 sind auch in CH1-Row (y=53). **Die ganze CH2-Gruppe wurde systematisch um einen Strip nach oben verschoben (y=53 statt y=79)**.

### Zusammenfassung: Systematischer Y-Versatz

**Kernproblem**: Der Builder-Script hat alle Kanal-Komponenten von CH2-CH6 einen Strip zu hoch platziert:
```
CH2 Bauteile → in CH1-Strip (y=53 statt 79)
CH3 Bauteile → in CH2-Strip (y=79 statt 105)
CH4 Bauteile → in CH3-Strip (y=105 statt 131)
CH5 Bauteile → in CH4-Strip (y=131 statt 157)
CH6 Bauteile → in CH5-Strip (y=157 statt 183)
```
CH1 Bauteile (U1, U7, R1-R9, SW für CH1) → nicht korrekt platziert oder im Power-Bereich.

**Der gesamte Kanal-Bereich ist um eine Reihe nach oben verschoben.**

Dies bedeutet:
- Die ICs U2-U6 sind bei y=53/79/105/131/157 statt bei y=79/105/131/157/183
- Die ICs U8-U12 sind bei y=53/79/105/131/157 statt bei y=79/105/131/157/183
- J3 (XLR CH1 Input) bei y=44.5 hat KEINE zugehörigen ICs in dieser Y-Range
- In CH6-Row (y=183) sind U7 (CH1 Driver!) und U13 (TEL5-2422!) placiert — beide falsch

---

## 5. Fallback-Komponenten: Zielposition

### Kondensatoren (14 Stück)

| Ref | Net | Funktion | Ziel-X | Ziel-Y | Ziel-Channel |
|---|---|---|---|---|---|
| C13 | V+ | Driver Dek. | 136 | 49 | CH1 (bei U7) |
| C37 | V+ | Bulk V+ | 158 | 22 | Power Zone |
| C44 | CH3_COLD_IN | DC Block | 42 | 107 | CH3 |
| C45 | CH4_HOT_IN | DC Block | 42 | 127 | CH4 |
| C46 | CH4_COLD_IN | DC Block | 42 | 133 | CH4 |
| C47 | CH5_HOT_IN | DC Block | 42 | 153 | CH5 |
| C48 | CH5_COLD_IN | DC Block | 42 | 159 | CH5 |
| C49 | CH6_HOT_IN | DC Block | 42 | 179 | CH6 |
| C74 | GND | Bypass | 163 | 15 | Power Zone |
| C75 | GND | Bypass | 163 | 22 | Power Zone |
| C76 | GND | Bypass | 163 | 29 | Power Zone |
| C77 | +12V/GND | +12V Dek. | 122 | 13 | Power Zone |
| C78 | -12V/GND | -12V Dek. | 122 | 27 | Power Zone |
| C79 | REMOTE_FILT | RC-Filter | 48 | 35 | Power Zone |

### Widerstände (68 Stück) — nach Kanal und Funktion

#### Power-Zone (7 Widerstände)
| Ref | Net | Funktion | Ziel-X | Ziel-Y |
|---|---|---|---|---|
| R79 | EN_CTRL | Pulldown | 44 | 38 |
| R80 | EN_CTRL | Pulldown | 50 | 38 |
| R105 | REMOTE_IN+FILT | RC R | 38 | 8 |
| R101 | CH5_HOT_RAW | EMI R | 28 | 153 |
| R102 | CH5_COLD_RAW | EMI R | 28 | 159 |
| R103 | CH6_HOT_RAW | EMI R | 28 | 179 |
| R104 | CH6_COLD_RAW | EMI R | 28 | 185 |

#### CH1-Strip (y=53) — 12 Widerstände
| Ref | Net | Funktion | Ziel-X | Ziel-Y |
|---|---|---|---|---|
| R3 | CH1_COLD_IN | Input R Cold | 63 | 56 |
| R4 | GND | Com.Mode R | 63 | 53 |
| R5 | CH1_RX+SUM | Sumnode | 70 | 49 |
| R6 | CH1_GAIN+SUM | Gain FB | 70 | 57 |
| R7 | CH1_SUMNODE | Sumnode | 67 | 51 |
| R8 | CH1_SUMNODE | Sumnode | 67 | 53 |
| R9 | CH1_SUMNODE | Sumnode | 67 | 55 |
| R10 | CH1_GAIN_OUT | Driver FB | 136 | 51 |
| R12 | CH1_OUT_HOT | Output Serie | 148 | 50 |
| R13 | CH1_HOT_RAW | EMI R HOT | 28 | 50 |
| R81 | CH1_OUT_HOT | Output Serie 2 | 148 | 56 |
| R82 | CH1_HOT_RAW | EMI R HOT 2 | 28 | 52 |
| R93 | CH1_HOT_RAW | EMI R HOT 3 | 28 | 48 |
| R94 | CH1_COLD_RAW | EMI R COLD | 28 | 56 |

#### CH2-Strip (y=79) — aktuell bei y=53, R18/R19/R25/R83/R84/R95/R96 fehlen
| Ref | Net | Ziel-X | Ziel-Y |
|---|---|---|---|
| R18 | CH2_RX+SUM | 70 | 75 |
| R19 | CH2_GAIN+SUM | 70 | 83 |
| R25 | CH2_OUT_HOT | 148 | 76 |
| R83 | CH2_OUT_HOT | 148 | 82 |
| R84 | CH2_HOT_RAW | 28 | 78 |
| R95 | CH2_HOT_RAW | 28 | 76 |
| R96 | CH2_COLD_RAW | 28 | 82 |

#### CH3-Strip (y=105)
| Ref | Net | Ziel-X | Ziel-Y |
|---|---|---|---|
| R30 | GND | 63 | 105 |
| R31 | CH3_RX+SUM | 70 | 101 |
| R36 | CH3_GAIN_OUT | 136 | 102 |
| R37* | (nicht in Netlist!) | — | — |
| R85 | CH3_OUT_HOT | 148 | 102 |
| R86 | CH3_HOT_RAW | 28 | 104 |
| R97 | CH3_HOT_RAW | 28 | 102 |
| R98 | CH3_COLD_RAW | 28 | 108 |

#### CH4-Strip (y=131)
| Ref | Net | Ziel-X | Ziel-Y |
|---|---|---|---|
| R42 | CH4_COLD_IN | 63 | 135 |
| R43 | GND | 63 | 131 |
| R48 | CH4_SUMNODE | 67 | 131 |
| R49 | CH4_GAIN_OUT | 136 | 128 |
| R87 | CH4_OUT_HOT | 148 | 128 |
| R99 | CH4_HOT_RAW | 28 | 130 |
| R100 | CH4_COLD_RAW | 28 | 136 |

#### CH5-Strip (y=157)
| Ref | Net | Ziel-X | Ziel-Y |
|---|---|---|---|
| R60 | CH5_SUMNODE | 67 | 157 |
| R61 | CH5_SUMNODE | 67 | 159 |
| R62 | CH5_GAIN_OUT | 136 | 154 |
| R65 | CH5_HOT_RAW | 33 | 154 |
| R66 | CH6_HOT_IN! | 63 | 181 |
| R67 | CH6_HOT_IN! | 63 | 179 |
| R68 | CH6_COLD_IN | 63 | 187 |
| R69 | GND | 63 | 183 |
| R89 | CH5_OUT_HOT | 148 | 154 |
| R90 | CH5_HOT_RAW | 28 | 155 |

#### CH6-Strip (y=183)
| Ref | Net | Ziel-X | Ziel-Y |
|---|---|---|---|
| R71 | CH6_GAIN+SUM | 70 | 187 |
| R72 | CH6_SUMNODE | 67 | 181 |
| R73 | CH6_SUMNODE | 67 | 183 |
| R74 | CH6_SUMNODE | 67 | 185 |
| R75 | CH6_GAIN_OUT | 136 | 180 |
| R77 | CH6_OUT_HOT | 148 | 180 |
| R78 | CH6_HOT_RAW | 28 | 181 |
| R91 | CH6_OUT_HOT | 148 | 186 |
| R92 | CH6_HOT_RAW | 28 | 183 |
| R77 | CH6_OUT_HOT | 148 | 180 |

#### Unklar / nicht in Netlist (Phantom-Komponenten)
| Ref | Problem |
|---|---|
| R11 | Nicht in Netlist — Phantom |
| R24 | Nicht in Netlist — Phantom |
| R37 | Nicht in Netlist — Phantom |
| R63 | Nicht in Netlist — Phantom |
| R107-R113 | Nicht in Netlist — Phantoms |

---

## 6. Bereits platziere Komponenten: Prüfergebnis

### Korrekt platziert ✓
- J3-J8 (XLR Input), J9-J14 (XLR Output): x=12.6/162.3 ✓ FIXED
- Q2-Q7 (Mute FETs) bei x=112, y=53/79/105/131/157/183 ✓
- SW2-SW7 (Gain-DIP) bei x=96, y=53/79/105/131/157/183 ✓ (aber SW7 korrekt NEU: ALWAYS/REMOTE bei y=183 ist fragwürdig — sollte zu Power Zone)
- D2-D12 (Input TVS SOD-323) bei x=34 ✓ — aber y-Positionen sind um 1 Strip versetzt!
- D13, D15, D17, D19, D21, D23 (Output TVS) bei x=155 ✓
- U2-U6 (Rx+Gain LM4562): OK für CH2-CH6, aber y-Positionen 1 Strip zu hoch  
- U8-U12 (Driver LM4562): OK für CH2-CH6, aber y-Positionen 1 Strip zu hoch
- C1-C12 (V+/V- Dek. für Rx-Amps) bei x=80 ✓ (aber y-Positionen 1 Strip zu hoch)

### Problematisch — Y-Offset
Alle folgenden Komponenten sind korrekt im Kanal-Strip **aber um 1 Strip nach oben verschoben**:
- R14-R17, U2, SW2, Q2, U8 sitzen bei y=48-58 (CH1-Strip) statt y=75-83 (CH2-Strip)
- R20-R23, U3, SW3, Q3, U9 sitzen bei y=74-84 (CH2-Strip) statt y=101-109 (CH3-Strip)
- usw.

---

## 7. Empfehlung: Vorgehen

### Option A — Kompletter Rebuild mit korrekter Netlist-basierter Platzierung (empfohlen)
1. Neues Placement-Script das **Kanal-Zugehörigkeit aus Netznamen ableitet** (CHx_...)
2. Jede Komponente an korrekte x+y-Position basierend auf ihrer Funktion im Signalfluss
3. Power-Zone separat behandeln basierend auf Power-Netzen (+12V, -12V, EN_CTRL)

**Vorteile**: Sauber, korrekt, erweiterbar  
**Nachteil**: Aufwendiger Rebuild (~3 Stunden Arbeit)

### Option B — Gezielte Korrekturen des aktuellen PCB
1. Y-Offset korrigieren (alle Kanal-Komponenten um 26mm nach unten verschieben für CH2-CH6)
2. Fehlende CH1-Komponenten im CH1-Strip platzieren
3. Power-Zone korrigieren (C14-C24 bewegen, C26/C35/C36 bewegen)
4. 82 Fallback-Komponenten platzieren

**Vorteile**: Schneller (nutzt vorhandene Platzierung als Basis)  
**Nachteil**: Fehleranfällig, viele Einzelkorrekturen

### Entscheidung Vorschlag:
**Option B**, da die Basis-Infrastruktur (Footprint-Bibliothek, DRU, Netklassen) bereits korrekt ist, und die y-Offset-Korrektur durch ein einfaches Script umsetzbar ist.

---

## 8. Fehler-Übersicht (bekannte Schaltplan-Anomalien)

| Anomalie | Beschreibung | Auswirkung |
|---|---|---|
| C39-C50 nur 1 Net-Pin | DC-Blocking Caps haben nur Pin 2 im Netlist — Pin 1 fehlt | Kein komplettes Netz für Routing |
| C51-C76 nur GND | EMI Filter Caps haben nur 1 GND-Verbindung sichtbar | Vermutlich ERC-Fehler im Schaltplan |
| D1 in Power-Zone | D1 hängt an CH1_HOT_RAW aber sitzt bei x=55,y=20 | Möglicherweise falsche Referenz-Zuordnung |
| R57 in Power-Zone | R57 verbindet CH5_RX+SUMNODE, liegt aber bei x=56,y=30 (Power-Zone) | Falsche Position |
| SW1/SW7 Tausch | SW1(EG1224 SPDT) hängt an CH1_RX_OUT in Netlist, logisch aber ALWAYS/REMOTE | Reference-Collision, User-fixed |
| C27-C34 Phantome | 8 Kondensatoren im PCB (bei x=135) die nicht im Netlist existieren | Können entfernt werden |
| U13 Doppelt | SOIC-8 U13 bei (130,183) ist Phantom — echter U13 (TEL5) bei (88.7,34.6) | Phantom muss entfernt werden |

> Diese Anomalien könnten vom ursprünglichen ERC-Report bekannt sein (aurora-dsp-icepower-booster-erc.rpt).
> **Empfehlung**: ERC-Bericht prüfen und Schaltplan bereinigen bevor PCB final fertiggestellt wird.
