#!/usr/bin/env python3
"""
Fix placement v5: Resolve DRC errors from corrected placement.

Problems and fixes:
1. Gain-Insel: DIP switch too close to gain Rs, Rs at 3mm pitch too tight
   Fix: Move DIP to yc-16, spread gain Rs to 4mm pitch, y=yc-10
2. PSU area: U14, C16, C20, C22, C17, C19, C77, FB1 inside U1 courtyard
   Fix: Move U14+caps to x≥118, C17/C19/C77 to x≤81
3. Inter-stage: R_fb_inv/R_fb_out overlap Stage2 op-amps
   Fix: Move to (64, y_hot±2) instead of (66, y_hot/cold)
4. J1 area: D1 too close to J1 (70.87, 10.83)
   Fix: Move D1 and C80 away
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

# ============================================================
# Corrections
# ============================================================
corrections = {}

# --- FIX 1: Gain-Insel spacing ---
# DIP switch: move from yc-12 to yc-16 (more clearance)
# Gain resistors: 4mm pitch starting at x=48, y=yc-10
# R_sum: at x=60, y=yc-10
from place_corrected import CHANNEL_REFS

for ch in range(1, 7):
    yc = CH_Y[ch]
    y_dip = yc - 16.0
    y_gain = yc - 10.0

    corrections[CHANNEL_REFS['SW'][ch-1]] = (55, y_dip, 0)
    corrections[CHANNEL_REFS['R_gain1'][ch-1]] = (48, y_gain, 0)
    corrections[CHANNEL_REFS['R_gain2'][ch-1]] = (52, y_gain, 0)
    corrections[CHANNEL_REFS['R_gain3'][ch-1]] = (56, y_gain, 0)
    corrections[CHANNEL_REFS['R_sum'][ch-1]]   = (60, y_gain, 0)

# --- FIX 2: Inter-stage feedback Rs overlap Stage2 ---
# Move R_fb_inv from (66, y_hot) to (64, yc-2)
# Move R_fb_out from (66, y_cold) to (64, yc+2)
# This avoids stage2 courtyard at (69, yc)
for ch in range(1, 7):
    yc = CH_Y[ch]
    corrections[CHANNEL_REFS['R_fb_inv'][ch-1]] = (64, yc - 2, 0)
    corrections[CHANNEL_REFS['R_fb_out'][ch-1]] = (64, yc + 2, 0)

# Also move R_inter1 from (63, y_hot) to (62, y_hot) for more gapfor ch in range(1, 7):
    yc = CH_Y[ch]
    y_hot = yc - 3.5
    y_cold = yc + 3.5
    corrections[CHANNEL_REFS['R_inter1'][ch-1]] = (62, y_hot, 0)
    corrections[CHANNEL_REFS['R_inter2'][ch-1]] = (62, y_cold, 0)

# --- FIX 3: PSU — move out of U1 courtyard ---
# U1 courtyard: x=[83.17..115.43], y=[0.97..21.79]
# Move U14 + caps to x ≥ 118
corrections['U14'] = (120, 8, 0)
corrections['C22'] = (118, 6, 90)
corrections['C20'] = (124, 6, 90)
corrections['C16'] = (124, 10, 90)

# U15 + caps
corrections['U15'] = (120, 24, 0)
corrections['C21'] = (118, 22, 90)
corrections['C79'] = (124, 22, 90)
corrections['C81'] = (124, 26, 90)
corrections['C78'] = (118, 26, 90)

# FB1, FB2 — move to x=117
corrections['FB1'] = (117, 10, 0)
corrections['FB2'] = (117, 26, 0)

# TEL5 caps inside U1 courtyard — move left (x < 83)
corrections['C17'] = (81, 14, 90)    # was (86, 10)
corrections['C19'] = (81, 18, 90)    # was (90, 10)
corrections['C23'] = (81, 26, 90)    # was (90, 26) — already outside but group logically
corrections['C77'] = (78, 10, 90)    # was (94, 10) — move far left

# Q1 + R106/R107 — move out of U1 courtyard
corrections['Q1']   = (76, 14, 0)    # was (64, 14) — inside courtyard? Actually x=64 < 83 so OK
corrections['R106'] = (76, 10, 0)    # was (64, 10) — OK, but move near Q1 for grouping
corrections['R107'] = (76, 18, 0)    # was (64, 18) — OK

# R56/R57 EN_CTRL near Q1
corrections['R56'] = (72, 14, 0)    # was (60, 14)
corrections['R57'] = (72, 18, 0)    # was (60, 18)

# --- FIX 4: J1 area — D1 and C80 away from J1 ---
# J1 at (70.87, 10.83)
corrections['D1']  = (78, 4, 0)     # was (75, 7) — move right and up
corrections['C80'] = (82, 4, 90)    # was (78, 7) — move right and up


# ============================================================
# Apply corrections
# ============================================================
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


def strip_routing(content):
    """Remove segments, vias, zone fills."""
    seg_count = 0
    via_count = 0
    fill_count = 0

    for tag in ['segment', 'via']:
        parts = []
        last_end = 0
        for m in re.finditer(rf'\({tag}\s', content):
            start = m.start()
            depth = 0
            i = start
            while i < len(content):
                if content[i] == '(':
                    depth += 1
                elif content[i] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            parts.append(content[last_end:start])
            last_end = i + 1
            if tag == 'segment':
                seg_count += 1
            else:
                via_count += 1
        parts.append(content[last_end:])
        content = ''.join(parts)

    # Zone fills
    parts = []
    last_end = 0
    for m in re.finditer(r'\(filled_polygon\s', content):
        start = m.start()
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        parts.append(content[last_end:start])
        last_end = i + 1
        fill_count += 1
    parts.append(content[last_end:])
    content = ''.join(parts)

    print(f"  Stripped: {seg_count} segments, {via_count} vias, {fill_count} zone fills")
    return content


def main():
    print("=" * 70)
    print("Fix Placement v5 — Resolve DRC courtyard/short errors")
    print("=" * 70)

    with open(PCB_PATH) as f:
        content = f.read()
    print(f"Read: {len(content):,} chars")

    # Strip routing
    print("Stripping routing...")
    content = strip_routing(content)

    # Apply corrections
    print(f"\nApplying {len(corrections)} corrections...")
    content, changes, failed = apply_corrections(content, corrections)
    print(f"  Applied: {changes}")
    if failed:
        print(f"  Failed: {failed}")

    # Check bracket balance
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
    print("\n✓ Fix v5 applied. Re-run routing pipeline.")


if __name__ == '__main__':
    main()
