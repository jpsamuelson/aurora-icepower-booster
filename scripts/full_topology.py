#!/usr/bin/env python3
"""Build complete wire + component pin topology using union-find.
Traces which labels, power symbols, and component pins are on each wire group.
This tells us exactly which labels need to be renamed and which GND power
symbols need to be removed."""
import re, math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# ---- Parse lib_symbols cache for pin offsets ----
def parse_lib_symbols():
    """Extract pin positions from each lib_symbol in cache."""
    pin_data = {}  # lib_name -> [(pin_name, x, y)]
    
    # Find lib_symbols section
    idx = text.find('(lib_symbols')
    if idx == -1:
        return pin_data
    
    # Find all symbols in lib_symbols
    pos = idx
    while True:
        pos = text.find('(symbol "', pos + 1)
        if pos == -1 or pos > text.find('(symbol (lib_id'):
            break
        
        # Get symbol name
        end_quote = text.find('"', pos + 9)
        sym_name = text[pos+9:end_quote]
        
        # Only collect sub-symbols (like "Device:R_0_1") that have pins
        if '_' not in sym_name.split(':')[-1]:
            continue
        
        # Find pins in this sub-symbol
        depth = 0
        block_start = pos
        for i in range(pos, len(text)):
            if text[i] == '(': depth += 1
            elif text[i] == ')': depth -= 1
            if depth == 0:
                break
        block = text[pos:i+1]
        
        # Parent symbol name (without _0_1 suffix)
        parts = sym_name.rsplit('_', 2)
        if len(parts) >= 3:
            parent = '_'.join(parts[:-2])
        else:
            parent = sym_name
        
        for pm in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+).*?\(name "([^"]*)".*?\(number "([^"]*)"', block, re.DOTALL):
            px, py = float(pm.group(1)), float(pm.group(2))
            pname = pm.group(3)
            pnum = pm.group(4)
            if parent not in pin_data:
                pin_data[parent] = []
            pin_data[parent].append((pnum, px, py))
        
        pos = i
    
    return pin_data

# We'll use a simpler approach: extract pin positions directly from symbol instances
# by looking at the actual connectivity in the netlist + wire positions

# ---- Parse wires ----
wires = []
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    wires.append(((float(m.group(1)), float(m.group(2))),
                  (float(m.group(3)), float(m.group(4)))))

# ---- Parse labels ----
labels = []
idx = 0
while True:
    idx = text.find('(label "', idx)
    if idx == -1:
        break
    start = idx
    nm_end = text.find('"', idx + 8)
    name = text[idx+8:nm_end]
    # Find position
    at_m = re.search(r'\(at ([\d.]+) ([\d.]+)', text[start:start+300])
    if at_m:
        lx, ly = float(at_m.group(1)), float(at_m.group(2))
        labels.append((name, lx, ly, start))
    idx = nm_end + 1

# ---- Parse power symbols ----
power_syms = []
# Power symbols are (symbol (lib_id "power:GND") ... (at x y ...) 
for m in re.finditer(r'\(symbol \(lib_id "power:GND"\)', text):
    start = m.start()
    # Find position
    at_m = re.search(r'\(at ([\d.]+) ([\d.]+)', text[start:start+500])
    ref_m = re.search(r'\(property "Reference" "([^"]+)"', text[start:start+1000])
    if at_m:
        px, py = float(at_m.group(1)), float(at_m.group(2))
        ref = ref_m.group(1) if ref_m else "?"
        power_syms.append(('GND', px, py, ref, start))

print(f"Parsed {len(wires)} wires, {len(labels)} labels, {len(power_syms)} GND power symbols")

# ---- Union-Find ----
class UnionFind:
    def __init__(self):
        self.parent = {}
    def _key(self, pt):
        return (round(pt[0], 2), round(pt[1], 2))
    def find(self, pt):
        x = self._key(pt)
        if x not in self.parent:
            self.parent[x] = x
        path = [x]
        while self.parent[x] != x:
            x = self.parent[x]
            path.append(x)
        for p in path:
            self.parent[p] = x
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

uf = UnionFind()

# Add wire endpoints
for (x1,y1), (x2,y2) in wires:
    uf.union((x1,y1), (x2,y2))

# Touch labels (ensure they're in the UF)
for name, lx, ly, _ in labels:
    uf.find((lx, ly))

# Touch power symbols
for name, px, py, ref, _ in power_syms:
    uf.find((px, py))

# ---- Group analysis ----
# Build groups: root -> {points, labels, power_syms}
groups = {}
all_points = set(uf.parent.keys())
for pt in all_points:
    root = uf.find(pt)
    if root not in groups:
        groups[root] = {'points': set(), 'labels': [], 'power': []}
    groups[root]['points'].add(pt)

for name, lx, ly, start in labels:
    pt = (round(lx,2), round(ly,2))
    root = uf.find(pt)
    if root in groups:
        groups[root]['labels'].append((name, lx, ly, start))

for name, px, py, ref, start in power_syms:
    pt = (round(px,2), round(py,2))
    root = uf.find(pt)
    if root in groups:
        groups[root]['power'].append((name, px, py, ref, start))

# ---- Find groups with OUT_COLD labels ----
print("\n=== Wire groups with OUT_COLD labels ===")
for root, g in sorted(groups.items(), key=lambda x: str(x[0])):
    outcold = [l for l in g['labels'] if 'OUT_COLD' in l[0]]
    if outcold:
        print(f"\nGroup at {root} ({len(g['points'])} points):")
        print(f"  Labels: {[(l[0], l[1], l[2]) for l in g['labels']]}")
        print(f"  Power:  {[(p[0], p[1], p[2], p[3]) for p in g['power']]}")
        # Show wire extent
        xs = [p[0] for p in g['points']]
        ys = [p[1] for p in g['points']]
        print(f"  Extent: x=[{min(xs):.1f}, {max(xs):.1f}], y=[{min(ys):.1f}, {max(ys):.1f}]")

# ---- Find groups with GND power symbols that might be misplaced ----
# These are groups that have GND power BUT are in the input area (near XLR connectors)
# and might be on signal wire groups
print("\n\n=== GND power symbol groups in input area (x < 60) ===")
for root, g in sorted(groups.items(), key=lambda x: str(x[0])):
    gnds = [p for p in g['power'] if p[0] == 'GND']
    if gnds:
        xs = [p[0] for p in g['points']]
        if min(xs) < 60:  # Input area
            other_labels = [l for l in g['labels'] if l[0] != 'GND']
            if len(g['points']) <= 10:  # Small groups (avoid the huge GND group)
                print(f"\nGroup at {root} ({len(g['points'])} points):")
                print(f"  Power: {[(p[3], p[1], p[2]) for p in gnds]}")
                print(f"  Labels: {[(l[0], l[1], l[2]) for l in g['labels']]}")
                ys = [p[1] for p in g['points']]
                print(f"  Points: x=[{min(xs):.1f}, {max(xs):.1f}], y=[{min(ys):.1f}, {max(ys):.1f}]")

# ---- Specifically look for groups that should be HOT_RAW ----
# These are groups in the y-range of each channel that have OUT_COLD labels at x~42
print("\n\n=== Suspected HOT_RAW groups (OUT_COLD at x=42) ===")
ch_y = {1: 110, 2: 190, 3: 270, 4: 350, 5: 430, 6: 510}
for ch, cy in ch_y.items():
    # Find the group with OUT_COLD label at (42, cy)
    for root, g in groups.items():
        for name, lx, ly, start in g['labels']:
            if f'CH{ch}_OUT_COLD' == name and 40 <= lx <= 44 and abs(ly - cy) < 5:
                print(f"\nCH{ch} input hot wire group (root={root}):")
                print(f"  All points: {sorted(g['points'])}")
                print(f"  Labels: {[(l[0], l[1], l[2]) for l in g['labels']]}")
                print(f"  Power: {[(p[3], p[1], p[2]) for p in g['power']]}")
