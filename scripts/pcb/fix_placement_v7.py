#!/usr/bin/env python3
"""
Fix placement v7: Resolve remaining 42 DRC errors.

Issues and fixes:
A) R_inter1/R_inter2 at x=58 overlap Stage1 (courtyard extends to x≈58)
   → Move to x=62, y=yc±7 (above/below signal path, clear of stage1)
B) R_fb_inv/R_fb_out at (62, yc±1.5) too close to each other (3mm, need 5mm)
   → Change to y=yc±2.5 with 90° rotation
C) U14 courtyard overlaps C16/C20/C22 — caps too close
   → U14 to x=128, spread caps wider
D) J1 area: C19/C77 in J1 courtyard, D1 overlap
   → Move C19/C77 far from J1
E) C25 ↔ SW3 still overlapping
   → Move C25 to less crowded area
"""
import re, sys

PCB_PATH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"
CH_Y = {1: 44.45, 2: 72.14, 3: 99.82, 4: 127.64, 5: 155.45, 6: 183.22}

sys.path.insert(0, '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/scripts/pcb')
from place_corrected import CHANNEL_REFS

corrections = {}

# === FIX A+B: Inter-stage area ===
# Stage1 at (55, yc) — courtyard right edge ≈ x=58
# Stage2 at (69, yc) — courtyard left edge ≈ x=66
# Available space: x=60-64
#
# Strategy: All 4 roles at x=62, vertically stacked:
#   R_inter1 at (62, yc-7, 0)  — above hot path
#   R_fb_inv at (62, yc-2.5, 90) — center-hot (compact x)
#   R_fb_out at (62, yc+2.5, 90) — center-cold (compact x)
#   R_inter2 at (62, yc+7, 0)  — below cold path
for ch in range(1, 7):
    yc = CH_Y[ch]
    corrections[CHANNEL_REFS['R_inter1'][ch-1]] = (62, yc - 7, 0)
    corrections[CHANNEL_REFS['R_fb_inv'][ch-1]] = (62, yc - 2.5, 90)
    corrections[CHANNEL_REFS['R_fb_out'][ch-1]] = (62, yc + 2.5, 90)
    corrections[CHANNEL_REFS['R_inter2'][ch-1]] = (62, yc + 7, 0)

# === FIX C: PSU U14/U15 area ===
# U14 (SOIC-8) courtyard ≈ 6.5mm wide → at x=128: courtyard x=124.75-131.25
corrections['U14'] = (128, 8, 0)
corrections['C22'] = (121, 6, 90)     # Input cap — outside courtyard left
corrections['C20'] = (135, 6, 90)     # Output cap — outside courtyard right
corrections['C16'] = (135, 10, 90)    # Bypass — outside courtyard right

# U15 symmetric
corrections['U15'] = (128, 24, 0)
corrections['C21'] = (121, 22, 90)
corrections['C79'] = (135, 22, 90)
corrections['C81'] = (135, 26, 90)
corrections['C78'] = (121, 28, 90)    # Far from U15

# === FIX D: J1 area ===
# J1 at (70.87, 10.83) — barrel jack, large courtyard extending ≈ 10-12mm
# Move C19/C77 far from J1
corrections['C19'] = (74, 28, 90)     # Move below J1, outside its courtyard
corrections['C77'] = (72, 4, 90)      # Move above J1
corrections['D1']  = (72, 28, 0)      # Move D1 far below (was (74, 4))
corrections['C80'] = (76, 28, 90)     # Near D1

# === FIX E: C25 ↔ SW3 ===
# SW3 at (55, 56.14) — large DIP switch
# C25 currently at (57, 54)
corrections['C25'] = (50, 58, 90)     # Move left, clear of SW3


def apply_corrections(pcb_content, corrections):
    changes = 0
    failed = []
    for ref, (x, y, rot) in corrections.items():
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
            new_at = f'(at {x} {y} {rot})' if rot else f'(at {x} {y})'
            pcb_content = pcb_content[:abs_start] + new_at + pcb_content[abs_end:]
            changes += 1
            break
    return pcb_content, changes, failed


def main():
    print("Fix v7 — Resolve remaining 42 DRC errors")
    with open(PCB_PATH) as f:
        content = f.read()
    print(f"Read: {len(content):,} chars")
    print(f"Applying {len(corrections)} corrections...")
    content, changes, failed = apply_corrections(content, corrections)
    print(f"  Applied: {changes}")
    if failed:
        print(f"  Failed: {failed}")
    depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
    assert depth == 0, f"Bracket imbalance: {depth}"
    print("Bracket balance: OK")
    with open(PCB_PATH, 'w') as f:
        f.write(content)
    print(f"Written: {len(content):,} chars")

if __name__ == '__main__':
    main()
