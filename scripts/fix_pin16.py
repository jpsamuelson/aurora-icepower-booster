#!/usr/bin/env python3
"""Fix U1 Pin 16 unspecified → power_in (missed in first pass)."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    text = f.read()

cache_start = text.find('(lib_symbols')
tel_start = text.find('"TEL5-2422"', cache_start)

if tel_start >= 0:
    search_region = text[tel_start:tel_start+5000]
    
    # Find Pin 16 with unspecified type
    pin16_m = re.search(
        r'\(pin\s+unspecified\s+line\s+\(at[^)]+\).*?\(number\s+"16"',
        search_region, re.DOTALL
    )
    if pin16_m:
        abs_start = tel_start + pin16_m.start()
        old_text = text[abs_start:abs_start + pin16_m.end() - pin16_m.start()]
        new_text = old_text.replace('unspecified', 'power_in', 1)
        text = text[:abs_start] + new_text + text[abs_start + len(old_text):]
        print("Pin 16: unspecified → power_in DONE")
        
        # Verify
        depth = 0
        for ch in text:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
        assert depth == 0, f"Bracket balance: {depth}"
        print("Brackets balanced ✅")
        
        with open(SCH, "w") as f:
            f.write(text)
        print("Written")
    else:
        print("Pin 16 (unspecified) not found — may already be fixed")
        # Check current state
        pin16_check = re.search(r'\(pin\s+(\w+)\s+line\s+\(at[^)]+\).*?\(number\s+"16"', search_region, re.DOTALL)
        if pin16_check:
            print(f"  Pin 16 current type: {pin16_check.group(1)}")
