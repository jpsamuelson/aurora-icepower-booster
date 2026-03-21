#!/usr/bin/env python3
"""Move C79 to clear both U1 and U15 courtyards, then strip for final re-route."""
import re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')

with open(PCB_FILE) as f:
    text = f.read()

def find_footprint_block(text, ref):
    for pattern in [f'(property "Reference" "{ref}"', f'fp_text reference "{ref}"']:
        idx = text.find(pattern)
        if idx >= 0: break
    else:
        return None, None
    depth = 0; start = idx
    while start > 0:
        if text[start] == ')': depth += 1
        elif text[start] == '(':
            depth -= 1
            if depth < 0 and ('(footprint ' in text[start:start+20] or '(footprint\n' in text[start:start+20]):
                break
        start -= 1
    depth = 0; end = start
    while end < len(text):
        if text[end] == '(': depth += 1
        elif text[end] == ')':
            depth -= 1
            if depth == 0: end += 1; break
        end += 1
    return start, end

# C79 needs to go right of U1 (courtyard ends at x=137.43)
# Move to x=139, y=22, keep 90° rotation
start, end = find_footprint_block(text, 'C79')
block = text[start:end]
m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
old_x, old_y = float(m.group(1)), float(m.group(2))
angle_str = f' {m.group(3)}' if m.group(3) else ''
new_at = f'(at 139 22{angle_str})'
new_block = block.replace(m.group(0), new_at, 1)
text = text[:start] + new_block + text[end:]
print(f"C79: ({old_x}, {old_y}) -> (139, 22)")

# Strip all traces, vias, and zone fills
def remove_balanced_blocks(text, keyword):
    result = []; i = 0; removed = 0
    kw_paren = '(' + keyword; kw_len = len(kw_paren)
    while i < len(text):
        if (text[i] == '(' and text[i:i+kw_len] == kw_paren
                and (i + kw_len >= len(text) or not text[i+kw_len].isalnum())):
            depth = 0; j = i
            while j < len(text):
                if text[j] == '(': depth += 1
                elif text[j] == ')':
                    depth -= 1
                    if depth == 0: break
                j += 1
            i = j + 1
            while i < len(text) and text[i] in ' \t\n\r': i += 1
            removed += 1
        else:
            result.append(text[i]); i += 1
    return ''.join(result), removed

text, seg = remove_balanced_blocks(text, 'segment')
text, via = remove_balanced_blocks(text, 'via')
text, fp = remove_balanced_blocks(text, 'filled_polygon')
print(f"Stripped: {seg} segments, {via} vias, {fp} filled_polygons")

depth = 0
for ch in text:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"

with open(PCB_FILE, 'w') as f:
    f.write(text)
print(f"Written: {len(text)} bytes")
