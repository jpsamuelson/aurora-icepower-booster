#!/usr/bin/env python3
"""Check coordinate systems of reference fields in PCB footprints."""
import re

with open('aurora-dsp-icepower-booster.kicad_pcb') as f:
    text = f.read()

for ref_name in ['R1', 'C1', 'R82', 'J9', 'C16', 'MH1', 'C80']:
    pat = r'\(footprint\s+"([^"]+)"[^)]*\(at\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?\)'
    for m in re.finditer(pat, text):
        start = m.start()
        depth = 0
        i = start
        while i < len(text):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = text[start:i+1]
        ref_match = re.search(r'\(property\s+"Reference"\s+"' + ref_name + '"', block)
        if ref_match:
            fp_name = m.group(1)
            fp_x, fp_y = m.group(2), m.group(3)
            fp_rot = m.group(4) or '0'
            ref_at = re.search(
                r'\(property\s+"Reference"\s+"' + ref_name + r'"[^)]*\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)',
                block
            )
            if ref_at:
                rx, ry = ref_at.group(1), ref_at.group(2)
                ra = ref_at.group(3) or '0'
                print(f'{ref_name}: fp={fp_name} fp_pos=({fp_x},{fp_y}) fp_rot={fp_rot} ref_local=({rx},{ry}) ref_rot={ra}')
            break
