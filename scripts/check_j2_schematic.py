#!/usr/bin/env python3
"""Extrahiere J2-Symbol und Pin-Details aus dem Schaltplan."""

import re

sch_path = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(sch_path, "r") as f:
    sch = f.read()

# Finde J2 - rückwärts zum Symbol-Start
j2_pos = sch.find('"J2"')
search_start = max(0, j2_pos - 3000)
segment = sch[search_start:j2_pos]

# Finde letzten (symbol vor J2
sym_starts = [m.start() for m in re.finditer(r'\(symbol \(lib_id', segment)]
if not sym_starts:
    print("Kein Symbol gefunden, versuche andere Suche...")
    sym_starts = [m.start() for m in re.finditer(r'\(symbol', segment)]

sym_abs_start = search_start + sym_starts[-1]

# Vorwärts: Klammer-Balance
depth = 0
sym_end = sym_abs_start
for i in range(sym_abs_start, min(sym_abs_start + 5000, len(sch))):
    if sch[i] == '(':
        depth += 1
    elif sch[i] == ')':
        depth -= 1
        if depth == 0:
            sym_end = i + 1
            break

sym_block = sch[sym_abs_start:sym_end]

# Extrahiere lib_id
lib_id = re.search(r'lib_id "([^"]+)"', sym_block)
print(f"J2 Symbol: {lib_id.group(1) if lib_id else 'UNKNOWN'}")

# Extrahiere Value
value = re.search(r'"Value" "([^"]+)"', sym_block)
print(f"J2 Value: {value.group(1) if value else 'UNKNOWN'}")

# Extrahiere Footprint
fp = re.search(r'"Footprint" "([^"]+)"', sym_block)
print(f"J2 Footprint: {fp.group(1) if fp else 'UNKNOWN'}")

# Suche nach Pin-Infos in lib_symbols cache
print("\n=== lib_symbols Cache für J2 ===")
# Finde das passende lib_symbols Entry
if lib_id:
    lib_name = lib_id.group(1)
    # Suche in lib_symbols
    cache_pos = sch.find(f'(symbol "{lib_name}"')
    if cache_pos >= 0 and cache_pos < sch.find('(symbol (lib_id'):
        # Finde Ende des Cache-Symbols
        depth = 0
        cache_end = cache_pos
        for i in range(cache_pos, min(cache_pos + 5000, len(sch))):
            if sch[i] == '(':
                depth += 1
            elif sch[i] == ')':
                depth -= 1
                if depth == 0:
                    cache_end = i + 1
                    break
        
        cache_block = sch[cache_pos:cache_end]
        
        # Extrahiere Pins
        pins = re.findall(r'\(pin (\w+) (\w+) \(at ([^)]+)\).*?\(name "([^"]*)"', cache_block)
        print(f"\nPins ({len(pins)}):")
        for ptype, pstyle, pos, name in pins:
            print(f"  {name:<10} Type: {ptype:<12} Pos: ({pos})")
    else:
        print("Cache-Symbol nicht gefunden")

# Prüfe auch Netz-Verbindungen für J2
print("\n=== J2 Netz-Verbindungen ===")
# Suche nach Netzen die J2 enthalten
nets = re.findall(r'net "([^"]*)"[^)]*"J2"', sch[:2000])
if not nets:
    # Alternative Suche in der Netlist
    net_path = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.net"
    try:
        with open(net_path, "r") as f:
            net_content = f.read()
        # Finde alle Netze mit J2
        j2_nets = re.findall(r'\(net \(code \d+\) \(name "([^"]+)"\).*?\(ref "J2"\) \(pin "([^"]+)"\)', net_content, re.DOTALL)
        if j2_nets:
            for net_name, pin_name in j2_nets:
                print(f"  Pin {pin_name} → Netz: {net_name}")
        else:
            # Suche anders
            # Finde J2 Comp-Block
            j2_comp = re.search(r'\(comp \(ref "J2"\)(.*?)\)\s*\(comp', net_content, re.DOTALL)
            if j2_comp:
                print(f"  Comp-Block gefunden")
            
            # Suche nets mit J2
            j2_in_nets = re.findall(r'\(net \(code (\d+)\) \(name "([^"]+)"\)[^)]*\(node \(ref "J2"\) \(pin "([^"]+)"\)', net_content)
            for code, name, pin in j2_in_nets:
                print(f"  Pin {pin} → Netz: {name}")
    except FileNotFoundError:
        print("  .net Datei nicht gefunden")
