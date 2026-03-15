#!/usr/bin/env python3
"""
Replicate Channel 1 schematic for Channels 2-6.

This script:
1. Reads the KiCad schematic file
2. Extracts all Channel 1 components, labels, and wires
3. Creates copies for channels 2-6 with offset positions,
   updated reference designators, and updated net names
4. Writes out the updated schematic
"""
import re
import uuid
import shutil
import sys
import os

SCH_FILE = "aurora-dsp-icepower-booster.kicad_sch"
BACKUP_FILE = SCH_FILE + ".bak5"
Y_OFFSET_PER_CHANNEL = 80  # mm between channel centers

# Reference designator mapping: Ch1 ref -> [Ch2, Ch3, Ch4, Ch5, Ch6]
REF_MAP = {
    'J1':  ['J2',  'J3',  'J4',  'J5',  'J6'],
    'U1':  ['U2',  'U3',  'U4',  'U5',  'U6'],
    'R1':  ['R14', 'R27', 'R40', 'R53', 'R66'],
    'R2':  ['R15', 'R28', 'R41', 'R54', 'R67'],
    'R3':  ['R16', 'R29', 'R42', 'R55', 'R68'],
    'R4':  ['R17', 'R30', 'R43', 'R56', 'R69'],
    'C1':  ['C5',  'C9',  'C13', 'C17', 'C21'],
    'C2':  ['C6',  'C10', 'C14', 'C18', 'C22'],
    'R5':  ['R18', 'R31', 'R44', 'R57', 'R70'],
    'R6':  ['R19', 'R32', 'R45', 'R58', 'R71'],
    'R7':  ['R20', 'R33', 'R46', 'R59', 'R72'],
    'R8':  ['R21', 'R34', 'R47', 'R60', 'R73'],
    'R9':  ['R22', 'R35', 'R48', 'R61', 'R74'],
    'SW1': ['SW2', 'SW3', 'SW4', 'SW5', 'SW6'],
    'U7':  ['U8',  'U9',  'U10', 'U11', 'U12'],
    'R10': ['R23', 'R36', 'R49', 'R62', 'R75'],
    'R11': ['R24', 'R37', 'R50', 'R63', 'R76'],
    'R12': ['R25', 'R38', 'R51', 'R64', 'R77'],
    'R13': ['R26', 'R39', 'R52', 'R65', 'R78'],
    'C3':  ['C7',  'C11', 'C15', 'C19', 'C23'],
    'C4':  ['C8',  'C12', 'C16', 'C20', 'C24'],
    'J7':  ['J8',  'J9',  'J10', 'J11', 'J12'],
}

# Value labels per channel for DIP switch
VALUE_MAP = {
    'Gain CH1': ['Gain CH2', 'Gain CH3', 'Gain CH4', 'Gain CH5', 'Gain CH6'],
    'XLR_IN_1': ['XLR_IN_2', 'XLR_IN_3', 'XLR_IN_4', 'XLR_IN_5', 'XLR_IN_6'],
    'XLR3_OUT': ['XLR3_OUT', 'XLR3_OUT', 'XLR3_OUT', 'XLR3_OUT', 'XLR3_OUT'],
}

# Channel 1 component refs (all instances)
CH1_REFS = set(REF_MAP.keys())


def find_block_end(data, start):
    """Find the matching closing paren for the opening paren at start."""
    depth = 0
    i = start
    while i < len(data):
        if data[i] == '(':
            depth += 1
        elif data[i] == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def new_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def replace_uuids(block):
    """Replace all UUIDs in a block with new ones."""
    return re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        lambda m: new_uuid(),
        block
    )


def offset_y_in_block(block, dy):
    """Offset all Y coordinates in (at X Y ...) and (xy X Y) patterns."""
    def offset_at(m):
        x = m.group(1)
        y = float(m.group(2))
        rest = m.group(3)
        return f'(at {x} {y + dy:.2f}{rest})'

    def offset_xy(m):
        x = m.group(1)
        y = float(m.group(2))
        return f'(xy {x} {y + dy:.2f})'

    block = re.sub(r'\(at ([\d.\-]+) ([\d.\-]+)([ \d.\-]*)\)', offset_at, block)
    block = re.sub(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', offset_xy, block)
    return block


def rename_ref_in_block(block, old_ref, new_ref):
    """Replace reference designator in a symbol block."""
    # Replace in (property "Reference" "REF" ...)
    block = block.replace(
        f'(property "Reference" "{old_ref}"',
        f'(property "Reference" "{new_ref}"'
    )
    return block


def rename_net_in_label(block, ch_num):
    """Replace CH1_ with CH{N}_ in label blocks."""
    return block.replace('CH1_', f'CH{ch_num}_')


def rename_value_in_block(block, ch_idx):
    """Update value properties for channel-specific values."""
    for old_val, new_vals in VALUE_MAP.items():
        if old_val in block:
            block = block.replace(
                f'(property "Value" "{old_val}"',
                f'(property "Value" "{new_vals[ch_idx]}"'
            )
    return block


def extract_blocks(data, start_offset, pattern):
    """Extract all S-expression blocks matching a pattern after start_offset."""
    blocks = []
    pos = start_offset
    while True:
        idx = data.find(pattern, pos)
        if idx == -1:
            break
        end = find_block_end(data, idx)
        if end == -1:
            break
        blocks.append({
            'start': idx,
            'end': end + 1,
            'text': data[idx:end+1]
        })
        pos = idx + 1
    return blocks


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Read schematic
    data = open(SCH_FILE).read()
    print(f"Read {len(data)} bytes from {SCH_FILE}")
    
    # Backup
    shutil.copy2(SCH_FILE, BACKUP_FILE)
    print(f"Backup saved to {BACKUP_FILE}")
    
    # Find end of lib_symbols
    lib_start = data.find('(lib_symbols')
    lib_end = find_block_end(data, lib_start) + 1
    print(f"lib_symbols section: {lib_start}..{lib_end}")
    
    # Extract all placed symbols
    symbols = extract_blocks(data, lib_end, '(symbol (lib_id')
    print(f"Found {len(symbols)} placed symbol instances")
    
    # Identify Channel 1 symbols
    ch1_symbols = []
    for s in symbols:
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', s['text'])
        if ref_m and ref_m.group(1) in CH1_REFS:
            s['ref'] = ref_m.group(1)
            ch1_symbols.append(s)
    
    print(f"Channel 1 symbols: {len(ch1_symbols)}")
    for s in ch1_symbols:
        print(f"  {s['ref']}")
    
    # Extract all labels after lib_symbols
    labels = extract_blocks(data, lib_end, '(label "')
    print(f"Found {len(labels)} labels total")
    
    # Identify Channel 1 labels (CH1_* and power labels in Ch1 Y range)
    # Ch1 Y range: ~85-170
    ch1_min_y = 80
    ch1_max_y = 175
    ch1_min_x = 20
    ch1_max_x = 265
    
    ch1_labels = []
    for l in labels:
        name_m = re.search(r'\(label "([^"]+)"', l['text'])
        at_m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)', l['text'])
        if name_m and at_m:
            name = name_m.group(1)
            x, y = float(at_m.group(1)), float(at_m.group(2))
            l['name'] = name
            l['x'] = x
            l['y'] = y
            
            # Include if it's a CH1_ label OR a power label in Ch1 area
            if name.startswith('CH1_'):
                ch1_labels.append(l)
            elif name in ('V+', 'V-', 'GND') and ch1_min_y <= y <= ch1_max_y and ch1_min_x <= x <= ch1_max_x:
                ch1_labels.append(l)
    
    print(f"Channel 1 labels: {len(ch1_labels)}")
    
    # Extract all wires after lib_symbols
    wires = extract_blocks(data, lib_end, '(wire (pts')
    print(f"Found {len(wires)} wires total")
    
    # Identify Channel 1 wires (in Ch1 Y range)
    ch1_wires = []
    for w in wires:
        pts = re.findall(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', w['text'])
        if len(pts) >= 2:
            y1, y2 = float(pts[0][1]), float(pts[1][1])
            x1, x2 = float(pts[0][0]), float(pts[1][0])
            # Include wire if both endpoints are in Ch1 area
            if (ch1_min_y <= y1 <= ch1_max_y and ch1_min_x <= x1 <= ch1_max_x and
                ch1_min_y <= y2 <= ch1_max_y and ch1_min_x <= x2 <= ch1_max_x):
                ch1_wires.append(w)
    
    print(f"Channel 1 wires: {len(ch1_wires)}")
    
    # Also check for junctions in Ch1 area
    junctions = extract_blocks(data, lib_end, '(junction (at')
    ch1_junctions = []
    for j in junctions:
        at_m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', j['text'])
        if at_m:
            x, y = float(at_m.group(1)), float(at_m.group(2))
            if ch1_min_y <= y <= ch1_max_y and ch1_min_x <= x <= ch1_max_x:
                ch1_junctions.append(j)
    
    print(f"Channel 1 junctions: {len(ch1_junctions)}")
    
    # Also check for no_connect flags in Ch1 area
    no_connects = extract_blocks(data, lib_end, '(no_connect (at')
    ch1_no_connects = []
    for nc in no_connects:
        at_m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', nc['text'])
        if at_m:
            x, y = float(at_m.group(1)), float(at_m.group(2))
            if ch1_min_y <= y <= ch1_max_y and ch1_min_x <= x <= ch1_max_x:
                ch1_no_connects.append(nc)
    
    print(f"Channel 1 no_connects: {len(ch1_no_connects)}")
    
    # Generate new blocks for channels 2-6
    new_blocks = []
    
    for ch_idx in range(5):  # 0=Ch2, 1=Ch3, 2=Ch4, 3=Ch5, 4=Ch6
        ch_num = ch_idx + 2
        dy = (ch_idx + 1) * Y_OFFSET_PER_CHANNEL
        
        print(f"\n--- Generating Channel {ch_num} (Y offset = +{dy}mm) ---")
        
        # Clone symbols
        for s in ch1_symbols:
            block = s['text']
            new_ref = REF_MAP[s['ref']][ch_idx]
            
            # Replace reference
            block = rename_ref_in_block(block, s['ref'], new_ref)
            
            # Replace channel-specific values
            block = rename_value_in_block(block, ch_idx)
            
            # Replace UUIDs
            block = replace_uuids(block)
            
            # Offset Y coordinates
            block = offset_y_in_block(block, dy)
            
            new_blocks.append(block)
            print(f"  Symbol: {s['ref']} -> {new_ref}")
        
        # Clone labels
        for l in ch1_labels:
            block = l['text']
            
            # Rename CH1_ to CH{N}_
            if l['name'].startswith('CH1_'):
                block = rename_net_in_label(block, ch_num)
            
            # Replace UUIDs
            block = replace_uuids(block)
            
            # Offset Y
            block = offset_y_in_block(block, dy)
            
            new_blocks.append(block)
        
        print(f"  Labels: {len(ch1_labels)}")
        
        # Clone wires
        for w in ch1_wires:
            block = w['text']
            block = replace_uuids(block)
            block = offset_y_in_block(block, dy)
            new_blocks.append(block)
        
        print(f"  Wires: {len(ch1_wires)}")
        
        # Clone junctions
        for j in ch1_junctions:
            block = j['text']
            block = replace_uuids(block)
            block = offset_y_in_block(block, dy)
            new_blocks.append(block)
        
        print(f"  Junctions: {len(ch1_junctions)}")
        
        # Clone no_connects
        for nc in ch1_no_connects:
            block = nc['text']
            block = replace_uuids(block)
            block = offset_y_in_block(block, dy)
            new_blocks.append(block)
        
        print(f"  No_connects: {len(ch1_no_connects)}")
    
    print(f"\nTotal new blocks to insert: {len(new_blocks)}")
    
    # Find insertion point: just before the final closing paren of the schematic
    # The schematic ends with ... (symbol_instances ...) )
    # We want to insert new symbols/labels/wires before symbol_instances
    
    # Find symbol_instances section
    si_start = data.find('(symbol_instances')
    if si_start == -1:
        # No symbol_instances yet — insert before final )
        insert_pos = data.rfind(')')
    else:
        insert_pos = si_start
    
    print(f"Inserting at position {insert_pos}")
    
    # Build the insertion text
    insert_text = ' '.join(new_blocks)
    
    # Also need to update symbol_instances with new entries
    # Extract existing symbol_instances for Ch1 components to replicate
    si_entries = []
    if si_start != -1:
        si_end = find_block_end(data, si_start)
        si_block = data[si_start:si_end+1]
        
        # Find all (path "/UUID" (reference "REF") (unit N)) entries
        path_pattern = r'\(path "(/[^"]+)" \(reference "([^"]+)"\) \(unit (\d+)\)\)'
        for m in re.finditer(path_pattern, si_block):
            path, ref, unit = m.group(1), m.group(2), int(m.group(3))
            si_entries.append({'path': path, 'ref': ref, 'unit': unit, 'text': m.group(0)})
        
        print(f"Found {len(si_entries)} symbol_instance entries")
        
        # For each Ch1 component, create new entries for Ch2-6
        new_si_entries = []
        for entry in si_entries:
            if entry['ref'] in CH1_REFS:
                for ch_idx in range(5):
                    new_ref = REF_MAP[entry['ref']][ch_idx]
                    new_path = f"/{new_uuid()}"
                    new_entry = f'(path "{new_path}" (reference "{new_ref}") (unit {entry["unit"]}))'
                    new_si_entries.append(new_entry)
        
        print(f"New symbol_instance entries: {len(new_si_entries)}")
        
        # Insert new si entries before closing of symbol_instances
        si_close = data.rfind(')', si_start, si_end+1)
        new_si_text = ' '.join(new_si_entries) + ' '
        
        # Reconstruct data
        new_data = (
            data[:insert_pos] +
            insert_text + ' ' +
            data[insert_pos:si_close] +
            ' ' + new_si_text +
            data[si_close:]
        )
    else:
        # No symbol_instances — just insert blocks
        new_data = data[:insert_pos] + insert_text + ' ' + data[insert_pos:]
    
    # Update paper size to fit (A1 = 841 x 594mm)
    new_data = new_data.replace('(paper "A4")', '(paper "A1")')
    
    # Write output
    with open(SCH_FILE, 'w') as f:
        f.write(new_data)
    
    print(f"\nWritten {len(new_data)} bytes to {SCH_FILE}")
    print(f"Paper size changed to A1")
    print("Done! Open in KiCad to verify.")


if __name__ == "__main__":
    main()
