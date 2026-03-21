#!/usr/bin/env python3
"""
Reset reference field positions to library defaults.

1. Load each footprint from KiCad standard library via pcbnew
2. Get the default reference position from the library version
3. Write back into the PCB file

This doesn't affect routing since only silk text positions change.
"""
import sys, os, re

sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
KICAD_FP = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

CUSTOM_REMAP = {
    'SOT-23': ('Package_TO_SOT_SMD', 'SOT-23'),
    'MountingHole_3.2mm_M3': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'L_0805_2012Metric': ('Inductor_SMD', 'L_0805_2012Metric'),
    'C_0402_1005Metric': ('Capacitor_SMD', 'C_0402_1005Metric'),
    'SOIC127P600X175-9N': None,
    'TEL5_DUAL_TRP': None,
}

# Load board to get footprint library info
board = pcbnew.LoadBoard(PCB_FILE)

# Collect library default reference positions
ref_defaults = {}  # ref -> (x_offset, y_offset) in local coords

for fp in board.GetFootprints():
    ref = fp.GetReference()
    fpid = fp.GetFPID()
    lib_name = str(fpid.GetLibNickname())
    fp_name = str(fpid.GetLibItemName())
    
    if not lib_name:
        remap = CUSTOM_REMAP.get(fp_name)
        if remap is None:
            continue
        lib_name, fp_name = remap
    
    fp_lib_path = os.path.join(KICAD_FP, f'{lib_name}.pretty')
    if not os.path.isdir(fp_lib_path):
        continue
    
    try:
        plugin = pcbnew.PCB_IO_KICAD_SEXPR()
        lib_fp = plugin.FootprintLoad(fp_lib_path, fp_name)
        if lib_fp is None:
            continue
        
        # Get the reference field position from library
        lib_ref_field = lib_fp.Reference()
        pos = lib_ref_field.GetPosition()
        # This is in library coords (relative to 0,0 footprint center)
        # pcbnew stores in nanometers
        x_nm, y_nm = pos.x, pos.y
        x_mm = x_nm / 1000000.0
        y_mm = y_nm / 1000000.0
        ref_defaults[ref] = (x_mm, y_mm)
        
    except Exception as e:
        pass

print(f"Got library defaults for {len(ref_defaults)} references")

# Output as a simple format that a text-processing script can use
with open('/tmp/ref_defaults.txt', 'w') as f:
    for ref, (x, y) in sorted(ref_defaults.items()):
        f.write(f"{ref}\t{x:.6f}\t{y:.6f}\n")

print(f"Written to /tmp/ref_defaults.txt")
print(f"Sample: {list(ref_defaults.items())[:5]}")
