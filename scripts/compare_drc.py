#!/usr/bin/env python3
"""Vergleich DRC vorher vs. nachher (Silk-Fix Delta)."""
import json
from collections import Counter

with open("/tmp/drc_before.json") as f:
    before = json.load(f)
with open("/tmp/drc_silk.json") as f:
    after = json.load(f)

before_v = before.get("violations", [])
after_v = after.get("violations", [])

before_types = Counter(v["type"] for v in before_v)
after_types = Counter(v["type"] for v in after_v)

all_types = sorted(set(list(before_types.keys()) + list(after_types.keys())))

print(f"{'Type':40s} {'Vorher':>8s} {'Nachher':>8s} {'Delta':>8s}")
print("-" * 70)
for t in all_types:
    b = before_types.get(t, 0)
    a = after_types.get(t, 0)
    delta = a - b
    marker = "" if delta == 0 else f" ← {'NEU' if delta > 0 else 'behoben'}"
    print(f"  {t:38s} {b:8d} {a:8d} {delta:+8d}{marker}")

print(f"\n  {'TOTAL':38s} {len(before_v):8d} {len(after_v):8d} {len(after_v)-len(before_v):+8d}")
print(f"  {'Unconnected':38s} {len(before.get('unconnected_items',[])):8d} {len(after.get('unconnected_items',[])):8d}")
