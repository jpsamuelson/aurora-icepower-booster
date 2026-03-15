#!/usr/bin/env python3
"""
Generate PCB placement commands for MCP.
Outputs a list of (ref, footprint, value, x, y, rotation) tuples.

Board Layout Strategy (based on Copilot Instructions §5):
- 6-channel balanced audio booster
- Connectors at board edges
- PSU section separate from audio
- Channels laid out in rows

Board dimensions: ~200mm x 160mm (estimate for 6 channels + PSU)

Layout zones:
  LEFT:   XLR inputs (J1-J6)     X: 10-25
  CENTER: Audio channels          X: 30-170
  RIGHT:  XLR outputs (J7-J12)   X: 175-195
  TOP:    PSU                     Y: 10-40
  
Channel strips (Y spacing ~20mm each):
  CH1: Y=50
  CH2: Y=70
  CH3: Y=90
  CH4: Y=110
  CH5: Y=130
  CH6: Y=150
"""
import json

with open('placement_data.json', 'r') as f:
    data = json.load(f)

components = data['components']

# Build reference -> component map
comp_map = {c['ref']: c for c in components}

# Placement results
placements = []

def place(ref, x, y, rot=0):
    if ref in comp_map:
        c = comp_map[ref]
        placements.append({
            'ref': ref,
            'footprint': c['footprint'],
            'value': c['value'],
            'x': round(x, 2),
            'y': round(y, 2),
            'rotation': rot
        })

# ============================================================
# PSU Section (top area, Y: 10-35)
# ============================================================
# Barrel Jack at far left
place('J13', 8, 22, 0)

# TEL5-2422 DC-DC converter
place('U13', 40, 22, 0)

# Bulk caps at TEL5 output
place('C35', 58, 16, 0)   # 100uF +12V
place('C36', 58, 28, 0)   # 100uF -12V

# HF bypass at TEL5 output
place('C77', 63, 16, 0)   # 100nF C0G +12V 
place('C78', 63, 28, 0)   # 100nF C0G -12V

# LDO +12V (ADP7118)
place('U14', 78, 16, 0)
place('C25', 88, 16, 0)   # 100nF bypass
place('C37', 93, 16, 0)   # 10uF output

# Muting RC for +12V
place('R79', 72, 12, 0)
place('C51', 72, 20, 0)

# LDO -12V (ADP7182)  
place('U15', 78, 28, 0)
place('C26', 88, 28, 0)   # 100nF bypass
place('C38', 93, 28, 0)   # 10uF output

# Muting RC for -12V
place('R80', 72, 32, 0)
place('C52', 72, 24, 180)

# ============================================================
# Channel placement function
# ============================================================
# Each channel has the same topology:
# XLR_IN → EMI_R(47) → EMI_C(100pF) → TVS → DC_Block_C(2.2uF) →
# InAmp(U_hot/U_cold) → DIP_SW → SumAmp(U_sum) → OutputAmp(U_out) →
# Zobel(R+C) → TVS_out → XLR_OUT

def place_channel(ch_num, y_center):
    """Place all components for one channel."""
    # Numbering scheme:
    # CH1: U1/U7(hot_path), U1/U7(cold_path) - dual opamps = 2 physical ICs
    # Resistors: R1-R13 for CH1, R14-R26 for CH2, etc.
    # Caps: C1-C6 basic bypass, C27-C34 additional
    
    ch = ch_num
    y = y_center
    
    # === Input XLR (left edge) ===
    xlr_in_ref = f'J{ch}'
    place(xlr_in_ref, 8, y, 0)
    
    # === EMI filter (47Ω + 100pF) per line (HOT & COLD) ===
    # EMI-R for hot
    emi_r_base = 93 + (ch-1)*2  # R93-R104
    emi_r_hot = f'R{emi_r_base}'
    emi_r_cold = f'R{emi_r_base + 1}'
    place(emi_r_hot, 28, y - 3, 0)
    place(emi_r_cold, 28, y + 3, 0)
    
    # EMI-C
    emi_c_base = 65 + (ch-1)*2  # C65-C76
    emi_c_hot = f'C{emi_c_base}'
    emi_c_cold = f'C{emi_c_base + 1}'
    place(emi_c_hot, 33, y - 3, 0)
    place(emi_c_cold, 33, y + 3, 0)
    
    # === Input TVS diodes ===
    tvs_in_base = (ch-1)*4 + 1  # D1-D4 for CH1, D5-D8 for CH2, etc.
    place(f'D{tvs_in_base}', 24, y - 3, 90)      # Hot input TVS
    place(f'D{tvs_in_base+1}', 24, y + 3, 90)      # Cold input TVS
    
    # === DC-Block caps (2.2uF C0G) ===
    dc_block_base = 39 + (ch-1)*2  # C39-C50
    place(f'C{dc_block_base}', 38, y - 3, 90)    # Hot DC block
    place(f'C{dc_block_base+1}', 38, y + 3, 90)  # Cold DC block
    
    # === Input InAmp stage (differential receiver) ===
    # Each channel uses 2 dual opamps = 4 opamp units
    # CH1: U1(unitA=hot_diff, unitB=cold_diff), U7(unitA=sum, unitB=output)
    # U1-U6: input stages, U7-U12: output stages
    u_in = f'U{ch}'
    u_out = f'U{ch+6}'
    
    place(u_in, 55, y, 0)
    
    # Input stage resistors (precision 10k for diff amp)
    r_base = (ch-1)*13 + 1  # R1-R13 for CH1
    # First 6 Rs are gain-setting (10k 0.1%)
    for i in range(6):
        rx = 45 + (i % 3) * 5
        ry = y - 8 + (i // 3) * 16
        place(f'R{r_base + i}', rx, ry, 90)
    
    # R7 = 30k feedback
    place(f'R{r_base + 6}', 65, y - 5, 0)
    # R8 = gain select (15k or 7.5k)
    place(f'R{r_base + 7}', 65, y + 5, 0)
    
    # === DIP switch for gain ===
    place(f'SW{ch}', 75, y, 0)
    
    # Bypass caps for input stage  
    # CH1: C1,C2 (bypass), C3,C4 (bypass output stage)
    c_bypass_base = (ch-1)*4 + 1  # C1-C24
    place(f'C{c_bypass_base}', 50, y - 8, 0)      # Input stage V+ bypass
    place(f'C{c_bypass_base+1}', 50, y + 8, 0)     # Input stage V- bypass
    
    # === Sum/Output amp stage ===
    place(u_out, 100, y, 0)
    
    # Remaining resistors for output stage
    # R9/R10 = 10k feedback (or equivalent)
    if r_base + 8 <= 104:
        place(f'R{r_base + 8}', 90, y - 4, 0)
    if r_base + 9 <= 104:
        place(f'R{r_base + 9}', 90, y + 4, 0)
    if r_base + 10 <= 104:
        place(f'R{r_base + 10}', 105, y - 4, 0)
    if r_base + 11 <= 104:
        place(f'R{r_base + 11}', 105, y + 4, 0)
    if r_base + 12 <= 104:
        place(f'R{r_base + 12}', 110, y, 0)
    
    # Output stage bypass caps
    place(f'C{c_bypass_base+2}', 95, y - 8, 0)     # Output V+ bypass
    place(f'C{c_bypass_base+3}', 95, y + 8, 0)      # Output V- bypass
    
    # === Zobel networks (10Ω + 100nF) ===
    zobel_r_base = 81 + (ch-1)*2  # R81-R92
    zobel_c_base = 53 + (ch-1)*2  # C53-C64
    place(f'R{zobel_r_base}', 120, y - 4, 0)      # Zobel-R hot
    place(f'C{zobel_c_base}', 125, y - 4, 0)      # Zobel-C hot
    place(f'R{zobel_r_base+1}', 120, y + 4, 0)    # Zobel-R cold
    place(f'C{zobel_c_base+1}', 125, y + 4, 0)    # Zobel-C cold
    
    # === Output TVS diodes ===
    place(f'D{tvs_in_base+2}', 135, y - 3, 90)     # Hot output TVS
    place(f'D{tvs_in_base+3}', 135, y + 3, 90)     # Cold output TVS

    # === Output XLR (right edge) ===
    xlr_out_ref = f'J{ch + 6}'
    place(xlr_out_ref, 150, y, 0)


# Place all 6 channels
for ch in range(1, 7):
    y_center = 50 + (ch - 1) * 20
    place_channel(ch, y_center)

# ============================================================
# Summary & output
# ============================================================
placed_refs = {p['ref'] for p in placements}
all_refs = {c['ref'] for c in components}
unplaced = all_refs - placed_refs

print(f"Placed: {len(placements)} components")
print(f"Unplaced: {len(unplaced)}: {sorted(unplaced)}")

# Write placement file
with open('pcb_placements.json', 'w') as f:
    json.dump(placements, f, indent=2)

print(f"\nPlacement data written to pcb_placements.json")
