#!/usr/bin/env python3
"""
Manually route CH6_GAIN_OUT missing connection via B.Cu bypass.
The area between the track end and R69 pad 2 is too congested on F.Cu.
Route: F.Cu end → via → B.Cu → via → F.Cu to pad
"""
import re, uuid

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

# Find net number for CH6_GAIN_OUT
net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
net_num = int(net_m.group(1))
print(f"CH6_GAIN_OUT = net {net_num}")

# Track currently ends at (103.525, 183.855) on F.Cu
# R69 pad 2 at (112, 178.8) on F.Cu
# Route: via near track end → B.Cu diagonal → via near R69 pad → F.Cu stub to pad

# Via parameters (Audio_Output netclass)
VIA_SIZE = 0.6   # via pad diameter
VIA_DRILL = 0.3  # via drill diameter
TRACE_W = 0.5    # trace width (Audio_Output)

# Route points
track_end = (103.525, 183.855)
pad_pos = (112.0, 178.8)

# Via 1: offset slightly south of track end to avoid conflicts
via1 = (103.525, 183.855)  # at the track end itself

# Via 2: near R69 pad 2 but offset slightly to avoid direct pad collision
# Place via at the pad position - it will connect through copper
via2 = (112.0, 178.8)

# Generate segment and via text
def gen_seg(start, end, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) (width {width}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def gen_via(pos, size, drill, net):
    uid = str(uuid.uuid4())
    return f'\t(via (at {pos[0]} {pos[1]}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

routing = ''
# Via 1 at track end
routing += gen_via(via1, VIA_SIZE, VIA_DRILL, net_num)
# B.Cu trace from via1 to via2
routing += gen_seg(via1, via2, TRACE_W, 'B.Cu', net_num)
# Via 2 at R69 pad
routing += gen_via(via2, VIA_SIZE, VIA_DRILL, net_num)

print(f"Adding route:")
print(f"  Via at ({via1[0]}, {via1[1]})")
print(f"  B.Cu trace ({via1[0]},{via1[1]}) -> ({via2[0]},{via2[1]})")
print(f"  Via at ({via2[0]}, {via2[1]})")

# Insert before the first (zone or (gr_text at the end
# Find the last segment/via block and insert after it
# Look for the last (via ...) or (segment ...) line
last_routing_pos = 0
for m in re.finditer(r'\t\((?:segment|via)\s', text):
    last_routing_pos = m.start()

# Find end of this block
depth = 0
i = last_routing_pos
while i < len(text):
    if text[i] == '(':
        depth += 1
    elif text[i] == ')':
        depth -= 1
        if depth == 0:
            insert_pos = i + 1
            # Skip whitespace/newline
            while insert_pos < len(text) and text[insert_pos] in ' \t\n':
                insert_pos += 1
            break
    i += 1

text = text[:insert_pos] + '\n' + routing + text[insert_pos:]

# Verify brackets
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(text)
print(f"Written {len(text)} bytes")
print("\n⚠️  Zone fill needed after adding B.Cu trace!")
