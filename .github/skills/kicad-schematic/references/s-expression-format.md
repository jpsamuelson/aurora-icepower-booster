# S-Expression Format Reference

## KiCad .kicad_sch Dateistruktur

```
(kicad_sch (version ...) (generator ...) (generator_version ...)
  (uuid "...")
  (paper "A1")
  (lib_symbols
    (symbol "Library:SymbolName" ...)     ← Cache aller verwendeten Symbole
    (symbol "Library:AnotherSymbol" ...)
  )
  (wire (pts ...) ...)                     ← Wires
  (label "NetName" (at X Y A) ...)         ← Net-Labels
  (junction (at X Y) ...)                  ← Junctions
  (symbol (lib_id "Library:Symbol")        ← Symbol-Instanzen
    (at X Y Rotation) 
    (property "Reference" "R1" ...)
    (property "Value" "10k" ...)
    (property "Footprint" "..." ...)
    ...
  )
  (sheet_instances ...)                     ← Optional
)
```

## Symbol-Block extrahieren (Balanced-Paren-Methode)

**IMMER diese Methode verwenden**, nie Regex über die ganze Datei:

```python
def extract_block(text, start_idx):
    """Extrahiert den balancierten Klammer-Block ab start_idx."""
    depth = 0
    for i in range(start_idx, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start_idx:i+1]
    return None
```

### Symbol finden und Block extrahieren

```python
import re

def find_symbol_by_reference(sch_text, reference):
    """Findet den Symbol-Block für eine bestimmte Reference (z.B. 'J14')."""
    # Alle Symbol-Starts finden
    for m in re.finditer(r'\(symbol \(lib_id "([^"]+)"\)\s*\(at', sch_text):
        block_start = m.start()
        block = extract_block(sch_text, block_start)
        if block and f'"Reference" "{reference}"' in block:
            return m.group(1), block  # (lib_id, full_block)
    return None, None
```

## lib_symbols Cache — Korrekte Struktur

```
(symbol "Connector_Audio:AudioJack2"       ← MIT Library-Prefix
  (exclude_from_sim no)
  (in_bom yes) (on_board yes)
  (property "Reference" "J" ...)
  (property "Value" "AudioJack2" ...)
  (property "Footprint" "" ...)
  (symbol "AudioJack2_0_1"                 ← OHNE Library-Prefix!
    (polyline ...)
    (pin passive line (at 5.08 0 180) 
      (length 2.54)
      (name "~" ...) (number "T" ...))     ← Pin T
    (pin passive line (at 5.08 2.54 180) 
      (length 2.54)  
      (name "~" ...) (number "S" ...))     ← Pin S
  )
  (symbol "AudioJack2_1_1"                 ← OHNE Library-Prefix!
    ...
  )
)
```

### Sub-Symbol-Naming-Regeln
- Format: `{SymbolName}_{unit}_{variant}`
- unit: 0-basiert (0 = graphisches, 1+ = Units)
- variant: 1 (Standard)
- **Kein Library-Prefix** bei Sub-Symbolen
- Vergleich mit funktionierenden Einträgen: `XLR3_Ground_0_1`, `Barrel_Jack_0_1`

### Symbol aus System-Library extrahieren

```python
def extract_from_system_library(library_name, symbol_name):
    """Liest ein Symbol aus der KiCad-Systembibliothek."""
    lib_path = f"/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/{library_name}.kicad_sym"
    with open(lib_path) as f:
        lib_text = f.read()
    
    # Hauptsymbol finden
    idx = lib_text.find(f'(symbol "{symbol_name}"')
    if idx < 0:
        return None
    
    block = extract_block(lib_text, idx)
    
    # Für lib_symbols Cache: Library-Prefix zum Hauptsymbol hinzufügen
    # aber NOT zu Sub-Symbolen
    prefixed = block.replace(
        f'(symbol "{symbol_name}"',
        f'(symbol "{library_name}:{symbol_name}"',
        1  # Nur das erste Vorkommen (Hauptsymbol)
    )
    return prefixed
```

## S-Expression Templates

### Wire
```
(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uuid}"))
```

### Label
```
(label "{net_name}" (at {x} {y} {angle}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uuid}"))
```

### Junction
```
(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid "{uuid}"))
```

### GND Power Symbol
```
(symbol (lib_id "power:GND") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uuid}") (property "Reference" "#PWR0{n}" (at {x} {y+1.27} 0) (effects (font (size 1.27 1.27)) hide)) (property "Value" "GND" (at {x} {y+1.016} 0) (effects (font (size 1.27 1.27)) hide)))
```

### Symbol-Instanz
```
(symbol (lib_id "{library}:{symbol}") (at {x} {y} {rotation}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uuid}") (property "Reference" "{ref}" (at {rx} {ry} 0) (effects (font (size 1.27 1.27)))) (property "Value" "{value}" (at {vx} {vy} 0) (effects (font (size 1.27 1.27)))) (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)) (property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)))
```

### Property-Offset-Konventionen
- Reference: (x, y - 2.54) relativ zum Symbol-Zentrum
- Value: (x, y + 2.54) relativ zum Symbol-Zentrum
- Bei Rotation 90°: Offsets rotieren mit

## Einfüge-Position in der Datei

Neue Elemente vor der letzten schließenden Klammer einfügen:

```python
def insert_before_end(sch_text, new_element):
    """Fügt Element vor der letzten ')' der Datei ein."""
    last_paren = sch_text.rfind(')')
    return sch_text[:last_paren] + ' ' + new_element + ')'
```

Für lib_symbols Cache:

```python
def insert_in_lib_symbols(sch_text, new_symbol_def):
    """Fügt Symbol-Definition in die lib_symbols-Sektion ein."""
    # Ende der lib_symbols-Sektion finden
    lib_start = sch_text.find('(lib_symbols')
    if lib_start < 0:
        return None
    block_end_idx = find_balanced_end(sch_text, lib_start)
    # Vor der schließenden Klammer von lib_symbols einfügen
    return sch_text[:block_end_idx] + ' ' + new_symbol_def + sch_text[block_end_idx:]
```

## Häufige Fehlerquellen

### Greedy Regex (GEFÄHRLICH)
```python
# FALSCH — matcht über Symbol-Grenzen:
re.search(r'lib_id "([^"]+)".*?Reference.*?J14', text, re.DOTALL)

# RICHTIG — erst Block extrahieren:
lib_id, block = find_symbol_by_reference(text, "J14")
```

### Pin-Nummer als reine Zahl
```python
# FALSCH — matcht keine Buchstaben-Pins:
re.findall(r'pin "(\d+)"', block)

# RICHTIG:
re.findall(r'pin "([^"]+)"', block)
```

### Einfach-Zeilen-Format
Die .kicad_sch Datei kann ein einzeiliges S-Expression-Format haben (kein `\n`).
- `replace_string_in_file` ist unzuverlässig für solche Dateien
- Immer Python-Skripte für Manipulation verwenden
- `grep` / `sed` funktionieren nicht zuverlässig
