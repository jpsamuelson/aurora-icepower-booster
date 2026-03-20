#!/usr/bin/env python3
"""
Aurora DSP ICEpower Booster — PCB Builder v3
Netlist-driven placement: every component placed based on its schematic connections.

Key fixes over v2:
- Correct U numbering: U1-U6 = Rx+Gain ICs, U7-U12 = Driver ICs, U13=TEL5, U14=ADP7118, U15=ADP7182
- Correct SW numbering: SW1-SW6 = DIP gain switches per channel, SW7 = ALWAYS/REMOTE (PCB "SW1")
- Correct J numbering: J1-J6 = XLR inputs, J7-J12 = XLR outputs, J13 = barrel, J14 = remote
- All channel passives mapped by net name patterns to correct channel strip
- FIXED positions for all connectors (J1-J14) and mode switch (SW7) per user request

NOTE about reference mapping vs PCB labels:
  PCB "J1" (barrel jack) → Netlist J13  (fixed at same physical position)
  PCB "J2" (remote)      → Netlist J14
  PCB "J3-J8" (XLR in)  → Netlist J1-J6
  PCB "J9-J14" (XLR out) → Netlist J7-J12
  PCB "SW1" (EG1224 SPDT)→ Netlist SW7  (fixed at same physical position)
  PCB "SW2-SW7" (DIP)    → Netlist SW1-SW6
All PHYSICAL POSITIONS are unchanged (user-fixed).
"""
import re
import uuid as uuid_mod

PROJECT  = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster'
NETLIST  = PROJECT + '.net'   # Use current KiCad netlist (not old XML)
OUT_PCB  = PROJECT + '.kicad_pcb'
PROJ_DIR = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster'

# Footprint overrides: component ref → force specific template ID
# Needed when netlist footprint name differs from the PCB/library footprint name
FOOTPRINT_OVERRIDE = {
    # ALWAYS/REMOTE switch: netlist=PinHeader, PCB has EG1224 SPDT (user placed)
    'SW7': 'Button_Switch_SMD:SW_E-Switch_EG1224_SPDT_Angled',
    # XLR connector name mismatch: netlist uses short names, PCB uses full names
    'J1':  'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal',
    'J2':  'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal',
    'J3':  'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal',
    'J4':  'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal',
    'J5':  'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal',
    'J6':  'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal',
    'J7':  'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal',
    'J8':  'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal',
    'J9':  'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal',
    'J10': 'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal',
    'J11': 'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal',
    'J12': 'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal',
    # TEL5-2422: netlist uses DCDC library name, PCB has custom project footprint
    'U13': 'project:TEL5_DUAL_TRP',
}

# Extra footprint files (project-specific, not in PCB templates)
KICAD_FP = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
EXTRA_FOOTPRINTS = {
    'project:TEL5_DUAL_TRP':
        PROJ_DIR + '/footprints.pretty/TEL5_DUAL_TRP.kicad_mod',
    'project:SOIC127P600X175-9N':
        PROJ_DIR + '/footprints.pretty/SOIC127P600X175-9N.kicad_mod',
    'Capacitor_SMD:C_0402_1005Metric':
        KICAD_FP + '/Capacitor_SMD.pretty/C_0402_1005Metric.kicad_mod',
    'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical':
        KICAD_FP + '/Connector_PinHeader_2.54mm.pretty/PinHeader_1x03_P2.54mm_Vertical.kicad_mod',
    # XLR fallback in case git HEAD PCB doesn't have them
    'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal':
        KICAD_FP + '/Connector_Audio.pretty/Jack_XLR_Neutrik_NC3FBH2_Horizontal.kicad_mod',
    'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal':
        KICAD_FP + '/Connector_Audio.pretty/Jack_XLR_Neutrik_NC3MBH_Horizontal.kicad_mod',
}

# ─────────────────────────────────────────────────────────────────────
# STEP 1 — Parse netlist
# ─────────────────────────────────────────────────────────────────────
def parse_netlist(path):
    with open(path) as f:
        text = f.read()
    comps = {}
    idx = 0
    while True:
        start = text.find('(comp ', idx)
        if start == -1:
            break
        depth = 0
        end = start
        for i, ch in enumerate(text[start:]):
            if ch == '(':   depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    end = start + i + 1
                    break
        block = text[start:end]
        ref_m = re.search(r'\(ref\s+"([^"]+)"\)', block)
        if not ref_m:
            idx = start + 1
            continue
        ref   = ref_m.group(1)
        val_m = re.search(r'\(value\s+"([^"]+)"\)', block)
        fp_m  = re.search(r'\(footprint\s+"([^"]+)"\)', block)
        comps[ref] = {
            'ref':        ref,
            'value':      val_m.group(1) if val_m else '',
            'footprint':  fp_m.group(1)  if fp_m  else '',
            'pins':       {}
        }
        idx = start + 1

    # Parse nets
    nets_start = text.find('\n  (nets\n')
    if nets_start < 0:
        nets_start = text.find('\n(nets\n')
    current_net = ''
    if nets_start >= 0:
        for line in text[nets_start:].split('\n'):
            nm = re.match(r'\s*\(net\s+\(code\s+"?\d+"?\)\s+\(name\s+"([^"]*)"\)', line)
            if nm:
                current_net = nm.group(1)
            node = re.match(r'\s*\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', line)
            if node and current_net:
                r, p = node.group(1), node.group(2)
                if r in comps:
                    comps[r]['pins'][p] = current_net
    print(f"Netlist: {len(comps)} components")
    return comps

# ─────────────────────────────────────────────────────────────────────
# STEP 2 — Extract footprint templates
# ─────────────────────────────────────────────────────────────────────
def extract_footprint_block(content, start):
    depth = 0
    for j, ch in enumerate(content[start:]):
        if ch == '(':   depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return content[start:start + j + 1]
    return content[start:]

def extract_footprint_templates(pcb_path):
    with open(pcb_path) as f:
        content = f.read()
    templates = {}
    for m in re.finditer(r'\(footprint\s+"', content):
        block = extract_footprint_block(content, m.start())
        fp_m  = re.match(r'\(footprint\s+"([^"]+)"', block)
        if not fp_m:
            continue
        fp_id = fp_m.group(1)
        if fp_id not in templates:
            templates[fp_id] = block

    # Load extra project footprints from .kicad_mod files
    for fp_id, fp_path in EXTRA_FOOTPRINTS.items():
        if fp_id not in templates:
            try:
                with open(fp_path) as f:
                    mod = f.read().strip()
                if '(at ' not in mod:
                    mod = re.sub(
                        r'(\(footprint\s+"[^"]+"\s*)',
                        r'\1(layer "F.Cu") (at 0 0) ',
                        mod, count=1
                    )
                templates[fp_id] = mod
                print(f"  [EXTRA] Loaded: {fp_id}")
            except FileNotFoundError:
                print(f"  [WARN]  Extra fp not found: {fp_path}")
    print(f"Templates: {len(templates)} footprint types")
    return templates

# ─────────────────────────────────────────────────────────────────────
# STEP 3 — Build placement positions  (THE CORE CHANGE IN v3)
# ─────────────────────────────────────────────────────────────────────

# Channel centers (mm from top edge), matching XLR connector Y positions
# CH1 center=53, then +26mm per channel
CH_Y = [53.0 + n * 26.0 for n in range(6)]   # index 0=CH1..5=CH6

# Stage X-positions (mm from left edge)
X_XLR_IN   = 12.58   # XLR female inputs  (FIXED)
X_XLR_OUT  = 162.31  # XLR male outputs   (FIXED)
X_TVS_IN   = 28.0    # Input TVS (SOD-323)
X_EMI_R    = 33.0    # Series R / EMI filter resistors
X_EMI_C    = 47.0    # EMI bypass caps
X_DC_BLOCK = 52.0    # DC blocking caps
X_INPUT_R  = 63.0    # Differential Rx input matched resistors
X_SUM_R    = 70.0    # Sumnode mixing resistors (outside of Rx IC)
X_SUM_R2   = 72.0    # Sumnode resistors (bank 2)
X_RX_IC    = 77.0    # LM4562 Rx+Gain IC
X_RX_DEC   = 82.0    # Rx IC decoupling caps (V+/V-)
X_DIP      = 96.0    # DIP gain switch
X_MUTE_Q   = 112.0   # Mute MOSFET
X_DRV_IC   = 130.0   # LM4562 Driver IC
X_DRV_FB   = 137.0   # Driver gain feedback R
X_DRV_DEC  = 136.0   # Driver IC decoupling caps
X_OUT_R    = 148.0   # Output series R
X_TVS_OUT  = 155.0   # Output TVS (SOD-323)

def build_positions(comps):
    """
    Returns dict: ref → (x, y, rotation)
    J1-J14 and SW7 use FIXED positions from the current PCB.
    All channel and power components are placed by their function.
    """
    pos = {}

    # ── FIXED CONNECTORS ─────────────────────────────────────────────
    # Netlist ref → physical position (user confirmed, DO NOT MOVE)
    # PCB label shown in comments for cross-reference
    FIXED = {
        # XLR female inputs (PCB: J3-J8)
        'J1':  (X_XLR_IN,  44.45,  180.0),
        'J2':  (X_XLR_IN,  72.14,  180.0),
        'J3':  (X_XLR_IN,  99.82,  180.0),
        'J4':  (X_XLR_IN, 127.64,  180.0),
        'J5':  (X_XLR_IN, 155.45,  180.0),
        'J6':  (X_XLR_IN, 183.22,  180.0),
        # XLR male outputs (PCB: J9-J14)
        'J7':  (X_XLR_OUT,  44.45,   90.0),
        'J8':  (X_XLR_OUT,  72.14,   90.0),
        'J9':  (X_XLR_OUT,  99.82,   90.0),
        'J10': (X_XLR_OUT, 127.51,   90.0),
        'J11': (X_XLR_OUT, 155.45,   90.0),
        'J12': (X_XLR_OUT, 183.13,   90.0),
        # Power connectors (PCB: J1=barrel, J2=remote)
        'J13': (70.87,  10.83,  -90.0),   # 24V barrel jack (PCB J1)
        'J14': (30.47,   5.08,    0.0),   # Remote 3.5mm (PCB J2)
        # ALWAYS/REMOTE switch (PCB: SW1 EG1224 SPDT, Netlist: SW7 PinHeader)
        # Physical footprint = EG1224 (override in FOOTPRINT_OVERRIDE)
        'SW7': (53.88,   6.79,  180.0),
    }
    pos.update(FIXED)

    # ── PER-CHANNEL COMPONENTS ────────────────────────────────────────
    for n in range(1, 7):          # n = 1..6
        yc   = CH_Y[n - 1]         # channel center Y
        base = 13 * (n - 1)        # resistor numbering offset

        # ICs
        pos[f'U{n}']     = (X_RX_IC,   yc,       0)    # Rx+Gain LM4562
        pos[f'U{6+n}']   = (X_DRV_IC,  yc,       0)    # Driver LM4562

        # DIP gain switch (SW1=CH1..SW6=CH6, keeping away from SW7)
        pos[f'SW{n}']    = (X_DIP,     yc,       0)

        # Mute MOSFET (Q2=CH1..Q7=CH6)
        pos[f'Q{1+n}']   = (X_MUTE_Q,  yc,       0)

        # ── Input TVS ────────────────────────────────────────────────
        # D{2n-1} = CHn_HOT_RAW (D1=CH1,D3=CH2,D5=CH3,D7=CH4,D9=CH5,D11=CH6)
        # D{2n}   = CHn_COLD_RAW (D2,D4,D6,D8,D10,D12)
        pos[f'D{2*n-1}'] = (X_TVS_IN,  yc - 3.5, 0)
        pos[f'D{2*n}']   = (X_TVS_IN,  yc + 3.5, 0)
        # Secondary input TVS (D14=CH1,D16=CH2,D18=CH3,D20=CH4,D22=CH5,D24=CH6)
        # D{14+2*(n-1)} = D14,D16,D18,D20,D22,D24 → CHn_HOT_RAW (input side)
        pos[f'D{14+2*(n-1)}'] = (X_TVS_IN, yc - 5.5, 0)

        # ── Output TVS ───────────────────────────────────────────────
        # D{13+2*(n-1)} = D13,D15,D17,D19,D21,D23 → CHn_OUT_HOT
        pos[f'D{13+2*(n-1)}'] = (X_TVS_OUT, yc - 3.5, 0)

        # ── Decoupling caps (V+/V-) ───────────────────────────────────
        # Rx+Gain IC: C{2n-1}=V+, C{2n}=V-   (C1/C2=CH1, C3/C4=CH2, ...)
        # X_RX_DEC=82 keeps them right of the SOIC-8 at X=77
        pos[f'C{2*n-1}']  = (X_RX_DEC,  yc - 5.0, 0)
        pos[f'C{2*n}']    = (X_RX_DEC,  yc + 5.0, 0)
        # Driver IC: C{12+2n-1}=V+, C{12+2n}=V-  (C13/C14=CH1, C15/C16=CH2, ...)
        # X_DRV_DEC=136: right of driver at 130, left of feedback R at 137
        # Use X=134 to stay clear of both driver pads and feedback R
        pos[f'C{12+2*n-1}'] = (134.0, yc - 5.0, 0)
        pos[f'C{12+2*n}']   = (134.0, yc + 5.0, 0)

        # ── DC blocking caps ──────────────────────────────────────────
        # C{38+2n-1}=CHn_HOT_IN, C{38+2n}=CHn_COLD_IN
        # C39=CH1HOT, C40=CH1COLD, C41=CH2HOT, ... C49=CH6HOT, C50=CH6COLD
        pos[f'C{38+2*n-1}'] = (X_DC_BLOCK, yc - 3.5, 90)
        pos[f'C{38+2*n}']   = (X_DC_BLOCK, yc + 3.5, 90)

        # ── EMI bypass caps ───────────────────────────────────────────
        # C{62+2*(n-1)}=HOT, C{63+2*(n-1)}=COLD
        # C62=CH1,C63=CH1, C64=CH2,C65=CH2, ...
        pos[f'C{62+2*(n-1)}'] = (X_EMI_C, yc - 3.5, 90)
        pos[f'C{63+2*(n-1)}'] = (X_EMI_C, yc + 3.5, 90)

        # ── Input resistors (matched pair network) ────────────────────
        # Group A: R{1-4+base} — differential input Rs + common-mode R
        pos[f'R{1+base}'] = (X_INPUT_R, yc - 5.5, 90)  # HOT R1
        pos[f'R{2+base}'] = (X_INPUT_R, yc - 3.5, 90)  # HOT R2
        pos[f'R{3+base}'] = (X_INPUT_R, yc + 3.5, 90)  # COLD R
        pos[f'R{4+base}'] = (X_INPUT_R, yc + 5.5, 90)  # Common-mode GND R
        # Group B: R{5-9+base} — sumnode mixing network
        pos[f'R{5+base}'] = (X_SUM_R,  yc - 7.0, 90)   # RX_OUT → SUMNODE
        pos[f'R{6+base}'] = (X_SUM_R,  yc + 7.0, 90)   # GAIN_OUT → SUMNODE
        pos[f'R{7+base}'] = (X_SUM_R2, yc - 3.5, 90)   # SUMNODE R
        pos[f'R{8+base}'] = (X_SUM_R2, yc,        90)   # SUMNODE R
        pos[f'R{9+base}'] = (X_SUM_R2, yc + 3.5, 90)   # SUMNODE R
        # R{11+base} = phantom (R11,R24,R37,R50,R63,R76) — skip (not in netlist)
        # Group C: R{10+base} — driver gain feedback
        # X_DRV_FB=137; must not collide with driver decouple caps at x=134
        pos[f'R{10+base}'] = (141.0, yc - 3.0, 90)  # GAIN_OUT near driver (x=141)
        # Group D: R{12+base} — output series R
        pos[f'R{12+base}'] = (X_OUT_R,  yc - 3.5, 90)  # CHn_OUT_HOT series
        # Group E: R{13+base} — input EMI series R
        pos[f'R{13+base}'] = (X_EMI_R,  yc - 5.0, 90)  # CHn_HOT_RAW series

        # ── Additional output/input Rs (wider number range) ───────────
        # R{79+2n}: CHn_OUT_HOT secondary  (R81=CH1,R83=CH2,...,R91=CH6)
        pos[f'R{79+2*n}']  = (X_OUT_R,  yc + 3.5, 90)
        # R{80+2n}: CHn_HOT_RAW secondary  (R82=CH1,R84=CH2,...,R92=CH6)
        pos[f'R{80+2*n}']  = (X_EMI_R,  yc - 3.0, 90)
        # R{91+2n}: CHn_HOT_RAW tertiary   (R93=CH1,R95=CH2,...,R103=CH6)
        pos[f'R{91+2*n}']  = (X_EMI_R,  yc - 1.0, 90)
        # R{92+2n}: CHn_COLD_RAW series    (R94=CH1,R96=CH2,...,R104=CH6)
        pos[f'R{92+2*n}']  = (X_EMI_R,  yc + 3.0, 90)

    # ── POWER ZONE COMPONENTS ─────────────────────────────────────────
    # TEL5-2422 DC/DC converter (DIP-24), center power zone
    pos['U13'] = (88.7,  20.0,  90.0)
    # ADP7118 LDO positive (SOIC-9)
    pos['U14'] = (138.0, 13.0,  0.0)
    # ADP7182 LDO negative (SOT-23-5)
    pos['U15'] = (155.0, 27.0,  0.0)
    # Q1: BSS138 enable MOSFET
    pos['Q1']  = (50.0,  33.0,  0.0)
    # D1: SMBJ15CA input TVS on CH1_HOT_RAW — at CH1 input zone
    # (large SMB package, place slightly offset from SOD-323 row)
    pos['D1']  = (21.0,  53.0,  0.0)
    # D25: REMOTE_IN TVS — near J14 (remote jack)
    pos['D25'] = (42.0,   5.0,  0.0)

    # Ferrite beads ±12V
    pos['FB1'] = (112.0, 13.0,  90.0)
    pos['FB2'] = (112.0, 27.0,  90.0)

    # ±12V rail decoupling (before LDOs — connect to +12V / -12V nets)
    pos['C25'] = (100.0, 10.0,  90.0)   # +12V/GND
    pos['C35'] = (106.0, 10.0,  90.0)   # +12V/GND
    pos['C77'] = (118.0, 10.0,  90.0)   # +12V/GND
    pos['C26'] = (100.0, 30.0,  90.0)   # -12V/GND
    pos['C36'] = (106.0, 30.0,  90.0)   # -12V/GND
    pos['C78'] = (118.0, 30.0,  90.0)   # -12V/GND
    # LDO output decoupling (V+, V- clean rails)
    pos['C37'] = (150.0, 10.0,  90.0)   # V+/GND (near U14)
    pos['C38'] = (150.0, 30.0,  90.0)   # V-/GND (near U15)
    # Soft-start and noise-reduction caps
    pos['C81'] = (130.0, 18.0,  0.0)    # SS_U14/GND — near U14
    pos['C82'] = (150.0, 22.0,  0.0)    # NR_U15/GND — near U15
    # Remote filter cap
    pos['C79'] = (43.0,  10.0,  0.0)    # REMOTE_FILT/GND — near SW7
    # Enable RC timing cap (near Q1)
    pos['C80'] = (46.0,  25.5,  0.0)    # near Q1 gate

    # Extra GND bypass caps
    pos['C74'] = (162.0, 13.0,  90.0)
    pos['C75'] = (162.0, 20.0,  90.0)
    pos['C76'] = (162.0, 27.0,  90.0)

    # EN_CTRL resistors (pulldown, near Q1/SW7)
    pos['R79']  = (44.0,  38.0,  90.0)
    pos['R80']  = (50.0,  38.0,  90.0)
    # Remote input filter R (near J14)
    pos['R105'] = (38.0,   8.0,  90.0)
    # Enable gate R (near Q1)
    pos['R106'] = (46.0,  17.0,  90.0)
    # R56: GND pull (power zone, near Q1 enable circuit)
    pos['R56']  = (56.0,  26.0,  90.0)
    # NOTE: R57 = CH5 SUMNODE R (R{5+base} for CH5, base=52) — handled by channel loop above
    # Do NOT set pos['R57'] here; the per-channel loop correctly places it at (70, 150, 90)

    # ── GND-only bypass caps (C51-C61) and phantom resistors ─────────
    # C51-C52: 100uF bulk bypass near power rails
    pos['C51'] = (165.0, 13.0,  90.0)
    pos['C52'] = (165.0, 27.0,  90.0)
    # C53-C58: 100nF shunt bypass, one per channel strip right side
    for _i, _ref in enumerate(['C53','C54','C55','C56','C57','C58']):
        pos[_ref] = (158.0, CH_Y[_i] + 5.5, 0)
    # C59-C61: additional bypass caps in power zone
    pos['C59'] = (168.0, 10.0, 0)
    pos['C60'] = (168.0, 20.0, 0)
    pos['C61'] = (168.0, 30.0, 0)
    # R11,R24,R37,R50,R63,R76: phantom (no nets) — place off-board below
    for _j, _ref in enumerate(['R11','R24','R37','R50','R63','R76']):
        pos[_ref] = (5.0 + _j * 8.0, 203.0, 0)

    return pos

# ─────────────────────────────────────────────────────────────────────
# STEP 4 — Net table
# ─────────────────────────────────────────────────────────────────────
def build_net_table(comps):
    all_nets = set()
    for c in comps.values():
        for net in c['pins'].values():
            all_nets.add(net)
    all_nets.discard('')
    net_list     = sorted(all_nets)
    net_to_id    = {n: i + 1 for i, n in enumerate(net_list)}
    net_to_id[''] = 0

    lines = ['\t(net 0 "")']
    for net, nid in sorted(net_to_id.items(), key=lambda x: x[1]):
        if net:
            lines.append(f'\t(net {nid} "{net.replace(chr(34), chr(92)+chr(34))}")')
    return '\n'.join(lines) + '\n', net_to_id

# ─────────────────────────────────────────────────────────────────────
# STEP 5 — Transform footprint block
# ─────────────────────────────────────────────────────────────────────
def apply_position_to_footprint(block, ref, value, x, y, rot, net_to_id, pins_map):
    # Normalize indentation
    lines = block.split('\n')
    inner = [l for l in lines[1:] if l.strip()]
    if inner:
        min_ind = min(len(l) - len(l.lstrip('\t')) for l in inner)
        excess  = max(0, min_ind - 1)
        if excess:
            lines = [lines[0]] + [l[excess:] if l.startswith('\t'*excess) else l for l in lines[1:]]
            block = '\n'.join(lines)

    # Update (at X Y ROT)
    rot_str = f' {rot:.6g}' if rot != 0 else ''
    block = re.sub(
        r'\(at\s+[-\d.]+\s+[-\d.]+(?:\s+[-\d.]+)?\)',
        f'(at {x:.4f} {y:.4f}{rot_str})',
        block, count=1
    )

    # Fresh UUIDs
    block = re.sub(
        r'\(uuid\s+"[0-9a-f-]+"\)',
        lambda _: f'(uuid "{str(uuid_mod.uuid4())}")',
        block
    )

    # Update Reference — try both KiCad 9 property format and older fp_text format
    escaped_ref = ref.replace('"', '\\"')
    ref_updated = False

    new_block, n_subs = re.subn(
        r'\(property\s+"Reference"\s+"[^"]*"',
        f'(property "Reference" "{escaped_ref}"',
        block, count=1
    )
    if n_subs:
        block = new_block
        ref_updated = True

    if not ref_updated:
        new_block, n_subs = re.subn(
            r'\(fp_text\s+reference\s+"?[^"\s]+"?',
            f'(fp_text reference "{escaped_ref}"',
            block, count=1
        )
        if n_subs:
            block = new_block
            ref_updated = True

    if not ref_updated:
        # Inject property before closing paren as last resort
        block = block.rstrip()
        block = block[:-1] + f'\n\t(property "Reference" "{escaped_ref}" (at 0 0) (layer "F.SilkS"))\n)'

    # Update Value
    escaped_val = value.replace('"', '\\"')
    block = re.sub(
        r'\(property\s+"Value"\s+"[^"]*"',
        f'(property "Value" "{escaped_val}"',
        block, count=1
    )
    block = re.sub(
        r'\(fp_text\s+value\s+"?[^"\s]+"?',
        f'(fp_text value "{escaped_val}"',
        block, count=1
    )

    # Strip stale net assignments from pads
    block = re.sub(r'\s*\(net\s+\d+\s+"[^"]*"\)', '', block)

    # Inject correct net assignments
    def inject_net(m):
        pad_text = m.group(0)
        pn_m = re.match(r'\(pad\s+"([^"]+)"', pad_text)
        if not pn_m:
            return pad_text
        net_name = pins_map.get(pn_m.group(1), '')
        if not net_name:
            return pad_text
        nid = net_to_id.get(net_name, 0)
        if nid == 0:
            return pad_text
        escaped_net = net_name.replace('"', '\\"')
        size_m = re.search(r'\(size\s+[\d.]+\s+[\d.]+\)', pad_text)
        if size_m:
            ins = size_m.end()
            return pad_text[:ins] + f'\n\t\t\t(net {nid} "{escaped_net}")' + pad_text[ins:]
        return pad_text[:-1] + f'\n\t\t\t(net {nid} "{escaped_net}")\n\t\t)'

    block = re.sub(
        r'\(pad\s+"[^"]+"\s+\w+\s+\w+[^(]*(?:\([^)]*\))*[^)]*\)',
        inject_net,
        block
    )
    return block

# ─────────────────────────────────────────────────────────────────────
# STEP 6 — Board outline + zones
# ─────────────────────────────────────────────────────────────────────
def build_board_outline():
    uid = str(uuid_mod.uuid4())
    return f'''
\t(gr_rect
\t\t(start 0 0)
\t\t(end 180.0000 200.0000)
\t\t(stroke (width 0.05) (type default))
\t\t(fill no)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uid}")
\t)
'''

def build_zones(net_to_id):
    gnd_name = '/GND' if '/GND' in net_to_id else 'GND'
    gnd_id   = net_to_id.get(gnd_name, 0)
    tmpl = '''\t(zone
\t\t(net {nid})
\t\t(net_name "{nm}")
\t\t(layer "{layer}")
\t\t(uuid "{uid}")
\t\t(hatch edge 0.5)
\t\t(connect_pads yes
\t\t\t(clearance 0.5)
\t\t)
\t\t(min_thickness 0.25)
\t\t(filled_areas_thickness no)
\t\t(fill yes
\t\t\t(thermal_gap 0.5)
\t\t\t(thermal_bridge_width 0.5)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy 0.5 0.5) (xy 179.5 0.5) (xy 179.5 199.5) (xy 0.5 199.5)
\t\t\t)
\t\t)
\t)
'''
    z1 = tmpl.format(nid=gnd_id, nm=gnd_name, layer='F.Cu', uid=str(uuid_mod.uuid4()))
    z2 = tmpl.format(nid=gnd_id, nm=gnd_name, layer='B.Cu', uid=str(uuid_mod.uuid4()))
    return '\n' + z1 + z2

# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────
def main():
    print("=== Aurora PCB Builder v3 (netlist-driven) ===\n")

    comps     = parse_netlist(NETLIST)

    # Extract footprint templates from git HEAD PCB (not current file which may be modified)
    import subprocess as _sub_tpl
    _git_tpl = _sub_tpl.run(
        ['git', 'show', 'HEAD:aurora-dsp-icepower-booster.kicad_pcb'],
        capture_output=True, text=True, cwd=PROJ_DIR
    )
    _tpl_path = '/tmp/aurora_template_src.kicad_pcb'
    with open(_tpl_path, 'w') as _f:
        _f.write(_git_tpl.stdout)
    templates = extract_footprint_templates(_tpl_path)

    pos_map   = build_positions(comps)

    net_table_text, net_to_id = build_net_table(comps)

    # Reuse original PCB header (guaranteed valid format)
    import subprocess as _sub
    _git = _sub.run(
        ['git', 'show', 'HEAD:aurora-dsp-icepower-booster.kicad_pcb'],
        capture_output=True, text=True, cwd=PROJ_DIR
    )
    orig = _git.stdout
    nt_idx = orig.find('\t(net 0 "")\n')
    if nt_idx < 0:
        raise RuntimeError("No net table start in original PCB")
    original_header = orig[:nt_idx]
    parts = [original_header, net_table_text, '\n']

    placed = 0
    skipped = 0
    fallback_count = 0

    for ref, comp in sorted(comps.items()):
        fp_id = comp['footprint']
        if not fp_id:
            print(f"  [SKIP]    {ref}: no footprint in netlist")
            skipped += 1
            continue

        # Footprint override (e.g. SW7 → EG1224)
        lookup_fp = FOOTPRINT_OVERRIDE.get(ref, fp_id)

        # Find template
        template = templates.get(lookup_fp)
        if not template:
            # Try partial match (footprint filename without library prefix)
            fp_short = lookup_fp.split(':')[-1] if ':' in lookup_fp else lookup_fp
            for tid, tblock in templates.items():
                if fp_short in tid:
                    template = tblock
                    break

        if not template:
            print(f"  [MISS]    {ref} ({lookup_fp}): no template found")
            skipped += 1
            continue

        # Determine position
        if ref in pos_map:
            x, y, rot = pos_map[ref]
        else:
            # Fallback: place below board in a grid for manual review
            idx        = fallback_count
            x          = 5.0 + (idx % 20) * 8.0
            y          = 205.0 + (idx // 20) * 8.0
            rot        = 0
            fallback_count += 1
            if fallback_count <= 10:
                print(f"  [FALLBACK]{ref}: fp={fp_id} → grid ({x:.0f},{y:.0f})")

        transformed = apply_position_to_footprint(
            template, ref, comp['value'], x, y, rot, net_to_id, comp['pins']
        )
        parts.append('\t' + transformed + '\n')
        placed += 1

    if fallback_count > 10:
        print(f"  [FALLBACK] ...and {fallback_count - 10} more below board")
    print(f"\nFallback (unpositioned): {fallback_count}")

    parts.append(build_board_outline())
    parts.append(build_zones(net_to_id))
    parts.append(')\n')

    tmp_path = '/tmp/aurora_v3.kicad_pcb'
    new_pcb  = ''.join(parts)

    with open(tmp_path, 'w') as f:
        f.write(new_pcb)

    # Validate bracket balance
    depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in new_pcb)
    print(f"\nBracket balance: {depth} (must be 0)")
    print(f"Placed:  {placed}")
    print(f"Skipped: {skipped}")
    print(f"File:    {tmp_path} ({len(new_pcb):,} bytes)")

    if depth == 0 and placed >= 200:
        import shutil
        shutil.copy(tmp_path, OUT_PCB)
        print(f"\n✅  Written to: {OUT_PCB}")
    elif depth != 0:
        print(f"\n❌  Bracket imbalance ({depth}) — NOT writing!")
    else:
        print(f"\n❌  Only {placed} placed (need ≥200) — NOT writing!")

if __name__ == '__main__':
    main()
