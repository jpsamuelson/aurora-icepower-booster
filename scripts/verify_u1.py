#!/usr/bin/env python3
"""Verify U1 connections after fix by checking netlist."""
import re, subprocess

# Export netlist
SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
NET = "/tmp/u1_verify.net"
r = subprocess.run([
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "sch", "export", "netlist", "--output", NET, SCH
], capture_output=True, text=True, timeout=30)
assert r.returncode == 0, f"Netlist export failed: {r.stderr}"

with open(NET, 'r') as f:
    netlist = f.read()

# Find all U1 pins in the netlist
print("=== U1 TEL5-2422 Pin Connections ===")
# Find U1 component block
u1_match = re.search(r'\(comp\s+\(ref\s+"U1"\).*?\n\s+\)', netlist, re.DOTALL)
if u1_match:
    print(f"U1 found in netlist ✓")

# Find all nets containing U1
u1_nets = re.findall(r'\(net\s+\(code\s+"(\d+)"\)\s+\(name\s+"([^"]*)"\).*?\)', netlist, re.DOTALL)
for code, name in u1_nets:
    # Check if this net has U1 pins
    net_block_match = re.search(
        rf'\(net\s+\(code\s+"{code}"\).*?(?=\(net\s+\(code|\Z)', 
        netlist, re.DOTALL
    )
    if net_block_match:
        net_block = net_block_match.group(0)
        u1_pins = re.findall(r'\(node\s+\(ref\s+"U1"\)\s+\(pin\s+"(\d+)"\)', net_block)
        if u1_pins:
            # Find all nodes in this net
            all_nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', net_block)
            print(f"\n  Net '{name}' (code {code}):")
            for ref, pin in all_nodes:
                marker = " ← U1" if ref == "U1" else ""
                print(f"    {ref}.{pin}{marker}")

# Summary: check all 8 U1 pins
print("\n=== PIN SUMMARY ===")
all_u1_pins = set()
for code, name in u1_nets:
    net_block_match = re.search(
        rf'\(net\s+\(code\s+"{code}"\).*?(?=\(net\s+\(code|\Z)', 
        netlist, re.DOTALL
    )
    if net_block_match:
        pins = re.findall(r'\(node\s+\(ref\s+"U1"\)\s+\(pin\s+"(\d+)"\)', net_block_match.group(0))
        all_u1_pins.update(pins)
        
expected = {'2', '3', '9', '11', '14', '16', '22', '23'}
connected = all_u1_pins
unconnected = expected - connected
print(f"Expected pins: {sorted(expected, key=int)}")
print(f"Connected pins: {sorted(connected, key=int)}")
if unconnected:
    print(f"❌ UNCONNECTED: {sorted(unconnected, key=int)}")
else:
    print(f"✅ All 8 pins connected!")
