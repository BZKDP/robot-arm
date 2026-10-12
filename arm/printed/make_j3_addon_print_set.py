# -*- coding: utf-8 -*-
"""
J3 add-on print set, without magnetic-angle-sensor parts.

New mechanical interface:
    20x20x1.5 tube -> deep square cup -> 8 x M4 -> perforated bottom of
    the 48x43 mm goBILDA-style U bracket.

The U-bottom hole pattern is taken from the measured/project model:
    (x, y) = (+/-16, +/-8) and (+/-8, +/-16), hole diameter 4.2 mm.

The cup prints flange-down and includes a 78 x 0.4 mm sacrificial adhesion
disc.  The tube is retained by two transverse M4 bolts through a hollow
16.6 mm internal anti-crush spacer.  Its 10.5 mm longitudinal cable channel
keeps the centre route usable.  No AS5600 bracket or magnet holder is put on
the combined plate, per the user's request.  The plate also carries the two
small anti-crush sleeves required by the already-printed roll cup.
"""
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import box as shapely_box


ROOT = Path(__file__).resolve().parent

CUP_OUT = ROOT / "j3_tube_to_u_cup_v1_FINAL_PETG.stl"
CUP_ALIAS = ROOT / "PRINT_J3_TUBE_TO_U_CUP.stl"
SPACER_OUT = ROOT / "j3_cup_internal_spacer_v1_PETG.stl"
CASSETTE_OUT = ROOT / "j3_nut_cassette_v4_single_PETG.stl"
PLATE_OUT = ROOT / "PLATE_J3_ADDON_NO_SENSORS_FINAL.stl"


def cyl(d, h, z0, x=0.0, y=0.0, sections=64):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=h, sections=sections)
    mesh.apply_translation([x, y, z0 + h / 2])
    return mesh


def boxc(sx, sy, sz, x=0.0, y=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_translation([x, y, z0 + sz / 2])
    return mesh


def hex_prism(across_flats, h, z0, x=0.0, y=0.0):
    mesh = trimesh.creation.cylinder(
        radius=across_flats / np.sqrt(3), height=h, sections=6
    )
    # Put flats parallel to X/Y for normal DIN934 nuts.
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 6, [0, 0, 1]))
    mesh.apply_translation([x, y, z0 + h / 2])
    return mesh


def transverse_cylinder_x(d, length, z, y=0.0):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=length, sections=48)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    mesh.apply_translation([0, y, z])
    return mesh


def triangular_gusset_x(sign, z0, height, x_inner, x_outer, width):
    """Triangular prism from square cup wall to the flange, along +/-X."""
    xi = sign * x_inner
    xo = sign * x_outer
    vertices = np.array(
        [
            [xi, -width / 2, z0], [xo, -width / 2, z0], [xi, -width / 2, z0 + height],
            [xi, width / 2, z0], [xo, width / 2, z0], [xi, width / 2, z0 + height],
        ],
        dtype=float,
    )
    faces = np.array(
        [
            [0, 1, 2], [3, 5, 4],
            [0, 3, 4], [0, 4, 1],
            [0, 2, 5], [0, 5, 3],
            [1, 4, 5], [1, 5, 2],
        ]
    )
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    # The mirrored (-X) prism has the opposite winding; boolean engines
    # require every closed shell to have a positive (outward) volume.
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def triangular_gusset_y(sign, z0, height, y_inner, y_outer, width):
    mesh = triangular_gusset_x(sign, z0, height, y_inner, y_outer, width)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    return mesh


# ---- Tube-to-U cup -------------------------------------------------------
FLANGE_X = 58.0
FLANGE_Y = 52.0
FLANGE_T = 8.0
FLANGE_CORNER_R = 3.0
TUBE_POCKET = 20.4
WALL = 4.8
OUTER = TUBE_POCKET + 2 * WALL       # 30.0 mm
CUP_HEIGHT = 43.0                    # total printable height
POCKET_FLOOR_Z = FLANGE_T + 1.5
BRIM_D = 78.0
BRIM_T = 0.4
M4_CLEARANCE = 4.6
M4_NUT_AF = 7.45
M4_NUT_DEPTH = 3.6
TUBE_BOLT_Z = (FLANGE_T + 11.0, FLANGE_T + 25.0)

# Rounded rectangular flange made from a Shapely outline.
flange_outline = shapely_box(
    -FLANGE_X / 2 + FLANGE_CORNER_R,
    -FLANGE_Y / 2 + FLANGE_CORNER_R,
    FLANGE_X / 2 - FLANGE_CORNER_R,
    FLANGE_Y / 2 - FLANGE_CORNER_R,
).buffer(FLANGE_CORNER_R, join_style=1)
flange = trimesh.creation.extrude_polygon(flange_outline, FLANGE_T)

body_parts = [
    cyl(BRIM_D, BRIM_T, 0.0, sections=96),
    flange,
    boxc(OUTER, OUTER, CUP_HEIGHT - FLANGE_T, 0, 0, FLANGE_T - 0.01),
]

# Four broad ribs carry bending load from the square sleeve into the flange.
for sign in (-1, 1):
    body_parts.append(
        triangular_gusset_x(sign, FLANGE_T - 0.02, 12.0, OUTER / 2 - 0.1, FLANGE_X / 2 - 2.0, 8.0)
    )
    body_parts.append(
        triangular_gusset_y(sign, FLANGE_T - 0.02, 12.0, OUTER / 2 - 0.1, FLANGE_Y / 2 - 2.0, 8.0)
    )

cup_body = trimesh.boolean.union(body_parts)

cup_cuts = [
    # Square tube pocket.  The 1.5 mm annular floor seats the tube end.
    boxc(TUBE_POCKET, TUBE_POCKET, CUP_HEIGHT - POCKET_FLOOR_Z + 2, 0, 0, POCKET_FLOOR_Z),
    # Cable route aligns with the U bracket's central Ø14 opening.
    cyl(14.0, POCKET_FLOOR_Z + 2, -1.0),
]

# Eight existing Ø4.2 holes in the U-bottom.  Bolts enter from inside the U;
# M4 nuts drop into open pockets on the cup side before the tube is inserted.
U_BOTTOM_M4 = [
    (-16, -8), (-16, 8), (16, -8), (16, 8),
    (-8, -16), (8, -16), (-8, 16), (8, 16),
]
for x, y in U_BOTTOM_M4:
    cup_cuts.append(cyl(M4_CLEARANCE, FLANGE_T + 3, -1, x, y, sections=40))
    cup_cuts.append(
        hex_prism(M4_NUT_AF, M4_NUT_DEPTH + 0.5, FLANGE_T - M4_NUT_DEPTH, x, y)
    )

# Two M4 bolts, 14 mm apart, cross sleeve + tube + solid internal spacer.
for z in TUBE_BOLT_Z:
    cup_cuts.append(transverse_cylinder_x(M4_CLEARANCE, OUTER + 5, z))

cup = trimesh.boolean.difference([cup_body] + cup_cuts)
cup.remove_unreferenced_vertices()
cup.merge_vertices()

for path in (CUP_OUT, CUP_ALIAS):
    cup.export(path)


# ---- Solid anti-crush insert for the tube inside the cup ----------------
SPACER_XY = 16.6
SPACER_LEN = 32.0
spacer_body = boxc(SPACER_XY, SPACER_XY, SPACER_LEN)
SPACER_CABLE = 10.5
spacer_cuts = [
    # A square longitudinal route leaves 3.05 mm anti-crush walls.  Motor
    # wiring can pass on either side of each transverse M4 shank.
    boxc(SPACER_CABLE, SPACER_CABLE, SPACER_LEN + 2, 0, 0, -1),
]
for cup_z in TUBE_BOLT_Z:
    relative_z = cup_z - POCKET_FLOOR_Z
    spacer_cuts.append(transverse_cylinder_x(M4_CLEARANCE, SPACER_XY + 3, relative_z))
spacer = trimesh.boolean.difference([spacer_body] + spacer_cuts)
spacer.remove_unreferenced_vertices()
spacer.export(SPACER_OUT)


# ---- One existing v4 nut cassette for the new J3 output tube ------------
cassette_pair = trimesh.load_mesh(ROOT / "nut_cassette_v4_x2_PETG.stl")
cassette_parts = cassette_pair.split(only_watertight=False)
if len(cassette_parts) < 2:
    raise RuntimeError("Expected two disconnected v4 cassettes in the source STL")
cassette = cassette_parts[0].copy()
cassette.apply_translation(-cassette.bounds[0])
cassette.export(CASSETTE_OUT)


# ---- Combined 220x220-bed print plate -----------------------------------
def grounded(mesh):
    result = mesh.copy()
    result.apply_translation(-result.bounds[0])
    return result


adapter = grounded(trimesh.load_mesh(ROOT / "gearbox_adapter_J2_v2.stl"))
bridge = grounded(trimesh.load_mesh(ROOT / "flange_bridge_v7_FINAL_T5_PETG.stl"))
cup_plate = grounded(cup)
spacer_plate = grounded(spacer)
cassette_plate = grounded(cassette)
roll_spacers_plate = grounded(trimesh.load_mesh(ROOT / "tube_spacers_x2_PETG.stl"))

# Manual packing keeps the cup's sacrificial disc clear of every other part.
placements = [
    (cup_plate, 0.0, 0.0),
    (adapter, 86.0, 0.0),
    (bridge, 86.0, 49.0),
    (cassette_plate, 134.0, 49.0),
    (spacer_plate, 160.0, 49.0),
    (roll_spacers_plate, 160.0, 77.0),
]
plate_parts = []
for mesh, x, y in placements:
    mesh.apply_translation([x, y, 0])
    plate_parts.append(mesh)

plate = trimesh.util.concatenate(plate_parts)
plate.apply_translation(
    [-(plate.bounds[0][0] + plate.bounds[1][0]) / 2,
     -(plate.bounds[0][1] + plate.bounds[1][1]) / 2,
     -plate.bounds[0][2]]
)
plate.export(PLATE_OUT)


def report(name, mesh):
    print(
        name,
        "watertight=", mesh.is_watertight,
        "volume_mm3=", round(float(mesh.volume), 1),
        "extents_mm=", np.round(mesh.extents, 2),
    )


report("J3 CUP", cup)
report("CUP SPACER", spacer)
report("J3 CASSETTE", cassette)
report("COMBINED PLATE", plate)
print("U-bottom pattern: 8 x M4 at (+/-16,+/-8) and (+/-8,+/-16)")
print("Tube pocket:", TUBE_POCKET, "mm; engagement:", CUP_HEIGHT - POCKET_FLOOR_Z, "mm")
print("Tube cross bolts Z:", TUBE_BOLT_Z, "mm; use M4x40 + washers + nyloc")
print("Spacer cable channel:", SPACER_CABLE, "x", SPACER_CABLE, "mm")
print("Combined plate:", PLATE_OUT)
