#!/usr/bin/env python3
"""Analyze and fix F4: Feedback R20-R25 connected to wrong op-amp input.
Currently: R20.pin1 → HOT_IN (non-inverting, NINV+)
Should be: R20.pin1 → INV_IN (inverting, INV-)

Strategy: Find the HOT_IN label on R20.pin1's wire and replace with INV_IN label.
Then verify for all 6 channels."""
import re, math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# First, find R20-R25 positions
def find_symbol_pos(ref):
    pat = rf'\(property "Reference" "{re.escape(ref)}"'
    for m in re.finditer(pat, text):
        pos = m.start()
        start = pos
        depth = 0
        while start > 0:
            start -= 1
            if text[start] == ')': depth += 1
            elif text[start] == '(':
                depth -= 1
                if depth < 0: break
        if start < text.find('(symbol (lib_id'):
            continue
        depth = 0
        for end in range(start, min(start+10000, len(text))):
            if text[end] == '(': depth += 1
            elif text[end] == ')': depth -= 1
            if depth == 0: break
        block = text[start:end+1]
        pos_m = re.search(r'\(at ([\d.]+) ([\d.]+)(?:\s+(\d+))?\)', block)
        if pos_m:
            return (float(pos_m.group(1)), float(pos_m.group(2)), int(pos_m.group(3)) if pos_m.group(3) else 0)
    return None

# Device:R pin offsets: pin1 at (0, 3.81), pin2 at (0, -3.81)
# Pin position = sym_pos + rotate(pin_offset) with Y-inverted

print("=== Feedback Resistors R20-R25 ===")
for i, ref in enumerate(['R20','R21','R22','R23','R24','R25']):
    pos = find_symbol_pos(ref)
    if pos:
        sx, sy, rot = pos
        # Compute pin positions
        # Pin 1: offset (0, 3.81) 
        # Pin 2: offset (0, -3.81)
        angle = math.radians(rot)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        
        p1_ox, p1_oy = 0, 3.81
        p1_rx = p1_ox * cos_a - p1_oy * sin_a
        p1_ry = p1_ox * sin_a + p1_oy * cos_a
        p1_x = round(sx + p1_rx, 2)
        p1_y = round(sy - p1_ry, 2)
        
        p2_ox, p2_oy = 0, -3.81
        p2_rx = p2_ox * cos_a - p2_oy * sin_a
        p2_ry = p2_ox * sin_a + p2_oy * cos_a
        p2_x = round(sx + p2_rx, 2)
        p2_y = round(sy - p2_ry, 2)
        
        print(f"  {ref} at ({sx}, {sy}) rot={rot}°")
        print(f"    Pin 1 → ({p1_x}, {p1_y}) [should be INV_IN, is HOT_IN]")
        print(f"    Pin 2 → ({p2_x}, {p2_y}) [RX_OUT - correct]")

# Now find HOT_IN labels near R20-R25 pin1 positions
# These are the labels we need to examine
print("\n=== HOT_IN labels (from verify output: R20.pin1 on HOT_IN) ===")
ch_info = {
    1: ('R20', 'CH1_HOT_IN', 'CH1_INV_IN'),
    2: ('R21', 'CH2_HOT_IN', 'CH2_INV_IN'),
    3: ('R22', 'CH3_HOT_IN', 'CH3_INV_IN'),
    4: ('R23', 'CH4_HOT_IN', 'CH4_INV_IN'),
    5: ('R24', 'CH5_HOT_IN', 'CH5_INV_IN'),
    6: ('R25', 'CH6_HOT_IN', 'CH6_INV_IN'),
}

# Find all HOT_IN and INV_IN label positions
print("\n=== All HOT_IN labels ===")
for m in re.finditer(r'\(label "(CH\d_HOT_IN)" \(at ([\d.]+) ([\d.]+)', text):
    print(f"  {m.group(1)} at ({m.group(2)}, {m.group(3)})")

print("\n=== All INV_IN labels ===")
for m in re.finditer(r'\(label "(CH\d_INV_IN)" \(at ([\d.]+) ([\d.]+)', text):
    print(f"  {m.group(1)} at ({m.group(2)}, {m.group(3)})")

# The fix: R20-R25 pin1 is on HOT_IN through a wire + label.
# Need to either:
# a) Move the wire from R20.pin1 to the INV_IN wire (physical rewire)
# b) Change the label on R20.pin1's wire from HOT_IN to INV_IN
# 
# Since R20.pin1 is at a specific position and there's a wire endpoint there
# with a HOT_IN label, option (b) is cleaner IF only R20.pin1 is on this label.
# 
# But HOT_IN has MORE nodes (C62.2, R2.2, R20.1, U2.3 for CH1).
# If we change the label, we'd disconnect C62.2, R2.2, and U2.3 from HOT_IN.
# That's wrong.
#
# So we need option (a): physically disconnect R20.pin1 from the HOT_IN wire
# and connect it to the INV_IN wire with a new label.
# 
# Alternative approach: R20.pin1 shares a wire that also has HOT_IN labels.
# We need to break R20.pin1 off that wire and give it an INV_IN label.

# Let's trace R20.pin1's wire group and find the HOT_IN label connection
print("\n=== Wire groups containing R20-R25 pin1 positions ===")

# Parse all wires
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

# For R20 at (80, 97.46) rot=0°:
# pin1 at (80, 97.46-3.81) = (80, 93.65)
# pin2 at (80, 97.46+3.81) = (80, 101.27)
# Wait, let me recalculate properly
for ref in ['R20']:
    pos = find_symbol_pos(ref)
    if pos:
        sx, sy, rot = pos
        p1_y = round(sy - 3.81, 2) if rot == 0 else sy  # Simplified for rot=0
        p1_x = sx
        
        pt = (round(p1_x, 3), round(p1_y, 3))
        root = uf.find(pt)
        
        group_pts = set()
        for p in uf.p:
            if uf.find(p) == root:
                group_pts.add(p)
        
        print(f"\n  {ref} pin1 at ({p1_x}, {p1_y}): wire group has {len(group_pts)} points")
        for gp in sorted(group_pts):
            print(f"    {gp}")
        
        # Find labels in this group
        for lm in re.finditer(r'\(label "([^"]+)" \(at ([\d.]+) ([\d.]+)', text):
            lname = lm.group(1)
            lx, ly = round(float(lm.group(2)),3), round(float(lm.group(3)),3)
            if uf.find((lx, ly)) == root:
                print(f"    Label: {lname} at ({lx}, {ly})")
