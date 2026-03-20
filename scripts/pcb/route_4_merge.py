#!/usr/bin/env python3
"""
Phase 4: Text-merge routing (segments + vias) from temp PCB into original.

- Extracts new segment/via blocks from pcbnew-saved temp file
- Remaps net IDs (pcbnew may renumber them)
- Inserts into original PCB before zone blocks
- Validates bracket balance
- Removes duplicate vias (same position + same net)
"""
import re, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORIG = os.path.join(BASE, 'aurora-dsp-icepower-booster.kicad_pcb')
TEMP = '/tmp/aurora-booster-routed.kicad_pcb'

if not os.path.exists(TEMP):
    print(f'ERROR: Temp PCB not found: {TEMP}')
    print('Run route_3_import_ses.py first!')
    sys.exit(1)

with open(ORIG) as f:
    orig_content = f.read()
with open(TEMP) as f:
    temp_content = f.read()


def extract_blocks(content, block_type):
    """Extract all top-level blocks of given type."""
    blocks = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # Match "(segment", "(segment ...", "(via", "(via ..." at start of stripped line
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


def fingerprint(block):
    """Create a fingerprint ignoring UUID."""
    fp = re.sub(r'\(uuid "[^"]*"\)', '', block)
    fp = ' '.join(fp.split())
    return fp


def parse_nets(content):
    """Parse (net ID "name") declarations."""
    nets = {}
    for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', content):
        name = m.group(2)
        nid = int(m.group(1))
        if name not in nets:
            nets[name] = nid
    return nets


def remap_nets(block, remap_dict):
    """Replace (net N) with remapped ID."""
    def replace_net(m):
        old_id = int(m.group(1))
        new_id = remap_dict.get(old_id, old_id)
        return f'(net {new_id})'
    return re.sub(r'\(net (\d+)\)', replace_net, block)


def normalize_block(block):
    """Normalize indentation to match original KiCad format (tab-based)."""
    lines = block.split('\n')
    normalized = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            continue
        indent = 0
        for ch in line:
            if ch == '\t':
                indent += 1
            elif ch == ' ':
                indent += 0.25
            else:
                break
        indent = max(1, round(indent))
        normalized.append('\t' * indent + stripped)
    return '\n'.join(normalized)


# ── Extract ──
orig_segments = extract_blocks(orig_content, 'segment')
temp_segments = extract_blocks(temp_content, 'segment')
orig_vias = extract_blocks(orig_content, 'via')
temp_vias = extract_blocks(temp_content, 'via')

print(f'Original:  {len(orig_segments)} segments, {len(orig_vias)} vias')
print(f'Routed:    {len(temp_segments)} segments, {len(temp_vias)} vias')

# ── Fingerprint & diff ──
orig_seg_fps = set(fingerprint(s) for s in orig_segments)
orig_via_fps = set(fingerprint(v) for v in orig_vias)

new_segments = [s for s in temp_segments if fingerprint(s) not in orig_seg_fps]
new_vias = [v for v in temp_vias if fingerprint(v) not in orig_via_fps]

print(f'New:       {len(new_segments)} segments, {len(new_vias)} vias')

# ── Net ID remapping ──
orig_nets = parse_nets(orig_content)
temp_nets = parse_nets(temp_content)

temp_id_to_name = {v: k for k, v in temp_nets.items()}
remap = {}
unmapped = []
for temp_id, name in temp_id_to_name.items():
    if name in orig_nets:
        remap[temp_id] = orig_nets[name]
    else:
        unmapped.append((temp_id, name))
        remap[temp_id] = temp_id

needs_remap = any(k != v for k, v in remap.items())
if needs_remap:
    diff_count = sum(1 for k, v in remap.items() if k != v)
    print(f'Net ID remap: {diff_count} IDs remapped')
    new_segments = [remap_nets(s, remap) for s in new_segments]
    new_vias = [remap_nets(v, remap) for v in new_vias]

if unmapped:
    for tid, name in unmapped:
        print(f'  WARNING: Unmapped net "{name}" (temp ID {tid})')

# ── Normalize ──
new_segments = [normalize_block(s) for s in new_segments]
new_vias = [normalize_block(v) for v in new_vias]

# ── Deduplicate vias (same position + net) ──
def via_key(block):
    m = re.search(r'\(at\s+([\d.+-]+)\s+([\d.+-]+)\)', block)
    n = re.search(r'\(net\s+(\d+)\)', block)
    if m and n:
        return (m.group(1), m.group(2), n.group(1))
    return None

seen_vias = set()
deduped_vias = []
for v in new_vias:
    k = via_key(v)
    if k and k not in seen_vias:
        seen_vias.add(k)
        deduped_vias.append(v)
    elif k is None:
        deduped_vias.append(v)

if len(deduped_vias) < len(new_vias):
    print(f'Dedup vias: {len(new_vias)} → {len(deduped_vias)}')
new_vias = deduped_vias

# ── Insert into original ──
all_new = new_segments + new_vias
if not all_new:
    print('\n⚠️  No new routing to merge!')
    sys.exit(0)

block_text = '\n'.join(all_new)

# Find insertion point (before first zone or gr_text or closing paren)
zone_m = re.search(r'\n\t\(zone\b', orig_content)
gr_text_m = re.search(r'\n\t\(gr_text\b', orig_content)
insert_targets = [m.start() for m in [zone_m, gr_text_m] if m]

if insert_targets:
    insert_pos = min(insert_targets)
else:
    insert_pos = orig_content.rstrip().rfind(')')

result = orig_content[:insert_pos] + '\n' + block_text + orig_content[insert_pos:]

# ── Bracket balance ──
depth = sum(1 if c == '(' else -1 if c == ')' else 0 for c in result)
if depth != 0:
    print(f'❌ Bracket balance: {depth}')
    sys.exit(1)
print(f'Bracket balance: OK')

with open(ORIG, 'w') as f:
    f.write(result)

total_segs = len(orig_segments) + len(new_segments)
total_vias = len(orig_vias) + len(new_vias)
print(f'\n✅ Merged into original PCB')
print(f'   Total: {total_segs} segments, {total_vias} vias')
print(f'   Size:  {len(result):,} bytes')
