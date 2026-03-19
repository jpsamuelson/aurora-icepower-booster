#!/usr/bin/env python3
"""Fix F5+F6: Connect Rgnd R2,R4,R6,R8,R10,R12 pin1 to GND.
1. Remove wires from R4-R12.pin1 to HOT_IN junctions (R2 has no wire — F5)
2. Add GND power symbol at each Rgnd.pin1 position"""
import re, uuid, subprocess

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()
orig_len = len(text)

# First, get the power:GND symbol definition from one existing instance
# to know the exact format to replicate
gnd_m = re.search(r'\(symbol \(lib_id "power:GND"\)', text)
if gnd_m:
    start = gnd_m.start()
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        if depth == 0: break
    example_gnd = text[start:i+1]
    print(f"Found example GND symbol ({len(example_gnd)} chars)")
else:
    print("ERROR: No power:GND symbol found!")
    exit(1)

# Rgnd info
rgnd_pins = {
    1: {'ref': 'R2', 'pin1': (55.0, 103.19), 'wire_to': None},
    2: {'ref': 'R4', 'pin1': (55.0, 183.19), 'wire_to': (72.38, 187.46)},
    3: {'ref': 'R6', 'pin1': (55.0, 263.19), 'wire_to': (72.38, 267.46)},
    4: {'ref': 'R8', 'pin1': (55.0, 343.19), 'wire_to': (72.38, 347.46)},
    5: {'ref': 'R10', 'pin1': (55.0, 423.19), 'wire_to': (72.38, 427.46)},
    6: {'ref': 'R12', 'pin1': (55.0, 503.19), 'wire_to': (72.38, 507.46)},
}

# Step 1: Remove wires from R4-R12.pin1
removed = 0
for ch, info in rgnd_pins.items():
    if info['wire_to'] is None:
        continue  # R2 has no wire
    
    px, py = info['pin1']
    jx, jy = info['wire_to']
    
    found = False
    for m in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
        x1, y1 = float(m.group(1)), float(m.group(2))
        x2, y2 = float(m.group(3)), float(m.group(4))
        if ((abs(x1-px)<0.1 and abs(y1-py)<0.1 and abs(x2-jx)<0.1 and abs(y2-jy)<0.1) or
            (abs(x2-px)<0.1 and abs(y2-py)<0.1 and abs(x1-jx)<0.1 and abs(y1-jy)<0.1)):
            start = m.start()
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '(': depth += 1
                elif text[i] == ')': depth -= 1
                if depth == 0: break
            pre = start
            while pre > 0 and text[pre-1] in ' \t':
                pre -= 1
            if pre > 0 and text[pre-1] == '\n':
                pre -= 1
            text = text[:pre] + text[i+1:]
            removed += 1
            print(f"  CH{ch} {info['ref']}: Removed wire ({px}, {py}) → ({jx}, {jy})")
            found = True
            break
    
    if not found:
        print(f"  CH{ch} {info['ref']}: WARNING - wire not found!")

print(f"\nRemoved {removed}/5 wires")

# Step 2: Add GND power symbols at each Rgnd.pin1
# The power:GND symbol has a pin at offset. Let me find the pin offset.
# From the existing example, extract the 'at' of the symbol and the pin UUID.
# The GND symbol connects through its pin, which in the schematic is at the
# symbol's (at X Y) position + the pin's offset from the library.
#
# Looking at existing GND symbols: they are placed at positions where their
# pin connects to a wire endpoint. The pin offset in power:GND is typically
# (0, 0) or very small.
#
# For simplicity: place GND symbol at pin1 position with a short wire going down

insert_pos = text.rfind(')')
new_elements = []

# Next available PWR number
pwr_nums = [int(m.group(1)) for m in re.finditer(r'#PWR(\d+)', text)]
next_pwr = max(pwr_nums) + 1 if pwr_nums else 200

for ch, info in rgnd_pins.items():
    px, py = info['pin1']
    ref = info['ref']
    
    # GND symbol position: below pin1 (add 2.54 units down for clearance)
    gnd_y = py + 2.54
    
    uid_wire = str(uuid.uuid4())
    uid_sym = str(uuid.uuid4())
    uid_pin = str(uuid.uuid4())
    pwr_ref = f"#PWR{next_pwr:03d}"
    next_pwr += 1
    
    # Wire from pin1 going down to GND symbol position
    wire_str = f'(wire (pts (xy {px} {py}) (xy {px} {gnd_y})) (stroke (width 0) (type default)) (uuid "{uid_wire}"))'
    new_elements.append(wire_str)
    
    # GND power symbol (copy format from existing but with new position/UUID)
    gnd_str = (
        f'(symbol (lib_id "power:GND") (at {px} {gnd_y} 0) (unit 1)'
        f' (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
        f' (fields_autoplaced yes)'
        f' (uuid "{uid_sym}")'
        f' (property "Reference" "{pwr_ref}" (at {px} {gnd_y + 1.27} 0)'
        f' (effects (font (size 1.27 1.27)) hide))'
        f' (property "Value" "GND" (at {px} {gnd_y + 3.81} 0)'
        f' (effects (font (size 1.27 1.27)) hide))'
        f' (property "Footprint" "" (at {px} {gnd_y} 0)'
        f' (effects (font (size 1.27 1.27)) hide))'
        f' (property "Datasheet" "" (at {px} {gnd_y} 0)'
        f' (effects (font (size 1.27 1.27)) hide))'
        f' (pin "1" (uuid "{uid_pin}")))'
    )
    new_elements.append(gnd_str)
    
    print(f"  CH{ch} {ref}: Added GND at ({px}, {gnd_y}) [{pwr_ref}]")

insert_text = '\n    ' + '\n    '.join(new_elements) + '\n  '
text = text[:insert_pos] + insert_text + text[insert_pos:]

# Verify bracket balance
depth = 0
for c in text:
    if c == '(': depth += 1
    elif c == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"
print(f"\nBracket balance: OK")

with open(SCH, 'w') as f:
    f.write(text)
print(f"Schematic written: {len(text)} chars (was {orig_len})")

# Verify with netlist export
cli = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
out = "/tmp/test_netlist_f56.net"
r = subprocess.run([cli, "sch", "export", "netlist", "--output", out, SCH],
                   capture_output=True, text=True)
print(f"Netlist export: {'OK' if r.returncode == 0 else 'FAIL'}")
if r.returncode != 0:
    print(r.stderr[:500])
    exit(1)

# Check Rgnd connections
with open(out) as f:
    c = f.read()

nets = {}
for nm in re.finditer(r'\(net \(code "(\d+)"\) \(name "([^"]*)"\)', c):
    code, name = nm.group(1), nm.group(2)
    start = nm.start()
    depth = 0
    for i in range(start, len(c)):
        if c[i] == '(': depth += 1
        elif c[i] == ')': depth -= 1
        if depth == 0: break
    block = c[start:i+1]
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)
    nets[name] = nodes

pin_to_net = {}
for nname, nodes in nets.items():
    for ref_n, pin in nodes:
        pin_to_net[(ref_n, pin)] = nname

print("\n=== Rgnd R2,R4,R6,R8,R10,R12 after fix ===")
for ref in ['R2','R4','R6','R8','R10','R12']:
    p1_net = pin_to_net.get((ref, '1'), 'NOT FOUND')
    p2_net = pin_to_net.get((ref, '2'), 'NOT FOUND')
    p1_ok = p1_net == 'GND'
    p2_ok = 'HOT_IN' in p2_net
    print(f"  {ref}.1 → {p1_net} {'✓' if p1_ok else '✗'}")
    print(f"  {ref}.2 → {p2_net} {'✓' if p2_ok else '✗'}")
