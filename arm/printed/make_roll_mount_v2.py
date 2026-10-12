# -*- coding: utf-8 -*-
"""
ROLL CUP V2: 20x20 tube end -> rear face of a NEMA17 motor.

Changes from the original roll_mount_PETG.stl:
- NEMA17 pattern remains the standard 31x31 mm square;
- printed M3 clearance is increased from 3.4 to 3.8 mm;
- four vertical corner scallops give a DIN912 M3 head and hex key real access;
- cross holes are 4.6 mm for M4 after PETG printing;
- old STL is intentionally preserved.

Print flange down, PETG, 0.2 mm, 5-6 walls, 60-100% infill.
"""
from pathlib import Path

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "roll_mount_v2_PETG.stl"
ALIAS = ROOT / "PLATE_2_ROLL_CUP_V2.stl"


def cyl(d, h, z0, x=0.0, y=0.0, sec=64):
    shape = trimesh.creation.cylinder(radius=d / 2, height=h, sections=sec)
    shape.apply_translation([x, y, z0 + h / 2])
    return shape


def boxc(sx, sy, sz, x, y, z0):
    shape = trimesh.creation.box(extents=[sx, sy, sz])
    shape.apply_translation([x, y, z0 + sz / 2])
    return shape


FLANGE = 50.0
FLANGE_T = 5.0
TUBE_POCKET = 20.4
WALL = 4.5
DEPTH = 32.0

body = trimesh.boolean.union(
    [
        boxc(FLANGE, FLANGE, FLANGE_T, 0, 0, 0),
        boxc(
            TUBE_POCKET + 2 * WALL,
            TUBE_POCKET + 2 * WALL,
            DEPTH,
            0,
            0,
            FLANGE_T - 0.01,
        ),
    ]
)

cuts = [
    # Tube pocket; leaves a 1.5 mm floor above the flange before the centre cut.
    boxc(TUBE_POCKET, TUBE_POCKET, DEPTH + 2, 0, 0, FLANGE_T + 1.5),
    # Motor ventilation/wire opening.
    cyl(23.0, FLANGE_T + 4, -1),
]

for sx in (-1, 1):
    for sy in (-1, 1):
        x = sx * 15.5
        y = sy * 15.5
        # Printed clearance for M3 on the standard NEMA17 31 mm square.
        cuts.append(cyl(3.8, FLANGE_T + 4, -1, x, y))
        # The old cup wall overlapped a DIN912 M3 head.  A full-height scallop
        # also leaves a straight path for the hex key during assembly.
        cuts.append(cyl(6.6, DEPTH + 1, FLANGE_T - 0.1, x, y))

# Two transverse M4 fasteners through cup + tube + internal tube spacers.
for z in (FLANGE_T + 9, FLANGE_T + 17):
    hole = trimesh.creation.cylinder(
        radius=2.3, height=TUBE_POCKET + 2 * WALL + 4, sections=48
    )
    hole.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
    )
    hole.apply_translation([0, 0, z])
    cuts.append(hole)

# Side-to-side wiring window.
cuts.append(boxc(12, TUBE_POCKET + 2 * WALL + 4, 10, 0, 0, FLANGE_T + 18))

part = trimesh.boolean.difference([body] + cuts)
part.remove_unreferenced_vertices()

for path in (OUT, ALIAS):
    part.export(path)

print("ROLL CUP V2", OUT)
print("  watertight:", part.is_watertight)
print("  extents:", np.round(part.extents, 3))
print("  NEMA17 pattern: 31x31 mm, M3 clearance 3.8 mm")
print("  head/tool scallops: 6.6 mm")
print("  tube cross holes: 4.6 mm for M4")

