#!/usr/bin/env python3
"""Analyze which CH*_OUT_COLD labels exist and where they are."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    sch = f.read()

print("=== All OUT_COLD labels ===")
for m in re.finditer(r'\(label "([^"]*OUT_COLD[^"]*)" \(at ([\d.]+) ([\d.]+) (\d+)\)', sch):
    name, x, y, angle = m.group(1), m.group(2), m.group(3), m.group(4)
    line = sch[:m.start()].count('\n') + 1
    print(f"  {name:20s} at ({x:>6s}, {y:>6s}) angle={angle} line={line}")

print("\n=== All HOT_IN labels ===")
for m in re.finditer(r'\(label "([^"]*HOT_IN[^"]*)" \(at ([\d.]+) ([\d.]+) (\d+)\)', sch):
    name, x, y, angle = m.group(1), m.group(2), m.group(3), m.group(4)
    line = sch[:m.start()].count('\n') + 1
    print(f"  {name:20s} at ({x:>6s}, {y:>6s}) angle={angle} line={line}")

print("\n=== All HOT_RAW / COLD_RAW labels ===")
for m in re.finditer(r'\(label "([^"]*(?:HOT_RAW|COLD_RAW)[^"]*)" \(at ([\d.]+) ([\d.]+) (\d+)\)', sch):
    name, x, y, angle = m.group(1), m.group(2), m.group(3), m.group(4)
    line = sch[:m.start()].count('\n') + 1
    print(f"  {name:20s} at ({x:>6s}, {y:>6s}) angle={angle} line={line}")

# Check net names in netlist to see which nets have which labels
print("\n=== Checking GND net in netlist ===")
with open("/tmp/test_netlist3.net") as f:
    nl = f.read()

# Find all nets and their components
gnd_idx = nl.find('(name "GND")')
if gnd_idx > 0:
    # Go back to find (net start
    net_start = nl.rfind('(net ', 0, gnd_idx)
    depth = 0
    for i in range(net_start, len(nl)):
        if nl[i] == '(': depth += 1
        elif nl[i] == ')': depth -= 1
        if depth == 0:
            gnd_block = nl[net_start:i+1]
            break
    # Count nodes
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', gnd_block)
    print(f"  GND net: {len(nodes)} nodes")
    # Show J, Q, U nodes
    for ref, pin in sorted(nodes):
        if ref.startswith(('J', 'Q', 'U')):
            print(f"    {ref}.{pin}")
