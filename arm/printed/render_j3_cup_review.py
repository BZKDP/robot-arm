# -*- coding: utf-8 -*-
"""Engineering preview of the J3 tube-to-U cup and its print plate."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "J3_CUP_CONNECTION_REVIEW.png"


def rgba(hex_color, alpha=1.0):
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def draw_mesh(ax, mesh, color, alpha=1.0, edges="#3a2414", linewidth=0.08):
    triangles = mesh.triangles
    if len(triangles) > 18000:
        triangles = triangles[::int(np.ceil(len(triangles) / 18000))]
    poly = Poly3DCollection(
        triangles,
        facecolor=rgba(color, alpha),
        edgecolor=rgba(edges, min(alpha + 0.1, 1.0)),
        linewidth=linewidth,
    )
    ax.add_collection3d(poly)


def box(extents, centre):
    mesh = trimesh.creation.box(extents=extents)
    mesh.apply_translation(centre)
    return mesh


def cyl_y(diameter, length, x, y, z, sections=32):
    mesh = trimesh.creation.cylinder(radius=diameter / 2, height=length, sections=sections)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    mesh.apply_translation([x, y, z])
    return mesh


def cup_to_world(mesh, axial_shift=0.0):
    """Cup local Z becomes -world Y; cup flange touches U-bottom at Y=0."""
    result = mesh.copy()
    transform = np.array([
        [1, 0, 0, 0],
        [0, 0, -1, axial_shift],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ], dtype=float)
    result.apply_transform(transform)
    return result


def equal_view(ax, bounds, elev=24, azim=-54):
    bounds = np.asarray(bounds, dtype=float)
    centre = bounds.mean(axis=0)
    span = max(bounds[1] - bounds[0]) * 0.56
    ax.set_xlim(centre[0] - span, centre[0] + span)
    ax.set_ylim(centre[1] - span, centre[1] + span)
    ax.set_zlim(centre[2] - span * 0.65, centre[2] + span * 0.65)
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 1, 0.75))
    ax.set_axis_off()


cup = trimesh.load_mesh(ROOT / "j3_tube_to_u_cup_v1_FINAL_PETG.stl")
spacer = trimesh.load_mesh(ROOT / "j3_cup_internal_spacer_v1_PETG.stl")
plate = trimesh.load_mesh(ROOT / "PLATE_J3_ADDON_NO_SENSORS_FINAL.stl")

fig = plt.figure(figsize=(18, 11), facecolor="#f3f5f7")
grid = fig.add_gridspec(2, 3, width_ratios=[1.05, 1.1, 0.95], hspace=0.12, wspace=0.05)

# Actual cup, print orientation.
ax = fig.add_subplot(grid[0, 0], projection="3d")
draw_mesh(ax, cup, "#e58d2c")
equal_view(ax, cup.bounds, elev=28, azim=-48)
ax.set_title("1. Новый стакан — реальная STL\n78 × 78 × 43 мм", fontsize=13, weight="bold")

# Flange view: eight bolts around the centre route.
ax = fig.add_subplot(grid[1, 0], projection="3d")
draw_mesh(ax, cup, "#e58d2c")
equal_view(ax, cup.bounds, elev=86, azim=-90)
ax.set_title("2. Фланец: 8 × M4 + центральный Ø14\nсетку отверстий скобы не меняем", fontsize=13, weight="bold")

# Assembled tube-cup-U bracket.
ax = fig.add_subplot(grid[:, 1], projection="3d")
cup_w = cup_to_world(cup)
draw_mesh(ax, cup_w, "#f09a3b", alpha=0.78)

# Existing 20x20 tube enters 33.5 mm into the square sleeve.
tube_outer = box([20, 105, 20], [0, -61.5, 0])
tube_inner = box([17, 107, 17], [0, -61.5, 0])
tube = trimesh.boolean.difference([tube_outer, tube_inner])
draw_mesh(ax, tube, "#737b84", alpha=0.82, edges="#22282f")

# Real spacer sits in the tube; show it semi-transparently.
spacer_in = spacer.copy()
spacer_in.apply_translation([0, 0, 9.5])
spacer_in = cup_to_world(spacer_in)
draw_mesh(ax, spacer_in, "#44b4dc", alpha=0.58, edges="#15556d")

# Measured 48x43x2.5 bottom and 96x48x2.5 side walls of the U bracket.
draw_mesh(ax, box([48, 2.5, 43], [0, 1.25, 0]), "#aab2ba", alpha=0.92, edges="#3a424a")
draw_mesh(ax, box([48, 96, 2.5], [0, 48, -22.75]), "#b9c1c8", alpha=0.45, edges="#4a5158")
draw_mesh(ax, box([48, 96, 2.5], [0, 48, 22.75]), "#b9c1c8", alpha=0.45, edges="#4a5158")

holes = [(-16, -8), (-16, 8), (16, -8), (16, 8),
         (-8, -16), (8, -16), (-8, 16), (8, 16)]
for x, z in holes:
    draw_mesh(ax, cyl_y(4.0, 14, x, -1.0, z), "#e4bd40", edges="#654d0d")
for local_z in (19.0, 33.0):
    # Cup local X-axis cross bolts.  In world coordinates: X-axis at Y=-local_z.
    bolt = trimesh.creation.cylinder(radius=2.0, height=42, sections=32)
    bolt.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    bolt.apply_translation([0, -local_z, 0])
    draw_mesh(ax, bolt, "#dc554d", edges="#6d1515")

equal_view(ax, [[-58, -120, -45], [58, 105, 45]], elev=21, azim=-48)
ax.set_title(
    "3. Собранное соединение\n"
    "серый — труба/скоба · оранжевый — стакан\n"
    "жёлтые — 8 винтов в скобу\n"
    "красные — 2 винта в трубу",
    fontsize=11.5,
    weight="bold",
)

# Print plate, true mesh and true bed footprint.
ax = fig.add_subplot(grid[0, 2], projection="3d")
draw_mesh(ax, plate, "#d98729")
equal_view(ax, plate.bounds, elev=70, azim=-90)
ax.set_title("4. Один файл на печать\n182 × 109 × 43 мм", fontsize=13, weight="bold")

# Compact print/assembly callouts.
ax = fig.add_subplot(grid[1, 2])
ax.axis("off")
text = (
    "ЧТО ЕСТЬ В ОБЩЕЙ STL\n\n"
    "1 × новый стакан J2→J3\n"
    "1 × полый внутренний вкладыш\n"
    "1 × адаптер редуктора v2\n"
    "1 × мост V7 (финальный шаг муфты)\n"
    "1 × кассета гаек v4\n"
    "2 × втулки для стакана roll\n\n"
    "НЕ ДОБАВЛЕНО\n"
    "• стакан roll — уже напечатан\n"
    "• AS5600, магнит и их крепления\n"
    "• старый кондуктор — используется повторно\n\n"
    "КЛЮЧЕВЫЕ РАЗМЕРЫ\n"
    "карман трубы 20,4 × 20,4 мм\n"
    "заход трубы 33,5 мм\n"
    "канал проводки 10,5 × 10,5 мм\n"
    "стакан→скоба: 8 × M4×16\n"
    "стакан→труба: 2 × M4×40"
)
ax.text(
    0.02, 0.98, text, va="top", fontsize=12.2, family="DejaVu Sans Mono",
    bbox=dict(boxstyle="round,pad=0.7", facecolor="white", edgecolor="#cbd1d6"),
)

fig.suptitle(
    "РОБОРУКА — НОВОЕ КРЕПЛЕНИЕ J2 → J3 БЕЗ ДАТЧИКОВ",
    fontsize=18,
    weight="bold",
    y=0.98,
)
fig.savefig(OUT, dpi=170, bbox_inches="tight")
plt.close(fig)
print("PASS", OUT)
