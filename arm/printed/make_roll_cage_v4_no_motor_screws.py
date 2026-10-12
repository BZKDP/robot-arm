# -*- coding: utf-8 -*-
"""
ROLL CAGE V4 — mounts a NEMA17 + CM36 assembly without touching the four
factory motor tie screws.

Load path:
    20x20 tube -> deep rear cup -> rear motor face / square anti-rotation key
    -> four external M5 tie rods -> split front reaction frame.

The front frame is split so it can be installed around the existing gearbox.
The four external rods sit outside both the 42.3 mm motor and the approximate
56 mm sandwich plate.  Factory motor screws remain installed and untouched.
"""
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import box as shapely_box


ROOT = Path(__file__).resolve().parent

REAR_OUT = ROOT / "roll_cage_v5_M5X80_rear_cup_NO_MOTOR_SCREWS_PETG.stl"
KEY_OUT = ROOT / "roll_cage_v5_M5X80_rear_square_key_PETG.stl"
FRONT_TOP_OUT = ROOT / "roll_cage_v5_M5X80_front_frame_TOP_PETG.stl"
FRONT_BOTTOM_OUT = ROOT / "roll_cage_v5_M5X80_front_frame_BOTTOM_PETG.stl"
PLATE_OUT = ROOT / "PLATE_ROLL_CAGE_V5_M5X80_NO_MOTOR_SCREWS_FINAL.stl"


def cyl(d, h, z0, x=0.0, y=0.0, sections=64):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=h, sections=sections)
    mesh.apply_translation([x, y, z0 + h / 2])
    return mesh


def boxc(sx, sy, sz, x=0.0, y=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_translation([x, y, z0 + sz / 2])
    return mesh


def transverse_cylinder_x(d, length, z, y=0.0):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=length, sections=48)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    mesh.apply_translation([0, y, z])
    return mesh


def rounded_rect(width, depth, radius):
    return shapely_box(
        -width / 2 + radius,
        -depth / 2 + radius,
        width / 2 - radius,
        depth / 2 - radius,
    ).buffer(radius, join_style=1)


def gusset_x(sign, z0, height, x_inner, x_outer, width):
    xi, xo = sign * x_inner, sign * x_outer
    vertices = np.array([
        [xi, -width / 2, z0], [xo, -width / 2, z0], [xi, -width / 2, z0 + height],
        [xi, width / 2, z0], [xo, width / 2, z0], [xi, width / 2, z0 + height],
    ])
    faces = np.array([
        [0, 1, 2], [3, 5, 4], [0, 3, 4], [0, 4, 1],
        [0, 2, 5], [0, 5, 3], [1, 4, 5], [1, 5, 2],
    ])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def gusset_y(sign, z0, height, y_inner, y_outer, width):
    mesh = gusset_x(sign, z0, height, y_inner, y_outer, width)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    return mesh


# -----------------------------------------------------------------------
# Rear tube cup and the rear reaction plate
# -----------------------------------------------------------------------
REAR_PLATE = 78.0
REAR_T = 8.0
REAR_R = 5.0
BRIM_D = 88.0
BRIM_T = 0.4

TUBE_POCKET = 20.4
WALL = 5.0
SLEEVE_OUTER = TUBE_POCKET + 2 * WALL   # 30.4
SLEEVE_TOP = 42.0
POCKET_FLOOR = REAR_T + 1.5             # motor face -> tube end offset 9.5
TUBE_BOLT_Z = (POCKET_FLOOR + 7.5, POCKET_FLOOR + 15.5)

ROD_GRID = 31.0                         # outside a 56 mm sandwich plate
M4_CLEAR = 4.6
M5_CLEAR = 5.6
FACTORY_HEAD_CLEAR = 8.2                # untouched factory M3 head clearance

rear_plate = trimesh.creation.extrude_polygon(
    rounded_rect(REAR_PLATE, REAR_PLATE, REAR_R), REAR_T
)

rear_parts = [
    cyl(BRIM_D, BRIM_T, 0, sections=96),
    rear_plate,
    boxc(SLEEVE_OUTER, SLEEVE_OUTER, SLEEVE_TOP - REAR_T, 0, 0, REAR_T - 0.01),
]
for sign in (-1, 1):
    rear_parts.append(gusset_x(sign, REAR_T - 0.02, 13.0, SLEEVE_OUTER / 2 - 0.1, 26.5, 9.0))
    rear_parts.append(gusset_y(sign, REAR_T - 0.02, 13.0, SLEEVE_OUTER / 2 - 0.1, 26.5, 9.0))
rear_body = trimesh.boolean.union(rear_parts)

rear_cuts = [
    # Deep tube pocket and the rear-motor-to-tube cable route.
    boxc(TUBE_POCKET, TUBE_POCKET, SLEEVE_TOP - POCKET_FLOOR + 2, 0, 0, POCKET_FLOOR),
    cyl(23.0, POCKET_FLOOR + 2, -1),
]

# Four external M5 tie rods: these are the only motor/cage fasteners.
for x in (-ROD_GRID, ROD_GRID):
    for y in (-ROD_GRID, ROD_GRID):
        rear_cuts.append(cyl(M5_CLEAR, REAR_T + 2, -1, x, y, sections=40))

# Shallow pockets receive the existing factory screw heads.  They are not
# bolts for this part and never need to be removed.
for x in (-15.5, 15.5):
    for y in (-15.5, 15.5):
        rear_cuts.append(cyl(FACTORY_HEAD_CLEAR, 6.0, -1, x, y, sections=48))

for z in TUBE_BOLT_Z:
    rear_cuts.append(transverse_cylinder_x(M4_CLEAR, SLEEVE_OUTER + 5, z))

# Open cable notch: no late bridge roof and no support inside the sleeve.
rear_cuts.append(boxc(13.0, SLEEVE_OUTER + 4, SLEEVE_TOP - 29.0 + 2, 0, 0, 29.0))

rear = trimesh.boolean.difference([rear_body] + rear_cuts)
rear.remove_unreferenced_vertices()
rear.merge_vertices()
rear.export(REAR_OUT)


# -----------------------------------------------------------------------
# Square anti-rotation key.  It surrounds 3.5 mm of the rear end cap and
# transfers roll torque by geometry instead of by the four factory screws.
# -----------------------------------------------------------------------
KEY_OUTER = 54.0
KEY_INNER = 43.0                       # 0.7 mm total clearance over 42.3 motor
KEY_T = 3.5

key_outer = rounded_rect(KEY_OUTER, KEY_OUTER, 4.0)
key_inner = rounded_rect(KEY_INNER, KEY_INNER, 2.0)
wire_notch = shapely_box(-8.0, 18.0, 8.0, KEY_OUTER / 2 + 1.0)
key_outline = key_outer.difference(key_inner.union(wire_notch))
key = trimesh.creation.extrude_polygon(key_outline, KEY_T)
key.export(KEY_OUT)


# -----------------------------------------------------------------------
# Split front reaction frame.  It installs from two sides around the CM36,
# so the gearbox and the motor do not need to be separated.
# -----------------------------------------------------------------------
FRONT_OUTER = 78.0
FRONT_T = 8.0
GEARBOX_CLEAR = 38.8                   # CM36 body + fitting clearance

front_body = trimesh.creation.extrude_polygon(
    rounded_rect(FRONT_OUTER, FRONT_OUTER, 5.0), FRONT_T
)
front_cuts = [cyl(GEARBOX_CLEAR, FRONT_T + 2, -1, sections=96)]

for x in (-ROD_GRID, ROD_GRID):
    for y in (-ROD_GRID, ROD_GRID):
        front_cuts.append(cyl(M5_CLEAR, FRONT_T + 2, -1, x, y, sections=40))

# Clearance for the motor/gearbox mounting screw heads if there is no large
# sandwich plate; with the plate present these holes are simply unused.
for x in (-15.5, 15.5):
    for y in (-15.5, 15.5):
        front_cuts.append(cyl(8.0, FRONT_T + 2, -1, x, y, sections=40))

front_full = trimesh.boolean.difference([front_body] + front_cuts)
top_clip = boxc(90, 45, FRONT_T + 4, 0, 22.5, -2)
bottom_clip = boxc(90, 45, FRONT_T + 4, 0, -22.5, -2)
front_top = trimesh.boolean.intersection([front_full, top_clip])
front_bottom = trimesh.boolean.intersection([front_full, bottom_clip])
for mesh, path in ((front_top, FRONT_TOP_OUT), (front_bottom, FRONT_BOTTOM_OUT)):
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    mesh.export(path)


# -----------------------------------------------------------------------
# Complete print plate: rear cup, key, split front frame and the two tube
# anti-crush sleeves already used by roll cup V3.
# -----------------------------------------------------------------------
def grounded(mesh):
    result = mesh.copy()
    result.apply_translation(-result.bounds[0])
    return result


roll_spacers = grounded(trimesh.load_mesh(ROOT / "tube_spacers_x2_PETG.stl"))
items = [
    (grounded(rear), 0.0, 0.0),
    (grounded(front_top), 96.0, 0.0),
    (grounded(front_bottom), 96.0, 44.0),
    (grounded(key), 0.0, 98.0),
    (roll_spacers, 62.0, 98.0),
]
placed = []
for mesh, x, y in items:
    mesh.apply_translation([x, y, 0])
    placed.append(mesh)
plate = trimesh.util.concatenate(placed)
plate.apply_translation([
    -(plate.bounds[0][0] + plate.bounds[1][0]) / 2,
    -(plate.bounds[0][1] + plate.bounds[1][1]) / 2,
    -plate.bounds[0][2],
])
plate.export(PLATE_OUT)


def report(label, mesh):
    print(
        label,
        "watertight=", mesh.is_watertight,
        "volume_mm3=", round(float(mesh.volume), 1),
        "extents_mm=", np.round(mesh.extents, 2),
        "components=", len(mesh.split(only_watertight=False)),
    )


report("REAR CUP", rear)
report("SQUARE KEY", key)
report("FRONT TOP", front_top)
report("FRONT BOTTOM", front_bottom)
report("PRINT PLATE", plate)
print("Factory motor screws: untouched; clearance pockets only")
print("External cage rods: grid 62 x 62 mm; clearance 5.6 mm; use 4 x M5x80 + washers + nyloc")
print("Motor fit in rear key:", KEY_INNER, "mm square for nominal 42.3 mm NEMA17")
print("Tube pocket:", TUBE_POCKET, "mm; engagement:", SLEEVE_TOP - POCKET_FLOOR, "mm")
print("OUTPUT", PLATE_OUT)
