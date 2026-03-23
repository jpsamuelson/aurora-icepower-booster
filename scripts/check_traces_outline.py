#!/usr/bin/env python3
"""Final check: Trace width distribution + netclass pattern matching + Board outline."""
import re, json
from collections import Counter, defaultdict

with open("aurora-dsp-icepower-booster.kicad_pcb") as f:
    pcb = f.read()

with open("aurora-dsp-icepower-booster.kicad_pro") as f:
    pro = json.load(f)

# Parse segments (multiline format)
widths = Counter()
net_widths = defaultdict(lambda: Counter())
for m in re.finditer(r'\(segment\s+\(start [\d.]+ [\d.]+\)\s+\(end [\d.]+ [\d.]+\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net (\d+)\)', pcb):
    w = float(m.group(1))
    layer = m.group(2)
    nid = int(m.group(3))
    widths[w] += 1
    net_widths[nid][w] += 1

print("Trace width distribution:")
for w, c in widths.most_common():
    print(f"  {w}mm: {c} segments")

# Parse net map
net_map = {}
for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', pcb):
    net_map[int(m.group(1))] = m.group(2)

# Apply netclass patterns
patterns = pro.get("net_settings", {}).get("netclass_patterns", None) or []
import fnmatch
def get_netclass(net_name):
    for p in patterns:
        if fnmatch.fnmatch(net_name, p["pattern"]):
            return p["netclass"]
    return "Default"

print("\nNets with non-default (>0.25mm) trace widths:")
for nid, ws in sorted(net_widths.items()):
    name = net_map.get(nid, f"net_{nid}")
    nc = get_netclass(name)
    non_default = {w: c for w, c in ws.items() if w != 0.25}
    if non_default:
        print(f"  {name:25s} [{nc:15s}] widths={dict(ws)}")

# Cross-check: Do netclass patterns actually result in wider traces?
print("\nNetclass pattern validation:")
nc_actual = defaultdict(list)
for nid, ws in net_widths.items():
    name = net_map.get(nid, f"net_{nid}")
    nc = get_netclass(name)
    nc_actual[nc].extend(ws.keys())

for nc_name, actual_widths in sorted(nc_actual.items()):
    min_w = min(actual_widths)
    max_w = max(actual_widths)
    print(f"  {nc_name:15s}: actual width range {min_w:.2f}-{max_w:.2f}mm  ({len(actual_widths)} segments)")

# Net count per class
print("\nNets per class:")
net_classes = Counter()
for nid, name in net_map.items():
    nc = get_netclass(name)
    net_classes[nc] += 1
for nc, count in net_classes.most_common():
    print(f"  {nc}: {count} nets")

# Board outline check
print("\nBoard Outline:")
# Check for fp_line on Edge.Cuts within footprints — the board outline might be in a footprint
edge_fp = re.findall(r'\(fp_line.*?\(layer "Edge\.Cuts"\)', pcb)
print(f"  fp_line on Edge.Cuts: {len(edge_fp)}")

# Check for gr_poly  
edge_poly = re.findall(r'\(gr_poly.*?\(layer "Edge\.Cuts"\)', pcb, re.DOTALL)
print(f"  gr_poly on Edge.Cuts: {len(edge_poly)}")

# Check gr_rect
edge_rect = re.findall(r'\(gr_rect.*?\(layer "Edge\.Cuts"\)', pcb, re.DOTALL)
print(f"  gr_rect on Edge.Cuts: {len(edge_rect)}")

# Actually search for ANY Edge.Cuts content
edge_any = re.findall(r'Edge\.Cuts', pcb)
print(f"  Total Edge.Cuts references: {len(edge_any)}")

# Find edge cuts content
for m in re.finditer(r'[^\n]*Edge\.Cuts[^\n]*', pcb):
    line = pcb[max(0,m.start()-50):m.end()+50].replace('\n', ' ').strip()
    if 'fp_line' not in line and 'pad' not in line:
        print(f"  Found: ...{line[:120]}...")
        break

# Get board setup dimensions
setup_m = re.search(r'\(setup\s+(.*?)\n\t\)', pcb, re.DOTALL)
if setup_m:
    setup = setup_m.group(1)
    # Look for page size or board dimensions
    page_m = re.search(r'\(page "([\w]+)"\)', pcb)
    if page_m:
        print(f"  Page: {page_m.group(1)}")
    
    # Look for aux_axis_origin (board origin)
    origin = re.search(r'\(aux_axis_origin ([\d.]+) ([\d.]+)\)', pcb)
    if origin:
        print(f"  Aux Origin: ({origin.group(1)}, {origin.group(2)})")
