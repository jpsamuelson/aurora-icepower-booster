#!/usr/bin/env python3
"""
Manually route CH6_GAIN_OUT to R69 via B.Cu detour.
Route south around V- and BUF_DRIVE obstacles on B.Cu.

Path:
  F.Cu track end at (103.525, 183.855)
  → Via to B.Cu at (103.525, 183.855) — RISK: near V- on B.Cu at (103.4, 184.1)
  
Instead, use the via+B.Cu that Freerouting already placed to go west,
then extend from the westernmost B.Cu point south, then east to R69.

Actually, let's first check existing vias on this net and use the
safest via point to branch from.
"""
import re, uuid

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

net_m = re.search(r'\(net\s+(\d+)\s+"/CH6_GAIN_OUT"\)', text)
NET = int(net_m.group(1))
print(f"CH6_GAIN_OUT = net {NET}")

# Find ALL vias (any format) for this net
print("\nSearching for vias with various formats...")
# Try different formats
patterns = [
    r'\(via\s+\(at\s+([\d.-]+)\s+([\d.-]+)\).*?\(net\s+' + str(NET) + r'\)',
    r'\(via\s.*?at\s+([\d.-]+)\s+([\d.-]+).*?net\s+' + str(NET) + r'\b',
]
for pat in patterns:
    for m in re.finditer(pat, text, re.DOTALL):
        x, y = float(m.group(1)), float(m.group(2))
        print(f"  Via at ({x}, {y})")

# Also find B.Cu-F.Cu transitions (segment endpoints that match across layers)
fcu_endpoints = set()
bcu_endpoints = set()
for m in re.finditer(r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+[\d.-]+\)\s+\(layer\s+"([^"]+)"\)[^)]*\(net\s+' + str(NET) + r'\)', text):
    layer = m.group(5)
    s = (round(float(m.group(1)), 4), round(float(m.group(2)), 4))
    e = (round(float(m.group(3)), 4), round(float(m.group(4)), 4))
    if layer == 'F.Cu':
        fcu_endpoints.add(s)
        fcu_endpoints.add(e)
    elif layer == 'B.Cu':
        bcu_endpoints.add(s)
        bcu_endpoints.add(e)

transitions = fcu_endpoints & bcu_endpoints
print(f"\nF.Cu/B.Cu transition points (implicit via locations):")
for t in sorted(transitions):
    print(f"  ({t[0]}, {t[1]})")

# Safe B.Cu detour route:
# Use transition point closest to the gap as starting point
# Route south to y=192 (well below all obstacles), east to x=113, north to R69

VIA_SIZE = 0.6
VIA_DRILL = 0.3
TRACE_W = 0.5

# Find a safe starting point on B.Cu
# The existing B.Cu segments are west of x=94. 
# Transition points should show where the existing vias are.
# From there, we add B.Cu segments going south then east then north.
# Finally via up to F.Cu near R69.

def gen_seg(start, end, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) (width {width}) (layer "{layer}") (net {net}) (uuid "{uid}"))\n'

def gen_via(pos, size, drill, net):
    uid = str(uuid.uuid4())
    return f'\t(via (at {pos[0]} {pos[1]}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid}"))\n'

print(f"\nPlanning route...")
# Start from transition point at approximately (93.93, 185.03) or (68.0, 185.48)
# Going south from the easternmost B.Cu endpoint
# Easternmost B.Cu endpoint: (93.48, 185.48) — but is this a transition? Check above.

# The most reliable approach: add a via at a safe F.Cu location, then B.Cu detour
# Safe F.Cu location: along the GAIN_OUT track, west of V- area
# Try (97, 183.855) on the existing F.Cu segment

# Check B.Cu for obstacles at (97, 183.855):
# V- on B.Cu: (66.4, 184.1) → (103.4, 184.1) at y=184.1
# At x=97, V- center at y=184.1, edges at 183.7-184.5
# Our point at (97, 183.855): distance from V- center = 0.245mm. Too close!

# Try (90, 183.855) — further west along F.Cu GAIN_OUT 
# Wait, the F.Cu GAIN_OUT track doesn't extend that far west... 
# The F.Cu segments: ...(71.475, 182.585) →... (96.937, 183.22) → (97.572, 183.855) → (103.525, 183.855)
# And → (96.937, 183.984) → (95.889, 185.032) → (93.928, 185.032) [via?] → B.Cu

# Actually let me just use the existing transition point and extend B.Cu from there.
# The detour:
# 1. From existing B.Cu at ~(93.48, 185.48), go south to (93.48, 192)
# 2. East to (113, 192) 
# 3. North to (113, 179)
# 4. Via up to F.Cu
# 5. F.Cu stub to R69 pad at (112, 178.8)

# But I need to verify (93.48, 185.48) is actually on B.Cu and connected.
# From the segments: (93.4766, 185.4828) → (68.0278, 185.4828) on B.Cu
# So (93.4766, 185.4828) IS an endpoint on B.Cu GAIN_OUT. 

# B.Cu obstacles along the detour path:
# At y=192: should be clear (board edge is at y=199.5)
# At x=113, y=179: check...

# Build the route
start_bcu = (93.4766, 185.4828)  # existing B.Cu endpoint
waypoint1 = (93.48, 192)          # south
waypoint2 = (113, 192)            # east
waypoint3 = (113, 179)            # north
via_point = (113, 179)            # via to F.Cu
end_fcu = (112, 178.8)            # R69 pad 2

routing = ''
# B.Cu segments for detour
routing += gen_seg(start_bcu, waypoint1, TRACE_W, 'B.Cu', NET)
routing += gen_seg(waypoint1, waypoint2, TRACE_W, 'B.Cu', NET)
routing += gen_seg(waypoint2, waypoint3, TRACE_W, 'B.Cu', NET)
# Via at the north end 
routing += gen_via(via_point, VIA_SIZE, VIA_DRILL, NET)
# Short F.Cu stub to R69 pad
routing += gen_seg(via_point, end_fcu, TRACE_W, 'F.Cu', NET)

print(f"Route: B.Cu ({start_bcu}) → ({waypoint1}) → ({waypoint2}) → ({waypoint3}) → Via → F.Cu → ({end_fcu})")

# Insert before zones
# Find last segment/via and insert after
last_pos = 0
for m in re.finditer(r'\t\((?:segment|via)\s', text):
    end = m.start()
    depth = 0
    i = end
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                last_pos = i + 1
                break
        i += 1

# Skip whitespace after last routing element
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
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(text)
print(f"Written {len(text)} bytes")
print("\n⚠️  Need zone refill after adding B.Cu traces!")
