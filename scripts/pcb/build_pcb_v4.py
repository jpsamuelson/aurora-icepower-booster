#!/usr/bin/env python3
"""
Aurora DSP ICEpower Booster — PCB Builder v4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY CHANGES vs v3:
  ✓ XML netlist (fresh from kicad-cli) — kein veraltetes .net
  ✓ Net-name-getriebenes Placement — kein hartkodiertes Nummerierungsschema
  ✓ Kanalzuordnung via /CHn_-Prefix in Netznamen
  ✓ Funktionserkennung via Netz-Muster-Matching
  ✓ Kollisionsfreie X-Spalten (fixiert für alle 0805/SOD-323)
  ✓ Board + Connector-Positionen identisch zu v3 (user-bestätigt)

BOARD: 180×200mm, 2-Layer FR-4, JLCPCB
"""
import re
import uuid as uuid_mod
import subprocess
import shutil
import os
from collections import defaultdict

PROJ_DIR = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster'
PROJ     = os.path.join(PROJ_DIR, 'aurora-dsp-icepower-booster')
OUT_PCB  = PROJ + '.kicad_pcb'
KICAD_FP = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

BOARD_W, BOARD_H = 180.0, 200.0

# ─────────────────────────────────────────────────────────────────────
# FIXED CONNECTOR POSITIONS (user-confirmed physical positions)
# Keys are ACTUAL NETLIST ref designators (verified from kicad-cli XML export)
# ─────────────────────────────────────────────────────────────────────
FIXED = {
    # J1 = 24V barrel jack power input
    'J1':  (70.87,  10.83,  -90.0),
    # J2 = Remote 3.5mm jack
    'J2':  (30.47,   5.08,    0.0),
    # J3-J8 = XLR female inputs (CH1-CH6)
    'J3':  (12.58,  44.45,  180.0),
    'J4':  (12.58,  72.14,  180.0),
    'J5':  (12.58,  99.82,  180.0),
    'J6':  (12.58, 127.64,  180.0),
    'J7':  (12.58, 155.45,  180.0),
    'J8':  (12.58, 183.22,  180.0),
    # J9-J14 = XLR male outputs (CH1-CH6)
    'J9':  (162.31,  44.45,  90.0),
    'J10': (162.31,  72.14,  90.0),
    'J11': (162.31,  99.82,  90.0),
    'J12': (162.31, 127.51,  90.0),
    'J13': (162.31, 155.45,  90.0),
    'J14': (162.31, 183.13,  90.0),
    # SW1 = ALWAYS/REMOTE switch (EG1224 SPDT)
    'SW1': (53.88,   6.79,  180.0),
}

# Channel Y-centers — from XLR connector Y positions (authoritative)
CH_Y = {1: 44.45, 2: 72.14, 3: 99.82, 4: 127.64, 5: 155.45, 6: 183.22}

# ─────────────────────────────────────────────────────────────────────
# X COLUMNS (signal path left → right, collision-free)
# ─────────────────────────────────────────────────────────────────────
X_XLR_IN   = 12.58   # XLR female (fixed)
X_TVS_IN   = 24.0    # Input TVS SOD-323  (moved in from 28 → symmetric)
X_EMI_R    = 30.0    # 47Ω EMI series R
X_EMI_C    = 47.0    # 100pF EMI bypass cap
X_DC_BLOCK = 54.0    # 2.2µF DC blocking cap
X_INPUT_R  = 63.0    # 10k input matched Rs (3 per channel, 3.5mm pitch)
X_FB_R     = 70.0    # 10k feedback/summing Rs
X_GAIN_R   = 76.0    # SUMNODE→GAIN_OUT R
X_RX_IC    = 82.0    # LM4562 Rx/Gain SOIC-8
X_RX_DEC   = 88.0    # Rx IC decouple caps
X_DIP_SW   = 97.0    # DIP gain switch (13mm wide)
X_MUTE_Q   = 113.0   # BSS138 mute MOSFET SOT-23
X_DRV_IC   = 128.0   # LM4562 Driver SOIC-8
X_DRV_DEC  = 134.0   # Driver IC decouple caps
X_DRV_R    = 140.0   # Driver feedback Rs (10k)
X_OUT_R    = 145.0   # Output series Rs (47Ω HOT/COLD)
X_OUT_TVS  = 150.0   # Output TVS SOD-323 (was 155 → collision fix)
X_OUT_DEC  = 155.0   # Output bypass/prot caps (was 158 → collision fix)
X_XLR_OUT  = 162.31  # XLR male (fixed)

# ─────────────────────────────────────────────────────────────────────
# FOOTPRINT OVERRIDES
# ─────────────────────────────────────────────────────────────────────
FOOTPRINT_OVERRIDE = {
    'SW1': 'Button_Switch_SMD:SW_E-Switch_EG1224_SPDT_Angled',
}

EXTRA_FOOTPRINTS = {
    'project:TEL5_DUAL_TRP':
        PROJ_DIR + '/footprints.pretty/TEL5_DUAL_TRP.kicad_mod',
    'project:SOIC127P600X175-9N':
        PROJ_DIR + '/footprints.pretty/SOIC127P600X175-9N.kicad_mod',
    'Capacitor_SMD:C_0402_1005Metric':
        KICAD_FP + '/Capacitor_SMD.pretty/C_0402_1005Metric.kicad_mod',
    'Capacitor_SMD:C_1206_3216Metric':
        KICAD_FP + '/Capacitor_SMD.pretty/C_1206_3216Metric.kicad_mod',
    'Capacitor_SMD:C_1210_3225Metric':
        KICAD_FP + '/Capacitor_SMD.pretty/C_1210_3225Metric.kicad_mod',
    'Package_TO_SOT_SMD:SOT-23-5':
        KICAD_FP + '/Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod',
    'Package_TO_SOT_SMD:SOT-23':
        KICAD_FP + '/Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod',
    'Inductor_SMD:L_0805_2012Metric':
        KICAD_FP + '/Inductor_SMD.pretty/L_0805_2012Metric.kicad_mod',
    'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical':
        KICAD_FP + '/Connector_PinHeader_2.54mm.pretty/PinHeader_1x03_P2.54mm_Vertical.kicad_mod',
    'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2_Horizontal':
        KICAD_FP + '/Connector_Audio.pretty/Jack_XLR_Neutrik_NC3FBH2_Horizontal.kicad_mod',
    'Connector_Audio:Jack_XLR_Neutrik_NC3MBH_Horizontal':
        KICAD_FP + '/Connector_Audio.pretty/Jack_XLR_Neutrik_NC3MBH_Horizontal.kicad_mod',
    'Connector_Audio:Jack_XLR_Neutrik_NC3FBH2':
        KICAD_FP + '/Connector_Audio.pretty/Jack_XLR_Neutrik_NC3FBH2_Horizontal.kicad_mod',
    'Connector_Audio:Jack_XLR_Neutrik_NC3MBH':
        KICAD_FP + '/Connector_Audio.pretty/Jack_XLR_Neutrik_NC3MBH_Horizontal.kicad_mod',
}

# ─────────────────────────────────────────────────────────────────────
# STEP 1 — Parse XML netlist (fresh from kicad-cli)
# ─────────────────────────────────────────────────────────────────────
def parse_netlist_xml(path):
    with open(path) as f:
        text = f.read()

    comps = {}
    # Components
    for m in re.finditer(r'<comp ref="([^"]+)">(.*?)</comp>', text, re.DOTALL):
        ref, block = m.group(1), m.group(2)
        val_m = re.search(r'<value>([^<]+)</value>', block)
        fp_m  = re.search(r'<footprint>([^<]+)</footprint>', block)
        comps[ref] = {
            'ref':       ref,
            'value':     val_m.group(1) if val_m else '',
            'footprint': fp_m.group(1)  if fp_m  else '',
            'pins':      {}
        }

    # Nets → pin assignments
    for m in re.finditer(r'<net code="\d+"[^>]*name="([^"]*)"[^>]*>(.*?)</net>', text, re.DOTALL):
        net_name, block = m.group(1), m.group(2)
        for nm in re.finditer(r'<node ref="([^"]+)" pin="([^"]+)"', block):
            ref, pin = nm.group(1), nm.group(2)
            if ref in comps:
                comps[ref]['pins'][pin] = net_name

    print(f"Netlist: {len(comps)} components, {sum(len(c['pins']) for c in comps.values())} pin-net assignments")
    return comps

# ─────────────────────────────────────────────────────────────────────
# STEP 2 — Channel and function detection from net names
# ─────────────────────────────────────────────────────────────────────
def assign_channel(nets_dict):
    """Return channel number 1-6 from CHn_ prefix, or None for global/power comps.
    Also handles mute gate Rs via Net-(Qn-G) where Q2=CH1 .. Q7=CH6.
    """
    channels = set()
    for net in nets_dict.values():
        m = re.search(r'/CH(\d+)_', net)
        if m:
            channels.add(int(m.group(1)))
        # Mute gate Rs: Net-(Q2-G)→CH1 .. Net-(Q7-G)→CH6
        m2 = re.search(r'Net-\(Q(\d+)-G\)', net)
        if m2:
            qn = int(m2.group(1))
            if 2 <= qn <= 7:
                channels.add(qn - 1)
    if len(channels) == 1:
        return channels.pop()
    return None

def classify_function(ref, footprint, nets_dict):
    """
    Returns (x, y_offset_from_ch_center, rotation) for a channel component,
    or None if it cannot be classified (handled by power-zone fallback).

    Y-offset convention: negative = HOT side (upper), positive = COLD side (lower)
    """
    ns = set(nets_dict.values())
    fp = footprint.split(':')[-1] if ':' in footprint else footprint

    def h(*subs):  # all substrings present
        return all(any(s in n for n in ns) for s in subs)
    def has(s):
        return any(s in n for n in ns)
    def is_gnd(n):
        return n in ('GND', '/GND', 'AGND')

    has_gnd = any(is_gnd(n) for n in ns)
    has_vp  = any(n in ('+12V', 'V+', '/V+', '/+12V') for n in ns)
    has_vm  = any(n in ('-12V', 'V-', '/V-', '/-12V') for n in ns)

    # ── ICs FIRST (by footprint type, before net-pattern rules can steal them) ──

    # Rx/Gain LM4562 (SOIC-8) — has RX_OUT as output
    if h('_RX_OUT') and ('LM4562' in fp or 'SOIC-8' in fp):
        return (X_RX_IC, 0.0, 0)

    # Driver LM4562 (SOIC-8) — has BUF_DRIVE or OUT_DRIVE
    if (h('_BUF_DRIVE') or h('_OUT_DRIVE')) and ('LM4562' in fp or 'SOIC-8' in fp):
        return (X_DRV_IC, 0.0, 0)

    # DIP gain switch — has RX_OUT + SW_OUT (multiple switch taps)
    if h('_RX_OUT') and h('_SW_OUT_') and ('DIP' in fp or 'Slide' in fp or 'A6S' in fp):
        return (X_DIP_SW, 0.0, 0)

    # Mute MOSFET — connects GAIN_OUT (passes/blocks audio)
    if h('_GAIN_OUT') and ('BSS138' in fp or 'SOT-23' in fp or 'SOT_23' in fp):
        return (X_MUTE_Q, 0.0, 0)

    # ── INPUT SIDE (left of Rx IC) ─────────────────────────────────

    # Input TVS diodes (SOD-323 / SMB)
    if h('_HOT_RAW') and not has('_EMI_HOT') and not has('_HOT_IN'):
        return (X_TVS_IN, -3.5, 0)
    if h('_COLD_RAW') and not has('_EMI_COLD') and not has('_COLD_IN'):
        return (X_TVS_IN, +3.5, 0)

    # EMI series Rs (47Ω) — between RAW and EMI_x
    if h('_HOT_RAW') and h('_EMI_HOT'):
        return (X_EMI_R, -3.5, 90)
    if h('_COLD_RAW') and h('_EMI_COLD'):
        return (X_EMI_R, +3.5, 90)

    # EMI bypass caps (100pF) — from EMI_HOT/COLD to GND (shunt cap)
    if h('_EMI_HOT') and has_gnd and not h('_HOT_IN') and not h('_HOT_RAW'):
        return (X_EMI_C, -3.5, 90)
    if h('_EMI_COLD') and has_gnd and not h('_COLD_IN') and not h('_COLD_RAW'):
        return (X_EMI_C, +3.5, 90)

    # DC blocking caps (2.2µF series) — from EMI_HOT → HOT_IN, or EMI_COLD → COLD_IN
    if h('_EMI_HOT') and h('_HOT_IN'):
        return (X_DC_BLOCK, -3.5, 90)
    if h('_EMI_COLD') and h('_COLD_IN'):
        return (X_DC_BLOCK, +3.5, 90)

    # DC blocking caps (fallback) — only HOT_IN or COLD_IN, no EMI net, not GND-terminated
    # (Series caps have no GND connection; shunt caps with GND are handled as input Rs)
    if h('_HOT_IN') and not has('_INV_IN') and not h('_EMI_HOT') and not has_gnd:
        return (X_DC_BLOCK, -3.5, 90)
    if h('_COLD_IN') and not has('_INV_IN') and not h('_EMI_COLD') and not has_gnd:
        return (X_DC_BLOCK, +3.5, 90)

    # Input Rs — HOT_IN → GND (termination)
    if h('_HOT_IN') and has_gnd and not has('_INV_IN'):
        return (X_INPUT_R, -7.0, 90)

    # Input Rs — COLD_IN → INV_IN
    if h('_COLD_IN') and h('_INV_IN') and not has('_RX_OUT'):
        return (X_INPUT_R, -3.5, 90)

    # Input Rs — GND → INV_IN (bias/termination at −In)
    if h('_INV_IN') and has_gnd and not has('_COLD_IN') and not has('_RX_OUT'):
        return (X_INPUT_R, +1.5, 90)

    # ── Rx FEEDBACK / SUMMING (around Rx IC) ─────────────────────

    # Rx feedback R — INV_IN ↔ RX_OUT
    if h('_INV_IN') and h('_RX_OUT'):
        return (X_FB_R, -3.5, 90)

    # Summing R — RX_OUT ↔ SUMNODE
    if h('_RX_OUT') and h('_SUMNODE'):
        return (X_FB_R, +3.5, 90)

    # ── GAIN SWITCH STAGE ─────────────────────────────────────────

    # Switch output Rs (connect between DIP switch and sumnode)
    if h('_SW_OUT_1') and h('_SUMNODE'):
        return (X_DIP_SW - 7.0, -7.0, 90)  # 30k, x=90 (was 87 — collision with U1)
    if h('_SW_OUT_2') and h('_SUMNODE'):
        return (X_DIP_SW - 7.0, -3.5, 90)  # 15k
    if h('_SW_OUT_3') and h('_SUMNODE'):
        return (X_DIP_SW - 7.0,  0.0, 90)  # 7.5k

    # SUMNODE → GAIN_OUT R
    if h('_SUMNODE') and h('_GAIN_OUT'):
        return (X_GAIN_R, 0.0, 90)

    # ── DRIVER SIDE ───────────────────────────────────────────────

    # Gain feedback R #1 — GAIN_FB ↔ GAIN_OUT
    if h('_GAIN_FB') and h('_GAIN_OUT'):
        return (X_DRV_R - 6.0, -3.5, 90)

    # Gain feedback R #2 — GAIN_FB ↔ OUT_DRIVE
    if h('_GAIN_FB') and h('_OUT_DRIVE'):
        return (X_DRV_R, -3.5, 90)

    # Output series Rs — OUT_DRIVE → OUT_HOT  (47Ω)
    if h('_OUT_DRIVE') and h('_OUT_HOT'):
        return (143.0, -3.5, 90)

    # Output series Rs — BUF_DRIVE → OUT_COLD  (47Ω)
    if h('_BUF_DRIVE') and h('_OUT_COLD'):
        return (143.0, +3.5, 90)

    # Output protection Rs — OUT_HOT → OUT_PROT_HOT  (10Ω)
    if h('_OUT_HOT') and h('_OUT_PROT_HOT'):
        return (147.0, -3.5, 90)

    # Output protection Rs — OUT_COLD → OUT_PROT_COLD  (10Ω)
    if h('_OUT_COLD') and h('_OUT_PROT_COLD'):
        return (147.0, +3.5, 90)

    # Output TVS diodes — OUT_HOT + GND, no DRIVE no PROT (diode between signal and GND)
    if h('_OUT_HOT') and has_gnd and not has('_OUT_DRIVE') and not has('_PROT_HOT'):
        return (X_OUT_TVS, -3.5, 0)

    # Output TVS diodes — OUT_COLD + GND
    if h('_OUT_COLD') and has_gnd and not has('_BUF_DRIVE') and not has('_PROT_COLD'):
        return (X_OUT_TVS, +3.5, 0)

    # Output protection caps — OUT_PROT_HOT/COLD → GND
    if h('_OUT_PROT_HOT'):
        return (X_OUT_DEC, -3.5, 90)
    if h('_OUT_PROT_COLD'):
        return (X_OUT_DEC, +3.5, 90)

    # Mute gate Rs — connect /MUTE to Net-(Qn-G) for per-channel MOSFET gates
    # Channel already assigned via assign_channel(); place above channel MOSFET
    if any('/MUTE' in n for n in ns) and any('Net-(Q' in n for n in ns):
        return (X_MUTE_Q + 4.0, -5.0, 90)

    return None  # → handled by power zone or fallback

# ─────────────────────────────────────────────────────────────────────
# STEP 3 — Build full position map
# ─────────────────────────────────────────────────────────────────────
def build_positions(comps):
    pos = {}

    # ── FIXED CONNECTORS ────────────────────────────────────────────
    pos.update(FIXED)

    # ── CHANNEL COMPONENTS (net-name driven) ──────────────────────
    unclassified_ch = []
    for ref, comp in comps.items():
        if ref in FIXED:
            continue
        ch = assign_channel(comp['pins'])
        if ch is None:
            continue  # global/power component, handled below

        result = classify_function(ref, comp['footprint'], comp['pins'])
        if result:
            x, dy, rot = result
            pos[ref] = (x, CH_Y[ch] + dy, rot)
        else:
            unclassified_ch.append((ref, comp, ch))

    # Still unclassified channel components — place with spread within channel strip
    _ch_fallback_count = defaultdict(int)
    for ref, comp, ch in unclassified_ch:
        if ref in pos:
            continue
        idx = _ch_fallback_count[ch]
        _ch_fallback_count[ch] += 1
        # Place in channel strip at evenly spaced x, y=channel center
        x = 15.0 + idx * 7.0
        y = CH_Y[ch]
        pos[ref] = (x, y, 0)
        print(f"  [UNCLASS] {ref} (CH{ch}, fp={comp['footprint'].split(':')[-1]}) → ({x:.0f},{y:.0f})")

    # ── POWER ZONE COMPONENTS ────────────────────────────────────
    # Explicit positions for all global (no CHn_ net) components.
    # Verified from kicad-cli XML netlist: U1=TEL5, U14=ADP7118, U15=ADP7182,
    # SW1=ALWAYS/REMOTE, J1=barrel jack, J2=remote (all already in FIXED).
    # Layout: x=20-80 (remote/switch area), x=80-180 (power rail area, y=0-40)
    POWER_ZONE = {
        # ── ICs ──────────────────────────────────────────────────────
        'U1':  (88.7,  20.0,   0.0),   # TEL5-2422 DC/DC DIP-24, rot=0
        'U14': (138.0, 13.0,   0.0),   # ADP7118 positive LDO
        'U15': (155.0, 27.0,   0.0),   # ADP7182 negative LDO

        # ── Ferrite beads ±12V ───────────────────────────────────────
        'FB1': (112.0, 10.0,  90.0),   # +12V_RAW → +12V
        'FB2': (112.0, 30.0,  90.0),   # -12V_RAW → -12V

        # ── Enable / Mute MOSFETs ─────────────────────────────────────
        'Q1':  ( 50.0,  30.0,   0.0),  # BSS138 mute enable MOSFET

        # ── Remote input TVS (SMBJ15CA, SMB pkg) ─────────────────────
        'D1':  ( 38.0,   8.0,   0.0),

        # ── +24V/±12V_RAW rail caps ───────────────────────────────────
        'C14': ( 80.0,  10.0,  90.0),  # 100nF +12V_RAW bypass
        'C15': ( 80.0,  30.0,  90.0),  # 100nF -12V_RAW bypass
        'C16': ( 84.0,  10.0,  90.0),  # 100µF +12V_RAW bulk (1210)
        'C17': ( 84.0,  30.0,  90.0),  # 100µF -12V_RAW bulk (1210)

        # ── ±12V (post ferrite) rail caps ────────────────────────────
        'C18': (118.0,  10.0,  90.0),  # 100nF +12V bypass
        'C19': (118.0,  30.0,  90.0),  # 100nF -12V bypass

        # ── /V+ rail decouple caps (multiple, spread in power zone) ──
        # U14 input/output, U2-U7 supply rail
        'C2':  ( 90.0,  10.0,  90.0),
        'C3':  ( 93.0,  10.0,  90.0),
        'C4':  ( 96.0,  10.0,  90.0),
        'C5':  ( 99.0,  10.0,  90.0),
        'C6':  (102.0,  10.0,  90.0),
        'C7':  (105.0,  10.0,  90.0),
        'C20': (124.0,  10.0,  90.0),  # 100µF V+ bulk (1210)
        'C22': (128.0,  10.0,  90.0),  # 100nF V+
        'C24': (131.0,  10.0,  90.0),  # 10µF V+ X5R
        'C26': (144.0,  10.0,  90.0),  # 100nF V+ — moved from 134 (was inside U14 courtyard)
        'C27': (143.0,  10.0,  90.0),  # 100nF V+
        'C28': (146.0,  10.0,  90.0),  # 100nF V+
        'C29': (149.0,  10.0,  90.0),  # 100nF V+
        'C30': (152.0,  10.0,  90.0),  # 100nF V+
        'C31': (155.0,  10.0,  90.0),  # 100nF V+
        'C74': (158.0,  10.0,  90.0),  # 10µF V+ X5R
        'C76': (161.0,  10.0,  90.0),  # 10µF V+
        'C78': (164.0,  10.0,  90.0),  # 10µF V+

        # ── /V- rail decouple caps ───────────────────────────────────
        'C8':  ( 90.0,  30.0,  90.0),
        'C9':  ( 93.0,  30.0,  90.0),
        'C10': ( 96.0,  30.0,  90.0),
        'C11': ( 99.0,  30.0,  90.0),
        'C12': (102.0,  30.0,  90.0),
        'C13': (105.0,  30.0,  90.0),
        'C21': (124.0,  30.0,  90.0),  # 100µF V- bulk (1210)
        'C25': (128.0,  30.0,  90.0),  # 10µF V- X5R
        'C32': (131.0,  30.0,  90.0),  # 100nF V-
        'C33': (134.0,  30.0,  90.0),  # 100nF V-
        'C34': (137.0,  30.0,  90.0),  # 100nF V-
        'C35': (140.0,  30.0,  90.0),  # 100nF V-
        'C36': (143.0,  30.0,  90.0),  # 100nF V-
        'C37': (146.0,  30.0,  90.0),  # 100nF V-
        'C75': (149.0,  30.0,  90.0),  # 10µF V- X5R
        'C77': (152.0,  30.0,  90.0),  # 10µF V-
        'C79': (155.0,  30.0,  90.0),  # 10µF V- — moved from 164 (was inside J9 courtyard)

        # ── Special single caps ──────────────────────────────────────
        'C1':  ( 43.0,  12.0,  90.0),  # 100nF /REMOTE_FILT bypass
        'C23': (152.0,  20.0,  90.0),  # 22nF /NR_U15 (ADP7182 noise reduction)
        'C80': ( 46.0,  28.0,   0.0),  # 10µF mute timing cap (Net-(Q1-G))
        'C81': (170.0,  20.0,  90.0),  # 22nF /SS_U14 (ADP7118 soft-start) — moved to clear C22

        # ── Enable / power-zone resistors ────────────────────────────
        'R1':   (40.0,  15.0,  90.0),  # 10k /REMOTE_IN → /REMOTE_FILT
        'R56':  (58.0,  25.0,  90.0),  # 100k /EN_CTRL → /V+ pullup
        'R57':  (58.0,  29.0,  90.0),  # 100k /EN_CTRL → GND pulldown
        'R106': (48.0,  21.0,  90.0),  # 10k /V+ → Net-(Q1-G) pullup
        'R107': (48.0,  25.0,  90.0),  # 100k /MUTE pullup to /V+
    }

    for ref, pos_tuple in POWER_ZONE.items():
        if ref not in pos:
            pos[ref] = pos_tuple

    # ── MOUNTING HOLES ────────────────────────────────────────────
    # M3, 4mm from board edge — all corners confirmed free
    MH_MARGIN = 4.0
    pos['MH1'] = (MH_MARGIN,            MH_MARGIN,             0.0)
    pos['MH2'] = (BOARD_W - MH_MARGIN,  MH_MARGIN,             0.0)
    pos['MH3'] = (BOARD_W - MH_MARGIN,  BOARD_H - MH_MARGIN,   0.0)
    pos['MH4'] = (MH_MARGIN,            BOARD_H - MH_MARGIN,   0.0)

    # Summary
    total = len([r for r in comps if r in pos])
    print(f"Positioned: {total}/{len(comps)} components")
    return pos

# ─────────────────────────────────────────────────────────────────────
# STEP 4 — Footprint templates (reused from v3)
# ─────────────────────────────────────────────────────────────────────
def extract_block(content, start):
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
        block = extract_block(content, m.start())
        fp_m  = re.match(r'\(footprint\s+"([^"]+)"', block)
        if not fp_m:
            continue
        fp_id = fp_m.group(1)
        if fp_id not in templates:
            templates[fp_id] = block

    # Load extra project footprints
    for fp_id, fp_path in EXTRA_FOOTPRINTS.items():
        if fp_id not in templates:
            try:
                with open(fp_path) as f:
                    mod = f.read().strip()
                # .kicad_mod files have NO component-level (at ...) — only sub-elements do.
                # ALWAYS inject (at 0 0) right after the footprint name so it becomes the
                # FIRST (at ...) in the string, which apply_position_to_footprint replaces.
                # Handles both quoted ("name") and unquoted (name) footprint names.
                mod = re.sub(
                    r'(\(footprint\s+(?:"[^"]+"|[^\s)]+)\s*)',
                    r'\1(at 0 0) ',
                    mod, count=1
                )
                templates[fp_id] = mod
                print(f"  [EXTRA] Loaded: {fp_id}")
            except FileNotFoundError:
                print(f"  [WARN]  Extra fp not found: {fp_path}")

    print(f"Templates: {len(templates)} footprint types")
    return templates

# ─────────────────────────────────────────────────────────────────────
# STEP 5 — Net table
# ─────────────────────────────────────────────────────────────────────
def build_net_table(comps):
    all_nets = set()
    for c in comps.values():
        for net in c['pins'].values():
            all_nets.add(net)
    all_nets.discard('')
    net_list  = sorted(all_nets)
    net_to_id = {n: i + 1 for i, n in enumerate(net_list)}
    net_to_id[''] = 0

    lines = ['\t(net 0 "")']
    for net, nid in sorted(net_to_id.items(), key=lambda x: x[1]):
        if net:
            lines.append(f'\t(net {nid} "{net.replace(chr(34), chr(92)+chr(34))}")')
    return '\n'.join(lines) + '\n', net_to_id

# ─────────────────────────────────────────────────────────────────────
# STEP 6 — Transform footprint (reused from v3, unchanged)
# ─────────────────────────────────────────────────────────────────────
def apply_position_to_footprint(block, ref, value, x, y, rot, net_to_id, pins_map):
    # Normalize indentation
    lines = block.split('\n')
    inner = [l for l in lines[1:] if l.strip()]
    if inner:
        min_ind = min(len(l) - len(l.lstrip('\t')) for l in inner)
        excess  = max(0, min_ind - 1)
        if excess:
            lines = [lines[0]] + [l[excess:] if l.startswith('\t' * excess) else l for l in lines[1:]]
            block = '\n'.join(lines)

    # Update position
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

    # Update Reference
    escaped_ref = ref.replace('"', '\\"')
    new_block, n = re.subn(
        r'\(property\s+"Reference"\s+"[^"]*"',
        f'(property "Reference" "{escaped_ref}"',
        block, count=1
    )
    if n:
        block = new_block
    else:
        new_block, n = re.subn(
            r'\(fp_text\s+reference\s+"?[^"\s]+"?',
            f'(fp_text reference "{escaped_ref}"',
            block, count=1
        )
        if n:
            block = new_block
        else:
            block = block.rstrip()[:-1] + f'\n\t(property "Reference" "{escaped_ref}" (at 0 0) (layer "F.SilkS"))\n)'

    # Update Value
    escaped_val = value.replace('"', '\\"')
    block = re.sub(r'\(property\s+"Value"\s+"[^"]*"',
                   f'(property "Value" "{escaped_val}"', block, count=1)
    block = re.sub(r'\(fp_text\s+value\s+"?[^"\s]+"?',
                   f'(fp_text value "{escaped_val}"', block, count=1)

    # Strip stale nets
    block = re.sub(r'\s*\(net\s+\d+\s+"[^"]*"\)', '', block)

    # Inject correct nets
    def inject_net(m):
        pad_text = m.group(0)
        # Match both quoted "1" and unquoted 1 pad names
        pn_m = re.match(r'\(pad\s+(?:"([^"]+)"|(\S+))', pad_text)
        if not pn_m:
            return pad_text
        pad_name = pn_m.group(1) or pn_m.group(2)
        net_name = pins_map.get(pad_name, '')
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

    # Match pads with both quoted and unquoted names
    # \s* inside repetition to consume whitespace between sub-expressions
    block = re.sub(
        r'\(pad\s+(?:"[^"]+"|[^\s)]+)\s+\w+\s+\w+\s*(?:\([^)]*\)\s*)*\)',
        inject_net, block
    )
    return block

# ─────────────────────────────────────────────────────────────────────
# STEP 7 — Board outline + GND zones (unchanged from v3)
# ─────────────────────────────────────────────────────────────────────
def build_board_outline():
    uid = str(uuid_mod.uuid4())
    return f'''
\t(gr_rect
\t\t(start 0 0)
\t\t(end {BOARD_W:.4f} {BOARD_H:.4f})
\t\t(stroke (width 0.05) (type default))
\t\t(fill no)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uid}")
\t)
'''

def build_mounting_holes():
    """Generate MH1-MH4 footprint blocks for M3 mounting holes."""
    MH_FP = KICAD_FP + '/MountingHole.pretty/MountingHole_3.2mm_M3.kicad_mod'
    if not os.path.exists(MH_FP):
        print("  [WARN] Mounting hole footprint not found, skipping")
        return ''
    with open(MH_FP) as f:
        raw = f.read().strip()
    # Inject component-level (at 0 0) — .kicad_mod has none at top level
    template = re.sub(
        r'(\(footprint\s+(?:"[^"]+"|[^\s)]+)\s*)',
        r'\1(at 0 0) ',
        raw, count=1
    )
    mh_positions = [
        ('MH1', 4.0,            4.0,              0),
        ('MH2', BOARD_W - 4.0,  4.0,              0),
        ('MH3', BOARD_W - 4.0,  BOARD_H - 4.0,   0),
        ('MH4', 4.0,            BOARD_H - 4.0,   0),
    ]
    blocks = []
    for ref, x, y, rot in mh_positions:
        blk = apply_position_to_footprint(template, ref, 'MountingHole', x, y, rot, {}, {})
        blocks.append('\t' + blk + '\n')
    return ''.join(blocks)

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
    print("=== Aurora DSP PCB Builder v4 (net-name driven) ===\n")

    # 1. Generate fresh XML netlist
    xml_path = '/tmp/aurora_v4_netlist.xml'
    print(f"Generating fresh netlist → {xml_path}")
    result = subprocess.run(
        ['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml',
         '-o', xml_path, PROJ + '.kicad_sch'],
        capture_output=True, text=True, cwd=PROJ_DIR
    )
    if result.returncode != 0:
        print(f"ERROR: kicad-cli failed:\n{result.stderr}")
        return
    print(f"  OK ({result.stderr.strip() or 'success'})")

    # 2. Parse netlist
    comps = parse_netlist_xml(xml_path)

    # 3. Extract footprint templates from git HEAD PCB
    git = subprocess.run(
        ['git', 'show', 'HEAD:aurora-dsp-icepower-booster.kicad_pcb'],
        capture_output=True, text=True, cwd=PROJ_DIR
    )
    tpl_path = '/tmp/aurora_v4_template.kicad_pcb'
    with open(tpl_path, 'w') as f:
        f.write(git.stdout)
    templates = extract_footprint_templates(tpl_path)

    # 4. Build positions (net-name driven)
    pos_map = build_positions(comps)

    # 5. Net table
    net_table_text, net_to_id = build_net_table(comps)

    # 6. Assemble PCB file
    # Use original header from git HEAD for guaranteed-valid format
    orig = git.stdout
    nt_idx = orig.find('\t(net 0 "")\n')
    if nt_idx < 0:
        raise RuntimeError("Could not find net table header in original PCB")
    original_header = orig[:nt_idx]
    parts = [original_header, net_table_text, '\n']

    placed = 0
    skipped = 0
    fallback_count = 0

    for ref, comp in sorted(comps.items()):
        fp_id = comp['footprint']
        if not fp_id:
            print(f"  [SKIP]    {ref}: no footprint")
            skipped += 1
            continue

        lookup_fp = FOOTPRINT_OVERRIDE.get(ref, fp_id)

        template = templates.get(lookup_fp)
        if not template:
            fp_short = lookup_fp.split(':')[-1] if ':' in lookup_fp else lookup_fp
            # Try exact match on short name first (e.g. "SOT-23" != "SOT-23-5")
            for tid, tblock in templates.items():
                tid_short = tid.split(':')[-1] if ':' in tid else tid
                if fp_short == tid_short:
                    template = tblock
                    break
            # Fallback: substring match
            if not template:
                for tid, tblock in templates.items():
                    if fp_short in tid:
                        template = tblock
                        break

        if not template:
            print(f"  [MISS]    {ref} ({lookup_fp}): no template")
            skipped += 1
            continue

        if ref in pos_map:
            x, y, rot = pos_map[ref]
        else:
            # Fallback: below board, for manual review
            idx = fallback_count
            x   = 5.0 + (idx % 20) * 8.0
            y   = 205.0 + (idx // 20) * 8.0
            rot = 0
            fallback_count += 1
            if fallback_count <= 15:
                ch = assign_channel(comp['pins'])
                nets_short = sorted(set(str(n).split('/')[-1][:20] for n in comp['pins'].values()))[:3]
                print(f"  [FALLBACK]{ref} CH={ch} fp={fp_id.split(':')[-1]} nets={nets_short}")

        transformed = apply_position_to_footprint(
            template, ref, comp['value'], x, y, rot, net_to_id, comp['pins']
        )
        parts.append('\t' + transformed + '\n')
        placed += 1

    if fallback_count > 15:
        print(f"  [FALLBACK] ... and {fallback_count - 15} more")

    # 7. Mounting holes
    parts.append(build_mounting_holes())

    # 8. Board outline + zones
    parts.append(build_board_outline())
    parts.append(build_zones(net_to_id))
    parts.append(')\n')

    # 9. Write + validate
    tmp_path = '/tmp/aurora_v4.kicad_pcb'
    new_pcb  = ''.join(parts)
    with open(tmp_path, 'w') as f:
        f.write(new_pcb)

    depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in new_pcb)

    print(f"\n{'='*50}")
    print(f"Placed:   {placed}")
    print(f"Skipped:  {skipped}")
    print(f"Fallback: {fallback_count}")
    print(f"Balance:  {depth} (must be 0)")
    print(f"Size:     {len(new_pcb):,} bytes")

    if depth == 0 and placed >= 230:
        shutil.copy(tmp_path, OUT_PCB)
        print(f"\n✅  Written to: {OUT_PCB}")

        # Quick DRC validation
        print("\nRunning DRC...")
        drc = subprocess.run(
            ['kicad-cli', 'pcb', 'drc',
             '--output', '/tmp/aurora_v4_drc.json',
             '--format', 'json',
             '--severity-all',
             OUT_PCB],
            capture_output=True, text=True, cwd=PROJ_DIR
        )
        if drc.returncode == 0:
            drc_text = open('/tmp/aurora_v4_drc.json').read()
            errors   = drc_text.count('"severity": "error"')
            warnings = drc_text.count('"severity": "warning"')
            unconn   = drc_text.count('unconnected')
            print(f"  Errors:   {errors}")
            print(f"  Warnings: {warnings}")
            print(f"  Unconnected mentions: {unconn}")
        else:
            print(f"  DRC stderr: {drc.stderr[:200]}")
    elif depth != 0:
        print(f"\n❌  Bracket imbalance ({depth}) — NOT written!")
    else:
        print(f"\n❌  Only {placed} placed (need ≥230) — NOT written!")
        print(f"    Check fallback list above.")


if __name__ == '__main__':
    main()
