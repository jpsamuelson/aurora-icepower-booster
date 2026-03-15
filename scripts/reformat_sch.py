#!/usr/bin/env python3
"""
Reformat KiCad schematic from single-line to proper multi-line format.
This is a simple S-expression pretty-printer that preserves all data.
"""
import sys

INPUT = 'aurora-dsp-icepower-booster.kicad_sch'
OUTPUT = INPUT  # overwrite in place

# Read
data = open(INPUT).read().strip()
print(f"Input: {len(data)} chars, {data.count(chr(10))} newlines")

# Verify paren balance before reformatting
balance = data.count('(') - data.count(')')
if balance != 0:
    print(f"ERROR: Paren imbalance: {balance}")
    sys.exit(1)

# Simple S-expression reformatter  
out = []
depth = 0
i = 0
n = len(data)

# Tokens that should start a new line at depth >= 1
NEWLINE_TOKENS = {
    'symbol', 'property', 'wire', 'junction', 'label',
    'polyline', 'rectangle', 'circle', 'arc', 'text',
    'pin', 'effects', 'stroke', 'fill', 'at', 'pts',
    'version', 'generator', 'uuid', 'paper', 'lib_symbols',
    'kicad_sch', 'in_bom', 'on_board', 'dnp',
    'unit', 'exclude_from_sim', 'pin_numbers', 'pin_names',
    'offset', 'length', 'name', 'number',
    'embedded_fonts',
}

while i < n:
    c = data[i]
    
    if c == '(':
        # Look ahead to get the token name
        j = i + 1
        while j < n and data[j] == ' ':
            j += 1
        k = j
        while k < n and data[k] not in ' ()"\n':
            k += 1
        token = data[j:k]
        
        # Decide if this should start a new line
        if depth >= 1 and token in NEWLINE_TOKENS:
            out.append('\n' + '  ' * depth)
        elif depth == 0:
            pass  # Top level, no indent needed
        
        out.append('(')
        depth += 1
        i += 1
        
    elif c == ')':
        depth -= 1
        out.append(')')
        i += 1
        
    elif c == '"':
        # String literal - copy verbatim
        j = i + 1
        while j < n:
            if data[j] == '\\':
                j += 2
                continue
            if data[j] == '"':
                j += 1
                break
            j += 1
        out.append(data[i:j])
        i = j
        
    elif c == ' ' or c == '\t' or c == '\n':
        # Whitespace - collapse to single space
        if out and out[-1] not in ('(', '\n'):
            out.append(' ')
        i += 1
        while i < n and data[i] in ' \t\n':
            i += 1
            
    else:
        # Regular token character
        out.append(c)
        i += 1

result = ''.join(out) + '\n'

# Verify paren balance after reformatting
balance2 = result.count('(') - result.count(')')
if balance2 != 0:
    print(f"ERROR: Output paren imbalance: {balance2}")
    sys.exit(1)

# Verify data integrity: same number of parens
orig_open = data.count('(')
new_open = result.count('(')
orig_close = data.count(')')
new_close = result.count(')')
print(f"Parens: orig=({orig_open}/{orig_close}), new=({new_open}/{new_close})")
if orig_open != new_open or orig_close != new_close:
    print("ERROR: Paren count mismatch!")
    sys.exit(1)

# Write
open(OUTPUT, 'w').write(result)
print(f"Output: {len(result)} chars, {result.count(chr(10))} newlines")
print("Done!")
