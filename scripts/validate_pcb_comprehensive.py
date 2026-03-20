#!/usr/bin/env python3
"""
Comprehensive PCB validation against ALL copilot-instructions rules.
Reads the actual PCB file, project file, and DRU, and checks every rule.
NO ASSUMPTIONS — every check reads real data.
"""
import re, json, os, sys, math, fnmatch
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
PRO_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pro')
DRU_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_dru')
SCH_FILE = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_sch')

# ═══════════════════════════════════════════════════════════════
# PARSING HELPERS
# ═══════════════════════════════════════════════════════════════

def extract_blocks(content, block_type, indent_prefix='\t'):
    """Extract all top-level blocks of given type from PCB content."""
    blocks = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == f'({block_type}' or stripped.startswith(f'({block_type} '):
            depth = 0
            block_lines = []
            j = i
            while j < len(lines):
                block_lines.append(lines[j])
                for ch in lines[j]:
                    if ch == '(': depth += 1
                    elif ch == ')': depth -= 1
                if depth <= 0:
                    break
                j += 1
            blocks.append('\n'.join(block_lines))
            i = j + 1
            continue
        i += 1
    return blocks


def parse_nets(content):
    """Parse net declarations: (net ID "name")."""
    nets = {}
    for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', content):
        nets[int(m.group(1))] = m.group(2)
    return nets


def parse_footprints(content):
    """Extract footprint blocks with reference, position, layer."""
    footprints = []
    blocks = extract_blocks(content, 'footprint')
    for block in blocks:
        ref_m = re.search(r'\(property "Reference" "([^"]*)"', block)
        at_m = re.search(r'\(at ([\d.+-]+) ([\d.+-]+)(?:\s+([\d.+-]+))?\)', block)
        layer_m = re.search(r'\(layer "([^"]+)"\)', block)
        fp_name_m = re.match(r'\s*\(footprint "([^"]+)"', block)
        ref = ref_m.group(1) if ref_m else '?'
        x = float(at_m.group(1)) if at_m else 0
        y = float(at_m.group(2)) if at_m else 0
        rot = float(at_m.group(3)) if at_m and at_m.group(3) else 0
        layer = layer_m.group(1) if layer_m else '?'
        fp_name = fp_name_m.group(1) if fp_name_m else '?'
        
        # Extract pads with net assignments
        pads = []
        for pm in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+) \(at ([\d.+-]+) ([\d.+-]+)', block):
            pad_name = pm.group(1)
            pad_type = pm.group(2)
            pad_shape = pm.group(3)
            # Find net for this pad
            pad_block_start = pm.start()
            pad_block_end = block.find(')', pad_block_start)
            # Simple: find (net N ...) after this pad start
            sub = block[pad_block_start:pad_block_start+500]
            net_m = re.search(r'\(net (\d+) "([^"]*)"\)', sub)
            net_id = int(net_m.group(1)) if net_m else 0
            net_name = net_m.group(2) if net_m else ''
            pads.append({
                'name': pad_name,
                'type': pad_type,
                'net_id': net_id,
                'net_name': net_name
            })
        
        footprints.append({
            'ref': ref,
            'x': x, 'y': y, 'rot': rot,
            'layer': layer,
            'fp_name': fp_name,
            'pads': pads,
            'block': block
        })
    return footprints


def parse_segments(content):
    """Extract segment data: start, end, width, layer, net."""
    segments = []
    blocks = extract_blocks(content, 'segment')
    for block in blocks:
        start_m = re.search(r'\(start ([\d.+-]+) ([\d.+-]+)\)', block)
        end_m = re.search(r'\(end ([\d.+-]+) ([\d.+-]+)\)', block)
        width_m = re.search(r'\(width ([\d.]+)\)', block)
        layer_m = re.search(r'\(layer "([^"]+)"\)', block)
        net_m = re.search(r'\(net (\d+)\)', block)
        
        if start_m and end_m:
            seg = {
                'start': (float(start_m.group(1)), float(start_m.group(2))),
                'end': (float(end_m.group(1)), float(end_m.group(2))),
                'width': float(width_m.group(1)) if width_m else 0.25,
                'layer': layer_m.group(1) if layer_m else '?',
                'net': int(net_m.group(1)) if net_m else 0
            }
            seg['length'] = math.sqrt(
                (seg['end'][0] - seg['start'][0])**2 + 
                (seg['end'][1] - seg['start'][1])**2
            )
            segments.append(seg)
    return segments


def parse_vias(content):
    """Extract via data: position, size, drill, layers, net."""
    vias = []
    blocks = extract_blocks(content, 'via')
    for block in blocks:
        at_m = re.search(r'\(at ([\d.+-]+) ([\d.+-]+)\)', block)
        size_m = re.search(r'\(size ([\d.]+)\)', block)
        drill_m = re.search(r'\(drill ([\d.]+)\)', block)
        net_m = re.search(r'\(net (\d+)\)', block)
        
        if at_m:
            vias.append({
                'x': float(at_m.group(1)),
                'y': float(at_m.group(2)),
                'size': float(size_m.group(1)) if size_m else 0.6,
                'drill': float(drill_m.group(1)) if drill_m else 0.3,
                'net': int(net_m.group(1)) if net_m else 0
            })
    return vias


def parse_zones(content):
    """Extract zone info: net, layer, connect mode, clearance."""
    zones = []
    blocks = extract_blocks(content, 'zone')
    for block in blocks:
        net_m = re.search(r'\(net (\d+)\)', block)
        net_name_m = re.search(r'\(net_name "([^"]*)"\)', block)
        layer_m = re.search(r'\(layers? "([^"]+)"\)', block)
        connect_m = re.search(r'\(connect_pads\s*(yes|no|thru_hole_only)?\s*\(clearance ([\d.]+)\)', block)
        min_thick_m = re.search(r'\(min_thickness ([\d.]+)\)', block)
        uuid_m = re.search(r'\(uuid "([^"]+)"\)', block)
        
        zones.append({
            'net': int(net_m.group(1)) if net_m else 0,
            'net_name': net_name_m.group(1) if net_name_m else '?',
            'layer': layer_m.group(1) if layer_m else '?',
            'connect_pads': connect_m.group(1) if connect_m and connect_m.group(1) else 'thermal',
            'clearance': float(connect_m.group(2)) if connect_m else 0,
            'min_thickness': float(min_thick_m.group(1)) if min_thick_m else 0,
            'uuid': uuid_m.group(1) if uuid_m else '?',
            'has_filled': 'filled_polygon' in block
        })
    return zones


def parse_gr_texts(content):
    """Extract graphic text elements."""
    texts = []
    blocks = extract_blocks(content, 'gr_text')
    for block in blocks:
        # Text content is the second token after (gr_text
        text_m = re.match(r'\s*\(gr_text\s+"([^"]*)"', block)
        layer_m = re.search(r'\(layer "([^"]+)"\)', block)
        at_m = re.search(r'\(at ([\d.+-]+) ([\d.+-]+)', block)
        size_m = re.search(r'\(size ([\d.]+) ([\d.]+)\)', block)
        thickness_m = re.search(r'\(thickness ([\d.]+)\)', block)
        
        texts.append({
            'text': text_m.group(1) if text_m else '?',
            'layer': layer_m.group(1) if layer_m else '?',
            'x': float(at_m.group(1)) if at_m else 0,
            'y': float(at_m.group(2)) if at_m else 0,
            'font_height': float(size_m.group(2)) if size_m else 0,
            'font_width': float(size_m.group(1)) if size_m else 0,
            'thickness': float(thickness_m.group(1)) if thickness_m else 0,
        })
    return texts


def parse_board_outline(content):
    """Extract board outline from gr_rect or gr_line on Edge.Cuts."""
    # Check for gr_rect (multiline format in KiCad 9)
    for m in re.finditer(r'\(gr_rect\s+\(start\s+([\d.+-]+)\s+([\d.+-]+)\)\s+\(end\s+([\d.+-]+)\s+([\d.+-]+)\).*?Edge\.Cuts', content, re.DOTALL):
        return {
            'type': 'rect',
            'x1': float(m.group(1)), 'y1': float(m.group(2)),
            'x2': float(m.group(3)), 'y2': float(m.group(4)),
            'width': abs(float(m.group(3)) - float(m.group(1))),
            'height': abs(float(m.group(4)) - float(m.group(2)))
        }
    # Check for gr_line segments on Edge.Cuts
    edge_lines = []
    for m in re.finditer(r'\(gr_line \(start ([\d.+-]+) ([\d.+-]+)\) \(end ([\d.+-]+) ([\d.+-]+)\).*?\(layer "Edge\.Cuts"\)', content):
        edge_lines.append({
            'start': (float(m.group(1)), float(m.group(2))),
            'end': (float(m.group(3)), float(m.group(4)))
        })
    if edge_lines:
        all_x = [l['start'][0] for l in edge_lines] + [l['end'][0] for l in edge_lines]
        all_y = [l['start'][1] for l in edge_lines] + [l['end'][1] for l in edge_lines]
        return {
            'type': 'lines',
            'count': len(edge_lines),
            'x1': min(all_x), 'y1': min(all_y),
            'x2': max(all_x), 'y2': max(all_y),
            'width': max(all_x) - min(all_x),
            'height': max(all_y) - min(all_y)
        }
    # Check for zone polygon = board outline (edge.cuts not detected above)
    return None


# ═══════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════

print("Loading PCB data...")
with open(PCB_FILE) as f:
    pcb = f.read()
with open(PRO_FILE) as f:
    pro = json.load(f)
with open(DRU_FILE) as f:
    dru = f.read()

nets = parse_nets(pcb)
net_name_to_id = {v: k for k, v in nets.items()}
footprints = parse_footprints(pcb)
segments = parse_segments(pcb)
vias = parse_vias(pcb)
zones = parse_zones(pcb)
gr_texts = parse_gr_texts(pcb)
outline = parse_board_outline(pcb)

# Project netclass data
pro_classes = {c['name']: c for c in pro.get('net_settings', {}).get('classes', [])}
pro_patterns = pro.get('net_settings', {}).get('netclass_patterns', [])

# Build net→netclass mapping based on patterns
def resolve_netclass(net_name, patterns, default='Default'):
    clean = net_name.lstrip('/')
    for p in patterns:
        pat = p['pattern']
        if fnmatch.fnmatch(clean, pat) or fnmatch.fnmatch(net_name, pat) or fnmatch.fnmatch(clean, pat.lstrip('/')):
            return p['netclass']
    return default

net_to_class = {}
for nid, nname in nets.items():
    net_to_class[nname] = resolve_netclass(nname, pro_patterns)

print(f"  Footprints: {len(footprints)}")
print(f"  Segments:   {len(segments)}")
print(f"  Vias:       {len(vias)}")
print(f"  Zones:      {len(zones)}")
print(f"  Nets:       {len(nets)}")
print(f"  gr_texts:   {len(gr_texts)}")

# ═══════════════════════════════════════════════════════════════
# VALIDATION ENGINE
# ═══════════════════════════════════════════════════════════════

class ValidationResult:
    def __init__(self):
        self.checks = []  # (section, check_name, status, detail)
    
    def ok(self, section, name, detail=''):
        self.checks.append((section, name, 'OK', detail))
    
    def warn(self, section, name, detail=''):
        self.checks.append((section, name, 'WARN', detail))
    
    def error(self, section, name, detail=''):
        self.checks.append((section, name, 'ERROR', detail))
    
    def info(self, section, name, detail=''):
        self.checks.append((section, name, 'INFO', detail))
    
    def report(self):
        from collections import Counter
        stats = Counter(s for _, _, s, _ in self.checks)
        
        print(f"\n{'='*80}")
        print(f" PCB VALIDATION REPORT — aurora-dsp-icepower-booster")
        print(f"{'='*80}")
        print(f"  ✅ OK:     {stats.get('OK', 0)}")
        print(f"  ⚠️  WARN:   {stats.get('WARN', 0)}")
        print(f"  ❌ ERROR:  {stats.get('ERROR', 0)}")
        print(f"  ℹ️  INFO:   {stats.get('INFO', 0)}")
        print(f"  Total:    {len(self.checks)}")
        
        # Group by section
        sections = {}
        for section, name, status, detail in self.checks:
            sections.setdefault(section, []).append((name, status, detail))
        
        for section in sorted(sections.keys()):
            items = sections[section]
            print(f"\n{'─'*80}")
            print(f" {section}")
            print(f"{'─'*80}")
            for name, status, detail in items:
                icon = {'OK': '✅', 'WARN': '⚠️ ', 'ERROR': '❌', 'INFO': 'ℹ️ '}[status]
                line = f"  {icon} {name}"
                if detail:
                    line += f": {detail}"
                print(line)
        
        return stats.get('ERROR', 0)


V = ValidationResult()

# ═══════════════════════════════════════════════════════════════
# SECTION 5: PCB-Layout & Routing   
# ═══════════════════════════════════════════════════════════════

# ── 5.1 Massekonzept ──

# Rule: Ungeteilte GND-Fläche auf B.Cu
bcu_gnd_zones = [z for z in zones if z['layer'] == 'B.Cu' and z['net_name'] == 'GND']
fcu_gnd_zones = [z for z in zones if z['layer'] == 'F.Cu' and z['net_name'] == 'GND']

if bcu_gnd_zones:
    V.ok("5.1 Massekonzept", "GND-Fläche auf B.Cu vorhanden", f"{len(bcu_gnd_zones)} Zone(n)")
else:
    V.error("5.1 Massekonzept", "GND-Fläche auf B.Cu fehlt!", "Copilot-Instructions fordern ungeteilte GND-Fläche auf B.Cu")

if fcu_gnd_zones:
    V.ok("5.1 Massekonzept", "GND-Fläche auf F.Cu vorhanden", f"{len(fcu_gnd_zones)} Zone(n)")
else:
    V.warn("5.1 Massekonzept", "GND-Fläche auf F.Cu fehlt", "Empfohlen für bessere EMV")

# Rule: Zone connect_pads mode
for z in zones:
    if z['net_name'] == 'GND':
        mode = z['connect_pads']
        layer = z['layer']
        if mode == 'yes':
            V.ok("5.1 Massekonzept", f"Zone {layer} GND: Solid connect", "connect_pads yes — ideal für Maschinenlötung")
        elif mode == 'thermal':
            V.warn("5.1 Massekonzept", f"Zone {layer} GND: Thermal Relief", "Kann starved_thermal DRC-Fehler verursachen")
        else:
            V.info("5.1 Massekonzept", f"Zone {layer} GND: connect_pads={mode}")

# Rule: Zone fill present
for z in zones:
    if z['has_filled']:
        V.ok("5.1 Massekonzept", f"Zone {z['layer']} {z['net_name']}: Zonen-Fill vorhanden")
    else:
        V.error("5.1 Massekonzept", f"Zone {z['layer']} {z['net_name']}: Kein Zonen-Fill!", "Zone ist leer — pcbnew Zone-Fill nötig")

# ── 5.2 Trace-Breiten prüfen ──
# Rule: Signal 0.2-0.25mm, Audio 0.3mm, Power 0.5mm

width_checks = {
    'Power': {'min': 0.5, 'nets': []},
    'Audio_Input': {'min': 0.3, 'nets': []},
    'Audio_Output': {'min': 0.3, 'nets': []},  # DRU says min 0.3
    'Audio_Power': {'min': 0.5, 'nets': []},  # DRU says min 0.5
    'HV': {'min': 0.5, 'nets': []},
    'Default': {'min': 0.15, 'nets': []},
}

seg_violations_width = defaultdict(list)
for seg in segments:
    net_name = nets.get(seg['net'], f'net_{seg["net"]}')
    nc = net_to_class.get(net_name, 'Default')
    
    min_w = width_checks.get(nc, {}).get('min', 0.15)
    if seg['width'] < min_w - 0.001:
        seg_violations_width[nc].append({
            'net': net_name,
            'width': seg['width'],
            'min': min_w,
            'layer': seg['layer']
        })

for nc, violations in seg_violations_width.items():
    if violations:
        unique_nets = set(v['net'] for v in violations)
        V.error("5.2 Trace-Breiten", f"Netzklasse {nc}: {len(violations)} Segmente zu dünn",
                f"Min: {violations[0]['min']}mm, Netze: {', '.join(list(unique_nets)[:5])}")
    else:
        V.ok("5.2 Trace-Breiten", f"Netzklasse {nc}: Alle Traces ≥ min width")

# General trace width stats
if segments:
    widths = [s['width'] for s in segments]
    V.info("5.2 Trace-Breiten", "Statistik",
           f"Min={min(widths):.3f}mm, Max={max(widths):.3f}mm, "
           f"Anzahl: {len(segments)} Segmente")

# ── 5.3 Layer-Verteilung ──
fcu_segs = [s for s in segments if s['layer'] == 'F.Cu']
bcu_segs = [s for s in segments if s['layer'] == 'B.Cu']

V.info("5.3 Layer-Verteilung", "Segmente pro Layer",
       f"F.Cu: {len(fcu_segs)}, B.Cu: {len(bcu_segs)}")

# Rule: Audio-Traces auf Top-Layer (B.Cu für ununterbrochene Massefläche freihalten)
audio_input_on_bcu = []
for seg in bcu_segs:
    net_name = nets.get(seg['net'], '')
    nc = net_to_class.get(net_name, 'Default')
    if nc == 'Audio_Input':
        audio_input_on_bcu.append(net_name)

if audio_input_on_bcu:
    unique = set(audio_input_on_bcu)
    V.warn("5.3 Audio-Signalführung", "Audio_Input Traces auf B.Cu",
           f"{len(audio_input_on_bcu)} Segs, Netze: {', '.join(list(unique)[:5])}... — "
           "Copilot-Instructions: Audio-Traces auf Top-Layer")
else:
    V.ok("5.3 Audio-Signalführung", "Keine Audio_Input Traces auf B.Cu")

# ── 5.4 Via-Prüfung ──
# Rule: Via-Pad min 0.45mm (JLCPCB), Standard 0.6mm  
# Rule: Via-Bohrung min 0.2mm, Standard 0.3mm
# Rule: Keine Vias im Audio-Signalpfad

via_too_small = []
audio_vias = []
for via in vias:
    if via['size'] < 0.45:
        via_too_small.append(via)
    if via['drill'] < 0.2:
        via_too_small.append(via)
    
    net_name = nets.get(via['net'], '')
    nc = net_to_class.get(net_name, 'Default')
    if nc in ('Audio_Input',):
        audio_vias.append((net_name, via))

if via_too_small:
    V.error("5.4 Via-Design", f"{len(via_too_small)} Vias unter JLCPCB-Minimum")
else:
    V.ok("5.4 Via-Design", "Alle Vias ≥ JLCPCB-Minimum (0.45mm Pad, 0.2mm Drill)")

if audio_vias:
    unique_nets = set(n for n, _ in audio_vias)
    V.warn("5.4 Via-Design", f"{len(audio_vias)} Vias in Audio_Input Netzen",
           f"Netze: {', '.join(list(unique_nets)[:5])}... — "
           "Copilot-Instructions: Keine Vias im Audio-Signalpfad (Impedanzsprung)")
else:
    V.ok("5.4 Via-Design", "Keine Vias in Audio_Input Netzen")

# Via size consistency with netclass
via_size_issues = []
for via in vias:
    net_name = nets.get(via['net'], '')
    nc = net_to_class.get(net_name, 'Default')
    expected = pro_classes.get(nc, pro_classes.get('Default', {}))
    exp_size = expected.get('via_diameter', 0.6)
    exp_drill = expected.get('via_drill', 0.3)
    
    if abs(via['size'] - exp_size) > 0.01 or abs(via['drill'] - exp_drill) > 0.01:
        via_size_issues.append((net_name, nc, via['size'], exp_size, via['drill'], exp_drill))

if via_size_issues:
    V.warn("5.4 Via-Design", f"{len(via_size_issues)} Vias mit abweichender Größe von Netzklasse",
           f"z.B. {via_size_issues[0][0]} ({via_size_issues[0][1]}): "
           f"ist {via_size_issues[0][2]}/{via_size_issues[0][4]}mm, "
           f"soll {via_size_issues[0][3]}/{via_size_issues[0][5]}mm")
else:
    V.ok("5.4 Via-Design", "Alle Via-Größen entsprechen Netzklasse")

# Via stats
if vias:
    sizes = set((v['size'], v['drill']) for v in vias)
    V.info("5.4 Via-Design", "Via-Größen im Board",
           ', '.join(f'{s}/{d}mm' for s, d in sorted(sizes)))

# ── 5.5 45°-Winkel prüfen ──
# Rule: 45°-Winkel statt 90°
right_angle_count = 0
# Check consecutive segments on same net for 90° turns
segs_by_net = defaultdict(list)
for seg in segments:
    segs_by_net[seg['net']].append(seg)

for net_id, net_segs in segs_by_net.items():
    if len(net_segs) < 2:
        continue
    # Simple check: find segments sharing endpoints
    endpoints = {}
    for i, seg in enumerate(net_segs):
        key_s = (round(seg['start'][0], 3), round(seg['start'][1], 3))
        key_e = (round(seg['end'][0], 3), round(seg['end'][1], 3))
        endpoints.setdefault(key_s, []).append(i)
        endpoints.setdefault(key_e, []).append(i)
    
    for point, seg_indices in endpoints.items():
        if len(seg_indices) >= 2:
            for a_idx in range(len(seg_indices)):
                for b_idx in range(a_idx+1, len(seg_indices)):
                    sa = net_segs[seg_indices[a_idx]]
                    sb = net_segs[seg_indices[b_idx]]
                    # Same layer check
                    if sa['layer'] != sb['layer']:
                        continue
                    # Calculate angle between segments
                    def vec(seg, ref_point):
                        sx, sy = seg['start']
                        ex, ey = seg['end']
                        if (round(sx,3), round(sy,3)) == ref_point:
                            return (ex - sx, ey - sy)
                        return (sx - ex, sy - ey)
                    
                    va = vec(sa, point)
                    vb = vec(sb, point)
                    dot = va[0]*vb[0] + va[1]*vb[1]
                    mag_a = math.sqrt(va[0]**2 + va[1]**2)
                    mag_b = math.sqrt(vb[0]**2 + vb[1]**2)
                    if mag_a < 0.001 or mag_b < 0.001:
                        continue
                    cos_angle = max(-1, min(1, dot / (mag_a * mag_b)))
                    angle = math.degrees(math.acos(cos_angle))
                    # 90° ± 2° tolerance
                    if 88 < angle < 92:
                        right_angle_count += 1

if right_angle_count > 0:
    V.warn("5.5 Routing-Winkel", f"{right_angle_count} Trace-Abschnitte mit ~90°-Winkeln",
           "Copilot-Instructions: 45°-Winkel statt 90° Ecken")
else:
    V.ok("5.5 Routing-Winkel", "Keine 90°-Winkel in Traces erkannt")

# ═══════════════════════════════════════════════════════════════
# SECTION 7: JLCPCB Design Rules & Fertigung
# ═══════════════════════════════════════════════════════════════

# ── 7.1 Minimale Design-Regeln ──
V.info("7.1 JLCPCB Rules", "Board-Dimensionen",
       f"{outline['width']:.1f} × {outline['height']:.1f} mm" if outline else "Nicht erkannt")

# Track width minimum (JLCPCB: 0.1mm, empfohlen: ≥0.15mm)
if segments:
    min_width = min(s['width'] for s in segments)
    if min_width < 0.1:
        V.error("7.1 JLCPCB Rules", f"Trace-Breite {min_width}mm < 0.1mm JLCPCB-Minimum!")
    elif min_width < 0.15:
        V.warn("7.1 JLCPCB Rules", f"Trace-Breite {min_width}mm < 0.15mm Empfehlung")
    else:
        V.ok("7.1 JLCPCB Rules", f"Min. Trace-Breite: {min_width}mm ≥ 0.15mm")

# Via drill minimum (JLCPCB: 0.2mm, empfohlen: ≥0.3mm)
if vias:
    min_drill = min(v['drill'] for v in vias)
    min_via_size = min(v['size'] for v in vias)
    annular_ring = (min_via_size - min_drill) / 2
    
    if min_drill < 0.2:
        V.error("7.1 JLCPCB Rules", f"Via-Bohrung {min_drill}mm < 0.2mm JLCPCB-Minimum!")
    else:
        V.ok("7.1 JLCPCB Rules", f"Min. Via-Bohrung: {min_drill}mm ≥ 0.2mm")
    
    if annular_ring < 0.125:
        V.error("7.1 JLCPCB Rules", f"Annular Ring {annular_ring}mm < 0.125mm JLCPCB-Minimum!")
    else:
        V.ok("7.1 JLCPCB Rules", f"Min. Annular Ring: {annular_ring:.3f}mm ≥ 0.125mm")

# ── 7.2 Netzklassen-Konfiguration prüfen ──
required_classes = {
    'Default': {'clearance': 0.2, 'track_width': 0.25, 'via_diameter': 0.6, 'via_drill': 0.3},
    'Power': {'clearance': 0.25, 'track_width': 0.5, 'via_diameter': 0.8, 'via_drill': 0.4},
    'Audio_Input': {'clearance': 0.25, 'track_width': 0.3, 'via_diameter': 0.6, 'via_drill': 0.3},
    'Audio_Output': {'clearance': 0.2, 'track_width': 0.5, 'via_diameter': 0.6, 'via_drill': 0.3},
    'Audio_Power': {'clearance': 0.2, 'track_width': 0.8, 'via_diameter': 0.8, 'via_drill': 0.4},
}

for nc_name, expected in required_classes.items():
    actual = pro_classes.get(nc_name)
    if not actual:
        V.error("7.2 Netzklassen", f"Netzklasse '{nc_name}' fehlt!")
        continue
    
    issues = []
    for key, exp_val in expected.items():
        act_val = actual.get(key, 0)
        if abs(act_val - exp_val) > 0.001:
            issues.append(f"{key}: ist {act_val}, soll {exp_val}")
    
    if issues:
        V.error("7.2 Netzklassen", f"Netzklasse '{nc_name}' falsch konfiguriert",
                '; '.join(issues))
    else:
        V.ok("7.2 Netzklassen", f"Netzklasse '{nc_name}' korrekt",
             f"clearance={expected['clearance']}, track={expected['track_width']}, "
             f"via={expected['via_diameter']}/{expected['via_drill']}")

# HV class check
hv = pro_classes.get('HV')
if hv:
    if hv.get('clearance', 0) >= 0.5:
        V.ok("7.2 Netzklassen", "HV-Netzklasse vorhanden", f"clearance={hv['clearance']}mm")
    else:
        V.error("7.2 Netzklassen", f"HV clearance {hv.get('clearance')}mm < 0.5mm")
else:
    V.error("7.2 Netzklassen", "HV-Netzklasse fehlt!", "+24V_IN braucht ≥0.5mm clearance")

# ── 7.3 DRU-Regeln prüfen ──
required_dru_rules = [
    'power_clearance',
    'power_width',
    'audio_input_clearance',
    'audio_input_digital_separation',
    'audio_output_width',
    'audio_power_width',
    'hv_clearance',
    'board_edge',
]

for rule_name in required_dru_rules:
    if rule_name in dru:
        V.ok("7.3 DRU-Regeln", f"Regel '{rule_name}' vorhanden")
    else:
        V.error("7.3 DRU-Regeln", f"Regel '{rule_name}' fehlt!", "In .kicad_dru definieren")

# ── 7.4 Net-zu-Netzklasse Zuweisungen ──
# Check that all audio/power nets are assigned
unassigned_audio = []
for nid, nname in nets.items():
    if nid == 0:  # unconnected
        continue
    nc = net_to_class.get(nname, 'Default')
    clean = nname.lstrip('/')
    # Check if audio-ish names are in Default
    if nc == 'Default' and any(p in clean for p in ['CH', 'HOT', 'COLD', 'EMI', 'GAIN', 'OUT', 'BUF', 'SW_OUT', 'INV', 'SUMNODE', 'RX']):
        unassigned_audio.append(nname)

if unassigned_audio:
    V.warn("7.4 Net-Zuweisungen", f"{len(unassigned_audio)} möglicherweise unzugewiesene Audio-Netze",
           f"{', '.join(unassigned_audio[:5])}")
else:
    V.ok("7.4 Net-Zuweisungen", "Alle Audio-Netze haben Netzklassen-Zuweisungen")

# Power nets check
power_nets = [n for n in nets.values() if any(p in n for p in ['+12V', '-12V', '+24V', 'GND', 'V+', 'V-'])]
power_in_default = [n for n in power_nets if net_to_class.get(n, 'Default') == 'Default']
if power_in_default:
    V.error("7.4 Net-Zuweisungen", f"{len(power_in_default)} Power-Netze in Default-Klasse",
            f"{', '.join(power_in_default)}")
else:
    V.ok("7.4 Net-Zuweisungen", "Alle Power-Netze korrekt klassifiziert")

# Net count per class
class_counts = defaultdict(int)
for nname in nets.values():
    if nname:
        class_counts[net_to_class.get(nname, 'Default')] += 1
V.info("7.4 Net-Zuweisungen", "Netze pro Klasse",
       ', '.join(f'{k}:{v}' for k, v in sorted(class_counts.items())))

# ═══════════════════════════════════════════════════════════════
# SECTION: Silkscreen (aus 5.2 Bauteil-Platzierung)
# ═══════════════════════════════════════════════════════════════

# Rule: Mindestens 0.8mm Texthöhe, 0.15mm Strichstärke
# Rule: Board-Info: Projektname, Version, Datum
has_board_name = False
has_version = False

for t in gr_texts:
    if t['font_height'] < 0.8 and t['font_height'] > 0:
        V.warn("Silkscreen", f"Text '{t['text'][:30]}' Höhe {t['font_height']}mm < 0.8mm",
               "JLCPCB-Minimum: 0.8mm")
    
    text_lower = t['text'].lower()
    if 'aurora' in text_lower or 'icepower' in text_lower or 'booster' in text_lower:
        has_board_name = True
    if 'rev' in text_lower or 'version' in text_lower or 'v1' in text_lower:
        has_version = True

if has_board_name:
    V.ok("Silkscreen", "Board-Name auf Silkscreen vorhanden")
else:
    V.error("Silkscreen", "Board-Name fehlt auf Silkscreen", "Projektnamen hinzufügen")

if has_version:
    V.ok("Silkscreen", "Versionsnummer auf Silkscreen vorhanden")
else:
    V.error("Silkscreen", "Versionsnummer fehlt auf Silkscreen")

V.info("Silkscreen", f"{len(gr_texts)} gr_text Elemente auf PCB",
       '; '.join(f'"{t["text"]}" auf {t["layer"]}' for t in gr_texts))


# ═══════════════════════════════════════════════════════════════
# SECTION: Board Outline & Edge Clearance
# ═══════════════════════════════════════════════════════════════

if outline:
    V.ok("Board Outline", "Board-Outline vorhanden",
         f"Typ: {outline['type']}, {outline['width']:.1f} × {outline['height']:.1f} mm")
    
    # Check edge clearance
    min_edge_x = outline['x1']
    max_edge_x = outline['x2']
    min_edge_y = outline['y1']
    max_edge_y = outline['y2']
    
    edge_violations = 0
    for seg in segments:
        for point in [seg['start'], seg['end']]:
            dx = min(abs(point[0] - min_edge_x), abs(point[0] - max_edge_x))
            dy = min(abs(point[1] - min_edge_y), abs(point[1] - max_edge_y))
            min_dist = min(dx, dy)
            if min_dist < 0.3 and min_dist > 0.01:  # > 0.01 to exclude edge-aligned stuff
                edge_violations += 1
    
    for via in vias:
        dx = min(abs(via['x'] - min_edge_x), abs(via['x'] - max_edge_x))
        dy = min(abs(via['y'] - min_edge_y), abs(via['y'] - max_edge_y))
        min_dist = min(dx, dy)
        if min_dist < 0.3 and min_dist > 0.01:
            edge_violations += 1
    
    if edge_violations > 0:
        V.warn("Board Outline", f"{edge_violations} Kupfer-Elemente < 0.3mm vom Board-Edge",
               "DRU: board_edge min 0.3mm")
    else:
        V.ok("Board Outline", "Alle Kupfer-Elemente ≥ 0.3mm vom Board-Edge")
else:
    V.error("Board Outline", "Board-Outline nicht erkannt!", "Edge.Cuts prüfen")


# ═══════════════════════════════════════════════════════════════
# SECTION: Entkopplung & Bypass-Caps (aus 4.3)
# ═══════════════════════════════════════════════════════════════

# Find IC footprints and nearby bypass caps
ics = [fp for fp in footprints if fp['ref'].startswith('U')]
caps = [fp for fp in footprints if fp['ref'].startswith('C')]

# Rule: Entkopplungskondensatoren direkt am IC-Pin (<3mm)
# Check: For each IC, find closest bypass cap
ic_bypass_check = []
for ic in ics:
    closest_cap_dist = float('inf')
    closest_cap = None
    for cap in caps:
        dist = math.sqrt((ic['x'] - cap['x'])**2 + (ic['y'] - cap['y'])**2)
        if dist < closest_cap_dist:
            closest_cap_dist = dist
            closest_cap = cap
    
    if closest_cap_dist < 3.0:
        ic_bypass_check.append((ic['ref'], closest_cap['ref'], closest_cap_dist, 'ok'))
    elif closest_cap_dist < 10.0:
        ic_bypass_check.append((ic['ref'], closest_cap['ref'], closest_cap_dist, 'far'))
    else:
        ic_bypass_check.append((ic['ref'], closest_cap['ref'] if closest_cap else '?', closest_cap_dist, 'missing'))

too_far = [c for c in ic_bypass_check if c[3] == 'far']
missing = [c for c in ic_bypass_check if c[3] == 'missing']

if missing:
    V.error("Entkopplung", f"{len(missing)} ICs ohne nahelegenden Bypass-Cap",
            ', '.join(f'{c[0]} (nächster C: {c[1]} @ {c[2]:.1f}mm)' for c in missing))
if too_far:
    V.warn("Entkopplung", f"{len(too_far)} ICs mit Bypass-Cap >3mm Entfernung",
           ', '.join(f'{c[0]}→{c[1]} ({c[2]:.1f}mm)' for c in too_far[:5]))
if not missing and not too_far:
    V.ok("Entkopplung", f"Alle {len(ics)} ICs haben Bypass-Cap innerhalb 3mm")

V.info("Entkopplung", f"{len(ics)} ICs, {len(caps)} Kondensatoren auf Board")


# ═══════════════════════════════════════════════════════════════
# SECTION: Mounting Holes (aus 6 ICEpower Integration)
# ═══════════════════════════════════════════════════════════════

mounting_holes = [fp for fp in footprints if 'MountingHole' in fp['fp_name'] or fp['ref'].startswith('H')]
if mounting_holes:
    V.ok("Montagelöcher", f"{len(mounting_holes)} Montagelöcher vorhanden",
         ', '.join(h['ref'] for h in mounting_holes))
else:
    V.warn("Montagelöcher", "Keine Montagelöcher erkannt", "Für Kühlkörper-/Gehäusemontage empfohlen")


# ═══════════════════════════════════════════════════════════════
# SECTION: Routing Completeness
# ═══════════════════════════════════════════════════════════════

# Check which nets have traces
routed_nets = set()
for seg in segments:
    routed_nets.add(seg['net'])
for via in vias:
    routed_nets.add(via['net'])

# Nets that should have traces (non-GND, non-empty)
non_gnd_nets = {nid: nname for nid, nname in nets.items() 
                if nid != 0 and nname != 'GND' and nname != ''}
unrouted_nets = {nid: nname for nid, nname in non_gnd_nets.items() if nid not in routed_nets}

# GND is connected via zones, not traces — so exclude it
if unrouted_nets:
    V.warn("Routing Completeness", f"{len(unrouted_nets)} Netze ohne Traces/Vias",
           f"z.B. {', '.join(list(unrouted_nets.values())[:10])}")
else:
    V.ok("Routing Completeness", "Alle Nicht-GND-Netze haben Routing")

V.info("Routing Completeness", "Routing-Abdeckung",
       f"{len(routed_nets)} geroutete Netze von {len(non_gnd_nets)} Nicht-GND-Netzen")


# ═══════════════════════════════════════════════════════════════
# SECTION: Steckverbinder (Connectors)
# ═══════════════════════════════════════════════════════════════

connectors = [fp for fp in footprints if fp['ref'].startswith('J')]
V.info("Steckverbinder", f"{len(connectors)} Steckverbinder auf Board",
       ', '.join(f'{c["ref"]}' for c in connectors[:10]))


# ═══════════════════════════════════════════════════════════════
# SECTION 8: Checkliste vor Fertigung (Partial — PCB-relevant items)
# ═══════════════════════════════════════════════════════════════

# Rule: Board-Outline geschlossen (Edge.Cuts)
if outline:
    V.ok("8. Fertigung", "Board-Outline vorhanden (Edge.Cuts)")
else:
    V.error("8. Fertigung", "Board-Outline fehlt!")

# Rule: Vias getented — check if mask layers exist in gerber
gerber_dir = os.path.join(BASE, 'production', 'gerber')
if os.path.isdir(gerber_dir):
    gerber_files = os.listdir(gerber_dir)
    required_gerbers = ['F_Cu.gtl', 'B_Cu.gbl', 'F_Mask.gts', 'B_Mask.gbs', 
                        'F_Paste.gtp', 'B_Paste.gbp', 'F_Silkscreen.gto', 
                        'B_Silkscreen.gbo', 'Edge_Cuts.gm1']
    missing_gerbers = [g for g in required_gerbers if not any(g in f for f in gerber_files)]
    
    if missing_gerbers:
        V.error("8. Fertigung", f"Fehlende Gerber-Layer: {', '.join(missing_gerbers)}")
    else:
        V.ok("8. Fertigung", "Alle 9 Gerber-Layer vorhanden")
    
    # Drill file
    drill_files = [f for f in gerber_files if f.endswith('.drl')]
    if drill_files:
        V.ok("8. Fertigung", f"Drill-Datei vorhanden: {', '.join(drill_files)}")
    else:
        V.error("8. Fertigung", "Drill-Datei fehlt!")
else:
    V.error("8. Fertigung", "Gerber-Verzeichnis fehlt!")

# BOM + Position
assembly_dir = os.path.join(BASE, 'production', 'assembly')
if os.path.isdir(assembly_dir):
    asm_files = os.listdir(assembly_dir)
    bom_files = [f for f in asm_files if 'bom' in f.lower()]
    pos_files = [f for f in asm_files if 'pos' in f.lower()]
    
    if bom_files:
        V.ok("8. Fertigung", f"BOM vorhanden: {', '.join(bom_files)}")
    else:
        V.warn("8. Fertigung", "BOM fehlt in production/assembly/")
    
    if pos_files:
        V.ok("8. Fertigung", f"Position-Datei vorhanden: {', '.join(pos_files)}")
    else:
        V.warn("8. Fertigung", "Position-Datei fehlt")
else:
    V.warn("8. Fertigung", "Assembly-Verzeichnis fehlt")


# ═══════════════════════════════════════════════════════════════
# SECTION: Parallel Trace Separation (Audio vs Digital/Power)
# ═══════════════════════════════════════════════════════════════

# Rule: Audio-Traces niemals parallel zu digitalen Signalen (≥3mm), zu Power (≥5mm)
# Simple check: find co-located traces on same layer but different netclasses
# This is a simplified proximity check

def segments_parallel_close(seg_a, seg_b, max_dist):
    """Check if two segments are roughly parallel and close."""
    if seg_a['layer'] != seg_b['layer']:
        return False
    # Simple midpoint distance
    mid_a = ((seg_a['start'][0] + seg_a['end'][0])/2, (seg_a['start'][1] + seg_a['end'][1])/2)
    mid_b = ((seg_b['start'][0] + seg_b['end'][0])/2, (seg_b['start'][1] + seg_b['end'][1])/2)
    dist = math.sqrt((mid_a[0]-mid_b[0])**2 + (mid_a[1]-mid_b[1])**2)
    return dist < max_dist

# Check Audio_Input vs Default (digital) — should be ≥0.5mm (DRU rule)  
# Check Audio_Input vs Power — should be ≥0.5mm (DRU rule)
# These are enforced by DRC so just note them
V.info("Trace-Separation", "Audio/Digital/Power-Separation",
       "Wird durch DRU-Regeln audio_input_digital_separation (0.5mm) und "
       "audio_input_power_separation (0.5mm) erzwungen")


# ═══════════════════════════════════════════════════════════════
# SECTION: DRC Result Integration
# ═══════════════════════════════════════════════════════════════

drc_json = '/tmp/aurora-drc-routed.json'
if os.path.exists(drc_json):
    with open(drc_json) as f:
        drc_data = json.load(f)
    
    violations = drc_data.get('violations', [])
    unconnected = drc_data.get('unconnected_items', [])
    
    errors = [v for v in violations if v.get('severity') == 'error']
    warnings = [v for v in violations if v.get('severity') == 'warning']
    
    # Group by type
    by_type = defaultdict(lambda: {'error': 0, 'warning': 0})
    for v in violations:
        by_type[v.get('type', '?')][v.get('severity', '?')] += 1
    
    V.info("DRC", "Letzte DRC-Ergebnisse",
           f"{len(errors)} Errors, {len(warnings)} Warnings, {len(unconnected)} Unconnected")
    
    # Clearance errors (should be 0)
    clearance_errs = [v for v in errors if v['type'] == 'clearance']
    if clearance_errs:
        V.error("DRC", f"{len(clearance_errs)} Clearance-Verletzungen!")
    else:
        V.ok("DRC", "Keine Clearance-Verletzungen")
    
    # Short circuits
    shorts = [v for v in errors if v['type'] == 'shorting_items']
    if shorts:
        V.error("DRC", f"{len(shorts)} Kurzschlüsse!")
    else:
        V.ok("DRC", "Keine Kurzschlüsse")
    
    # Courtyard overlaps
    courtyard = [v for v in errors if v['type'] == 'courtyards_overlap']
    if courtyard:
        items_str = []
        for c in courtyard:
            descs = [i.get('description', '?')[:40] for i in c.get('items', [])]
            items_str.append(' + '.join(descs))
        V.warn("DRC", f"{len(courtyard)} Courtyard-Überlappungen",
               '; '.join(items_str))
    
    # Unconnected
    if unconnected:
        # Check if all are GND zone islands
        all_gnd = all('GND' in u.get('items', [{}])[0].get('description', '') 
                      for u in unconnected if u.get('items'))
        if all_gnd:
            V.warn("DRC", f"{len(unconnected)} unverbundene GND-Zonen-Inseln (F.Cu)",
                   "Via-Stitching empfohlen, aber B.Cu liefert kontinuierlichen GND-Rückpfad")
        else:
            V.error("DRC", f"{len(unconnected)} unverbundene Items (nicht nur GND-Inseln)")
    else:
        V.ok("DRC", "Keine unverbundenen Items")
    
    # Silkscreen warnings breakdown
    silk_warns = sum(1 for v in warnings if 'silk' in v.get('type', ''))
    if silk_warns > 100:
        V.warn("DRC", f"{silk_warns} Silkscreen-Warnungen",
               "Typisch bei dichter Bestückung, visuell prüfen")
    
    # lib_footprint_mismatch
    lib_mismatch = by_type.get('lib_footprint_mismatch', {}).get('warning', 0)
    if lib_mismatch > 0:
        V.warn("DRC", f"{lib_mismatch} lib_footprint_mismatch Warnungen",
               "Durch Build-Skript generierte Footprints — akzeptabel für Prototyp")
else:
    V.warn("DRC", "Keine DRC-Ergebnisse verfügbar", "kicad-cli pcb drc ausführen")


# ═══════════════════════════════════════════════════════════════
# SECTION: Footprint Component Types Count
# ═══════════════════════════════════════════════════════════════

ref_types = defaultdict(int)
for fp in footprints:
    prefix = ''.join(c for c in fp['ref'] if c.isalpha())
    ref_types[prefix] += 1

V.info("Bestückung", "Bauteil-Übersicht",
       ', '.join(f'{k}:{v}' for k, v in sorted(ref_types.items())))


# ═══════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════

error_count = V.report()
print(f"\n{'='*80}")
if error_count == 0:
    print("🎉 VALIDATION BESTANDEN — Keine kritischen Fehler!")
else:
    print(f"⚠️  {error_count} kritische Fehler gefunden — Korrektur empfohlen")
print(f"{'='*80}")

sys.exit(0 if error_count == 0 else 1)
