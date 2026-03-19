#!/usr/bin/env python3
"""Compute actual pin positions for key components to map them to wire groups.
Uses lib_symbols cache for pin offsets and symbol instance rotation/mirror."""
import re, math

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# ---- Get pin offsets from lib_symbols cache ----
def get_lib_pins(lib_name):
    """Get pin number -> (x, y) offset from lib_symbols cache."""
    pins = {}
    # Find the sub-symbols (e.g., "Device:R_0_1") that contain pins
    base = lib_name.replace(':', '_') if ':' in lib_name else lib_name
    # Search for sub-symbol blocks
    cache_start = text.find('(lib_symbols')
    cache_end = text.find('(symbol (lib_id')  # First instance
    cache = text[cache_start:cache_end] if cache_start >= 0 else ""
    
    for m in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+)(?: (\d+))?\).*?\(number "([^"]+)"\)', cache, re.DOTALL):
        px, py = float(m.group(1)), float(m.group(2))
        rot = int(m.group(3)) if m.group(3) else 0
        pnum = m.group(4)
        # Pin direction from 'at' in lib is the pin tip position relative to symbol center
        pins[pnum] = (px, py, rot)
    
    return pins

# ---- Get symbol instance data ----
def get_instance(ref_name):
    """Get symbol instance position, rotation, mirror."""
    pat = rf'\(property "Reference" "{re.escape(ref_name)}"'
    for m in re.finditer(pat, text):
        pos = m.start()
        # Walk back to find symbol start
        start = pos
        depth = 0
        while start > 0:
            start -= 1
            if text[start] == ')': depth += 1
            elif text[start] == '(':
                depth -= 1
                if depth < 0: break
        
        # Skip if in lib_symbols
        if start < text.find('(symbol (lib_id'):
            continue
        
        # Find end
        depth = 0
        for end in range(start, min(start+10000, len(text))):
            if text[end] == '(': depth += 1
            elif text[end] == ')': depth -= 1
            if depth == 0: break
        
        block = text[start:end+1]
        lib_m = re.search(r'lib_id "([^"]+)"', block)
        pos_m = re.search(r'\(at ([\d.]+) ([\d.]+)(?:\s+(\d+))?\)', block)
        mirror_m = re.search(r'\(mirror ([xy])\)', block)
        
        if pos_m:
            return {
                'ref': ref_name,
                'lib': lib_m.group(1) if lib_m else '?',
                'x': float(pos_m.group(1)),
                'y': float(pos_m.group(2)),
                'rot': int(pos_m.group(3)) if pos_m.group(3) else 0,
                'mirror': mirror_m.group(1) if mirror_m else None,
                'block': block,
            }
    return None

def compute_pin_pos(sym_x, sym_y, sym_rot, pin_x, pin_y, mirror=None):
    """Compute absolute pin position from symbol pos + pin offset + rotation."""
    # Apply mirror first (if any)
    if mirror == 'x':
        pin_x = -pin_x
    elif mirror == 'y':
        pin_y = -pin_y
    
    # Apply rotation (CCW in KiCad)
    angle = math.radians(sym_rot)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    rx = pin_x * cos_a - pin_y * sin_a
    ry = pin_x * sin_a + pin_y * cos_a
    
    # KiCad schematic: Y is inverted for pin positions
    abs_x = sym_x + rx
    abs_y = sym_y - ry
    
    return (round(abs_x, 2), round(abs_y, 2))

# Get pin definitions for Device:R and Device:D
print("=== Library pin offsets ===")
# Device:R typically has pins at (0, 1.27) and (0, -1.27)
# Device:D typically has pins at (0, 1.27) and (0, -1.27) 
# Let me find them from the cache

# Search for pins in Device:R sub-symbols
r_pins = {}
d_pins = {}
xlr3_pins = {}
xlr3g_pins = {}

# Device:R pins
for m in re.finditer(r'\(symbol "Device:R_0_1"\s*\(', text):
    start = m.start()
    depth = 0
    for i in range(start, min(start+2000, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    for pm in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\).*?\(number "([^"]+)"\)', block, re.DOTALL):
        r_pins[pm.group(4)] = (float(pm.group(1)), float(pm.group(2)))
    break

# Device:D pins
for m in re.finditer(r'\(symbol "Device:D_0_1"\s*\(', text):
    start = m.start()
    depth = 0
    for i in range(start, min(start+2000, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    for pm in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\).*?\(number "([^"]+)"\)', block, re.DOTALL):
        d_pins[pm.group(4)] = (float(pm.group(1)), float(pm.group(2)))
    break

# XLR3 pins
for m in re.finditer(r'\(symbol "Connector_Audio:XLR3_0_1"\s*\(', text):
    start = m.start()
    depth = 0
    for i in range(start, min(start+3000, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    for pm in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\).*?\(number "([^"]+)"\)', block, re.DOTALL):
        xlr3_pins[pm.group(4)] = (float(pm.group(1)), float(pm.group(2)))
    break

# XLR3_Ground pins  
for m in re.finditer(r'\(symbol "Connector_Audio:XLR3_Ground_0_1"\s*\(', text):
    start = m.start()
    depth = 0
    for i in range(start, min(start+3000, len(text))):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    block = text[start:i+1]
    for pm in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+)(?:\s+(\d+))?\).*?\(number "([^"]+)"\)', block, re.DOTALL):
        xlr3g_pins[pm.group(4)] = (float(pm.group(1)), float(pm.group(2)))
    break

print(f"Device:R pins: {r_pins}")
print(f"Device:D pins: {d_pins}")
print(f"XLR3 pins: {xlr3_pins}")
print(f"XLR3_Ground pins: {xlr3g_pins}")

# ---- Compute pin positions for CH1 components ----
print("\n=== CH1 Pin Positions ===")

components = ['J3', 'J9', 'R58', 'R88', 'R94', 'R95', 'D8', 'D9', 'D10', 'R2', 'R3']
for ref in components:
    inst = get_instance(ref)
    if not inst:
        print(f"  {ref}: NOT FOUND")
        continue
    
    # Select pin library
    if inst['lib'] == 'Device:R':
        lib_pins = r_pins
    elif inst['lib'] == 'Device:D':
        lib_pins = d_pins
    elif inst['lib'] == 'Connector_Audio:XLR3':
        lib_pins = xlr3_pins
    elif inst['lib'] == 'Connector_Audio:XLR3_Ground':
        lib_pins = xlr3g_pins
    else:
        print(f"  {ref}: Unknown lib {inst['lib']}")
        continue
    
    print(f"\n  {ref} ({inst['lib']}) at ({inst['x']}, {inst['y']}) rot={inst['rot']}° mirror={inst['mirror']}")
    for pnum, (px, py) in lib_pins.items():
        abs_pos = compute_pin_pos(inst['x'], inst['y'], inst['rot'], px, py, inst['mirror'])
        print(f"    Pin {pnum}: lib_offset=({px}, {py}) → abs=({abs_pos[0]}, {abs_pos[1]})")
