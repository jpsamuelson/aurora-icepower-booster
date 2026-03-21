#!/usr/bin/env python3
"""
Fix v8: Final placement corrections for remaining 27 DRC errors.
"""
import re, sys

PCB_PATH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"
CH_Y = {1: 44.45, 2: 72.14, 3: 99.82, 4: 127.64, 5: 155.45, 6: 183.22}

sys.path.insert(0, '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/scripts/pcb')
from place_corrected import CHANNEL_REFS

corrections = {}

# === FIX: R_inter2 overlap with adjacent channel DIP switches ===
# DIP switch courtyard extends to ~x=60 (right edge)
# Move R_inter2 from (62, yc+7) to (64, yc+7) for more gap
for ch in range(1, 7):
    yc = CH_Y[ch]
    corrections[CHANNEL_REFS['R_inter2'][ch-1]] = (64, yc + 7, 0)
    # Also move R_inter1 to same x for symmetry
    corrections[CHANNEL_REFS['R_inter1'][ch-1]] = (64, yc - 7, 0)

# === FIX: PSU caps in the y≈28 area ===
# Spread D1, C19, C23, C80 (currently all stacked near y=28)
# Also fix C16/C20 (both at x=135, 4mm apart)

# J1 at (70.87, 10.83) — courtyard roughly (65, 5) to (77, 17)
# U1 courtyard: x=[83..115], y=[1..22]

# Input protection group — ABOVE and LEFT of J1
corrections['D1']  = (62, 5, 0)       # Protection diode, top-left
corrections['C80'] = (66, 5, 90)      # Input cap near D1

# PSU caps — spread along bottom of PSU area
corrections['C19'] = (80, 24, 90)     # TEL5 cap, below U1 (was inside courtyard)
corrections['C23'] = (80, 30, 90)     # TEL5 cap, well below U1
corrections['C77'] = (82, 32, 90)     # HF bypass, bottom of PSU area

# Reorganize C17 to avoid J1 courtyard
corrections['C17'] = (82, 12, 90)     # was (78, 12) inside J1 courtyard

# C16/C20 — separate more (currently both near x=135)
corrections['C16'] = (132, 12, 90)    # was (135, 10) — move left, more y sep
corrections['C20'] = (132, 4, 90)     # was (135, 6) — move left, more y sep

# === FIX: C25 ↔ SW3 ===
# SW3 (DIP CH2) at (55, 56.14). C25 at (50, 58) still overlaps
# Move C25 further from ALL DIP switches
corrections['C25'] = (46, 58, 90)     # x=46, well left of any DIP switch


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


with open(PCB_PATH) as f:
    content = f.read()
print(f"Read: {len(content):,} chars, applying {len(corrections)} corrections...")
content, changes, failed = apply_corrections(content, corrections)
print(f"Applied: {changes}")
if failed:
    print(f"Failed: {failed}")
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
assert depth == 0
with open(PCB_PATH, 'w') as f:
    f.write(content)
print(f"Written: {len(content):,} chars")
