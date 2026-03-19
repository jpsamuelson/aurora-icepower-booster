#!/usr/bin/env python3
"""Quick netlist verification after F1 fix."""
import re

with open("/tmp/test_netlist4.net") as f:
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

print(f"GND: {len(nets.get('GND',[]))} nodes")

print("\nOUT_COLD nets:")
for n in sorted(nets):
    if 'OUT_COLD' in n:
        print(f"  {n}: {len(nets[n])} nodes -> {nets[n]}")

print("\nHOT_IN nets:")
for n in sorted(nets):
    if 'HOT_IN' in n:
        print(f"  {n}: {len(nets[n])} nodes")

print("\nBSS138 Source (Q.pin2):")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref.startswith('Q') and pin == '2':
            print(f"  {ref}.2 -> {n}")

print("\nXLR Input Hot (J3-J8.pin2):")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref in ['J3','J4','J5','J6','J7','J8'] and pin == '2':
            print(f"  {ref}.2 -> {n}")

print("\nXLR Output Cold (J9-J14.pin3):")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref in ['J9','J10','J11','J12','J13','J14'] and pin == '3':
            print(f"  {ref}.3 -> {n}")

print("\nOpAmp NINV_B (U.pin5):")
for n, nodes in nets.items():
    for ref, pin in nodes:
        if ref.startswith('U') and ref not in ['U1','U14','U15'] and pin == '5':
            print(f"  {ref}.5 -> {n}")
