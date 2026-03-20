#!/usr/bin/env python3
"""
Phase 6: Run DRC on the routed board and analyze results.
"""
import subprocess, json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
DRC_JSON = '/tmp/aurora-drc-routed.json'

print(f'Running DRC on: {PCB}')
result = subprocess.run(
    ['kicad-cli', 'pcb', 'drc',
     '--output', DRC_JSON,
     '--format', 'json',
     '--severity-all',
     PCB],
    capture_output=True, text=True, timeout=120
)

if result.returncode != 0 and not os.path.exists(DRC_JSON):
    print(f'DRC failed: {result.stderr}')
    sys.exit(1)

with open(DRC_JSON) as f:
    drc = json.load(f)

violations = drc.get('violations', [])
unconnected = drc.get('unconnected_items', [])

# Count by severity and type
errors = [v for v in violations if v.get('severity') == 'error']
warnings = [v for v in violations if v.get('severity') == 'warning']

by_type = {}
for v in violations:
    t = v.get('type', 'unknown')
    sev = v.get('severity', '?')
    by_type.setdefault(t, {'error': 0, 'warning': 0})
    by_type[t][sev] = by_type[t].get(sev, 0) + 1

print(f'\n{"="*60}')
print(f'DRC RESULTS')
print(f'{"="*60}')
print(f'  Errors:      {len(errors)}')
print(f'  Warnings:    {len(warnings)}')
print(f'  Unconnected: {len(unconnected)}')

if by_type:
    print(f'\n  By type:')
    for t, counts in sorted(by_type.items()):
        parts = []
        if counts.get('error', 0) > 0:
            parts.append(f'{counts["error"]} err')
        if counts.get('warning', 0) > 0:
            parts.append(f'{counts["warning"]} warn')
        print(f'    {t:35s} {", ".join(parts)}')

# Show first few errors in detail
if errors:
    print(f'\n  First errors:')
    for e in errors[:5]:
        desc = e.get('description', '?')
        items = e.get('items', [])
        item_info = ', '.join(i.get('description', '?')[:50] for i in items[:2])
        print(f'    ❌ {desc[:60]}')
        if item_info:
            print(f'       {item_info}')

if unconnected:
    # Group by net
    net_counts = {}
    for u in unconnected:
        items = u.get('items', [])
        for item in items:
            desc = item.get('description', '')
            net_m = None
            if 'Net' in desc:
                net_m = desc
            if net_m:
                net_counts[net_m] = net_counts.get(net_m, 0) + 1

    print(f'\n  Unconnected summary: {len(unconnected)} items')
    if len(unconnected) <= 10:
        for u in unconnected:
            items = u.get('items', [])
            descs = [i.get('description', '?')[:60] for i in items[:2]]
            print(f'    → {" | ".join(descs)}')

if len(errors) == 0 and len(unconnected) == 0:
    print(f'\n✅ DRC PASSED — 0 errors, 0 unconnected!')
elif len(errors) == 0:
    print(f'\n⚠️  0 errors but {len(unconnected)} unconnected items')
else:
    print(f'\n❌ {len(errors)} errors, {len(unconnected)} unconnected')
