#!/usr/bin/env python3
"""
Fix placement v4: Correct ALL 63 misplaced channel components.

Root cause: CHANNEL_REFS in place_plan_b.py assumed linear ref numbering
per channel, but the schematic assigns refs differently.

Approach: Read fresh netlist → build correct ref→channel map → recalculate
positions using place_plan_b.py's per-role position formulas → apply.
"""
import re
import sys
import os

BASE = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
PCB = os.path.join(BASE, "aurora-dsp-icepower-booster.kicad_pcb")
NETLIST = "/tmp/aurora-fresh.net"

CH_Y = {1: 44.45, 2: 72.14, 3: 99.82, 4: 127.64, 5: 155.45, 6: 183.22}

FIXED_REFS = {
    'J1','J2','J3','J4','J5','J6','J7','J8',
    'J9','J10','J11','J12','J13','J14','SW1',
    'MH1','MH2','MH3','MH4',
}

# ── Step 1: Parse netlist for ref→channel ──
def parse_netlist():
    with open(NETLIST) as f:
        nl = f.read()
    
    ref_to_nets = {}
    for net_m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)', nl):
        net_name = net_m.group(1)
        depth = 0
        i = net_m.start()
        while i < len(nl):
            if nl[i] == '(':
                depth += 1
            elif nl[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = nl[net_m.start():i+1]
        for node_m in re.finditer(r'\(node \(ref "([^"]+)"\)', block):
            ref_to_nets.setdefault(node_m.group(1), set()).add(net_name)
    
    ref_channel = {}
    for ref, nets in ref_to_nets.items():
        chs = set()
        for net in nets:
            m = re.match(r'/CH(\d+)_', net)
            if m:
                chs.add(int(m.group(1)))
        if len(chs) == 1:
            ref_channel[ref] = list(chs)[0]
    
    return ref_channel

# ── Step 2: Position formulas from place_plan_b.py ──
# These define WHERE each role is placed relative to channel center
def get_role_position(role, ch):
    """Return (x, y, rot) for a given role in a given channel."""
    yc = CH_Y[ch]
    y_hot = yc - 3.5
    y_cold = yc + 3.5
    y_gain_r = yc - 8.0
    y_dip = yc - 12.0
    
    positions = {
        'D_tvs_hot_in':      (33, y_hot, 0),
        'D_tvs_cold_in':     (33, y_cold, 0),
        'R_emi_hot':         (37, y_hot, 0),
        'R_emi_cold':        (37, y_cold, 0),
        'C_emi_hot':         (41, y_hot, 90),
        'C_emi_cold':        (41, y_cold, 90),
        'C_couple_hot':      (45, y_hot, 0),
        'C_couple_cold':     (45, y_cold, 0),
        'R_diff_hot':        (49, y_hot - 1.5, 90),
        'R_diff_cold':       (49, y_cold + 1.5, 90),
        'R_inv_in':          (49, yc, 90),
        'U_stage1':          (55, yc, 0),
        'C_byp1_vp':         (52, yc - 5.0, 90),
        'C_byp1_vn':         (52, yc + 5.0, 90),
        'SW':                (55, y_dip, 0),
        'R_gain1':           (49, y_gain_r, 0),
        'R_gain2':           (52, y_gain_r, 0),
        'R_gain3':           (55, y_gain_r, 0),
        'R_sum':             (58, y_gain_r, 0),
        'R_inter1':          (63, y_hot, 0),
        'R_inter2':          (63, y_cold, 0),
        'U_stage2':          (69, yc, 0),
        'C_byp2_vp':         (66, yc - 5.0, 90),
        'C_byp2_vn':         (66, yc + 5.0, 90),
        'R_out1':            (76, y_hot - 1.5, 90),
        'R_out2':            (76, round(yc - 2, 2), 90),  # v3 fix: +/-2mm
        'R_out3':            (80, y_hot, 0),
        'R_out4':            (76, round(yc + 2, 2), 90),   # v3 fix: +/-2mm
        'R_out5':            (76, y_cold + 1.5, 90),
        'C_out1':            (84, y_hot, 0),
        'C_out2':            (84, y_cold, 0),
        'Q_mute':            (92, yc, 0),
        'R_mute':            (96, yc, 0),
        'D_tvs_hot_out':     (101, y_hot, 0),
        'D_tvs_cold_out':    (101, y_cold, 0),
        'R_zobel_cold_extra': (88, y_cold, 0),
        'R_zobel_hot_extra':  (88, y_hot, 0),
    }
    
    return positions.get(role)

# ── Step 3: CHANNEL_REFS from place_plan_b.py ──
CHANNEL_REFS = {
    'D_tvs_hot_in':  ['D10', 'D11', 'D12', 'D13', 'D14', 'D15'],
    'D_tvs_cold_in': ['D8', 'D16', 'D17', 'D18', 'D19', 'D20'],
    'D_tvs_hot_out': ['D9', 'D21', 'D22', 'D23', 'D24', 'D25'],
    'D_tvs_cold_out': ['D2', 'D3', 'D4', 'D5', 'D6', 'D7'],
    'R_emi_hot':   ['R95', 'R96', 'R97', 'R98', 'R99', 'R100'],
    'R_emi_cold':  ['R94', 'R101', 'R102', 'R103', 'R104', 'R105'],
    'C_emi_hot':   ['C51', 'C52', 'C53', 'C54', 'C55', 'C56'],
    'C_emi_cold':  ['C50', 'C57', 'C58', 'C59', 'C60', 'C61'],
    'C_couple_hot':  ['C63', 'C64', 'C65', 'C66', 'C67', 'C68'],
    'C_couple_cold': ['C62', 'C69', 'C70', 'C71', 'C72', 'C73'],
    'R_diff_hot':   ['R3', 'R4', 'R5', 'R6', 'R7', 'R8'],
    'R_diff_cold':  ['R2', 'R9', 'R10', 'R11', 'R12', 'R13'],
    'R_inv_in':     ['R14', 'R15', 'R16', 'R17', 'R18', 'R19'],
    'U_stage1':     ['U2', 'U3', 'U4', 'U5', 'U6', 'U7'],
    'C_byp1_vp': ['C8', 'C9', 'C10', 'C11', 'C12', 'C13'],
    'C_byp1_vn': ['C2', 'C3', 'C4', 'C5', 'C6', 'C7'],
    'SW': ['SW2', 'SW3', 'SW4', 'SW5', 'SW6', 'SW7'],
    'R_gain1': ['R27', 'R30', 'R33', 'R36', 'R39', 'R42'],
    'R_gain2': ['R28', 'R31', 'R34', 'R37', 'R40', 'R43'],
    'R_gain3': ['R29', 'R32', 'R35', 'R38', 'R41', 'R44'],
    'R_sum':   ['R50', 'R51', 'R52', 'R53', 'R54', 'R55'],
    'R_inter1': ['R20', 'R21', 'R22', 'R23', 'R24', 'R25'],
    'R_inter2': ['R26', 'R45', 'R46', 'R47', 'R48', 'R49'],
    'U_stage2': ['U8', 'U9', 'U10', 'U11', 'U12', 'U13'],
    'C_byp2_vp': ['C26', 'C27', 'C28', 'C29', 'C30', 'C31'],
    'C_byp2_vn': ['C32', 'C33', 'C34', 'C74', 'C75', 'C76'],
    'R_out1': ['R64', 'R65', 'R66', 'R67', 'R68', 'R69'],
    'R_out2': ['R70', 'R71', 'R72', 'R73', 'R74', 'R75'],
    'R_out3': ['R76', 'R77', 'R78', 'R56', 'R57', 'R58'],
    'R_out4': ['R82', 'R83', 'R84', 'R85', 'R86', 'R87'],
    'R_out5': ['R88', 'R89', 'R90', 'R91', 'R92', 'R93'],
    'C_out1': ['C38', 'C39', 'C40', 'C41', 'C42', 'C43'],
    'C_out2': ['C44', 'C45', 'C46', 'C47', 'C48', 'C49'],
    'R_mute': ['R108', 'R109', 'R110', 'R111', 'R112', 'R113'],
    'Q_mute': ['Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'],
    'D_tvs_cold_out': ['D2', 'D3', 'D4', 'D5', 'D6', 'D7'],
    'R_zobel_cold_extra': [None, 'R59', 'R60', 'R61', 'R62', 'R63'],
    'R_zobel_hot_extra': [None, None, None, 'R79', 'R80', 'R81'],
}


def strip_routing(content):
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
    moved = 0
    failed = []
    for ref, (x, y, rot) in fixes.items():
        if ref in FIXED_REFS:
            continue
        pat = rf'\(property "Reference" "{re.escape(ref)}"'
        m = re.search(pat, content)
        if not m:
            failed.append(f"{ref} (not found)")
            continue
        fp_start = content.rfind('(footprint "', 0, m.start())
        if fp_start == -1:
            failed.append(f"{ref} (no fp)")
            continue
        region = content[fp_start:m.start()]
        at_m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)( -?[\d.]+)?\)', region)
        if not at_m:
            failed.append(f"{ref} (no at)")
            continue
        at_start = fp_start + at_m.start()
        at_end = fp_start + at_m.end()
        if rot == 0:
            new_at = f'(at {x} {y})'
        else:
            new_at = f'(at {x} {y} {rot})'
        content = content[:at_start] + new_at + content[at_end:]
        moved += 1
    return content, moved, failed


def main():
    # Get correct channel assignments from netlist
    print("=== Building correct ref→channel map from netlist ===")
    ref_channel = parse_netlist()
    print(f"  Single-channel refs: {len(ref_channel)}")
    
    # Build correction map: for each misplaced ref, calculate correct position
    fixes = {}
    already_correct = 0
    
    for role, refs in CHANNEL_REFS.items():
        for script_idx, ref in enumerate(refs):
            if ref is None:
                continue
            script_ch = script_idx + 1  # assumed channel
            actual_ch = ref_channel.get(ref)
            
            if actual_ch is None:
                continue  # not a channel component
            
            if actual_ch == script_ch:
                already_correct += 1
                continue
            
            # This ref needs to move to actual_ch
            pos = get_role_position(role, actual_ch)
            if pos is None:
                print(f"  WARNING: No position formula for {role} in CH{actual_ch}")
                continue
            
            fixes[ref] = pos
    
    print(f"  Already correct: {already_correct}")
    print(f"  Need correction: {len(fixes)}")
    
    if not fixes:
        print("  Nothing to fix!")
        return
    
    # Show planned moves
    print(f"\n=== Planned moves ({len(fixes)}) ===")
    for ref in sorted(fixes, key=lambda r: fixes[r][1]):
        x, y, rot = fixes[ref]
        actual_ch = ref_channel.get(ref, '?')
        print(f"  {ref:8s} → CH{actual_ch} ({x}, {y}, {rot}°)")
    
    # Apply to PCB
    print(f"\n=== Applying to PCB ===")
    with open(PCB) as f:
        content = f.read()
    print(f"  Loaded: {len(content):,} chars")
    
    content, n_routes = strip_routing(content)
    print(f"  Stripped routing: {n_routes}")
    
    content, n_fills = strip_zone_fills(content)
    print(f"  Stripped zone fills: {n_fills}")
    
    content, moved, failed = apply_fixes(content, fixes)
    print(f"  Moved: {moved}")
    if failed:
        print(f"  Failed: {failed}")
    
    # Bracket balance
    depth = 0
    for ch in content:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
    if depth != 0:
        print(f"ERROR: Bracket balance = {depth}")
        sys.exit(1)
    print(f"  Bracket balance: OK")
    
    with open(PCB, 'w') as f:
        f.write(content)
    print(f"  Written: {len(content):,} chars")
    print(f"\n==> Fix v4 complete — {moved} components corrected")


if __name__ == '__main__':
    main()
