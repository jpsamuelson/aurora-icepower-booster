#!/usr/bin/env python3
"""Compare lib_symbols cache (in .kicad_sch) vs library (.kicad_sym) for TEL5-2422 and ADP7118ARDZ."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
LIB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sym"

with open(SCH) as f:
    sch = f.read()
with open(LIB) as f:
    lib = f.read()

def extract_balanced(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

def normalize(block):
    """Normalize whitespace for comparison."""
    # Collapse multiple spaces/newlines to single space
    return re.sub(r'\s+', ' ', block.strip())

for name in ['TEL5-2422', 'ADP7118ARDZ']:
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    
    # Find in cache (lib_symbols section of .kicad_sch)
    cache_pat = re.search(rf'\(symbol\s+"aurora-dsp-icepower-booster:{name}"', sch)
    if cache_pat:
        cache_block = extract_balanced(sch, cache_pat.start())
        print(f"  Cache: {len(cache_block)} chars at pos {cache_pat.start()}")
    else:
        print(f"  Cache: NOT FOUND")
        continue
    
    # Find in library (.kicad_sym)
    lib_pat = re.search(rf'\(symbol\s+"{name}"', lib)
    if lib_pat:
        lib_block = extract_balanced(lib, lib_pat.start())
        print(f"  Library: {len(lib_block)} chars at pos {lib_pat.start()}")
    else:
        print(f"  Library: NOT FOUND")
        continue
    
    # Compare normalized
    cache_norm = normalize(cache_block)
    lib_norm = normalize(lib_block)
    
    # The cache uses "aurora-dsp-icepower-booster:NAME" prefix, library uses "NAME"
    # Normalize the prefix away for comparison
    cache_norm_clean = cache_norm.replace(f'aurora-dsp-icepower-booster:{name}', name)
    
    if cache_norm_clean == lib_norm:
        print(f"  ✅ MATCH (after prefix normalization)")
    else:
        print(f"  ❌ MISMATCH")
        # Find differences
        # Split into tokens for comparison
        cache_tokens = cache_norm_clean.split()
        lib_tokens = lib_norm.split()
        
        print(f"  Cache tokens: {len(cache_tokens)}, Library tokens: {len(lib_tokens)}")
        
        # Show first N differences
        diffs = 0
        max_diffs = 20
        i = j = 0
        while i < len(cache_tokens) and j < len(lib_tokens) and diffs < max_diffs:
            if cache_tokens[i] != lib_tokens[j]:
                # Show context
                ctx_c = ' '.join(cache_tokens[max(0,i-2):i+3])
                ctx_l = ' '.join(lib_tokens[max(0,j-2):j+3])
                print(f"\n  Diff #{diffs+1} at token ~{i}:")
                print(f"    Cache: ...{ctx_c}...")
                print(f"    Lib:   ...{ctx_l}...")
                diffs += 1
                # Try to sync by looking ahead
                found = False
                for lookahead in range(1, 10):
                    if i+lookahead < len(cache_tokens) and cache_tokens[i+lookahead] == lib_tokens[j]:
                        print(f"    → Cache has {lookahead} extra token(s)")
                        i += lookahead
                        found = True
                        break
                    if j+lookahead < len(lib_tokens) and cache_tokens[i] == lib_tokens[j+lookahead]:
                        print(f"    → Library has {lookahead} extra token(s)")
                        j += lookahead
                        found = True
                        break
                if not found:
                    i += 1
                    j += 1
            else:
                i += 1
                j += 1
        
        if i < len(cache_tokens):
            print(f"\n  Cache has {len(cache_tokens) - i} extra tokens at end")
        if j < len(lib_tokens):
            print(f"\n  Library has {len(lib_tokens) - j} extra tokens at end")
