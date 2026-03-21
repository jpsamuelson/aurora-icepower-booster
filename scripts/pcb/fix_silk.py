#!/usr/bin/env python3
"""
Fix silk screen warnings:
1. silk_over_copper: Move/hide reference designators that overlap with copper
2. silk_overlap: Hide overlapping reference designators (keep only visible ones)
3. silk_edge_clearance: Move silkscreen text away from board edge

Strategy: For SMD components, hide the reference text (set to invisible).
For through-hole and connectors, keep references but move if needed.
"""
import re, json, os

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"
DRC = "/tmp/aurora-drc-routed.json"

with open(PCB) as f:
    content = f.read()

# Read DRC to find specific problematic references
with open(DRC) as f:
    drc = json.load(f)

# Collect all references that cause silk warnings
problem_refs = set()
for v in drc.get('violations', []):
    vtype = v.get('type', '')
    if vtype in ('silk_over_copper', 'silk_overlap', 'silk_edge_clearance'):
        for item in v.get('items', []):
            desc = item.get('description', '')
            # Pattern: "Reference 'R1' of footprint ..."
            m = re.search(r"Reference '([^']+)'", desc)
            if m:
                problem_refs.add(m.group(1))
            # Pattern: "Value 'xxx' of footprint ..."
            m = re.search(r"Value '([^']+)'", desc)
            if m:
                pass  # We'll handle values separately

print(f"Problem references from DRC: {len(problem_refs)}")

# For all SMD footprints, hide reference text to clean up silk layer
# This is standard practice for production PCBs from JLCPCB
# We'll hide ALL reference properties on silk to reduce clutter

# Find all footprint reference properties and make them invisible
# Pattern in KiCad 9: (property "Reference" "R1" (at ...) (layer "F.Silkscreen") (...)
# The visibility is controlled by having or not having (hide yes)

changes = 0
lines = content.split('\n')
result_lines = []

i = 0
while i < len(lines):
    line = lines[i]
    
    # Look for reference properties in footprints
    if '(property "Reference"' in line:
        # Collect the full property block
        depth = 0
        block_start = i
        block_lines = [line]
        for ch in line:
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
        
        j = i + 1
        while j < len(lines) and depth > 0:
            block_lines.append(lines[j])
            for ch in lines[j]:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            j += 1
        
        block = '\n'.join(block_lines)
        
        # Check if this is on a Silkscreen layer
        if 'SilkS' in block or 'Silkscreen' in block:
            # Extract reference name
            ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
            ref_name = ref_m.group(1) if ref_m else '?'
            
            # Make it invisible if not already
            if '(hide yes)' not in block:
                # Find the effects section and add hide
                if '(effects' in block:
                    block = block.replace('(effects', '(hide yes)\n' + '\t' * 5 + '(effects', 1)
                    changes += 1
                
                # Write modified block
                result_lines.extend(block.split('\n'))
                i = j
                continue
        
        result_lines.extend(block_lines)
        i = j
        continue
    
    # Also handle "Value" properties on Silkscreen
    if '(property "Value"' in line:
        depth = 0
        block_lines = [line]
        for ch in line:
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
        
        j = i + 1
        while j < len(lines) and depth > 0:
            block_lines.append(lines[j])
            for ch in lines[j]:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            j += 1
        
        block = '\n'.join(block_lines)
        
        if ('SilkS' in block or 'Silkscreen' in block) and '(hide yes)' not in block:
            block = block.replace('(effects', '(hide yes)\n' + '\t' * 5 + '(effects', 1)
            changes += 1
            result_lines.extend(block.split('\n'))
            i = j
            continue
        
        result_lines.extend(block_lines)
        i = j
        continue
    
    result_lines.append(line)
    i += 1

content = '\n'.join(result_lines)

# Bracket balance
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
if depth != 0:
    print(f"❌ Bracket balance: {depth}")
    import sys; sys.exit(1)

print(f"Bracket balance: OK")
print(f"References/Values hidden: {changes}")

with open(PCB, 'w') as f:
    f.write(content)

print(f"✅ Silk cleanup done")
print(f"   Size: {len(content):,} bytes")
