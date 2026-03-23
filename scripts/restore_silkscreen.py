#!/usr/bin/env python3
"""Restore user's silkscreen changes from stash into current HEAD PCB.

Changes to apply:
1. Add Gain table (new gr_text from stash)
2. Add Switch description (new gr_text from stash)
3. Move "Balanced Booster" to user's position (24.892, 197.866)
4. Remove "Rev 1.0" gr_text (B.SilkS) — user removed it
5. Remove "Aurora DSP IcePower Booster" gr_text (B.SilkS) — user removed it
6. Move SW2 Reference label to user's position (-6.994, -4.066)
"""
import re
import sys

STASH_PCB = "/tmp/pcb_stash.kicad_pcb"
HEAD_PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

def extract_block(text, start):
    """Extract balanced parenthesized block starting at 'start'."""
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

# Read both files
with open(STASH_PCB) as f:
    stash = f.read()
with open(HEAD_PCB) as f:
    head = f.read()

# =====================================================
# Step 1 & 2: Extract Gain table and Switch desc from stash
# =====================================================
stash_new_blocks = []
for m in re.finditer(r'\(gr_text\b', stash):
    block, end = extract_block(stash, m.start())
    if block and 'GAIN (dB)' in block:
        stash_new_blocks.append(('Gain table', block))
        print(f"Found Gain table block ({len(block)} chars)")
    elif block and 'ON ↑' in block:
        stash_new_blocks.append(('Switch desc', block))
        print(f"Found Switch description block ({len(block)} chars)")

# =====================================================
# Step 3: Move "Balanced Booster" to user's position
# =====================================================
balanced_changed = False
for m in re.finditer(r'\(gr_text\b', head):
    block, end = extract_block(head, m.start())
    if block and 'Balanced Booster' in block:
        # Replace position (3.556, 19.812) → (24.892, 197.866)
        old_at = re.search(r'\(at\s+3\.556\s+19\.812', block)
        if old_at:
            new_block = block.replace('(at 3.556 19.812', '(at 24.892 197.866')
            head = head[:m.start()] + new_block + head[end:]
            balanced_changed = True
            print(f"Moved 'Balanced Booster' to (24.892, 197.866)")
        break

# =====================================================
# Step 4 & 5: Remove "Rev 1.0" and "Aurora DSP IcePower Booster"
# =====================================================
removals = []
for m in re.finditer(r'\(gr_text\b', head):
    block, end = extract_block(head, m.start())
    if block and 'Rev 1.0' in block and 'B.SilkS' in block:
        removals.append((m.start(), end, 'Rev 1.0'))
    elif block and 'Aurora DSP IcePower Booster' in block and 'B.SilkS' in block:
        removals.append((m.start(), end, 'Aurora DSP IcePower Booster'))

# Remove in reverse order
for start, end, name in sorted(removals, key=lambda r: r[0], reverse=True):
    # Also remove trailing whitespace
    while end < len(head) and head[end] in ' \t\n':
        end += 1
    head = head[:start] + head[end:]
    print(f"Removed '{name}' from B.SilkS")

# =====================================================
# Step 6: Move SW2 Reference to user's position
# =====================================================
# Find SW2 footprint and modify its Reference property position
sw2_match = re.search(r'\(footprint\b[^)]*\n[^)]*"Reference"\s+"SW2"', head)
if not sw2_match:
    # Try broader search
    sw2_start = head.find('"Reference" "SW2"')
    if sw2_start >= 0:
        # Find the (property "Reference" "SW2" ...) block
        # Go back to find (property
        prop_start = head.rfind('(property', 0, sw2_start)
        if prop_start >= 0:
            prop_block, prop_end = extract_block(head, prop_start)
            if prop_block:
                # Replace position
                old_at = re.search(r'\(at\s+[\d.-]+\s+[\d.-]+', prop_block)
                if old_at:
                    new_prop = re.sub(r'\(at\s+[\d.-]+\s+[\d.-]+', '(at -6.994 -4.066', prop_block, count=1)
                    head = head[:prop_start] + new_prop + head[prop_end:]
                    print(f"Moved SW2 Reference to (-6.994, -4.066)")

# =====================================================
# Insert new gr_text blocks from stash
# =====================================================
# Find a good insertion point — after the last gr_text in head
last_gr_text_end = 0
for m in re.finditer(r'\(gr_text\b', head):
    block, end = extract_block(head, m.start())
    if block:
        last_gr_text_end = end

if last_gr_text_end > 0 and stash_new_blocks:
    insert_text = ""
    for name, block in stash_new_blocks:
        insert_text += "\n\t" + block
        print(f"Inserting '{name}'")
    head = head[:last_gr_text_end] + insert_text + head[last_gr_text_end:]

# =====================================================
# Verify bracket balance
# =====================================================
depth = 0
for ch in head:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
print(f"\nBracket balance: {depth}")

if depth != 0:
    print("ERROR: Bracket imbalance! Not writing.")
    sys.exit(1)

with open(HEAD_PCB, 'w') as f:
    f.write(head)
print("Written to PCB.")

# Verify the changes
print("\n=== Verification ===")
for text_check in ['GAIN (dB)', 'ON ↑', 'Balanced Booster']:
    if text_check in head:
        print(f"  ✓ '{text_check}' present")
    else:
        print(f"  ✗ '{text_check}' MISSING")

for text_check in ['Rev 1.0', 'Aurora DSP IcePower Booster']:
    # Check in gr_text context on B.SilkS
    found = False
    for m in re.finditer(r'\(gr_text\b', head):
        block, _ = extract_block(head, m.start())
        if block and text_check in block and 'B.SilkS' in block:
            found = True
    if not found:
        print(f"  ✓ '{text_check}' removed from B.SilkS")
    else:
        print(f"  ✗ '{text_check}' still on B.SilkS")
