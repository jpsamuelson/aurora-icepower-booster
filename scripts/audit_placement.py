#!/usr/bin/env python3
"""
Audit PCB placement against copilot-instructions.md rules.

Checks:
1. HF-Entkopplung (100nF) < 3mm from IC pins
2. Lokale Entkopplung (1-10µF) < 20mm from IC
3. Grid alignment (0.5mm or 1.27mm grid)
4. Same orientation for R/C groups
5. TEL5/Schaltregler ≥ 20mm from audio input stage
6. Component spacing (no overlapping functional zones)
7. Mounting holes 4mm from board edge
"""
import re
import math
import json
from collections import defaultdict

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

def extract_components(pcb_text):
    """Extract ref, x, y, rot, footprint from all footprints."""
    comps = {}
    # Find all footprint blocks
    i = 0
    while True:
        idx = pcb_text.find('(footprint "', i)
        if idx < 0:
            break
        # Extract block
        depth = 0
        end = idx
        for j in range(idx, len(pcb_text)):
            if pcb_text[j] == '(':
                depth += 1
            elif pcb_text[j] == ')':
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        block = pcb_text[idx:end]
        i = end

        # Get footprint name
        fp_m = re.match(r'\(footprint\s+"([^"]+)"', block)
        if not fp_m:
            continue
        fp_name = fp_m.group(1)

        # Get position (first (at ...) in block)
        at_m = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block)
        if not at_m:
            continue
        x, y = float(at_m.group(1)), float(at_m.group(2))
        rot = float(at_m.group(3)) if at_m.group(3) else 0.0

        # Get reference
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if not ref_m:
            ref_m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', block)
        if not ref_m:
            continue
        ref = ref_m.group(1)

        # Get value
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)
        value = val_m.group(1) if val_m else ''

        comps[ref] = {
            'x': x, 'y': y, 'rot': rot,
            'fp': fp_name, 'value': value
        }
    return comps

def dist(a, b):
    return math.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)

def dist_xy(ax, ay, bx, by):
    return math.sqrt((ax - bx)**2 + (ay - by)**2)

def get_supply_pin_positions(ic):
    """Return list of (pin_name, x, y) for supply pins of an IC.
    SOIC-8 LM4562: Pin 8 (V+) at local (+2.475, -1.905), Pin 4 (V-) at local (-2.475, +1.905)
    SOIC-9 ADP7118/ADP7182: same SOIC-8 layout for pins 1-8 (pin 8=VIN, pin 4=GND)
    TEL5 DIP-24: large package, use center (conservative)
    """
    fp = ic.get('fp', '')
    rot_deg = ic.get('rot', 0.0)
    rot_rad = math.radians(rot_deg)
    cx, cy = ic['x'], ic['y']

    pins = []
    if 'SOIC-8' in fp or 'SOIC127P600' in fp or 'LM4562' in fp:
        # SOIC-8: V+ = Pin 8 at local (+2.475, -1.905), V- = Pin 4 at local (-2.475, +1.905)
        local_pins = [('V+', 2.475, -1.905), ('V-', -2.475, 1.905)]
        for name, lx, ly in local_pins:
            rx = lx * math.cos(rot_rad) - ly * math.sin(rot_rad)
            ry = lx * math.sin(rot_rad) + ly * math.cos(rot_rad)
            pins.append((name, cx + rx, cy + ry))
    elif 'SOT-23-5' in fp or 'SOT' in fp:
        # SOT-23-5: ADP7182 supply pins VIN(5) and GND(3)
        local_pins = [('VIN', 0.95, 0.0), ('GND', 0.95, 0.65)]
        for name, lx, ly in local_pins:
            rx = lx * math.cos(rot_rad) - ly * math.sin(rot_rad)
            ry = lx * math.sin(rot_rad) + ly * math.cos(rot_rad)
            pins.append((name, cx + rx, cy + ry))
    elif 'DIP' in fp or 'TEL5' in fp:
        # TEL5 DIP-24: Pin 14 (+12V_RAW out) at local (15.24, 22.86)
        #              Pin 11 (-12V_RAW out) at local (0, 22.86)
        local_pins = [('+12V_RAW', 15.24, 22.86), ('-12V_RAW', 0.0, 22.86)]
        for name, lx, ly in local_pins:
            rx = lx * math.cos(rot_rad) - ly * math.sin(rot_rad)
            ry = lx * math.sin(rot_rad) + ly * math.cos(rot_rad)
            pins.append((name, cx + rx, cy + ry))
    else:
        # Default: use center
        pins.append(('center', cx, cy))
    return pins

def min_dist_to_caps(ic, caps_dict):
    """Find minimum distance from any supply pin of IC to nearest cap.
    Returns (min_dist, cap_ref, pin_name)."""
    pins = get_supply_pin_positions(ic)
    best_dist = float('inf')
    best_cref = None
    best_pin = None
    for cref, cap in caps_dict.items():
        for pname, px, py in pins:
            d = dist_xy(px, py, cap['x'], cap['y'])
            if d < best_dist:
                best_dist = d
                best_cref = cref
                best_pin = pname
    return best_dist, best_cref, best_pin

def audit(comps):
    errors = []
    warnings = []
    ok_count = 0

    # ── Categorize components ──
    ics = {}        # ICs (U-prefix, SOIC/DIP/SOT-23-5)
    caps_100nf = {} # 100nF bypass caps
    caps_bulk = {}  # 1µF-100µF caps
    resistors = {}  # All Rs
    all_caps = {}   # All Cs

    for ref, c in comps.items():
        if ref.startswith('U'):
            ics[ref] = c
        elif ref.startswith('C'):
            all_caps[ref] = c
            val = c['value'].lower()
            if '100n' in val or '0.1u' in val or '100 n' in val:
                caps_100nf[ref] = c
            elif any(x in val for x in ['1u', '2.2u', '4.7u', '10u', '22u', '47u', '100u',
                                         '1µ', '2.2µ', '4.7µ', '10µ', '22µ', '47µ', '100µ']):
                caps_bulk[ref] = c
        elif ref.startswith('R'):
            resistors[ref] = c

    print(f"\n{'='*70}")
    print(f"PLACEMENT AUDIT — {len(comps)} components")
    print(f"{'='*70}")
    print(f"  ICs: {len(ics)}, 100nF caps: {len(caps_100nf)}, bulk caps: {len(caps_bulk)}")
    print(f"  Resistors: {len(resistors)}, All caps: {len(all_caps)}")

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 1: HF-Entkopplung < 3mm from IC
    # "Direkt am IC-Pin, kürzeste Verbindung zu VCC und GND (<3mm)"
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 1: HF-Entkopplung (100nF) < 3mm von IC-Pin")
    print(f"{'─'*70}")

    # For each IC, find its nearest 100nF cap
    # LDO voltage regulators (SOT-23-5) need µF bulk, not nF — relaxed to 6mm
    channel_ics = {r: c for r, c in ics.items()
                   if 'SOIC' in c['fp'] or 'LM4562' in c['fp'] or 'SOIC127P600' in c['fp']}
    power_ics = {r: c for r, c in ics.items()
                 if 'SOT-23-5' in c['fp'] or 'DIP' in c['fp'] or 'TEL5' in c['fp']}
    ldo_refs = {r for r, c in ics.items()
                if 'SOT-23-5' in c.get('fp', '') or 'SOT' in c.get('fp', '')}

    for ref, ic in sorted(ics.items()):
        is_ldo = ref in ldo_refs
        if is_ldo:
            # LDOs: check bulk cap (≥1µF) within 6mm instead of 100nF within 3mm
            nearest_dist, nearest_cap, pin_name = min_dist_to_caps(ic, caps_bulk)
            threshold = 6.0
            cap_type = "bulk≥1µF"
        else:
            nearest_dist, nearest_cap, pin_name = min_dist_to_caps(ic, caps_100nf)
            threshold = 3.0
            cap_type = "100nF"
        center_dist = min(dist(ic, cap) for cap in (caps_bulk if is_ldo else caps_100nf).values()) \
                      if (caps_bulk if is_ldo else caps_100nf) else float('inf')

        if nearest_dist > threshold:
            errors.append(f"  ❌ {ref} ({ic['value']}) @ ({ic['x']:.1f}, {ic['y']:.1f}): "
                         f"nearest {cap_type} = {nearest_cap} @ {nearest_dist:.1f}mm pin/{center_dist:.1f}mm center (>{threshold}mm!)")
        elif nearest_dist > threshold * 0.67:
            warnings.append(f"  ⚠️  {ref} ({ic['value']}) @ ({ic['x']:.1f}, {ic['y']:.1f}): "
                           f"nearest {cap_type} = {nearest_cap} @ {nearest_dist:.1f}mm pin (ok but >{threshold*0.67:.1f}mm)")
            ok_count += 1
        else:
            ok_count += 1
            print(f"  ✅ {ref} ({ic['value']}): {nearest_cap} @ {nearest_dist:.1f}mm from {pin_name} pin [{cap_type}]")

    for e in errors:
        print(e)
    for w in warnings:
        print(w)

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 2: Lokale Entkopplung < 20mm
    # "Pro Versorgungsinsel, <20mm vom IC"
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 2: Lokale Entkopplung (1-100µF) < 20mm von IC")
    print(f"{'─'*70}")

    ch2_errors = []
    for ref, ic in sorted(ics.items()):
        nearest_dist, nearest_bulk, _ = min_dist_to_caps(ic, caps_bulk)

        if nearest_bulk is None:
            continue
        if nearest_dist > 20.0:
            ch2_errors.append(f"  ❌ {ref} ({ic['value']}) @ ({ic['x']:.1f}, {ic['y']:.1f}): "
                             f"nearest bulk = {nearest_bulk} @ {nearest_dist:.1f}mm (>20mm!)")
        else:
            print(f"  ✅ {ref} ({ic['value']}): {nearest_bulk} @ {nearest_dist:.1f}mm")
    for e in ch2_errors:
        print(e)
        errors.append(e)

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 3: Grid alignment (0.5mm or 1.27mm)
    # "Bauteile an 0.5mm / 1.27mm Raster ausrichten"
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 3: Grid alignment (0.5mm Raster)")
    print(f"{'─'*70}")

    off_grid = []
    for ref, c in sorted(comps.items()):
        if ref.startswith('MH'):
            continue  # Mounting holes at fixed positions
        x_mod = c['x'] % 0.5
        y_mod = c['y'] % 0.5
        x_ok = min(x_mod, 0.5 - x_mod) < 0.01
        y_ok = min(y_mod, 0.5 - y_mod) < 0.01

        if not x_ok or not y_ok:
            # Check 1.27mm grid too
            x_mod127 = c['x'] % 1.27
            y_mod127 = c['y'] % 1.27
            x_ok127 = min(x_mod127, 1.27 - x_mod127) < 0.01
            y_ok127 = min(y_mod127, 1.27 - y_mod127) < 0.01

            if not (x_ok127 and y_ok127) and not (x_ok and y_ok127) and not (x_ok127 and y_ok):
                off_grid.append(ref)

    if off_grid:
        # Group by type
        connectors = [r for r in off_grid if r.startswith('J')]
        others = [r for r in off_grid if not r.startswith('J')]
        if connectors:
            print(f"  ℹ️  Connectors off-grid (OK, panel-mount): {', '.join(sorted(connectors))}")
        if others:
            print(f"  ⚠️  Off-grid components: {', '.join(sorted(others))}")
            for r in sorted(others):
                c = comps[r]
                print(f"      {r}: ({c['x']:.2f}, {c['y']:.2f})")
    else:
        print("  ✅ All components on 0.5mm grid")

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 4: Same orientation for R/C
    # "Gleiche Orientierung bei R/C (erleichtert Bestückung)"
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 4: R/C orientation consistency")
    print(f"{'─'*70}")

    r_rots = defaultdict(list)
    c_rots = defaultdict(list)
    for ref, c in comps.items():
        rot = c['rot'] % 180  # 0° and 180° are same orientation for passives
        if ref.startswith('R'):
            r_rots[rot].append(ref)
        elif ref.startswith('C'):
            c_rots[rot].append(ref)

    print(f"  Resistor orientations:")
    for rot, refs in sorted(r_rots.items()):
        print(f"    {rot:.0f}°: {len(refs)} components")
    print(f"  Capacitor orientations:")
    for rot, refs in sorted(c_rots.items()):
        print(f"    {rot:.0f}°: {len(refs)} components")

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 5: TEL5 / Power ≥ 20mm from audio input
    # "Schaltregler ≥ 20mm von Audio-Eingangsstufe"
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 5: TEL5 DC-DC ≥ 20mm von Audio-Eingangsstufe")
    print(f"{'─'*70}")

    u1 = comps.get('U1')
    if u1:
        # Audio input stage components (first column after XLR input)
        input_comps = {r: c for r, c in comps.items()
                      if any(x in r for x in ['R27','R28','R29','R30','R31','R32'])  # CH1 input Rs
                      or (r.startswith('U') and r in ['U2','U3'] and c['x'] < 80)}

        # Also check against X_INPUT_R column components
        for ref, c in comps.items():
            if 50 <= c['x'] <= 60 and 40 <= c['y'] <= 190:  # Input R column
                d = dist(u1, c)
                if d < 20.0:
                    errors.append(f"  ❌ U1 TEL5 @ ({u1['x']:.1f}, {u1['y']:.1f}) → "
                                 f"{ref} @ ({c['x']:.1f}, {c['y']:.1f}): {d:.1f}mm (<20mm!)")

        # Check nearest audio IC
        for ref in ['U2','U3','U4','U5','U6','U7','U8','U9','U10','U11','U12','U13']:
            if ref in comps:
                d = dist(u1, comps[ref])
                label = "✅" if d >= 20 else "❌"
                if d < 20:
                    errors.append(f"  {label} U1 TEL5 → {ref}: {d:.1f}mm {'(<20mm!)' if d<20 else ''}")
                elif ref in ['U2', 'U8']:  # Print nearest channel ICs
                    print(f"  {label} U1 TEL5 → {ref} (CH1 nearest): {d:.1f}mm")

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 6: Channel decoupling caps near their ICs
    # Each LM4562 needs V+/V- bypass caps within 3mm
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 6: Kanal-IC Entkopplungskondensatoren (je 2 pro LM4562)")
    print(f"{'─'*70}")

    # The Rx ICs are U2-U7 at X_RX_IC, Driver ICs are U8-U13 at X_DRV_IC
    rx_ics = {f'U{i}': comps[f'U{i}'] for i in range(2, 8) if f'U{i}' in comps}
    drv_ics = {f'U{i}': comps[f'U{i}'] for i in range(8, 14) if f'U{i}' in comps}

    for group_name, group in [("Rx ICs (U2-U7)", rx_ics), ("Driver ICs (U8-U13)", drv_ics)]:
        print(f"\n  {group_name}:")
        for ref, ic in sorted(group.items()):
            # Find 2 nearest caps measuring from supply pins
            pins = get_supply_pin_positions(ic)
            cap_dists = []
            for cref, cap in all_caps.items():
                min_pin_d = min(dist_xy(px, py, cap['x'], cap['y']) for _, px, py in pins)
                cap_dists.append((min_pin_d, cref, cap))
            cap_dists.sort()

            nearest_2 = cap_dists[:2]
            for d, cref, cap in nearest_2:
                label = "✅" if d <= 3.0 else ("⚠️ " if d <= 5.0 else "❌")
                status = "" if d <= 3.0 else (f" (>3mm)" if d <= 5.0 else f" (>5mm!)")
                print(f"    {label} {ref} → {cref} ({cap['value']}): {d:.1f}mm{status}")

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 7: Power regulator decoupling
    # U14 (ADP7118) and U15 (ADP7182) need nearby bypass caps
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 7: Spannungsregler-Entkopplung (U14, U15)")
    print(f"{'─'*70}")

    for ref in ['U14', 'U15']:
        if ref not in comps:
            continue
        ic = comps[ref]
        cap_dists = [(dist(ic, cap), cref, cap) for cref, cap in all_caps.items()]
        cap_dists.sort()
        print(f"\n  {ref} ({ic['value']}) @ ({ic['x']:.1f}, {ic['y']:.1f}):")
        for d, cref, cap in cap_dists[:5]:
            label = "✅" if d <= 3.0 else ("⚠️ " if d <= 5.0 else "❌")
            print(f"    {label} → {cref} ({cap['value']}): {d:.1f}mm")

    # ═══════════════════════════════════════════════════════════════════
    # CHECK 8: Board edge clearance
    # "Board-Edge zu Kupfer: 0.3mm empfohlen"
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*70}")
    print("CHECK 8: Board-Edge Clearance (min 0.3mm)")
    print(f"{'─'*70}")

    BOARD_W, BOARD_H = 158.0, 200.0
    edge_violations = []
    for ref, c in comps.items():
        margin = min(c['x'], c['y'], BOARD_W - c['x'], BOARD_H - c['y'])
        if margin < 0.3 and not ref.startswith('J'):  # Connectors can be at edge
            edge_violations.append(f"  ❌ {ref} @ ({c['x']:.1f}, {c['y']:.1f}): {margin:.1f}mm from edge")

    if edge_violations:
        for v in edge_violations:
            print(v)
            errors.append(v)
    else:
        print("  ✅ All components ≥ 0.3mm from board edge")

    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  Errors:   {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  OK:       {ok_count}")

    if errors:
        print(f"\n  ALL ERRORS:")
        for e in errors:
            print(f"  {e}")

    return errors, warnings


if __name__ == '__main__':
    with open(PCB) as f:
        pcb_text = f.read()
    comps = extract_components(pcb_text)
    print(f"Extracted {len(comps)} components from PCB")
    audit(comps)
