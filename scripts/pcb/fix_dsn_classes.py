#!/usr/bin/env python3
"""
Fix DSN file to apply proper netclass assignments and clearances.
pcbnew doesn't read .kicad_pro netclass_patterns, so we fix the DSN post-export.
"""
import re, json, os, fnmatch

DSN = '/tmp/aurora-booster.dsn'
PRO = 'aurora-dsp-icepower-booster.kicad_pro'

with open(PRO) as f:
    pro = json.load(f)

ns = pro['net_settings']
classes_def = {c['name']: c for c in ns['classes']}
patterns = ns.get('netclass_patterns', [])

with open(DSN) as f:
    dsn = f.read()

# Extract all net names from DSN class section (most reliable source)
all_nets = set()

# Find the class section and extract all net names from it
class_section = re.search(r'\(class kicad_default (.+?)\(circuit', dsn, re.DOTALL)
if class_section:
    net_text = class_section.group(1)
    # Match: /name, "quoted-name", or plain-word (like GND)
    for m in re.finditer(r'(/[A-Za-z0-9_+]+|"[^"]+"|(?<!\()\b[A-Z][A-Za-z0-9_]+\b)', net_text):
        name = m.group(0).strip('"')
        if name not in ('circuit', 'use_via', 'rule', 'width', 'clearance', 'type'):
            all_nets.add(name)

# Also extract from Power class (GND is here)
power_section = re.search(r'\(class Power (.+?)\(circuit', dsn, re.DOTALL)
if power_section:
    net_text = power_section.group(1)
    for m in re.finditer(r'(/[A-Za-z0-9_+]+|"[^"]+"|(?<!\()\b[A-Z][A-Za-z0-9_]+\b)', net_text):
        name = m.group(0).strip('"')
        if name not in ('circuit', 'use_via', 'rule', 'width', 'clearance', 'type'):
            all_nets.add(name)

print(f"Total nets in DSN: {len(all_nets)}")

# Apply netclass patterns to classify nets
def match_net(net_name, pattern):
    """Match net name against pattern (supports * wildcard)."""
    # Try various combinations: with/without leading /
    clean = net_name.lstrip('/')
    return (fnmatch.fnmatch(clean, pattern) or 
            fnmatch.fnmatch(net_name, pattern) or
            fnmatch.fnmatch(clean, pattern.lstrip('/')))

net_to_class = {}
for net in all_nets:
    net_to_class[net] = 'Default'  # default

# Apply patterns (last match wins)
for p in patterns:
    cls_name = p['netclass']
    pat = p['pattern']
    for net in all_nets:
        if match_net(net, pat):
            net_to_class[net] = cls_name

# Build class → nets mapping
class_nets = {}
for net, cls in net_to_class.items():
    class_nets.setdefault(cls, []).append(net)

# Print summary
for cls_name in sorted(class_nets.keys()):
    nets = class_nets[cls_name]
    cls_info = classes_def.get(cls_name, classes_def.get('Default', {}))
    clearance = cls_info.get('clearance', 0.2)
    track_width = cls_info.get('track_width', 0.25)
    via_dia = cls_info.get('via_diameter', 0.6)
    via_drill = cls_info.get('via_drill', 0.3)
    print(f"\n  {cls_name}: {len(nets)} nets")
    print(f"    clearance={clearance}, track={track_width}, via={via_dia}/{via_drill}")
    for n in sorted(nets)[:5]:
        print(f"      {n}")
    if len(nets) > 5:
        print(f"      ... +{len(nets)-5} more")

# Generate new class section for DSN
# DSN units are 10nm, so 0.25mm = 250
def mm_to_dsn(mm):
    return int(mm * 1000)

dsn_classes = []
for cls_name in sorted(class_nets.keys()):
    nets = sorted(class_nets[cls_name])
    cls_info = classes_def.get(cls_name, classes_def.get('Default', {}))
    clearance = mm_to_dsn(cls_info.get('clearance', 0.2))
    track_width = mm_to_dsn(cls_info.get('track_width', 0.25))
    via_dia = mm_to_dsn(cls_info.get('via_diameter', 0.6))
    via_drill = mm_to_dsn(cls_info.get('via_drill', 0.3))
    
    # Format net names: names with special chars need quotes
    net_strs = []
    for n in nets:
        if any(c in n for c in ' -()"') or n.startswith('/') == False:
            net_strs.append(f'"{n}"')
        else:
            net_strs.append(n)
    
    # Build class definition
    nets_line = ' '.join(net_strs)
    cls_block = f"""    (class {cls_name} {nets_line}
      (circuit
        (use_via "Via[0-1]_{via_dia}:{via_drill}_um")
      )
      (rule
        (width {track_width})
        (clearance {clearance})
      )
    )"""
    dsn_classes.append(cls_block)

new_class_section = '\n'.join(dsn_classes)

# Replace existing class sections in DSN
# Find from first "(class " to end of last class ")"
class_start = dsn.find('    (class ')
if class_start == -1:
    print("ERROR: Could not find class section in DSN!")
    exit(1)

# Find the end: after last class closing paren, before (wiring)
wiring_pos = dsn.find('  (wiring')
if wiring_pos == -1:
    print("ERROR: Could not find (wiring) in DSN!")
    exit(1)

# Everything between class_start and the line before (wiring) is classes
# Also need the closing paren of (structure ...)
# The classes are inside (structure ...) which ends with ")  \n  (wiring..."
# Find the ") before (wiring"
close_structure = dsn.rfind(')', class_start, wiring_pos)
# Actually, let me find the exact boundaries
# Count from class_start to find all classes, then replace

# Simple approach: find text from first (class to line before (wiring
# Original text ends with "  )\n  (wiring"
lines = dsn.split('\n')
class_start_line = None
class_end_line = None
for i, line in enumerate(lines):
    if '(class ' in line and class_start_line is None:
        class_start_line = i
    if '(wiring' in line:
        class_end_line = i
        break

if class_start_line and class_end_line:
    # Replace lines from class_start_line to class_end_line-1
    # But we need to preserve the "  )" closing the structure section
    # Check what's between the last class and (wiring)
    between = lines[class_start_line:class_end_line]
    print(f"\nReplacing lines {class_start_line}-{class_end_line-1}")
    
    # The section ends with "  )" closing the (rule section 
    # Need to keep structure intact - just replace the class lines
    # and the closing "  )" of structure
    new_lines = lines[:class_start_line] + new_class_section.split('\n') + ['  )'] + lines[class_end_line:]
    
    result = '\n'.join(new_lines)
    
    with open(DSN, 'w') as f:
        f.write(result)
    
    print(f"✅ DSN updated: {os.path.getsize(DSN):,} bytes")
else:
    print(f"ERROR: Could not locate class section (start={class_start_line}, end={class_end_line})")
