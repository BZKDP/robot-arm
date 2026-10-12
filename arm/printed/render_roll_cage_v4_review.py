# -*- coding: utf-8 -*-
"""Visual engineering review of the no-factory-screw roll cage V5 M5x80."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ROLL_CAGE_V5_M5X80_NO_MOTOR_SCREWS_REVIEW.png"


def rgba(value, alpha=1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def draw(ax, mesh, color, alpha=1.0, edge="#3b2716", lw=0.08):
    triangles = mesh.triangles
    if len(triangles) > 18000:
        triangles = triangles[::int(np.ceil(len(triangles) / 18000))]
    ax.add_collection3d(Poly3DCollection(
        triangles,
        facecolor=rgba(color, alpha),
        edgecolor=rgba(edge, min(1.0, alpha + 0.12)),
        linewidth=lw,
    ))


def equal(ax, bounds, elev=26, azim=-48, zscale=0.75):
    bounds = np.asarray(bounds, float)
    centre = bounds.mean(axis=0)
    span = max(bounds[1] - bounds[0]) * 0.58
    ax.set_xlim(centre[0] - span, centre[0] + span)
    ax.set_ylim(centre[1] - span, centre[1] + span)
    ax.set_zlim(centre[2] - span * zscale, centre[2] + span * zscale)
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 1, zscale * 1.35))
    ax.set_axis_off()


def box(extents, centre):
    mesh = trimesh.creation.box(extents=extents)
    mesh.apply_translation(centre)
    return mesh


def cyl_y(d, length, x, y, z, sections=40):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=length, sections=sections)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    mesh.apply_translation([x, y, z])
    return mesh


def local_z_to_world_y(mesh, direction=1, y_shift=0):
    result = mesh.copy()
    result.apply_transform(np.array([
        [1, 0, 0, 0],
        [0, 0, direction, y_shift],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ], float))
    return result


rear = trimesh.load_mesh(ROOT / "roll_cage_v5_M5X80_rear_cup_NO_MOTOR_SCREWS_PETG.stl")
key = trimesh.load_mesh(ROOT / "roll_cage_v5_M5X80_rear_square_key_PETG.stl")
front_top = trimesh.load_mesh(ROOT / "roll_cage_v5_M5X80_front_frame_TOP_PETG.stl")
front_bottom = trimesh.load_mesh(ROOT / "roll_cage_v5_M5X80_front_frame_BOTTOM_PETG.stl")
plate = trimesh.load_mesh(ROOT / "PLATE_ROLL_CAGE_V5_M5X80_NO_MOTOR_SCREWS_FINAL.stl")

fig = plt.figure(figsize=(18, 11), facecolor="#f3f5f7")
grid = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.28, 1.0], hspace=0.14, wspace=0.04)

ax = fig.add_subplot(grid[0, 0], projection="3d")
draw(ax, rear, "#e68b2d")
equal(ax, rear.bounds, elev=28, azim=-50)
ax.set_title("1. Задний стакан — реальная STL\n88 × 88 × 42 мм с печатным кантом", fontsize=12.5, weight="bold")

ax = fig.add_subplot(grid[1, 0], projection="3d")
pieces = []
for mesh, dx, dy, color in (
    (front_top, -42, 12, "#65bb72"),
    (front_bottom, 42, 12, "#65bb72"),
    (key, 0, -55, "#48b9dd"),
):
    item = mesh.copy()
    item.apply_translation([dx, dy, 0])
    pieces.append(item)
    draw(ax, item, color)
all_bounds = np.vstack([p.bounds for p in pieces])
equal(ax, [all_bounds.min(axis=0), all_bounds.max(axis=0)], elev=61, azim=-72)
ax.set_title("2. Разъёмная клетка\nзелёные половины спереди · голубой квадрат сзади", fontsize=12.5, weight="bold")

# Assembly: remove the 0.4 mm sacrificial disc from the visual model.
clip = box([120, 120, 60], [0, 0, 30.4])
rear_structural = trimesh.boolean.intersection([rear, clip])
rear_w = local_z_to_world_y(rear_structural, direction=-1)
key_w = local_z_to_world_y(key, direction=1)
top_w = local_z_to_world_y(front_top, direction=1, y_shift=50)
bottom_w = local_z_to_world_y(front_bottom, direction=1, y_shift=50)

ax = fig.add_subplot(grid[:, 1], projection="3d")
draw(ax, rear_w, "#ed932f", alpha=0.86)
draw(ax, key_w, "#48b9dd", alpha=0.9, edge="#15596d")
draw(ax, box([42.3, 47, 42.3], [0, 23.5, 0]), "#30343a", alpha=0.93, edge="#101215")
draw(ax, box([56, 3, 56], [0, 48.5, 0]), "#aeb7c0", alpha=0.72, edge="#444b52")
draw(ax, cyl_y(36, 35, 0, 67.5, 0), "#315fab", alpha=0.95, edge="#17366a")
draw(ax, cyl_y(8, 17, 0, 93.5, 0), "#9ea8b2", alpha=0.9, edge="#434c55")
draw(ax, top_w, "#62bf72", alpha=0.86, edge="#21602c")
draw(ax, bottom_w, "#62bf72", alpha=0.86, edge="#21602c")

# Hollow 20x20 tube behind the cup.
for tube_wall in (
    box([20, 105, 1.5], [0, -61.5, -9.25]), box([20, 105, 1.5], [0, -61.5, 9.25]),
    box([1.5, 105, 17], [-9.25, -61.5, 0]), box([1.5, 105, 17], [9.25, -61.5, 0]),
):
    draw(ax, tube_wall, "#68727c", alpha=0.85, edge="#262c32")

for x in (-31, 31):
    for z in (-31, 31):
        draw(ax, cyl_y(5, 80, x, 32.0, z), "#e5bb3e", edge="#634b0e")

# Red discs are the original motor screws: visible but never removed/loaded.
for x in (-15.5, 15.5):
    for z in (-15.5, 15.5):
        draw(ax, cyl_y(7, 2.5, x, -0.8, z), "#df574f", edge="#6f1916")

equal(ax, [[-58, -125, -58], [58, 108, 58]], elev=20, azim=-48)
ax.set_title(
    "3. Собранный вариант без заводских винтов\n"
    "жёлтые — 4 внешние M5×80\n"
    "красные — старые винты остаются на месте",
    fontsize=12.5,
    weight="bold",
)

ax = fig.add_subplot(grid[0, 2], projection="3d")
draw(ax, plate, "#d98729")
equal(ax, plate.bounds, elev=72, azim=-90)
ax.set_title("4. Один файл на печать\n174 × 152 × 42 мм · 6 тел", fontsize=12.5, weight="bold")

ax = fig.add_subplot(grid[1, 2])
ax.axis("off")
ax.text(
    0.02, 0.98,
    "КАК ДЕРЖИТСЯ МОТОР\n\n"
    "• задняя плита упирается в крышку\n"
    "• голубой квадрат не даёт проворачиваться\n"
    "• зелёные половины упираются в переднюю\n"
    "  часть/металлическую пластину\n"
    "• 4 внешние M5 стягивают весь пакет\n\n"
    "ЗАВОДСКИЕ ВИНТЫ\n"
    "не выкручиваются и нагрузку не несут;\n"
    "под их головки сделаны четыре кармана Ø8,2\n\n"
    "КРЕПЁЖ\n"
    "4 × M5×80 + 8 шайб + 4 nyloc\n"
    "2 × M4×40 для трубы\n"
    "2 печатные распорные втулки\n\n"
    "ПОСАДКИ\n"
    "мотор: 42,3 мм\n"
    "голубой квадрат: 43,0 мм\n"
    "редуктор: Ø36\n"
    "проход зелёной рамки: Ø38,8",
    va="top", fontsize=11.7, family="DejaVu Sans Mono",
    bbox=dict(boxstyle="round,pad=0.7", facecolor="white", edgecolor="#cbd1d6"),
)

fig.suptitle("ROLL V5 M5×80 — КЛЕТКА NEMA17 БЕЗ ОТКРУЧИВАНИЯ ЗАВОДСКИХ ВИНТОВ", fontsize=18, weight="bold", y=0.98)
fig.savefig(OUT, dpi=170, bbox_inches="tight")
plt.close(fig)
print("PASS", OUT)
