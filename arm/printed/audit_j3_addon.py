# -*- coding: utf-8 -*-
"""Independent dimensional/mesh checks for the J3 add-on print set."""
from pathlib import Path

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
CUP = ROOT / "j3_tube_to_u_cup_v1_FINAL_PETG.stl"
SPACER = ROOT / "j3_cup_internal_spacer_v1_PETG.stl"
PLATE = ROOT / "PLATE_J3_ADDON_NO_SENSORS_FINAL.stl"


def close(actual, expected, tol=0.06):
    return bool(np.allclose(actual, expected, atol=tol, rtol=0))


def require(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS", message)


cup = trimesh.load_mesh(CUP)
spacer = trimesh.load_mesh(SPACER)
plate = trimesh.load_mesh(PLATE)

require(cup.is_watertight and cup.is_winding_consistent, "cup is a closed, consistently wound volume")
require(spacer.is_watertight and spacer.is_winding_consistent, "spacer is a closed, consistently wound volume")
require(plate.is_watertight and plate.is_winding_consistent, "combined plate contains valid closed volumes")
require(close(cup.extents, [78.0, 78.0, 42.99]), "cup envelope is 78 x 78 x 42.99 mm including adhesion disc")
require(close(spacer.extents, [16.6, 16.6, 32.0]), "spacer envelope is 16.6 x 16.6 x 32 mm")
require(close(plate.extents, [182.0, 109.0, 42.99]), "combined plate envelope is 182 x 109 x 42.99 mm")
require(len(plate.split(only_watertight=False)) == 7, "combined plate has exactly seven printable bodies")
require(plate.extents[0] <= 220 and plate.extents[1] <= 220, "combined plate fits a 220 x 220 mm bed")

# Point-membership probes verify that the booleans did not accidentally heal
# the functional openings.  All probe points are well away from boundaries.
u_holes = [(-16, -8), (-16, 8), (16, -8), (16, 8),
           (-8, -16), (8, -16), (-8, 16), (8, 16)]
for x, y in u_holes:
    inside = cup.contains([[x, y, 2.0], [x, y, 6.0]])
    require(not inside.any(), f"U-bottom M4 passage is open at ({x},{y})")

require(not cup.contains([[0, 0, 3.0], [0, 0, 8.5]]).any(), "central 14 mm wire passage is open")
require(not cup.contains([[0, 0, 12.0], [0, 0, 30.0], [0, 0, 41.0]]).any(), "20.4 mm tube pocket is open")
require(cup.contains([[13.0, 0, 26.0], [-13.0, 0, 26.0]]).all(), "square sleeve side walls exist between the cross holes")
for z in (19.0, 33.0):
    require(not cup.contains([[0, 0, z], [12.0, 0, z]]).any(), f"transverse M4 passage at Z={z:g} is open")

require(not spacer.contains([[0, 0, 4.0], [0, 0, 16.0], [0, 0, 28.0]]).any(), "10.5 mm spacer wire channel is open")
require(spacer.contains([[7.0, 0, 4.0], [-7.0, 0, 28.0]]).all(), "spacer anti-crush side walls exist")

print("PASS J3 ADD-ON AUDIT COMPLETE")
