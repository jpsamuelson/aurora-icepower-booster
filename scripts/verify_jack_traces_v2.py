#!/usr/bin/env python3
"""Verify J2/J15 pad positions with rotation support, check trace connectivity."""
import re
import math

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    text = f.read()

# Local pad positions (from footprint, rotation=0)
LOCAL_PADS = {
    "1": (4.15, -3.75),   # Tip
    "2": (-4.15, 3.75),   # Ring1
    "3": (-1.15, 3.75),   # Ring1 Normal
    "4": (2.75, 3.75),    # Sleeve (GND)
    "5": (-4.15, -3.75),  # Tip Normal
}

def rotate_point(dx, dy, angle_deg):
    """Rotate (dx,dy) by angle_deg CCW. KiCad uses CW positive."""
    rad = math.radians(-angle_deg)  # KiCad: positive = CW
    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)
    return rx, ry

# Find J2 and J15 footprints with rotation
jacks = {}
for m in re.finditer(r'\(footprint\s+"aurora-dsp-icepower-booster:AUDIO-SMD[^"]*"[^)]*\n\s*\(layer[^)]*\)\n\s*\(uuid[^)]*\)\n\s*\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', text):
    fx = float(m.group(1))
    fy = float(m.group(2))
    rot = float(m.group(3)) if m.group(3) else 0.0
    block = text[m.start():m.start()+500]
    for ref in ["J2", "J15"]:
        if f'"Reference" "{ref}"' in block:
            jacks[ref] = (fx, fy, rot)

print("=== Footprint Positions ===")
for ref in sorted(jacks.keys()):
    fx, fy, rot = jacks[ref]
    print(f"{ref} at ({fx}, {fy}), rotation={rot}°")
    print(f"  Absolute pad positions (with rotation):")
    for pname in sorted(LOCAL_PADS.keys()):
        dx, dy = LOCAL_PADS[pname]
        rdx, rdy = rotate_point(dx, dy, rot)
        ax = round(fx + rdx, 4)
        ay = round(fy + rdy, 4)
        print(f"    Pad {pname}: ({ax:.4f}, {ay:.4f})")

# Collect all absolute pad positions
pad_positions = {}
for ref in jacks:
    fx, fy, rot = jacks[ref]
    for pname in LOCAL_PADS:
        dx, dy = LOCAL_PADS[pname]
        rdx, rdy = rotate_point(dx, dy, rot)
        key = f"{ref}.{pname}"
        pad_positions[key] = (round(fx + rdx, 4), round(fy + rdy, 4))

# Collect all REMOTE_IN trace endpoints (net 130)
print("\n=== REMOTE_IN Trace Network (net 130) ===")
trace_endpoints = set()
traces = []
for m in re.finditer(r'\(segment\s*\n\s*\(start\s+([\d.-]+)\s+([\d.-]+)\)\s*\n\s*\(end\s+([\d.-]+)\s+([\d.-]+)\)\s*\n\s*\(width\s+[\d.]+\)\s*\n\s*\(layer\s+"([^"]+)"\)\s*\n\s*\(net\s+130\)', text):
    sx, sy = float(m.group(1)), float(m.group(2))
    ex, ey = float(m.group(3)), float(m.group(4))
    layer = m.group(5)
    traces.append(((sx, sy), (ex, ey), layer))
    trace_endpoints.add((round(sx, 4), round(sy, 4)))
    trace_endpoints.add((round(ex, 4), round(ey, 4)))
    print(f"  ({sx:.4f}, {sy:.4f}) -> ({ex:.4f}, {ey:.4f}) [{layer}]")

# Check connectivity: Do J2.Pad1 and J15.Pad1 touch any trace endpoint?
print("\n=== Connectivity Check ===")
TOLERANCE = 0.05  # 50µm tolerance

for key in ["J2.1", "J15.1"]:  # Pad 1 = Tip = REMOTE_IN
    px, py = pad_positions[key]
    connected = False
    for tx, ty in trace_endpoints:
        if abs(px - tx) < TOLERANCE and abs(py - ty) < TOLERANCE:
            connected = True
            break
    status = "CONNECTED" if connected else "DISCONNECTED"
    print(f"  {key} ({px:.4f}, {py:.4f}): {status}")

for key in ["J2.4", "J15.4"]:  # Pad 4 = Sleeve = GND
    px, py = pad_positions[key]
    print(f"  {key} ({px:.4f}, {py:.4f}): GND via zone fill (no trace needed)")

# Check old trace endpoints that are now dangling
print("\n=== Old Trace Endpoints (potentially dangling) ===")
old_j2_pad1 = (34.62, 1.33)   # Old J2 Pad1 position (no rotation)
old_j15_pad1 = (23.15, 1.33)  # Old J15 Pad1 position (no rotation)
new_j2_pad1 = pad_positions["J2.1"]
new_j15_pad1 = pad_positions["J15.1"]

print(f"  Old J2 Pad1:  ({old_j2_pad1[0]}, {old_j2_pad1[1]})")
print(f"  New J2 Pad1:  ({new_j2_pad1[0]:.4f}, {new_j2_pad1[1]:.4f})")
print(f"  Old J15 Pad1: ({old_j15_pad1[0]}, {old_j15_pad1[1]})")
print(f"  New J15 Pad1: ({new_j15_pad1[0]:.4f}, {new_j15_pad1[1]:.4f})")

# Check if old endpoints are still in trace network
for name, pos in [("Old J2 Pad1", old_j2_pad1), ("Old J15 Pad1", old_j15_pad1)]:
    found = any(abs(pos[0]-tx) < TOLERANCE and abs(pos[1]-ty) < TOLERANCE for tx, ty in trace_endpoints)
    if found:
        print(f"  {name} still has trace at ({pos[0]}, {pos[1]}) -> DANGLING (pad moved away)")

# Summary
print("\n=== SUMMARY ===")
j2_connected = any(abs(pad_positions["J2.1"][0]-tx) < TOLERANCE and abs(pad_positions["J2.1"][1]-ty) < TOLERANCE for tx, ty in trace_endpoints)
j15_connected = any(abs(pad_positions["J15.1"][0]-tx) < TOLERANCE and abs(pad_positions["J15.1"][1]-ty) < TOLERANCE for tx, ty in trace_endpoints)

if j2_connected and j15_connected:
    print("  All REMOTE_IN connections OK!")
else:
    if not j2_connected:
        print(f"  PROBLEM: J2 Pad1 at {pad_positions['J2.1']} has NO trace connection")
    if not j15_connected:
        print(f"  PROBLEM: J15 Pad1 at {pad_positions['J15.1']} has NO trace connection")
    print("  -> Traces need to be re-routed to new pad positions!")
