#!/usr/bin/env python3
"""Verify F1 fix: Check GND net separation via S-expression netlist."""
import re

NETLIST = "/tmp/test_netlist3.net"
with open(NETLIST, 'r') as f:
    content = f.read()

nets = {}
for m in re.finditer(r'\(net \(code (\d+)\) \(name "([^"]*)"', content):
    code, name = m.group(1), m.group(2)
    start = m.start()
    depth = 0
    for i in range(start, len(content)):
        if content[i] == '(': depth += 1
        elif content[i] == ')': depth -= 1
        if depth == 0:
            end = i + 1
            break
    block = content[start:end]
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)
    nets[name] = {'code': code, 'nodes': nodes, 'count': len(nodes)}

print("=== F1 Verification ===\n")
print("Large nets (>20 pins):")
for name, info in sorted(nets.items(), key=lambda x: -x[1]['count']):
    if info['count'] > 20:
        print(f"  {name}: {info['count']} pins")

gnd = nets.get('GND') or nets.get('/GND')
ch1_cold = nets.get('/CH1_OUT_COLD') or nets.get('CH1_OUT_COLD')

print(f"\nGND: {gnd['count'] if gnd else 'NOT FOUND'} pins")
print(f"\nOUT_COLD Nets:")
for name in sorted(nets.keys()):
    if 'OUT_COLD' in name:
        print(f"  {name}: {nets[name]['count']} pins")

print(f"\nBSS138 Source (Pin 2):")
for name, info in nets.items():
    for ref, pin in info['nodes']:
        if ref.startswith('Q') and pin == '2':
            print(f"  {ref}.Pin2 -> {name}")

print(f"\nXLR Input Hot (J3-J8 Pin 2):")
for name, info in nets.items():
    for ref, pin in info['nodes']:
        if ref in ['J3','J4','J5','J6','J7','J8'] and pin == '2':
            print(f"  {ref}.Pin2 -> {name}")

print(f"\nXLR Output Cold (J9-J14 Pin 3):")
for name, info in nets.items():
    for ref, pin in info['nodes']:
        if ref in ['J9','J10','J11','J12','J13','J14'] and pin == '3':
            print(f"  {ref}.Pin3 -> {name}")

print(f"\n=== SUMMARY ===")
gnd_ok = gnd and gnd['count'] > 100
print(f"  GND separate: {'PASS' if gnd_ok else 'FAIL'} ({gnd['count'] if gnd else 0} pins)")
cold_ok = ch1_cold and ch1_cold['count'] < 20
print(f"  CH1_OUT_COLD separate: {'PASS' if cold_ok else 'FAIL'} ({ch1_cold['count'] if ch1_cold else 0} pins)")
cold_nets = [n for n in nets if 'OUT_COLD' in n]
print(f"  All 6 OUT_COLD: {'PASS' if len(cold_nets) >= 6 else 'FAIL'} ({len(cold_nets)} found)")
