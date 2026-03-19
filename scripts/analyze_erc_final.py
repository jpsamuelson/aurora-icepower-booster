#!/usr/bin/env python3
"""Find dangling wire, check PWR_FLAG nets, check U1 Pin 1, and verify C14 connections."""

import re, math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    text = f.read()

NETLIST = "/tmp/revalidation_netlist.net"
with open(NETLIST, "r") as f:
    netlist = f.read()

# Parse all wires
wires = []
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    wires.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))))

def wire_endpoints_at(x, y, tol=0.05):
    hits = []
    for x1, y1, x2, y2 in wires:
        if abs(x1-x) < tol and abs(y1-y) < tol:
            hits.append(('start', x1, y1, x2, y2))
        if abs(x2-x) < tol and abs(y2-y) < tol:
            hits.append(('end', x1, y1, x2, y2))
    return hits

# ===== 1. Find ALL short vertical wires (W5 dangling endpoint) =====
print("=" * 70)
print("1. ALL Wires with length < 1mm")
print("=" * 70)
short_wires = []
for x1, y1, x2, y2 in wires:
    length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    if length < 1.0:
        short_wires.append((x1, y1, x2, y2, length))
        # Check if both ends connect to other wires
        ep1 = len(wire_endpoints_at(x1, y1)) - 1  # -1 for the wire itself
        ep2 = len(wire_endpoints_at(x2, y2)) - 1
        is_vertical = abs(x1 - x2) < 0.01
        print(f"  ({x1},{y1})→({x2},{y2}), L={length:.4f}mm, {'V' if is_vertical else 'H'}")
        print(f"    Start connects to {ep1} other wire(s), End connects to {ep2} other wire(s)")
        if ep1 == 0 or ep2 == 0:
            print(f"    ⚠️ DANGLING ENDPOINT!")

# ===== 2. PWR_FLAG connections =====
print("\n" + "=" * 70)
print("2. PWR_FLAG Net Connections")
print("=" * 70)

# Trace what net each PWR_FLAG connects to
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"power:PWR_FLAG"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    x, y = float(m.group(1)), float(m.group(2))
    rot = int(m.group(3))
    start = m.start()
    chunk = text[start:start+1500]
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
    ref = ref_m.group(1) if ref_m else "?"
    
    print(f"\n  {ref}: PWR_FLAG at ({x}, {y}), rot={rot}°")
    # PWR_FLAG has its pin at the symbol position
    ep = wire_endpoints_at(x, y)
    print(f"    Wire endpoints at flag: {len(ep)}")
    for e in ep:
        print(f"      ({e[1]},{e[2]})→({e[3]},{e[4]})")
    
    # Trace the wire connectivity
    visited = set()
    to_visit = [(x, y)]
    points = []
    while to_visit:
        px, py = to_visit.pop()
        key = (round(px, 2), round(py, 2))
        if key in visited:
            continue
        visited.add(key)
        points.append(key)
        for x1, y1, x2, y2 in wires:
            if abs(x1-px) < 0.01 and abs(y1-py) < 0.01:
                to_visit.append((x2, y2))
            elif abs(x2-px) < 0.01 and abs(y2-py) < 0.01:
                to_visit.append((x1, y1))
    print(f"    Connected points: {points[:10]}{'...' if len(points) > 10 else ''}")
    
    # Check for power symbols at these points
    for px, py in points:
        for pm in re.finditer(r'\(symbol\s+\(lib_id\s+"(power:[^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
            sx, sy = float(pm.group(2)), float(pm.group(3))
            if abs(sx - px) < 0.01 and abs(sy - py) < 0.01:
                pstart = pm.start()
                pchunk = text[pstart:pstart+1000]
                pref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', pchunk)
                pval_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', pchunk)
                pref = pref_m.group(1) if pref_m else "?"
                pval = pval_m.group(1) if pval_m else "?"
                print(f"    → Connected to {pref} ({pval}) at ({sx}, {sy})")
    
    # Check for labels at these points
    for px, py in points:
        for lm in re.finditer(r'\(label\s+"([^"]+)"\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
            lx, ly = float(lm.group(2)), float(lm.group(3))
            if abs(lx - px) < 0.01 and abs(ly - py) < 0.01:
                print(f"    → Connected to label '{lm.group(1)}' at ({lx}, {ly})")

# ===== 3. U1 Pin 1 — where is it? =====
print("\n" + "=" * 70)
print("3. U1 Pin 1 (~, power_out)")
print("=" * 70)
# The TEL5-2422 cache has Pin 1 (~): power_out
# U1 at (80.0, 40.0), rotation 0
# Need to find Pin 1's local position in cache
cache_start = text.find('(lib_symbols')
tel_idx = text.find('"TEL5-2422"', cache_start)
if tel_idx >= 0:
    chunk = text[tel_idx:tel_idx+5000]
    pins = re.findall(r'\(pin\s+(\w+)\s+\w+\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+\d+)?\).*?\(name\s+"([^"]+)".*?\(number\s+"(\d+)"', chunk)
    for ptype, px, py, pname, pnum in pins:
        if pnum == '1':
            sch_x = 80.0 + float(px)
            sch_y = 40.0 - float(py)
            print(f"  Pin 1 ({pname}, {ptype}): local ({px}, {py}) → schematic ({sch_x:.2f}, {sch_y:.2f})")
            ep = wire_endpoints_at(sch_x, sch_y)
            print(f"  Wire endpoints at pin: {len(ep)}")
            for e in ep:
                print(f"    ({e[1]},{e[2]})→({e[3]},{e[4]})")

# Check netlist for U1 Pin 1
print("\n  U1.1 in netlist:")
for m in re.finditer(r'\(net \(code "(\d+)"\) \(name "([^"]*)"\)(.*?)\)\)', netlist, re.DOTALL):
    if '"U1"' in m.group(3) and '"1"' in m.group(3):
        # Check if this is actually pin 1
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "(\d+)"\)', m.group(3))
        for ref, pin in nodes:
            if ref == 'U1' and pin == '1':
                print(f"  Net '{m.group(2)}' (code {m.group(1)}): {nodes}")
                break

# ===== 4. Verify C14 connections =====
print("\n" + "=" * 70)
print("4. C14 (100nF C0G) at (98.0, 25.0) — Connection Trace")
print("=" * 70)
# C14 Pin 1: (98.0, 25.0 - 3.81) = (98.0, 21.19) — goes to #PWR001
# C14 Pin 2: (98.0, 25.0 + 3.81) = (98.0, 28.81) — goes to ?
print("  C14 Pin 1 at (98.0, 21.19):")
ep = wire_endpoints_at(98.0, 21.19)
for e in ep:
    print(f"    Wire: ({e[1]},{e[2]})→({e[3]},{e[4]})")

print("  C14 Pin 2 at (98.0, 28.81):")
ep = wire_endpoints_at(98.0, 28.81)
for e in ep:
    print(f"    Wire: ({e[1]},{e[2]})→({e[3]},{e[4]})")

# Trace C14 Pin 2 network
visited = set()
to_visit = [(98.0, 28.81)]
p2_points = []
while to_visit:
    px, py = to_visit.pop()
    key = (round(px, 2), round(py, 2))
    if key in visited:
        continue
    visited.add(key)
    p2_points.append(key)
    for x1, y1, x2, y2 in wires:
        if abs(x1-px) < 0.01 and abs(y1-py) < 0.01:
            to_visit.append((x2, y2))
        elif abs(x2-px) < 0.01 and abs(y2-py) < 0.01:
            to_visit.append((x1, y1))
print(f"  Pin 2 wire-connected points: {p2_points}")

# Check for labels/power at these points
for px, py in p2_points:
    for lm in re.finditer(r'\(label\s+"([^"]+)"\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)', text):
        lx, ly = float(lm.group(2)), float(lm.group(3))
        if abs(lx - px) < 0.01 and abs(ly - py) < 0.01:
            print(f"    Label '{lm.group(1)}' at ({lx}, {ly})")

# ===== 5. Check GND net in netlist — is there a PWR_FLAG? =====
print("\n" + "=" * 70)
print("5. GND Net — Components on it")
print("=" * 70)
gnd_net_m = re.search(r'\(net \(code "\d+"\) \(name "GND"\)(.*?)\)\)', netlist, re.DOTALL)
if gnd_net_m:
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "(\d+)"\) \(pintype "(\w+)"\)', gnd_net_m.group(1))
    # Look for power_out pins
    power_out = [n for n in nodes if n[2] == 'power_out']
    print(f"  Total pins on GND: {len(nodes)}")
    print(f"  power_out pins: {power_out}")
    print(f"  Pin types: {set(n[2] for n in nodes)}")
    # Check for FLG (PWR_FLAG)
    flg = [n for n in nodes if '#FLG' in n[0]]
    print(f"  PWR_FLAG on GND: {flg}")

# Check V+ net
vp_net_m = re.search(r'\(net \(code "\d+"\) \(name "/V\+"\)(.*?)\)\)', netlist, re.DOTALL)
if vp_net_m:
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "(\d+)"\) \(pintype "(\w+)"\)', vp_net_m.group(1))
    power_out = [n for n in nodes if n[2] == 'power_out']
    flg = [n for n in nodes if '#FLG' in n[0]]
    print(f"\n  V+ net: {len(nodes)} pins, power_out: {power_out}, PWR_FLAG: {flg}")

# Check +24V_IN
vin_net = re.search(r'\(net \(code "\d+"\) \(name "/\+24V_IN"\)(.*?)\)\)', netlist, re.DOTALL)
if vin_net:
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "(\d+)"\) \(pintype "(\w+)"\)', vin_net.group(1))
    power_out = [n for n in nodes if n[2] == 'power_out']
    flg = [n for n in nodes if '#FLG' in n[0]]
    print(f"  +24V_IN net: {len(nodes)} pins, power_out: {power_out}, PWR_FLAG: {flg}")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
