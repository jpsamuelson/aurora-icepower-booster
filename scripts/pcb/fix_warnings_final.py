#!/usr/bin/env python3
"""
Fix letzte 4 Silk-Warnings:
- SW1 Reference: silk_over_copper + silk_overlap → auf F.Fab verschieben
- FB1, FB2 Reference: silk_overlap → Position anpassen (weiter vom Outline)
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

fixes = []

# ── SW1: Reference auf F.Fab verschieben ──
lines = content.split('\n')
result_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    if '(property "Reference"' in line:
        ref_m = re.search(r'"Reference"\s+"([^"]+)"', line)
        ref = ref_m.group(1) if ref_m else ''
        
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
        
        if ref == 'SW1' and 'SilkS' in block:
            # SW1: Verschiebe auf F.Fab
            block = block.replace('(layer "F.SilkS")', '(layer "F.Fab")')
            fixes.append(f"SW1: F.SilkS → F.Fab")
        
        elif ref in ('FB1', 'FB2') and 'SilkS' in block:
            # FB1/FB2: Reference Position anpassen — weg vom Outline
            # FB1 ist bei (118, 10), FB2 bei (118, 26)
            # Ref-Text 3mm über dem Bauteil platzieren
            at_m = re.search(r'\(at\s+([\d.+-]+)\s+([\d.+-]+)', block)
            if at_m:
                old_x, old_y = at_m.group(1), at_m.group(2)
                # Verschiebe Y um -3mm (nach oben, weg vom Silk-Outline)
                new_y = float(old_y) - 3.0
                block = block.replace(
                    f'(at {old_x} {old_y}',
                    f'(at {old_x} {new_y:.2f}',
                    1
                )
                fixes.append(f"{ref}: Ref Y verschoben {old_y} → {new_y:.2f}")
        
        result_lines.extend(block.split('\n'))
        i = j
        continue
    
    result_lines.append(line)
    i += 1

content = '\n'.join(result_lines)

# Bracket balance
depth_check = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
if depth_check != 0:
    print(f"❌ Bracket balance: {depth_check}")
    import sys; sys.exit(1)

with open(PCB, 'w') as f:
    f.write(content)

print("✅ Letzte Silk-Fixes:")
for f_ in fixes:
    print(f"   {f_}")
print(f"   Bracket balance: OK")
print(f"   Größe: {len(content):,} bytes")
