#!/usr/bin/env python3
"""Add courtyard to KH-PJ-320EA-5P-SMT footprint.
Analyze pad/silk extents and create F.CrtYd rectangle with 0.25mm margin."""
import re

MOD_FILE = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/footprints.pretty/AUDIO-SMD_KH-PJ-320EA-5P-SMT.kicad_mod"

with open(MOD_FILE) as f:
    content = f.read()

# Find all coordinates: pads, fp_lines
min_x = float('inf')
max_x = float('-inf')
min_y = float('inf')
max_y = float('-inf')

# Pads - local coordinates with size
for m in re.finditer(r'\(pad\b', content):
    # Extract block
    depth = 0
    i = m.start()
    start = i
    while i < len(content):
        if content[i] == '(': depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                block = content[start:i+1]
                break
        i += 1
    
    at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)', block)
    size = re.search(r'\(size\s+([\d.-]+)\s+([\d.-]+)', block)
    drill = re.search(r'\(drill\s+([\d.-]+)', block)
    
    if at:
        x, y = float(at.group(1)), float(at.group(2))
        if size:
            sx, sy = float(size.group(1)), float(size.group(2))
        elif drill:
            d = float(drill.group(1))
            sx = sy = d
        else:
            sx = sy = 0
        
        min_x = min(min_x, x - sx/2)
        max_x = max(max_x, x + sx/2)
        min_y = min(min_y, y - sy/2)
        max_y = max(max_y, y + sy/2)
        print(f"  Pad at ({x}, {y}) size=({sx}, {sy}) → extent [{x-sx/2:.2f}, {x+sx/2:.2f}] x [{y-sy/2:.2f}, {y+sy/2:.2f}]")

# fp_lines on F.SilkS or F.Fab
for m in re.finditer(r'\(fp_line\b', content):
    depth = 0
    i = m.start()
    start = i
    while i < len(content):
        if content[i] == '(': depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                block = content[start:i+1]
                break
        i += 1
    
    s = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)', block)
    e = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)', block)
    if s and e:
        x1, y1 = float(s.group(1)), float(s.group(2))
        x2, y2 = float(e.group(1)), float(e.group(2))
        min_x = min(min_x, x1, x2)
        max_x = max(max_x, x1, x2)
        min_y = min(min_y, y1, y2)
        max_y = max(max_y, y1, y2)

print(f"\nExtent: X=[{min_x:.2f}, {max_x:.2f}], Y=[{min_y:.2f}, {max_y:.2f}]")
print(f"Size: {max_x-min_x:.2f} x {max_y-min_y:.2f} mm")

# Courtyard with 0.25mm margin, rounded to 0.05mm grid
margin = 0.25
import math
cx1 = math.floor((min_x - margin) * 20) / 20  # round down to 0.05
cy1 = math.floor((min_y - margin) * 20) / 20
cx2 = math.ceil((max_x + margin) * 20) / 20   # round up to 0.05
cy2 = math.ceil((max_y + margin) * 20) / 20

print(f"\nCourtyard: ({cx1}, {cy1}) to ({cx2}, {cy2})")
print(f"Courtyard size: {cx2-cx1:.2f} x {cy2-cy1:.2f} mm")

# Add courtyard rectangle to footprint
courtyard = f"""	(fp_rect
		(start {cx1} {cy1})
		(end {cx2} {cy2})
		(stroke
			(width 0.05)
			(type default)
		)
		(fill none)
		(layer "F.CrtYd")
		(uuid "courtyard-crtyd-auto")
	)"""

# Insert before the last closing paren of the footprint
last_paren = content.rfind(')')
# Go back to find a good insertion point — before the last )
indent_pos = content.rfind('\n', 0, last_paren)
content = content[:indent_pos] + '\n' + courtyard + content[indent_pos:]

# Balance check
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"Bracket balance: {depth}")

with open(MOD_FILE, 'w') as f:
    f.write(content)
print("Written courtyard to footprint.")
