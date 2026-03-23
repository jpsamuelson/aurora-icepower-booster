#!/usr/bin/env python3
"""Analyze gr_text in fa39dd8 base commit."""
import re

with open("/tmp/pcb_fa39dd8.kicad_pcb") as f:
    text = f.read()

for m in re.finditer(r'\(gr_text\s+"([^"]{1,80})', text):
    t = m.group(1)
    rest = text[m.end():m.end()+300]
    at = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)', rest)
    layer = re.search(r'\(layer\s+"([^"]+)"', rest)
    pos = f'({at.group(1)}, {at.group(2)})' if at else '?'
    ly = layer.group(1) if layer else '?'
    print(f'  [{ly}] at {pos}: "{t[:60]}"')

print()
print(f'Gain table: {"GAIN (dB)" in text}')
print(f'Switch desc: {"ON ↑" in text}')
print(f'Rev 1.0: {"Rev 1.0" in text}')
print(f'Aurora DSP: {"Aurora DSP IcePower Booster" in text}')

at_match = re.search(r'Balanced Booster.*?\(at\s+([\d.]+)\s+([\d.]+)', text, re.DOTALL)
print(f'Balanced Booster at: ({at_match.group(1)}, {at_match.group(2)})' if at_match else 'not found')

# Also check SW2 reference position
sw2_match = re.search(r'\(footprint\b.*?"Reference"\s+"SW2"', text, re.DOTALL)
if sw2_match:
    # Find property Reference block
    rest2 = text[sw2_match.start():sw2_match.start()+5000]
    ref_at = re.search(r'"Reference"\s+"SW2"\s*\(at\s+([\d.-]+)\s+([\d.-]+)', rest2)
    if ref_at:
        print(f'SW2 Reference at: ({ref_at.group(1)}, {ref_at.group(2)})')
