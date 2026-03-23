#!/usr/bin/env python3
"""Add courtyard to J2 and J15 footprint instances in the PCB file."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

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

courtyard = """(fp_rect
			(start -9.4 -5.5)
			(end 5.15 5.5)
			(stroke
				(width 0.05)
				(type default)
			)
			(fill none)
			(layer "F.CrtYd")
			(uuid "courtyard-pcb-auto")
		)"""

fixed = 0
# Find J2 and J15 footprints in PCB
for ref_name in ["J2", "J15"]:
    ref_idx = content.find(f'"Reference" "{ref_name}"')
    if ref_idx < 0:
        print(f"  {ref_name} not found!")
        continue
    
    fp_start = content.rfind('(footprint', 0, ref_idx)
    fp_block, fp_end = extract_block(content, fp_start)
    
    if fp_block and 'F.CrtYd' not in fp_block:
        # Insert courtyard before the last ) of the footprint
        insert_pos = fp_end - 1  # before the closing )
        # Find the last newline before the closing )
        last_nl = content.rfind('\n', fp_start, fp_end)
        
        indent = "\n\t\t"
        insert_text = indent + courtyard
        content = content[:last_nl] + insert_text + content[last_nl:]
        fixed += 1
        print(f"  Added courtyard to {ref_name}")
    elif fp_block and 'F.CrtYd' in fp_block:
        print(f"  {ref_name} already has courtyard")
    
    # After modifying, need to update offsets for next search
    # Re-read for second pass

# If we modified, write and re-do for the second footprint
if fixed == 1:
    # Write and re-read to fix offsets
    with open(PCB, 'w') as f:
        f.write(content)
    with open(PCB) as f:
        content = f.read()
    
    # Try the other one
    for ref_name in ["J2", "J15"]:
        ref_idx = content.find(f'"Reference" "{ref_name}"')
        fp_start = content.rfind('(footprint', 0, ref_idx)
        fp_block, fp_end = extract_block(content, fp_start)
        
        if fp_block and 'F.CrtYd' not in fp_block:
            last_nl = content.rfind('\n', fp_start, fp_end)
            indent = "\n\t\t"
            insert_text = indent + courtyard.replace("courtyard-pcb-auto", f"courtyard-pcb-{ref_name.lower()}")
            content = content[:last_nl] + insert_text + content[last_nl:]
            fixed += 1
            print(f"  Added courtyard to {ref_name}")

# Balance check
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"\nBracket balance: {depth}")
print(f"Fixed {fixed} footprints")

with open(PCB, 'w') as f:
    f.write(content)
print("Written.")
