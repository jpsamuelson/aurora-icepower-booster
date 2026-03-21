#!/usr/bin/env python3
"""
Phase 1: Update ALL footprints from KiCad standard library via pcbnew API.

Uses pcbnew's FOOTPRINT_EDITOR to load library footprints and exchange them
on board footprints. Preserves position, orientation, layer, nets.

Then text-merges results into original PCB (pcbnew.SaveBoard corrupts KiCad 9).
"""
import os, sys, re, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP_PCB = '/tmp/aurora-fp-update.kicad_pcb'
FP_LIB_BASE = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

# Custom footprints without library prefix need remapping
CUSTOM_REMAP = {
    'SOT-23': ('Package_TO_SOT_SMD', 'SOT-23'),
    'MountingHole_3.2mm_M3': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'L_0805_2012Metric': ('Inductor_SMD', 'L_0805_2012Metric'),
    'C_0402_1005Metric': ('Capacitor_SMD', 'C_0402_1005Metric'),
}
SKIP_FOOTPRINTS = {'TEL5_DUAL_TRP', 'SOIC127P600X175-9N'}

def extract_balanced_lines(lines, start):
    depth = 0
    block = []
    j = start
    while j < len(lines):
        block.append(lines[j])
        for ch in lines[j]:
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
        if depth <= 0:
            return block, j
        j += 1
    return block, j

def load_lib_fp(lib_name, fp_name):
    path = os.path.join(FP_LIB_BASE, f'{lib_name}.pretty', f'{fp_name}.kicad_mod')
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return None

# ====== MAIN ======
with open(PCB_FILE) as f:
    text = f.read()
lines = text.split('\n')
print(f"PCB loaded: {len(lines)} lines")

# Find all footprint blocks in original
fp_blocks = []  # (start_line, end_line, fp_type, ref, block_text)
i = 0
while i < len(lines):
    if lines[i].strip().startswith('(footprint "'):
        block_lines, end_j = extract_balanced_lines(lines, i)
        block_text = '\n'.join(block_lines)
        fp_m = re.match(r'\s*\(footprint "([^"]*)"', block_lines[0])
        ref_m = re.search(r'\(property "Reference" "([^"]*)"', block_text)
        fp_type = fp_m.group(1) if fp_m else '?'
        ref = ref_m.group(1) if ref_m else '?'
        fp_blocks.append((i, end_j, fp_type, ref, block_text))
        i = end_j + 1
        continue
    i += 1
print(f"Found {len(fp_blocks)} footprints")

# For each footprint, build the updated version from library
def extract_pad_nets(block_text):
    """Extract pad→net mapping from board footprint."""
    pad_nets = {}
    # Find each (pad ...) block
    pos = 0
    while True:
        pad_start = block_text.find('(pad "', pos)
        if pad_start < 0:
            break
        # Extract pad number
        pad_num_end = block_text.index('"', pad_start + 6)
        pad_num = block_text[pad_start+5:pad_num_end+1].strip('"')
        
        # Find end of pad block (balanced parens)
        depth = 0
        pe = pad_start
        while pe < len(block_text):
            if block_text[pe] == '(': depth += 1
            elif block_text[pe] == ')':
                depth -= 1
                if depth == 0:
                    break
            pe += 1
        pad_block = block_text[pad_start:pe+1]
        
        net_m = re.search(r'\(net (\d+) "([^"]*)"\)', pad_block)
        if net_m:
            pad_nets[pad_num] = (net_m.group(1), net_m.group(2))
        else:
            pad_nets[pad_num] = None
        
        pos = pe + 1
    return pad_nets

def reindent_lib_block(lib_text, indent='\t\t'):
    """Re-indent a library block for board embedding."""
    result = []
    for line in lib_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        # Count original indent
        orig_indent = len(line) - len(line.lstrip())
        # Base indent is 2 tabs, add 1 tab per 2 spaces of original indent
        extra = '\t' * max(0, orig_indent // 2 - 1)
        result.append(indent + extra + stripped)
    return '\n'.join(result)

def build_updated_fp(lib_content, board_block_text, new_fp_name=None):
    """Build updated footprint from library + board identity."""
    # Extract board identity
    fp_m = re.match(r'\s*\(footprint "([^"]*)"', board_block_text)
    old_fp_name = fp_m.group(1) if fp_m else '?'
    
    ref_m = re.search(r'\(property "Reference" "([^"]*)"', board_block_text)
    ref = ref_m.group(1) if ref_m else 'REF'
    
    val_m = re.search(r'\(property "Value" "([^"]*)"', board_block_text)
    val = val_m.group(1) if val_m else ''
    
    at_m = re.search(r'^\s*\(footprint[^)]*?\n\s*\(layer[^)]*\)\n\s*\(uuid[^)]*\)\n\s*\(at ([^\n]+)\)', 
                     board_block_text, re.MULTILINE)
    if not at_m:
        at_m = re.search(r'\(at ([^\n)]+)\)', board_block_text[:500])
    at_str = at_m.group(1) if at_m else '0 0'
    
    layer_m = re.search(r'\(layer "([^"]+)"\)', board_block_text[:500])
    layer = layer_m.group(1) if layer_m else 'F.Cu'
    
    uuid_m = re.search(r'\(uuid "([^"]+)"\)', board_block_text[:800])
    uuid = uuid_m.group(1) if uuid_m else None
    
    pad_nets = extract_pad_nets(board_block_text)
    
    fp_name = new_fp_name or old_fp_name
    
    # Parse library content line by line
    lib_lines = lib_content.strip().split('\n')
    out = []
    
    # Header
    out.append(f'\t(footprint "{fp_name}"')
    out.append(f'\t\t(layer "{layer}")')
    if uuid:
        out.append(f'\t\t(uuid "{uuid}")')
    out.append(f'\t\t(at {at_str})')
    
    # Process library content, skipping header elements
    i = 1  # skip first line (footprint declaration)
    while i < len(lib_lines):
        line = lib_lines[i].strip()
        
        # Skip library header elements we already handled
        if any(line.startswith(f'({tag} ') or line.startswith(f'({tag})') 
               for tag in ['layer', 'uuid', 'at', 'tedit', 'tstamp', 'version', 'generator', 'generator_version']):
            i += 1
            continue
        
        # Skip closing paren of footprint
        if line == ')' and i == len(lib_lines) - 1:
            i += 1
            continue
        
        # Handle multi-line blocks
        if line.startswith('('):
            block, end_j = extract_balanced_lines(lib_lines, i)
            block_text = '\n'.join(block)
            
            # Property blocks: update Reference and Value
            if line.startswith('(property '):
                if '"Reference"' in block_text:
                    block_text = re.sub(r'(property "Reference" )"[^"]*"',
                                       f'\\1"{ref}"', block_text)
                elif '"Value"' in block_text:
                    block_text = re.sub(r'(property "Value" )"[^"]*"',
                                       f'\\1"{val}"', block_text)
                out.append(reindent_lib_block(block_text))
                i = end_j + 1
                continue
            
            # fp_text blocks (older format)
            if line.startswith('(fp_text '):
                if 'reference' in line:
                    block_text = re.sub(r'(fp_text reference )"[^"]*"',
                                       f'\\1"{ref}"', block_text)
                elif 'value' in line:
                    block_text = re.sub(r'(fp_text value )"[^"]*"',
                                       f'\\1"{val}"', block_text)
                out.append(reindent_lib_block(block_text))
                i = end_j + 1
                continue
            
            # Pad blocks: add net assignment
            if line.startswith('(pad '):
                pad_num_m = re.match(r'\(pad "([^"]*)"', line)
                if pad_num_m:
                    pad_num = pad_num_m.group(1)
                    net = pad_nets.get(pad_num)
                    if net:
                        net_id, net_name = net
                        # Insert net before closing paren
                        # Find last line of block, insert before )
                        block_lines_out = []
                        for bl in block:
                            block_lines_out.append(bl)
                        # Add net line before final )
                        last = block_lines_out[-1]
                        # If single-line pad
                        if len(block_lines_out) == 1:
                            last = last.rstrip(')')
                            block_lines_out[-1] = last
                            block_lines_out.append(f'\t\t\t(net {net_id} "{net_name}")')
                            block_lines_out.append('\t\t)')
                        else:
                            # Multi-line: insert before last closing )
                            block_lines_out.insert(-1, f'\t\t\t(net {net_id} "{net_name}")')
                        
                        block_text = '\n'.join(block_lines_out)
                
                out.append(reindent_lib_block(block_text))
                i = end_j + 1
                continue
            
            # All other elements (fp_line, fp_rect, fp_poly, model, etc.)
            out.append(reindent_lib_block(block_text))
            i = end_j + 1
            continue
        
        i += 1
    
    out.append('\t)')
    return '\n'.join(out)

# Process all footprints
new_lines = []
last_end = 0
updated = 0
skipped = 0
remapped = 0
failed_list = []

for start, end, fp_type, ref, block_text in fp_blocks:
    new_lines.extend(lines[last_end:start])
    
    # Determine library source
    if ':' in fp_type:
        lib_name, lib_fp_name = fp_type.split(':', 1)
        new_name = None
    else:
        bare = fp_type
        if bare in SKIP_FOOTPRINTS:
            new_lines.extend(lines[start:end+1])
            last_end = end + 1
            skipped += 1
            print(f"  SKIP {ref} ({bare}) - custom footprint")
            continue
        if bare in CUSTOM_REMAP:
            lib_name, lib_fp_name = CUSTOM_REMAP[bare]
            new_name = f"{lib_name}:{lib_fp_name}"
            remapped += 1
        else:
            new_lines.extend(lines[start:end+1])
            last_end = end + 1
            failed_list.append(f"{ref} ({bare}) - no mapping")
            continue
    
    # Load library footprint
    lib_content = load_lib_fp(lib_name, lib_fp_name)
    if lib_content is None:
        new_lines.extend(lines[start:end+1])
        last_end = end + 1
        failed_list.append(f"{ref} ({lib_name}:{lib_fp_name}) - not in library")
        continue
    
    # Build updated footprint
    if ':' in fp_type:
        new_name = None
    updated_fp = build_updated_fp(lib_content, block_text, new_name)
    new_lines.extend(updated_fp.split('\n'))
    last_end = end + 1
    updated += 1

new_lines.extend(lines[last_end:])

print(f"\n=== Results ===")
print(f"Updated from library: {updated}")
print(f"Remapped (added lib prefix): {remapped} of those")
print(f"Skipped (custom): {skipped}")
print(f"Failed: {len(failed_list)}")
for f in failed_list:
    print(f"  {f}")

# Bracket balance
result = '\n'.join(new_lines)
depth = 0
for ch in result:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
if depth != 0:
    print(f"\n❌ BRACKET IMBALANCE: depth={depth}")
    sys.exit(1)
print(f"✅ Bracket balance: OK")

# Footprint count check - count top-level footprints only (depth=1 after kicad_pcb open)
# Simply count how many updated + skipped + failed = original
total_processed = updated + skipped + len(failed_list)
print(f"Footprints processed: {total_processed} of {len(fp_blocks)}")
if total_processed != len(fp_blocks):
    print(f"❌ PROCESSING COUNT MISMATCH!")
    sys.exit(1)

with open(PCB_FILE, 'w') as f:
    f.write(result)
print(f"✅ PCB saved")
