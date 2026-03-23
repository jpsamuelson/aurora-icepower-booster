#!/usr/bin/env python3
"""Analyze DRC JSON output."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/drc_j15_v2.json"

with open(path) as f:
    d = json.load(f)

types = {}
for v in d.get("violations", []):
    t = v.get("type", "unknown")
    types[t] = types.get(t, 0) + 1

print("=== Violation types ===")
for t, c in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {c:3d}x {t}")

# Check for shorts
shorts = [v for v in d.get("violations", []) if v.get("type") == "shorting_items"]
if shorts:
    print("\n=== SHORTS (BAD!) ===")
    for s in shorts:
        print(f"  {s.get('description', '')}")
        for it in s.get("items", []):
            print(f"    {it.get('description', '')}")
else:
    print("\n=== No shorts! ===")

# Unconnected summary
uncon = d.get("unconnected_items", [])
utypes = set()
for u in uncon:
    utypes.add(u.get("type", ""))
print(f"\n=== {len(uncon)} unconnected ({utypes}) ===")
