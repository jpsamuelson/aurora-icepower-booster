#!/usr/bin/env python3
"""
Fix CH6_GAIN_OUT manual route.
Remove old route (via at 123,179 + segments) and add new route:
  B.Cu: (93.48,193) → (111,193) → (111,181) → Via(111,181) → F.Cu: (111,181) → (112,178.8)

Clearance checks:
- B.Cu x=111 north: BUF_DRIVE at y=181 is x=112.15, edge=111.9. Via edge=111.3. Gap=0.6mm ✓
- F.Cu (111,181)→(112,178.8): V+ at x=109.94, GAIN_FB at x=112 y=180.6. All clear ✓
"""
import re

PCB = 'aurora-dsp-icepower-booster.kicad_pcb'
NET_ID = 112  # CH6_GAIN_OUT

with open(PCB) as f:
    text = f.read()

# Remove old manual route segments and via
old_segments = [
    # Old B.Cu east segment
    ('93.48', '193', '123', '193', 'B.Cu'),
    ('93.48', '193.0', '123.0', '193.0', 'B.Cu'),
    ('93.48', '193', '123.0', '193.0', 'B.Cu'),
    ('93.4766', '193', '123', '193', 'B.Cu'),  # possible variants
    # Old B.Cu north segment
    ('123', '193', '123', '179', 'B.Cu'),
    ('123.0', '193.0', '123.0', '179.0', 'B.Cu'),
    # Old F.Cu stub
    ('123', '179', '112', '178.8', 'F.Cu'),
    ('123.0', '179.0', '112.0', '178.8', 'F.Cu'),
    ('123.0', '179.0', '112.0', '178.80', 'F.Cu'),
]

# More robust: find and remove segments with net 112 that match the manual route coords
removed_segs = 0
removed_vias = 0

# Find segments to remove by matching key coordinates
def remove_segment(text, x1, y1, x2, y2, layer, net):
    """Remove a segment matching approximate coordinates."""
    pattern = (
        rf'\(segment\s+\(start\s+{re.escape(x1)}\s+{re.escape(y1)}\)\s+'
        rf'\(end\s+{re.escape(x2)}\s+{re.escape(y2)}\)\s+'
        rf'\(width\s+[\d.]+\)\s+'
        rf'\(layer\s+"{re.escape(layer)}"\)\s+'
        rf'\(net\s+{net}\)\s*'
        rf'\(uuid\s+"[^"]+"\)\)'
    )
    m = re.search(pattern, text)
    if m:
        return text[:m.start()] + text[m.end():], True
    return text, False

# Remove the 3 old manual segments
for x1, y1, x2, y2, layer in [
    ('93.48', '193', '123', '193', 'B.Cu'),      # east
    ('123', '193', '123', '179', 'B.Cu'),          # north
    ('123', '179', '112', '178.8', 'F.Cu'),        # stub
]:
    text, ok = remove_segment(text, x1, y1, x2, y2, layer, NET_ID)
    if ok:
        removed_segs += 1
        print(f'  Removed segment ({x1},{y1})->({x2},{y2}) {layer}')

# Also try with .0 suffixes
if removed_segs < 3:
    for x1, y1, x2, y2, layer in [
        ('93.48', '193.0', '123.0', '193.0', 'B.Cu'),
        ('93.48', '193.00', '123.00', '193.00', 'B.Cu'),
        ('123.0', '193.0', '123.0', '179.0', 'B.Cu'),
        ('123.00', '193.00', '123.00', '179.00', 'B.Cu'),
        ('123.0', '179.0', '112.0', '178.8', 'F.Cu'),
        ('123.00', '179.00', '112.00', '178.80', 'F.Cu'),
    ]:
        text, ok = remove_segment(text, x1, y1, x2, y2, layer, NET_ID)
        if ok:
            removed_segs += 1
            print(f'  Removed segment ({x1},{y1})->({x2},{y2}) {layer}')

# Remove old via at (123,179) net=112
via_pattern = rf'\(via\s+\(at\s+123(?:\.0)?\s+179(?:\.0)?\)\s+\(size\s+[\d.]+\)\s+\(drill\s+[\d.]+\)\s+\(layers\s+"[^"]+"\s+"[^"]+"\)\s+\(net\s+{NET_ID}\)\s*\(uuid\s+"[^"]+"\)\)'
m = re.search(via_pattern, text)
if m:
    text = text[:m.start()] + text[m.end():]
    removed_vias += 1
    print(f'  Removed via at (123,179)')

print(f'\nRemoved: {removed_segs} segments, {removed_vias} vias')

# Now find the existing south segment to determine the exact coordinates
# It should be: (93.4766,185.4828)->(93.48,193) or similar
south_seg = re.search(
    rf'\(segment\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)\s+\(width\s+[\d.]+\)\s+\(layer\s+"B\.Cu"\)\s+\(net\s+{NET_ID}\)',
    text
)
# Find the segment that goes to y≈193
for m in re.finditer(
    rf'\(segment\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)\s+'
    rf'\(width\s+([\d.]+)\)\s+\(layer\s+"B\.Cu"\)\s+\(net\s+{NET_ID}\)',
    text
):
    y_vals = [float(m.group(2)), float(m.group(4))]
    if max(y_vals) > 190:
        south_x = m.group(1) if float(m.group(2)) > 190 else m.group(3)
        south_y = m.group(2) if float(m.group(2)) > 190 else m.group(4)
        print(f'\nFound south endpoint: ({south_x}, {south_y})')
        break

# Generate new route segments
import uuid as uuid_mod

def make_segment(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid_mod.uuid4())
    return (
        f'\t(segment (start {x1} {y1}) (end {x2} {y2}) '
        f'(width {width}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'
    )

def make_via(x, y, size, drill, net):
    uid = str(uuid_mod.uuid4())
    return (
        f'\t(via (at {x} {y}) (size {size}) (drill {drill}) '
        f'(layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'
    )

new_elements = ''
# B.Cu: south point → (111, 193)
new_elements += make_segment(south_x, south_y, '111', south_y, '0.5', 'B.Cu', NET_ID)
# B.Cu: (111, 193) → (111, 181)
new_elements += make_segment('111', south_y, '111', '181', '0.5', 'B.Cu', NET_ID)
# Via at (111, 181)
new_elements += make_via('111', '181', '0.6', '0.3', NET_ID)
# F.Cu: (111, 181) → (112, 178.8) — diagonal to R69
new_elements += make_segment('111', '181', '112', '178.8', '0.5', 'F.Cu', NET_ID)

print(f'\nNew elements:\n{new_elements}')

# Insert before the closing ) of the PCB file
# Find last segment/via to insert after
insert_pos = text.rfind('\t(segment ')
if insert_pos == -1:
    insert_pos = text.rfind('\t(via ')
# Find end of that line
end_of_line = text.find('\n', insert_pos)
text = text[:end_of_line+1] + new_elements + text[end_of_line+1:]

# Bracket balance
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in text)
assert depth == 0, f'Bracket imbalance: {depth}'

with open(PCB, 'w') as f:
    f.write(text)

print(f'\n✅ CH6_GAIN_OUT route updated')
print(f'   Size: {len(text):,} bytes')
