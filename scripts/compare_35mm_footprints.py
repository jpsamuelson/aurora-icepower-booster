#!/usr/bin/env python3
"""Vergleiche alle KiCad 3.5mm Audio Jack Footprints mit Lumberg 1503 02 Pad-Layout."""

import re
import os
import glob

kicad_fp_base = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_Audio.pretty"

def extract_pads(fp_path):
    """Extrahiere Pads aus einem .kicad_mod."""
    with open(fp_path, "r") as f:
        content = f.read()
    
    pads = []
    # Finde alle pad-Blöcke
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)', content):
        name = m.group(1)
        ptype = m.group(2)  # smd, thru_hole, np_thru_hole
        shape = m.group(3)
        
        # Position
        after = content[m.end():m.end()+200]
        at_match = re.search(r'\(at ([\d.-]+) ([\d.-]+)', after)
        size_match = re.search(r'\(size ([\d.-]+) ([\d.-]+)', after)
        drill_match = re.search(r'\(drill ([\d.-]+)', after)
        
        x = float(at_match.group(1)) if at_match else 0
        y = float(at_match.group(2)) if at_match else 0
        sx = float(size_match.group(1)) if size_match else 0
        sy = float(size_match.group(2)) if size_match else 0
        drill = float(drill_match.group(1)) if drill_match else 0
        
        pads.append({
            'name': name, 'type': ptype, 'shape': shape,
            'x': x, 'y': y, 'sx': sx, 'sy': sy, 'drill': drill
        })
    return pads

# === Referenz: Lumberg 1503 02 ===
ref_path = os.path.join(kicad_fp_base, "Jack_3.5mm_Lumberg_1503_02_Horizontal.kicad_mod")
ref_pads = extract_pads(ref_path)

print("=== REFERENZ: Lumberg 1503 02 ===\n")
print(f"{'Name':<6} {'Type':<14} {'Shape':<10} {'Pos':<16} {'Size':<12} {'Drill'}")
print("-" * 72)
for p in ref_pads:
    print(f"{p['name'] or '(mh)':<6} {p['type']:<14} {p['shape']:<10} ({p['x']:>6.2f}, {p['y']:>5.2f})  {p['sx']:.1f}x{p['sy']:.1f}     {p['drill'] or ''}")

# Signal-Pads (ohne Mounting Holes)
ref_signal = [p for p in ref_pads if p['name']]
ref_names = sorted(set(p['name'] for p in ref_signal))
ref_mounting = [p for p in ref_pads if not p['name']]

print(f"\nSignal-Pads: {ref_names}")
print(f"Mounting Holes: {len(ref_mounting)}")
print(f"Typ: {'SMD' if any(p['type']=='smd' for p in ref_signal) else 'THT'}")

# === Alle 3.5mm Jacks vergleichen ===
print("\n\n=== KOMPATIBILITÄT MIT ANDEREN 3.5mm JACKS ===\n")

results = []

for fp_path in sorted(glob.glob(os.path.join(kicad_fp_base, "Jack_3.5mm_*.kicad_mod"))):
    fp_name = os.path.basename(fp_path).replace(".kicad_mod", "")
    if fp_name == "Jack_3.5mm_Lumberg_1503_02_Horizontal":
        continue
    
    pads = extract_pads(fp_path)
    signal_pads = [p for p in pads if p['name']]
    mounting = [p for p in pads if not p['name']]
    pad_names = sorted(set(p['name'] for p in signal_pads))
    is_smd = any(p['type'] == 'smd' for p in signal_pads)
    is_tht = any(p['type'] == 'thru_hole' for p in signal_pads)
    
    # Kompatibilitäts-Score berechnen
    score = 0
    notes = []
    
    # 1. Gleiche Pin-Namen?
    if pad_names == ref_names:
        score += 3
        notes.append("Pin-Namen identisch (R,S,T)")
    elif set(ref_names).issubset(set(pad_names)):
        score += 2
        notes.append(f"Pin-Namen kompatibel ({','.join(pad_names)})")
    else:
        notes.append(f"Pins: {','.join(pad_names)}")
    
    # 2. Gleicher Typ (SMD/THT)?
    if is_smd and not is_tht:
        score += 2
        notes.append("SMD ✓")
    elif is_tht:
        notes.append("THT")
    
    # 3. Pad-Positionen vergleichen
    if pad_names == ref_names and is_smd:
        max_pos_diff = 0
        for ref_p in ref_signal:
            # Finde matching pad
            matching = [p for p in signal_pads if p['name'] == ref_p['name']]
            if matching:
                # Finde bestes Match (nächste Position)
                min_diff = float('inf')
                for mp in matching:
                    diff = abs(mp['x'] - ref_p['x']) + abs(mp['y'] - ref_p['y'])
                    min_diff = min(min_diff, diff)
                max_pos_diff = max(max_pos_diff, min_diff)
        
        if max_pos_diff < 0.1:
            score += 5
            notes.append(f"EXAKTER Pad-Match! (Δ<0.1mm)")
        elif max_pos_diff < 1.0:
            score += 3
            notes.append(f"Nah (Δ={max_pos_diff:.2f}mm)")
        elif max_pos_diff < 3.0:
            score += 1
            notes.append(f"Ähnlich (Δ={max_pos_diff:.2f}mm)")
        else:
            notes.append(f"Pos. abweichend (Δ={max_pos_diff:.2f}mm)")

    # 4. Mounting Holes
    if len(mounting) == len(ref_mounting):
        score += 1
        
        # Positionen vergleichen
        if ref_mounting and mounting:
            mh_match = True
            for rm in ref_mounting:
                found = False
                for m in mounting:
                    if abs(m['x'] - rm['x']) < 0.5 and abs(m['y'] - rm['y']) < 0.5:
                        found = True
                        break
                if not found:
                    mh_match = False
            if mh_match:
                score += 2
                notes.append("Mounting identisch")

    results.append((score, fp_name, pad_names, is_smd, is_tht, len(signal_pads), notes))

# Sortiere nach Score (höchste zuerst)
results.sort(key=lambda x: -x[0])

print(f"{'Score':<6} {'Footprint':<55} {'Pads':<6} {'Type':<5} Notes")
print("-" * 120)
for score, name, pnames, smd, tht, npad, notes in results:
    ptype = "SMD" if smd and not tht else "THT" if tht else "?"
    marker = "★★★" if score >= 8 else "★★" if score >= 5 else "★" if score >= 3 else ""
    print(f"{score:<6} {name:<55} {npad:<6} {ptype:<5} {'; '.join(notes)} {marker}")

# === Zusammenfassung ===
print("\n\n=== ZUSAMMENFASSUNG ===\n")
print("Lumberg 1503 02 Pad-Layout:")
print("  • SMD 3.5mm TRS Jack (Tip/Ring/Sleeve)")
print("  • 2× Tip-Pads: (-4.05, -2.5) + (4.05, -2.5), 1.5×2.0mm")
print("  • 1× Ring-Pad: (4.05, 6.35), 1.5×1.5mm")
print("  • 1× Sleeve-Pad: (-4.05, 6.35), 1.5×1.5mm")
print("  • 2× Mounting Holes: (-2.5, 2.5) + (2.5, 2.5), Ø1.2mm")
print("  • Pad-Abstand horizontal: 8.1mm")
print("  • Pad-Abstand vertikal: 8.85mm")

top_matches = [r for r in results if r[0] >= 5]
if top_matches:
    print(f"\nBeste Matches (Score ≥ 5):")
    for score, name, _, _, _, _, notes in top_matches:
        part = name.replace("Jack_3.5mm_", "").replace("_Horizontal", "").replace("_", " ")
        print(f"  {score}/10 — {part}: {'; '.join(notes)}")

print("\n\nLCSC-Suchvorschläge:")
print("  1. 'Lumberg 1503 02' — Original")
print("  2. Suche nach Footprint-kompatiblen Teilen basierend auf Pad-Layout")
print("  3. Ähnliche SMD 3.5mm Jacks von CUI, Switronic, etc.")
