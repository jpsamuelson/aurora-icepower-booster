#!/usr/bin/env python3
"""
Phase 1: Update footprints via pcbnew Python API.

For each footprint on the board, load its library version using pcbnew's
native FootprintLoad, then exchange the footprint in-place (preserving
position, orientation, layer, reference, value, pad nets).

Save to temp file, then text-merge footprint blocks back into original
(because pcbnew.SaveBoard corrupts KiCad 9 format).
"""
import os, sys, re, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP_PCB = '/tmp/aurora-fp-update.kicad_pcb'
KICAD_FP = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
LOCAL_FP = os.path.join(BASE, 'footprints.pretty')

# Custom footprints without library prefix need remapping
CUSTOM_REMAP = {
    'SOT-23': ('Package_TO_SOT_SMD', 'SOT-23'),
    'MountingHole_3.2mm_M3': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'L_0805_2012Metric': ('Inductor_SMD', 'L_0805_2012Metric'),
    'C_0402_1005Metric': ('Capacitor_SMD', 'C_0402_1005Metric'),
    'SOIC127P600X175-9N': None,  # local/custom, skip
    'TEL5_DUAL_TRP': None,  # local/custom, skip
}

shutil.copy2(PCB_FILE, TEMP_PCB)
print(f"Copied to {TEMP_PCB}")

sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

board = pcbnew.LoadBoard(TEMP_PCB)
print(f"Board footprints: {len(board.GetFootprints())}")

updated = 0
failed = []
skipped = []

# Collect footprints first (can't modify while iterating)
fp_list = list(board.GetFootprints())

for fp in fp_list:
    ref = fp.GetReference()
    fpid = fp.GetFPID()
    lib_name = str(fpid.GetLibNickname())
    fp_name = str(fpid.GetLibItemName())

    # Handle custom footprints without library prefix
    if not lib_name:
        remap = CUSTOM_REMAP.get(fp_name)
        if remap is None:
            skipped.append(f"{ref} ({fp_name})")
            continue
        lib_name, fp_name = remap

    # Determine library path
    fp_lib_path = os.path.join(KICAD_FP, f'{lib_name}.pretty')
    if not os.path.isdir(fp_lib_path):
        # Try local footprints
        fp_lib_path = LOCAL_FP
        if not os.path.isdir(fp_lib_path):
            failed.append(f"{ref} ({lib_name}:{fp_name}) - lib dir not found")
            continue

    # Load library footprint
    try:
        plugin = pcbnew.PCB_IO_KICAD_SEXPR()
        lib_fp = plugin.FootprintLoad(fp_lib_path, fp_name)
        if lib_fp is None:
            failed.append(f"{ref} ({lib_name}:{fp_name}) - FootprintLoad returned None")
            continue
    except Exception as e:
        failed.append(f"{ref} ({lib_name}:{fp_name}) - load error: {e}")
        continue

    # Preserve identity from board footprint
    pos = fp.GetPosition()
    orient = fp.GetOrientationDegrees()
    layer = fp.GetLayer()
    ref_text = fp.GetReference()
    val_text = fp.GetValue()

    # Save pad-to-net mapping
    pad_nets = {}
    for pad in fp.Pads():
        pad_name = pad.GetNumber()
        net = pad.GetNet()
        if net:
            pad_nets[pad_name] = net

    # Configure library footprint with board identity
    lib_fp.SetPosition(pos)
    lib_fp.SetOrientationDegrees(orient)
    lib_fp.SetLayer(layer)
    lib_fp.SetReference(ref_text)
    lib_fp.SetValue(val_text)

    # FPID: library-loaded footprint already has correct FPID from FootprintLoad
    # For remapped footprints, we loaded from the correct library so FPID is correct

    # Copy net assignments
    for lib_pad in lib_fp.Pads():
        pad_name = lib_pad.GetNumber()
        if pad_name in pad_nets:
            lib_pad.SetNet(pad_nets[pad_name])

    # Replace on board
    board.Remove(fp)
    board.Add(lib_fp)
    updated += 1

print(f"\n=== Results ===")
print(f"Updated: {updated}")
print(f"Skipped: {len(skipped)}")
print(f"Failed: {len(failed)}")
for s in skipped:
    print(f"  SKIP: {s}")
for f in failed:
    print(f"  FAIL: {f}")

# Save to temp
pcbnew.SaveBoard(TEMP_PCB, board)
print(f"\nSaved to {TEMP_PCB}")
print(f"Board footprints after: {len(board.GetFootprints())}")
print("\nNext: text-merge footprint blocks from temp into original PCB")
