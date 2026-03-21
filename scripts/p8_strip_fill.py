#!/usr/bin/env python3
"""Strip all filled_polygon blocks from zones, keeping zone definitions intact."""
import re

PCB = 'aurora-dsp-icepower-booster.kicad_pcb'

with open(PCB) as f:
    text = f.read()

orig_size = len(text)

# Remove filled_polygon blocks (balanced parens)
result = []
i = 0
removed = 0
while i < len(text):
    # Check for filled_polygon start
    if text[i:i+15] == '(filled_polygon':
        # Skip this balanced block
        depth = 0
        j = i
        while j < len(text):
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        # Also skip trailing whitespace/newline
        while j < len(text) and text[j] in ' \t\n':
            j += 1
        removed += 1
        i = j
    else:
        result.append(text[i])
        i += 1

text_out = ''.join(result)

# Bracket balance check
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in text_out)
assert depth == 0, f'Bracket imbalance: {depth}'

with open(PCB, 'w') as f:
    f.write(text_out)

print(f'Removed {removed} filled_polygon blocks')
print(f'Size: {orig_size:,} → {len(text_out):,} bytes')
