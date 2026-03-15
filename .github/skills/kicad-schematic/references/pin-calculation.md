# Pin-Position-Berechnung

## Grundformel

Für ein Symbol an Position `(sx, sy)` mit Rotation `θ` (in Grad):

```
Pin lokal:     (px, py)        ← aus lib_symbols Cache
Rotiert:       (rx, ry) = rotate_ccw(px, py, θ)
Schematisch:   (sx + rx, sy - ry)    ← KiCad Y-Achse invertiert!
```

## Rotation (Counter-Clockwise)

```python
import math

def pin_schematic_position(symbol_x, symbol_y, symbol_rot_deg, pin_local_x, pin_local_y):
    """Berechnet die Schematic-Position eines Pins."""
    theta = math.radians(symbol_rot_deg)
    # CCW-Rotation
    rx = pin_local_x * math.cos(theta) - pin_local_y * math.sin(theta)
    ry = pin_local_x * math.sin(theta) + pin_local_y * math.cos(theta)
    # KiCad: Y-Achse invertiert
    sch_x = symbol_x + rx
    sch_y = symbol_y - ry
    return round(sch_x, 2), round(sch_y, 2)
```

## Schnell-Referenz für Standard-Rotationen

| Symbol-Rotation | Transformation (px, py) → (rx, ry) | Schematic |
|-----------------|-------------------------------------|-----------|
| 0°   | (px, py) → (px, py)       | (sx + px, sy - py) |
| 90°  | (px, py) → (-py, px)      | (sx - py, sy - px) |
| 180° | (px, py) → (-px, -py)     | (sx - px, sy + py) |
| 270° | (px, py) → (py, -px)      | (sx + py, sy + px) |

## Beispiel: AudioJack2 bei (40.16, 82.46) @ 180°

```
Pin T lokal: (5.08, 0)
  → rot 180°: (-5.08, 0)
  → schematic: (40.16 + (-5.08), 82.46 - 0) = (35.08, 82.46)

Pin S lokal: (5.08, 2.54)
  → rot 180°: (-5.08, -2.54)
  → schematic: (40.16 + (-5.08), 82.46 - (-2.54)) = (35.08, 85.0)
```

## Pin-Positionen aus lib_symbols lesen

```python
import re

def get_pin_positions(cache_block, symbol_name):
    """Liest Pin-Positionen aus einem lib_symbols Cache-Block."""
    pins = {}
    # Finde Sub-Symbol mit den Pins (typisch: _0_1)
    for m in re.finditer(r'\(pin \w+ \w+ \(at ([\d.]+) ([\d.]+) (\d+)\).*?\(number "([^"]+)"\)', cache_block, re.DOTALL):
        px, py = float(m.group(1)), float(m.group(2))
        pin_angle = int(m.group(3))
        pin_number = m.group(4)
        pins[pin_number] = (px, py, pin_angle)
    return pins
```

## Wire-Endpunkt = Pin-Schematic-Position

Ein Wire muss **exakt** an der berechneten Pin-Schematic-Position beginnen/enden.
Toleranz: ±0.01mm (KiCad-internes Raster).

**WICHTIG**: MCP-erstellte Wires verbinden Pins nur zuverlässig, wenn mindestens ein **Net-Label** im Wire-Chain vorhanden ist. Ohne Label erkennt KiCad die Pin-Verbindung möglicherweise nicht!

```python
# Wire von Pin zu Label (bevorzugt — Label sorgt für zuverlässige Netz-Erkennung)
wire = f'(wire (pts (xy {pin_x} {pin_y}) (xy {label_x} {label_y})) (stroke (width 0) (type default)) (uuid "{uuid}"))'
label = f'(label "{net_name}" (at {label_x} {label_y} 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{label_uuid}"))'
```

## Pin-Richtung (für Wire-Routing)

Der `pin_angle` (0°, 90°, 180°, 270°) gibt die Richtung an, in die der Pin zeigt.
Wire sollte in die **entgegengesetzte** Richtung verlaufen:

| Pin-Winkel | Pin zeigt nach | Wire geht nach |
|------------|---------------|----------------|
| 0°         | Rechts        | Links vom Pin  |
| 90°        | Oben          | Unten vom Pin  |
| 180°       | Links         | Rechts vom Pin |
| 270°       | Unten         | Oben vom Pin   |

Bei 180°-Pin (zeigt nach links): Wire geht nach rechts → höhere X-Koordinaten.

## Häufig verwendete Symbol-Positionen

### LM4562 (SOIC-8, keine Rotation)

**ACHTUNG**: Die Pin-Positionen stammen aus dem lib_symbols-Cache des Schaltplans.
Immer mit `get_lib_pins()` verifizieren — sie können von KiCad-Version zu Version variieren!

| Pin | Nummer | Lokal (x,y) | Bei (80, 110) @ 0° |
|-----|--------|-------------|---------------------|
| Out A | 1 | (7.62, 0) | (87.62, 110) |
| -In A | 2 | (-7.62, -2.54) | (72.38, 112.54) |
| +In A | 3 | (-7.62, 2.54) | (72.38, 107.46) |
| V- | 4 | (-2.54, -7.62) | (77.46, 117.62) |
| +In B | 5 | (-7.62, 2.54) | (72.38, 107.46) |
| -In B | 6 | (-7.62, -2.54) | (72.38, 112.54) |
| Out B | 7 | (7.62, 0) | (87.62, 110) |
| V+ | 8 | (-2.54, 7.62) | (77.46, 102.38) |

*Pins 5-7 gelten für Unit 2 an eigener (at)-Position.*
*Pins 4+8 gelten für Unit 3 (Power) an eigener (at)-Position.*

### Barrel_Jack (keine Rotation)
| Pin | Lokal (x,y) |
|-----|-------------|
| 1 (Center/+) | (5.08, 0) |
| 2 (Barrel/GND) | (5.08, 5.08) |
