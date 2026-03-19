#!/usr/bin/env python3
"""
Fix: 2 Symbole haben falsche instances-Path UUID.
Richtig: /09fde901-d8c0-4b5a-a63a-824cb2cd0bb6  (440x verwendet)
Falsch:  /e42b1bb1-fbe7-4279-a498-b6ec67098e90  (2x - veraltet)

Wenn instances path auf falsche UUID zeigt, findet eeschema keine Instanz
und behandelt das Symbol als unannotiert (#PWR?).
"""
import re

SCH = "aurora-dsp-icepower-booster.kicad_sch"
with open(SCH, "r") as f:
    content = f.read()

WRONG_UUID = "e42b1bb1-fbe7-4279-a498-b6ec67098e90"
RIGHT_UUID = "09fde901-d8c0-4b5a-a63a-824cb2cd0bb6"

# Zeige welche Symbole betroffen sind
print(f"Vorkommen von falschem UUID: {content.count(WRONG_UUID)}")
idx = 0
while True:
    idx = content.find(WRONG_UUID, idx)
    if idx == -1:
        break
    ctx = content[max(0, idx-150):idx+200]
    print(f"  offset {idx}: ...{ctx}...")
    print()
    idx += 1

# Bracket balance vorher
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Vorher schon defekt: {depth}"

# Fix: alle falschen UUIDs ersetzen
new_content = content.replace(WRONG_UUID, RIGHT_UUID)

print(f"UUID-Ersetzungen: {content.count(WRONG_UUID)} → 0")
print(f"Verbleibende alte UUID: {new_content.count(WRONG_UUID)}")

# Bracket balance nachher
depth = 0
for ch in new_content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1
assert depth == 0, f"Klammer-Balance: {depth}"
print(f"Klammer-Balance: OK")

with open(SCH, "w") as f:
    f.write(new_content)
print(f"Geschrieben: {SCH}")
