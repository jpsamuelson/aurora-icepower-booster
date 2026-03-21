#!/usr/bin/env python3
"""
Strip all routing (segments + vias) from PCB.
Keeps footprints, zones (unfilled), edge cuts, etc.
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(PCB) as f:
    content = f.read()

orig_len = len(content)

# Count before
seg_count = len(re.findall(r'\n\t\(segment\b', content))
via_count = len(re.findall(r'\n\t\(via\b', content))
print(f"Before: {seg_count} segments, {via_count} vias")

# Remove all top-level (segment ...) blocks
# They are at indent level 1 (one tab)
lines = content.split('\n')
result_lines = []
skip_depth = 0
i = 0
while i < len(lines):
    stripped = lines[i].strip()
    if stripped == '(segment' or stripped.startswith('(segment ') or stripped == '(via' or stripped.startswith('(via '):
        # Check it's at top level (1 tab indent)
        if lines[i].startswith('\t') and not lines[i].startswith('\t\t'):
            # Skip this block — count brackets
            depth = 0
            while i < len(lines):
                for ch in lines[i]:
                    if ch == '(': depth += 1
                    elif ch == ')': depth -= 1
                if depth <= 0:
                    i += 1
                    break
                i += 1
            continue
    result_lines.append(lines[i])
    i += 1

content = '\n'.join(result_lines)

# Remove any empty line runs (more than 2 consecutive)
content = re.sub(r'\n{3,}', '\n\n', content)

# Count after
seg_after = len(re.findall(r'\n\t\(segment\b', content))
via_after = len(re.findall(r'\n\t\(via\b', content))
print(f"After:  {seg_after} segments, {via_after} vias")
print(f"Removed: {seg_count - seg_after} segments, {via_count - via_after} vias")

# Bracket balance
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket balance error: {depth}"
print(f"Bracket balance: OK")

with open(PCB, 'w') as f:
    f.write(content)

print(f"Size: {orig_len:,} → {len(content):,} bytes ({orig_len - len(content):,} removed)")
print("✅ Routing stripped")
