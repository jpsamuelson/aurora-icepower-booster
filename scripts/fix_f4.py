#!/usr/bin/env python3
"""Fix F4: Reconnect feedback R20-R25 from HOT_IN (+) to INV_IN (-).
For each channel:
1. Remove wire from R*.pin1 to HOT_IN junction
2. Add short wire stub at R*.pin1 + INV_IN label"""
import re, uuid, subprocess

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH) as f:
    text = f.read()
orig_len = len(text)

# R20-R25 pin1 positions (x=80, y=ch_y-13.81 for rot=0° resistors at ch_y-10)
# R20 at (80, 100) → pin1 at (80, 96.19) 
# Pattern: pin1_y = resistor_y - 3.81 = (ch_y - 10) - 3.81 = ch_y - 13.81
ch_y = {1: 110, 2: 190, 3: 270, 4: 350, 5: 430, 6: 510}
# HOT_IN junction point: (72.38, ch_y - 2.54) based on CH1 analysis
# CH1: junction at (72.38, 107.46) = (72.38, 110 - 2.54) ✓

channels = {
    1: {'ref': 'R20', 'pin1': (80, 96.19), 'junction': (72.38, 107.46), 'label': 'CH1_INV_IN'},
    2: {'ref': 'R21', 'pin1': (80, 176.19), 'junction': (72.38, 187.46), 'label': 'CH2_INV_IN'},
    3: {'ref': 'R22', 'pin1': (80, 256.19), 'junction': (72.38, 267.46), 'label': 'CH3_INV_IN'},
    4: {'ref': 'R23', 'pin1': (80, 336.19), 'junction': (72.38, 347.46), 'label': 'CH4_INV_IN'},
    5: {'ref': 'R24', 'pin1': (80, 416.19), 'junction': (72.38, 427.46), 'label': 'CH5_INV_IN'},
    6: {'ref': 'R25', 'pin1': (80, 496.19), 'junction': (72.38, 507.46), 'label': 'CH6_INV_IN'},
}

# Step 1: Remove wires from R*.pin1 to HOT_IN junction
removed = 0
for ch, info in channels.items():
    px, py = info['pin1']
    jx, jy = info['junction']
    
    # Search for wire with these endpoints (either order)
    found = False
    for pattern in [
        rf'\(wire \(pts \(xy {px} {py}\) \(xy {jx} {jy}\)\)',
        rf'\(wire \(pts \(xy {jx} {jy}\) \(xy {px} {py}\)\)',
    ]:
        m = re.search(pattern, text)
        if m:
            # Extract full wire block
            start = m.start()
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '(': depth += 1
                elif text[i] == ')': depth -= 1
                if depth == 0: break
            # Remove wire block (with preceding whitespace)
            pre = start
            while pre > 0 and text[pre-1] in ' \t':
                pre -= 1
            if pre > 0 and text[pre-1] == '\n':
                pre -= 1
            text = text[:pre] + text[i+1:]
            removed += 1
            found = True
            print(f"  CH{ch}: Removed wire ({px}, {py}) → ({jx}, {jy})")
            break
    
    if not found:
        print(f"  CH{ch}: WARNING - wire not found, trying flexible search")
        # Try with approximate coordinates
        for wm in re.finditer(r'\(wire \(pts \(xy ([\d.]+) ([\d.]+)\) \(xy ([\d.]+) ([\d.]+)\)\)', text):
            wx1, wy1 = float(wm.group(1)), float(wm.group(2))
            wx2, wy2 = float(wm.group(3)), float(wm.group(4))
            if ((abs(wx1-px)<0.1 and abs(wy1-py)<0.1 and abs(wx2-jx)<0.1 and abs(wy2-jy)<0.1) or
                (abs(wx2-px)<0.1 and abs(wy2-py)<0.1 and abs(wx1-jx)<0.1 and abs(wy1-jy)<0.1)):
                start = wm.start()
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
                print(f"  CH{ch}: Removed wire ({wx1}, {wy1}) → ({wx2}, {wy2}) [approx match]")
                found = True
                break
        if not found:
            print(f"  CH{ch}: FAILED to find wire!")

print(f"\nRemoved {removed}/6 wires")

# Step 2: Add INV_IN labels at R*.pin1 positions
# Add short wire stubs (1 unit left) + INV_IN labels
insert_pos = text.rfind(')')
new_elements = []

for ch, info in channels.items():
    px, py = info['pin1']
    label_name = info['label']
    uid_wire = str(uuid.uuid4())
    uid_label = str(uuid.uuid4())
    
    # Short wire from pin1 going left
    stub_x = px - 1  # 1 unit to the left
    wire_str = f'(wire (pts (xy {px} {py}) (xy {stub_x} {py})) (stroke (width 0) (type default)) (uuid "{uid_wire}"))'
    new_elements.append(wire_str)
    
    # Label at the stub end, pointing left (angle 180)
    label_str = f'(label "{label_name}" (at {stub_x} {py} 180) (effects (font (size 1.27 1.27))) (uuid "{uid_label}"))'
    new_elements.append(label_str)
    
    print(f"  CH{ch}: Added wire ({px}, {py}) → ({stub_x}, {py}) + label {label_name}")

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
out = "/tmp/test_netlist_f4.net"
r = subprocess.run([cli, "sch", "export", "netlist", "--output", out, SCH],
                   capture_output=True, text=True)
print(f"Netlist export: {'OK' if r.returncode == 0 else 'FAIL'}")
if r.returncode != 0:
    print(r.stderr[:500])
    exit(1)

# Check R20-R25 connections
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
    for ref, pin in nodes:
        pin_to_net[(ref, pin)] = nname

print("\n=== Feedback R20-R25 after fix ===")
for ref in ['R20','R21','R22','R23','R24','R25']:
    p1_net = pin_to_net.get((ref, '1'), 'NOT FOUND')
    p2_net = pin_to_net.get((ref, '2'), 'NOT FOUND')
    p1_ok = 'INV_IN' in p1_net
    p2_ok = 'RX_OUT' in p2_net
    print(f"  {ref}.1 → {p1_net} {'✓' if p1_ok else '✗'}")
    print(f"  {ref}.2 → {p2_net} {'✓' if p2_ok else '✗'}")
