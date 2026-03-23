#!/usr/bin/env python3
"""Analyze differences between committed PCB (fa39dd8) and user's backup PCB.

Finds: 3D model changes, silkscreen text changes, footprint modifications.
"""
import re
import subprocess
import sys

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout

# Get full diff
diff = run("diff -u /tmp/kicad-committed.kicad_pcb /tmp/kicad-backup/aurora-dsp-icepower-booster.kicad_pcb")

# Parse hunks
hunks = []
current_hunk = None
for line in diff.splitlines():
    if line.startswith("@@"):
        if current_hunk:
            hunks.append(current_hunk)
        current_hunk = {"header": line, "minus": [], "plus": [], "context": []}
    elif current_hunk:
        if line.startswith("-") and not line.startswith("---"):
            current_hunk["minus"].append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            current_hunk["plus"].append(line[1:])
        else:
            current_hunk["context"].append(line)
if current_hunk:
    hunks.append(current_hunk)

print(f"Total hunks: {len(hunks)}")
print()

# Categorize hunks
model_hunks = []
silk_hunks = []
text_hunks = []
other_hunks = []

for h in hunks:
    all_lines = " ".join(h["minus"] + h["plus"] + h["context"])
    if "model" in all_lines.lower() or "3dshapes" in all_lines or "xyz" in all_lines:
        model_hunks.append(h)
    elif "SilkS" in all_lines or "gr_text" in all_lines or "fp_text" in all_lines:
        silk_hunks.append(h)
    elif "uuid" in all_lines.lower() and len(h["minus"]) <= 1 and len(h["plus"]) <= 1:
        pass  # Skip UUID-only changes
    else:
        other_hunks.append(h)

print(f"=== 3D Model changes: {len(model_hunks)} hunks ===")
for h in model_hunks:
    minus_text = "\n".join(h["minus"])
    plus_text = "\n".join(h["plus"])
    # Find component context
    context = "\n".join(h["context"])
    ref_match = re.search(r'"Reference"\s+"([^"]+)"', context)
    ref = ref_match.group(1) if ref_match else "?"
    
    # Find model paths
    old_models = re.findall(r'model\s+"([^"]+)"', minus_text)
    new_models = re.findall(r'model\s+"([^"]+)"', plus_text)
    old_offsets = re.findall(r'xyz\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)', minus_text)
    new_offsets = re.findall(r'xyz\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)', plus_text)
    
    print(f"\n  Hunk near {ref}:")
    if old_models:
        print(f"    Old model: {old_models}")
    if new_models:
        print(f"    New model: {new_models}")
    if old_offsets:
        print(f"    Old offset/scale/rot: {old_offsets}")
    if new_offsets:
        print(f"    New offset/scale/rot: {new_offsets}")
    if not old_models and not new_models:
        print(f"    Minus: {h['minus'][:5]}")
        print(f"    Plus:  {h['plus'][:5]}")

print(f"\n=== Silkscreen/Text changes: {len(silk_hunks)} hunks ===")
for h in silk_hunks:
    minus_text = "\n".join(h["minus"])
    plus_text = "\n".join(h["plus"])
    
    # Compact view
    m_lines = [l.strip() for l in h["minus"] if l.strip()]
    p_lines = [l.strip() for l in h["plus"] if l.strip()]
    
    print(f"\n  Hunk {h['header'][:60]}:")
    for l in m_lines[:10]:
        print(f"    - {l}")
    for l in p_lines[:10]:
        print(f"    + {l}")

print(f"\n=== Other changes: {len(other_hunks)} hunks ===")
for h in other_hunks:
    m_lines = [l.strip() for l in h["minus"] if l.strip()]
    p_lines = [l.strip() for l in h["plus"] if l.strip()]
    if m_lines or p_lines:
        print(f"\n  Hunk {h['header'][:60]}:")
        for l in m_lines[:5]:
            print(f"    - {l}")
        for l in p_lines[:5]:
            print(f"    + {l}")
