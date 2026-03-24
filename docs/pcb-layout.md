# PCB Layout

[← Back to README](../README.md) | [Component Reference](component-reference.md)

---

## Overview

| Parameter | Value |
|-----------|-------|
| Board Size | 145.6 × 200 mm |
| Layers | 2 (F.Cu + B.Cu) |
| Footprints | 269 |
| Nets | 135 in 5 net classes |
| Routing | Freerouting v2.0.1 — 1543 segments + 476 vias |
| GND Zones | F.Cu (solid connect) + B.Cu (thermal relief) |
| DRC | 0 Errors, 0 Unconnected, 198 Warnings (cosmetic) |
| Silkscreen | 199 component references on F.Silkscreen |

---

## Net Classes

| Class | Nets | Track Width | Clearance |
|-------|------|-------------|-----------|
| Default | 62 | 0.25 mm | 0.2 mm |
| Audio_Input | 30 | 0.3 mm | 0.25 mm |
| Audio_Output | 36 | 0.5 mm | 0.2 mm |
| Audio_Power | 0 | 0.8 mm | 0.2 mm |
| Power | 7 | 0.5 mm | 0.2 mm |

---

## DRC Warnings Breakdown (198 total)

| Category | Count | Severity |
|----------|-------|----------|
| holes_co_located | 138 | Cosmetic |
| silk_edge_clearance | 27 | Cosmetic |
| silk_overlap | 11 | Cosmetic |
| silk_over_copper | 10 | Cosmetic |
| hole_to_hole | 9 | Cosmetic |
| via_dangling | 3 | Minor |

---

## Validation Status

This design was validated using two independent automated methods:

| Method | Checks | Result |
|--------|--------|--------|
| **Method 1** — OrcadPCB2 netlist, component-centric | 85/85 | ✅ |
| **Method 2** — KiCad-native netlist, net-centric (pintype/pinfunction) | 177/177 | ✅ |
