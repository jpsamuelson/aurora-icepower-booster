#!/usr/bin/env python3
"""
Investigate and fix SS_U14 label_dangling.
Label is at (132.38, 30), wire endpoint at (132.38, 30) — should match.
Check if there's a coordinate precision issue.
"""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, 'r') as f:
    content = f.read()

# Find the SS_U14 label
label_match = re.search(r'\(label "SS_U14" \(at ([\d.]+) ([\d.]+)', content)
if label_match:
    lx, ly = label_match.group(1), label_match.group(2)
    print(f"Label SS_U14 at ({lx}, {ly})")
else:
    print("Label not found!")

# Find wire ending at (132.38, 30)
wires = re.findall(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', content)
matching = []
for x1, y1, x2, y2 in wires:
    for px, py in [(x1, y1), (x2, y2)]:
        if abs(float(px) - 132.38) < 0.01 and abs(float(py) - 30) < 0.01:
            matching.append(f"({x1},{y1})→({x2},{y2}) endpoint ({px},{py})")
            
print(f"\nWires with endpoint at (132.38, 30):")
for w in matching:
    print(f"  {w}")

# Check exact text around the label
idx = content.find('"SS_U14"')
context = content[idx-100:idx+200]
print(f"\nLabel context:")
print(repr(context))

# Check if the label has `(justify left bottom)` — this might matter for connection
# Labels connect at THEIR POSITION regardless of justify
print("\nChecking: is there any element right at (132.38, 30)?")
# Also check for pins at that position
for m in re.finditer(r'\(at 132\.38 30[ )]', content):
    ctx = content[max(0,m.start()-50):m.start()+50]
    print(f"  Found at offset {m.start()}: ...{ctx[:80]}...")
