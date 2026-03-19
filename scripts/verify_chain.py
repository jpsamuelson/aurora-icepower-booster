#!/usr/bin/env python3
"""Verify the entire CH1 signal chain from XLR input to Op-Amp, 
including ESD, EMI filter, DC blocking, using the netlist."""
import subprocess, re

# Export fresh netlist
sch = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
cli = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
out = "/tmp/test_netlist6.net"

r = subprocess.run([cli, "sch", "export", "netlist", "--output", out, sch],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("Netlist export FAILED:", r.stderr)
    exit(1)

with open(out) as f:
    c = f.read()

# Parse all nets with their nodes
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

# Build reverse map: (ref, pin) -> net_name
pin_to_net = {}
for nname, nodes in nets.items():
    for ref, pin in nodes:
        pin_to_net[(ref, pin)] = nname

# Show all TVS diodes (D2-D25)
print("=== TVS Diodes (D2-D25) ===")
for i in range(2, 26):
    ref = f"D{i}"
    for pin in ['1', '2', 'A', 'K']:
        key = (ref, pin)
        if key in pin_to_net:
            print(f"  {ref}.{pin} -> {pin_to_net[key]}")

# Show complete CH1 signal chain
print("\n=== CH1 Complete Signal Chain (Input) ===")
# XLR connector J3
for pin in ['1', '2', '3', 'G', 'S', 'T']:
    key = ('J3', pin)
    if key in pin_to_net:
        print(f"  J3.{pin} -> {pin_to_net[key]}")

# EMI filter resistors (47 ohm) - look for R with "47" on CH1 nets
print("\n  EMI/Filter components on CH1 nets:")
for nname in sorted(nets):
    if 'CH1' in nname:
        print(f"  Net '{nname}':")
        for ref, pin in nets[nname]:
            print(f"    {ref}.{pin}")

# Show CH1 output chain too
print("\n=== CH1 Complete Signal Chain (Output) ===")
for pin in ['1', '2', '3', 'G', 'S', 'T']:
    key = ('J9', pin)
    if key in pin_to_net:
        print(f"  J9.{pin} -> {pin_to_net[key]}")

print("\n  Nets with OUT_COLD/OUT_HOT:")
for nname in sorted(nets):
    if 'CH1_OUT' in nname:
        print(f"  Net '{nname}':")
        for ref, pin in nets[nname]:
            print(f"    {ref}.{pin}")

# Check: are there unconnected nets?
print("\n=== Unconnected pins ===")
for nname, nodes in nets.items():
    if 'unconnected' in nname.lower():
        for ref, pin in nodes:
            print(f"  {ref}.{pin} -> {nname}")

# Show all R2 connections (Rgnd CH1)
print("\n=== R2 (Rgnd CH1) ===")
for pin in ['1', '2']:
    key = ('R2', pin)
    if key in pin_to_net:
        print(f"  R2.{pin} -> {pin_to_net[key]}")

# Show all R3 connections
print("\n=== R3 ===")
for pin in ['1', '2']:
    key = ('R3', pin)
    if key in pin_to_net:
        print(f"  R3.{pin} -> {pin_to_net[key]}")
