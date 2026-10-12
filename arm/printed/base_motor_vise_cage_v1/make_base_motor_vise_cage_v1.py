# -*- coding: utf-8 -*-
"""Printable vise-safe cage for the bottom NEMA17 + CM36 assembly.

The motor factory screws remain untouched.  Four longitudinal M5x80 rods
clamp a rear reaction plate, two ventilated jaw shells and a split front frame.
The vise grips the broad PETG sides of the lower jaw shell, never the motor.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely.geometry import box as shapely_box


ROOT = Path(__file__).resolve().parent
REAR_OUT = ROOT / "base_vise_cage_v1_rear_plate_PETG.stl"
LOWER_OUT = ROOT / "base_vise_cage_v1_lower_jaw_PETG.stl"
UPPER_OUT = ROOT / "base_vise_cage_v1_upper_cover_PETG.stl"
FRONT_TOP_OUT = ROOT / "base_vise_cage_v1_front_frame_TOP_PETG.stl"
FRONT_BOTTOM_OUT = ROOT / "base_vise_cage_v1_front_frame_BOTTOM_PETG.stl"
FIT_TEST_OUT = ROOT / "base_vise_cage_v1_motor_fit_test_43mm.stl"
PLATE_OUT = ROOT / "PLATE_BASE_VISE_CAGE_V1_PRINT_ALL.stl"
ASSEMBLY_OUT = ROOT / "base_vise_cage_v1_ASSEMBLY_REVIEW_ONLY.stl"
REVIEW_OUT = ROOT / "BASE_VISE_CAGE_V1_REVIEW.png"

# Known project dimensions.
MOTOR_SIDE = 42.3
MOTOR_LENGTH = 48.0
GEARBOX_D = 36.0
GEARBOX_LENGTH = 35.0

# Main fit and cage dimensions.
JAW_INNER = 43.2             # 0.45 mm nominal clearance per side
KEY_INNER = 43.0             # rear anti-rotation key; test before full print
JAW_LENGTH = 42.5            # clears rear key and front reaction plate
JAW_X = 1.75                 # leaves 1 mm at both axial ends
JAW_OUTER_Y = 72.0
JAW_HALF_Z = 36.0
PLATE_SIZE = 78.0
PLATE_T = 8.0
PLATE_R = 5.0
ROD_GRID = 31.0              # same proven 62 x 62 mm grid as roll cage V5
M5_CLEAR = 5.8
GEARBOX_CLEAR = 38.8
FACTORY_HEAD_CLEAR = 8.2


def boxc(sx, sy, sz, x=0.0, y=0.0, z=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_translation([x, y, z])
    return mesh


def cyl_x(d, length, x=0.0, y=0.0, z=0.0, sections=64):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=length, sections=sections)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    mesh.apply_translation([x, y, z])
    return mesh


def rounded_rect(width, depth, radius):
    return shapely_box(
        -width / 2 + radius,
        -depth / 2 + radius,
        width / 2 - radius,
        depth / 2 - radius,
    ).buffer(radius, join_style=1)


def rounded_plate_x(size_y, size_z, radius, thickness, x0):
    # Polygon X/Y becomes final Z/Y after rotating its extrusion onto X.
    mesh = trimesh.creation.extrude_polygon(rounded_rect(size_z, size_y, radius), thickness)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    mesh.apply_translation([x0, 0, 0])
    return mesh


def clean(mesh):
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    return mesh


def ground(mesh):
    result = mesh.copy()
    result.apply_translation(-result.bounds[0])
    return result


def orient_x_plate_for_print(mesh):
    result = mesh.copy()
    result.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
    return ground(result)


# ---------------------------------------------------------------------------
# Rear reaction plate with integrated square anti-rotation key.
# ---------------------------------------------------------------------------
rear_base = rounded_plate_x(PLATE_SIZE, PLATE_SIZE, PLATE_R, PLATE_T, -32.0)
rear_cuts = []

for y in (-ROD_GRID, ROD_GRID):
    for z in (-ROD_GRID, ROD_GRID):
        rear_cuts.append(cyl_x(M5_CLEAR, PLATE_T + 2, -28.0, y, z, sections=48))

# Shallow pockets receive the untouched factory M3 screw heads.
for y in (-15.5, 15.5):
    for z in (-15.5, 15.5):
        rear_cuts.append(cyl_x(FACTORY_HEAD_CLEAR, 5.4, -26.6, y, z, sections=48))

# Large lower cable exit, away from the four head pockets.
rear_cuts.append(boxc(15.0, 18.0, 19.0, -25.5, 0.0, -18.5))
rear = trimesh.boolean.difference([rear_base] + rear_cuts)

# 3.5 mm deep key surrounds the rear edge of the 42.3 mm motor.
key_outer = boxc(3.55, 54.0, 54.0, -22.275, 0, 0)
key_inner = boxc(4.5, KEY_INNER, KEY_INNER, -22.25, 0, 0)
key_notch = boxc(5.0, 18.0, 20.0, -22.25, 0, -18.0)
key_ring = trimesh.boolean.difference([key_outer, key_inner, key_notch])
rear = clean(trimesh.boolean.union([rear, key_ring]))


# ---------------------------------------------------------------------------
# Lower vise jaw.  The vise contacts the flat y=+-36 mm sides.
# ---------------------------------------------------------------------------
lower_outer = boxc(JAW_LENGTH, JAW_OUTER_Y, JAW_HALF_Z, JAW_X, 0, -JAW_HALF_Z / 2)
lower_cavity = boxc(JAW_LENGTH + 2, JAW_INNER, JAW_INNER / 2 + 1.2,
                    JAW_X, 0, -JAW_INNER / 4 + 0.6)
lower_cuts = [lower_cavity]
for y in (-ROD_GRID, ROD_GRID):
    lower_cuts.append(cyl_x(M5_CLEAR, JAW_LENGTH + 2, JAW_X, y, -ROD_GRID, sections=48))

# Broad rear cable relief continues the opening in the rear plate.
lower_cuts.append(boxc(12.0, 20.0, 18.0, JAW_X - JAW_LENGTH / 2 + 3.0, 0, -18.0))
lower = clean(trimesh.boolean.difference([lower_outer] + lower_cuts))


# ---------------------------------------------------------------------------
# Upper cover; same square motor fit, with five cooling slots in its roof.
# ---------------------------------------------------------------------------
upper_outer = boxc(JAW_LENGTH, JAW_OUTER_Y, JAW_HALF_Z, JAW_X, 0, JAW_HALF_Z / 2)
upper_cavity = boxc(JAW_LENGTH + 2, JAW_INNER, JAW_INNER / 2 + 1.2,
                    JAW_X, 0, JAW_INNER / 4 - 0.6)
upper_cuts = [upper_cavity]
for y in (-ROD_GRID, ROD_GRID):
    upper_cuts.append(cyl_x(M5_CLEAR, JAW_LENGTH + 2, JAW_X, y, ROD_GRID, sections=48))
for x in (-16.0, -8.0, 0.0, 8.0, 16.0):
    upper_cuts.append(boxc(5.0, 28.0, 18.0, JAW_X + x, 0, 29.0))
upper = clean(trimesh.boolean.difference([upper_outer] + upper_cuts))


# ---------------------------------------------------------------------------
# Split front reaction frame.  It installs around an already mounted CM36.
# ---------------------------------------------------------------------------
front_full = rounded_plate_x(PLATE_SIZE, PLATE_SIZE, PLATE_R, PLATE_T, 24.0)
front_cuts = [cyl_x(GEARBOX_CLEAR, PLATE_T + 2, 28.0, 0, 0, sections=96)]
for y in (-ROD_GRID, ROD_GRID):
    for z in (-ROD_GRID, ROD_GRID):
        front_cuts.append(cyl_x(M5_CLEAR, PLATE_T + 2, 28.0, y, z, sections=48))

# Relief for possible motor/gearbox screw heads around the CM36 body.
for y in (-15.5, 15.5):
    for z in (-15.5, 15.5):
        front_cuts.append(cyl_x(FACTORY_HEAD_CLEAR, 5.4, 25.4, y, z, sections=48))

front = trimesh.boolean.difference([front_full] + front_cuts)
front_top = clean(trimesh.boolean.intersection([front, boxc(12, 90, 45, 28, 0, 22.5)]))
front_bottom = clean(trimesh.boolean.intersection([front, boxc(12, 90, 45, 28, 0, -22.5)]))


# ---------------------------------------------------------------------------
# Fit coupon for the critical 43.0 mm square rear key.
# ---------------------------------------------------------------------------
fit_outer = boxc(3.5, 54.0, 54.0, 0, 0, 0)
fit_inner = boxc(5.0, KEY_INNER, KEY_INNER, 0, 0, 0)
fit_notch = boxc(5.0, 18.0, 20.0, 0, 0, -18.0)
fit_test = clean(trimesh.boolean.difference([fit_outer, fit_inner, fit_notch]))


# ---------------------------------------------------------------------------
# Export individual print-oriented parts.
# ---------------------------------------------------------------------------
rear_print = orient_x_plate_for_print(rear)
lower_print = ground(lower)

# Turn the upper cover upside-down: solid roof on the bed, motor cavity upward.
upper_print = upper.copy()
upper_print.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
upper_print = ground(upper_print)

front_top_print = orient_x_plate_for_print(front_top)
front_bottom_print = orient_x_plate_for_print(front_bottom)
fit_test_print = orient_x_plate_for_print(fit_test)

for mesh, path in (
    (rear_print, REAR_OUT),
    (lower_print, LOWER_OUT),
    (upper_print, UPPER_OUT),
    (front_top_print, FRONT_TOP_OUT),
    (front_bottom_print, FRONT_BOTTOM_OUT),
    (fit_test_print, FIT_TEST_OUT),
):
    mesh.export(path)


# One 190 x 168 mm plate, five disconnected printable bodies.
items = [
    (rear_print, 0.0, 0.0),
    (lower_print, 88.0, 0.0),
    (upper_print, 144.0, 0.0),
    (front_top_print, 0.0, 90.0),
    (front_bottom_print, 49.0, 90.0),
]
placed = []
for mesh, x, y in items:
    item = mesh.copy()
    item.apply_translation([x, y, 0])
    placed.append(item)
plate = trimesh.util.concatenate(placed)
plate.apply_translation([
    -(plate.bounds[0][0] + plate.bounds[1][0]) / 2,
    -(plate.bounds[0][1] + plate.bounds[1][1]) / 2,
    -plate.bounds[0][2],
])
plate.export(PLATE_OUT)

assembly = trimesh.util.concatenate([rear, lower, upper, front_top, front_bottom])
assembly.export(ASSEMBLY_OUT)


# ---------------------------------------------------------------------------
# Review sheet.
# ---------------------------------------------------------------------------
def rgba(value, alpha=1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def draw_mesh(ax, mesh, color, alpha=1.0, edge="#22272d", lw=0.06):
    tris = mesh.triangles
    ax.add_collection3d(Poly3DCollection(
        tris, facecolor=rgba(color, alpha), edgecolor=rgba(edge, min(1.0, alpha + 0.15)), linewidth=lw,
    ))


def set_view(ax, bounds, elev=24, azim=-48):
    bounds = np.asarray(bounds, float)
    center = bounds.mean(axis=0)
    span = max(bounds[1] - bounds[0]) * 0.62
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(center[2] - span, center[2] + span)
    ax.set_box_aspect((1.0, 1.0, 1.0))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


motor = boxc(MOTOR_LENGTH, MOTOR_SIDE, MOTOR_SIDE, 0, 0, 0)
gearbox = cyl_x(GEARBOX_D, GEARBOX_LENGTH, 24.0 + GEARBOX_LENGTH / 2, 0, 0, sections=72)
shaft = cyl_x(8.0, 13.0, 24.0 + GEARBOX_LENGTH + 6.5, 0, 0, sections=48)
bolts = [cyl_x(5.0, 80.0, 0, y, z, sections=32) for y in (-ROD_GRID, ROD_GRID) for z in (-ROD_GRID, ROD_GRID)]

# Conceptual steel vise jaws pressing only the printed lower shell.
vise_a = boxc(66, 8, 24, 0, -40, -16)
vise_b = boxc(66, 8, 24, 0, 40, -16)

fig = plt.figure(figsize=(19, 11), facecolor="#f2f5f8")
gs = fig.add_gridspec(2, 3, width_ratios=[1.15, 1.15, 0.9], hspace=0.08, wspace=0.03)

ax = fig.add_subplot(gs[:, :2], projection="3d")
for mesh, color, alpha in (
    (rear, "#e6962d", 0.98), (lower, "#e6962d", 0.92), (upper, "#f0aa46", 0.72),
    (front_top, "#50ae7b", 0.93), (front_bottom, "#50ae7b", 0.93),
    (motor, "#272a2d", 1.0), (gearbox, "#3157a4", 1.0), (shaft, "#aeb7bf", 1.0),
    (vise_a, "#59636d", 0.72), (vise_b, "#59636d", 0.72),
):
    draw_mesh(ax, mesh, color, alpha)
for bolt in bolts:
    draw_mesh(ax, bolt, "#c79a35", 1.0)
set_view(ax, [[-42, -54, -45], [86, 54, 45]], elev=23, azim=-53)
ax.set_title(
    "СОБРАННАЯ КЛЕТКА НИЖНЕГО NEMA17\n"
    "серые губки тисков касаются только печатной нижней обоймы",
    fontsize=13, weight="bold",
)

ax = fig.add_subplot(gs[0, 2], projection="3d")
exploded = [
    (rear, [-20, 0, 0], "#e6962d"),
    (lower, [0, 0, -12], "#e6962d"),
    (upper, [0, 0, 12], "#f0aa46"),
    (front_top, [20, 0, 12], "#50ae7b"),
    (front_bottom, [20, 0, -12], "#50ae7b"),
]
for mesh, offset, color in exploded:
    item = mesh.copy(); item.apply_translation(offset); draw_mesh(ax, item, color, 0.96)
draw_mesh(ax, motor, "#272a2d", 1.0); draw_mesh(ax, gearbox, "#3157a4", 1.0)
set_view(ax, [[-55, -48, -52], [95, 48, 52]], elev=24, azim=-48)
ax.set_title("РАЗБОРНАЯ КОНСТРУКЦИЯ · 5 ПЕЧАТНЫХ ДЕТАЛЕЙ", fontsize=11, weight="bold")

ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
notes = (
    "КАК РАБОТАЕТ\n"
    "• мотор 42,3 × 42,3 × 47–48 мм\n"
    "• редуктор CM36 проходит через Ø38,8\n"
    "• заводские винты мотора не откручиваются\n"
    "• задний ключ 43,0 мм не даёт мотору вращаться\n"
    "• нижняя/верхняя обоймы: карман 43,2 мм\n"
    "• 4 внешних M5×80 стягивают весь пакет\n"
    "• тиски зажимают плоские стенки нижней обоймы\n"
    "• провод выходит через заднее нижнее окно\n"
    "• верх имеет пять вентиляционных пазов\n\n"
    "КРЕПЁЖ НА ОДНУ КЛЕТКУ\n"
    "4 × M5×80 DIN 912\n"
    "8 × увеличенная шайба M5\n"
    "4 × гайка M5 DIN 985 nyloc\n\n"
    "M4×40 здесь не требуется:\n"
    "он остаётся для стакана roll и трубы 20×20.\n\n"
    "СНАЧАЛА НАПЕЧАТАТЬ ПРОБНИК 43,0 мм.\n"
    "Полная пластина: 186,5 × 168 мм, 5 тел."
)
ax.text(0.02, 0.98, notes, va="top", fontsize=10.5, family="DejaVu Sans Mono",
        bbox=dict(boxstyle="round,pad=.7", facecolor="white", edgecolor="#aab5c0"))

fig.suptitle("КОРПУС НИЖНЕГО NEMA17 ДЛЯ ЗАЖИМА В ТИСКАХ · V1", fontsize=18, weight="bold", y=.985)
fig.savefig(REVIEW_OUT, dpi=175, bbox_inches="tight")
plt.close(fig)


def report(name, mesh):
    print(name, "watertight=", mesh.is_watertight,
          "components=", len(mesh.split(only_watertight=False)),
          "extents=", np.round(mesh.extents, 2),
          "volume=", round(float(mesh.volume), 1))


for name, mesh in (
    ("REAR", rear_print), ("LOWER", lower_print), ("UPPER", upper_print),
    ("FRONT TOP", front_top_print), ("FRONT BOTTOM", front_bottom_print),
    ("FIT TEST", fit_test_print), ("PRINT PLATE", plate),
):
    report(name, mesh)

print("MOTOR", MOTOR_SIDE, "x", MOTOR_SIDE, "x", MOTOR_LENGTH)
print("M5 rod grid", ROD_GRID * 2, "x", ROD_GRID * 2, "mm; hole", M5_CLEAR, "mm")
print("PRINT PLATE bounds", np.round(plate.bounds, 2))
print("OUTPUT", REVIEW_OUT)
