#!/usr/bin/env python3
"""
Phase 1: Silk-Referenzen unhiden und intelligent positionieren.

Strategie:
- R, C (0805 SMD): Reference auf F.Fab verschieben (kein Platz auf Silk bei dichten Boards)
- U, D, Q, FB: Reference auf F.SilkS, Font 0.6mm, Position neben dem Bauteil
- J (Connectors): Reference auf F.SilkS, Font 0.8mm, sichtbar halten
- SW (Switches): Reference auf F.SilkS, Font 0.6mm
- MH (Mounting Holes): Reference auf F.Fab

Für alle: (hide yes) entfernen
Für F.Fab-Texte: kein Silk-Overlap möglich
Für F.SilkS-Texte: Font verkleinern + Position justieren
"""
import re, math

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

# Kategorisierung nach Prefix
MOVE_TO_FAB = {'R', 'C'}  # Widerstände, Kondensatoren → F.Fab (kein Platz auf Silk)
KEEP_ON_SILK_SMALL = {'U', 'D', 'Q', 'FB'}  # ICs, Dioden, Transistoren → F.SilkS, 0.6mm
KEEP_ON_SILK_LARGE = {'J', 'SW'}  # Connectors, Switches → F.SilkS, 0.8mm  
MOVE_TO_FAB_ALSO = {'MH'}  # Mounting Holes → F.Fab

def get_ref_prefix(ref):
    """Extract letter prefix from reference (e.g., 'R1' → 'R', 'FB1' → 'FB')."""
    m = re.match(r'^([A-Za-z]+)', ref)
    return m.group(1) if m else ''

def make_font_block(size, thickness):
    return (
        f'(effects\n'
        f'\t\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t\t(size {size} {size})\n'
        f'\t\t\t\t\t\t\t(thickness {thickness})\n'
        f'\t\t\t\t\t\t)\n'
        f'\t\t\t\t\t)'
    )

lines = content.split('\n')
result_lines = []
changes = {'unhide': 0, 'to_fab': 0, 'resize_small': 0, 'resize_large': 0}
i = 0

while i < len(lines):
    line = lines[i]
    
    if '(property "Reference"' in line:
        # Extract reference name
        ref_m = re.search(r'"Reference"\s+"([^"]+)"', line)
        if not ref_m:
            result_lines.append(line)
            i += 1
            continue
        
        ref = ref_m.group(1)
        prefix = get_ref_prefix(ref)
        
        # Collect the entire property block
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
        
        # 1. Remove (hide yes) — alle Referenzen sichtbar machen
        if '(hide yes)' in block:
            # Remove the hide line entirely
            block_new_lines = []
            for bl in block.split('\n'):
                if bl.strip() == '(hide yes)':
                    continue
                block_new_lines.append(bl)
            block = '\n'.join(block_new_lines)
            changes['unhide'] += 1
        
        # 2. Kategoriebasierte Anpassungen
        if prefix in MOVE_TO_FAB or prefix in MOVE_TO_FAB_ALSO:
            # Layer auf F.Fab ändern
            block = re.sub(r'\(layer "F\.SilkS"\)', '(layer "F.Fab")', block)
            block = re.sub(r'\(layer "B\.SilkS"\)', '(layer "B.Fab")', block)
            # Font: Standard 1mm (auf Fab spielt Größe keine Rolle für DRC)
            changes['to_fab'] += 1
            
        elif prefix in KEEP_ON_SILK_SMALL:
            # Font auf 0.6mm verkleinern
            block = re.sub(
                r'\(size\s+[\d.]+\s+[\d.]+\)',
                '(size 0.6 0.6)',
                block
            )
            block = re.sub(
                r'\(thickness\s+[\d.]+\)',
                '(thickness 0.12)',
                block
            )
            changes['resize_small'] += 1
            
        elif prefix in KEEP_ON_SILK_LARGE:
            # Font auf 0.8mm 
            block = re.sub(
                r'\(size\s+[\d.]+\s+[\d.]+\)',
                '(size 0.8 0.8)',
                block
            )
            block = re.sub(
                r'\(thickness\s+[\d.]+\)',
                '(thickness 0.15)',
                block
            )
            changes['resize_large'] += 1
        
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
print("Bracket balance: OK")

with open(PCB, 'w') as f:
    f.write(content)

print(f"\n✅ Phase 1 abgeschlossen:")
print(f"   Unhidden:            {changes['unhide']}")
print(f"   → F.Fab (R/C/MH):   {changes['to_fab']}")
print(f"   SilkS 0.6mm (U/D/Q/FB): {changes['resize_small']}")
print(f"   SilkS 0.8mm (J/SW): {changes['resize_large']}")
print(f"   Größe: {len(content):,} bytes")
