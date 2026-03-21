#!/usr/bin/env python3
"""
Phase 1b: Text-merge footprint blocks from pcbnew temp output into original PCB.

pcbnew.SaveBoard corrupts KiCad 9 format, so we extract footprint blocks
from the temp file and replace the corresponding blocks in the original.
Match by reference designator (unique per board).
"""
import os, sys, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP_PCB = '/tmp/aurora-fp-update.kicad_pcb'
OUTPUT_PCB = PCB_FILE  # Write back to original

def extract_footprint_blocks(text):
    """Extract all (footprint ...) top-level blocks from PCB text.
    Returns dict mapping reference -> block text."""
    blocks = {}
    i = 0
    while True:
        # Find next top-level footprint
        idx = text.find('(footprint ', i)
        if idx < 0:
            break
        # Find matching closing paren
        depth = 0
        j = idx
        while j < len(text):
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = text[idx:j+1]
        # Extract reference
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if ref_m:
            ref = ref_m.group(1)
            blocks[ref] = block
        i = j + 1
    return blocks

# Read both files
print("Reading original PCB...")
with open(PCB_FILE, 'r') as f:
    orig_text = f.read()

print("Reading pcbnew temp PCB...")
with open(TEMP_PCB, 'r') as f:
    temp_text = f.read()

# Extract footprint blocks from both
print("Extracting footprint blocks from original...")
orig_blocks = extract_footprint_blocks(orig_text)
print(f"  Found {len(orig_blocks)} footprints in original")

print("Extracting footprint blocks from temp...")
temp_blocks = extract_footprint_blocks(temp_text)
print(f"  Found {len(temp_blocks)} footprints in temp")

# Replace original blocks with temp blocks
replaced = 0
not_in_temp = []
result = orig_text

for ref, orig_block in sorted(orig_blocks.items()):
    if ref in temp_blocks:
        temp_block = temp_blocks[ref]
        # Replace in result text
        pos = result.find(orig_block)
        if pos >= 0:
            result = result[:pos] + temp_block + result[pos + len(orig_block):]
            replaced += 1
        else:
            print(f"  WARNING: Could not find block for {ref} in result text")
    else:
        not_in_temp.append(ref)

print(f"\n=== Merge Results ===")
print(f"Replaced: {replaced}")
print(f"Not in temp (kept original): {len(not_in_temp)}")
for r in not_in_temp:
    print(f"  KEPT: {r}")

# Validate bracket balance
depth = 0
for ch in result:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: depth={depth}"
print(f"Bracket balance: OK (depth=0)")

# Write output
with open(OUTPUT_PCB, 'w') as f:
    f.write(result)
print(f"Written to {OUTPUT_PCB}")
print(f"File size: {len(result)} bytes")
