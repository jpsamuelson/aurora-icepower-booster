#!/usr/bin/env python3
"""Fix F1: Netclass patterns — add / prefix and verify matching."""
import json, re, fnmatch

PRO = "aurora-dsp-icepower-booster.kicad_pro"
PCB = "aurora-dsp-icepower-booster.kicad_pcb"

# Get actual net names from PCB
with open(PCB) as f:
    pcb = f.read()
net_names = set()
for m in re.finditer(r'\(net \d+ "([^"]*)"\)', pcb):
    if m.group(1):
        net_names.add(m.group(1))

# Load project
with open(PRO) as f:
    pro = json.load(f)

patterns = pro.get("net_settings", {}).get("netclass_patterns", []) or []

# Test current patterns
print("=== Aktuell: Pattern-Matching ===")
matched = set()
unmatched_nets = set()
for net in sorted(net_names):
    found = False
    for p in patterns:
        if fnmatch.fnmatch(net, p["pattern"]):
            found = True
            matched.add(net)
            break
    if not found:
        unmatched_nets.add(net)

print(f"  Matched: {len(matched)}/{len(net_names)}")
print(f"  Unmatched: {len(unmatched_nets)}")
for n in sorted(unmatched_nets):
    print(f"    {n}")

# Fix: Add / prefix to patterns
print("\n=== Fix: Patterns mit / Prefix ===")
new_patterns = []
for p in patterns:
    old = p["pattern"]
    # KiCad 9 net names start with / — add it to pattern
    new_pat = "/" + old if not old.startswith("/") else old
    new_patterns.append({"netclass": p["netclass"], "pattern": new_pat})
    if old != new_pat:
        print(f"  {p['netclass']:15s} {old:25s} -> {new_pat}")

# Test new patterns
print("\n=== Nach Fix: Pattern-Matching ===")
matched2 = set()
unmatched2 = set()
for net in sorted(net_names):
    found = False
    for p in new_patterns:
        if fnmatch.fnmatch(net, p["pattern"]):
            found = True
            matched2.add(net)
            break
    if not found:
        unmatched2.add(net)

print(f"  Matched: {len(matched2)}/{len(net_names)}")
print(f"  Unmatched: {len(unmatched2)}")

# Show class distribution
from collections import Counter
class_count = Counter()
for net in net_names:
    for p in new_patterns:
        if fnmatch.fnmatch(net, p["pattern"]):
            class_count[p["netclass"]] += 1
            break
    else:
        class_count["Default"] += 1

print("\n  Netzklassen-Verteilung:")
for nc, count in class_count.most_common():
    print(f"    {nc:15s}: {count} Netze")

# Check remaining unmatched
if unmatched2:
    print("\n  Verbleibende ungematchte Netze:")
    for n in sorted(unmatched2):
        print(f"    {n}")

# Apply fix
pro["net_settings"]["netclass_patterns"] = new_patterns
with open(PRO, "w") as f:
    json.dump(pro, f, indent=2)
    f.write("\n")

print(f"\n=== {PRO} aktualisiert — {len(new_patterns)} Patterns gefixt ===")
