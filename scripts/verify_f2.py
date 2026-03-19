#!/usr/bin/env python3
"""Verify F2 fix: check that HOT_RAW nets exist and OUT_COLD is correct."""
import subprocess, re

sch = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
cli = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
out = "/tmp/test_netlist7.net"

r = subprocess.run([cli, "sch", "export", "netlist", "--output", out, sch],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("FAIL:", r.stderr)
    exit(1)
print("Netlist export: OK")

with open(out) as f:
    c = f.read()

# Parse nets
nets = {}
for m in re.finditer(r'\(net \(code "(\d+)"\) \(name "([^"]*)"\)', c):
    code, name = m.group(1), m.group(2)
    start = m.start()
    depth = 0
    for i in range(start, len(c)):
        if c[i] == '(': depth += 1
        elif c[i] == ')': depth -= 1
        if depth == 0: break
    block = c[start:i+1]
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)
    nets[name] = nodes

pin_to_net = {}
for nname, nodes in nets.items():
    for ref, pin in nodes:
        pin_to_net[(ref, pin)] = nname

# Show HOT_RAW nets
print("\n=== HOT_RAW nets ===")
for n in sorted(nets):
    if 'HOT_RAW' in n:
        print(f"  {n}: {len(nets[n])} nodes -> {nets[n]}")

# Show OUT_COLD nets
print("\n=== OUT_COLD nets ===")
for n in sorted(nets):
    if 'OUT_COLD' in n:
        print(f"  {n}: {len(nets[n])} nodes -> {nets[n]}")

# Verify J3-J8.pin2 moved to HOT_RAW
print("\n=== XLR Input Hot (J3-J8.pin2) ===")
for j in ['J3','J4','J5','J6','J7','J8']:
    net = pin_to_net.get((j, '2'), 'NOT FOUND')
    ok = 'HOT_RAW' in net
    print(f"  {j}.2 -> {net} {'✓' if ok else '✗'}")

# Verify R94-R104.pin1 moved to HOT_RAW 
print("\n=== EMI Filter R.pin1 (R94,R96,R98,R100,R102,R104) ===")
for r in ['R94','R96','R98','R100','R102','R104']:
    net = pin_to_net.get((r, '1'), 'NOT FOUND')
    ok = 'HOT_RAW' in net
    print(f"  {r}.1 -> {net} {'✓' if ok else '✗'}")

# Verify J9-J14.pin3 still on OUT_COLD
print("\n=== XLR Output Cold (J9-J14.pin3) ===")
for j in ['J9','J10','J11','J12','J13','J14']:
    net = pin_to_net.get((j, '3'), 'NOT FOUND')
    ok = 'OUT_COLD' in net
    print(f"  {j}.3 -> {net} {'✓' if ok else '✗'}")

# Verify R88-R93.pin1 still on OUT_COLD (Zobel cold)
print("\n=== Zobel Cold R.pin1 (R88-R93) ===")
for r in ['R88','R89','R90','R91','R92','R93']:
    net = pin_to_net.get((r, '1'), 'NOT FOUND')
    ok = 'OUT_COLD' in net
    print(f"  {r}.1 -> {net} {'✓' if ok else '✗'}")

# Check GND count
print(f"\n=== GND: {len(nets.get('GND',[]))} nodes ===")

# Show feedback R20-R25 (for F4 reference)
print("\n=== Feedback R20-R25 ===")
for r in ['R20','R21','R22','R23','R24','R25']:
    for p in ['1','2']:
        net = pin_to_net.get((r, p), 'NOT FOUND')
        print(f"  {r}.{p} -> {net}")

# Show Rgnd R2,R4,R6,R8,R10,R12 (for F5/F6 reference)
print("\n=== Rgnd R2,R4,R6,R8,R10,R12 ===")
for r in ['R2','R4','R6','R8','R10','R12']:
    for p in ['1','2']:
        net = pin_to_net.get((r, p), 'NOT FOUND')
        print(f"  {r}.{p} -> {net}")
