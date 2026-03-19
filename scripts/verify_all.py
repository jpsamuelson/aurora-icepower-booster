#!/usr/bin/env python3
"""Export netlist and verify F1 fix."""
import subprocess, sys

# Step 1: Export netlist
sch = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
cli = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
out = "/tmp/test_netlist5.net"

r = subprocess.run([cli, "sch", "export", "netlist", "--output", out, sch],
                   capture_output=True, text=True)
print("Netlist export:", "OK" if r.returncode == 0 else "FAIL")
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

# Step 2: Parse netlist
import re
with open(out) as f:
    c = f.read()

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

print(f"\nGND: {len(nets.get('GND',[]))} nodes")

print("\n--- OUT_COLD nets ---")
for n in sorted(nets):
    if 'OUT_COLD' in n:
        print(f"  {n}: {len(nets[n])} nodes -> {nets[n]}")

print("\n--- HOT_IN nets ---")
for n in sorted(nets):
    if 'HOT_IN' in n:
        print(f"  {n}: {len(nets[n])} nodes -> {nets[n]}")

print("\n--- XLR Input Hot (J3-J8.pin2) ---")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref in ['J3','J4','J5','J6','J7','J8'] and pin == '2':
            print(f"  {ref}.2 -> net '{n}'")

print("\n--- XLR Output Cold (J9-J14.pin3) ---")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref in ['J9','J10','J11','J12','J13','J14'] and pin == '3':
            print(f"  {ref}.3 -> net '{n}'")

print("\n--- OpAmp NINV_B (U.pin5) ---")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref.startswith('U') and ref not in ['U1','U14','U15'] and pin == '5':
            print(f"  {ref}.5 -> net '{n}'")

print("\n--- Feedback R20-R25 ---")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref in ['R20','R21','R22','R23','R24','R25']:
            print(f"  {ref}.{pin} -> net '{n}'")

print("\n--- Rgnd R2,R4,R6,R8,R10,R12 ---")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref in ['R2','R4','R6','R8','R10','R12']:
            print(f"  {ref}.{pin} -> net '{n}'")
