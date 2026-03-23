#!/usr/bin/env python3
"""Analyze silk violations from DRC results."""
import json, re, sys
from collections import Counter

drc_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/drc_silk_v31.json"
with open(drc_file) as f:
    data = json.load(f)

def extract_refs(violations, vtype):
    refs = []
    for v in violations:
        if v["type"] != vtype:
            continue
        for item in v.get("items", []):
            d = item.get("description", "")
            # Format: "Reference field of C30" or '"C30"'
            m = re.search(r'of ([A-Z]+\d+)', d) or re.search(r'"([A-Z]+\d+)"', d)
            if m:
                refs.append(m.group(1))
    return Counter(refs)

violations = data.get("violations", [])
types = Counter(v["type"] for v in violations)
print("=== Type breakdown:")
for t, c in types.most_common():
    print(f"  {t}: {c}")
print(f"  Total: {sum(types.values())}")
print(f"  Unconnected: {len(data.get('unconnected_items', []))}")

soc = extract_refs(violations, "silk_over_copper")
sol = extract_refs(violations, "silk_overlap")

print("=== silk_over_copper (87) - Affected Refs:")
for r, c in sorted(soc.items()):
    print(f"  {r}: {c}")
print(f"  Unique refs: {len(soc)}")

print()
print("=== silk_overlap (21) - Affected Refs:")
for r, c in sorted(sol.items()):
    print(f"  {r}: {c}")
print(f"  Unique refs: {len(sol)}")

# Check if silk_over_copper involves own pads or other pads
print()
print("=== silk_over_copper - Full details (first 15):")
count = 0
for v in violations:
    if v["type"] != "silk_over_copper":
        continue
    if count >= 15:
        break
    count += 1
    print(f"  Type: {v['type']}")
    for item in v.get("items", []):
        desc = item.get("description", "")
        pos = item.get("pos", {})
        x = pos.get("x", "?")
        y = pos.get("y", "?")
        print(f"    [{x}, {y}] {desc}")
    print()
