#!/usr/bin/env python3
"""Check D1 SMBJ15CA pin positions and the dangling wire."""
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()

cache_start = text.find('(lib_symbols')

# Find SMBJ15CA in cache
for name in ['SMBJ15CA', 'D_TVS', 'D_TVS_x2']:
    idx = text.find('"' + name + '"', cache_start)
    if idx >= 0:
        chunk = text[idx:idx+3000]
        pins = re.findall(
            r'\(pin\s+(\w+)\s+\w+\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+\d+)?\)'
            r'.*?\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"',
            chunk
        )
        print(f'{name} pins in cache:')
        for ptype, px, py, pname, pnum in pins:
            print(f'  Pin {pnum} ({pname}, {ptype}): local ({px}, {py})')
        break

# Find D1 in schematic (its lib_id and rotation)
for m in re.finditer(r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)\s+(\d+)\)', text):
    lib_id = m.group(1)
    x, y, rot = float(m.group(2)), float(m.group(3)), int(m.group(4))
    start = m.start()
    chunk = text[start:start+1500]
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', chunk)
    if ref_m and ref_m.group(1) == 'D1':
        print(f'\nD1: lib_id={lib_id}, pos=({x}, {y}), rot={rot}')
        
        # Calculate pin positions with rotation
        idx2 = text.find('"' + lib_id.split(':')[-1] + '"', cache_start)
        if idx2 >= 0:
            chunk2 = text[idx2:idx2+3000]
            pins2 = re.findall(
                r'\(pin\s+(\w+)\s+\w+\s+\(at\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+\d+)?\)'
                r'.*?\(name\s+"([^"]+)".*?\(number\s+"([^"]+)"',
                chunk2
            )
            import math
            for ptype, px, py, pname, pnum in pins2:
                lpx, lpy = float(px), float(py)
                # Rotation: CCW in degrees
                rad = math.radians(rot)
                rx = lpx * math.cos(rad) - lpy * math.sin(rad)
                ry = lpx * math.sin(rad) + lpy * math.cos(rad)
                # Schematic: Y inverted
                sch_x = x + rx
                sch_y = y - ry
                print(f'  Pin {pnum} ({pname}): sch ({sch_x:.2f}, {sch_y:.2f})')
        break

# Check: what wire endpoint is at (42.0, 81.81)?
print('\nWire analysis at (42.0, 81.81):')
for wm in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\s+\(xy\s+([\d.\-]+)\s+([\d.\-]+)\)\)', text):
    x1, y1, x2, y2 = float(wm.group(1)), float(wm.group(2)), float(wm.group(3)), float(wm.group(4))
    if (abs(x1 - 42.0) < 0.02 and abs(y1 - 81.81) < 0.02) or \
       (abs(x2 - 42.0) < 0.02 and abs(y2 - 81.81) < 0.02):
        print(f'  Wire: ({x1},{y1})->({x2},{y2})')

# Find D1 pin 2 (anode) in netlist
with open('/tmp/revalidation_netlist.net') as f:
    netlist = f.read()
for nm in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)".*?\)\)', netlist, re.DOTALL):
    if '"D1"' in nm.group(0):
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "(\d+)"\)', nm.group(0))
        for ref, pin in nodes:
            if ref == 'D1':
                print(f'  D1 pin {pin} on net "{nm.group(1)}"')
