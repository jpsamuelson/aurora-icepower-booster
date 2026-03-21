#!/usr/bin/env python3
"""
Fix placement v3: Resolve ALL 35 DRC errors.

U1 courtyard (board coords): x=[83.17..115.43] y=[0.97..21.79]
J1 courtyard (board coords): x=[64.12..75.62] y=[-3.17..12.83]

Strategy:
  LEFT of U1 (x < 83): TEL5 input caps, D1, C80
  BELOW U1 (y > 22, x = 84-114): TEL5 output + ferrites + LDO area
  R_out2/R_out4: increase spacing from 3mm to 4mm
"""
import re
import sys

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

CH_Y = {1: 44.45, 2: 72.14, 3: 99.82, 4: 127.64, 5: 155.45, 6: 183.22}

FIXED_REFS = {
    'J1','J2','J3','J4','J5','J6','J7','J8',
    'J9','J10','J11','J12','J13','J14','SW1',
    'MH1','MH2','MH3','MH4',
}

# R_out2 (hot) and R_out4 (cold) per channel
R_OUT2 = ['R70', 'R71', 'R72', 'R73', 'R74', 'R75']  # CH1..CH6
R_OUT4 = ['R82', 'R83', 'R84', 'R85', 'R86', 'R87']  # CH1..CH6


def build_corrections():
    fixes = {}

    # -- PSU LEFT COLUMN (x < 83) --
    # TEL5 input caps + protection (near J1 and U1 input pins)
    fixes['C14'] = (78, 4, 90)       # +12V_RAW bulk -- above J1
    fixes['C17'] = (80, 10, 90)      # +12V_RAW bypass (C_1210) -- left of U1
    fixes['C15'] = (78, 32, 90)      # -12V_RAW bulk -- below U1 left
    fixes['C18'] = (80, 28, 90)      # -12V_RAW bypass -- below U1 left
    fixes['D1']  = (68, 16, 0)       # TVS protection -- below J1
    fixes['C80'] = (68, 22, 90)      # Input filter -- below D1

    # -- PSU BELOW U1 -- ROW 1 (y=24, just below U1 courtyard) --
    fixes['FB1'] = (86, 24, 0)       # +12V ferrite bead
    fixes['C19'] = (90, 24, 90)      # +12V post-ferrite cap
    fixes['C22'] = (94, 24, 90)      # U14 input cap
    fixes['C20'] = (99, 24, 0)       # U14 output cap (C_1210 at 0deg)
    fixes['C16'] = (104, 24, 0)      # U14 output bulk (C_1210 at 0deg)
    fixes['C79'] = (112, 24, 90)     # U15 output cap

    # -- PSU BELOW U1 -- ROW 2 (y=28-30, LDOs + ferrites) --
    fixes['FB2'] = (86, 28, 0)       # -12V ferrite bead
    fixes['C23'] = (90, 28, 90)      # -12V post-ferrite cap
    fixes['C21'] = (94, 30, 90)      # U15 input cap (C_1210 at 90deg)
    fixes['U14'] = (100, 30, 0)      # LDO +V (SOIC-8)
    fixes['U15'] = (108, 30, 0)      # LDO -V (SOT-23-5)
    fixes['C78'] = (112, 28, 90)     # U15 NR cap

    # -- PSU BELOW U1 -- ROW 3 (y=32+) --
    fixes['C77'] = (90, 32, 90)      # HF bypass cap
    fixes['C81'] = (112, 32, 90)     # U15 output cap2 (C_0402)

    # -- R_out2/R_out4: increase spacing from +/-1.5mm to +/-2mm --
    for ch in range(1, 7):
        yc = CH_Y[ch]
        fixes[R_OUT2[ch-1]] = (76, round(yc - 2, 2), 90)   # was yc - 1.5
        fixes[R_OUT4[ch-1]] = (76, round(yc + 2, 2), 90)   # was yc + 1.5

    return fixes


def strip_routing(content):
    """Remove all routing segments and vias."""
    lines = content.split('\n')
    result = []
    i = 0
    removed = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if (stripped == '(segment' or stripped.startswith('(segment ') or
            stripped == '(via' or stripped.startswith('(via ')):
            if lines[i].startswith('\t') and not lines[i].startswith('\t\t'):
                depth = 0
                while i < len(lines):
                    for ch in lines[i]:
                        if ch == '(': depth += 1
                        elif ch == ')': depth -= 1
                    if depth <= 0:
                        i += 1
                        break
                    i += 1
                removed += 1
                continue
        result.append(lines[i])
        i += 1
    return '\n'.join(result), removed


def strip_zone_fills(content):
    """Remove all zone fill polygons."""
    lines = content.split('\n')
    result = []
    i = 0
    removed = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith('(filled_polygon'):
            depth = 0
            while i < len(lines):
                for ch in lines[i]:
                    if ch == '(': depth += 1
                    elif ch == ')': depth -= 1
                if depth <= 0:
                    i += 1
                    break
                i += 1
            removed += 1
            continue
        result.append(lines[i])
        i += 1
    return '\n'.join(result), removed


def apply_fixes(content, fixes):
    """Move components to new positions."""
    moved = 0
    failed = []
    for ref, (x, y, rot) in fixes.items():
        if ref in FIXED_REFS:
            failed.append(f"{ref} (FIXED)")
            continue
        pat = rf'\(property "Reference" "{re.escape(ref)}"'
        m = re.search(pat, content)
        if not m:
            failed.append(f"{ref} (not found)")
            continue
        fp_start = content.rfind('(footprint "', 0, m.start())
        if fp_start == -1:
            failed.append(f"{ref} (no footprint)")
            continue
        region = content[fp_start:m.start()]
        at_match = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)', region)
        if not at_match:
            failed.append(f"{ref} (no at)")
            continue
        at_start = fp_start + at_match.start()
        at_end = fp_start + at_match.end()
        if rot == 0:
            new_at = f'(at {x} {y})'
        else:
            new_at = f'(at {x} {y} {rot})'
        content = content[:at_start] + new_at + content[at_end:]
        moved += 1
    return content, moved, failed


def main():
    with open(PCB) as f:
        content = f.read()
    print(f"PCB loaded: {len(content):,} chars")

    # Strip routing (segments + vias)
    content, n_routes = strip_routing(content)
    print(f"Stripped routing: {n_routes} elements")

    # Strip zone fills
    content, n_fills = strip_zone_fills(content)
    print(f"Stripped zone fills: {n_fills} elements")

    # Apply placement corrections
    fixes = build_corrections()
    print(f"\nApplying {len(fixes)} corrections:")
    content, moved, failed = apply_fixes(content, fixes)
    print(f"  Moved: {moved}")
    if failed:
        print(f"  Failed: {failed}")
        if any('not found' in f for f in failed):
            print("ERROR: Some refs not found!")
            sys.exit(1)

    # Verify bracket balance
    depth = 0
    for ch in content:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
    if depth != 0:
        print(f"ERROR: Bracket balance = {depth}")
        sys.exit(1)
    print(f"\nBracket balance: OK")

    with open(PCB, 'w') as f:
        f.write(content)
    print(f"PCB written: {len(content):,} chars")
    print("\n==> Placement v3 complete -- next: run routing pipeline")


if __name__ == '__main__':
    main()
