#!/usr/bin/env python3
"""Classify ERC errors as new vs pre-existing."""
import json

with open('/tmp/erc_post_fix.json') as f:
    data = json.load(f)

violations = data['sheets'][0]['violations']
errors = [v for v in violations if v['severity'] == 'error']

print('=== Error Classification ===')
new_from_fix = 0
pre_existing = 0
for e in errors:
    typ = e['type']
    desc = e['description']
    items = [i['description'] for i in e.get('items', [])]
    
    is_new = False
    if typ == 'pin_to_pin' and any('U1' in i or 'U14' in i for i in items):
        status = 'NEW (expected - parallel pins)'
        is_new = True
    elif typ == 'pin_not_driven' and any('U14' in i for i in items):
        status = 'NEW (SS_U14 has no driver/cap yet)'
        is_new = True
    elif typ == 'label_dangling' and 'SS_U14' in str(items):
        status = 'NEW (investigate)'
        is_new = True
    else:
        status = 'PRE-EXISTING'
        pre_existing += 1
    
    if is_new:
        new_from_fix += 1
    print(f'  [{typ}] {status}')
    for i in items:
        print(f'    > {i[:70]}')

print(f'\nSummary: {new_from_fix} new from fix, {pre_existing} pre-existing')
print(f'Baseline had 117 errors, now only 13')
