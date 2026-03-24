# Muting & Remote Control

[← Back to README](../README.md) | [Power Supply](power-supply.md) | [Gain Configuration](gain-configuration.md)

---

## Remote Control

```mermaid
flowchart TD
    J2["J2: KH-PJ-320EA-5P-SMT\n3.5mm Jack — Remote IN"]
    D1["D1: SMBJ15CA\nBidirectional TVS 15V\nESD protection remote"]
    R1["R1: 10kΩ\nSeries resistor"]
    C1["C1: 100nF\nRC low-pass\nRemote signal filtering"]
    SW1["SW1: SPDT\nALWAYS ─── REMOTE\n(Jumper)"]
    R56["R56: 100kΩ\nPullup /V+ → EN_CTRL"]
    R57["R57: 100kΩ\nPulldown EN_CTRL → GND"]
    EN["EN_CTRL\n→ U14.EN + U15.EN"]

    J2 -->|/REMOTE_IN| D1
    D1 -->|/REMOTE_IN| R1
    R1 -->|/REMOTE_FILT| C1
    R1 -->|Center pin| SW1
    SW1 -->|"ALWAYS: direct pullup"| EN
    SW1 -->|"REMOTE: filtered signal"| EN
    R56 --> EN
    R57 --> EN
    EN -->|LDO enable pin| U14["U14 ADP7118"]
    EN -->|LDO enable pin| U15["U15 ADP7182"]

    U14 -->|"/V+ active"| MUTE_LOGIC["Muting Logic\n→ Q1…Q7 BSS138\n→ Audio unmuted"]
    U15 -->|"/V− active"| MUTE_LOGIC
```

**Operation:**

- **SW1 = ALWAYS:** EN_CTRL is HIGH (pullup R56 / pulldown R57) → LDOs always active → board always operational
- **SW1 = REMOTE:** EN_CTRL follows the FreeDSP remote signal (J2) via RC filter → board powers on/off with the DSP
- **D1 (SMBJ15CA):** Protects the remote input against overvoltage up to ±15V (bidirectional)

---

## Components — Remote & Muting

| Ref | Value | Function | Net |
|-----|-------|----------|-----|
| J2 | KH-PJ-320EA-5P-SMT | Remote input | PinT=/REMOTE_IN, PinS=GND |
| J15 | KH-PJ-320EA-5P-SMT | Remote passthrough (OUT) | PinT=/REMOTE_IN, PinS=GND |
| D1 | SMBJ15CA | ESD remote 15V bidi | Pin1=/REMOTE_IN, Pin2=GND |
| R1 | 10kΩ | RC series resistor | /REMOTE_IN → /REMOTE_FILT |
| C1 | 100nF C0G | RC low-pass | /REMOTE_FILT → GND |
| SW1 | SW_SPDT | ALWAYS/REMOTE select | COM=/EN_CTRL, A=/REMOTE_FILT, Pin1=/+12V (ALWAYS) |
| R56 | 100kΩ | Pullup EN_CTRL | /V+ → /EN_CTRL |
| R57 | 100kΩ | Pulldown EN_CTRL | /EN_CTRL → GND |
