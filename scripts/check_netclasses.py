#!/usr/bin/env python3
"""Check net class assignments in KiCad 9 format."""
import json, re

with open("aurora-dsp-icepower-booster.kicad_pro") as f:
    pro = json.load(f)

ns = pro.get("net_settings", {})
assignments = ns.get("netclass_assignments", None) or {}
patterns = ns.get("netclass_patterns", None) or []
print(f"netclass_assignments: {len(assignments)} entries")
for k, v in list(assignments.items())[:15]:
    print(f"  {k} -> {v}")
print(f"netclass_patterns: {len(patterns)} entries")
for p in patterns[:10]:
    print(f"  {p}")

# Check PCB for net class info
with open("aurora-dsp-icepower-booster.kicad_pcb") as f:
    pcb = f.read()

# KiCad 9: net classes stored in setup section
nc_setup = re.findall(r'\(net_class\s+"([^"]+)"\s+"([^"]*)"', pcb)
print(f"\nnet_class in PCB setup: {len(nc_setup)}")
for nc in nc_setup[:5]:
    print(f"  {nc}")

# Check if nets have class assignments in PCB
nc_assigns = re.findall(r'\(netclass_assignments\s*\n(.*?)\)', pcb, re.DOTALL)
print(f"\nnetclass_assignments blocks in PCB: {len(nc_assigns)}")

# Check board_setup for net classes
board_setup = re.search(r'\(setup\s+(.*?)\n\t\)', pcb, re.DOTALL)
if board_setup:
    setup = board_setup.group(1)
    print(f"\nSetup section: {len(setup)} chars")
    
# Trace width distribution tells us what widths are actually used
from collections import Counter
widths = Counter()
for m in re.finditer(r'\(segment.*?\(width ([\d.]+)\)', pcb):
    widths[float(m.group(1))] += 1
print("\nTrace width distribution:")
for w, c in widths.most_common():
    print(f"  {w}mm: {c} segments")

# Via size distribution
via_sizes = Counter()
for m in re.finditer(r'\(via.*?\(size ([\d.]+)\).*?\(drill ([\d.]+)\)', pcb):
    via_sizes[(float(m.group(1)), float(m.group(2)))] += 1
print("\nVia size distribution:")
for (s, d), c in via_sizes.most_common():
    print(f"  size={s}mm drill={d}mm: {c} vias")

# Check which nets USE non-default widths (actual routing constraints)
print("\nNets with non-default trace widths:")
net_widths = {}
for m in re.finditer(r'\(segment.*?\(width ([\d.]+)\).*?\(net (\d+)\)', pcb):
    w = float(m.group(1))
    nid = int(m.group(2))
    if nid not in net_widths:
        net_widths[nid] = set()
    net_widths[nid].add(w)

net_map = {}
for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', pcb):
    net_map[int(m.group(1))] = m.group(2)

for nid, ws in sorted(net_widths.items()):
    name = net_map.get(nid, f"net_{nid}")
    if any(w != 0.25 for w in ws):
        print(f"  {name}: {sorted(ws)}")
