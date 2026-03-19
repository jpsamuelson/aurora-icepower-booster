#!/usr/bin/env python3
"""Extract the raw TEL5-2422 block from lib_symbols."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, 'r') as f:
    content = f.read()

cache_start = content.find('(lib_symbols')
cache_text = content[cache_start:]

# Find TEL5-2422
idx = cache_text.find('TEL5-2422')
print(f"TEL5-2422 at offset {idx}")

# Go back to find the enclosing (symbol
block_start = cache_text.rfind('(symbol', 0, idx)

# Count brackets to find end
depth = 0
i = block_start
while i < len(cache_text):
    if cache_text[i] == '(':
        depth += 1
    elif cache_text[i] == ')':
        depth -= 1
        if depth == 0:
            break
    i += 1

block = cache_text[block_start:i+1]
# Print first/last 500 chars and any lines with "pin"
print(f"\nBlock size: {len(block)} chars")
print(f"\n--- First 800 chars ---")
print(block[:800])
print(f"\n--- Pin lines ---")
for line in block.split('\n'):
    if 'pin ' in line.lower() or 'at ' in line.lower() and 'number' in line.lower():
        print(line[:200])

# Also search for pin patterns more broadly
print(f"\n--- All occurrences of '(pin ' ---")
for m in re.finditer(r'\(pin\s', block):
    snippet = block[m.start():m.start()+200]
    snippet = snippet.replace('\n', ' ')
    print(f"  offset {m.start()}: {snippet[:150]}")
