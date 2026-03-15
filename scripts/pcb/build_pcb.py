#!/usr/bin/env python3
"""
Generate populated .kicad_pcb from netlist and placement data.
Reads footprints from KiCad libraries and assembles a complete PCB file.
"""
import json
import os
import re
import uuid as uuid_mod

KICAD_FP_DIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
PROJECT_DIR = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster"

# Custom footprint paths (project-specific libs)
CUSTOM_FP_DIRS = [
    os.path.join(PROJECT_DIR, "libs"),
    os.path.join(PROJECT_DIR, "aurora-dsp-icepower-booster.pretty"),
]

# Mapping: schematic footprint ID → actual KiCad library file path
# Used when the schematic footprint name differs from the .kicad_mod filename
FP_NAME_MAP = {
    "Connector_Audio:XLR-F_Neutrik_NC3FBH2":
        os.path.join(KICAD_FP_DIR, "Connector_Audio.pretty", "Jack_XLR_Neutrik_NC3FBH2_Horizontal.kicad_mod"),
    "Connector_Audio:XLR-M_Neutrik_NC3MBH":
        os.path.join(KICAD_FP_DIR, "Connector_Audio.pretty", "Jack_XLR_Neutrik_NC3MBH_Horizontal.kicad_mod"),
    "Button_Switch_SMD:SW_DIP_SPSTx03_Slide_Omron_A6S-310x":
        os.path.join(KICAD_FP_DIR, "Button_Switch_SMD.pretty", "SW_DIP_SPSTx03_Slide_Omron_A6S-310x_W8.9mm_P2.54mm.kicad_mod"),
    "Converter_DCDC:Converter_DCDC_TRACO_TEL5_DIP-24":
        os.path.join(KICAD_FP_DIR, "Package_DIP.pretty", "DIP-24_W15.24mm.kicad_mod"),
}

def find_footprint_file(footprint_id):
    """Find .kicad_mod file for a footprint like 'Resistor_SMD:R_0805_2012Metric'."""
    # Check explicit name mapping first
    if footprint_id in FP_NAME_MAP:
        mapped = FP_NAME_MAP[footprint_id]
        if os.path.exists(mapped):
            return mapped

    lib, fp = footprint_id.split(":", 1)
    
    # Check KiCad standard libraries
    fp_path = os.path.join(KICAD_FP_DIR, f"{lib}.pretty", f"{fp}.kicad_mod")
    if os.path.exists(fp_path):
        return fp_path
    
    # Check custom paths
    for d in CUSTOM_FP_DIRS:
        fp_path = os.path.join(d, f"{fp}.kicad_mod")
        if os.path.exists(fp_path):
            return fp_path
    
    return None

def load_footprint(footprint_id):
    """Load a footprint .kicad_mod file content."""
    fp_path = find_footprint_file(footprint_id)
    if fp_path is None:
        print(f"  WARNING: Footprint not found: {footprint_id}")
        return None
    with open(fp_path, 'r') as f:
        return f.read()

def transform_footprint(fp_content, ref, value, x, y, rotation, fp_id):
    """Transform a footprint module content for placement in pcb."""
    # The .kicad_mod file starts with (footprint "name" ...)
    # We need to:
    # 1. Update the footprint header with position
    # 2. Update reference and value
    # 3. Add UUID
    
    uid = str(uuid_mod.uuid4())
    
    # Replace the first line: (footprint "..." → (footprint "..." (layer "F.Cu") (at x y rot) ...
    # The .kicad_mod format might differ from pcb format
    lines = fp_content.strip()
    
    # Extract the footprint name from the first line
    fp_name_match = re.match(r'\(footprint\s+"([^"]+)"', lines)
    if not fp_name_match:
        # Try module format (older KiCad)
        fp_name_match = re.match(r'\(module\s+"?([^"\s]+)"?', lines)
        if not fp_name_match:
            print(f"  WARNING: Cannot parse footprint format for {ref}")
            return None
    
    fp_name = fp_name_match.group(1)
    
    # Build the position string
    at_str = f"(at {x} {y}" + (f" {rotation}" if rotation != 0 else "") + ")"
    
    # Replace/insert position and layer in the header
    # Remove existing (layer ...) and (at ...) if any
    # Insert our own after the footprint name
    
    # Find the end of the first ( footprint "name" section
    header_end = lines.find('\n', lines.find('"'))
    if header_end == -1:
        header_end = min(200, len(lines))
    
    # Rebuild: keep everything after header, insert our attrs
    # First, strip any existing (at ...) and (layer ...) from the content
    content_clean = lines
    content_clean = re.sub(r'\(at\s+[^)]+\)', '', content_clean, count=1)
    content_clean = re.sub(r'\(layer\s+"[^"]+"\)', '', content_clean, count=1)
    
    # Re-match after cleaning
    fp_name_match = re.match(r'\(footprint\s+"([^"]+)"\s*', content_clean)
    if not fp_name_match:
        fp_name_match = re.match(r'\(module\s+"?([^"\s]+)"?\s*', content_clean)
    
    insert_pos = fp_name_match.end()
    
    # Insert layer, at, uuid
    insert_str = f'(layer "F.Cu") {at_str} (uuid "{uid}")\n\t'
    
    new_content = content_clean[:insert_pos] + insert_str + content_clean[insert_pos:]
    
    # Update Reference property
    new_content = re.sub(
        r'(\(property\s+"Reference"\s+)"[^"]*"',
        f'\\1"{ref}"',
        new_content,
        count=1
    )
    # Also try fp_text format (older KiCad)
    new_content = re.sub(
        r'(\(fp_text\s+reference\s+)"[^"]*"',
        f'\\1"{ref}"',
        new_content,
        count=1
    )
    
    # Update Value property
    new_content = re.sub(
        r'(\(property\s+"Value"\s+)"[^"]*"',
        f'\\1"{value}"',
        new_content,
        count=1
    )
    new_content = re.sub(
        r'(\(fp_text\s+value\s+)"[^"]*"',
        f'\\1"{value}"',
        new_content,
        count=1
    )
    
    # Update Footprint property if it exists
    new_content = re.sub(
        r'(\(property\s+"Footprint"\s+)"[^"]*"',
        f'\\1"{fp_id}"',
        new_content,
        count=1
    )
    
    return new_content

# ============================================================
# Read placement data and netlist
# ============================================================
with open(os.path.join(PROJECT_DIR, 'pcb_placements.json'), 'r') as f:
    placements = json.load(f)

with open(os.path.join(PROJECT_DIR, 'placement_data.json'), 'r') as f:
    netlist_data = json.load(f)

# ============================================================
# Check which footprints we need and verify they exist
# ============================================================
unique_fps = set()
for p in placements:
    unique_fps.add(p['footprint'])

print(f"Unique footprints needed: {len(unique_fps)}")
for fp in sorted(unique_fps):
    fp_path = find_footprint_file(fp)
    status = "✅" if fp_path else "❌"
    print(f"  {status} {fp}")

# ============================================================
# Load and cache footprint templates
# ============================================================
fp_cache = {}
for fp in unique_fps:
    content = load_footprint(fp)
    if content:
        fp_cache[fp] = content

print(f"\nLoaded {len(fp_cache)}/{len(unique_fps)} footprints")

# ============================================================
# Read existing PCB header
# ============================================================
pcb_path = os.path.join(PROJECT_DIR, 'aurora-dsp-icepower-booster.kicad_pcb')
with open(pcb_path, 'r') as f:
    pcb_content = f.read()

# Find the end of the header (before any footprints or the closing paren)
# The PCB has: header, setup, layers, nets section, then footprints, then )
# We keep everything up to and including the net definitions, then add footprints

# Parse nets from netlist
net_section = ""
net_id = 0
net_names = {}

# Add unconnected net
net_section += f'\t(net {net_id} "")\n'
net_names[""] = net_id

for net_info in netlist_data['nets']:
    net_id += 1
    name = net_info['name']
    # Remove leading / from net names
    if name.startswith('/'):
        name = name[1:]
    net_section += f'\t(net {net_id} "{name}")\n'
    net_names[name] = net_id

# Also add V+, V-, GND nets (from schematic labels, not in netlist as separate entries)
# These are connected via labels in the schematic
for extra_net in ['GND', 'V+', 'V-']:
    if extra_net not in net_names:
        net_id += 1
        net_section += f'\t(net {net_id} "{extra_net}")\n'
        net_names[extra_net] = net_id

print(f"Nets defined: {len(net_names)}")

# ============================================================
# Build footprint section
# ============================================================
footprint_section = ""
placed_count = 0
failed_count = 0

for p in placements:
    ref = p['ref']
    fp_id = p['footprint']
    value = p['value']
    x = p['x']
    y = p['y']
    rot = p.get('rotation', 0)
    
    if fp_id not in fp_cache:
        print(f"  SKIP: {ref} ({fp_id}) — footprint not loaded")
        failed_count += 1
        continue
    
    transformed = transform_footprint(fp_cache[fp_id], ref, value, x, y, rot, fp_id)
    if transformed:
        footprint_section += "\t" + transformed + "\n"
        placed_count += 1
    else:
        failed_count += 1

print(f"\nFootprints transformed: {placed_count} ok, {failed_count} failed")

# ============================================================
# Assemble complete PCB file
# ============================================================
# Remove existing net definitions
if '(net ' in pcb_content:
    pcb_content = re.sub(r'\t\(net \d+ "[^"]*"\)\n', '', pcb_content)
    pcb_content = re.sub(r'\t\(net \d+ ""\)\n', '', pcb_content)

# Remove existing footprints (multi-line blocks starting with \t(footprint)
# Each footprint block is a balanced s-expression starting at column 1 tab
def remove_footprint_blocks(content):
    """Remove all top-level (footprint ...) blocks from PCB content."""
    result = []
    i = 0
    lines = content.split('\n')
    skip = False
    depth = 0
    for line in lines:
        if not skip and re.match(r'^\t\(footprint\s', line):
            skip = True
            depth = 0
            for ch in line:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            if depth == 0:
                skip = False
            continue
        if skip:
            for ch in line:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            if depth <= 0:
                skip = False
            continue
        result.append(line)
    return '\n'.join(result)

pcb_content = remove_footprint_blocks(pcb_content)

# Find the position after the setup section to insert nets
setup_end = pcb_content.find(')\n', pcb_content.rfind('(setup'))
if setup_end > 0:
    setup_end += 2  # After the )\n
else:
    setup_end = pcb_content.rfind(')')

# Insert nets after setup, footprints after nets, keep board outline etc.
# Find closing paren position
close_pos = pcb_content.rstrip().rfind(')')
before_close = pcb_content[:close_pos].rstrip()

new_pcb = before_close + "\n" + net_section + "\n" + footprint_section + "\n)\n"

# Write the new PCB file
with open(pcb_path, 'w') as f:
    f.write(new_pcb)

file_size = len(new_pcb)
print(f"\nPCB file written: {file_size} bytes")
print(f"Components: {placed_count}")
print(f"Nets: {len(net_names)}")

# Quick validation
depth = 0
for ch in new_pcb:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"Paren balance: {depth}")
