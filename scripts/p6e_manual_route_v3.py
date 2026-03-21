#!/usr/bin/env python3
"""
Remove manual route v2 for CH6_GAIN_OUT and add corrected wide detour.
Goes further east (x=123) to avoid BUF_DRIVE trace on B.Cu.
"""
import re, uuid

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
NET = int(net_m.group(1))

# Remove the v2 manual route elements (via at 113,179 and segments)
# Remove via at (113, 179)
text = re.sub(r'\t\(via\s+\(at\s+113\s+179\).*?\(net\s+' + str(NET) + r'\).*?\)\n', '', text, flags=re.DOTALL)

# Remove segments with these coordinates
for coords_pair in [
    ('93.4766', '185.4828', '93.48', '192'),
    ('93.48', '192', '113', '192'),
    ('113', '192', '113', '179'),
    ('113', '179', '112', '178.8'),
]:
    pat = re.compile(
        r'\t\(segment\s+\(start\s+' + re.escape(coords_pair[0]) + r'\s+' + re.escape(coords_pair[1]) +
        r'\)\s+\(end\s+' + re.escape(coords_pair[2]) + r'\s+' + re.escape(coords_pair[3]) +
        r'\).*?\(net\s+' + str(NET) + r'\).*?\)\n', re.DOTALL
    )
    text = pat.sub('', text)

# Now add the corrected route:
# Path: (93.4766, 185.4828) → south → east → north → via → F.Cu stub to R69
# Go to x=123 to fully clear BUF_DRIVE (at x=120.8 max)

VIA_SIZE = 0.6
VIA_DRILL = 0.3
TRACE_W = 0.5

def gen_seg(start, end, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) (width {width}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def gen_via(pos, size, drill, net):
    uid = str(uuid.uuid4())
    return f'\t(via (at {pos[0]} {pos[1]}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

# B.Cu detour waypoints
start = (93.4766, 185.4828)  # existing B.Cu endpoint
wp1 = (93.48, 193)            # south (below all obstacles)
wp2 = (123, 193)              # east (past BUF_DRIVE at x=120.8)  
wp3 = (123, 179)              # north (to R69 latitude)
via_pt = (123, 179)           # via to F.Cu
end_pt = (112, 178.8)         # R69 pad 2

routing = ''
routing += gen_seg(start, wp1, TRACE_W, 'B.Cu', NET)
routing += gen_seg(wp1, wp2, TRACE_W, 'B.Cu', NET)
routing += gen_seg(wp2, wp3, TRACE_W, 'B.Cu', NET)
routing += gen_via(via_pt, VIA_SIZE, VIA_DRILL, NET)
routing += gen_seg(via_pt, end_pt, TRACE_W, 'F.Cu', NET)

# Insert before zones
last_pos = 0
for m in re.finditer(r'\t\((?:segment|via)\s', text):
    match_start = m.start()
    depth = 0
    i = match_start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                last_pos = i + 1
                break
        i += 1

insert_pos = last_pos
while insert_pos < len(text) and text[insert_pos] in ' \t\n':
    insert_pos += 1

text = text[:insert_pos] + '\n' + routing + text[insert_pos:]

# Verify brackets
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"

print(f"Route: B.Cu {start}→{wp1}→{wp2}→{wp3} → Via → F.Cu→{end_pt}")
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(text)
print(f"Written {len(text)} bytes")
