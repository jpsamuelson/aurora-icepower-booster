#!/usr/bin/env python3
"""
Fix placement v6: Resolve remaining 75 DRC errors.

Remaining issues:
A) R_fb_out/R_fb_inv overlap Stage2 U2-U7 (18 errors)
   → Move to x=58-62, away from Stage2 courtyard (left edge ~x=66)
B) PSU: U14/U15 overlap FB1/FB2/caps (30 errors)
   → Spread PSU components wider, U14/U15 to x=125
C) J1 area: R106/C77/D1/C80 near J1 (5 errors)
   → Move R106, C77 away from J1
D) C25 ↔ SW3 (CH2 DIP switch) (1 error)
   → Move C25 further from SW3
"""
import re
import sys

PCB_PATH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

CH_Y = {1: 44.45, 2: 72.14, 3: 99.82, 4: 127.64, 5: 155.45, 6: 183.22}

FIXED_REFS = {
    'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8',
    'J9', 'J10', 'J11', 'J12', 'J13', 'J14',
    'SW1', 'MH1', 'MH2', 'MH3', 'MH4',
}

sys.path.insert(0, '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/scripts/pcb')
from place_corrected import CHANNEL_REFS

corrections = {}

# === FIX A: Inter-stage feedback Rs ===
# Stage2 (U2-U7) courtyard left edge ≈ x=66.
# Move all 4 inter-stage roles to x=58-62 with clear separation.
for ch in range(1, 7):
    yc = CH_Y[ch]
    y_hot = yc - 3.5
    y_cold = yc + 3.5

    # R_inter1 (GAIN_FB↔GAIN_OUT) at x=58, hot side
    corrections[CHANNEL_REFS['R_inter1'][ch-1]] = (58, y_hot, 0)
    # R_inter2 (SUMNODE↔RX_OUT) at x=58, cold side
    corrections[CHANNEL_REFS['R_inter2'][ch-1]] = (58, y_cold, 0)
    # R_fb_inv (INV_IN↔RX_OUT) at x=62, center-hot (rotated for compact)
    corrections[CHANNEL_REFS['R_fb_inv'][ch-1]] = (62, yc - 1.5, 90)
    # R_fb_out (GAIN_FB↔OUT_DRIVE) at x=62, center-cold (rotated)
    corrections[CHANNEL_REFS['R_fb_out'][ch-1]] = (62, yc + 1.5, 90)

# === FIX B: PSU area ===
# U1 courtyard: x=[83..115], y=[1..22]
# U14/U15 need to be well outside BOTH U1 and each other.

# U14 ADP7118 LDO +12V → x=126 (far right, clear of U1)
corrections['U14'] = (126, 8, 0)
corrections['C22'] = (122, 6, 90)     # Input cap, left of U14
corrections['C20'] = (130, 6, 90)     # Output cap, right of U14
corrections['C16'] = (130, 10, 90)    # Bypass cap, right of U14

# U15 ADP7182 LDO -12V → x=126
corrections['U15'] = (126, 24, 0)
corrections['C21'] = (122, 22, 90)    # Input cap
corrections['C79'] = (130, 22, 90)    # Output cap
corrections['C81'] = (130, 26, 90)    # Bypass
corrections['C78'] = (122, 26, 90)    # HF bypass

# FB1/FB2 just outside U1 courtyard (x=117)
corrections['FB1'] = (118, 10, 0)
corrections['FB2'] = (118, 26, 0)

# TEL5 caps: C17/C19 were inside U1 courtyard → move to x<83
corrections['C14'] = (80, 8, 90)      # +12V_RAW bulk, left of U1
corrections['C15'] = (80, 28, 90)     # -12V_RAW bulk, below U1
corrections['C17'] = (78, 12, 90)     # +12V_RAW bypass
corrections['C18'] = (78, 28, 90)     # -12V_RAW bypass (was already outside)
corrections['C19'] = (76, 8, 90)      # Additional cap
corrections['C23'] = (76, 28, 90)     # Additional cap (was already outside)
corrections['C77'] = (74, 8, 90)      # HF bypass (far left, away from J1)

# === FIX C: J1 area ===
# J1 at (70.87, 10.83), barrel jack with large courtyard
# Move R106/R107/Q1 further from J1
corrections['Q1']   = (72, 16, 0)     # was (76, 14) — still overlaps, move down
corrections['R106'] = (72, 20, 0)     # was (76, 10) — move below J1 area
corrections['R107'] = (76, 20, 0)     # Group with Q1
corrections['R56']  = (72, 24, 0)     # EN_CTRL, group with Q1/R106
corrections['R57']  = (76, 24, 0)     # EN_CTRL

# D1 and C80 — move above board center, away from J1
corrections['D1']  = (74, 4, 0)       # Protection diode, top edge
corrections['C80'] = (78, 4, 90)      # Input cap

# === FIX D: C25 ↔ SW3 ===
# C25 at (57, 58), SW3 (CH2 DIP) at (55, 56.14) — too close
corrections['C25'] = (57, 54, 90)     # Move above, more clearance from SW3


def apply_corrections(pcb_content, corrections):
    changes = 0
    failed = []

    for ref, (x, y, rot) in corrections.items():
        if ref in FIXED_REFS:
            continue

        ref_pattern = rf'(\(property "Reference" "{re.escape(ref)}")'
        ref_matches = list(re.finditer(ref_pattern, pcb_content))

        if not ref_matches:
            failed.append(ref)
            continue

        for match in ref_matches:
            pos = match.start()
            fp_start = pcb_content.rfind('(footprint "', 0, pos)
            if fp_start == -1:
                failed.append(ref)
                continue

            fp_region = pcb_content[fp_start:pos]
            at_pat = r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)'
            at_match = re.search(at_pat, fp_region)

            if not at_match:
                failed.append(ref)
                continue

            abs_start = fp_start + at_match.start()
            abs_end = fp_start + at_match.end()

            if rot == 0:
                new_at = f'(at {x} {y})'
            else:
                new_at = f'(at {x} {y} {rot})'

            pcb_content = pcb_content[:abs_start] + new_at + pcb_content[abs_end:]
            changes += 1
            break

    return pcb_content, changes, failed


def main():
    print("=" * 70)
    print("Fix Placement v6 — Resolve remaining 75 DRC errors")
    print("=" * 70)

    with open(PCB_PATH) as f:
        content = f.read()
    print(f"Read: {len(content):,} chars")

    print(f"\nApplying {len(corrections)} corrections...")
    content, changes, failed = apply_corrections(content, corrections)
    print(f"  Applied: {changes}")
    if failed:
        print(f"  Failed: {failed}")

    # Bracket balance
    depth = 0
    for c in content:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
    assert depth == 0, f"Bracket imbalance: {depth}"
    print(f"Bracket balance: OK")

    with open(PCB_PATH, 'w') as f:
        f.write(content)
    print(f"Written: {len(content):,} chars")
    print("\n✓ Fix v6 applied.")


if __name__ == '__main__':
    main()
