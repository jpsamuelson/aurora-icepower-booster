#!/usr/bin/env python3
"""Add CH6_GAIN_OUT manual B.Cu route + via + F.Cu stub."""
import re, uuid as uuid_mod

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
NET = int(net_m.group(1))

def gen_seg(s, e, w, layer, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(segment (start {s[0]} {s[1]}) (end {e[0]} {e[1]}) (width {w}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def gen_via(p, size, drill, net):
    uid = str(uuid_mod.uuid4())
    return f'\t(via (at {p[0]} {p[1]}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

# Route: B.Cu detour south around V-/BUF_DRIVE at x=123
start = (93.4766, 185.4828)
wp1 = (93.48, 193)
wp2 = (123, 193)
wp3 = (123, 179)
via_pt = (123, 179)
end_pt = (112, 178.8)

routing = gen_seg(start, wp1, 0.5, 'B.Cu', NET)
routing += gen_seg(wp1, wp2, 0.5, 'B.Cu', NET)
routing += gen_seg(wp2, wp3, 0.5, 'B.Cu', NET)
routing += gen_via(via_pt, 0.6, 0.3, NET)
routing += gen_seg(via_pt, end_pt, 0.5, 'F.Cu', NET)

# Find last routing element and insert after it
last_pos = 0
for m in re.finditer(r'\t\((?:segment|via)\s', text):
    ms = m.start()
    d = 0
    i = ms
    while i < len(text):
        if text[i] == '(': d += 1
        elif text[i] == ')':
            d -= 1
            if d == 0:
                last_pos = i + 1
                break
        i += 1

ip = last_pos
while ip < len(text) and text[ip] in ' \t\n':
    ip += 1

text = text[:ip] + '\n' + routing + text[ip:]

d = sum(1 if c == '(' else -1 if c == ')' else 0 for c in text)
assert d == 0, f"Imbalance: {d}"

with open(PCB, 'w') as f:
    f.write(text)
print(f"Manual route added. {len(text):,} bytes")
