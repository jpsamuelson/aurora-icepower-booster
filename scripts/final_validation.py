#!/usr/bin/env python3
"""Final validation of all schematic fixes."""
import subprocess, re, sys

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

# Step 1: Bracket balance
with open(SCH) as f:
    text = f.read()
depth = 0
for c in text:
    if c == '(': depth += 1
    elif c == ')': depth -= 1
print(f"[1] Bracket balance: {'OK' if depth == 0 else f'FAIL ({depth})'}")

# Step 2: Netlist export
net_out = "/tmp/final_netlist.net"
r = subprocess.run([CLI, "sch", "export", "netlist", "--output", net_out, SCH],
                   capture_output=True, text=True)
print(f"[2] Netlist export: {'OK' if r.returncode == 0 else 'FAIL'}")
if r.returncode != 0:
    print(f"    Error: {r.stderr[:300]}")
    sys.exit(1)

# Step 3: ERC 
erc_out = "/tmp/final_erc.json"
r = subprocess.run([CLI, "sch", "erc", "--output", erc_out, "--format", "json",
                    "--severity-all", SCH],
                   capture_output=True, text=True)
print(f"[3] ERC: exit code {r.returncode}")

# Parse ERC results
import json
try:
    with open(erc_out) as f:
        erc = json.load(f)
    
    violations = erc.get('violations', [])
    by_severity = {}
    by_type = {}
    for v in violations:
        sev = v.get('severity', 'unknown')
        typ = v.get('type', 'unknown')
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_type[typ] = by_type.get(typ, 0) + 1
    
    print(f"    ERC violations by severity: {by_severity}")
    print(f"    ERC violations by type:")
    for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"      {t}: {cnt}")
    
    # Show errors specifically
    errors = [v for v in violations if v.get('severity') == 'error']
    if errors:
        print(f"\n    ⚠️  ERC ERRORS ({len(errors)}):")
        for e in errors[:10]:
            desc = e.get('description', '')
            items = e.get('items', [])
            locs = '; '.join(f"{i.get('description','')}" for i in items[:2])
            print(f"      {desc} [{locs}]")
except Exception as ex:
    print(f"    ERC parse failed: {ex}")

# Step 4: Parse netlist and validate all key connections
with open(net_out) as f:
    c = f.read()

nets = {}
for m in re.finditer(r'\(net \(code "(\d+)"\) \(name "([^"]*)"\)', c):
    name = m.group(2)
    start = m.start()
    depth = 0
    for i in range(start, len(c)):
        if c[i] == '(': depth += 1
        elif c[i] == ')': depth -= 1
        if depth == 0: break
    block = c[start:i+1]
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)
    nets[name] = nodes

p2n = {}
for n, nodes in nets.items():
    for ref, pin in nodes:
        p2n[(ref, pin)] = n

print(f"\n[4] Netlist analysis: {len(nets)} nets")

# ===== F1: GND separated from OUT_COLD =====
print(f"\n--- F1: GND Separation ---")
gnd_count = len(nets.get('GND', []))
print(f"  GND nodes: {gnd_count}")
# Check BSS138 sources are on GND
for q in ['Q1','Q2','Q3','Q4','Q5','Q6','Q7']:
    net = p2n.get((q, '2'), '?')
    ok = net == 'GND'
    if not ok: print(f"  ✗ {q}.Source → {net} (expected GND)")
    
# Check OUT_COLD exists as separate nets
for ch in range(1, 7):
    net = f'/CH{ch}_OUT_COLD'
    nodes = nets.get(net, [])
    ok = len(nodes) >= 3
    if ok: print(f"  ✓ {net}: {len(nodes)} nodes")
    else: print(f"  ✗ {net}: {len(nodes)} nodes (expected ≥3)")

# ===== F2: HOT_RAW separated from OUT_COLD =====
print(f"\n--- F2: Input/Output Separation ---")
for ch in range(1, 7):
    j_in = f'J{ch+2}'  # J3-J8
    j_out = f'J{ch+8}'  # J9-J14
    
    in_hot = p2n.get((j_in, '2'), '?')
    out_cold = p2n.get((j_out, '3'), '?')
    
    in_ok = 'HOT_RAW' in in_hot
    out_ok = 'OUT_COLD' in out_cold
    separate = in_hot != out_cold
    
    print(f"  CH{ch}: {j_in}.2→{in_hot} {'✓' if in_ok else '✗'} | {j_out}.3→{out_cold} {'✓' if out_ok else '✗'} | Separate: {'✓' if separate else '✗'}")

# ===== F4: Negative Feedback =====
print(f"\n--- F4: Feedback R20-R25 ---")
all_ok = True
for ch, ref in enumerate(['R20','R21','R22','R23','R24','R25'], 1):
    p1 = p2n.get((ref, '1'), '?')
    p2 = p2n.get((ref, '2'), '?')
    ok1 = 'INV_IN' in p1
    ok2 = 'RX_OUT' in p2
    if ok1 and ok2:
        print(f"  ✓ {ref}: INV_IN ↔ RX_OUT (negative feedback)")
    else:
        all_ok = False
        print(f"  ✗ {ref}: {p1} ↔ {p2}")

# ===== F5+F6: Rgnd =====
print(f"\n--- F5+F6: Rgnd Resistors ---")
for ch, ref in enumerate(['R2','R4','R6','R8','R10','R12'], 1):
    p1 = p2n.get((ref, '1'), '?')
    p2 = p2n.get((ref, '2'), '?')
    ok1 = p1 == 'GND'
    ok2 = 'HOT_IN' in p2
    if ok1 and ok2:
        print(f"  ✓ {ref}: GND ↔ HOT_IN")
    else:
        print(f"  ✗ {ref}: {p1} ↔ {p2}")

# ===== F9: ADP7118 ARDZ =====
print(f"\n--- F9: ADP7118ARDZ ---")
u14_lib = '?'
for m in re.finditer(r'\(symbol \(lib_id "([^"]+)".*?property "Reference" "U14"', text, re.DOTALL):
    u14_lib = m.group(1)
    break
print(f"  U14 lib_id: {u14_lib} {'✓' if 'ADP7118ARDZ' in u14_lib else '✗'}")

# ===== F10: TEL5-2422 =====
print(f"\n--- F10: TEL5-2422 ---")
u1_lib = '?'
for m in re.finditer(r'\(symbol \(lib_id "([^"]+)".*?property "Reference" "U1"', text, re.DOTALL):
    u1_lib = m.group(1)
    break
print(f"  U1 lib_id: {u1_lib} {'✓' if 'TEL5-2422' in u1_lib else '✗'}")
# Check TEL5-2422 pins
tel5_pins = {}
for pin_name in ['2', '3', '9', '11', '14', '16', '22', '23']:
    tel5_pins[pin_name] = p2n.get(('U1', pin_name), '?') 
print(f"  U1 pins: {tel5_pins}")

# ===== Signal Chain Integrity =====
print(f"\n--- Signal Chain Integrity (CH1) ---")
chain = [
    ('J3.2', 'HOT_RAW', p2n.get(('J3','2'), '?')),
    ('R94.1→HOT_RAW', 'HOT_RAW', p2n.get(('R94','1'), '?')),
    ('R94.2→EMI_HOT', 'EMI_HOT', p2n.get(('R94','2'), '?')),
    ('C62.2→HOT_IN', 'HOT_IN', p2n.get(('C62','2'), '?')),
    ('U2.3→HOT_IN(NINV)', 'HOT_IN', p2n.get(('U2','3'), '?')),
    ('R2.2→HOT_IN', 'HOT_IN', p2n.get(('R2','2'), '?')),
    ('R2.1→GND', 'GND', p2n.get(('R2','1'), '?')),
    ('U2.2→INV_IN', 'INV_IN', p2n.get(('U2','2'), '?')),
    ('R20.1→INV_IN(Rfb)', 'INV_IN', p2n.get(('R20','1'), '?')),
    ('R20.2→RX_OUT', 'RX_OUT', p2n.get(('R20','2'), '?')),
    ('U2.1→RX_OUT', 'RX_OUT', p2n.get(('U2','1'), '?')),
]
for desc, expected, actual in chain:
    ok = expected in actual
    print(f"  {'✓' if ok else '✗'} {desc}: {actual}")

# Summary
print(f"\n{'='*60}")
print(f"FINAL SUMMARY")
print(f"{'='*60}")
print(f"  Schematic size: {len(text)} chars")
print(f"  Total nets: {len(nets)}")
print(f"  GND nodes: {gnd_count}")
unconnected = [n for n in nets if 'unconnected' in n.lower()]
print(f"  Unconnected pins: {len(unconnected)}")
for u in unconnected:
    for ref, pin in nets[u]:
        print(f"    {ref}.{pin} → {u}")
