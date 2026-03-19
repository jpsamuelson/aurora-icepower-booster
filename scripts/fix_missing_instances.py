#!/usr/bin/env python3
"""
Fix 6 GND power symbols missing their (instances ...) section.

Root cause: fix_erc_all.py created these symbols without the required
(instances (project "..." (path "..." (reference "...") (unit 1)))) block.

eeschema treats symbols without instances as unannotated (#PWR?) which causes:
- 6x duplicate_reference (all appear as #PWR?)
- 1x unannotated

Fix: Add the missing instances section to each symbol, using the project UUID
from the schematic header and the reference from the property.
"""
import re

SCH = "aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, "r") as f:
    content = f.read()

# 1. Get the project UUID from the schematic header
# Format: (kicad_sch ... (uuid "PROJECT_UUID"))
# The project path UUID is the root sheet UUID
# Let's find it from a working symbol's instances section
project_uuid_m = re.search(
    r'\(instances\s+\(project\s+"aurora-dsp-icepower-booster"\s+\(path\s+"/([^"]+)"',
    content
)
if not project_uuid_m:
    print("ERROR: Could not find project UUID from existing instances")
    exit(1)

project_uuid = project_uuid_m.group(1)
print(f"Project UUID: {project_uuid}")

# 2. Skip lib_symbols section
lib_start = content.find('(lib_symbols')
depth = 0
lib_end = lib_start
for i in range(lib_start, len(content)):
    if content[i] == '(':
        depth += 1
    elif content[i] == ')':
        depth -= 1
        if depth == 0:
            lib_end = i + 1
            break

# 3. Find the 6 GND symbols without instances
def extract_balanced(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
    return None, start

gnd_pattern = re.compile(r'\(symbol\s+\(lib_id\s+"power:GND"\)')
fixes = []  # (start, end, old_block, new_block)

for m in gnd_pattern.finditer(content):
    if lib_start <= m.start() < lib_end:
        continue
    
    block, block_end = extract_balanced(content, m.start())
    if not block:
        continue
    
    # Check if instances section exists
    if '(instances' in block:
        continue
    
    # Get position
    at_m = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)', block)
    pos = (float(at_m.group(1)), float(at_m.group(2))) if at_m else None
    
    # Get reference from property
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    ref = ref_m.group(1) if ref_m else None
    
    if not ref:
        print(f"WARNING: No reference found for GND at {pos}")
        continue
    
    # Build the instances section
    instances_str = (
        f'\n    (instances\n'
        f'      (project "aurora-dsp-icepower-booster"\n'
        f'  (path "/{project_uuid}" (reference "{ref}") (unit 1))\n'
        f'))'
    )
    
    # Insert instances section before the closing parenthesis of the symbol
    # Find the last ')' in the block — it's the symbol's closing paren
    # We insert BEFORE it
    # Find the last pin entry to insert after it
    last_pin_end = block.rfind(')')  # The very last ) closes the symbol
    
    # Actually, we need to insert before the final closing paren
    # The block ends with ')' - we insert the instances section before it
    new_block = block[:-1] + instances_str + '\n)'
    
    fixes.append((m.start(), block_end, block, new_block, ref, pos))
    print(f"Will fix: {ref} at {pos}")

if not fixes:
    print("No fixes needed!")
    exit(0)

print(f"\nApplying {len(fixes)} fixes...")

# Apply fixes in reverse order (to preserve offsets)
fixes.sort(key=lambda x: x[0], reverse=True)
new_content = content
for start, end, old_block, new_block, ref, pos in fixes:
    new_content = new_content[:start] + new_block + new_content[end:]
    print(f"  Fixed: {ref} at {pos}")

# 4. Bracket balance check
depth = 0
for ch in new_content:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket balance FAILED: {depth}"
print(f"\nBracket balance: OK (depth=0)")

# 5. Write
with open(SCH, 'w') as f:
    f.write(new_content)
print(f"Wrote {SCH}")

# 6. Verify: check all GND symbols now have instances
with open(SCH, 'r') as f:
    verify = f.read()

# Re-find lib_symbols
lib_start2 = verify.find('(lib_symbols')
depth2 = 0
lib_end2 = lib_start2
for i in range(lib_start2, len(verify)):
    if verify[i] == '(':
        depth2 += 1
    elif verify[i] == ')':
        depth2 -= 1
        if depth2 == 0:
            lib_end2 = i + 1
            break

missing = 0
for m in gnd_pattern.finditer(verify):
    if lib_start2 <= m.start() < lib_end2:
        continue
    block, _ = extract_balanced(verify, m.start())
    if block and '(instances' not in block:
        at_m = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)', block)
        pos = f"({at_m.group(1)}, {at_m.group(2)})" if at_m else "unknown"
        print(f"  STILL MISSING instances: GND at {pos}")
        missing += 1

print(f"\nVerification: {missing} GND symbols still missing instances")
if missing == 0:
    print("ALL GND symbols have instances sections!")
