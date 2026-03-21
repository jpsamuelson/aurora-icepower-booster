#!/usr/bin/env python3
"""
Reset ALL reference field positions to library defaults based on footprint type.
This reverses the blind shifts from p5_fix_silk.py.
Uses known KiCad library default offsets per footprint type.
"""
import re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

# Library default reference offsets (local coords, before rotation)
# Format: footprint_name -> (x_offset, y_offset)
# These are the standard KiCad library reference positions
LIB_REF_DEFAULTS = {
    'R_0805_2012Metric': (0, -1.68),
    'C_0805_2012Metric': (0, -1.68),
    'C_1206_3216Metric': (0, -1.82),
    'C_1210_3225Metric': (0, -1.82),
    'C_0402_1005Metric': (0, -1.16),
    'D_SOD-323': (0, -1.55),
    'L_0805_2012Metric': (0, -1.68),
    'SOIC-8_3.9x4.9mm_P1.27mm': (0, -4.3),
    'SOT-23': (0, -2.4),
    'SOT-23-5': (0, -2.4),
    'Jack_XLR_Neutrik_NC3FBH2_Horizontal': (4.3, -10),
    'Jack_XLR_Neutrik_NC3MBH_Horizontal': (4.3, -10),
    'Jack_3.5mm_Lumberg_1503_02_Horizontal': (0, -3),
    'BarrelJack_Horizontal': (0, -5),
    'MountingHole_3.2mm_M3': (0, -4.15),
    'SW_DIP_SPSTx03_Slide_Omron_A6S-310x_W8.9mm_P2.54mm': (-4.45, -5.08),
}

with open(PCB_FILE) as f:
    text = f.read()

# Find all footprint blocks and their reference fields
# Strategy: iterate through all footprints, find the reference property,
# and set its (at ...) to the library default

def find_all_footprints(text):
    """Find all footprint blocks. Returns list of (start, end, ref, fp_type)."""
    results = []
    idx = 0
    while True:
        # Find next footprint block
        fp_start = text.find('(footprint ', idx)
        if fp_start < 0:
            fp_start = text.find('(footprint\n', idx)
        if fp_start < 0:
            break
        
        # Extract footprint type name (first string after "footprint")
        after = text[fp_start+len('(footprint'):]
        # Skip whitespace
        i = 0
        while i < len(after) and after[i] in ' \t\n\r':
            i += 1
        # Read the type string (quoted)
        if after[i] == '"':
            close_q = after.index('"', i+1)
            fp_type = after[i+1:close_q]
        else:
            # Unquoted: read until whitespace or newline
            j = i
            while j < len(after) and after[j] not in ' \t\n\r(':
                j += 1
            fp_type = after[i:j]
        
        # Find balanced end
        depth = 0
        j = fp_start
        while j < len(text):
            if text[j] == '(': depth += 1
            elif text[j] == ')':
                depth -= 1
                if depth == 0: break
            j += 1
        fp_end = j + 1
        
        block = text[fp_start:fp_end]
        
        # Extract reference
        ref = None
        ref_m = re.search(r'property "Reference" "([^"]+)"', block)
        if ref_m:
            ref = ref_m.group(1)
        else:
            ref_m = re.search(r'fp_text reference "([^"]+)"', block)
            if ref_m:
                ref = ref_m.group(1)
        
        if ref:
            # Strip library prefix from fp_type
            if ':' in fp_type:
                fp_type = fp_type.split(':', 1)[1]
            results.append((fp_start, fp_end, ref, fp_type))
        
        idx = fp_end
    
    return results

footprints = find_all_footprints(text)
print(f"Found {len(footprints)} footprints")

# Count types
type_counts = {}
for _, _, _, fp_type in footprints:
    type_counts[fp_type] = type_counts.get(fp_type, 0) + 1
print("Types:")
for t in sorted(type_counts.keys()):
    default = "✓" if t in LIB_REF_DEFAULTS else "✗"
    print(f"  {type_counts[t]:3d}  {default}  {t}")

# Reset reference positions
reset_count = 0
for fp_start, fp_end, ref, fp_type in reversed(footprints):
    if fp_type not in LIB_REF_DEFAULTS:
        continue
    
    default_x, default_y = LIB_REF_DEFAULTS[fp_type]
    block = text[fp_start:fp_end]
    
    # Find reference field property
    # New format: (property "Reference" "REF" (at X Y [angle]) ...)
    ref_pat = f'(property "Reference" "{ref}"'
    ref_idx = block.find(ref_pat)
    if ref_idx < 0:
        # Old format: (fp_text reference "REF" (at X Y [angle]) ...)
        ref_pat = f'(fp_text reference "{ref}"'
        ref_idx = block.find(ref_pat)
    if ref_idx < 0:
        continue
    
    # Find (at ...) within this property (first one after the reference text)
    after_ref = block[ref_idx:]
    at_m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\s*(?:unlocked\s*)?\)', after_ref)
    if not at_m:
        continue
    
    old_x = float(at_m.group(1))
    old_y = float(at_m.group(2))
    angle_part = ''
    if at_m.group(3):
        angle_part = f' {at_m.group(3)}'
    
    # Check if 'unlocked' is in the at group
    unlock_str = ''
    if 'unlocked' in at_m.group(0):
        unlock_str = ' unlocked'
    
    # Only update if different from default
    if abs(old_x - default_x) > 0.001 or abs(old_y - default_y) > 0.001:
        old_at = at_m.group(0)
        new_at = f'(at {default_x} {default_y}{angle_part}{unlock_str})'
        
        # Replace in block
        new_after_ref = after_ref.replace(old_at, new_at, 1)
        new_block = block[:ref_idx] + new_after_ref
        text = text[:fp_start] + new_block + text[fp_end:]
        reset_count += 1

print(f"\nReset {reset_count} reference positions to library defaults")

# Bracket balance
depth = 0
for ch in text:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"Bracket balance: OK")

with open(PCB_FILE, 'w') as f:
    f.write(text)
print(f"Written: {len(text)} bytes")
