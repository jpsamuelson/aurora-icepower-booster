#!/usr/bin/env python3
"""
Phase 2: Deep investigation of failures from phase 1.
Analyzes the actual netlist to understand:
1. U1 (TEL5-2422) - all pins unconnected
2. U14 (ADP7118ARDZ) - pins misconnected
3. Signal chain driver mapping
4. Correct net names for V+, V-, +12V, -12V
5. ESD diode part names
"""

import re, os, json
from collections import defaultdict

NETLIST = "/tmp/revalidation_netlist.net"

with open(NETLIST, 'r') as f:
    content = f.read()

# ──────────────────────────────────────────────
# 1. All U1 pins and their nets
# ──────────────────────────────────────────────
print("=" * 70)
print("1. TEL5-2422 (U1) — Alle Pins und Netze")
print("=" * 70)

# Find all nets containing U1
for m in re.finditer(r'\(net\s+\(code\s+"?(\d+)"?\)\s*\(name\s+"([^"]*)"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
    code, name, body = m.groups()
    if '"U1"' in body:
        pins = re.findall(r'\(node\s+\(ref\s+"U1"\)\s*\(pin\s+"(\d+)"\)', body)
        print(f"  Net '{name}' (code {code}): U1 Pins = {pins}")

# ──────────────────────────────────────────────
# 2. All U14 pins and their nets
# ──────────────────────────────────────────────
print()
print("=" * 70)
print("2. ADP7118ARDZ (U14) — Alle Pins und Netze")
print("=" * 70)

for m in re.finditer(r'\(net\s+\(code\s+"?(\d+)"?\)\s*\(name\s+"([^"]*)"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
    code, name, body = m.groups()
    if '"U14"' in body:
        pins = re.findall(r'\(node\s+\(ref\s+"U14"\)\s*\(pin\s+"(\d+)"\)', body)
        print(f"  Net '{name}' (code {code}): U14 Pins = {pins}")

# ──────────────────────────────────────────────
# 3. Driver mapping: U7-U12 actual nets
# ──────────────────────────────────────────────
print()
print("=" * 70)
print("3. Balanced Driver (U7–U12) — Pin-Zuordnung")
print("=" * 70)

for u in range(7, 13):
    ref = f"U{u}"
    pin_nets = {}
    for m in re.finditer(r'\(net\s+\(code\s+"?(\d+)"?\)\s*\(name\s+"([^"]*)"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
        code, name, body = m.groups()
        for pm in re.finditer(rf'\(node\s+\(ref\s+"{ref}"\)\s*\(pin\s+"(\d+)"\)', body):
            pin_nets[pm.group(1)] = name
    
    print(f"\n  {ref}:")
    for pin in sorted(pin_nets.keys(), key=int):
        name = {
            "1": "OutA", "2": "InvA(-)", "3": "NinvA(+)", "4": "V-",
            "5": "NinvB(+)", "6": "InvB(-)", "7": "OutB", "8": "V+"
        }.get(pin, "???")
        print(f"    Pin{pin} ({name:10s}) = {pin_nets[pin]}")

# ──────────────────────────────────────────────
# 4. All net names containing key patterns
# ──────────────────────────────────────────────
print()
print("=" * 70)
print("4. Netz-Namensübersicht — Versorgung + Schlüssel-Netze")
print("=" * 70)

patterns = ["12V", "24V", "V+", "V-", "VCC", "VEE", "VOUT", "VIN", "EN_CTRL", "MUTE", "REMOTE"]
for pat in patterns:
    matches = re.findall(rf'\(name\s+"([^"]*{re.escape(pat)}[^"]*)"\)', content)
    if matches:
        print(f"  Muster '{pat}': {sorted(set(matches))}")

# ──────────────────────────────────────────────
# 5. Component parts (Dioden)
# ──────────────────────────────────────────────
print()
print("=" * 70)
print("5. Dioden-Bauteile im Netlist (D1–D25)")
print("=" * 70)

for m in re.finditer(r'\(comp\s+\(ref\s+"(D\d+)"\).*?\(value\s+"([^"]*)"\).*?\(libsource\s+\(lib\s+"([^"]*)"\)\s*\(part\s+"([^"]*)"\)', content, re.DOTALL):
    ref, val, lib, part = m.groups()
    print(f"  {ref}: value='{val}', lib='{lib}', part='{part}'")

# ──────────────────────────────────────────────
# 6. XLR output mapping: which outputs go where
# ──────────────────────────────────────────────
print()
print("=" * 70)
print("6. XLR-Ausgang / Balanced Driver Verbindungskette")
print("=" * 70)

# For each CHx, trace: Driver Out → Serien-R (47Ω) → XLR
for ch in range(1, 7):
    out_hot = f"/CH{ch}_OUT_HOT"
    out_cold = f"/CH{ch}_OUT_COLD"
    buf_drive = f"/CH{ch}_BUF_DRIVE"
    out_drive = f"/CH{ch}_OUT_DRIVE"
    
    for net_name in [buf_drive, out_drive, out_hot, out_cold]:
        pins = []
        for m in re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"' + re.escape(net_name) + r'"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
            body = m.group(1)
            pins = re.findall(r'\(node\s+\(ref\s+"([^"]*)"\)\s*\(pin\s+"([^"]*)"\)', body)
        if pins:
            print(f"  CH{ch} {net_name}: {[f'{r}.{p}' for r, p in pins]}")

# ──────────────────────────────────────────────
# 7. U1 / U14 unconnected pin investigation
# ──────────────────────────────────────────────
print()
print("=" * 70)
print("7. Unverbundene U1/U14 Pins — Details")
print("=" * 70)

unconnected = []
for m in re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"(unconnected-[^"]*)"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
    name, body = m.groups()
    pins = re.findall(r'\(node\s+\(ref\s+"([^"]*)"\)\s*\(pin\s+"([^"]*)"\)', body)
    for r, p in pins:
        if r in ["U1", "U14"]:
            # Extract pin function from unconnected name
            func = re.search(r'unconnected-\(' + r + r'-(.+?)-Pad\d+\)', name)
            func_name = func.group(1) if func else "???"
            unconnected.append((r, p, func_name, name))
            
unconnected.sort(key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else 0))
for ref, pin, func, name in unconnected:
    print(f"  {ref}.Pin{pin:2s} ({func:15s}) = '{name}'")

# ──────────────────────────────────────────────
# 8. +24V_IN net (what's connected to barrel jack?)
# ──────────────────────────────────────────────
print()
print("=" * 70) 
print("8. Barrel Jack (J1) + 24V-Kette")
print("=" * 70)

j1_pins = {}
for m in re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
    name, body = m.groups()
    for pm in re.finditer(r'\(node\s+\(ref\s+"J1"\)\s*\(pin\s+"(\d+)"\)', body):
        j1_pins[pm.group(1)] = name

print(f"  J1.Pin1 = {j1_pins.get('1', 'NOT FOUND')}")
print(f"  J1.Pin2 = {j1_pins.get('2', 'NOT FOUND')}")

# Check +24V net
for m in re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"/\+24V_IN"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
    body = m.group(1)
    pins = re.findall(r'\(node\s+\(ref\s+"([^"]*)"\)\s*\(pin\s+"([^"]*)"\)', body)
    print(f"  /+24V_IN: {[f'{r}.{p}' for r, p in pins]}")

# ──────────────────────────────────────────────
# 9. +12V, -12V nets (what's on them?)
# ──────────────────────────────────────────────
print()
print("=" * 70)
print("9. ±12V Schienen")
print("=" * 70)

for search_name in ["/+12V", "/-12V"]:
    for m in re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"' + re.escape(search_name) + r'"\)(.*?)\)\s*(?=\(net|\Z)', content, re.DOTALL):
        body = m.group(1)
        pins = re.findall(r'\(node\s+\(ref\s+"([^"]*)"\)\s*\(pin\s+"([^"]*)"\)', body)
        print(f"  {search_name}: {[f'{r}.{p}' for r, p in pins]}")

print("\nDone.")
