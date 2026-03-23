#!/usr/bin/env python3
"""Fix GND pattern — GND has no / prefix in PCB net names."""
import json

PRO = "aurora-dsp-icepower-booster.kicad_pro"

with open(PRO) as f:
    pro = json.load(f)

patterns = pro["net_settings"]["netclass_patterns"]

# Fix: GND pattern should also match without /
# Replace /GND with GND (no prefix) since net name is "GND" not "/GND"
fixed = 0
for p in patterns:
    if p["pattern"] == "/GND":
        p["pattern"] = "GND"
        print(f"Fixed: /GND -> GND")
        fixed += 1

if fixed == 0:
    print("GND pattern not found — skipping")

with open(PRO, "w") as f:
    json.dump(pro, f, indent=2)
    f.write("\n")

print(f"Done, {fixed} pattern(s) fixed")
