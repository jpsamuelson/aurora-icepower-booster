#!/usr/bin/env python3
"""Fix CH6 route v4: use x=122 to clear BUF_DRIVE endpoint at (120.79,189.64)."""
import re, uuid as uuid_mod

PCB = 'aurora-dsp-icepower-booster.kicad_pcb'
NET_ID = 112

with open(PCB) as f:
    text = f.read()

removed = 0
# Remove v3 segments
for x1, y1, x2, y2, layer in [
    ('93.48', '193', '121', '193', 'B.Cu'),
    ('121', '193', '121', '177', 'B.Cu'),
    ('121', '177', '112', '177', 'F.Cu'),
    ('112', '177', '112', '178.8', 'F.Cu'),
]:
    pat = (rf'\(segment\s+\(start\s+{re.escape(x1)}\s+{re.escape(y1)}\)\s+'
           rf'\(end\s+{re.escape(x2)}\s+{re.escape(y2)}\)\s+'
           rf'\(width\s+[\d.]+\)\s+\(layer\s+"{re.escape(layer)}"\)\s+'
           rf'\(net\s+{NET_ID}\)\s*\(uuid\s+"[^"]+"\)\)')
    m = re.search(pat, text)
    if m:
        text = text[:m.start()] + text[m.end():]
        removed += 1

# Remove via at (121,177)
pat = rf'\(via\s+\(at\s+121\s+177\)\s+\(size\s+[\d.]+\)\s+\(drill\s+[\d.]+\)\s+\(layers\s+"[^"]+"\s+"[^"]+"\)\s+\(net\s+{NET_ID}\)\s*\(uuid\s+"[^"]+"\)\)'
m = re.search(pat, text)
if m:
    text = text[:m.start()] + text[m.end():]
    removed += 1

print(f'Removed {removed} old elements')

def make_seg(x1, y1, x2, y2, w, layer, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def make_via(x, y, s, d, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(via (at {x} {y}) (size {s}) (drill {d}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

new = ''
new += make_seg('93.48', '193', '122', '193', '0.5', 'B.Cu', NET_ID)
new += make_seg('122', '193', '122', '177', '0.5', 'B.Cu', NET_ID)
new += make_via('122', '177', '0.6', '0.3', NET_ID)
new += make_seg('122', '177', '112', '177', '0.5', 'F.Cu', NET_ID)
new += make_seg('112', '177', '112', '178.8', '0.5', 'F.Cu', NET_ID)

insert_pos = text.rfind('\t(segment ')
end_of_line = text.find('\n', insert_pos)
text = text[:end_of_line+1] + new + text[end_of_line+1:]

depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in text)
assert depth == 0, f'Bracket imbalance: {depth}'

with open(PCB, 'w') as f:
    f.write(text)
print(f'✅ Route v4 (x=122), {len(text):,} bytes')
