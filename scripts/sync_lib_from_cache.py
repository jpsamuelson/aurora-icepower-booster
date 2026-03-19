#!/usr/bin/env python3
"""Sync .kicad_sym library entries from lib_symbols cache to fix lib_symbol_mismatch warnings.
Copies the cache version (from .kicad_sch) to the library (.kicad_sym), 
adjusting 'aurora-dsp-icepower-booster:NAME' → 'NAME'."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
LIB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sym"

with open(SCH) as f:
    sch = f.read()
with open(LIB) as f:
    lib = f.read()

PREFIX = "aurora-dsp-icepower-booster:"

def extract_balanced(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], start, i+1
    return None, start, start

changes = []

for name in ['TEL5-2422', 'ADP7118ARDZ']:
    # Extract from cache
    cache_m = re.search(rf'\(symbol\s+"{PREFIX}{re.escape(name)}"', sch)
    if not cache_m:
        print(f"  {name}: NOT FOUND in cache!")
        continue
    cache_block, _, _ = extract_balanced(sch, cache_m.start())
    
    # Strip the library prefix from all symbol names within the block
    # e.g. "aurora-dsp-icepower-booster:TEL5-2422" → "TEL5-2422"
    adapted = cache_block.replace(f'"{PREFIX}{name}"', f'"{name}"')
    # Also for sub-symbols (shouldn't have prefix per memory, but just in case)
    adapted = adapted.replace(f'{PREFIX}', '')
    
    # Find in library
    lib_m = re.search(rf'\(symbol\s+"{re.escape(name)}"', lib)
    if not lib_m:
        print(f"  {name}: NOT FOUND in library!")
        continue
    lib_block, lib_start, lib_end = extract_balanced(lib, lib_m.start())
    
    # Replace library entry with adapted cache entry
    lib = lib[:lib_start] + adapted + lib[lib_end:]
    changes.append(f"{name}: replaced library entry ({len(lib_block)} → {len(adapted)} chars)")
    print(f"  ✅ {name}: synced ({len(lib_block)} → {len(adapted)} chars)")

# Bracket balance
depth = 0
for ch in lib:
    if ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"  Brackets balanced ✅")

with open(LIB, "w") as f:
    f.write(lib)

print(f"\n{len(changes)} changes applied to .kicad_sym")
