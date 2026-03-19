#!/usr/bin/env python3
"""Analyse aller 13 ERC-Errors + 5 relevanter Warnings im Detail."""

import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, "r") as f:
    text = f.read()

# Helper: extract symbol block by reference
def find_symbol_by_ref(ref):
    """Find schematic symbol block by Reference value."""
    # Look for (property "Reference" "ref" ...)
    pattern = rf'\(symbol\s+\(lib_id\s+"[^"]+"\)\s+\(at\s+[\d.\-\s]+\)'
    results = []
    for m in re.finditer(r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
        lib_id = m.group(1)
        x, y, rot = m.group(2), m.group(3), m.group(4)
        start = m.start()
        # Find the Reference property in this symbol
        # Look forward from start, but limit search
        chunk = text[start:start+3000]
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
        if ref_m and ref_m.group(1) == ref:
            # Find the Value property
            val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', chunk)
            value = val_m.group(1) if val_m else "?"
            # Find the Footprint
            fp_m = re.search(r'\(property\s+"Footprint"\s+"([^"]*)"', chunk)
            footprint = fp_m.group(1) if fp_m else "?"
            results.append({
                'ref': ref,
                'lib_id': lib_id,
                'x': float(x),
                'y': float(y),
                'rot': int(rot),
                'value': value,
                'footprint': footprint,
                'start': start
            })
    return results

print("=" * 70)
print("DETAILANALYSIS ALLER 13 ERC-ERRORS + 5 WARNINGS")
print("=" * 70)

# ===== GROUP 1: #PWR pin_not_connected (7 errors) =====
print("\n" + "=" * 70)
print("GRUPPE 1: #PWR Pin nicht verbunden (7 Errors)")
print("=" * 70)
pwr_refs = ['#PWR063', '#PWR014', '#PWR083', '#PWR005', '#PWR088', '#PWR028', '#PWR037']
for ref in pwr_refs:
    syms = find_symbol_by_ref(ref)
    if syms:
        s = syms[0]
        print(f"\n  {ref}: lib_id={s['lib_id']}, value={s['value']}")
        print(f"    Position: ({s['x']}, {s['y']}), Rotation: {s['rot']}°")
        # Check if there's a wire near this symbol
        # Look for nearby wires
        chunk = text[max(0,s['start']-500):s['start']+3000]
        # Check pin connections - look for net labels nearby
    else:
        print(f"\n  {ref}: NICHT GEFUNDEN im Schaltplan!")

# ===== GROUP 2: pin_to_pin U1 (Error 2) =====
print("\n" + "=" * 70)
print("GRUPPE 2: U1 Pin 2 ↔ Pin 3 pin_to_pin (1 Error)")
print("=" * 70)
u1 = find_symbol_by_ref('U1')
if u1:
    s = u1[0]
    print(f"  U1: lib_id={s['lib_id']}, value={s['value']}")
    print(f"  Position: ({s['x']}, {s['y']})")
    print(f"  Pin 2 + Pin 3 sind beide 'Power output' Typ und am selben Netz")
    print(f"  → Beide sind -VIN(GND) = Eingangs-Minus des DC/DC-Wandlers")

# ===== GROUP 3: #PWR001 power_pin_not_driven (Error 3) =====
print("\n" + "=" * 70)
print("GRUPPE 3: #PWR001 power_pin_not_driven (1 Error)")
print("=" * 70)
pwr001 = find_symbol_by_ref('#PWR001')
if pwr001:
    s = pwr001[0]
    print(f"  #PWR001: lib_id={s['lib_id']}, value={s['value']}")
    print(f"  Position: ({s['x']}, {s['y']})")

# ===== GROUP 4: U14 SS pin (Errors 4+5) =====
print("\n" + "=" * 70)
print("GRUPPE 4: U14 Pin 6 (SS) + SS_U14 Label (2 Errors)")
print("=" * 70)
u14 = find_symbol_by_ref('U14')
if u14:
    s = u14[0]
    print(f"  U14: lib_id={s['lib_id']}, value={s['value']}")
    print(f"  Position: ({s['x']}, {s['y']})")
    print(f"  Pin 6 = SS (Soft-Start), Typ: Input")
    print(f"  Label SS_U14 ist gesetzt aber 'dangling' laut ERC")

# ===== GROUP 5: C22 Pin 1 (Error 6) =====
print("\n" + "=" * 70)
print("GRUPPE 5: C22 Pin 1 nicht verbunden (1 Error)")
print("=" * 70)
c22 = find_symbol_by_ref('C22')
if c22:
    s = c22[0]
    print(f"  C22: lib_id={s['lib_id']}, value={s['value']}")
    print(f"  Position: ({s['x']}, {s['y']})")
    print(f"  Footprint: {s['footprint']}")

# ===== GROUP 6: U14 Pin 1 ↔ Pin 2 pin_to_pin (Error 7) =====
print("\n" + "=" * 70)
print("GRUPPE 6: U14 Pin 1 ↔ Pin 2 pin_to_pin (1 Error)")
print("=" * 70)
if u14:
    s = u14[0]
    print(f"  U14: Pin 1 + Pin 2 sind beide 'VOUT, Power output' Typ")
    print(f"  → Parallele Output-Pins am selben Netz /V+")

# ===== WARNINGS =====
print("\n" + "=" * 70)
print("WARNINGS (nicht off-grid)")
print("=" * 70)

# W1+W4: lib_symbol_mismatch
print("\n  W1: TEL5-2422 lib_symbol_mismatch")
print("    U1 Symbol-Cache ≠ Library-Symbol (wir haben Cache manuell editiert)")

print("\n  W4: ADP7118ARDZ lib_symbol_mismatch")
print("    U14 Symbol-Cache ≠ Library-Symbol (wir haben Cache manuell editiert)")

# W2+W3: U1 pin_to_pin (warnings)
print("\n  W2: U1 Pin 16 (COMMON, Unspecified) ↔ #PWR122 (Power input)")
print("    Pin-Typ 'Unspecified' verbunden mit Power-Pin")

print("\n  W3: U1 Pin 9 (COMMON) ↔ Pin 16 (COMMON) — beide Unspecified")
print("    Zwei 'Unspecified' Pins am selben Netz")

# W5: unconnected_wire_endpoint
print("\n  W5: Unconnected wire endpoint (0.0238 mm kurzer Wire)")

# ===== NETLIST CHECK =====
print("\n" + "=" * 70)
print("NETLIST-KONTEXT")
print("=" * 70)

# Read netlist
with open("/tmp/revalidation_netlist.net", "r") as f:
    netlist = f.read()

# Check what net C22 is on
c22_nets = re.findall(r'\(comp \(ref "C22"\).*?\)\s*\)', netlist, re.DOTALL)
if c22_nets:
    print(f"\n  C22 in netlist: {c22_nets[0][:300]}")

# Check SS_U14 net
ss_net = re.findall(r'\(net.*?SS_U14.*?\)', netlist, re.DOTALL)
print(f"\n  SS_U14 Netz in Netlist: {len(ss_net)} Treffer")
for n in ss_net[:3]:
    print(f"    {n[:200]}")

# Check #PWR symbols in netlist
pwr_in_netlist = re.findall(r'\(comp \(ref "#PWR\d+"\).*?\)\s*\)', netlist, re.DOTALL)
print(f"\n  #PWR Symbole in Netlist: {len(pwr_in_netlist)}")

# Specifically check the problematic ones
for ref in ['#PWR063', '#PWR001', '#PWR014', '#PWR083', '#PWR005', '#PWR088', '#PWR028', '#PWR037']:
    found = re.findall(rf'\(comp \(ref "{re.escape(ref)}"\).*?\)\s*\)', netlist, re.DOTALL)
    if found:
        val = re.search(r'\(value "([^"]+)"', found[0])
        fp = re.search(r'\(footprint "([^"]*)"', found[0])
        print(f"    {ref}: value={val.group(1) if val else '?'}, fp={fp.group(1) if fp else '?'}")

# Check which nets these #PWR are on
print("\n  #PWR Netz-Zuordnungen:")
for ref in ['#PWR063', '#PWR001', '#PWR014', '#PWR083', '#PWR005', '#PWR088', '#PWR028', '#PWR037']:
    # Search in nets section
    pattern = rf'\(node \(ref "{re.escape(ref)}"\)\s+\(pin "(\d+)"\)'
    nodes = re.findall(pattern, netlist)
    if nodes:
        # Find which net contains this node
        for net_m in re.finditer(r'\(net \(code "(\d+)"\) \(name "([^"]*)".*?\)\)', netlist, re.DOTALL):
            net_text = net_m.group(0)
            if ref in net_text:
                print(f"    {ref}: Netz '{net_m.group(2)}' (Code {net_m.group(1)})")
                break
    else:
        print(f"    {ref}: KEIN Netz gefunden (unconnected)")

print("\n" + "=" * 70)
print("ZUSAMMENFASSUNG")
print("=" * 70)
print("""
ERRORS (13):
  Typ A: 7× #PWR pin_not_connected  → Power-Symbole ohne Wire-Verbindung
  Typ B: 2× pin_to_pin              → Parallele Output-Pins (U1:2↔3, U14:1↔2)
  Typ C: 1× power_pin_not_driven    → #PWR001 Power-Input ohne Treiber
  Typ D: 1× pin_not_driven          → U14 Pin 6 (SS) ohne Eingangs-Treiber
  Typ E: 1× label_dangling          → SS_U14 Label nicht verbunden
  Typ F: 1× pin_not_connected       → C22 Pin 1 Kondensator-Pin offen

WARNINGS (5, excl. off-grid):
  Typ G: 2× lib_symbol_mismatch     → U1/U14 Cache ≠ Library
  Typ H: 2× pin_to_pin (warning)    → U1 COMMON/Power Pin-Typ-Mismatch
  Typ I: 1× unconnected_wire_endpoint → Kurzes Wire-Fragment
""")
