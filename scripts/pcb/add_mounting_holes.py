#!/usr/bin/env python3
"""
Add 4x M3 mounting holes at board corners and configure board text.
Edits .kicad_pcb directly.
"""
import uuid
import re
import os

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
PCB_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_pcb")

# Mounting hole positions: 5mm from edges on a 200x170mm board
HOLES = [
    {"x": 5,   "y": 5,   "label": "MH1"},
    {"x": 195, "y": 5,   "label": "MH2"},
    {"x": 5,   "y": 165, "label": "MH3"},
    {"x": 195, "y": 165, "label": "MH4"},
]

def make_mounting_hole(x, y, label):
    """Generate a KiCad 9 footprint block for a 3.2mm NPTH mounting hole with 6mm copper pad."""
    uid = str(uuid.uuid4())
    uid_ref = str(uuid.uuid4())
    uid_val = str(uuid.uuid4())
    uid_fab = str(uuid.uuid4())
    uid_cyd = str(uuid.uuid4())
    uid_pad = str(uuid.uuid4())
    return f"""\t(footprint "MountingHole:MountingHole_3.2mm_M3_Pad"
\t\t(layer "F.Cu")
\t\t(at {x} {y})
\t\t(uuid "{uid}")
\t\t(property "Reference" "{label}"
\t\t\t(at 0 -4.2)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{uid_ref}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "MountingHole"
\t\t\t(at 0 4.2)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{uid_val}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(fp_circle
\t\t\t(center 0 0)
\t\t\t(end 3.2 0)
\t\t\t(stroke
\t\t\t\t(width 0.15)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{uid_cyd}")
\t\t)
\t\t(fp_text user "${{REFERENCE}}"
\t\t\t(at 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{uid_fab}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pad "1" thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size 6 6)
\t\t\t(drill 3.2)
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(remove_unused_layers no)
\t\t\t(uuid "{uid_pad}")
\t\t)
\t)
"""


with open(PCB_FILE, 'r') as f:
    content = f.read()

# Insert mounting holes before closing paren
close_pos = content.rstrip().rfind(')')
before = content[:close_pos].rstrip()

holes_section = "\n"
for h in HOLES:
    holes_section += make_mounting_hole(h["x"], h["y"], h["label"])

new_content = before + holes_section + "\n)\n"

with open(PCB_FILE, 'w') as f:
    f.write(new_content)

# Verify
depth = 0
for ch in new_content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"Mounting holes added: {len(HOLES)}")
print(f"PCB file size: {len(new_content)} bytes")
print(f"Paren balance: {depth}")
