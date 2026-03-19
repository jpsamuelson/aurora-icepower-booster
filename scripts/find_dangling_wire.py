#!/usr/bin/env python3
"""Find the exact unconnected_wire_endpoint warning from ERC JSON."""
import json

with open('/tmp/erc_revalidation.json') as f:
    data = json.load(f)

violations = data['sheets'][0]['violations']
for v in violations:
    if v['type'] == 'unconnected_wire_endpoint':
        print(json.dumps(v, indent=2))

# Also find exact coordinates
print('\n--- Checking position ---')
for v in violations:
    if v['type'] == 'unconnected_wire_endpoint':
        for item in v.get('items', []):
            pos = item.get('pos', {})
            # These are in mm (coordinate_units field)
            x = pos.get('x', 0) * 100  # Convert if needed
            y = pos.get('y', 0) * 100
            print(f'Position raw: ({pos.get("x")}, {pos.get("y")})')
            print(f'Position *100: ({x}, {y})')
