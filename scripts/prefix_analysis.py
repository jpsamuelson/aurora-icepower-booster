#!/usr/bin/env python3
"""Pre-fix analysis: check #PWR010 area and PWR_FLAG cache."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

# 1. Check all wires at (140, 40) — #PWR010 (GND)
print("=== Wires at #PWR010 (140, 40) ===")
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    for wx, wy in [(x1, y1), (x2, y2)]:
        if abs(wx - 140.0) < 0.02 and abs(wy - 40.0) < 0.02:
            print(f"  ({x1},{y1})->({x2},{y2})")
            break

# 2. Check if PWR_FLAG is already in lib_symbols cache
print("\n=== PWR_FLAG in lib_symbols cache? ===")
cache_start = text.find('(lib_symbols')
if cache_start >= 0:
    idx = text.find('"power:PWR_FLAG"', cache_start)
    if idx >= 0:
        print("  YES — PWR_FLAG already in cache")
        # Extract first 200 chars
        print(f"  Fragment: {text[idx:idx+200]}")
    else:
        print("  NO — Need to add PWR_FLAG to lib_symbols cache")

# 3. Check existing PWR_FLAG symbol definition from system library
import os
sys_lib = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/power.kicad_sym"
if os.path.exists(sys_lib):
    with open(sys_lib) as f:
        pwr_text = f.read()
    # Find PWR_FLAG
    idx = pwr_text.find('"PWR_FLAG"')
    if idx >= 0:
        # Extract balanced block
        start = pwr_text.rfind('(symbol', max(0, idx - 50), idx)
        depth = 0
        end = start
        for i in range(start, min(start + 2000, len(pwr_text))):
            if pwr_text[i] == '(':
                depth += 1
            elif pwr_text[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        print(f"\n=== PWR_FLAG from system library ===")
        print(pwr_text[start:end])

# 4. Find existing #FLG references to determine next available number
print("\n=== Existing #FLG references ===")
flg_refs = re.findall(r'"(#FLG\d+)"', text)
print(f"  Found: {sorted(set(flg_refs))}")

# 5. Check existing capacitor references for next available C number
print("\n=== Highest C reference ===")
c_refs = re.findall(r'"(C\d+)"', text)
c_nums = sorted(set(int(r[1:]) for r in c_refs))
print(f"  Max C: C{max(c_nums)}, next: C{max(c_nums)+1}")

# 6. Check highest #PWR reference
print("\n=== Highest #PWR reference ===")
pwr_refs = re.findall(r'"(#PWR\d+)"', text)
pwr_nums = sorted(set(int(r[4:]) for r in pwr_refs))
print(f"  Max #PWR: #PWR{max(pwr_nums):03d}, next: #PWR{max(pwr_nums)+1:03d}")

# 7. Check the #PWR001 wire situation
print("\n=== #PWR001 wire detail ===")
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    if abs(x1 - 98.0) < 0.02 or abs(x2 - 98.0) < 0.02:
        if (abs(y1 - 18.65) < 5 or abs(y2 - 18.65) < 5) and (abs(y1 - 21.19) < 5 or abs(y2 - 21.19) < 5):
            print(f"  ({x1},{y1})->({x2},{y2})")

# 8. Check wires at V+ area near C22 for Fix 6
print("\n=== V+ wires near C22 (x≈150.16, y=32-35) ===")
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    if abs(x1 - 150.16) < 0.02 or abs(x2 - 150.16) < 0.02:
        if (30 < y1 < 36) or (30 < y2 < 36):
            print(f"  ({x1},{y1})->({x2},{y2})")

print("\n=== #PWR0152 at (150.16, 35.0) connections ===")
for m in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    if (abs(x1 - 150.16) < 0.02 and abs(y1 - 35.0) < 0.02) or \
       (abs(x2 - 150.16) < 0.02 and abs(y2 - 35.0) < 0.02):
        print(f"  ({x1},{y1})->({x2},{y2})")
