#!/usr/bin/env python3
"""
Fix text_height/text_thickness Warnings: 0.6mm ist unter KiCad-Minimum.
Erhöhe alle 0.6mm Text auf F.SilkS auf 0.8mm (JLCPCB Minimum).
Plus: SW3-SW7 Reference-Texte verschieben (silk_over_copper).
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

# ── Fix 1: Alle 0.6mm Silk-Texte → 0.8mm ──
# Die text_height/text_thickness-Warnings kommen von (size 0.6 0.6) und (thickness 0.12)
# KiCad Minimum ist 0.8mm Höhe / 0.15mm Dicke
lines = content.split('\n')
result_lines = []
text_fixes = 0
sw_fixes = 0

i = 0
while i < len(lines):
    line = lines[i]
    
    if '(property "Reference"' in line:
        ref_m = re.search(r'"Reference"\s+"([^"]+)"', line)
        ref = ref_m.group(1) if ref_m else ''
        prefix = re.match(r'^([A-Za-z]+)', ref)
        prefix = prefix.group(1) if prefix else ''
        
        # Collect block
        depth = 0
        block_lines = [line]
        for ch in line:
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
        j = i + 1
        while j < len(lines) and depth > 0:
            block_lines.append(lines[j])
            for ch in lines[j]:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            j += 1
        
        block = '\n'.join(block_lines)
        
        # Fix text size: 0.6 → 0.8, thickness 0.12 → 0.15
        if 'SilkS' in block and '(size 0.6 0.6)' in block:
            block = block.replace('(size 0.6 0.6)', '(size 0.8 0.8)')
            block = block.replace('(thickness 0.12)', '(thickness 0.15)')
            text_fixes += 1
        
        # Fix SW3-SW7: Reference position verschieben (weg von Pads)
        # SW Footprints sind vertikal (DIP-Switches), Reference muss weiter weg
        if prefix == 'SW' and 'SilkS' in block:
            # Move reference 3mm zur Seite (negative X = links vom Bauteil)
            at_m = re.search(r'\(at\s+([\d.+-]+)\s+([\d.+-]+)', block)
            if at_m:
                old_x = float(at_m.group(1))
                old_y = float(at_m.group(2))
                # Verschiebe den Text 5mm nach links (außerhalb der Pads)
                new_x = old_x - 5.0
                block = block.replace(
                    f'(at {at_m.group(1)} {at_m.group(2)}',
                    f'(at {new_x:.2f} {old_y}',
                    1
                )
                sw_fixes += 1
        
        result_lines.extend(block.split('\n'))
        i = j
        continue
    
    result_lines.append(line)
    i += 1

content = '\n'.join(result_lines)

# ── Bracket balance ──
depth_check = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
if depth_check != 0:
    print(f"❌ Bracket balance: {depth_check}")
    import sys; sys.exit(1)

with open(PCB, 'w') as f:
    f.write(content)

print(f"✅ Text-Fixes:")
print(f"   Font 0.6→0.8mm: {text_fixes}")
print(f"   SW Ref verschoben: {sw_fixes}")
print(f"   Bracket balance: OK")
print(f"   Größe: {len(content):,} bytes")
