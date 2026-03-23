#!/usr/bin/env python3
"""
Reroute REMOTE_IN traces around J2 NPTH at (32.512, 10.239).

NPTH drill=1.5mm → radius=0.75mm → edge at Y=10.989
hole_clearance=0.25mm → exclusion at Y=11.239
trace_width=0.25mm → half=0.125mm → min trace center Y=11.364

Plan: Route at Y=11.5 (safe margin)

Current traces to REMOVE (the 4 we added last time):
  (36.262, 10.339) → (36.262, 10.4436)   J2 Pad1 vertical stub
  (36.262, 10.4436) → (31.7356, 10.4436)  horizontal to junction  
  (20.006, 10.246) → (20.006, 10.4436)    J15 Pad1 vertical stub
  (20.006, 10.4436) → (31.7356, 10.4436)  horizontal to junction

New traces:
  (36.262, 10.339) → (36.262, 11.5)       J2 Pad1 south
  (36.262, 11.5)   → (31.7356, 11.5)      horizontal to junction
  (20.006, 10.246) → (20.006, 11.5)        J15 Pad1 south
  (20.006, 11.5)   → (31.7356, 11.5)       horizontal to junction

Also update existing trace that connects to old junction:
  (31.7356, 10.4436) → (36.292, 15.0)  needs start changed to (31.7356, 11.5)
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"
NET_ID = 130  # /REMOTE_IN
NEW_Y = 11.5
OLD_JUNCTION_Y = 10.4436
JUNCTION_X = 31.7356

with open(PCB) as f:
    content = f.read()

def extract_block(text, start):
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(': depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0: return text[start:i+1], i+1
        i += 1
    return None, start

# Collect all REMOTE_IN segments with their positions
segments = []
for m in re.finditer(r'\(segment\b', content):
    block, end = extract_block(content, m.start())
    if block and f'(net {NET_ID})' in block:
        s = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', block)
        e = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', block)
        if s and e:
            sx, sy = float(s.group(1)), float(s.group(2))
            ex, ey = float(e.group(1)), float(e.group(2))
            segments.append({
                'sx': sx, 'sy': sy, 'ex': ex, 'ey': ey,
                'start': m.start(), 'end': end, 'block': block
            })

# Identify segments to remove (the 4 at old Y=10.4436)
to_remove = []
for seg in segments:
    # Match segments involving old junction Y
    if (abs(seg['sy'] - OLD_JUNCTION_Y) < 0.01 or abs(seg['ey'] - OLD_JUNCTION_Y) < 0.01):
        # These are our 4 traces
        if (abs(seg['sx'] - 36.262) < 0.01 or abs(seg['ex'] - 36.262) < 0.01 or
            abs(seg['sx'] - 20.006) < 0.01 or abs(seg['ex'] - 20.006) < 0.01 or
            abs(seg['sx'] - JUNCTION_X) < 0.01 or abs(seg['ex'] - JUNCTION_X) < 0.01):
            to_remove.append(seg)
            print(f"REMOVE: ({seg['sx']}, {seg['sy']}) → ({seg['ex']}, {seg['ey']})")

# Also find the segment from old junction to (36.292, 15.0)
junction_to_far = None
for seg in segments:
    if (abs(seg['sx'] - JUNCTION_X) < 0.01 and abs(seg['sy'] - OLD_JUNCTION_Y) < 0.01):
        if abs(seg['ex'] - 36.292) < 0.01 and abs(seg['ey'] - 15.0) < 0.01:
            junction_to_far = seg
            print(f"MODIFY: ({seg['sx']}, {seg['sy']}) → ({seg['ex']}, {seg['ey']}) — update start Y")

print(f"\nRemoving {len(to_remove)} segments, modifying 1")

# Remove old segments (reverse order)
new_content = content
for seg in sorted(to_remove, key=lambda s: s['start'], reverse=True):
    # Also remove trailing whitespace
    end = seg['end']
    while end < len(new_content) and new_content[end] in ' \t\n':
        end += 1
    new_content = new_content[:seg['start']] + new_content[end:]
    print(f"  Removed segment at offset {seg['start']}")

# Modify the junction→far segment: change start Y from 10.4436 to NEW_Y
if junction_to_far:
    old_start = f"(start {JUNCTION_X} {OLD_JUNCTION_Y})"
    new_start = f"(start {JUNCTION_X} {NEW_Y})"
    # Find this specific segment in modified content
    idx = new_content.find(old_start)
    if idx >= 0:
        # Check it's in a REMOTE_IN segment
        seg_start = new_content.rfind('(segment', max(0, idx-500), idx)
        seg_block, _ = extract_block(new_content, seg_start)
        if seg_block and f'(net {NET_ID})' in seg_block and '36.292' in seg_block:
            new_content = new_content[:idx] + new_start + new_content[idx+len(old_start):]
            print(f"  Modified junction segment start: {OLD_JUNCTION_Y} → {NEW_Y}")

# Insert new segments
NEW_SEGMENTS = [
    # J2 Pad1 south to new Y
    f"""(segment
		(start 36.262 10.339)
		(end 36.262 {NEW_Y})
		(width 0.25)
		(layer "F.Cu")
		(net {NET_ID})
		(uuid "a1b2c3d4-reroute-j2-south")
	)""",
    # J2 horizontal to junction
    f"""(segment
		(start 36.262 {NEW_Y})
		(end {JUNCTION_X} {NEW_Y})
		(width 0.25)
		(layer "F.Cu")
		(net {NET_ID})
		(uuid "a1b2c3d4-reroute-j2-horiz")
	)""",
    # J15 Pad1 south to new Y
    f"""(segment
		(start 20.006 10.246)
		(end 20.006 {NEW_Y})
		(width 0.25)
		(layer "F.Cu")
		(net {NET_ID})
		(uuid "a1b2c3d4-reroute-j15-south")
	)""",
    # J15 horizontal to junction
    f"""(segment
		(start 20.006 {NEW_Y})
		(end {JUNCTION_X} {NEW_Y})
		(width 0.25)
		(layer "F.Cu")
		(net {NET_ID})
		(uuid "a1b2c3d4-reroute-j15-horiz")
	)""",
]

# Find insertion point — after last segment
last_seg_end = 0
for m in re.finditer(r'\(segment\b', new_content):
    block, end = extract_block(new_content, m.start())
    if block:
        last_seg_end = end

if last_seg_end > 0:
    insert_text = "\n" + "\n".join(NEW_SEGMENTS)
    new_content = new_content[:last_seg_end] + insert_text + new_content[last_seg_end:]
    print(f"  Inserted 4 new segments at offset {last_seg_end}")

# Bracket check
depth = 0
for ch in new_content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"\nBracket balance: {depth}")

if depth != 0:
    print("ERROR: Bracket imbalance!")
    import sys; sys.exit(1)

with open(PCB, 'w') as f:
    f.write(new_content)
print("Written.")

# Verify
print("\n=== VERIFICATION ===")
with open(PCB) as f:
    verify = f.read()
for m in re.finditer(r'\(segment\b', verify):
    block, _ = extract_block(verify, m.start())
    if block and f'(net {NET_ID})' in block:
        s = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', block)
        e = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', block)
        if s and e:
            print(f"  ({s.group(1)}, {s.group(2)}) → ({e.group(1)}, {e.group(2)})")
