#!/usr/bin/env python3
"""
Phase 1: Export fresh DSN from current PCB via pcbnew Python API.
Must be run BEFORE Freerouting.
"""
import sys, os
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
DSN = '/tmp/aurora-booster.dsn'

print(f'Loading board: {PCB}')
board = pcbnew.LoadBoard(PCB)
print(f'  Tracks: {len(board.GetTracks())}')
print(f'  Footprints: {len(board.GetFootprints())}')
print(f'  Nets: {board.GetNetCount()}')

print(f'\nExporting DSN → {DSN}')
ok = pcbnew.ExportSpecctraDSN(board, DSN)
if not ok:
    print('ERROR: DSN export failed!')
    sys.exit(1)

size = os.path.getsize(DSN)
print(f'  DSN size: {size:,} bytes')
print('✅ DSN export complete')
