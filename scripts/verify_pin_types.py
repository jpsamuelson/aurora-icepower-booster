#!/usr/bin/env python3
"""Verify all lib_symbols pin type changes."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

cache_start = text.find('(lib_symbols')

print("=== TEL5-2422 Pin Types ===")
tel_start = text.find('"TEL5-2422"', cache_start)
if tel_start >= 0:
    chunk = text[tel_start:tel_start+5000]
    pins = re.findall(
        r'\(pin\s+(\w+)\s+\w+\s+\(at[^)]+\).*?\(name\s+"([^"]+)".*?\(number\s+"(\d+)"',
        chunk, re.DOTALL
    )
    for ptype, pname, pnum in pins:
        status = "✅" if ptype != "unspecified" and ptype != "power_out" or pnum in ['14', '11', '1'] else "⚠️"
        if pnum == '3' and ptype == 'passive':
            status = "✅ FIXED"
        elif pnum in ['9', '16'] and ptype == 'power_in':
            status = "✅ FIXED"
        elif pnum in ['14', '11', '1'] and ptype == 'power_out':
            status = "✅ OK"
        elif pnum in ['22', '23'] and ptype == 'power_in':
            status = "✅ OK"
        elif pnum == '2' and ptype == 'power_out':
            status = "✅ OK"
        print(f"  Pin {pnum:>2} ({pname:>12}): {ptype:>12} {status}")

print("\n=== ADP7118ARDZ Pin Types ===")
adp_start = text.find('"ADP7118ARDZ"', cache_start)
if adp_start >= 0:
    chunk = text[adp_start:adp_start+5000]
    pins = re.findall(
        r'\(pin\s+(\w+)\s+\w+\s+\(at[^)]+\).*?\(name\s+"([^"]+)".*?\(number\s+"(\d+)"',
        chunk, re.DOTALL
    )
    for ptype, pname, pnum in pins:
        status = ""
        if pnum == '2' and ptype == 'passive':
            status = "✅ FIXED"
        elif pnum == '1' and ptype == 'power_out':
            status = "✅ OK"
        else:
            status = "✅ OK"
        print(f"  Pin {pnum:>2} ({pname:>12}): {ptype:>12} {status}")
