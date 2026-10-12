# -*- coding: utf-8 -*-
"""
ROLL CUP V3 — print-stable final version.

Compared with V2:
- a built-in 70 mm x 0.4 mm sacrificial adhesion disc increases the bed contact
  area by about 66% after accounting for the existing holes, and is cut/peeled
  away after printing;
- the old enclosed cable window is changed to an open-top notch, eliminating
  the late 12 mm bridge whose curled edge could catch the nozzle;
- tube pocket, NEMA17 pattern, M3 head access and transverse M4 locations stay
  unchanged.
"""
from pathlib import Path

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "roll_mount_v3_FINAL_PRINTSAFE_PETG.stl"
ALIAS = ROOT / "PLATE_ROLL_CUP_V3_FINAL.stl"


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
OUTER = TUBE_POCKET + 2 * WALL
BRIM_D = 70.0
BRIM_T = 0.4

body = trimesh.boolean.union(
    [
        # Built into the STL so slicer brim settings cannot omit it.
        cyl(BRIM_D, BRIM_T, 0.0, sec=96),
        boxc(FLANGE, FLANGE, FLANGE_T, 0, 0, 0),
        boxc(OUTER, OUTER, DEPTH, 0, 0, FLANGE_T - 0.01),
    ]
)

cuts = [
    boxc(TUBE_POCKET, TUBE_POCKET, DEPTH + 2, 0, 0, FLANGE_T + 1.5),
    cyl(23.0, FLANGE_T + 4, -1),
]

for sx in (-1, 1):
    for sy in (-1, 1):
        x = sx * 15.5
        y = sy * 15.5
        cuts.append(cyl(3.8, FLANGE_T + 4, -1, x, y))
        cuts.append(cyl(6.6, DEPTH + 1, FLANGE_T - 0.1, x, y))

for z in (FLANGE_T + 9, FLANGE_T + 17):
    hole = trimesh.creation.cylinder(
        radius=2.3, height=OUTER + 4, sections=48
    )
    hole.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
    )
    hole.apply_translation([0, 0, z])
    cuts.append(hole)

# Open-top cable notch.  It begins above the upper M4 hole and never closes
# again, so the printer does not have to bridge a roof late in the print.
notch_z0 = FLANGE_T + 21.0
cuts.append(boxc(12, OUTER + 4, DEPTH + FLANGE_T - notch_z0 + 2, 0, 0, notch_z0))

part = trimesh.boolean.difference([body] + cuts)
part.remove_unreferenced_vertices()

for path in (OUT, ALIAS):
    part.export(path)

print("ROLL CUP V3 FINAL", OUT)
print("  watertight:", part.is_watertight)
print("  extents:", np.round(part.extents, 3))
print("  structural cup: 50 x 50 x 36.99 mm")
print("  built-in sacrificial adhesion disc: OD70 x 0.4 mm")
print("  cable notch: open top, no bridge roof")
print("  NEMA17/tube interfaces: unchanged from V2")
