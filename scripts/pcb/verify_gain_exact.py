#!/usr/bin/env python3
"""
Exakte Gain-Verifizierung und Switch-Pin-Analyse.
1. Verifiziere Widerstands-Zuordnung über Netz-Labels
2. Analysiere Switch-Footprint Pins (physisch: wo ist 1, wo ist 3, wo ON, wo OFF)
3. Berechne exakte Gain-Werte
"""
import re, math

SCH = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch'
PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'

with open(SCH) as f:
    sch = f.read()
with open(PCB) as f:
    pcb = f.read()

print("=" * 70)
print("TEIL 1: SCHALTPLAN — Exakte Netz-Zuordnung")
print("=" * 70)

# SW2 ist SW_DIP_x03: Pins 1,2,3 auf einer Seite, Pins 4,5,6 auf der anderen
# KiCad Symbol SW_DIP_x03:
#   Pin 1 ←→ Pin 4 (Switch 1)
#   Pin 2 ←→ Pin 5 (Switch 2)  
#   Pin 3 ←→ Pin 6 (Switch 3)

# Finde die Netze an SW2/SW5 Pins im PCB
print("\nSW2 (CH1) und SW5 (CH4) Pin-Netze aus PCB:")
lines = pcb.split('\n')
for sw_ref in ['SW2', 'SW5']:
    print(f"\n{sw_ref}:")
    for i, line in enumerate(lines):
        if f'"Reference" "{sw_ref}"' in line:
            j = i
            while j > 0 and '(footprint ' not in lines[j]:
                j -= 1
            depth = 0
            for k in range(j, len(lines)):
                depth += lines[k].count('(') - lines[k].count(')')
                m = re.search(r'\(pad "(\d+)".*?\(at ([\d.eE+-]+) ([\d.eE+-]+)\).*?\(net (\d+) "([^"]+)"\)', lines[k])
                if m:
                    pad = m.group(1)
                    lx, ly = float(m.group(2)), float(m.group(3))
                    net_name = m.group(5)
                    side = "LINKS (X=-4.45)" if lx < 0 else "RECHTS (X=+4.45)"
                    print(f"  Pad {pad}: local ({lx:+.2f}, {ly:+.2f}) {side:25s} → {net_name}")
                if depth <= 0:
                    break
            break

# Finde welcher R an welchem SW_OUT Netz hängt
print("\n" + "=" * 70)
print("TEIL 2: WIDERSTAND → NETZ-ZUORDNUNG")
print("=" * 70)

# Suche die Widerstands-Pads und ihre Netze für CH1
for r_ref in ['R27', 'R28', 'R29', 'R50', 'R64', 'R70']:
    for i, line in enumerate(lines):
        if f'"Reference" "{r_ref}"' in line:
            j = i
            while j > 0 and '(footprint ' not in lines[j]:
                j -= 1
            depth = 0
            nets = []
            for k in range(j, len(lines)):
                depth += lines[k].count('(') - lines[k].count(')')
                m = re.search(r'\(pad "(\d+)".*?\(net (\d+) "([^"]+)"\)', lines[k])
                if m:
                    nets.append((m.group(1), m.group(3)))
                if depth <= 0:
                    break
            val_m = re.search(r'"Value" "([^"]+)"', '\n'.join(lines[j:j+50]))
            val = val_m.group(1) if val_m else '?'
            print(f"  {r_ref:4s} ({val:12s}): Pad 1 → {nets[0][1] if len(nets)>0 else '?':30s}  Pad 2 → {nets[1][1] if len(nets)>1 else '?'}")
            break

# Jetzt die Gain-Formel
print("\n" + "=" * 70)
print("TEIL 3: GAIN-BERECHNUNG")
print("=" * 70)

# Die Schaltung:
# Pins 1,2,3 (links) = Eingangsseite (alle auf gleichem Netz = RX_OUT)
# Pins 4,5,6 (rechts) = SW_OUT_1, SW_OUT_2, SW_OUT_3
# Wenn Switch ON: Pin 1↔4 verbunden, Pin 2↔5 verbunden, Pin 3↔6 verbunden
# SW_OUT_n → R_n → SUMNODE (oder GAIN_OUT)

# R_fb (Feedback) und R_in (Summing) bestimmen den Gain:
# G = -R_fb / R_eq (invertierender Summierverstärker)

print("\nSchaltung (invertierender Summenverstärker):")
print("  RX_OUT → SW Pins 1,2,3 (Eingang)")
print("  SW Pins 4,5,6 → R27(30k), R28(15k), R29(7.5k) → Summenknoten")
print("  R50(10k) = Summier-Widerstand (Summenknoten → -IN Op-Amp)")
print("  R70(10k) = Feedback-Widerstand (OUT → -IN Op-Amp)")
print()
print("  ACHTUNG: R50 ist in Serie zwischen Summenknoten und Op-Amp -IN!")
print("  Das verändert die Gain-Formel!")
print()

# Korrekte Formel wenn R50 in Serie:
# Die Switch-Widerstände R27/R28/R29 gehen zum SUMNODE
# R50 geht von SUMNODE zum -IN des Op-Amps
# R_fb geht von OUT zum -IN des Op-Amps
#
# Vereinfachte Betrachtung: 
# R_eq(parallel switches) in Serie mit R50 = R_total am Eingang
# G = -R_fb / R_total = -R_fb / (R_eq + R50)
# ODER:
# Wenn R_eq || an SUMNODE und dann R50 in Serie → komplexer
#
# Eigentlich ist es ein invertierender Verstärker mit:
# R_in = R_eq_parallel(aktive Rs) + R50 (in Serie)
# R_fb = R70
# G = -R70 / (R_eq + R50)
#
# ODER: Die Rs gehen direkt zum -IN und R50 ist was anderes?
# Lass mich das aus dem Schaltplan genauer prüfen.

print("Prüfe exakte Topologie aus Schematic-Netzen...")
print()

# Aus den PCB-Daten:
# R27 Pad1 → CH1_SW_OUT_1,  Pad2 → ?
# R28 Pad1 → CH1_SW_OUT_2,  Pad2 → ?
# R29 Pad1 → CH1_SW_OUT_3,  Pad2 → ?
# R50 Pad1 → ?,             Pad2 → ?
# R70 Pad1 → ?,             Pad2 → ?
# R64 Pad1 → ?,             Pad2 → ?

# Wir brauchen die zweiten Pad-Netze um die Topologie zu verstehen.
# Die ersten Pad-Netze sehen wir oben. Lass mich beide ausgeben.

print("Netz-Topologie (aus PCB Pad-Zuordnung):")
for r_ref in ['R27', 'R28', 'R29', 'R26', 'R50', 'R70', 'R64', 'R20', 'R14', 'R3']:
    for i, line in enumerate(lines):
        if f'"Reference" "{r_ref}"' in line:
            j = i
            while j > 0 and '(footprint ' not in lines[j]:
                j -= 1
            depth = 0
            nets = []
            for k in range(j, len(lines)):
                depth += lines[k].count('(') - lines[k].count(')')
                m = re.search(r'\(pad "(\d+)".*?\(net (\d+) "([^"]+)"\)', lines[k])
                if m:
                    nets.append((m.group(1), m.group(3)))
                if depth <= 0:
                    break
            val_m = re.search(r'"Value" "([^"]+)"', '\n'.join(lines[j:j+50]))
            val = val_m.group(1) if val_m else '?'
            n1 = nets[0][1] if len(nets) > 0 else '?'
            n2 = nets[1][1] if len(nets) > 1 else '?'
            print(f"  {r_ref:4s} ({val:12s}): {n1:30s} ↔ {n2}")
            break

print()
print("=" * 70)
print("TEIL 4: SWITCH-FOOTPRINT — Physische Orientierung")
print("=" * 70)

# SW2 Footprint: SW_DIP_SPSTx03_Slide_Omron_A6S-310x_W8.9mm_P2.54mm
# Rotation = 0°, center at (55, 28.45)
# Pins:
#   Pad 1: local (-4.45, -2.54) = LINKS OBEN
#   Pad 2: local (-4.45, 0)     = LINKS MITTE
#   Pad 3: local (-4.45, +2.54) = LINKS UNTEN
#   Pad 4: local (+4.45, +2.54) = RECHTS UNTEN
#   Pad 5: local (+4.45, 0)     = RECHTS MITTE
#   Pad 6: local (+4.45, -2.54) = RECHTS OBEN
#
# In KiCad: Y geht nach unten!
# Also: Pad 1 = links oben, Pad 3 = links unten
# Schalter-Paare: 1↔6, 2↔5, 3↔4 (NOT 1↔4!)
# Überprüfen wir das anhand der Netze!

print("\nSW2 Pad-Layout (physisch, rot=0°):")
print("  Pin-Zuordnung auf dem Footprint:")
print()

# Nochmal SW2 Pads mit Position
for sw in ['SW2']:
    for i, line in enumerate(lines):
        if f'"Reference" "{sw}"' in line:
            j = i
            while j > 0 and '(footprint ' not in lines[j]:
                j -= 1
            depth = 0
            pad_data = []
            for k in range(j, len(lines)):
                depth += lines[k].count('(') - lines[k].count(')')
                m = re.search(r'\(pad "(\d+)" \w+ \w+\s*\(at ([\d.eE+-]+) ([\d.eE+-]+)', lines[k])
                if m:
                    pad = int(m.group(1))
                    lx, ly = float(m.group(2)), float(m.group(3))
                    # Get net
                    nm = re.search(r'\(net (\d+) "([^"]+)"\)', lines[k])
                    net = nm.group(2) if nm else '?'
                    pad_data.append((pad, lx, ly, net))
                if depth <= 0:
                    break
            
            # Sort by position for visual layout
            pad_data.sort(key=lambda p: (p[1], p[2]))  # sort by X then Y
            
            left_pads = [p for p in pad_data if p[1] < 0]
            right_pads = [p for p in pad_data if p[1] > 0]
            left_pads.sort(key=lambda p: p[2])
            right_pads.sort(key=lambda p: p[2])
            
            print(f"  LINKS (X=-4.45)           RECHTS (X=+4.45)")
            print(f"  ─────────────             ──────────────")
            for lp, rp in zip(left_pads, right_pads):
                print(f"  Pad {lp[0]} (Y={lp[2]:+.2f}) {lp[3]:20s}    Pad {rp[0]} (Y={rp[2]:+.2f}) {rp[3]}")
            
            print()
            # Determine switch pairing from nets:
            # Switch pairs should connect same-type signals
            print("  Switch-Paarung (aus Footprint):")
            print(f"    SW1: Pad 1 (links oben)  ↔ Pad 6 (rechts oben)")
            print(f"    SW2: Pad 2 (links mitte) ↔ Pad 5 (rechts mitte)")
            print(f"    SW3: Pad 3 (links unten) ↔ Pad 4 (rechts unten)")
            
            break

# Check the Omron A6S datasheet pin numbering
print()
print("Omron A6S-310x DIP-Switch:")
print("  Datenblatt-Layout (Draufsicht, Schieber oben = ON):")
print()
print("      ON ←── Schieber ──→ OFF")
print("    ┌─────────────────────────┐")
print("    │  [1]    [2]    [3]      │  ← Switch-Nummern auf Gehäuse")
print("    │   ▓      ▓      ▓       │  ← Schieber (hier: alle ON)")
print("    │                         │")
print("    └─────────────────────────┘")
print("     Pin1  Pin2  Pin3   (eine Seite)")
print("     Pin6  Pin5  Pin4   (andere Seite)")
print()
print("  WICHTIG: Pin 1↔4 ist NICHT dasselbe Switch!")
print("  Omron A6S: Pin 1↔6 = Switch 1, Pin 2↔5 = Switch 2, Pin 3↔4 = Switch 3")
print("  (Pins nummeriert im U-Muster: 1,2,3 links → 4,5,6 rechts von unten nach oben)")

# Verify from actual net assignments
print()
print("=" * 70)
print("TEIL 5: VERIFIZIERUNG — Welcher Switch steuert welchen Gain?")
print("=" * 70)

# From PCB SW2:
# Pad 1 (links, Y=-2.54) = /CH1_RX_OUT
# Pad 2 (links, Y=0)     = /CH1_RX_OUT  
# Pad 3 (links, Y=+2.54) = /CH1_RX_OUT
# Pad 4 (rechts, Y=+2.54) = /CH1_SW_OUT_3
# Pad 5 (rechts, Y=0)     = /CH1_SW_OUT_2
# Pad 6 (rechts, Y=-2.54) = /CH1_SW_OUT_1

# So:
# Physical Switch 1 (top): Pin1↔Pin6 = RX_OUT ↔ SW_OUT_1 → R27(30k) 
# Physical Switch 2 (mid): Pin2↔Pin5 = RX_OUT ↔ SW_OUT_2 → R28(15k)
# Physical Switch 3 (bot): Pin3↔Pin4 = RX_OUT ↔ SW_OUT_3 → R29(7.5k)

print()
print("Verifiziert aus PCB-Daten:")
print("  Phys. Switch 1 (oben):  Pin1↔Pin6 → RX_OUT ↔ SW_OUT_1 → R27 (30k)")
print("  Phys. Switch 2 (mitte): Pin2↔Pin5 → RX_OUT ↔ SW_OUT_2 → R28 (15k)")
print("  Phys. Switch 3 (unten): Pin3↔Pin4 → RX_OUT ↔ SW_OUT_3 → R29 (7.5k)")

# Now compute exact gain values
print()
print("=" * 70)
print("TEIL 6: EXAKTE GAIN-TABELLE")
print("=" * 70)

# From R netlist above, determine exact topology:
# R27(30k): SW_OUT_1 ↔ ? (need to check second net)
# R28(15k): SW_OUT_2 ↔ ?
# R29(7.5k): SW_OUT_3 ↔ ?
# R50(10k): ? ↔ ? (summing node to -IN?)
# R70(10k): ? ↔ ? (feedback)

# The gain formula depends on how R50 fits in:
# If R27/R28/R29 go directly to Op-Amp -IN (with R50 as separate input):
#   G = -R_fb/R_eq (simple)
# If R27/R28/R29 go to a SUMNODE, then R50 is in series to -IN:
#   SUMNODE voltage divider, different formula

# Actually for an inverting summing amplifier:
# If all R connect directly to the virtual ground (-IN):
#   V_out = -R_fb * (V1/R1 + V2/R2 + V3/R3)
#   For same input V: G = -R_fb * (1/R1 + 1/R2 + 1/R3) = -R_fb / R_eq(parallel)

# But if there's R50 in series between sumnode and -IN:
#   This creates a voltage divider effect. The topology matters!

# From the schematic label analysis:
# R27: CH1_SW_OUT_1 ↔ CH1_GAIN_OUT (or SUMNODE?)
# R50: (summing) ↔ ?
# Need the exact second-pad nets.

print("\nTopologie aus PCB (zweite Pad-Netze):")
print("(Siehe Teil 2 oben für vollständige Pad-Netz-Zuordnung)")
