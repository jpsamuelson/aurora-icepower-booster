#!/usr/bin/env python3
"""Verify U14 ADP7118ARDZ connections after fix."""
import re, subprocess

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
NET = "/tmp/u14_verify.net"
r = subprocess.run([
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "sch", "export", "netlist", "--output", NET, SCH
], capture_output=True, text=True, timeout=30)
assert r.returncode == 0

with open(NET, 'r') as f:
    netlist = f.read()

# Find all nets containing U14 pins
u14_nets = re.findall(r'\(net\s+\(code\s+"(\d+)"\)\s+\(name\s+"([^"]*)"\).*?\)', netlist, re.DOTALL)

print("=== U14 ADP7118ARDZ Pin Connections ===")
all_u14_pins = set()
for code, name in u14_nets:
    net_block_match = re.search(
        rf'\(net\s+\(code\s+"{code}"\).*?(?=\(net\s+\(code|\Z)', 
        netlist, re.DOTALL
    )
    if net_block_match:
        net_block = net_block_match.group(0)
        u14_pins = re.findall(r'\(node\s+\(ref\s+"U14"\)\s+\(pin\s+"(\d+)"\)', net_block)
        if u14_pins:
            all_u14_pins.update(u14_pins)
            all_nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', net_block)
            print(f"\n  Net '{name}' (code {code}):")
            for ref, pin in all_nodes:
                marker = " ← U14" if ref == "U14" else ""
                print(f"    {ref}.{pin}{marker}")

# Verify expected connections
print("\n=== PIN VERIFICATION ===")
expected = {
    '1': 'V+',      # VOUT → V+
    '2': 'V+',      # VOUT → V+ (tied to Pin 1)
    '3': 'V+',      # SENSE → V+ (tied to VOUT)
    '4': 'GND',     # GND
    '5': 'EN_CTRL', # EN → EN_CTRL
    '6': 'SS_U14',  # SS → SS_U14
    '7': '+12V',    # VIN → +12V
    '8': '+12V',    # VIN → +12V (tied to Pin 7)
    '9': 'GND',     # EP → GND
}

expected_pins = set(expected.keys())
connected = all_u14_pins
unconnected = expected_pins - connected

print(f"Expected: {sorted(expected_pins, key=int)}")
print(f"Connected: {sorted(connected, key=int)}")
if unconnected:
    print(f"❌ UNCONNECTED: {sorted(unconnected, key=int)}")
else:
    print(f"✅ All 9 pins connected!")

# Check net assignments
for code, name in u14_nets:
    net_block_match = re.search(
        rf'\(net\s+\(code\s+"{code}"\).*?(?=\(net\s+\(code|\Z)', 
        netlist, re.DOTALL
    )
    if net_block_match:
        net_block = net_block_match.group(0)
        u14_pins = re.findall(r'\(node\s+\(ref\s+"U14"\)\s+\(pin\s+"(\d+)"\)', net_block)
        for pin in u14_pins:
            exp_net = expected.get(pin, '?')
            # Check if net name contains expected string
            if exp_net in name or ('/' + exp_net) in name:
                print(f"  Pin {pin} ({exp_net}): ✅ on '{name}'")
            elif name == exp_net:
                print(f"  Pin {pin} ({exp_net}): ✅ on '{name}'")
            else:
                print(f"  Pin {pin} ({exp_net}): ❌ WRONG — on '{name}' (expected '{exp_net}')")
