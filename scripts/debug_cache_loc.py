#!/usr/bin/env python3
"""Debug: find the exact text around TEL5-2422 and ADP7118ARDZ in lib_symbols cache."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

cache_start = text.find('(lib_symbols')
print(f"lib_symbols at: {cache_start}")

# Find TEL5-2422
tel_idx = text.find('"TEL5-2422"', cache_start)
print(f"\nTEL5-2422 name at: {tel_idx}")
if tel_idx >= 0:
    # Show 150 chars before
    print(f"Context before: ...{repr(text[tel_idx-150:tel_idx])}")
    print(f"Context after: {repr(text[tel_idx:tel_idx+100])}")
    
    # Try to find '(symbol' before it
    check_region = text[max(0, tel_idx-200):tel_idx]
    sym_pos = check_region.rfind('(symbol')
    print(f"  '(symbol' found in check_region at: {sym_pos}")
    if sym_pos >= 0:
        abs_pos = max(0, tel_idx-200) + sym_pos
        print(f"  Absolute position: {abs_pos}")
        print(f"  Text there: {repr(text[abs_pos:abs_pos+80])}")

# Find ADP7118ARDZ
adp_idx = text.find('"ADP7118ARDZ"', cache_start)
print(f"\nADP7118ARDZ name at: {adp_idx}")
if adp_idx >= 0:
    print(f"Context before: ...{repr(text[adp_idx-150:adp_idx])}")
    print(f"Context after: {repr(text[adp_idx:adp_idx+100])}")
    
    check_region = text[max(0, adp_idx-200):adp_idx]
    sym_pos = check_region.rfind('(symbol')
    print(f"  '(symbol' found in check_region at: {sym_pos}")
    if sym_pos >= 0:
        abs_pos = max(0, adp_idx-200) + sym_pos
        print(f"  Absolute position: {abs_pos}")
        print(f"  Text there: {repr(text[abs_pos:abs_pos+80])}")
