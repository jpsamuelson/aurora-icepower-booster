#!/usr/bin/env python3
"""Analyse der aktuellen Silk-Situation: was ist versteckt, was sichtbar."""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"
with open(PCB) as f:
    content = f.read()

# Finde alle property-Blöcke mit "Reference" und "Value"
ref_visible = 0
ref_hidden = 0
val_visible = 0
val_hidden = 0

# Simplified: count (hide yes) after (property "Reference" on SilkS
lines = content.split('\n')
i = 0
while i < len(lines):
    line = lines[i]
    if '(property "Reference"' in line:
        # Collect block
        depth = 0
        block = []
        j = i
        while j < len(lines):
            block.append(lines[j])
            for ch in lines[j]:
                if ch == '(':  depth += 1
                elif ch == ')': depth -= 1
            if depth <= 0: break
            j += 1
        blk = '\n'.join(block)
        if 'SilkS' in blk or 'Silkscreen' in blk:
            if '(hide yes)' in blk:
                ref_hidden += 1
            else:
                ref_visible += 1
        i = j + 1
        continue
    elif '(property "Value"' in line:
        depth = 0
        block = []
        j = i
        while j < len(lines):
            block.append(lines[j])
            for ch in lines[j]:
                if ch == '(':  depth += 1
                elif ch == ')': depth -= 1
            if depth <= 0: break
            j += 1
        blk = '\n'.join(block)
        if 'SilkS' in blk or 'Silkscreen' in blk:
            if '(hide yes)' in blk:
                val_hidden += 1
            else:
                val_visible += 1
        i = j + 1
        continue
    i += 1

print(f"Reference on Silk:  {ref_visible} sichtbar, {ref_hidden} versteckt")
print(f"Value on Silk:      {val_visible} sichtbar, {val_hidden} versteckt")

# Welche Layer haben die Reference-Texte?
ref_layers = {}
for m in re.finditer(r'\(property "Reference" "([^"]+)"[^)]*\n[^(]*\(layer "([^"]+)"\)', content):
    layer = m.group(2)
    ref_layers.setdefault(layer, []).append(m.group(1))
print(f"\nReference-Texte nach Layer:")
for layer, refs in sorted(ref_layers.items()):
    print(f"  {layer}: {len(refs)} refs")

# Connectors am Board-Edge (J9-J14) — Position prüfen
print(f"\nConnector-Positionen (J9-J14):")
for m in re.finditer(r'\(footprint "([^"]*)".*?\(at ([\d.+-]+) ([\d.+-]+)( [\d.+-]+)?\)', content, re.DOTALL):
    fp, x, y = m.group(1), float(m.group(2)), float(m.group(3))
    # Nur J9-J14 anzeigen
    ref_m = re.search(r'\(property "Reference" "([^"]+)"', m.group(0))
    if ref_m:
        ref = ref_m.group(1)
        if ref.startswith('J') and int(ref[1:]) >= 9:
            print(f"  {ref}: ({x}, {y}) — {fp}")
