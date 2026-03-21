#!/usr/bin/env python3
"""
Strip all trace segments and vias from PCB, preparing for re-routing.
Also strip zone fill polygons (will be regenerated after routing).
Preserves: footprints, zones (outlines only), nets, board outline, groups, etc.
"""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

with open(PCB_FILE, 'r') as f:
    text = f.read()

orig_len = len(text)

# Count before
seg_count = len(re.findall(r'\(segment\b', text))
via_count = len(re.findall(r'\(via\b', text))
fp_count = len(re.findall(r'\(filled_polygon\b', text))
print(f"Before: {seg_count} segments, {via_count} vias, {fp_count} filled_polygons")

def remove_balanced_blocks(text, keyword):
    """Remove all balanced-paren blocks starting with (keyword ...) from text."""
    result = []
    i = 0
    removed = 0
    kw_paren = '(' + keyword
    kw_len = len(kw_paren)
    while i < len(text):
        # Check if we're at a block to remove
        if (text[i] == '(' and text[i:i+kw_len] == kw_paren
                and (i + kw_len >= len(text) or not text[i+kw_len].isalnum())):
            # Find matching close paren
            depth = 0
            j = i
            while j < len(text):
                if text[j] == '(':
                    depth += 1
                elif text[j] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            # Skip block and trailing whitespace/newlines
            i = j + 1
            while i < len(text) and text[i] in ' \t\n\r':
                i += 1
            removed += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result), removed

text, seg_removed = remove_balanced_blocks(text, 'segment')
print(f"Removed {seg_removed} segments")

text, via_removed = remove_balanced_blocks(text, 'via')
print(f"Removed {via_removed} vias")

text, fp_removed = remove_balanced_blocks(text, 'filled_polygon')
print(f"Removed {fp_removed} filled_polygon blocks")

# Verify
seg_after = len(re.findall(r'\(segment\b', text))
via_after = len(re.findall(r'\(via\b', text))
fp_after = len(re.findall(r'\(filled_polygon\b', text))
print(f"After: {seg_after} segments, {via_after} vias, {fp_after} filled_polygons")

# Bracket balance check
depth = 0
for ch in text:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: depth={depth}"
print(f"Bracket balance: OK")

with open(PCB_FILE, 'w') as f:
    f.write(text)
print(f"Written: {len(text)} bytes (was {orig_len})")
print(f"Size delta: {len(text) - orig_len} bytes")
