#!/usr/bin/env python3
"""
Production export: Gerber, Drill, BOM, and Position files for JLCPCB.
"""
import subprocess, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
SCH = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_sch')
GERBER_DIR = os.path.join(BASE, 'production', 'gerber')
ASSEMBLY_DIR = os.path.join(BASE, 'production', 'assembly')

os.makedirs(GERBER_DIR, exist_ok=True)
os.makedirs(ASSEMBLY_DIR, exist_ok=True)

print("=" * 60)
print("PRODUCTION EXPORT")
print("=" * 60)

# 1. Gerber export
print("\n[1/4] Gerber export...")
gerber_layers = [
    'F.Cu', 'B.Cu',
    'F.Paste', 'B.Paste',
    'F.SilkS', 'B.SilkS',
    'F.Mask', 'B.Mask',
    'Edge.Cuts',
]
layer_args = []
for layer in gerber_layers:
    layer_args.extend(['-l', layer])

result = subprocess.run(
    ['kicad-cli', 'pcb', 'export', 'gerbers',
     '--output', GERBER_DIR + '/',
     '--subtract-soldermask',
     '--no-protel-ext',
     '--use-drill-file-origin',
     ] + layer_args + [PCB],
    capture_output=True, text=True, timeout=60
)
if result.returncode == 0:
    files = os.listdir(GERBER_DIR)
    gerber_files = [f for f in files if f.endswith(('.gbr', '.gbl', '.gtl', '.gbs', '.gts', '.gbo', '.gto', '.gbp', '.gtp', '.gm1', '.gbrjob'))]
    print(f"  ✅ {len(gerber_files)} gerber files")
else:
    print(f"  ❌ Gerber export failed: {result.stderr[:200]}")

# 2. Drill file export
print("\n[2/4] Drill export...")
result = subprocess.run(
    ['kicad-cli', 'pcb', 'export', 'drill',
     '--output', GERBER_DIR + '/',
     '--format', 'excellon',
     '--drill-origin', 'absolute',
     '--excellon-units', 'mm',
     PCB],
    capture_output=True, text=True, timeout=60
)
if result.returncode == 0:
    drill_files = [f for f in os.listdir(GERBER_DIR) if f.endswith(('.drl', '.DRL'))]
    print(f"  ✅ {len(drill_files)} drill files")
else:
    print(f"  ❌ Drill export failed: {result.stderr[:200]}")

# 3. BOM export
print("\n[3/4] BOM export...")
bom_file = os.path.join(ASSEMBLY_DIR, 'aurora-dsp-icepower-booster-bom.csv')
result = subprocess.run(
    ['kicad-cli', 'sch', 'export', 'bom',
     '--output', bom_file,
     '--fields', 'Reference,Value,Footprint,${QUANTITY},${DNP}',
     '--group-by', 'Value,Footprint',
     '--sort-field', 'Reference',
     SCH],
    capture_output=True, text=True, timeout=60
)
if result.returncode == 0:
    size = os.path.getsize(bom_file)
    print(f"  ✅ BOM: {bom_file} ({size:,} bytes)")
else:
    print(f"  ❌ BOM export failed: {result.stderr[:200]}")

# 4. Position file export
print("\n[4/4] Position file export...")
pos_file = os.path.join(ASSEMBLY_DIR, 'aurora-dsp-icepower-booster-pos.csv')
result = subprocess.run(
    ['kicad-cli', 'pcb', 'export', 'pos',
     '--output', pos_file,
     '--format', 'csv',
     '--units', 'mm',
     '--side', 'both',
     '--use-drill-file-origin',
     PCB],
    capture_output=True, text=True, timeout=60
)
if result.returncode == 0:
    size = os.path.getsize(pos_file)
    print(f"  ✅ Position: {pos_file} ({size:,} bytes)")
else:
    print(f"  ❌ Position export failed: {result.stderr[:200]}")

# Summary
print("\n" + "=" * 60)
print("EXPORT SUMMARY")
print("=" * 60)
all_files = []
for d in [GERBER_DIR, ASSEMBLY_DIR]:
    for f in sorted(os.listdir(d)):
        fpath = os.path.join(d, f)
        size = os.path.getsize(fpath)
        rel = os.path.relpath(fpath, BASE)
        all_files.append((rel, size))
        print(f"  {rel:60s} {size:>8,} bytes")
print(f"\nTotal: {len(all_files)} files, {sum(s for _, s in all_files):,} bytes")
