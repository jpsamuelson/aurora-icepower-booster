#!/usr/bin/env python3
"""
Corrected Plan B Placement — Netlist-derived ref→role→channel mapping.

This replaces fix_placement_v4.py with a COMPLETE corrected placement based on
the actual netlist pin connections, not guessed sequential numbering.

Key corrections vs. original place_plan_b.py:
1. U_stage1/U_stage2 SWAPPED (U8-U13 is stage1, U2-U7 is stage2)
2. TVS hot/cold IN and OUT roles corrected (D8=hot_in CH1, not D10)
3. EMI R hot/cold swapped (R94=hot CH1, not R95)
4. Diff R roles corrected (R2=diff_hot CH1, R3=inv_in CH1)
5. R64-R69 → inter-stage (GAIN_FB↔GAIN_OUT), NOT output
6. R70-R75 → feedback (GAIN_FB↔OUT_DRIVE), NOT output
7. R20-R25 → feedback (INV_IN↔RX_OUT), was unassigned
8. R56/R57 → PSU (EN_CTRL), NOT channel output
9. Bypass caps V+/V- label corrected (C2=V+, C8=V-)
10. Gain resistors re-mapped from netlist
"""
import re
import sys

PCB_PATH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

# ============================================================
# Channel Y centers (from fixed XLR connectors)
# ============================================================
CH_Y = {
    1: 44.45,
    2: 72.14,
    3: 99.82,
    4: 127.64,
    5: 155.45,
    6: 183.22,
}

# ============================================================
# CORRECTED Channel Refs — derived from netlist analysis
# Each list: [CH1, CH2, CH3, CH4, CH5, CH6]
# ============================================================
CHANNEL_REFS = {
    # Op-amps (SWAPPED vs original!)
    'U_stage1': ['U8', 'U9', 'U10', 'U11', 'U12', 'U13'],   # INV_IN, BUF_DRIVE
    'U_stage2': ['U2', 'U3', 'U4', 'U5', 'U6', 'U7'],       # GAIN_FB, OUT_DRIVE

    # DIP switches (unchanged)
    'SW': ['SW2', 'SW3', 'SW4', 'SW5', 'SW6', 'SW7'],

    # Mute MOSFETs (unchanged)
    'Q_mute': ['Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'],

    # === INPUT SECTION ===
    # TVS input — HOT: GND↔HOT_RAW
    'D_tvs_hot_in':  ['D8', 'D11', 'D14', 'D17', 'D20', 'D23'],
    # TVS input — COLD: GND↔COLD_RAW
    'D_tvs_cold_in': ['D10', 'D13', 'D16', 'D19', 'D22', 'D25'],

    # EMI resistors — HOT: HOT_RAW↔EMI_HOT
    'R_emi_hot':  ['R94', 'R96', 'R98', 'R100', 'R102', 'R104'],
    # EMI resistors — COLD: COLD_RAW↔EMI_COLD
    'R_emi_cold': ['R95', 'R97', 'R99', 'R101', 'R103', 'R105'],

    # EMI caps — HOT: EMI_HOT↔GND
    'C_emi_hot':  ['C50', 'C52', 'C54', 'C56', 'C58', 'C60'],
    # EMI caps — COLD: EMI_COLD↔GND
    'C_emi_cold': ['C51', 'C53', 'C55', 'C57', 'C59', 'C61'],

    # Coupling caps — HOT: EMI_HOT↔HOT_IN
    'C_couple_hot':  ['C62', 'C64', 'C66', 'C68', 'C70', 'C72'],
    # Coupling caps — COLD: EMI_COLD↔COLD_IN
    'C_couple_cold': ['C63', 'C65', 'C67', 'C69', 'C71', 'C73'],

    # Differential input — HOT: GND↔HOT_IN
    'R_diff_hot': ['R2', 'R4', 'R6', 'R8', 'R10', 'R12'],
    # Differential input — INV: INV_IN↔COLD_IN
    'R_inv_in':   ['R3', 'R5', 'R7', 'R9', 'R11', 'R13'],
    # Inverting input bias: GND↔INV_IN
    'R_bias_inv': ['R14', 'R15', 'R16', 'R17', 'R18', 'R19'],

    # === STAGE 1 BYPASS CAPS (V+ and V- near stage1 op-amp) ===
    # V+ bypass (C2-C7 connect to /V+)
    'C_byp1_vp': ['C2', 'C3', 'C4', 'C5', 'C6', 'C7'],
    # V- bypass (C8-C13 connect to /V-)
    'C_byp1_vn': ['C8', 'C9', 'C10', 'C11', 'C12', 'C13'],

    # === GAIN-INSEL ===
    # Gain resistors: SW_OUT_n↔SUMNODE
    'R_gain1': ['R27', 'R31', 'R35', 'R39', 'R43', 'R47'],
    'R_gain2': ['R28', 'R32', 'R36', 'R40', 'R44', 'R48'],
    'R_gain3': ['R29', 'R33', 'R37', 'R41', 'R45', 'R49'],
    # Sum resistor: GAIN_FB↔INV_IN
    'R_sum':   ['R50', 'R51', 'R52', 'R53', 'R54', 'R55'],

    # === INTER-STAGE ===
    # Inter-stage 1: GAIN_FB↔GAIN_OUT
    'R_inter1': ['R64', 'R65', 'R66', 'R67', 'R68', 'R69'],
    # Inter-stage 2: SUMNODE↔RX_OUT
    'R_inter2': ['R26', 'R30', 'R34', 'R38', 'R42', 'R46'],
    # Feedback output: GAIN_FB↔OUT_DRIVE
    'R_fb_out': ['R70', 'R71', 'R72', 'R73', 'R74', 'R75'],
    # Feedback inverting: INV_IN↔RX_OUT
    'R_fb_inv': ['R20', 'R21', 'R22', 'R23', 'R24', 'R25'],

    # === STAGE 2 BYPASS CAPS ===
    # V+ bypass (C26-C31 connect to /V+)
    'C_byp2_vp': ['C26', 'C27', 'C28', 'C29', 'C30', 'C31'],
    # V- bypass (C32-C34, C74-C76 connect to /V-)
    'C_byp2_vn': ['C32', 'C33', 'C34', 'C74', 'C75', 'C76'],

    # === OUTPUT SECTION ===
    # Output drive hot: OUT_DRIVE↔OUT_HOT
    'R_out_hot':  ['R76', 'R77', 'R78', 'R79', 'R80', 'R81'],
    # Output drive cold: BUF_DRIVE↔OUT_COLD
    'R_out_cold': ['R58', 'R59', 'R60', 'R61', 'R62', 'R63'],
    # Output protection hot: OUT_HOT↔OUT_PROT_HOT
    'R_prot_hot':  ['R82', 'R83', 'R84', 'R85', 'R86', 'R87'],
    # Output protection cold: OUT_COLD↔OUT_PROT_COLD
    'R_prot_cold': ['R88', 'R89', 'R90', 'R91', 'R92', 'R93'],

    # Output caps
    'C_out1': ['C38', 'C39', 'C40', 'C41', 'C42', 'C43'],
    'C_out2': ['C44', 'C45', 'C46', 'C47', 'C48', 'C49'],

    # Mute drive resistors (R108→Q2=CH1, R109→Q3=CH2, etc.)
    'R_mute': ['R108', 'R109', 'R110', 'R111', 'R112', 'R113'],

    # === OUTPUT TVS ===
    # TVS output — HOT: GND↔OUT_HOT (or OUT_PROT_HOT)
    'D_tvs_hot_out':  ['D2', 'D3', 'D4', 'D5', 'D6', 'D7'],
    # TVS output — COLD: GND↔OUT_COLD (or OUT_PROT_COLD)
    'D_tvs_cold_out': ['D9', 'D12', 'D15', 'D18', 'D21', 'D24'],
}


# ============================================================
# Position formulas per channel
# ============================================================
def get_channel_placements():
    """Return dict of ref → (x, y, rotation) for all channel components."""
    placements = {}

    for ch in range(1, 7):
        yc = CH_Y[ch]
        y_hot = yc - 3.5
        y_cold = yc + 3.5
        y_gain_r = yc - 8.0
        y_dip = yc - 12.0

        # --- Input TVS diodes (x=33) ---
        placements[CHANNEL_REFS['D_tvs_hot_in'][ch-1]]  = (33, y_hot, 0)
        placements[CHANNEL_REFS['D_tvs_cold_in'][ch-1]] = (33, y_cold, 0)

        # --- EMI resistors 47Ω (x=37) ---
        placements[CHANNEL_REFS['R_emi_hot'][ch-1]]  = (37, y_hot, 0)
        placements[CHANNEL_REFS['R_emi_cold'][ch-1]] = (37, y_cold, 0)

        # --- EMI caps 100pF (x=41) ---
        placements[CHANNEL_REFS['C_emi_hot'][ch-1]]  = (41, y_hot, 90)
        placements[CHANNEL_REFS['C_emi_cold'][ch-1]] = (41, y_cold, 90)

        # --- Coupling caps 2.2µF (x=45) ---
        placements[CHANNEL_REFS['C_couple_hot'][ch-1]]  = (45, y_hot, 0)
        placements[CHANNEL_REFS['C_couple_cold'][ch-1]] = (45, y_cold, 0)

        # --- Differential input resistors (x=49) ---
        placements[CHANNEL_REFS['R_diff_hot'][ch-1]]  = (49, y_hot - 1.5, 90)
        placements[CHANNEL_REFS['R_inv_in'][ch-1]]    = (49, y_cold + 1.5, 90)
        placements[CHANNEL_REFS['R_bias_inv'][ch-1]]  = (49, yc, 90)

        # --- Stage 1 OpAmp (x=55) ---
        placements[CHANNEL_REFS['U_stage1'][ch-1]] = (55, yc, 0)

        # --- Stage 1 bypass caps (x=52, flanking OpAmp) ---
        placements[CHANNEL_REFS['C_byp1_vp'][ch-1]] = (52, yc - 5.0, 90)
        placements[CHANNEL_REFS['C_byp1_vn'][ch-1]] = (52, yc + 5.0, 90)

        # --- GAIN-INSEL: DIP switch (x=55, y=yc-12) ---
        placements[CHANNEL_REFS['SW'][ch-1]] = (55, y_dip, 0)

        # --- GAIN-INSEL: Gain resistors (x=49..58) ---
        placements[CHANNEL_REFS['R_gain1'][ch-1]] = (49, y_gain_r, 0)
        placements[CHANNEL_REFS['R_gain2'][ch-1]] = (52, y_gain_r, 0)
        placements[CHANNEL_REFS['R_gain3'][ch-1]] = (55, y_gain_r, 0)
        placements[CHANNEL_REFS['R_sum'][ch-1]]   = (58, y_gain_r, 0)

        # --- Inter-stage resistors (x=63) ---
        placements[CHANNEL_REFS['R_inter1'][ch-1]] = (63, y_hot, 0)
        placements[CHANNEL_REFS['R_inter2'][ch-1]] = (63, y_cold, 0)

        # --- Feedback resistors (x=66) ---
        placements[CHANNEL_REFS['R_fb_inv'][ch-1]] = (66, y_hot, 0)
        placements[CHANNEL_REFS['R_fb_out'][ch-1]] = (66, y_cold, 0)

        # --- Stage 2 OpAmp (x=69) ---
        placements[CHANNEL_REFS['U_stage2'][ch-1]] = (69, yc, 0)

        # --- Stage 2 bypass caps (x=72, flanking OpAmp) ---
        placements[CHANNEL_REFS['C_byp2_vp'][ch-1]] = (72, yc - 5.0, 90)
        placements[CHANNEL_REFS['C_byp2_vn'][ch-1]] = (72, yc + 5.0, 90)

        # --- Output resistors (x=76-80) ---
        placements[CHANNEL_REFS['R_prot_hot'][ch-1]]  = (76, y_hot - 1.5, 90)
        placements[CHANNEL_REFS['R_out_hot'][ch-1]]   = (80, y_hot, 0)
        placements[CHANNEL_REFS['R_prot_cold'][ch-1]] = (76, y_cold + 1.5, 90)
        placements[CHANNEL_REFS['R_out_cold'][ch-1]]  = (80, y_cold, 0)

        # --- Output caps (x=84) ---
        placements[CHANNEL_REFS['C_out1'][ch-1]] = (84, y_hot, 0)
        placements[CHANNEL_REFS['C_out2'][ch-1]] = (84, y_cold, 0)

        # --- Mute MOSFET + drive resistor ---
        placements[CHANNEL_REFS['Q_mute'][ch-1]] = (92, yc, 0)
        placements[CHANNEL_REFS['R_mute'][ch-1]] = (96, yc, 0)

        # --- Output TVS diodes (x=101) ---
        placements[CHANNEL_REFS['D_tvs_hot_out'][ch-1]]  = (101, y_hot, 0)
        placements[CHANNEL_REFS['D_tvs_cold_out'][ch-1]] = (101, y_cold, 0)

    return placements


# ============================================================
# PSU components (not per-channel)
# ============================================================
def get_psu_placements():
    """Return dict of ref → (x, y, rotation) for PSU components."""
    placements = {}

    # U1 TEL5-2422 DC-DC converter
    placements['U1'] = (88, 19, 90)

    # Input protection diode
    placements['D1'] = (75, 7, 0)
    placements['C80'] = (78, 7, 90)

    # Remote circuit
    placements['R1'] = (40, 15, 0)
    placements['C1'] = (43, 12, 90)

    # U14 ADP7118 LDO +12V
    placements['U14'] = (108, 8, 0)
    placements['C22'] = (104, 6, 90)
    placements['C20'] = (112, 6, 90)
    placements['C16'] = (112, 10, 90)

    # U15 ADP7182 LDO -12V
    placements['U15'] = (108, 24, 0)
    placements['C21'] = (104, 22, 90)
    placements['C79'] = (112, 22, 90)
    placements['C81'] = (112, 26, 90)
    placements['C78'] = (104, 26, 90)

    # Ferrite beads
    placements['FB1'] = (100, 10, 0)
    placements['FB2'] = (100, 26, 0)

    # TEL5 output caps
    placements['C14'] = (82, 10, 90)
    placements['C15'] = (82, 26, 90)
    placements['C17'] = (86, 10, 90)
    placements['C18'] = (86, 26, 90)
    placements['C19'] = (90, 10, 90)
    placements['C23'] = (90, 26, 90)

    # HF bypass
    placements['C77'] = (94, 10, 90)

    # Mute/enable circuitry
    placements['Q1'] = (64, 14, 0)
    placements['R106'] = (64, 10, 0)
    placements['R107'] = (64, 18, 0)
    # R56/R57 — EN_CTRL resistors (PSU, NOT output!)
    placements['R56'] = (60, 14, 0)
    placements['R57'] = (60, 18, 0)

    # Shared V+/V- bulk caps
    placements['C24'] = (69, 58, 90)
    placements['C25'] = (57, 58, 90)

    # Shared V- bypass caps
    placements['C35'] = (69, 114, 90)
    placements['C36'] = (69, 142, 90)
    placements['C37'] = (69, 170, 90)

    return placements


# ============================================================
# FIXED components — must NOT be moved
# ============================================================
FIXED_REFS = {
    'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8',
    'J9', 'J10', 'J11', 'J12', 'J13', 'J14',
    'SW1', 'MH1', 'MH2', 'MH3', 'MH4',
}


# ============================================================
# Apply placements to PCB
# ============================================================
def strip_routing_and_zones(content):
    """Remove all routing segments, vias, and zone fills."""
    import re
    segment_count = 0
    via_count = 0
    zone_fill_count = 0

    # Remove segments
    result = content
    segments = list(re.finditer(r'\(segment\s', result))
    if segments:
        # Remove each segment block
        new_parts = []
        last_end = 0
        for m in segments:
            start = m.start()
            # Find balanced end
            depth = 0
            i = start
            while i < len(result):
                if result[i] == '(':
                    depth += 1
                elif result[i] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            new_parts.append(result[last_end:start])
            last_end = i + 1
            segment_count += 1
        new_parts.append(result[last_end:])
        result = ''.join(new_parts)

    # Remove vias
    vias = list(re.finditer(r'\(via\s', result))
    if vias:
        new_parts = []
        last_end = 0
        for m in vias:
            start = m.start()
            depth = 0
            i = start
            while i < len(result):
                if result[i] == '(':
                    depth += 1
                elif result[i] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            new_parts.append(result[last_end:start])
            last_end = i + 1
            via_count += 1
        new_parts.append(result[last_end:])
        result = ''.join(new_parts)

    # Remove zone fill polygons (filled_polygon blocks inside zones)
    fills = list(re.finditer(r'\(filled_polygon\s', result))
    if fills:
        new_parts = []
        last_end = 0
        for m in fills:
            start = m.start()
            depth = 0
            i = start
            while i < len(result):
                if result[i] == '(':
                    depth += 1
                elif result[i] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            new_parts.append(result[last_end:start])
            last_end = i + 1
            zone_fill_count += 1
        new_parts.append(result[last_end:])
        result = ''.join(new_parts)

    print(f"  Stripped: {segment_count} segments, {via_count} vias, {zone_fill_count} zone fills")
    return result


def apply_placements(pcb_content, placements):
    """Apply placement changes to PCB content."""
    changes_made = 0
    changes_failed = []

    for ref, (x, y, rot) in placements.items():
        if ref in FIXED_REFS:
            continue

        ref_pattern = rf'(\(property "Reference" "{re.escape(ref)}")'
        ref_matches = list(re.finditer(ref_pattern, pcb_content))

        if not ref_matches:
            changes_failed.append(ref)
            continue

        for match in ref_matches:
            pos = match.start()
            fp_start = pcb_content.rfind('(footprint "', 0, pos)
            if fp_start == -1:
                changes_failed.append(ref)
                continue

            fp_region = pcb_content[fp_start:pos]
            at_pattern = r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)'
            at_match = re.search(at_pattern, fp_region)

            if not at_match:
                changes_failed.append(ref)
                continue

            old_at = at_match.group(0)
            abs_start = fp_start + at_match.start()
            abs_end = fp_start + at_match.end()

            if rot == 0:
                new_at = f'(at {x} {y})'
            else:
                new_at = f'(at {x} {y} {rot})'

            pcb_content = pcb_content[:abs_start] + new_at + pcb_content[abs_end:]
            changes_made += 1
            break

    return pcb_content, changes_made, changes_failed


def main():
    print("=" * 70)
    print("CORRECTED Plan B Placement — Netlist-derived mapping")
    print("=" * 70)

    # Read PCB
    with open(PCB_PATH) as f:
        content = f.read()
    print(f"Read PCB: {len(content):,} chars")

    # Strip routing first
    print("\nStripping old routing...")
    content = strip_routing_and_zones(content)

    # Get all placements
    ch_placements = get_channel_placements()
    psu_placements = get_psu_placements()
    all_placements = {**ch_placements, **psu_placements}

    print(f"\nChannel placements: {len(ch_placements)}")
    print(f"PSU placements: {len(psu_placements)}")
    print(f"Total: {len(all_placements)}")

    # Verify no collisions (same position for different refs)
    pos_map = {}
    for ref, pos in all_placements.items():
        key = (pos[0], pos[1])
        pos_map.setdefault(key, []).append(ref)
    collisions = {k: v for k, v in pos_map.items() if len(v) > 1}
    if collisions:
        print(f"\n*** WARNING: {len(collisions)} position collisions! ***")
        for pos, refs in sorted(collisions.items()):
            print(f"  ({pos[0]}, {pos[1]}): {', '.join(refs)}")
        print("\nAborting to prevent stacked components.")
        sys.exit(1)

    # Apply placements
    print("\nApplying placements...")
    content, changes, failed = apply_placements(content, all_placements)
    print(f"  Applied: {changes} changes")
    if failed:
        print(f"  Failed: {len(failed)} refs: {', '.join(failed)}")

    # Verify bracket balance
    depth = 0
    for c in content:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
    assert depth == 0, f"Bracket imbalance: depth={depth}"
    print(f"\nBracket balance: OK (depth={depth})")

    # Write PCB
    with open(PCB_PATH, 'w') as f:
        f.write(content)
    print(f"Written: {len(content):,} chars to PCB")

    print("\n✓ Corrected placement applied successfully!")
    print("Next: run routing pipeline (route_1 → route_6)")


if __name__ == '__main__':
    main()
