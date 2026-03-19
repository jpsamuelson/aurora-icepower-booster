#!/usr/bin/env python3
"""Fix Pin 2 mid-wire issue: split VOUT tie wire into two segments."""
import uuid, subprocess

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, 'r') as f:
    content = f.read()

original_len = len(content)

# Replace single wire (150.16, 22.38)→(150.16, 27.46) with two segments
old = '(wire (pts (xy 150.16 22.38) (xy 150.16 27.46))'
assert old in content, f"Wire not found!"

# Replace with two wires: Pin1→Pin2, Pin2→Pin3
uuid1 = str(uuid.uuid4())
uuid2 = str(uuid.uuid4())

# Find the full line to get the UUID
idx = content.find(old)
line_start = content.rfind('\n', 0, idx) + 1
line_end = content.find('\n', idx)
old_line = content[line_start:line_end]

new_lines = (
    f'  (wire (pts (xy 150.16 22.38) (xy 150.16 24.92)) (stroke (width 0) (type default)) (uuid "{uuid1}"))\n'
    f'  (wire (pts (xy 150.16 24.92) (xy 150.16 27.46)) (stroke (width 0) (type default)) (uuid "{uuid2}"))'
)

content = content[:line_start] + new_lines + content[line_end:]

# Validate
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket imbalance: {depth}"

with open(SCH, 'w') as f:
    f.write(content)

print(f"✅ Split VOUT wire: (22.38→27.46) → (22.38→24.92) + (24.92→27.46)")
print(f"   Size: {original_len} → {len(content)}")

# Verify
r = subprocess.run([
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "sch", "export", "netlist", "--output", "/tmp/u14_fix2.net", SCH
], capture_output=True, text=True, timeout=30)
print(f"   Netlist: {'OK' if r.returncode == 0 else 'FAILED'}")
