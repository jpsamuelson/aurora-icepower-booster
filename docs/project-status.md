# Project Status

> This file contains volatile project data (counts, coordinates, DRC results).
> Updated separately from the stable design rules in `.github/copilot-instructions.md`.

---

## Schematic Status

- **242 symbols**: 104 R, 64+4 C, 24 D (TVS), 15 U, 13 J, 6 SW
- **143 nets**, schematic exports cleanly
- **ERC**: 0 errors (reduced from 115→66→0), 890 warnings (838 off-grid, acceptable)
- All fixes (F1-F10) verified and passed

---

## PCB Routing Status (Commit bf62bd0)

- **0 Errors, 0 Unconnected, 198 Warnings** (all acceptable)
- 1543 trace segments + 476 vias via Freerouting v2.0.1
- 2 GND zones: F.Cu (solid connect) + B.Cu (thermal)
- 269 footprints, 135 nets in 5 classes

### DRC Breakdown (198 Warnings)

- 138× holes_co_located, 27× silk_edge_clearance, 11× silk_overlap
- 10× silk_over_copper, 9× hole_to_hole, 3× via_dangling

### Net Classes

| Class        | Nets | Track  | Clearance |
| ------------ | ---- | ------ | --------- |
| Default      | 62   | 0.25mm | 0.2mm     |
| Audio_Input  | 30   | 0.3mm  | 0.25mm    |
| Audio_Output | 36   | 0.5mm  | 0.2mm     |
| Audio_Power  | 0    | 0.8mm  | 0.2mm     |
| Power        | 7    | 0.5mm  | 0.2mm     |

---

## Next Steps

1. Remove dangling vias (3 total)
2. Export Gerber + drill files
3. Export BOM + placement data
4. Visual inspection in KiCad

---

## Reference Data

### Wire Dangling Fix Reference

- Wire-to-pin connections work reliably ONLY with at least one net label
- Fix: add `(label "NET_NAME" (at x y 0) ...)` at every dangling endpoint

### Channel Net Names (11 nets × 6 channels = 66)

CHn_INV_IN, CHn_SW_OUT_1/2/3, CHn_BUF_DRIVE, CHn_GAIN_FB, CHn_OUT_DRIVE, CHn_OUT_PROT_HOT, CHn_OUT_PROT_COLD, CHn_EMI_HOT, CHn_EMI_COLD

### Key Coordinates

- Channels: CY = 110 + (ch-1) × 80, for ch=1..6
- Input protection: X_PROT = 280
- Output Zobel HOT: X=265, COLD: X=280

### S-Expression Templates

```
Symbol: (symbol (lib_id "LIB") (at X Y A) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "UUID") (property "Reference" ...) ...)
Wire:   (wire (pts (xy X1 Y1) (xy X2 Y2)) (stroke (width 0) (type default)) (uuid "UUID"))
Label:  (label "NAME" (at X Y A) (fields_autoplaced yes) (effects ...) (uuid "UUID"))
```
