#!/usr/bin/env python3
"""Deep pin-level analysis for C22, #PWR001, #PWR063, and the 6 channel #PWR symbols."""

import re
import math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, "r") as f:
    text = f.read()

# Parse ALL wires
wires = []
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    wires.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))))

# Parse ALL junctions
junctions = []
for m in re.finditer(r'\(junction\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\)', text):
    junctions.append((float(m.group(1)), float(m.group(2))))

# Parse ALL no_connect flags
no_connects = []
for m in re.finditer(r'\(no_connect\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\)', text):
    no_connects.append((float(m.group(1)), float(m.group(2))))

def wire_endpoints_at(x, y, tol=0.01):
    """Check if any wire has an endpoint at (x,y)."""
    hits = []
    for x1, y1, x2, y2 in wires:
        if abs(x1-x) < tol and abs(y1-y) < tol:
            hits.append(('start', x1, y1, x2, y2))
        if abs(x2-x) < tol and abs(y2-y) < tol:
            hits.append(('end', x1, y1, x2, y2))
    return hits

def point_on_wire_mid(x, y, tol=0.01):
    """Check if (x,y) is on a wire but NOT at an endpoint."""
    hits = []
    for x1, y1, x2, y2 in wires:
        # Skip if it's an endpoint
        if (abs(x1-x) < tol and abs(y1-y) < tol) or (abs(x2-x) < tol and abs(y2-y) < tol):
            continue
        # Check if point is on segment
        if abs(x1 - x2) < tol:  # Vertical wire
            if abs(x - x1) < tol and min(y1, y2) - tol <= y <= max(y1, y2) + tol:
                hits.append((x1, y1, x2, y2))
        elif abs(y1 - y2) < tol:  # Horizontal wire
            if abs(y - y1) < tol and min(x1, x2) - tol <= x <= max(x1, x2) + tol:
                hits.append((x1, y1, x2, y2))
    return hits

print("=" * 70)
print("PIN-LEVEL WIRE CONNECTION ANALYSIS")
print("=" * 70)

# ===== #PWR063 at (55.0, 42.54) =====
print("\n--- #PWR063 (GND) Pin at (55.0, 42.54) ---")
ep = wire_endpoints_at(55.0, 42.54)
mid = point_on_wire_mid(55.0, 42.54)
print(f"  Wire endpoints here: {len(ep)}")
print(f"  Mid-wire passes: {len(mid)}")
for w in mid:
    print(f"    Wire: ({w[0]},{w[1]})→({w[2]},{w[3]})")
# Check junction
jn = [j for j in junctions if abs(j[0]-55.0) < 0.01 and abs(j[1]-42.54) < 0.01]
print(f"  Junctions here: {len(jn)}")
# Check no_connect
nc = [n for n in no_connects if abs(n[0]-55.0) < 0.01 and abs(n[1]-42.54) < 0.01]
print(f"  No-connect: {len(nc)}")
print(f"  DIAGNOSIS: {'CONNECTED' if ep else 'FLOATING (no wire endpoint)'}")

# ===== 6× Channel GND power symbols =====
print("\n--- 6× Channel GND Power Symbols at x=285 ---")
for ref, ypos in [('#PWR014', 115.0), ('#PWR083', 195.0), ('#PWR005', 275.0),
                   ('#PWR088', 355.0), ('#PWR028', 435.0), ('#PWR037', 515.0)]:
    ep = wire_endpoints_at(285.0, ypos)
    mid = point_on_wire_mid(285.0, ypos)
    jn = [j for j in junctions if abs(j[0]-285.0) < 0.01 and abs(j[1]-ypos) < 0.01]
    status = "CONNECTED" if ep or jn else ("MID-WIRE" if mid else "FLOATING")
    print(f"  {ref} at (285.0, {ypos}): endpoints={len(ep)}, mid-wire={len(mid)}, junctions={len(jn)} → {status}")
    if mid:
        for w in mid:
            print(f"    Mid-wire: ({w[0]},{w[1]})→({w[2]},{w[3]})")

# ===== #PWR001 at (98.0, 18.65) =====
print("\n--- #PWR001 (GND) Pin at (98.0, 18.65) ---")
ep = wire_endpoints_at(98.0, 18.65)
mid = point_on_wire_mid(98.0, 18.65)
print(f"  Wire endpoints: {len(ep)}")
for e in ep:
    print(f"    {e[0]}: ({e[1]},{e[2]})→({e[3]},{e[4]})")
print(f"  Mid-wire: {len(mid)}")
# What's at the other end of this wire?
if ep:
    for e in ep:
        other_x = e[3] if e[0] == 'start' else e[1]
        other_y = e[4] if e[0] == 'start' else e[2]
        print(f"  Other end of wire: ({other_x}, {other_y})")
        # What connects at this other end?
        ep2 = wire_endpoints_at(other_x, other_y)
        print(f"    Wire endpoints at other end: {len(ep2)}")
        for e2 in ep2:
            print(f"      {e2[0]}: ({e2[1]},{e2[2]})→({e2[3]},{e2[4]})")

# What else is at (98, 18.65)? Any power symbols?
# Check what else connects at the wire's other endpoint
print("\n  Tracing from #PWR001 to find connected pins:")
visited = set()
to_visit = [(98.0, 18.65)]
connected_points = []
while to_visit:
    px, py = to_visit.pop()
    key = (round(px, 2), round(py, 2))
    if key in visited:
        continue
    visited.add(key)
    connected_points.append(key)
    # Find all wires with endpoint here
    for x1, y1, x2, y2 in wires:
        if abs(x1-px) < 0.01 and abs(y1-py) < 0.01:
            to_visit.append((x2, y2))
        elif abs(x2-px) < 0.01 and abs(y2-py) < 0.01:
            to_visit.append((x1, y1))
print(f"  Wire-connected points: {connected_points}")

# ===== SS_U14 label at (132.38, 30.0) =====
print("\n--- SS_U14 Label at (132.38, 30.0) ---")
ep = wire_endpoints_at(132.38, 30.0)
mid = point_on_wire_mid(132.38, 30.0)
print(f"  Wire endpoints: {len(ep)}")
for e in ep:
    print(f"    {e[0]}: ({e[1]},{e[2]})→({e[3]},{e[4]})")
# Trace this net
visited2 = set()
to_visit2 = [(132.38, 30.0)]
ss_points = []
while to_visit2:
    px, py = to_visit2.pop()
    key = (round(px, 2), round(py, 2))
    if key in visited2:
        continue
    visited2.add(key)
    ss_points.append(key)
    for x1, y1, x2, y2 in wires:
        if abs(x1-px) < 0.01 and abs(y1-py) < 0.01:
            to_visit2.append((x2, y2))
        elif abs(x2-px) < 0.01 and abs(y2-py) < 0.01:
            to_visit2.append((x1, y1))
print(f"  Connected wire points: {ss_points}")

# ===== C22 at (147.62, 38.0) =====
print("\n--- C22 (100nF C0G) Pin Connection Check ---")
# Device:C standard pin positions (from lib_symbols)
# Need to check actual cache
cache_start = text.find('(lib_symbols')
c_start = text.find('"Device:C"', cache_start) if cache_start >= 0 else -1
if c_start >= 0:
    chunk = text[c_start:c_start+2000]
    pins = re.findall(r'\(pin\s+\w+\s+\w+\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+\d+)?\).*?\(number\s+"(\d+)"', chunk)
    print(f"  Device:C pin positions in cache:")
    for px, py, pnum in pins:
        print(f"    Pin {pnum}: local ({px}, {py})")
        # Calculate schematic position (rotation 0)
        sch_x = 147.62 + float(px)
        sch_y = 38.0 + float(py)
        print(f"    Pin {pnum}: schematic ({sch_x:.2f}, {sch_y:.2f})")
        ep = wire_endpoints_at(sch_x, sch_y)
        mid = point_on_wire_mid(sch_x, sch_y)
        print(f"    Pin {pnum}: endpoints={len(ep)}, mid-wire={len(mid)}")
        if ep:
            for e in ep:
                print(f"      {e[0]}: ({e[1]},{e[2]})→({e[3]},{e[4]})")

# What's connected to C22 Pin 2?
print("\n  Tracing C22 Pin 2 network:")
# Need pin 2 position first — let's check what the netlist says about C22
with open("/tmp/revalidation_netlist.net", "r") as f:
    netlist = f.read()

# Find C22 in netlist nets
print("\n  C22 nets in netlist:")
for m in re.finditer(r'\(net \(code "(\d+)"\) \(name "([^"]*)"\)(.*?)\)\)', netlist, re.DOTALL):
    if 'C22' in m.group(3):
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "(\d+)"\)', m.group(3))
        print(f"    Net '{m.group(2)}' (code {m.group(1)}): {nodes}")

# ===== Check for PWR_FLAG symbols =====
print("\n" + "=" * 70)
print("PWR_FLAG ANALYSIS")
print("=" * 70)
pwr_flags = []
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"power:PWR_FLAG"\)', text):
    start = m.start()
    chunk = text[start:start+1500]
    at_m = re.search(r'\(at\s+([\d.\-]+)\s+([\d.\-]+)', chunk)
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
    if at_m:
        x, y = float(at_m.group(1)), float(at_m.group(2))
        ref = ref_m.group(1) if ref_m else "?"
        pwr_flags.append((ref, x, y))
        print(f"  {ref}: PWR_FLAG at ({x}, {y})")

if not pwr_flags:
    print("  ⚠️ KEINE PWR_FLAG Symbole im Schaltplan gefunden!")
    print("  → Dies erklärt den 'power_pin_not_driven' Error!")

# ===== Check for the 6 channel GND connections at 285 =====
print("\n" + "=" * 70)
print("CHANNEL GND DETAIL — What's at (285, 117) for each channel?")
print("=" * 70)
for ypos_lower, ypos_upper in [(117.0, 115.0), (197.0, 195.0), (277.0, 275.0),
                                (357.0, 355.0), (437.0, 435.0), (517.0, 515.0)]:
    ep_lower = wire_endpoints_at(285.0, ypos_lower)
    ep_upper = wire_endpoints_at(285.0, ypos_upper)
    mid_upper = point_on_wire_mid(285.0, ypos_upper)
    print(f"\n  y={ypos_upper} (orphaned #PWR): endpoints={len(ep_upper)}, mid-wire={len(mid_upper)}")
    print(f"  y={ypos_lower} (connected GND):  endpoints={len(ep_lower)}")
    if mid_upper:
        print(f"    → Mid-wire kill: wire passes through y={ypos_upper}")
        for w in mid_upper:
            print(f"      Wire: ({w[0]},{w[1]})→({w[2]},{w[3]})")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
