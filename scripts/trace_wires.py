#!/usr/bin/env python3
"""Trace wire network to find where GND and signal wires are bridged.

Strategy: Build a wire connectivity graph, then for each incorrectly-GNDed pin,
trace back through the wire network to find the bridge point.
"""
import re
import os
from collections import defaultdict

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
SCH_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_sch")

with open(SCH_FILE) as f:
    sch = f.read()

def extract_balanced_block(content, start_idx):
    depth = 0
    for i in range(start_idx, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
        if depth == 0:
            return content[start_idx:i + 1], i + 1
    raise ValueError(f"Unbalanced parens at {start_idx}")

# ============================================================
# 1. Parse all wire segments
# ============================================================
wires = []
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', sch):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    line = sch[:m.start()].count('\n') + 1
    wires.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'line': line, 'start': m.start()})

print(f"Total wires: {len(wires)}")

# ============================================================
# 2. Parse all labels (regular labels that remain)
# ============================================================
labels = []
for m in re.finditer(r'\(label "([^"]+)" \(at ([\d.]+) ([\d.]+) (\d+)\)', sch):
    name, x, y, angle = m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4))
    labels.append({'name': name, 'x': x, 'y': y})

print(f"Total labels: {len(labels)}")

# ============================================================
# 3. Parse all power:GND symbol positions
# ============================================================
gnd_symbols = []
for m in re.finditer(r'\(symbol \(lib_id "power:GND"\) \(at ([\d.]+) ([\d.]+)', sch):
    x, y = float(m.group(1)), float(m.group(2))
    gnd_symbols.append({'x': x, 'y': y})

print(f"power:GND symbols: {len(gnd_symbols)}")

# ============================================================
# 4. Build connectivity graph
# Wire endpoints that are at the same position are connected.
# Labels and power symbols connect at their position.
# ============================================================
# Use a union-find structure to group connected points
EPS = 0.01  # tolerance for position matching

def coord_key(x, y):
    """Round to nearest 0.01 to handle floating point."""
    return (round(x, 2), round(y, 2))

parent = {}
def find(p):
    while parent.get(p, p) != p:
        parent[p] = parent.get(parent[p], parent[p])
        p = parent[p]
    return p

def union(a, b):
    a, b = find(a), find(b)
    if a != b:
        parent[a] = b

# Connect wire endpoints
for w in wires:
    p1 = coord_key(w['x1'], w['y1'])
    p2 = coord_key(w['x2'], w['y2'])
    union(p1, p2)

# Group all points by their root
groups = defaultdict(set)
all_points = set()
for w in wires:
    p1 = coord_key(w['x1'], w['y1'])
    p2 = coord_key(w['x2'], w['y2'])
    all_points.add(p1)
    all_points.add(p2)

for p in all_points:
    groups[find(p)].add(p)

print(f"\nWire network groups: {len(groups)}")
print(f"Largest groups:")
sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))
for root, points in sorted_groups[:5]:
    print(f"  Group {root}: {len(points)} points")

# ============================================================
# 5. Check which groups have GND AND OUT_COLD labels
# ============================================================
print("\n=== Checking for GND/OUT_COLD overlap ===")

# For each power:GND symbol, find its wire group
gnd_groups = set()
for gs in gnd_symbols:
    p = coord_key(gs['x'], gs['y'])
    root = find(p)
    gnd_groups.add(root)

# For each OUT_COLD label, find its wire group
out_cold_labels_on_gnd = []
for lbl in labels:
    if 'OUT_COLD' in lbl['name']:
        p = coord_key(lbl['x'], lbl['y'])
        root = find(p)
        on_gnd = root in gnd_groups
        print(f"  {lbl['name']:20s} at ({lbl['x']}, {lbl['y']}) → group {root} → {'ON GND!' if on_gnd else 'separate'}")
        if on_gnd:
            out_cold_labels_on_gnd.append(lbl)

print(f"\nOUT_COLD labels on GND wire chain: {len(out_cold_labels_on_gnd)}")

# Check HOT_IN labels
print("\n=== HOT_IN labels ===")
for lbl in labels:
    if 'HOT_IN' in lbl['name']:
        p = coord_key(lbl['x'], lbl['y'])
        root = find(p)
        on_gnd = root in gnd_groups
        print(f"  {lbl['name']:20s} at ({lbl['x']}, {lbl['y']}) → {'ON GND!' if on_gnd else 'separate'}")

# How many distinct GND groups?
print(f"\n=== GND wire groups ===")
print(f"  {len(gnd_groups)} distinct GND groups")
for g in gnd_groups:
    size = len(groups.get(g, set()))
    print(f"  Group {g}: {size} points")
