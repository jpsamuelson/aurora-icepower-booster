#!/usr/bin/env python3
"""
Apply library-default reference positions to all footprints in the PCB.
Uses the JSON output from p5e_get_lib_refs.py (pcbnew-extracted positions).
Handles rotation: library default (0, -1.65) is the LOCAL offset from
footprint center in the footprint's own coordinate system.
"""
import re, json, math

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'
LIB_REFS = '/tmp/lib_ref_positions.json'

with open(PCB) as f:
    text = f.read()

with open(LIB_REFS) as f:
    lib_refs = json.load(f)

def extract_balanced(text, start):
    """Extract balanced parentheses block starting at text[start]='('."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
        i += 1
    return None, start

def find_footprint_blocks(text):
    """Find all (footprint ...) blocks with their positions."""
    results = []
    i = 0
    while True:
        idx = text.find('(footprint ', i)
        if idx < 0:
            break
        block, end = extract_balanced(text, idx)
        if block:
            results.append((idx, end, block))
        i = idx + 1
    return results

def get_ref_from_block(block):
    """Extract reference designator from footprint block."""
    m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    return m.group(1) if m else None

def get_fp_rotation(block):
    """Extract footprint rotation from (at x y angle)."""
    m = re.search(r'\(at\s+[\d.-]+\s+[\d.-]+(?:\s+([\d.-]+))?\)', block)
    if m and m.group(1):
        return float(m.group(1))
    return 0.0

# For KiCad PCB, reference field (at x y angle) is in LOCAL coordinates
# of the footprint. The library default offset (dx, dy) is already in local coords.
# We just need to update the local (at ...) of the Reference property.

# Examine a sample first
fp_blocks = find_footprint_blocks(text)
print(f"Found {len(fp_blocks)} footprints")

# Check a few for current format
for start, end, block in fp_blocks[:3]:
    ref = get_ref_from_block(block)
    ref_prop_m = re.search(
        r'\(property\s+"Reference"\s+"[^"]+"\s+\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)',
        block
    )
    if ref_prop_m:
        rx, ry = ref_prop_m.group(1), ref_prop_m.group(2)
        ra = ref_prop_m.group(3) or '0'
        rot = get_fp_rotation(block)
        print(f"  {ref}: ref_local=({rx},{ry},{ra}) fp_rot={rot}")

# Now apply library defaults
changes = 0
skipped = 0
new_text = text

# Process in reverse order (so positions stay valid as we replace)
for start, end, block in reversed(fp_blocks):
    ref = get_ref_from_block(block)
    if not ref or ref not in lib_refs:
        skipped += 1
        continue
    
    dx, dy = lib_refs[ref]
    
    # Find the Reference property in this block
    ref_prop_m = re.search(
        r'(\(property\s+"Reference"\s+"[^"]+"\s+\(at\s+)([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?(\))',
        block
    )
    if not ref_prop_m:
        skipped += 1
        continue
    
    old_at = ref_prop_m.group(0)
    old_rx = float(ref_prop_m.group(2))
    old_ry = float(ref_prop_m.group(3))
    old_ra = ref_prop_m.group(4)
    
    # Build new at string - keep existing rotation angle if present
    if old_ra:
        new_at = f'{ref_prop_m.group(1)}{dx} {dy} {old_ra})'
    else:
        new_at = f'{ref_prop_m.group(1)}{dx} {dy})'
    
    if old_at != new_at:
        # Replace within the original text
        abs_pos = start + ref_prop_m.start()
        new_text = new_text[:abs_pos] + new_at + new_text[abs_pos + len(old_at):]
        changes += 1

print(f"\nApplied {changes} reference position changes, skipped {skipped}")

# Verify bracket balance
depth = 0
for ch in new_text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print("Bracket balance OK")

with open(PCB, 'w') as f:
    f.write(new_text)
print(f"Written {len(new_text)} bytes to PCB")
