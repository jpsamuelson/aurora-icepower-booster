#!/usr/bin/env python3
"""Zone Refill via pcbnew Python API + text-merge back to original.

Steps:
1. Copy PCB to temp
2. Use pcbnew to fill zones on temp
3. Save to temp2 (pcbnew corrupts KiCad 9 format)
4. Extract filled_polygon blocks from temp2
5. Merge them into original PCB by matching zone UUIDs
"""
import subprocess
import re
import shutil
import os
import sys

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"
TEMP_PCB = "/tmp/aurora_zone_fill.kicad_pcb"
TEMP_FILLED = "/tmp/aurora_zone_filled.kicad_pcb"

# Step 1: Copy PCB
shutil.copy2(PCB, TEMP_PCB)
print("Step 1: Copied PCB to temp")

# Step 2 & 3: Fill zones via pcbnew Python script
fill_script = """
import pcbnew
import sys

board = pcbnew.LoadBoard("{temp}")
zones = board.Zones()
print(f"Found {{len(zones)}} zones")

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(zones)
print("Zone fill completed")

pcbnew.SaveBoard("{filled}", board)
print(f"Saved to {{'{filled}'}}")
""".format(temp=TEMP_PCB, filled=TEMP_FILLED)

fill_script_path = "/tmp/zone_fill_script.py"
with open(fill_script_path, 'w') as f:
    f.write(fill_script)

# Find pcbnew Python - it's usually in KiCad's Python framework
python_paths = [
    "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3",
    "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3",
]

# Also try finding via kicad-cli's bundled python
kicad_python = None
for p in python_paths:
    if os.path.exists(p):
        kicad_python = p
        break

if not kicad_python:
    # Try to find it
    result = subprocess.run(
        ["find", "/Applications/KiCad/KiCad.app", "-name", "python3", "-type", "f"],
        capture_output=True, text=True, timeout=10
    )
    paths = result.stdout.strip().split('\n')
    for p in paths:
        if p and os.path.exists(p):
            kicad_python = p
            break

if not kicad_python:
    print("ERROR: Could not find KiCad's Python!")
    print("Trying system python with pcbnew...")
    kicad_python = "python3"

print(f"Step 2: Using Python: {kicad_python}")

# Set PYTHONPATH to include pcbnew
env = os.environ.copy()
env["PYTHONPATH"] = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages"

result = subprocess.run(
    [kicad_python, fill_script_path],
    capture_output=True, text=True, timeout=120,
    env=env
)

print(f"stdout: {result.stdout}")
if result.stderr:
    print(f"stderr: {result.stderr[:500]}")
if result.returncode != 0:
    print(f"Zone fill failed with code {result.returncode}")
    # Try alternative approach
    print("\nTrying with system python and pcbnew import...")
    result2 = subprocess.run(
        ["python3", fill_script_path],
        capture_output=True, text=True, timeout=120
    )
    print(f"stdout: {result2.stdout}")
    if result2.stderr:
        print(f"stderr: {result2.stderr[:500]}")
    if result2.returncode != 0:
        print("Zone fill failed! User must do zone refill in KiCad (B key)")
        sys.exit(1)

if not os.path.exists(TEMP_FILLED):
    print("ERROR: Filled PCB file not created!")
    sys.exit(1)

print("Step 3: Zone fill completed")

# Step 4: Extract filled_polygon blocks from filled PCB
print("Step 4: Extracting filled polygons...")

with open(TEMP_FILLED) as f:
    filled_content = f.read()
with open(PCB) as f:
    orig_content = f.read()

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

def extract_zones_with_fills(text):
    """Extract zone UUIDs and their filled_polygon blocks."""
    zones = {}
    for m in re.finditer(r'\(zone\b', text):
        block, end = extract_block(text, m.start())
        if not block:
            continue
        
        uuid_match = re.search(r'\(uuid\s+"([^"]+)"\)', block)
        if not uuid_match:
            continue
        uuid = uuid_match.group(1)
        
        # Extract all filled_polygon blocks within this zone
        fills = []
        for fm in re.finditer(r'\(filled_polygon\b', block):
            fill_block, _ = extract_block(block, fm.start())
            if fill_block:
                fills.append(fill_block)
        
        zones[uuid] = {
            'fills': fills,
            'start': m.start(),
            'end': end,
            'block': block
        }
    return zones

filled_zones = extract_zones_with_fills(filled_content)
orig_zones = extract_zones_with_fills(orig_content)

print(f"  Filled PCB: {len(filled_zones)} zones")
print(f"  Original PCB: {len(orig_zones)} zones")

# Step 5: Merge filled polygons into original
print("Step 5: Merging filled polygons...")

merged = 0
new_content = orig_content

for uuid in orig_zones:
    if uuid not in filled_zones:
        print(f"  Zone {uuid[:8]}... not in filled version")
        continue
    
    orig_zone = orig_zones[uuid]
    filled_zone = filled_zones[uuid]
    
    if not filled_zone['fills']:
        print(f"  Zone {uuid[:8]}... has no fills in filled version")
        continue
    
    # Replace the zone block in the original:
    # Remove existing filled_polygon blocks and add new ones
    orig_block = orig_zone['block']
    
    # Remove existing filled_polygon blocks from orig_block
    cleaned = orig_block
    while True:
        fp_match = re.search(r'\(filled_polygon\b', cleaned)
        if not fp_match:
            break
        fp_block, fp_end = extract_block(cleaned, fp_match.start())
        if fp_block:
            # Also remove trailing whitespace
            end = fp_end
            while end < len(cleaned) and cleaned[end] in ' \t\n':
                end += 1
            cleaned = cleaned[:fp_match.start()] + cleaned[end:]
        else:
            break
    
    # Add new filled_polygon blocks before the closing ) of the zone
    last_paren = cleaned.rfind(')')
    insert_text = ""
    for fill in filled_zone['fills']:
        insert_text += "\n\t\t" + fill
    
    new_block = cleaned[:last_paren] + insert_text + "\n\t" + cleaned[last_paren:]
    
    # Replace in content
    idx = new_content.find(orig_block)
    if idx >= 0:
        new_content = new_content[:idx] + new_block + new_content[idx+len(orig_block):]
        merged += 1
        print(f"  Zone {uuid[:8]}... merged {len(filled_zone['fills'])} fill polygons")
    else:
        print(f"  Zone {uuid[:8]}... NOT FOUND in content (offset shift?)")

print(f"\nMerged {merged} zones")

# Balance check
depth = 0
for ch in new_content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
print(f"Bracket balance: {depth}")

if depth != 0:
    print("ERROR: Bracket imbalance! Not writing.")
    sys.exit(1)

with open(PCB, 'w') as f:
    f.write(new_content)
print("Written to PCB.")
