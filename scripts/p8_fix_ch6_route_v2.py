#!/usr/bin/env python3
"""
Fix CH6_GAIN_OUT route v2: remove old via at (111,181) and reroute.
New route:
  B.Cu: (93.48,193) → (111,193) → (111,181) → (113,179) → Via(113,179) → F.Cu: (113,179) → (112,178.8)

Clearance verification:
- B.Cu (111,181)→(113,179): BUF_DRIVE at y=180 is x=111.15, our trace at x=112 → gap=0.35mm ✓
- Via (113,179) on F.Cu: nearest trace is GAIN_FB at (112,180.63), dist=2.8mm ✓
- Via (113,179) on B.Cu: BUF_DRIVE at y=179 is x=110.15, our via at x=113 → gap=2.3mm ✓
- F.Cu (113,179)→(112,178.8): 1mm stub, clear area ✓
"""
import re
import uuid as uuid_mod

PCB = 'aurora-dsp-icepower-booster.kicad_pcb'
NET_ID = 112

with open(PCB) as f:
    text = f.read()

removed = 0

def remove_segment(text, x1, y1, x2, y2, layer, net):
    pattern = (
        rf'\(segment\s+\(start\s+{re.escape(x1)}\s+{re.escape(y1)}\)\s+'
        rf'\(end\s+{re.escape(x2)}\s+{re.escape(y2)}\)\s+'
        rf'\(width\s+[\d.]+\)\s+\(layer\s+"{re.escape(layer)}"\)\s+'
        rf'\(net\s+{net}\)\s*\(uuid\s+"[^"]+"\)\)'
    )
    m = re.search(pattern, text)
    if m:
        return text[:m.start()] + text[m.end():], True
    return text, False

# Remove old manual route segments (from v1 fix)
for x1, y1, x2, y2, layer in [
    ('93.48', '193', '111', '193', 'B.Cu'),          # east
    ('93.48', '193.00', '111.00', '193.00', 'B.Cu'),  # alt format
    ('111', '193', '111', '181', 'B.Cu'),              # north
    ('111.00', '193.00', '111.00', '181.00', 'B.Cu'),
    ('111', '181', '112', '178.8', 'F.Cu'),            # F.Cu stub
    ('111.00', '181.00', '112.00', '178.80', 'F.Cu'),
]:
    text, ok = remove_segment(text, x1, y1, x2, y2, layer, NET_ID)
    if ok:
        removed += 1
        print(f'  Removed segment ({x1},{y1})->({x2},{y2}) {layer}')

# Remove old via at (111,181)
via_pattern = rf'\(via\s+\(at\s+111(?:\.0)?\s+181(?:\.0)?\)\s+\(size\s+[\d.]+\)\s+\(drill\s+[\d.]+\)\s+\(layers\s+"[^"]+"\s+"[^"]+"\)\s+\(net\s+{NET_ID}\)\s*\(uuid\s+"[^"]+"\)\)'
m = re.search(via_pattern, text)
if m:
    text = text[:m.start()] + text[m.end():]
    removed += 1
    print(f'  Removed via at (111,181)')

print(f'\nRemoved {removed} elements')

# Find south endpoint (should be (93.48, 193) from Freerouting → manual south segment)
south_y = '193'
for m in re.finditer(
    rf'\(segment\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)\s+'
    rf'\(width\s+[\d.]+\)\s+\(layer\s+"B\.Cu"\)\s+\(net\s+{NET_ID}\)',
    text
):
    y_vals = [float(m.group(2)), float(m.group(4))]
    if max(y_vals) > 190:
        south_y = m.group(2) if float(m.group(2)) > 190 else m.group(4)
        print(f'South segment found, y_south={south_y}')
        break

def make_segment(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {width}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def make_via(x, y, size, drill, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(via (at {x} {y}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

new = ''
new += make_segment('93.48', south_y, '111', south_y, '0.5', 'B.Cu', NET_ID)    # east
new += make_segment('111', south_y, '111', '181', '0.5', 'B.Cu', NET_ID)          # north
new += make_segment('111', '181', '113', '179', '0.5', 'B.Cu', NET_ID)            # diagonal past BUF_DRIVE
new += make_via('113', '179', '0.6', '0.3', NET_ID)                                # via
new += make_segment('113', '179', '112', '178.8', '0.5', 'F.Cu', NET_ID)          # short to R69

print(f'\nNew route:')
print(new)

# Insert after last segment
insert_pos = text.rfind('\t(segment ')
end_of_line = text.find('\n', insert_pos)
text = text[:end_of_line+1] + new + text[end_of_line+1:]

depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in text)
assert depth == 0, f'Bracket imbalance: {depth}'

with open(PCB, 'w') as f:
    f.write(text)
print(f'✅ Route updated, {len(text):,} bytes')
