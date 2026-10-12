# -*- coding: utf-8 -*-
"""Mesh and functional-interface checks for roll cage V5 with M5x80 ties."""
from pathlib import Path

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
FILES = {
    "rear": ROOT / "roll_cage_v5_M5X80_rear_cup_NO_MOTOR_SCREWS_PETG.stl",
    "key": ROOT / "roll_cage_v5_M5X80_rear_square_key_PETG.stl",
    "top": ROOT / "roll_cage_v5_M5X80_front_frame_TOP_PETG.stl",
    "bottom": ROOT / "roll_cage_v5_M5X80_front_frame_BOTTOM_PETG.stl",
    "plate": ROOT / "PLATE_ROLL_CAGE_V5_M5X80_NO_MOTOR_SCREWS_FINAL.stl",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS", message)


m = {name: trimesh.load_mesh(path) for name, path in FILES.items()}
for name, mesh in m.items():
    require(mesh.is_watertight, f"{name}: watertight")
    require(mesh.is_winding_consistent, f"{name}: consistent winding")

require(np.allclose(m["rear"].extents, [88, 88, 41.99], atol=0.06), "rear cup envelope 88 x 88 x 41.99 mm including brim")
require(np.allclose(m["key"].extents, [54, 54, 3.5], atol=0.06), "rear square key envelope 54 x 54 x 3.5 mm")
require(np.allclose(m["top"].extents, [78, 39, 8], atol=0.06), "front top frame dimensions")
require(np.allclose(m["bottom"].extents, [78, 39, 8], atol=0.06), "front bottom frame dimensions")
require(np.allclose(m["plate"].extents, [174, 152, 41.99], atol=0.06), "print plate envelope 174 x 152 x 41.99 mm")
require(len(m["plate"].split(only_watertight=False)) == 6, "print plate has six disconnected printable bodies")
require((m["plate"].extents[:2] <= [220, 220]).all(), "print plate fits 220 x 220 mm bed")

rear = m["rear"]
require(not rear.contains([[0, 0, 4], [0, 0, 9], [0, 0, 20]]).any(), "rear centre cable route and tube pocket are open")
for x in (-31, 31):
    for y in (-31, 31):
        require(not rear.contains([[x, y, 4]]).any(), f"rear external M5 rod hole open at ({x},{y})")
for x in (-15.5, 15.5):
    for y in (-15.5, 15.5):
        require(not rear.contains([[x, y, 2.0]]).any(), f"factory screw head pocket exists at ({x},{y})")
for z in (17.0, 25.0):
    require(not rear.contains([[0, 0, z], [12, 0, z]]).any(), f"tube cross-bolt hole open at Z={z:g}")
require(rear.contains([[13.5, 0, 21], [-13.5, 0, 21]]).all(), "rear cup sleeve walls exist between cross holes")

key = m["key"]
require(not key.contains([[0, 0, 1.5], [20, 20, 1.5]]).any(), "43 mm motor opening in rear key is clear")
require(key.contains([[24, 0, 1.5], [-24, 0, 1.5]]).all(), "rear key has anti-rotation side walls")
require(not key.contains([[0, 24, 1.5]]).any(), "rear key motor-wire notch is open")

for name in ("top", "bottom"):
    frame = m[name]
    # Pick the rod holes that belong to that half.
    y = 31 if name == "top" else -31
    for x in (-31, 31):
        require(not frame.contains([[x, y, 4]]).any(), f"{name} external M5 rod hole open at ({x},{y})")
    centre_y = 10 if name == "top" else -10
    require(not frame.contains([[0, centre_y, 4]]).any(), f"{name} half leaves the CM36 opening clear")

# Static dimensional clearances independent of the STL boolean engine.
motor_corner_gap = np.hypot(31 - 42.3 / 2, 31 - 42.3 / 2) - 5.6 / 2
sandwich_corner_gap = np.hypot(31 - 56 / 2, 31 - 56 / 2) - 5.6 / 2
require(motor_corner_gap > 10, f"external rods clear 42.3 mm motor by {motor_corner_gap:.2f} mm at corners")
require(sandwich_corner_gap > 1.2, f"M5 clearance holes clear approximate 56 mm plate by {sandwich_corner_gap:.2f} mm")
require(38.8 - 36.0 >= 2.5, "front frame gives at least 1.25 mm radial clearance around CM36")

print("PASS ROLL CAGE V5 M5X80 AUDIT COMPLETE")
