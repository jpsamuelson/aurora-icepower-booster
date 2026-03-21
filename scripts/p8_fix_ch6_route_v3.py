#!/usr/bin/env python3
"""
Fix CH6_GAIN_OUT route v3: via at (121,177) east of BUF_DRIVE diagonal.
Route:
  B.Cu: (93.48,193) → (121,193) → (121,177) → Via(121,177)
  F.Cu: (121,177) → (112,177) → (112,178.8) [R69 pad]

BUF_DRIVE on B.Cu goes from (108.84,177.69)→(120.79,189.64).
At x=121, we're east of BUF_DRIVE's entire diagonal.
On F.Cu at y=177, x=112-121: well above congested output section (y≈178.8-181).
"""
import re
import uuid as uuid_mod

PCB = 'aurora-dsp-icepower-booster.kicad_pcb'
NET_ID = 112

with open(PCB) as f:
    text = f.read()

# Remove ALL manual route segments for net 112 that contain coordinates
# from the previous attempts. Search by net and identify manual segments
# by their unique coordinates (not from Freerouting).
manual_coords = [
    (93.48, 193), (111, 193), (111, 181), (113, 179), (112, 178.8),
    (123, 193), (123, 179),  # v1 coords
]

removed = 0
# Remove segments matching manual route coordinates on net 112
for m in list(re.finditer(
    rf'\(segment\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)\s+'
    rf'\(width\s+[\d.]+\)\s+\(layer\s+"[^"]+"\)\s+\(net\s+{NET_ID}\)\s*'
    rf'\(uuid\s+"[^"]+"\)\)',
    text
)):
    x1, y1 = float(m.group(1)), float(m.group(2))
    x2, y2 = float(m.group(3)), float(m.group(4))
    # Check if both endpoints are manual route coords
    is_manual = False
    for cx, cy in manual_coords:
        if (abs(x1-cx)<0.1 and abs(y1-cy)<0.1) or (abs(x2-cx)<0.1 and abs(y2-cy)<0.1):
            is_manual = True
            break
    if is_manual:
        # Verify this isn't a Freerouting segment (check for typical Freerouting precision)
        # Manual segments have round numbers; Freerouting has 4-decimal precision
        if any(abs(v-round(v))<0.01 for v in [x1,y1,x2,y2]):
            pass  # Could be manual

# Simpler: just remove specific known segments
segs_to_remove = [
    # v2 route
    ('93.48', '193', '111', '193', 'B.Cu'),
    ('111', '193', '111', '181', 'B.Cu'),
    ('111', '181', '113', '179', 'B.Cu'),
    ('113', '179', '112', '178.8', 'F.Cu'),
]

for x1, y1, x2, y2, layer in segs_to_remove:
    pat = (
        rf'\(segment\s+\(start\s+{re.escape(x1)}\s+{re.escape(y1)}\)\s+'
        rf'\(end\s+{re.escape(x2)}\s+{re.escape(y2)}\)\s+'
        rf'\(width\s+[\d.]+\)\s+\(layer\s+"{re.escape(layer)}"\)\s+'
        rf'\(net\s+{NET_ID}\)\s*\(uuid\s+"[^"]+"\)\)'
    )
    m = re.search(pat, text)
    if m:
        text = text[:m.start()] + text[m.end():]
        removed += 1
        print(f'  Removed ({x1},{y1})->({x2},{y2}) {layer}')

# Remove via at (113,179) or (111,181)
for vx, vy in [('113', '179'), ('111', '181')]:
    pat = rf'\(via\s+\(at\s+{re.escape(vx)}\s+{re.escape(vy)}\)\s+\(size\s+[\d.]+\)\s+\(drill\s+[\d.]+\)\s+\(layers\s+"[^"]+"\s+"[^"]+"\)\s+\(net\s+{NET_ID}\)\s*\(uuid\s+"[^"]+"\)\)'
    m = re.search(pat, text)
    if m:
        text = text[:m.start()] + text[m.end():]
        removed += 1
        print(f'  Removed via at ({vx},{vy})')

# Also check for the south segment that connects to (93.48, 193) - should already be from Freerouting
print(f'\nRemoved {removed} old elements')

# Verify the south segment still exists
south_seg = re.search(
    rf'\(segment\s+\(start\s+93\.4766\s+185\.4828\)\s+\(end\s+93\.48\s+193\)',
    text
)
if south_seg:
    print('South segment (93.4766,185.4828)->(93.48,193) exists ✓')
elif re.search(rf'93\.48.*193.*B\.Cu.*{NET_ID}', text):
    print('South segment variant found ✓')
else:
    # Check what connects to y≈193
    for m in re.finditer(rf'\(segment.*?net\s+{NET_ID}\)', text):
        seg = m.group(0)
        if '193' in seg:
            print(f'  Found: {seg[:100]}...')

def make_segment(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {width}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def make_via(x, y, size, drill, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(via (at {x} {y}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

new = ''
new += make_segment('93.48', '193', '121', '193', '0.5', 'B.Cu', NET_ID)    # east past BUF_DRIVE
new += make_segment('121', '193', '121', '177', '0.5', 'B.Cu', NET_ID)      # north
new += make_via('121', '177', '0.6', '0.3', NET_ID)                          # via
new += make_segment('121', '177', '112', '177', '0.5', 'F.Cu', NET_ID)      # west on F.Cu
new += make_segment('112', '177', '112', '178.8', '0.5', 'F.Cu', NET_ID)    # south to R69

print(f'\nNew route (5 elements):')
for line in new.strip().split('\n'):
    print(f'  {line.strip()[:100]}')

insert_pos = text.rfind('\t(segment ')
end_of_line = text.find('\n', insert_pos)
text = text[:end_of_line+1] + new + text[end_of_line+1:]

depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in text)
assert depth == 0, f'Bracket imbalance: {depth}'

with open(PCB, 'w') as f:
    f.write(text)
print(f'\n✅ Route v3 applied, {len(text):,} bytes')
