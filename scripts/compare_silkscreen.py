#!/usr/bin/env python3
"""Compare gr_text blocks between stash PCB and current PCB.
Identify what the user added/changed in their silkscreen edits."""
import re

def extract_gr_texts(filepath):
    """Extract all gr_text blocks with balanced parentheses."""
    with open(filepath) as f:
        content = f.read()
    
    results = []
    for m in re.finditer(r'\(gr_text\b', content):
        # Extract balanced block
        depth = 0
        i = m.start()
        start = i
        while i < len(content):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    block = content[start:i+1]
                    results.append(block)
                    break
            i += 1
    return results

def parse_gr_text(block):
    """Parse a gr_text block to extract text, position, layer."""
    # Text content (may be multiline with \n)
    text_match = re.search(r'\(gr_text\s+"((?:[^"\\]|\\.)*)"\s*$', block, re.MULTILINE)
    if not text_match:
        text_match = re.search(r'\(gr_text\s+"((?:[^"\\]|\\.)*)"', block)
    text = text_match.group(1) if text_match else "?"
    
    # Position
    at_match = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
    pos = (float(at_match.group(1)), float(at_match.group(2))) if at_match else (0, 0)
    angle = float(at_match.group(3)) if at_match and at_match.group(3) else 0
    
    # Layer
    layer_match = re.search(r'\(layer\s+"([^"]+)"\)', block)
    layer = layer_match.group(1) if layer_match else "?"
    
    # UUID
    uuid_match = re.search(r'\(uuid\s+"([^"]+)"\)', block)
    uuid = uuid_match.group(1) if uuid_match else None
    
    return {
        'text': text[:80],
        'pos': pos,
        'angle': angle,
        'layer': layer,
        'uuid': uuid,
        'full': block
    }

stash_texts = extract_gr_texts("/tmp/pcb_stash.kicad_pcb")
head_texts = extract_gr_texts("/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb")

stash_parsed = [parse_gr_text(t) for t in stash_texts]
head_parsed = [parse_gr_text(t) for t in head_texts]

stash_uuids = {p['uuid']: p for p in stash_parsed if p['uuid']}
head_uuids = {p['uuid']: p for p in head_parsed if p['uuid']}

print(f"Stash gr_text count: {len(stash_parsed)}")
print(f"HEAD gr_text count: {len(head_parsed)}")

# Texts only in stash (added by user, missing from HEAD)
only_stash = set(stash_uuids.keys()) - set(head_uuids.keys())
print(f"\n=== ONLY IN STASH (missing from HEAD, user created): {len(only_stash)} ===")
for uuid in only_stash:
    p = stash_uuids[uuid]
    print(f"  [{p['layer']}] at ({p['pos'][0]}, {p['pos'][1]}) angle={p['angle']}: \"{p['text']}\"")

# Texts only in HEAD (created by me)
only_head = set(head_uuids.keys()) - set(stash_uuids.keys())
print(f"\n=== ONLY IN HEAD (not in stash): {len(only_head)} ===")
for uuid in only_head:
    p = head_uuids[uuid]
    print(f"  [{p['layer']}] at ({p['pos'][0]}, {p['pos'][1]}) angle={p['angle']}: \"{p['text']}\"")

# Same UUID but different content (user moved/edited)
print(f"\n=== MODIFIED (same UUID, different content): ===")
shared = set(stash_uuids.keys()) & set(head_uuids.keys())
for uuid in shared:
    s = stash_uuids[uuid]
    h = head_uuids[uuid]
    if s['full'] != h['full']:
        print(f"\n  UUID: {uuid}")
        print(f"  STASH: [{s['layer']}] at ({s['pos'][0]}, {s['pos'][1]}) angle={s['angle']}: \"{s['text']}\"")
        print(f"  HEAD:  [{h['layer']}] at ({h['pos'][0]}, {h['pos'][1]}) angle={h['angle']}: \"{h['text']}\"")
        # Show what changed
        if s['pos'] != h['pos']:
            print(f"    → Position changed: ({s['pos'][0]}, {s['pos'][1]}) → ({h['pos'][0]}, {h['pos'][1]})")
        if s['angle'] != h['angle']:
            print(f"    → Angle changed: {s['angle']} → {h['angle']}")
        if s['text'] != h['text']:
            print(f"    → Text changed")
        if s['layer'] != h['layer']:
            print(f"    → Layer changed: {s['layer']} → {h['layer']}")
