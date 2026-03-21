#!/usr/bin/env python3
"""
Fix Plan B placement issues identified by DRC:
1. Gain-Insel: DIP too close to gain Rs, Rs too close to each other (3mm pitch → 4mm)
2. Output Rs: vertical pairs too close (3mm → 4mm)  
3. PSU: caps inside U1 DIP-24 courtyard
4. D1/C80/R106: overlapping J1 barrel jack
5. C24/C25: overlapping DIP switches
Also strips existing routing first.
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

CH_Y = {1: 44.45, 2: 72.14, 3: 99.82, 4: 127.64, 5: 155.45, 6: 183.22}

# Per-channel refs (same mapping as place_plan_b.py)
CHANNEL_REFS = {
    'SW':       ['SW2', 'SW3', 'SW4', 'SW5', 'SW6', 'SW7'],
    'R_gain1':  ['R27', 'R30', 'R33', 'R36', 'R39', 'R42'],
    'R_gain2':  ['R28', 'R31', 'R34', 'R37', 'R40', 'R43'],
    'R_gain3':  ['R29', 'R32', 'R35', 'R38', 'R41', 'R44'],
    'R_sum':    ['R50', 'R51', 'R52', 'R53', 'R54', 'R55'],
    'R_out1':   ['R64', 'R65', 'R66', 'R67', 'R68', 'R69'],
    'R_out2':   ['R70', 'R71', 'R72', 'R73', 'R74', 'R75'],
    'R_out4':   ['R82', 'R83', 'R84', 'R85', 'R86', 'R87'],
    'R_out5':   ['R88', 'R89', 'R90', 'R91', 'R92', 'R93'],
}

FIXED_REFS = {
    'J1','J2','J3','J4','J5','J6','J7','J8',
    'J9','J10','J11','J12','J13','J14','SW1',
    'MH1','MH2','MH3','MH4',
}


def build_corrections():
    """Build dict of ref → (x, y, rotation) for all components that need moving."""
    fixes = {}

    # ── Channel fixes ──
    for ch in range(1, 7):
        yc = CH_Y[ch]
        y_hot = yc - 3.5
        y_cold = yc + 3.5

        # FIX 1: Gain-Insel — DIP moved higher, Rs spread to 4mm pitch
        # DIP: y_ch-12 → y_ch-16 (6mm from gain Rs instead of 4mm)
        fixes[CHANNEL_REFS['SW'][ch-1]] = (54, yc - 16, 0)
        
        # Gain Rs: y_ch-8 → y_ch-9, X pitch 3mm → 4mm
        fixes[CHANNEL_REFS['R_gain1'][ch-1]] = (48, yc - 9, 0)
        fixes[CHANNEL_REFS['R_gain2'][ch-1]] = (52, yc - 9, 0)
        fixes[CHANNEL_REFS['R_gain3'][ch-1]] = (56, yc - 9, 0)
        fixes[CHANNEL_REFS['R_sum'][ch-1]]   = (60, yc - 9, 0)

        # FIX 2: Output Rs — vertical spacing 3mm → 4mm (90° rotation)
        fixes[CHANNEL_REFS['R_out1'][ch-1]] = (76, y_hot - 2, 90)
        fixes[CHANNEL_REFS['R_out2'][ch-1]] = (76, y_hot + 2, 90)
        fixes[CHANNEL_REFS['R_out4'][ch-1]] = (76, y_cold - 2, 90)
        fixes[CHANNEL_REFS['R_out5'][ch-1]] = (76, y_cold + 2, 90)

    # ── PSU fixes ──
    # FIX 3: Move TEL5 caps OUTSIDE U1 courtyard (U1 at 88,19,90° → courtyard ~x=79..97, y=4..34)
    
    # Left of U1 (x=74-78)
    fixes['C14'] = (76, 10, 90)     # +12V_RAW bulk
    fixes['C15'] = (76, 28, 90)     # -12V_RAW bulk
    fixes['C17'] = (78, 14, 90)     # +12V_RAW bypass
    fixes['C18'] = (78, 24, 90)     # -12V_RAW bypass

    # Right of U1 (x=98-102)
    fixes['C19'] = (98, 10, 90)
    fixes['C23'] = (98, 28, 90)
    fixes['C77'] = (100, 14, 90)    # HF bypass
    fixes['FB1'] = (100, 10, 0)     # keep x=100
    fixes['FB2'] = (100, 28, 0)     # slight move

    # LDO U14 caps — prevent overlap with U14 at (108,8)
    fixes['C22'] = (102, 6, 90)     # input cap, moved left
    fixes['C20'] = (114, 6, 90)     # output cap, moved right
    fixes['C16'] = (114, 10, 90)    # output bulk, moved right

    # LDO U15 caps — prevent overlap with U15 at (108,24)
    fixes['C21'] = (102, 22, 90)    # moved left
    fixes['C79'] = (114, 22, 90)    # moved right
    fixes['C81'] = (114, 26, 90)    # moved right
    fixes['C78'] = (102, 26, 90)    # moved left

    # FIX 4: D1/C80 — move away from J1 barrel jack (J1 at 70.87, 10.83, courtyard to ~76, ~18)
    fixes['D1']  = (72, 22, 0)      # below J1
    fixes['C80'] = (76, 22, 90)     # near D1

    # Mute circuit — move away from J1
    fixes['Q1']   = (50, 22, 0)
    fixes['R106'] = (46, 22, 0)
    fixes['R107'] = (54, 22, 0)

    # FIX 5: Shared power caps — move to PSU area (away from DIP switches)
    fixes['C24'] = (118, 8, 90)     # V+ 10µF near LDO output
    fixes['C25'] = (118, 26, 90)    # V- 10µF near LDO output
    
    # V- bypass caps — between channels, x=35 (left side, away from signal path)
    fixes['C35'] = (35, 114, 90)    # between CH3/CH4
    fixes['C36'] = (35, 142, 90)    # between CH4/CH5
    fixes['C37'] = (35, 170, 90)    # between CH5/CH6

    return fixes


def strip_routing(content):
    """Remove all segments and vias."""
    lines = content.split('\n')
    result = []
    i = 0
    removed = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == '(segment' or stripped.startswith('(segment ') or \
           stripped == '(via' or stripped.startswith('(via '):
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
    content = '\n'.join(result)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content, removed


def strip_zone_fills(content):
    """Remove filled_polygon blocks from zones (keep zone definitions)."""
    # Simple approach: remove all (filled_polygon ...) blocks
    result = []
    lines = content.split('\n')
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
    """Apply position fixes to PCB content."""
    moved = 0
    failed = []
    
    for ref, (x, y, rot) in fixes.items():
        if ref in FIXED_REFS:
            continue
            
        pat = rf'\(property "Reference" "{re.escape(ref)}"'
        m = re.search(pat, content)
        if not m:
            failed.append(ref)
            continue
        
        fp_start = content.rfind('(footprint "', 0, m.start())
        if fp_start == -1:
            failed.append(ref)
            continue
        
        region = content[fp_start:m.start()]
        at_match = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)', region)
        if not at_match:
            failed.append(ref)
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

    # Step 1: Strip routing
    content, n_routes = strip_routing(content)
    print(f"Stripped routing: {n_routes} elements")

    # Step 2: Strip zone fills
    content, n_fills = strip_zone_fills(content)
    print(f"Stripped zone fills: {n_fills} elements")

    # Step 3: Apply placement corrections
    fixes = build_corrections()
    print(f"\nApplying {len(fixes)} placement corrections...")
    content, moved, failed = apply_fixes(content, fixes)
    print(f"  Moved: {moved}")
    if failed:
        print(f"  Failed: {failed}")

    # Bracket balance
    depth = 0
    for ch in content:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
    assert depth == 0, f"Bracket balance error: {depth}"
    print(f"\nBracket balance: OK")

    with open(PCB, 'w') as f:
        f.write(content)
    print(f"PCB written: {len(content):,} chars")
    print("✅ Placement v2 complete")


if __name__ == '__main__':
    main()
