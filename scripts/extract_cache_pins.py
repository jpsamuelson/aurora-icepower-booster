#!/usr/bin/env python3
"""Extract the lib_symbols cache entries for TEL5-2422 and ADP7118ARDZ."""  
import re

SCH = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sch"

with open(SCH, 'r') as f:
    content = f.read()

def extract_balanced(text, start):
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(': depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0: return text[start:i+1]
        i += 1
    return None

# Find TEL5-2422 cache
for name in ["aurora-dsp-icepower-booster:TEL5-2422", "aurora-dsp-icepower-booster:ADP7118ARDZ"]:
    m = re.search(r'\(symbol\s+"' + re.escape(name) + r'"', content)
    if m:
        block = extract_balanced(content, m.start())
        if block:
            print(f"{'='*60}")
            print(f"Cache: {name}")
            print(f"{'='*60}")
            # Show first 3000 chars to see pin format
            print(block[:3000])
            if len(block) > 3000:
                print(f"\n... ({len(block)} chars total)")
            
            # Extract pins with more flexible regex
            pin_count = block.count('(pin ')
            print(f"\n  Total (pin ...) occurrences: {pin_count}")
            
            # Show all pin blocks
            for pm in re.finditer(r'\(pin\s+\w+\s+\w+\s+\(at\s+[^)]+\)', block):
                pin_text = block[pm.start():pm.start()+300]
                # Find the closing balanced block
                pb = extract_balanced(block, pm.start())
                if pb:
                    print(f"\n  PIN: {pb[:200]}")
            print()
