#!/usr/bin/env python3
"""Find all wires near x=280, y=104-106 to identify the bridge
between input hot (R94) and output cold (R88) wire groups."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# Find ALL wires where either endpoint is near x=280, y=100-115
print("=== Wires near x=280, y=100-115 (CH1 area) ===")
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    
    # Check if any endpoint is in the target area
    in_area = False
    if 275 <= x1 <= 295 and 100 <= y1 <= 115:
        in_area = True
    if 275 <= x2 <= 295 and 100 <= y2 <= 115:
        in_area = True
    
    if in_area:
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")

# Also find wires near x=250 (J9 output XLR area)  
print("\n=== Wires near x=250, y=100-125 (J9 area) ===")
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    
    if (245 <= x1 <= 260 and 100 <= y1 <= 125) or (245 <= x2 <= 260 and 100 <= y2 <= 125):
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")

# And near x=190 (R58 area)
print("\n=== Wires near x=190, y=85-100 (R58 area) ===")
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    
    if (185 <= x1 <= 195 and 85 <= y1 <= 100) or (185 <= x2 <= 195 and 85 <= y2 <= 100):
        print(f"  ({x1}, {y1}) → ({x2}, {y2})")

# Let me also trace ALL wires that touch the HOT_RAW/OUT_COLD chain
# Build union-find to find ALL connected wire groups at y≈105 area
print("\n\n=== Comprehensive wire chain trace for CH1 ===")
# Parse ALL wires
wires = []
for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
    wires.append(((float(m.group(1)), float(m.group(2))),
                  (float(m.group(3)), float(m.group(4)))))

class UF:
    def __init__(self):
        self.p = {}
    def find(self, x):
        x = (round(x[0],3), round(x[1],3))
        if x not in self.p: self.p[x] = x
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a = (round(a[0],3), round(a[1],3))
        b = (round(b[0],3), round(b[1],3))
        ra, rb = self.find(a), self.find(b)
        if ra != rb: self.p[ra] = rb

uf = UF()
for (x1,y1),(x2,y2) in wires:
    uf.union((x1,y1),(x2,y2))

# Find the group containing (42, 110) [J3.pin2 area] 
target = (42.0, 110.0)
root = uf.find(target)

# Find ALL points in this group
group_pts = set()
for pt in uf.p:
    if uf.find(pt) == root:
        group_pts.add(pt)

print(f"Wire group containing (42, 110): {len(group_pts)} points")
if len(group_pts) < 30:
    for pt in sorted(group_pts):
        print(f"  {pt}")
else:
    print("  Too many points, showing x-range groups:")
    by_x = {}
    for x, y in sorted(group_pts):
        bucket = round(x / 10) * 10
        by_x.setdefault(bucket, []).append((x, y))
    for bx in sorted(by_x):
        pts = by_x[bx]
        print(f"  x≈{bx}: {len(pts)} points, y range [{min(y for _,y in pts):.2f}, {max(y for _,y in pts):.2f}]")

# Also find the group containing (280, 104) [OUT_COLD / R88 area]
target2 = (280.0, 104.0)
root2 = uf.find(target2) 
same = root == root2
print(f"\nGroup containing (280, 104): root={root2}")
print(f"Same group as (42, 110)? {same}")

# And group containing (290, 105) [HOT_RAW / R94 area]
target3 = (290.0, 105.0)
root3 = uf.find(target3)
same3 = root == root3
print(f"Group containing (290, 105): root={root3}")
print(f"Same group as (42, 110)? {same3}")

# Check if (280, 105) and (280, 105.19) are the same group
p1 = uf.find((280.0, 105.0))
p2 = uf.find((280.0, 105.19))
print(f"\n(280, 105.0) and (280, 105.19) same group? {p1 == p2}")

# Check for tiny wires between them
for (x1,y1),(x2,y2) in wires:
    if abs(x1 - 280) < 0.01 and abs(x2 - 280) < 0.01:
        if min(y1,y2) <= 105.19 and max(y1,y2) >= 105.0:
            print(f"  Potential bridge wire: ({x1},{y1}) → ({x2},{y2})")
