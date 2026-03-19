#!/usr/bin/env python3
"""Debug: find exact lib_symbols cache structure."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# Find all top-level symbols in lib_symbols cache
cache_start = text.find('(lib_symbols')
print(f"lib_symbols start: {cache_start}")

# Find all (symbol "..." entries within lib_symbols
# The cache structure is: (lib_symbols (symbol "lib:name" ...) (symbol "lib:name" ...) ...)
pos = cache_start
count = 0
for m in re.finditer(r'\(symbol\s+"([^"]+)"', text[cache_start:cache_start+10000]):
    name = m.group(1)
    abs_pos = cache_start + m.start()
    if 'TEL5' in name or 'ADP' in name or count < 5:
        print(f"  Symbol '{name}' at pos {abs_pos}")
    count += 1
    if count > 50:
        break

# Also search further
for name_pat in ['TEL5-2422', 'ADP7118']:
    hits = [(m.start(), m.group(0)) for m in re.finditer(r'\(symbol\s+"[^"]*' + name_pat + r'[^"]*"', text)]
    print(f"\n  Matches for '{name_pat}':")
    for pos, match in hits:
        print(f"    pos {pos}: {match}")
