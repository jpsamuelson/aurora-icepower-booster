#!/usr/bin/env python3
"""
Add KH-PJ-320EA-5P-SMT symbol to project symbol library.
"""

import re

PROJ_SYM = "/Users/roroor/Documents/Workspace/CAD/Electric/aurora-dsp-icepower-booster/aurora-dsp-icepower-booster.kicad_sym"

# The symbol definition for the 5-pin 3.5mm jack
# Pin assignment based on EasyEDA export:
# Pin 1: Tip (T) - audio signal
# Pin 2: Ring 1 (R1) - switch
# Pin 3: Ring 1 Normal (R1N) - switch normally closed
# Pin 4: Sleeve (S) - ground
# Pin 5: Tip Normal (TN) - switch detect
NEW_SYMBOL = '''
  (symbol "KH-PJ-320EA-5P-SMT" (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Value" "KH-PJ-320EA-5P-SMT" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "aurora-dsp-icepower-booster:AUDIO-SMD_KH-PJ-320EA-5P-SMT" (at 0 -11.43 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "https://www.lcsc.com/datasheet/C5123132.pdf" (at 0 -13.97 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "3.5mm Stereo Audio Jack SMD 5-Pin with detect switches, Kinghelm, LCSC C5123132" (at 0 -16.51 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "LCSC" "C5123132" (at 0 -19.05 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "ki_keywords" "audio jack 3.5mm stereo SMD connector" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "KH-PJ-320EA-5P-SMT_0_1"
        (polyline (pts (xy -2.54 5.08) (xy 0 5.08) (xy 0.635 4.445) (xy 1.27 5.08)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.54 0) (xy 0 0) (xy 0.635 0.635) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.54 -5.08) (xy 0 -5.08)) (stroke (width 0) (type default)) (fill (type none)))
        (rectangle (start -2.54 7.62) (end -3.81 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
        (polyline (pts (xy -2.54 2.54) (xy -1.27 2.54) (xy -1.27 -2.54) (xy -2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "KH-PJ-320EA-5P-SMT_1_1"
        (pin passive line (at 3.81 5.08 180) (length 2.54) (name "T" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 2.54 180) (length 2.54) (name "R1" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "R1N" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 -2.54 180) (length 2.54) (name "S" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 -5.08 180) (length 2.54) (name "TN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      )
      (embedded_fonts no))
'''

# Read current project symbol library
with open(PROJ_SYM, 'r') as f:
    content = f.read()

# Check if already exists
if 'KH-PJ-320EA-5P-SMT' in content:
    print("Symbol already exists in project library, skipping.")
else:
    # Insert before the closing parenthesis
    # Find the last )
    last_paren = content.rstrip().rfind(')')
    if last_paren < 0:
        print("ERROR: Cannot find closing parenthesis in symbol library!")
        exit(1)
    
    content = content[:last_paren] + NEW_SYMBOL + "\n)"
    
    with open(PROJ_SYM, 'w') as f:
        f.write(content)
    
    print("Symbol added to project library.")

# Verify bracket balance
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Bracket balance error: {depth}"
print(f"Bracket balance OK (depth=0)")
print("Done.")
