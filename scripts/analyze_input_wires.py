#!/usr/bin/env python3
"""Trace wire topology around the misplaced OUT_COLD labels at x=42 (input area).
Determine what the correct label should be and what components are affected."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# Parse all wires
wires = []
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    wires.append(((float(m.group(1)), float(m.group(2))),
                  (float(m.group(3)), float(m.group(4)))))

# Parse all labels
labels = []
for m in re.finditer(r'\(label "([^"]+)" \(at ([\d.]+) ([\d.]+)', text):
    labels.append((m.group(1), float(m.group(2)), float(m.group(3))))

# Parse all symbol instances with pin positions
# For each symbol, extract reference, lib_id, position, and pin UUIDs
def extract_symbols():
    """Extract symbol instances with their reference and position."""
    symbols = []
    # Find all symbol blocks
    idx = 0
    while True:
        idx = text.find('(symbol (lib_id', idx)
        if idx == -1:
            break
        start = idx
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '(': depth += 1
            elif text[i] == ')': depth -= 1
            if depth == 0: break
        block = text[start:i+1]
        
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
        pos_m = re.search(r'\(at ([\d.]+) ([\d.]+)', block)
        lib_m = re.search(r'lib_id "([^"]+)"', block)
        
        if ref_m and pos_m:
            ref = ref_m.group(1)
            pos = (float(pos_m.group(1)), float(pos_m.group(2)))
            lib = lib_m.group(1) if lib_m else "?"
            
            # Extract pins with their positions relative to symbol
            pins = []
            for pm in re.finditer(r'\(pin "([^"]+)" \(uuid', block):
                pins.append(pm.group(1))
            
            symbols.append({
                'ref': ref,
                'pos': pos,
                'lib': lib,
                'pins': pins
            })
        idx = i + 1
    return symbols

symbols = extract_symbols()

# Union-Find for wire connectivity
class UnionFind:
    def __init__(self):
        self.parent = {}
    def find(self, x):
        x = (round(x[0], 2), round(x[1], 2))
        if x not in self.parent:
            self.parent[x] = x
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def union(self, a, b):
        a = (round(a[0], 2), round(a[1], 2))
        b = (round(b[0], 2), round(b[1], 2))
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

uf = UnionFind()
for (x1,y1), (x2,y2) in wires:
    uf.union((x1,y1), (x2,y2))

# For each misplaced OUT_COLD label at x=42, find its wire group
print("=== Analyzing OUT_COLD labels at x=42 (INPUT area) ===\n")

for ch in range(1, 7):
    name = f"CH{ch}_OUT_COLD"
    # Find the OUT_COLD label at x=42 for this channel
    target = None
    for lbl_name, lx, ly in labels:
        if lbl_name == name and 40 <= lx <= 44:
            target = (lx, ly)
            break
    
    if not target:
        print(f"CH{ch}: No OUT_COLD label found at x=42")
        continue
    
    print(f"CH{ch}: OUT_COLD at ({target[0]}, {target[1]})")
    
    # Find the root of the wire group containing this label
    root = uf.find(target)
    
    # Find all points in this group
    group_points = set()
    for pt in uf.parent:
        if uf.find(pt) == root:
            group_points.add(pt)
    
    # Find all labels in this group
    group_labels = []
    for lbl_name, lx, ly in labels:
        pt = (round(lx, 2), round(ly, 2))
        if pt in uf.parent and uf.find(pt) == root:
            group_labels.append((lbl_name, lx, ly))
    
    print(f"  Wire group has {len(group_points)} points")
    print(f"  Labels on this group:")
    for ln, lx, ly in sorted(group_labels, key=lambda x: x[1]):
        marker = " ← WRONG!" if "OUT_COLD" in ln else ""
        print(f"    {ln} at ({lx}, {ly}){marker}")
    
    # Find symbols near this wire group (within 5 units of any group point)
    nearby = []
    for sym in symbols:
        sx, sy = sym['pos']
        for gx, gy in group_points:
            if abs(sx - gx) < 15 and abs(sy - gy) < 15:
                nearby.append(sym)
                break
    
    if nearby:
        print(f"  Nearby symbols:")
        for sym in sorted(nearby, key=lambda s: s['pos'][0]):
            print(f"    {sym['ref']} ({sym['lib']}) at {sym['pos']}")
    
    print()

# Also check: what is the correct label for the input hot path?
print("\n=== Signal chain analysis ===")
print("Expected hot input path per channel:")
print("  J*.pin2 → CH*_HOT_RAW(?) → TVS → CH*_EMI_HOT → 47Ω → CH*_HOT_IN → 2.2µF + Rin → OpAmp")
print()
print("Existing labels (count):")
for prefix in ['HOT_RAW', 'EMI_HOT', 'HOT_IN']:
    count = sum(1 for n,_,_ in labels if prefix in n)
    print(f"  *_{prefix}: {count}")
print()
print("Cold path for comparison:")
for prefix in ['COLD_RAW', 'EMI_COLD', 'COLD_IN']:
    count = sum(1 for n,_,_ in labels if prefix in n)
    print(f"  *_{prefix}: {count}")
