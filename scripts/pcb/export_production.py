#!/usr/bin/env python3
"""Export Gerber, Drill, BOM and Position files for JLCPCB production."""
import subprocess, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
SCH = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_sch')
GERBER_DIR = os.path.join(BASE, 'production', 'gerber')
ASSEMBLY_DIR = os.path.join(BASE, 'production', 'assembly')

os.makedirs(GERBER_DIR, exist_ok=True)
os.makedirs(ASSEMBLY_DIR, exist_ok=True)

def run(cmd, label):
    print(f'  {label}...')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f'  FAILED: {r.stderr.strip()}')
        return False
    return True

print('=' * 60)
print('PRODUCTION EXPORT')
print('=' * 60)

# 1. Gerber export (all layers)
print('\n[1/4] Gerber export...')
ok = run([
    'kicad-cli', 'pcb', 'export', 'gerbers',
    '--output', GERBER_DIR + '/',
    '--layers', 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts',
    '--subtract-soldermask',
    '--no-protel-ext',
    PCB
], 'Gerber layers')

# 2. Drill file
print('\n[2/4] Drill export...')
ok2 = run([
    'kicad-cli', 'pcb', 'export', 'drill',
    '--output', GERBER_DIR + '/',
    '--format', 'excellon',
    '--drill-origin', 'absolute',
    '--excellon-units', 'mm',
    PCB
], 'Drill file')

# 3. BOM
print('\n[3/4] BOM export...')
bom_file = os.path.join(ASSEMBLY_DIR, 'aurora-dsp-icepower-booster-bom.csv')
ok3 = run([
    'kicad-cli', 'sch', 'export', 'bom',
    '--output', bom_file,
    '--fields', 'Reference,Value,Footprint,${QUANTITY}',
    '--group-by', 'Value,Footprint',
    SCH
], 'BOM')

# 4. Position file (component placement)
print('\n[4/4] Position file export...')
pos_file = os.path.join(ASSEMBLY_DIR, 'aurora-dsp-icepower-booster-pos.csv')
ok4 = run([
    'kicad-cli', 'pcb', 'export', 'pos',
    '--output', pos_file,
    '--format', 'csv',
    '--units', 'mm',
    '--side', 'both',
    '--smd-only',
    PCB
], 'Position file')

print('\n' + '=' * 60)
print('RESULTS')
print('=' * 60)

# List output files
for d, label in [(GERBER_DIR, 'Gerber'), (ASSEMBLY_DIR, 'Assembly')]:
    files = sorted(os.listdir(d))
    print(f'\n{label} ({len(files)} files):')
    for f in files:
        size = os.path.getsize(os.path.join(d, f))
        print(f'  {f:50s} {size:>8,} bytes')

all_ok = ok and ok2 and ok3 and ok4
print(f'\nOverall: {"✅ ALL OK" if all_ok else "⚠️ Some exports failed"}')
