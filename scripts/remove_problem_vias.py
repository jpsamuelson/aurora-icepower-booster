#!/usr/bin/env python3
"""Remove problematic vias:
1. GND via at (12.5, 2.5) — shorts with J15 Pad2
2. REMOTE_IN via at (22.5, 2.5) — dangling, old routing
"""
import re

PCB = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

# Vias to remove: (x, y, net_name) with tolerance
VIAS_TO_REMOVE = [
    (12.5, 2.5, "GND"),
    (22.5, 2.5, "/REMOTE_IN"),
]

with open(PCB, "r") as f:
    lines = f.readlines()

removed = 0
new_lines = []
skip_until_close = False
skip_depth = 0

i = 0
while i < len(lines):
    line = lines[i]
    
    if not skip_until_close:
        # Check if this line starts a via block
        if line.strip().startswith("(via "):
            # Collect the full via block (may span multiple lines but usually 1)
            via_text = line
            depth = line.count("(") - line.count(")")
            j = i + 1
            while depth > 0 and j < len(lines):
                via_text += lines[j]
                depth += lines[j].count("(") - lines[j].count(")")
                j += 1
            
            # Check if this via matches any of our targets
            should_remove = False
            for vx, vy, vnet in VIAS_TO_REMOVE:
                # Match position
                at_match = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)\)', via_text)
                if at_match:
                    x = float(at_match.group(1))
                    y = float(at_match.group(2))
                    if abs(x - vx) < 0.1 and abs(y - vy) < 0.1:
                        # Check net
                        net_match = re.search(r'\(net\s+\d+\s+"([^"]+)"\)', via_text)
                        if net_match and net_match.group(1) == vnet:
                            should_remove = True
                            print(f"Removing via: net={vnet} at ({x}, {y})")
                            break
            
            if should_remove:
                removed += 1
                i = j  # Skip the entire via block
                continue
            else:
                new_lines.append(line)
                i += 1
                continue
        else:
            new_lines.append(line)
            i += 1
    else:
        i += 1

print(f"\nRemoved {removed}/{len(VIAS_TO_REMOVE)} vias")

if removed > 0:
    with open(PCB, "w") as f:
        f.writelines(new_lines)
    
    # Verify bracket balance
    text = "".join(new_lines)
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
    print(f"Bracket balance: {depth}")
    print("Written to PCB.")
else:
    print("No vias found to remove!")
