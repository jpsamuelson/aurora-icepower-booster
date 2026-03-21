#!/usr/bin/env python3
"""
Analyze positions of components involved in silk violations.
For each violating reference, show footprint position, rotation, current ref offset.
"""
import re, json

PCB = '/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb'
DRC = '/tmp/drc_p5f.json'

with open(PCB) as f:
    text = f.read()
with open(DRC) as f:
    drc = json.load(f)

# Collect all references involved in violations
problem_refs = set()
for v in drc.get('violations', []):
    for item in v.get('items', []):
        desc = item.get('description', '')
        m = re.match(r'Reference field of (\w+)', desc)
        if m:
            problem_refs.add(m.group(1))
# Add edge clearance
for v in drc.get('violations', []):
    if v['type'] == 'silk_edge_clearance':
        for item in v.get('items', []):
            m = re.match(r'Reference field of (\w+)', item.get('description',''))
            if m:
                problem_refs.add(m.group(1))

print(f"Problem refs: {sorted(problem_refs)}")

def extract_balanced(text, start):
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
        i += 1
    return None, start

# Find all footprint blocks
i = 0
fp_data = {}
while True:
    idx = text.find('(footprint ', i)
    if idx < 0:
        break
    block, end = extract_balanced(text, idx)
    if not block:
        i = idx + 1
        continue
    
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    if not ref_m:
        i = idx + 1
        continue
    ref = ref_m.group(1)
    
    fp_m = re.search(r'\(footprint\s+"([^"]+)"', block)
    at_m = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    ref_at_m = re.search(
        r'\(property\s+"Reference"\s+"[^"]+"\s+\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)',
        block
    )
    
    if fp_m and at_m and ref_at_m:
        fp_data[ref] = {
            'fp': fp_m.group(1),
            'x': float(at_m.group(1)),
            'y': float(at_m.group(2)),
            'rot': float(at_m.group(3) or 0),
            'ref_dx': float(ref_at_m.group(1)),
            'ref_dy': float(ref_at_m.group(2)),
            'ref_rot': float(ref_at_m.group(3) or 0),
        }
    i = idx + 1

# Print data for problem refs
print("\n=== SILK_OVER_COPPER refs ===")
for v in drc.get('violations', []):
    if v['type'] == 'silk_over_copper':
        for item in v.get('items', []):
            m = re.match(r'Reference field of (\w+)', item.get('description',''))
            if m and m.group(1) in fp_data:
                ref = m.group(1)
                d = fp_data[ref]
                global_rx = d['x'] + d['ref_dx']
                global_ry = d['y'] + d['ref_dy']
                print(f"  {ref}: fp={d['fp']} pos=({d['x']},{d['y']}) rot={d['rot']} "
                      f"ref_local=({d['ref_dx']},{d['ref_dy']}) ref_global≈({global_rx:.1f},{global_ry:.1f})")

print("\n=== IC/CAP pairs (ref vs ref) ===")
for v in drc.get('violations', []):
    if v['type'] == 'silk_overlap':
        items = v.get('items', [])
        refs = []
        for item in items:
            m = re.match(r'Reference field of (\w+)', item.get('description',''))
            if m:
                refs.append(m.group(1))
        if len(refs) == 2:
            r1, r2 = refs
            if r1 in fp_data and r2 in fp_data:
                d1, d2 = fp_data[r1], fp_data[r2]
                print(f"  {r1}({d1['fp'][:20]}) @ ({d1['x']},{d1['y']},{d1['rot']}) ref=({d1['ref_dx']},{d1['ref_dy']})" 
                      f" <-> {r2}({d2['fp'][:20]}) @ ({d2['x']},{d2['y']},{d2['rot']}) ref=({d2['ref_dx']},{d2['ref_dy']})")

print("\n=== EDGE CLEARANCE refs ===")
for ref in ['MH1', 'MH2']:
    if ref in fp_data:
        d = fp_data[ref]
        print(f"  {ref}: pos=({d['x']},{d['y']}) rot={d['rot']} ref_local=({d['ref_dx']},{d['ref_dy']})")

print("\n=== XLR connector positions ===")
for ref in sorted(fp_data.keys()):
    if ref.startswith('J') and 'XLR' in fp_data[ref]['fp']:
        d = fp_data[ref]
        print(f"  {ref}: pos=({d['x']},{d['y']}) rot={d['rot']} ref_local=({d['ref_dx']},{d['ref_dy']})")
