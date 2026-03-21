#!/usr/bin/env python3
"""
Phase 3: Import SES into pcbnew temp file (NOT the original!).
pcbnew.SaveBoard() corrupts KiCad 9 format — so we save to temp only.
"""
import sys, os
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
SES = '/tmp/aurora-booster.ses'
TEMP_PCB = '/tmp/aurora-booster-routed.kicad_pcb'

if not os.path.exists(SES):
    print(f'ERROR: SES file not found: {SES}')
    print('Run route_2_freerouting.py first!')
    sys.exit(1)

print(f'Loading board: {PCB}')
board = pcbnew.LoadBoard(PCB)
tracks_before = len(board.GetTracks())
print(f'  Tracks before: {tracks_before}')

print(f'\nImporting SES: {SES}')
ok = pcbnew.ImportSpecctraSES(board, SES)
print(f'  Import: {"OK" if ok else "FAILED"}')

tracks_after = len(board.GetTracks())
print(f'  Tracks after:  {tracks_after}')
print(f'  New tracks:    {tracks_after - tracks_before}')

# Save to temp ONLY (NEVER to original — SaveBoard corrupts KiCad 9)
pcbnew.SaveBoard(TEMP_PCB, board)
print(f'\n✅ Saved to temp: {TEMP_PCB} ({os.path.getsize(TEMP_PCB):,} bytes)')
print('  ⚠️  This is a temp file — use route_4_merge.py to merge back!')
