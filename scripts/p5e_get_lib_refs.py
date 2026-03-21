#!/usr/bin/env python3
"""
Extract library-default reference positions via pcbnew API.
For each footprint on the board, load the library version and get
the reference field's position relative to footprint origin.
Output a JSON map: { "R1": [dx, dy], "C1": [dx, dy], ... }
"""
import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew
import json
import os

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'
LIB_BASE = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
OUT = '/tmp/lib_ref_positions.json'

LIBRARY_MAP = {
    'R_0805_2012Metric': ('Resistor_SMD', 'R_0805_2012Metric'),
    'C_0805_2012Metric': ('Capacitor_SMD', 'C_0805_2012Metric'),
    'C_1206_3216Metric': ('Capacitor_SMD', 'C_1206_3216Metric'),
    'C_1210_3225Metric': ('Capacitor_SMD', 'C_1210_3225Metric'),
    'C_0402_1005Metric': ('Capacitor_SMD', 'C_0402_1005Metric'),
    'SOIC-8_3.9x4.9mm_P1.27mm': ('Package_SO', 'SOIC-8_3.9x4.9mm_P1.27mm'),
    'SOT-23': ('Package_TO_SOT_SMD', 'SOT-23'),
    'SOT-23-5': ('Package_TO_SOT_SMD', 'SOT-23-5'),
    'L_0805_2012Metric': ('Inductor_SMD', 'L_0805_2012Metric'),
    'D_SOD-323': ('Diode_SMD', 'D_SOD-323'),
    'D_SMB': ('Diode_SMD', 'D_SMB'),
    'MountingHole_3.2mm_M3': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'AudioJack2_Ground_SwitchT': ('Connector_Audio', 'AudioJack2_Ground_SwitchT'),
    'BarrelJack_Horizontal': ('Connector_BarrelJack', 'BarrelJack_Horizontal'),
    'SW_DIP_SPSTx03_Slide_9.78x9.8mm_W7.62mm_P2.54mm': ('Button_Switch_SMD', 'SW_DIP_SPSTx03_Slide_9.78x9.8mm_W7.62mm_P2.54mm'),
}

def nm2mm(v):
    return v / 1e6

board = pcbnew.LoadBoard(PCB)
io = pcbnew.PCB_IO_KICAD_SEXPR()

# Cache: footprint_name -> (ref_dx_mm, ref_dy_mm)
lib_cache = {}
result = {}
skipped = []

for fp in board.GetFootprints():
    ref = fp.GetReference()
    fp_name = fp.GetFPID().GetUniStringLibItemName()
    
    if fp_name in lib_cache:
        result[ref] = lib_cache[fp_name]
        continue
    
    if fp_name not in LIBRARY_MAP:
        skipped.append((ref, fp_name))
        continue
    
    lib_nick, lib_fp_name = LIBRARY_MAP[fp_name]
    lib_path = os.path.join(LIB_BASE, f'{lib_nick}.pretty')
    
    if not os.path.isdir(lib_path):
        skipped.append((ref, f'{lib_nick}.pretty not found'))
        continue
    
    try:
        lib_fp = io.FootprintLoad(lib_path, lib_fp_name)
        # Library footprint is at origin (0,0), rotation 0
        # Reference position IS the offset from footprint center
        ref_pos = lib_fp.Reference().GetPosition()
        dx = nm2mm(ref_pos.x)
        dy = nm2mm(ref_pos.y)
        lib_cache[fp_name] = (dx, dy)
        result[ref] = (dx, dy)
    except Exception as e:
        skipped.append((ref, str(e)))

print(f"Extracted {len(result)} reference positions from library")
print(f"Skipped {len(skipped)}:")
for ref, reason in skipped:
    print(f"  {ref}: {reason}")

print(f"\nLibrary default positions per footprint type:")
for fp_name, (dx, dy) in sorted(lib_cache.items()):
    print(f"  {fp_name}: ({dx:.3f}, {dy:.3f})")

with open(OUT, 'w') as f:
    json.dump(result, f, indent=2)
print(f"\nWritten to {OUT}")
