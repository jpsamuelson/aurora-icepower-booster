#!/usr/bin/env python3
"""
Classify ALL schematic components into roles and channels using the fresh netlist.
This replaces the manual CHANNEL_REFS mapping with netlist-derived assignments.
"""
import re
import json

NETLIST_PATH = '/tmp/aurora-fresh.net'

# Fixed refs that should never be placed by this script
FIXED_REFS = {
    'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8',
    'J9', 'J10', 'J11', 'J12', 'J13', 'J14',
    'SW1', 'MH1', 'MH2', 'MH3', 'MH4',
}

# ============================================================
# Step 1: Parse netlist → ref→{pin→net}
# ============================================================
with open(NETLIST_PATH) as f:
    nl = f.read()

ref_pin_net = {}
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
    for node_m in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block):
        ref = node_m.group(1)
        pin = node_m.group(2)
        ref_pin_net.setdefault(ref, {})[pin] = net_name

# ============================================================
# Step 2: Determine channel for each ref
# ============================================================
def get_channel(pins_dict):
    """Return channel number(s) from net names, or None for PSU."""
    channels = set()
    for pin, net in pins_dict.items():
        m = re.match(r'/CH(\d+)_', net)
        if m:
            channels.add(int(m.group(1)))
    return channels

def get_signal_nets(pins_dict):
    """Return non-GND, non-power nets (the actual signal connections)."""
    result = {}
    for pin, net in pins_dict.items():
        if net not in ('GND', '', 'unconnected') and not net.startswith('+') and not net.startswith('-'):
            result[pin] = net
    return result

def get_net_suffixes(pins_dict):
    """Extract CHn_ suffixes from nets."""
    suffixes = {}
    for pin, net in pins_dict.items():
        m = re.match(r'/CH\d+_(.*)', net)
        if m:
            suffixes[pin] = m.group(1)
    return suffixes

# ============================================================
# Step 3: Role classification based on net patterns
# ============================================================
def classify_component(ref, pins):
    """
    Classify a component into a role based on its net connections.
    Returns (role, channel) or (None, None) if unclassifiable.
    """
    channels = get_channel(pins)
    if not channels:
        return None, None  # PSU or power component
    
    if len(channels) > 1:
        return 'MULTI_CH', sorted(channels)
    
    ch = list(channels)[0]
    suffixes = get_net_suffixes(pins)
    sig_nets = get_signal_nets(pins)
    net_vals = set(pins.values())
    suffix_vals = set(suffixes.values())
    
    prefix = ref[0]  # D, R, C, U, Q, SW, FB
    
    # === DIODES (TVS, 2 pins: one GND, one signal) ===
    if prefix == 'D':
        if 'GND' in net_vals:
            # TVS diode: GND + signal
            for p, s in suffixes.items():
                if s == 'HOT_RAW':
                    return 'D_tvs_hot_in', ch
                elif s == 'COLD_RAW':
                    return 'D_tvs_cold_in', ch
                elif s == 'OUT_HOT':
                    return 'D_tvs_hot_out', ch
                elif s == 'OUT_COLD':
                    return 'D_tvs_cold_out', ch
                elif s == 'OUT_PROT_HOT':
                    return 'D_tvs_hot_out', ch  # same position
                elif s == 'OUT_PROT_COLD':
                    return 'D_tvs_cold_out', ch
            # Fallback: check raw net names
            for p, n in pins.items():
                if 'HOT_RAW' in n: return 'D_tvs_hot_in', ch
                if 'COLD_RAW' in n: return 'D_tvs_cold_in', ch
                if 'OUT_HOT' in n: return 'D_tvs_hot_out', ch
                if 'OUT_COLD' in n: return 'D_tvs_cold_out', ch
                if 'OUT_PROT_HOT' in n: return 'D_tvs_hot_out', ch
                if 'OUT_PROT_COLD' in n: return 'D_tvs_cold_out', ch
        return f'D_UNKNOWN({suffix_vals})', ch
    
    # === SWITCHES ===
    if ref.startswith('SW'):
        return 'SW', ch
    
    # === MOSFETS ===
    if prefix == 'Q':
        return 'Q_mute', ch
    
    # === OP-AMPS ===
    if prefix == 'U':
        # Determine if stage1 or stage2 based on net connections
        for p, s in suffixes.items():
            if s in ('INV_IN', 'BUF_DRIVE') or 'INV_IN' in s or 'BUF_DRIVE' in s:
                return 'U_stage1', ch
            if s in ('GAIN_FB', 'GAIN_OUT', 'OUT_DRIVE', 'RX_OUT'):
                return 'U_stage2', ch
        # Check all suffix vals
        if any('INV_IN' in s or 'BUF_DRIVE' in s for s in suffix_vals):
            return 'U_stage1', ch
        if any('GAIN_FB' in s or 'OUT_DRIVE' in s or 'RX_OUT' in s for s in suffix_vals):
            return 'U_stage2', ch
        return f'U_UNKNOWN({suffix_vals})', ch
    
    # === RESISTORS ===
    if prefix == 'R':
        pairs = set()
        for p, s in suffixes.items():
            pairs.add(s)
        
        # EMI resistors: connect RAW to EMI
        if 'HOT_RAW' in pairs and 'EMI_HOT' in pairs:
            return 'R_emi_hot', ch
        if 'COLD_RAW' in pairs and 'EMI_COLD' in pairs:
            return 'R_emi_cold', ch
        
        # Differential input: GND + HOT_IN or GND + COLD_IN
        if 'GND' in net_vals:
            if 'HOT_IN' in pairs:
                return 'R_diff_hot', ch
            if 'COLD_IN' in pairs:
                return 'R_diff_cold', ch
        
        # Inverting input: INV_IN + COLD_IN
        if 'INV_IN' in pairs and 'COLD_IN' in pairs:
            return 'R_inv_in', ch
        
        # Gain resistors: SW_OUT_n + SUMNODE
        if 'SUMNODE' in pairs:
            if 'SW_OUT_1' in pairs: return 'R_gain1', ch
            if 'SW_OUT_2' in pairs: return 'R_gain2', ch
            if 'SW_OUT_3' in pairs: return 'R_gain3', ch
            if 'RX_OUT' in pairs: return 'R_inter2', ch  # feedback to sumnode
            return 'R_sum', ch  # generic sumnode connection
        
        # Sum resistor: GAIN_FB + INV_IN
        if 'GAIN_FB' in pairs and 'INV_IN' in pairs:
            return 'R_sum', ch
        
        # Inter-stage: GAIN_OUT + RX_OUT or GAIN_FB + RX_OUT
        if 'GAIN_OUT' in pairs:
            return 'R_inter1', ch
        if 'GAIN_FB' in pairs:
            return 'R_inter1', ch  # same region
        
        # Output resistors: various output net patterns
        if 'OUT_DRIVE' in pairs:
            if 'OUT_HOT' in pairs: return 'R_out3', ch  # hot output
            if 'OUT_COLD' in pairs: return 'R_out3_cold', ch
        if 'BUF_DRIVE' in pairs:
            if 'OUT_COLD' in pairs: return 'R_out3_cold', ch
            if 'OUT_HOT' in pairs: return 'R_out3', ch
        
        # Output protection: OUT_HOT + OUT_PROT_HOT
        if 'OUT_HOT' in pairs and 'OUT_PROT_HOT' in pairs:
            return 'R_out1', ch
        if 'OUT_COLD' in pairs and 'OUT_PROT_COLD' in pairs:
            return 'R_out4', ch
        
        # Zobel: OUT_PROT_HOT/COLD + further
        if 'OUT_PROT_HOT' in pairs:
            return 'R_out2', ch
        if 'OUT_PROT_COLD' in pairs:
            return 'R_out5', ch
        
        # Mute resistor
        if any('MUTE' in s for s in suffix_vals):
            return 'R_mute', ch
        
        return f'R_UNKNOWN({suffix_vals})', ch
    
    # === CAPACITORS ===
    if prefix == 'C':
        pairs = set()
        for p, s in suffixes.items():
            pairs.add(s)
        
        # EMI caps: EMI_HOT/COLD + GND
        if 'GND' in net_vals:
            if 'EMI_HOT' in pairs: return 'C_emi_hot', ch
            if 'EMI_COLD' in pairs: return 'C_emi_cold', ch
        
        # Coupling caps: EMI + IN
        if 'EMI_HOT' in pairs and 'HOT_IN' in pairs:
            return 'C_couple_hot', ch
        if 'EMI_COLD' in pairs and 'COLD_IN' in pairs:
            return 'C_couple_cold', ch
        
        # Bypass caps: V+/V- connections
        v_plus = any(n in ('/V+', '+12V', '/+12V') for n in net_vals)
        v_minus = any(n in ('/V-', '-12V', '/-12V') for n in net_vals)
        
        # Check if connected to stage1 or stage2 opamp net
        stage1_nets = {'INV_IN', 'BUF_DRIVE', 'COLD_IN', 'HOT_IN'}
        stage2_nets = {'GAIN_FB', 'GAIN_OUT', 'OUT_DRIVE', 'RX_OUT'}
        
        if v_plus or v_minus:
            # Determine which stage based on proximity/association
            # This is tricky - need to check which U this cap is near
            # For now classify by V+/V-
            if v_plus:
                # Check if any pin connects to a stage-specific net
                for s in pairs:
                    if s in stage1_nets: return 'C_byp1_vp', ch
                    if s in stage2_nets: return 'C_byp2_vp', ch
                return 'C_byp_vp', ch  # generic
            if v_minus:
                for s in pairs:
                    if s in stage1_nets: return 'C_byp1_vn', ch
                    if s in stage2_nets: return 'C_byp2_vn', ch
                return 'C_byp_vn', ch  # generic
        
        # Output caps
        if 'OUT_HOT' in pairs or 'OUT_PROT_HOT' in pairs:
            return 'C_out1', ch  # hot output cap
        if 'OUT_COLD' in pairs or 'OUT_PROT_COLD' in pairs:
            return 'C_out2', ch  # cold output cap
        
        return f'C_UNKNOWN({suffix_vals})', ch
    
    return f'UNKNOWN_{prefix}', ch


# ============================================================
# Step 4: Classify all components
# ============================================================
role_channel_map = {}  # ref → (role, channel)
by_role = {}  # role → [(ref, channel)]
psu_refs = []
unclassified = []
fixed_skip = []

for ref in sorted(ref_pin_net.keys(), key=lambda r: (r[0], int(re.search(r'\d+', r).group()) if re.search(r'\d+', r) else 0)):
    if ref in FIXED_REFS:
        fixed_skip.append(ref)
        continue
    
    pins = ref_pin_net[ref]
    role, ch = classify_component(ref, pins)
    
    if role is None:
        psu_refs.append(ref)
    elif 'UNKNOWN' in str(role) or role == 'MULTI_CH':
        unclassified.append((ref, role, ch, pins))
    else:
        role_channel_map[ref] = (role, ch)
        by_role.setdefault(role, []).append((ref, ch))

# ============================================================
# Step 5: Report
# ============================================================
print("=" * 80)
print("COMPONENT CLASSIFICATION FROM NETLIST")
print("=" * 80)

print(f"\nTotal refs in netlist: {len(ref_pin_net)}")
print(f"Fixed (skip): {len(fixed_skip)}")
print(f"PSU (no channel): {len(psu_refs)}")
print(f"Classified channel components: {len(role_channel_map)}")
print(f"Unclassified: {len(unclassified)}")

print(f"\nPSU refs: {', '.join(sorted(psu_refs, key=lambda r: (r[0], int(re.search(r'[0-9]+', r).group()) if re.search(r'[0-9]+', r) else 0)))}")

print("\n" + "=" * 80)
print("ROLE ASSIGNMENTS (role → refs per channel)")
print("=" * 80)
for role in sorted(by_role.keys()):
    items = by_role[role]
    items.sort(key=lambda x: x[1])  # sort by channel
    ch_map = {}
    for ref, ch in items:
        ch_map.setdefault(ch, []).append(ref)
    
    print(f"\n  {role}:")
    for ch in range(1, 7):
        refs = ch_map.get(ch, [])
        status = "OK" if len(refs) == 1 else ("MISSING!" if len(refs) == 0 else f"COLLISION: {len(refs)} refs!")
        print(f"    CH{ch}: {', '.join(refs) if refs else '---':20s} [{status}]")

if unclassified:
    print("\n" + "=" * 80)
    print("UNCLASSIFIED COMPONENTS")
    print("=" * 80)
    for ref, role, ch, pins in unclassified:
        pin_str = ', '.join(f'{p}:{n}' for p, n in sorted(pins.items()))
        print(f"  {ref:8s} role={role!s:30s} ch={ch} {pin_str}")

# ============================================================
# Step 6: Collision analysis
# ============================================================
print("\n" + "=" * 80)
print("COLLISION SUMMARY (roles needing exactly 1 ref per channel)")
print("=" * 80)
needs_fix = False
for role in sorted(by_role.keys()):
    items = by_role[role]
    ch_counts = {}
    for ref, ch in items:
        ch_counts[ch] = ch_counts.get(ch, 0) + 1
    
    problems = [(ch, cnt) for ch, cnt in ch_counts.items() if cnt != 1]
    missing = [ch for ch in range(1, 7) if ch not in ch_counts]
    
    if problems or missing:
        needs_fix = True
        print(f"\n  {role}: {len(items)} refs total")
        if problems:
            for ch, cnt in sorted(problems):
                refs = [r for r, c in items if c == ch]
                print(f"    CH{ch}: {cnt} refs → {', '.join(refs)}")
        if missing:
            print(f"    MISSING channels: {missing}")

if not needs_fix:
    print("\n  ALL ROLES have exactly 1 ref per channel! No collisions.")

# ============================================================
# Step 7: Export mapping for placement script
# ============================================================
output = {}
for ref, (role, ch) in role_channel_map.items():
    output[ref] = {'role': role, 'channel': ch}

with open('/tmp/ref_classification.json', 'w') as f:
    json.dump(output, f, indent=2, sort_keys=True)
print(f"\nMapping exported to /tmp/ref_classification.json")
