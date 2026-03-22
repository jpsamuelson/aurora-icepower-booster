#!/usr/bin/env python3
"""
Phase 3+4+5: Zone-Inseln entfernen, Stitching-Vias fixen, U1 Silk-Overlap fixen.

Phase 3: island_removal_mode 2 → 1 (alle Inseln entfernen)
Phase 4: Stitching-Vias bei (12.5, 72.5) und (12.5, 182.5) entfernen (zu nah an J4/J8)
Phase 5: U1 Value-Text Position verschieben (weg vom Reference)
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

changes = []

# ── Phase 3: island_removal_mode 2 → 1 ──
count = content.count('(island_removal_mode 2)')
content = content.replace('(island_removal_mode 2)', '(island_removal_mode 1)')
changes.append(f"Phase 3: island_removal_mode → 1 ({count} Zonen)")

# ── Phase 4: Stitching-Vias bei J4 und J8 entfernen ──
# Via bei (12.5, 72.5) und (12.5, 182.5) — zu nah an J4 Pad1 (12.58, 72.14) / J8 Pad1 (12.58, 183.22)
# Finde und entferne diese spezifischen Vias
lines = content.split('\n')
result_lines = []
removed_vias = 0
i = 0
while i < len(lines):
    stripped = lines[i].strip()
    if (stripped == '(via' or stripped.startswith('(via ')) and lines[i].startswith('\t') and not lines[i].startswith('\t\t'):
        # Collect via block
        depth = 0
        block_lines = []
        j = i
        while j < len(lines):
            block_lines.append(lines[j])
            for ch in lines[j]:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            if depth <= 0: break
            j += 1
        
        block = '\n'.join(block_lines)
        # Check if this is one of the problem vias
        at_m = re.search(r'\(at\s+12\.5\s+72\.5\)', block)
        at_m2 = re.search(r'\(at\s+12\.5\s+182\.5\)', block)
        net_m = re.search(r'\(net\s+134\)', block)  # GND = 134
        
        if (at_m or at_m2) and net_m:
            removed_vias += 1
            i = j + 1
            continue
        
        result_lines.extend(block_lines)
        i = j + 1
        continue
    
    result_lines.append(lines[i])
    i += 1

content = '\n'.join(result_lines)
changes.append(f"Phase 4: {removed_vias} Stitching-Vias entfernt (J4/J8 hole_to_hole)")

# ── Phase 5: U1 Value-Text verschieben ──
# U1 hat Reference und Value an derselben Position (77.16, 19.00)
# Value auf F.Fab verschieben (statt F.SilkS)
# Finde U1 footprint block und seinen Value
# U1 Value: Suche nach (property "Value" innerhalb von U1 footprint
# Einfacher: Suche nach "TEL5" value text auf SilkS bei U1 Position
u1_val_found = False
lines = content.split('\n')
result_lines = []
i = 0
in_u1 = False
while i < len(lines):
    line = lines[i]
    
    # Track when we're inside U1 footprint
    if '(property "Reference" "U1"' in line:
        in_u1 = True
    
    if in_u1 and '(property "Value"' in line:
        # Collect the value property block
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
        if 'SilkS' in block or 'Silkscreen' in block or '77.16' in block:
            # Move value 2.5mm down: change (at X Y) → (at X Y+2.5)
            block = re.sub(
                r'\(at\s+([\d.+-]+)\s+([\d.+-]+)',
                lambda m: f'(at {m.group(1)} {float(m.group(2)) + 2.5:.2f}',
                block, count=1
            )
            u1_val_found = True
        
        result_lines.extend(block.split('\n'))
        in_u1 = False
        i = j
        continue
    
    result_lines.append(line)
    i += 1

content = '\n'.join(result_lines)
if u1_val_found:
    changes.append("Phase 5: U1 Value-Text um 2.5mm verschoben")
else:
    changes.append("Phase 5: U1 Value-Text nicht gefunden (manuell prüfen)")

# ── Bracket balance ──
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in content)
if depth != 0:
    print(f"❌ Bracket balance: {depth}")
    import sys; sys.exit(1)
print("Bracket balance: OK")

# ── Speichern ──
with open(PCB, 'w') as f:
    f.write(content)

print(f"\n✅ Änderungen angewendet:")
for c in changes:
    print(f"   {c}")
print(f"   Größe: {len(content):,} bytes")
