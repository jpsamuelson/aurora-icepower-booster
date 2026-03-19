#!/usr/bin/env python3
"""Deep analysis of GND net to find unexpected connections."""
import re

with open("/tmp/test_netlist3.net") as f:
    nl = f.read()

# Parse ALL nets
nets = {}
pos = 0
while True:
    # Find next (net ...)
    idx = nl.find('(net (code', pos)
    if idx < 0:
        break
    # Extract balanced block
    depth = 0
    for i in range(idx, len(nl)):
        if nl[i] == '(': depth += 1
        elif nl[i] == ')': depth -= 1
        if depth == 0:
            block = nl[idx:i+1]
            break
    pos = i + 1
    
    code_m = re.search(r'code "(\d+)"', block)
    name_m = re.search(r'name "([^"]*)"', block)
    if code_m and name_m:
        name = name_m.group(1)
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)
        nets[name] = nodes

print(f"Total nets: {len(nets)}")
print(f"\nLargest nets:")
for name, nodes in sorted(nets.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"  {name}: {len(nodes)} nodes")

# GND analysis
gnd_nodes = nets.get('GND', [])
print(f"\n=== GND Net: {len(gnd_nodes)} nodes ===")
print("\nComponents on GND that should NOT be (signal components):")
for ref, pin in sorted(gnd_nodes):
    # J3-J8 Pin 2 = Hot IN → should NOT be GND
    if ref in ['J3','J4','J5','J6','J7','J8'] and pin == '2':
        print(f"  ❌ {ref}.{pin} (XLR Input Hot → should be CHx_HOT_IN)")
    # J9-J14 Pin 3 = Cold OUT → should NOT be GND
    elif ref in ['J9','J10','J11','J12','J13','J14'] and pin == '3':
        print(f"  ❌ {ref}.{pin} (XLR Output Cold → should be CHx_OUT_COLD)")
    # U OpAmp signal pins should NOT be GND (pins 1,2,3,5,6,7)
    elif ref.startswith('U') and ref not in ['U1','U14','U15'] and pin in ['1','2','3','5','6','7']:
        print(f"  ❌ {ref}.{pin} (OpAmp signal pin → should be signal)")

print("\nComponents on GND that SHOULD be:")
for ref, pin in sorted(gnd_nodes):
    if ref.startswith('Q') and pin == '2':
        print(f"  ✓ {ref}.{pin} (BSS138 Source → GND)")
    elif ref.startswith('#'):
        pass  # power flags
    elif ref in ['J3','J4','J5','J6','J7','J8'] and pin in ['1','G']:
        print(f"  ✓ {ref}.{pin} (XLR Shield/GND)")
    elif ref in ['J9','J10','J11','J12','J13','J14'] and pin == '1':
        print(f"  ✓ {ref}.{pin} (XLR GND)")

# Check OUT_COLD nets
print(f"\n=== OUT_COLD Nets ===")
for name in sorted(nets.keys()):
    if 'OUT_COLD' in name:
        nodes = nets[name]
        print(f"  {name}: {len(nodes)} nodes")
        for ref, pin in nodes:
            print(f"    {ref}.{pin}")

# Check HOT_IN nets
print(f"\n=== HOT_IN Nets ===")
for name in sorted(nets.keys()):
    if 'HOT_IN' in name:
        nodes = nets[name]
        print(f"  {name}: {len(nodes)} nodes - {[(r,p) for r,p in nodes[:5]]}")
