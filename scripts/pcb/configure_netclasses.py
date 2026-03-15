#!/usr/bin/env python3
"""
Configure netclasses and design rules in the KiCad project file.
Per copilot-instructions.md §7 JLCPCB Design Rules.
"""
import json
import os

PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"
PRO_FILE = os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.kicad_pro")

with open(PRO_FILE, 'r') as f:
    pro = json.load(f)

# ============================================================
# Netclasses per §7 copilot-instructions.md
# ============================================================
netclasses = [
    {
        "bus_width": 12,
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.2,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Default",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "priority": 2147483647,
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "track_width": 0.25,
        "via_diameter": 0.6,
        "via_drill": 0.3,
        "wire_width": 6
    },
    {
        "bus_width": 12,
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.5,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Power",
        "pcb_color": "rgba(255, 0, 0, 0.500)",
        "priority": 100,
        "schematic_color": "rgba(255, 0, 0, 0.500)",
        "track_width": 0.5,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6
    },
    {
        "bus_width": 12,
        "clearance": 0.25,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.3,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Audio_Input",
        "pcb_color": "rgba(0, 128, 0, 0.500)",
        "priority": 200,
        "schematic_color": "rgba(0, 128, 0, 0.500)",
        "track_width": 0.3,
        "via_diameter": 0.6,
        "via_drill": 0.3,
        "wire_width": 6
    },
    {
        "bus_width": 12,
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.5,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Audio_Output",
        "pcb_color": "rgba(0, 0, 255, 0.500)",
        "priority": 300,
        "schematic_color": "rgba(0, 0, 255, 0.500)",
        "track_width": 0.5,
        "via_diameter": 0.6,
        "via_drill": 0.3,
        "wire_width": 6
    },
    {
        "bus_width": 12,
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.8,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Audio_Power",
        "pcb_color": "rgba(255, 128, 0, 0.500)",
        "priority": 400,
        "schematic_color": "rgba(255, 128, 0, 0.500)",
        "track_width": 0.8,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6
    },
]

# ============================================================
# Net-to-class assignment patterns
# ============================================================
# KiCad uses glob patterns matched against net names
netclass_patterns = [
    # Power nets
    {"netclass": "Power", "pattern": "+12V"},
    {"netclass": "Power", "pattern": "-12V"},
    # Audio Power (V+, V-, GND)
    {"netclass": "Audio_Power", "pattern": "V+"},
    {"netclass": "Audio_Power", "pattern": "V-"},
    {"netclass": "Audio_Power", "pattern": "GND"},
    # Audio Input nets (HOT_IN, COLD_IN, HOT_RAW, COLD_RAW)
    {"netclass": "Audio_Input", "pattern": "CH*_HOT_IN"},
    {"netclass": "Audio_Input", "pattern": "CH*_COLD_IN"},
    {"netclass": "Audio_Input", "pattern": "CH*_HOT_RAW"},
    {"netclass": "Audio_Input", "pattern": "CH*_COLD_RAW"},
    # Audio Output nets
    {"netclass": "Audio_Output", "pattern": "CH*_OUT_HOT"},
    {"netclass": "Audio_Output", "pattern": "CH*_GAIN_OUT"},
    {"netclass": "Audio_Output", "pattern": "CH*_RX_OUT"},
]

# ============================================================
# Update project file
# ============================================================
pro["net_settings"]["classes"] = netclasses
pro["net_settings"]["netclass_patterns"] = netclass_patterns

# ============================================================
# Design rules (§7 JLCPCB, optimized for audio)
# ============================================================
rules = pro["board"]["design_settings"]["rules"]
rules["min_clearance"] = 0.15
rules["min_track_width"] = 0.15
rules["min_via_diameter"] = 0.45
rules["min_via_annular_width"] = 0.125
rules["min_through_hole_diameter"] = 0.2
rules["min_hole_clearance"] = 0.25
rules["min_hole_to_hole"] = 0.25
rules["min_copper_edge_clearance"] = 0.3
rules["min_silk_clearance"] = 0.1
rules["min_text_height"] = 0.8
rules["min_text_thickness"] = 0.15

# Track width presets
pro["board"]["design_settings"]["track_widths"] = [
    0.15,   # Minimum (JLCPCB)
    0.2,    # Fine signal
    0.25,   # Default signal
    0.3,    # Audio signal
    0.5,    # Power
    0.8,    # Audio Power
    1.0,    # High current
    1.5,    # Speaker
]

# Via dimension presets
pro["board"]["design_settings"]["via_dimensions"] = [
    {"diameter": 0.6, "drill": 0.3},   # Standard signal
    {"diameter": 0.8, "drill": 0.4},   # Power
]

# ============================================================
# Write updated project file
# ============================================================
with open(PRO_FILE, 'w') as f:
    json.dump(pro, f, indent=2)

print("Project file updated:")
print(f"  Netclasses: {len(netclasses)}")
print(f"  Net patterns: {len(netclass_patterns)}")
print(f"  Track presets: {len(pro['board']['design_settings']['track_widths'])}")
print(f"  Via presets: {len(pro['board']['design_settings']['via_dimensions'])}")
print(f"  Design rules updated ✅")
