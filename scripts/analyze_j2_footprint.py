#!/usr/bin/env python3
"""Analysiere J2-Footprint und suche kompatible 3.5mm Jacks in KiCad-Bibliothek."""

import re
import os
import glob

# === 1. J2 Footprint aus PCB extrahieren ===
pcb_path = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb"

with open(pcb_path, "r") as f:
    pcb = f.read()

# Finde den Footprint-Block der J2 enthält
# Suche nach (footprint ... das "J2" als Reference hat
# Strategie: Finde "J2" Position, dann rückwärts zum (footprint Start

j2_pos = pcb.find('"J2"')
if j2_pos == -1:
    print("ERROR: J2 nicht in PCB gefunden!")
    exit(1)

# Rückwärts zum (footprint gehen
search_start = max(0, j2_pos - 5000)
segment = pcb[search_start:j2_pos]

# Finde den letzten (footprint vor J2
fp_starts = [m.start() for m in re.finditer(r'\(footprint ', segment)]
if not fp_starts:
    print("ERROR: Kein (footprint vor J2 gefunden!")
    exit(1)

fp_abs_start = search_start + fp_starts[-1]

# Vorwärts: Klammer-Balance bis Footprint-Ende
depth = 0
fp_end = fp_abs_start
for i in range(fp_abs_start, len(pcb)):
    if pcb[i] == '(':
        depth += 1
    elif pcb[i] == ')':
        depth -= 1
        if depth == 0:
            fp_end = i + 1
            break

fp_block = pcb[fp_abs_start:fp_end]

# Footprint-Name
fp_name_match = re.search(r'\(footprint "([^"]+)"', fp_block)
fp_name = fp_name_match.group(1) if fp_name_match else "UNKNOWN"
print(f"=== J2 Footprint: {fp_name} ===\n")

# Pads extrahieren
pads = re.findall(r'\(pad "([^"]*)" (\w+) (\w+) \(at ([^)]+)\).*?\(size ([^)]+)\)(?:.*?\(drill (?:oval )?([^)]+)\))?', fp_block)
print("Pads:")
print(f"  {'Name':<6} {'Type':<6} {'Shape':<8} {'Position':<16} {'Size':<16} {'Drill':<16}")
print(f"  {'-'*6} {'-'*6} {'-'*8} {'-'*16} {'-'*16} {'-'*16}")
for pad in pads:
    name, ptype, shape, pos, size, drill = pad
    print(f"  {name:<6} {ptype:<6} {shape:<8} {pos:<16} {size:<16} {drill or 'N/A':<16}")

# Courtyard/Outline Größe
courtyard = re.findall(r'\(fp_line \(start ([^)]+)\) \(end ([^)]+)\).*?F\.CrtYd', fp_block)
if courtyard:
    all_x = []
    all_y = []
    for start, end in courtyard:
        sx, sy = map(float, start.split())
        ex, ey = map(float, end.split())
        all_x.extend([sx, ex])
        all_y.extend([sy, ey])
    if all_x:
        print(f"\nCourtyard: {max(all_x)-min(all_x):.2f} x {max(all_y)-min(all_y):.2f} mm")
        print(f"  X: {min(all_x):.2f} to {max(all_x):.2f}")
        print(f"  Y: {min(all_y):.2f} to {max(all_y):.2f}")

# === 2. KiCad Footprint-Bibliothek durchsuchen ===
print("\n\n=== KiCad 3.5mm Audio Jack Footprints ===\n")

# KiCad App-Pfad
kicad_fp_base = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
# Auch projekt-eigene Footprints
project_fp = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/footprints.pretty"

# Suche nach Jack/Audio Footprints
audio_libs = glob.glob(os.path.join(kicad_fp_base, "Connector_Audio*"))
print(f"Audio-Connector-Bibliotheken: {len(audio_libs)}")

for lib in sorted(audio_libs):
    lib_name = os.path.basename(lib)
    footprints = sorted(glob.glob(os.path.join(lib, "*.kicad_mod")))
    
    # Nur 3.5mm Jacks
    jack_fps = [fp for fp in footprints if "3.5" in os.path.basename(fp) or "Jack" in os.path.basename(fp)]
    
    if jack_fps:
        print(f"\n--- {lib_name} ---")
        for fp_path in jack_fps:
            fp_file = os.path.basename(fp_path).replace(".kicad_mod", "")
            
            # Pad-Analyse
            with open(fp_path, "r") as f:
                content = f.read()
            
            fp_pads = re.findall(r'\(pad "([^"]*)" (\w+) (\w+) \(at ([^)]+)\)', content)
            pad_count = len(fp_pads)
            
            # Pad-Positionen
            positions = []
            for pname, ptype, pshape, ppos in fp_pads:
                coords = ppos.split()
                x, y = float(coords[0]), float(coords[1])
                positions.append((pname, x, y, ptype))
            
            # Vergleiche mit J2-Pads
            j2_pad_positions = {}
            for pad in pads:
                name, ptype, shape, pos, size, drill = pad
                coords = pos.split()
                x, y = float(coords[0]), float(coords[1])
                j2_pad_positions[name] = (x, y)
            
            # Kompatibilitätscheck: Gleiche Pad-Anzahl und ähnliche Positionen?
            compatible = False
            if pad_count == len(pads):
                # Prüfe ob Positionen ähnlich sind (±1mm Toleranz)
                lib_positions = {p[0]: (p[1], p[2]) for p in positions}
                if set(lib_positions.keys()) == set(j2_pad_positions.keys()):
                    max_diff = 0
                    for pname in j2_pad_positions:
                        if pname in lib_positions:
                            dx = abs(j2_pad_positions[pname][0] - lib_positions[pname][0])
                            dy = abs(j2_pad_positions[pname][1] - lib_positions[pname][1])
                            max_diff = max(max_diff, dx, dy)
                    if max_diff < 0.5:
                        compatible = True
            
            compat_str = " ✅ KOMPATIBEL" if compatible else ""
            print(f"  {fp_file}")
            print(f"    Pads: {pad_count} — {', '.join(f'{p[0]}@({p[1]},{p[2]})' for p in positions)}")
            if compatible:
                print(f"    {compat_str}")

# === 3. Projekt-eigene Footprints ===
if os.path.exists(project_fp):
    print(f"\n--- Projekt-Footprints ({project_fp}) ---")
    for fp_path in sorted(glob.glob(os.path.join(project_fp, "*.kicad_mod"))):
        fp_file = os.path.basename(fp_path).replace(".kicad_mod", "")
        if "Jack" in fp_file or "jack" in fp_file or "3.5" in fp_file or "audio" in fp_file.lower():
            with open(fp_path, "r") as f:
                content = f.read()
            fp_pads = re.findall(r'\(pad "([^"]*)" (\w+) (\w+) \(at ([^)]+)\)', content)
            print(f"  {fp_file}")
            for pname, ptype, pshape, ppos in fp_pads:
                print(f"    Pad {pname}: {ptype} {pshape} at ({ppos})")

# === 4. Zusammenfassung: Welche KiCad-Symbole passen? ===
print("\n\n=== Zusammenfassung für LCSC-Suche ===\n")
print(f"J2 nutzt Footprint: {fp_name}")
print(f"Pad-Anzahl: {len(pads)}")
print(f"Pad-Namen: {', '.join(p[0] for p in pads)}")
print(f"\nGeeignete Suchbegriffe für LCSC:")
print(f"  - 3.5mm audio jack horizontal THT")
print(f"  - PJ-301M / PJ-302M (Thonkiconn)")  
print(f"  - Lumberg 1503 02")
print(f"  - 3.5mm stereo/mono jack PCB mount")

# Prüfe ob der Footprint ein Custom-Footprint ist
if fp_name.startswith("footprints:") or "Lumberg" in fp_name or "KIPRJMOD" in fp_name:
    print(f"\n⚠️  Custom/Projekt-Footprint — Pad-Layout ist maßgeblich, nicht der Name!")
