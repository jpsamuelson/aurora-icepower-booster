#!/usr/bin/env python3
"""Analyze shorts and dangling vias in detail."""
import json

with open("/tmp/drc_fixed.json") as f:
    d = json.load(f)

print("=== SHORTS ===")
for v in d.get("violations", []):
    if v.get("type") == "shorting_items":
        print(f"  {v.get('description', '')}")
        for it in v.get("items", []):
            desc = it.get("description", "")
            pos = it.get("pos", {})
            print(f"    {desc} at ({pos.get('x','?')}, {pos.get('y','?')})")

print("\n=== DANGLING VIAS ===")
for v in d.get("violations", []):
    if v.get("type") == "via_dangling":
        print(f"  {v.get('description', '')}")
        for it in v.get("items", []):
            desc = it.get("description", "")
            pos = it.get("pos", {})
            print(f"    {desc} at ({pos.get('x','?')}, {pos.get('y','?')})")

print("\n=== CLEARANCE ===")
for v in d.get("violations", []):
    if v.get("type") == "clearance":
        print(f"  {v.get('description', '')}")
        for it in v.get("items", []):
            desc = it.get("description", "")
            pos = it.get("pos", {})
            print(f"    {desc} at ({pos.get('x','?')}, {pos.get('y','?')})")

print("\n=== REAL UNCONNECTED (not zone fill) ===")
for u in d.get("unconnected_items", []):
    desc = u.get("description", "")
    if "zone" not in desc.lower():
        items = u.get("items", [])
        i_descs = [(i.get("description",""), i.get("pos",{})) for i in items]
        print(f"  {desc}")
        for id, ip in i_descs:
            print(f"    {id} at ({ip.get('x','?')}, {ip.get('y','?')})")
