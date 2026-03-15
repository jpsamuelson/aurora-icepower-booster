#!/usr/bin/env python3
"""
Wiederverwendbare KiCad S-Expression Manipulation Library.
Importierbar in andere Skripte:

    from kicad_sexp import SchematicEditor, extract_block, pin_schematic_position
"""
import re
import math
import uuid as uuid_mod


def extract_block(text, start_idx):
    """Extrahiert einen balancierten Klammer-Block ab start_idx."""
    depth = 0
    for i in range(start_idx, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start_idx:i+1]
    return None


def paren_balance(text):
    """Gibt die Klammer-Balance zurueck (0 = korrekt)."""
    depth = 0
    for ch in text:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    return depth


def new_uuid():
    """Erzeugt eine neue UUID fuer KiCad-Elemente."""
    return str(uuid_mod.uuid4())


def pin_schematic_position(symbol_x, symbol_y, symbol_rot_deg, pin_local_x, pin_local_y):
    """Berechnet die Schematic-Position eines Pins.
    
    Args:
        symbol_x, symbol_y: Symbol-Position im Schematic
        symbol_rot_deg: Symbol-Rotation in Grad (0, 90, 180, 270)
        pin_local_x, pin_local_y: Pin-Position relativ zum Symbol-Zentrum (aus lib_symbols)
    
    Returns:
        (sch_x, sch_y): Pin-Position im Schematic-Koordinatensystem
    """
    theta = math.radians(symbol_rot_deg)
    rx = pin_local_x * math.cos(theta) - pin_local_y * math.sin(theta)
    ry = pin_local_x * math.sin(theta) + pin_local_y * math.cos(theta)
    sch_x = symbol_x + rx
    sch_y = symbol_y - ry
    return round(sch_x, 2), round(sch_y, 2)


def make_wire(x1, y1, x2, y2):
    """Erzeugt ein Wire S-Expression Element."""
    return (
        f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) '
        f'(stroke (width 0) (type default)) (uuid "{new_uuid()}"))'
    )


def make_label(net_name, x, y, angle=0):
    """Erzeugt ein Label S-Expression Element."""
    return (
        f'(label "{net_name}" (at {x} {y} {angle}) (fields_autoplaced yes) '
        f'(effects (font (size 1.27 1.27)) (justify left)) (uuid "{new_uuid()}"))'
    )


def make_junction(x, y):
    """Erzeugt ein Junction S-Expression Element."""
    return (
        f'(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) '
        f'(uuid "{new_uuid()}"))'
    )


def make_symbol(library, symbol_name, ref, value, x, y, rotation=0, footprint="", unit=1):
    """Erzeugt ein Symbol-Instanz S-Expression Element."""
    rx, ry = x, y - 2.54  # Reference offset
    vx, vy = x, y + 2.54  # Value offset
    fp_str = f'{library}:{footprint}' if footprint and ':' not in footprint else footprint
    return (
        f'(symbol (lib_id "{library}:{symbol_name}") (at {x} {y} {rotation}) '
        f'(unit {unit}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) '
        f'(uuid "{new_uuid()}") '
        f'(property "Reference" "{ref}" (at {rx} {ry} 0) '
        f'(effects (font (size 1.27 1.27)))) '
        f'(property "Value" "{value}" (at {vx} {vy} 0) '
        f'(effects (font (size 1.27 1.27)))) '
        f'(property "Footprint" "{fp_str}" (at {x} {y} 0) '
        f'(effects (font (size 1.27 1.27)) hide)) '
        f'(property "Datasheet" "~" (at {x} {y} 0) '
        f'(effects (font (size 1.27 1.27)) hide)))'
    )


class SchematicEditor:
    """Editor fuer KiCad .kicad_sch Dateien."""
    
    def __init__(self, path):
        self.path = path
        with open(path) as f:
            self.text = f.read()
    
    def find_symbol_by_reference(self, reference):
        """Findet lib_id und Block fuer eine Reference."""
        for m in re.finditer(r'\(symbol \(lib_id "([^"]+)"\)\s*\(at', self.text):
            block = extract_block(self.text, m.start())
            if block and f'"Reference" "{reference}"' in block:
                return m.group(1), block, m.start()
        return None, None, None
    
    def get_lib_symbols_section(self):
        """Gibt Start-Index und Block der lib_symbols-Sektion zurueck."""
        idx = self.text.find('(lib_symbols')
        if idx < 0:
            return None, None
        block = extract_block(self.text, idx)
        return idx, block
    
    def get_pin_positions(self, reference):
        """Liest Pin-Positionen eines Symbols im Schematic-Koordinatensystem."""
        lib_id, block, _ = self.find_symbol_by_reference(reference)
        if not block:
            return None
        
        # Symbol-Position und Rotation
        pos_m = re.search(r'\(at ([\d.]+) ([\d.]+) (\d+)\)', block)
        if not pos_m:
            return None
        sx, sy, rot = float(pos_m.group(1)), float(pos_m.group(2)), int(pos_m.group(3))
        
        # Lib-Prefix entfernen fuer Cache-Suche
        symbol_name = lib_id.split(':')[-1] if ':' in lib_id else lib_id
        
        # Pins aus lib_symbols Cache lesen
        lib_idx, lib_block = self.get_lib_symbols_section()
        if not lib_block:
            return None
        
        # Sub-Symbol mit Pins finden
        pins = {}
        for m in re.finditer(
            r'\(pin \w+ \w+ \(at ([\d.]+) ([\d.]+) (\d+)\).*?\(number "([^"]+)"\)',
            lib_block, re.DOTALL
        ):
            # Nur Pins dieses Symbols (grob: muss nach dem Hauptsymbol-Start kommen)
            cache_sym_start = lib_block.find(f'(symbol "{lib_id}"')
            if cache_sym_start < 0:
                continue
            cache_sym_end_block = extract_block(lib_block, cache_sym_start)
            if cache_sym_end_block and m.group(0) in cache_sym_end_block:
                px, py = float(m.group(1)), float(m.group(2))
                pin_num = m.group(4)
                sch_x, sch_y = pin_schematic_position(sx, sy, rot, px, py)
                pins[pin_num] = (sch_x, sch_y)
        
        return pins
    
    def insert_before_end(self, element):
        """Fuegt Element vor der letzten ')' der Datei ein."""
        last_paren = self.text.rfind(')')
        self.text = self.text[:last_paren] + ' ' + element + ')'
    
    def insert_in_lib_symbols(self, symbol_def):
        """Fuegt Symbol-Definition in lib_symbols-Sektion ein."""
        idx, block = self.get_lib_symbols_section()
        if idx is None:
            return False
        # Ende der lib_symbols-Sektion (vor schliessender Klammer)
        end_of_block = idx + len(block) - 1  # Position der ')'
        self.text = self.text[:end_of_block] + ' ' + symbol_def + self.text[end_of_block:]
        return True
    
    def add_wire(self, x1, y1, x2, y2):
        """Fuegt einen Wire hinzu."""
        self.insert_before_end(make_wire(x1, y1, x2, y2))
    
    def add_label(self, net_name, x, y, angle=0):
        """Fuegt ein Label hinzu."""
        self.insert_before_end(make_label(net_name, x, y, angle))
    
    def add_junction(self, x, y):
        """Fuegt eine Junction hinzu."""
        self.insert_before_end(make_junction(x, y))
    
    def validate(self):
        """Prueft Klammer-Balance."""
        bal = paren_balance(self.text)
        if bal != 0:
            raise ValueError(f"Klammer-Balance: {bal}")
        return True
    
    def save(self, path=None):
        """Speichert die Datei (nach Validierung)."""
        self.validate()
        target = path or self.path
        with open(target, 'w') as f:
            f.write(self.text)
    
    def backup(self, suffix):
        """Erstellt ein Backup mit dem gegebenen Suffix."""
        import shutil
        backup_path = f"{self.path}.bak_pre_{suffix}"
        shutil.copy2(self.path, backup_path)
        return backup_path
