#!/usr/bin/env python3
"""
Smart GND via stitching using pcbnew API to check for conflicts.
Adds vias only where they won't short to non-GND copper.

Process:
1. Load board in pcbnew
2. Generate candidate grid positions
3. For each candidate, check clearance against all existing tracks/pads
4. Write valid vias to temp file
5. Text-merge into original PCB
"""
import sys, os, re, uuid
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

print("Loading board for via stitching analysis...")
board = pcbnew.LoadBoard(PCB)

# Find GND net
nets_by_name = board.GetNetsByName()
gnd_net = None
for name, net_info in nets_by_name.items():
    if name == 'GND':
        gnd_net = net_info
        break

if not gnd_net:
    # Try alternative approach
    netinfo = board.FindNet('GND')
    if netinfo:
        gnd_net = netinfo
    else:
        print("ERROR: GND net not found!")
        # List first 10 nets for debugging
        for i, (name, _) in enumerate(nets_by_name.items()):
            if i >= 10:
                break
            print(f"  Net: '{name}'")
        sys.exit(1)

GND_NETCODE = gnd_net.GetNetCode()
print(f"GND net code: {GND_NETCODE}")

# Collect all non-GND copper items with their bounding positions
# We need to know where non-GND copper exists so we don't place vias there
def nm(val):
    """Convert KiCad internal units (nm) to mm."""
    return val / 1e6

def mm_to_nm(val):
    """Convert mm to KiCad internal units (nm)."""
    return int(val * 1e6)

# Collect positions of all non-GND pads and track segments
non_gnd_positions = []  # list of (x_mm, y_mm, radius_mm)

for track in board.GetTracks():
    net = track.GetNetCode()
    if net == GND_NETCODE:
        continue
    if track.GetClass() == 'PCB_VIA':
        x, y = nm(track.GetX()), nm(track.GetY())
        r = nm(track.GetWidth()) / 2 + 0.3  # via radius + clearance
        non_gnd_positions.append((x, y, r))
    else:
        # Segment — check start and end
        sx, sy = nm(track.GetStart().x), nm(track.GetStart().y)
        ex, ey = nm(track.GetEnd().x), nm(track.GetEnd().y)
        w = nm(track.GetWidth()) / 2 + 0.3
        # Sample along the segment
        dx, dy = ex - sx, ey - sy
        length = (dx**2 + dy**2) ** 0.5
        if length < 0.01:
            non_gnd_positions.append((sx, sy, w))
            continue
        steps = max(1, int(length / 0.5))  # sample every 0.5mm
        for i in range(steps + 1):
            t = i / steps
            x = sx + dx * t
            y = sy + dy * t
            non_gnd_positions.append((x, y, w))

# Also collect non-GND pad positions
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetCode() != GND_NETCODE:
            x, y = nm(pad.GetPosition().x), nm(pad.GetPosition().y)
            # Use pad size + clearance
            sx = nm(pad.GetBoundingBox().GetWidth()) / 2 + 0.3
            sy = nm(pad.GetBoundingBox().GetHeight()) / 2 + 0.3
            r = max(sx, sy)
            non_gnd_positions.append((x, y, r))

print(f"Non-GND copper positions to avoid: {len(non_gnd_positions)}")

# Board dimensions
board_xmin, board_ymin = 0.5, 0.5
board_xmax, board_ymax = 145.054, 199.5

# Via parameters
VIA_SIZE = 0.6  # mm
VIA_DRILL = 0.3  # mm
VIA_RADIUS = VIA_SIZE / 2
GRID_SPACING = 10.0  # mm
EDGE_MARGIN = 2.0  # mm
MIN_CLEARANCE = 0.5  # mm from any non-GND copper

# Generate candidate grid
candidates = []
x = board_xmin + EDGE_MARGIN
while x < board_xmax - EDGE_MARGIN:
    y = board_ymin + EDGE_MARGIN
    while y < board_ymax - EDGE_MARGIN:
        candidates.append((round(x, 2), round(y, 2)))
        y += GRID_SPACING
    x += GRID_SPACING

print(f"Grid candidates: {len(candidates)}")

# Filter candidates — check against all non-GND copper
valid = []
for cx, cy in candidates:
    ok = True
    for px, py, pr in non_gnd_positions:
        dist = ((cx - px)**2 + (cy - py)**2) ** 0.5
        if dist < pr + VIA_RADIUS + MIN_CLEARANCE:
            ok = False
            break
    if ok:
        valid.append((cx, cy))

print(f"Valid via positions: {len(valid)}")

if not valid:
    print("No valid positions for via stitching!")
    sys.exit(0)

# Read original PCB and find GND net ID in text
with open(PCB) as f:
    content = f.read()

gnd_match = re.search(r'\(net (\d+) "GND"\)', content)
GND_NET_TEXT = int(gnd_match.group(1))

# Generate via blocks
via_blocks = []
for x, y in valid:
    uid = str(uuid.uuid4())
    via_text = (
        f'\t(via\n'
        f'\t\t(at {x} {y})\n'
        f'\t\t(size {VIA_SIZE})\n'
        f'\t\t(drill {VIA_DRILL})\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n'
        f'\t\t(net {GND_NET_TEXT})\n'
        f'\t\t(uuid "{uid}")\n'
        f'\t)'
    )
    via_blocks.append(via_text)

# Insert before zones
zone_pos = content.find('\t(zone\n')
if zone_pos == -1:
    zone_pos = content.find('\t(zone ')
if zone_pos == -1:
    print("ERROR: No zone found!")
    sys.exit(1)

via_text = '\n'.join(via_blocks) + '\n'
result = content[:zone_pos] + via_text + content[zone_pos:]

# Bracket balance
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in result)
if depth != 0:
    print(f"❌ Bracket balance: {depth}")
    sys.exit(1)
print("Bracket balance: OK")

with open(PCB, 'w') as f:
    f.write(result)

print(f"\n✅ Added {len(valid)} GND stitching vias (of {len(candidates)} candidates)")
print(f"   Rejected {len(candidates) - len(valid)} due to clearance conflicts")
print(f"   Size: {len(result):,} bytes")
