#!/usr/bin/env python3
"""Compare fp_text reference/value positions between stash and HEAD.
These are the silkscreen labels on footprints that user may have moved."""
import re

def extract_footprints(filepath):
    """Extract all footprint blocks with their fp_text properties."""
    with open(filepath) as f:
        content = f.read()
    
    results = {}
    for m in re.finditer(r'\(footprint\b', content):
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
                    # Get reference
                    ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
                    if ref_match:
                        ref = ref_match.group(1)
                        results[ref] = block
                    break
            i += 1
    return results

def extract_fp_texts(block):
    """Extract property locations from a footprint block."""
    texts = {}
    for m in re.finditer(r'\(property\s+"(Reference|Value|Footprint)"', block):
        # Find the balanced block for this property
        depth = 0
        i = m.start()
        start = i
        while i < len(block):
            if block[i] == '(':
                depth += 1
            elif block[i] == ')':
                depth -= 1
                if depth == 0:
                    prop_block = block[start:i+1]
                    break
            i += 1
        else:
            continue
        
        prop_name = m.group(1)
        at_match = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', prop_block)
        if at_match:
            x = float(at_match.group(1))
            y = float(at_match.group(2))
            angle = float(at_match.group(3)) if at_match.group(3) else 0
            
            # Check hide
            hide = "hide" in prop_block and "do_not_autoplace" not in prop_block.split("hide")[0][-20:]
            
            layer_match = re.search(r'\(layer\s+"([^"]+)"\)', prop_block)
            layer = layer_match.group(1) if layer_match else "?"
            
            texts[prop_name] = {
                'x': x, 'y': y, 'angle': angle, 'layer': layer,
                'block': prop_block
            }
    return texts

print("Extracting footprints...")
stash_fps = extract_footprints("/tmp/pcb_stash.kicad_pcb")
head_fps = extract_footprints("/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_pcb")

print(f"Stash: {len(stash_fps)} footprints, HEAD: {len(head_fps)} footprints")

# Compare Reference and Value text positions
changed = []
for ref in sorted(set(stash_fps.keys()) & set(head_fps.keys())):
    stash_texts = extract_fp_texts(stash_fps[ref])
    head_texts = extract_fp_texts(head_fps[ref])
    
    for prop in ["Reference", "Value"]:
        if prop in stash_texts and prop in head_texts:
            s = stash_texts[prop]
            h = head_texts[prop]
            if (abs(s['x'] - h['x']) > 0.01 or abs(s['y'] - h['y']) > 0.01 or
                abs(s['angle'] - h['angle']) > 0.01 or s['layer'] != h['layer']):
                changed.append({
                    'ref': ref,
                    'prop': prop,
                    'stash': s,
                    'head': h
                })

print(f"\n=== MODIFIED fp_text positions: {len(changed)} ===")
for c in changed:
    s = c['stash']
    h = c['head']
    print(f"  {c['ref']} {c['prop']}:")
    print(f"    STASH: ({s['x']}, {s['y']}) angle={s['angle']} layer={s['layer']}")
    print(f"    HEAD:  ({h['x']}, {h['y']}) angle={h['angle']} layer={h['layer']}")
