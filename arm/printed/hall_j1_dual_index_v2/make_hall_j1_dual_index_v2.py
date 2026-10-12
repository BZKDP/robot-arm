# -*- coding: utf-8 -*-
"""Dual-SS49E differential J1 index for CM36 + metal U-bracket coupling.

The fixed carrier bolts to the four unused M3 holes on the CM36 output face.
A tiny bushing places a D3x2 axially magnetised magnet in the existing 4.2 mm
hole at (11, 11) in the rotating U-bracket bottom.  Two fixed SS49E sensors
straddle the magnet track.  Home is the calibrated crossing of their analogue
signals, which is more repeatable than a single absolute threshold.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


ROOT = Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)

MOUNT_OUT = ROOT / "hall_j1_cm36_face_mount_DUAL_SS49E_PETG.stl"
RETAINER_OUT = ROOT / "hall_j1_DUAL_SS49E_retainer_frame_M3_PETG.stl"
MAGNET_OUT = ROOT / "hall_j1_magnet_bushing_D3x2_OD4p15_PETG.stl"
FIT_OUT = ROOT / "hall_j1_magnet_bushing_fit_set_OD4p00_4p15_4p30_PETG.stl"
HALL_FIT_OUT = ROOT / "hall_j1_SS49E_body_pocket_fit_test_3_sizes_PETG.stl"
PLATE_OUT = ROOT / "PLATE_HALL_J1_DUAL_INDEX_V2_PRINT_ALL.stl"
ASSEMBLY_OUT = ROOT / "HALL_J1_DUAL_INDEX_V2_ASSEMBLY_REVIEW_ONLY.stl"
REVIEW_OUT = ROOT / "HALL_J1_DUAL_INDEX_V2_REVIEW.png"
PARTS_OUT = ROOT / "HALL_J1_DUAL_INDEX_V2_PARTS_REVIEW.png"
HTML_OUT = ROOT / "HALL_J1_DUAL_INDEX_V2_INTERACTIVE_3D.html"
THREE_JS_PATH = ROOT / "three.r160.min.js"
GUIDE_OUT = ROOT / "HALL_J1_DUAL_INDEX_V2_PRINT_WIRING_AND_ASSEMBLY_RU.md"

# Real project dimensions, millimetres.
CM36_FACE_Z = 83.0
CM36_BOSS_D = 22.0
CM36_BOSS_H = 1.6
CM36_M3_BC = 27.5
SHAFT_D = 8.0
COUPLING_HUB_D = 14.1
COUPLING_FLANGE_D = 21.8
U_WEB_BOTTOM_Z = 97.0
U_WEB_T = 2.5

# Existing unused hole in the U bottom: (11, 11), diameter 4.2.
INDEX_X = 11.0
INDEX_Y = 11.0
U_INDEX_HOLE_D = 4.2

# Honeywell SS49E flat TO-92-style body is nominally 4.1 x 3.0 x 1.6 mm.
# These pockets include FDM and clone-package allowance.  The flat sensing
# faces point upward.  Local X is tangent to the magnet path; local Y is radial.
HALL_BODY_X = 4.60
HALL_BODY_Y = 3.50
HALL_BODY_DEPTH = 1.80           # 0.20 mm deeper than nominal 1.60 mm body
HALL_TOP_Z = 95.2                 # 1.8 mm below flush D3x2 magnet
HALL_SEPARATION = 5.40            # 0.8 mm printed divider between pockets
RETAINER_X = 19.0
RETAINER_Y = 7.4
RETAINER_T = 0.9
RETAINER_SCREW_OFFSET = 7.25

INDEX_R = float(np.hypot(INDEX_X, INDEX_Y))
RADIAL = np.array([INDEX_X, INDEX_Y], dtype=float) / INDEX_R
TANGENT = np.array([-RADIAL[1], RADIAL[0]])
LOCAL_ANGLE_DEG = -45.0           # local +Y points radially outwards


def boxc(sx, sy, sz, x=0.0, y=0.0, z=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_translation([x, y, z])
    return mesh


def box_rot_z(sx, sy, sz, x=0.0, y=0.0, z=0.0, angle_deg=0.0):
    """Centred box rotated about global Z after creation."""
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(angle_deg), [0, 0, 1]
    ))
    mesh.apply_translation([x, y, z])
    return mesh


def cyl_z(d, height, x=0.0, y=0.0, z=0.0, sections=64):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=height, sections=sections)
    mesh.apply_translation([x, y, z])
    return mesh


def clean(mesh):
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    trimesh.repair.fix_normals(mesh)
    return mesh


def ground(mesh):
    result = mesh.copy()
    result.apply_translation([0, 0, -result.bounds[0][2]])
    return result


# ---------------------------------------------------------------------------
# Fixed Hall carrier.  It prints flat on the CM36 face ring.
# ---------------------------------------------------------------------------
base_bottom = CM36_FACE_Z
base_t = 2.6
outer = cyl_z(46.0, base_t, z=base_bottom + base_t / 2, sections=128)
# The clearance continues through the full tower height.  This deliberately
# notches its inner corner and guarantees that the rotating O21.8 flange never
# touches the fixed printed carrier, even near the Hall pocket.
inner = cyl_z(22.8, 16.0, z=90.0, sections=128)

# Wide diagonal tower carries two flat SS49E bodies.  A thin radial tail leads
# all six legs to the outside of the ring, clear of every rotating metal part.
tower_bottom = base_bottom + base_t - 0.15
tower_top = HALL_TOP_Z
tower = box_rot_z(RETAINER_X, 7.4, tower_top - tower_bottom,
                  INDEX_X, INDEX_Y, (tower_bottom + tower_top) / 2,
                  LOCAL_ANGLE_DEG)
tail_center = np.array([INDEX_X, INDEX_Y]) + RADIAL * 4.9
tail = box_rot_z(11.8, 7.2, 2.8,
                 tail_center[0], tail_center[1], HALL_TOP_Z - 1.4,
                 LOCAL_ANGLE_DEG)

# Two triangular-ish support webs are represented as hulls between low and
# high boxes.  They stiffen the 10 mm tower without entering the coupling.
web_x = trimesh.convex.convex_hull(trimesh.util.concatenate([
    boxc(2.2, 7.0, 1.0, 7.0, INDEX_Y, base_bottom + base_t),
    boxc(2.2, 7.0, 1.0, 9.6, INDEX_Y, HALL_TOP_Z - 2.5),
]))
web_y = trimesh.convex.convex_hull(trimesh.util.concatenate([
    boxc(7.0, 2.2, 1.0, INDEX_X, 7.0, base_bottom + base_t),
    boxc(7.0, 2.2, 1.0, INDEX_X, 9.6, HALL_TOP_Z - 2.5),
]))

carrier_raw = trimesh.boolean.union([outer, tower, tail, web_x, web_y])
cuts = [inner]

# Four through holes match the CM36 output-face M3 pattern.
for angle in (0, 90, 180, 270):
    a = np.deg2rad(angle)
    x = (CM36_M3_BC / 2) * np.cos(a)
    y = (CM36_M3_BC / 2) * np.sin(a)
    cuts.append(cyl_z(3.55, base_t + 1.4, x, y, base_bottom + base_t / 2, sections=48))

# Two pockets, one on each side of the desired home centre.  A single D3x2
# magnet passes midway between them.  Six individual lead grooves prevent
# accidental shorts; at the outer service bay VCC and GND can be joined into a
# single four-core cable (3V3, GND, OUT_A, OUT_B).
sensor_centres = []
for side in (-1.0, 1.0):
    centre = np.array([INDEX_X, INDEX_Y]) + TANGENT * side * HALL_SEPARATION / 2
    sensor_centres.append(centre)
    cuts.append(box_rot_z(
        HALL_BODY_X, HALL_BODY_Y, HALL_BODY_DEPTH + 0.5,
        centre[0], centre[1], HALL_TOP_Z - HALL_BODY_DEPTH / 2 + 0.2,
        LOCAL_ANGLE_DEG,
    ))
    for pin_offset in (-1.27, 0.0, 1.27):
        groove_centre = centre + TANGENT * pin_offset + RADIAL * 4.45
        cuts.append(box_rot_z(
            0.78, 6.1, 1.75,
            groove_centre[0], groove_centre[1], HALL_TOP_Z - 0.70,
            LOCAL_ANGLE_DEG,
        ))

# Recessed solder/service bay at the outer end of the six grooves.  The two
# narrow through-slots accept a 2.5 mm cable tie for strain relief.
bay_centre = np.array([INDEX_X, INDEX_Y]) + RADIAL * 6.35
cuts.append(box_rot_z(10.8, 2.4, 1.70,
                     bay_centre[0], bay_centre[1], HALL_TOP_Z - 0.68,
                     LOCAL_ANGLE_DEG))
for side in (-1.0, 1.0):
    tie_centre = bay_centre + TANGENT * side * 5.0
    cuts.append(box_rot_z(1.7, 3.2, 4.0,
                         tie_centre[0], tie_centre[1], HALL_TOP_Z - 1.0,
                         LOCAL_ANGLE_DEG))

# Two vertical pilot holes let the separate frame clamp both sensor bodies.
# M3x6 screws self-form their thread in PETG; no nut is trapped under the ring.
retainer_screw_centres = []
for side in (-1.0, 1.0):
    screw_centre = np.array([INDEX_X, INDEX_Y]) + TANGENT * side * RETAINER_SCREW_OFFSET
    retainer_screw_centres.append(screw_centre)
    cuts.append(cyl_z(2.60, 7.0, screw_centre[0], screw_centre[1],
                      HALL_TOP_Z - 2.5, sections=48))

carrier = clean(trimesh.boolean.difference([carrier_raw] + cuts))
# Boolean contact at the notched inner corner may leave a zero-volume sliver;
# retain only the real connected carrier body before exporting.
carrier = clean(max(carrier.split(only_watertight=False), key=lambda m: abs(m.volume)))
carrier_print = ground(carrier)
carrier_print.export(MOUNT_OUT)

# Separate low-profile retaining frame.  Two closed windows leave the active
# faces visible to the magnet.  The six legs already lie below the top plane in
# the carrier grooves, so the solid outer rail protects rather than crushes them.
retainer_raw = box_rot_z(RETAINER_X, RETAINER_Y, RETAINER_T,
                        INDEX_X, INDEX_Y, HALL_TOP_Z + RETAINER_T / 2,
                        LOCAL_ANGLE_DEG)
retainer_cuts = []
for centre in sensor_centres:
    retainer_cuts.append(box_rot_z(
        3.20, 2.25, RETAINER_T + 1.2,
        centre[0], centre[1], HALL_TOP_Z + RETAINER_T / 2,
        LOCAL_ANGLE_DEG,
    ))
for centre in retainer_screw_centres:
    retainer_cuts.append(cyl_z(3.45, RETAINER_T + 1.2,
                               centre[0], centre[1],
                               HALL_TOP_Z + RETAINER_T / 2, sections=48))
retainer = clean(trimesh.boolean.difference([retainer_raw] + retainer_cuts))
retainer = clean(max(retainer.split(only_watertight=False), key=lambda m: abs(m.volume)))
retainer_print = ground(retainer)
retainer_print.export(RETAINER_OUT)

# Quick body-pocket test for inexpensive SS49E clones.  Datasheet nominal is
# 4.1 x 3.0 x 1.6 mm, but mould flash and printer flow vary.  The middle pocket
# matches the production carrier; the other two bracket it by +/-0.20 mm.
hall_fit_items = []
for i, (px, py) in enumerate(((4.40, 3.30), (4.60, 3.50), (4.80, 3.70))):
    base = boxc(8.6, 7.4, 3.0, x=i * 11.0, z=1.5)
    pocket = boxc(px, py, 2.15, x=i * 11.0, z=2.45)
    lead_exit = boxc(3.4, 3.8, 2.15, x=i * 11.0, y=3.2, z=2.45)
    hall_fit_items.append(clean(trimesh.boolean.difference([base, pocket, lead_exit])))
hall_fit_set = trimesh.util.concatenate(hall_fit_items)
hall_fit_set.apply_translation([-11.0, 0, 0])
hall_fit_set.export(HALL_FIT_OUT)


# ---------------------------------------------------------------------------
# Rotating magnet bushing.  Installed from inside/top of the U bottom.
# The D3x2 magnet is glued from below and finishes flush with the underside.
# ---------------------------------------------------------------------------
def magnet_bushing(outer_d=4.15):
    flange = cyl_z(6.6, 1.0, z=U_WEB_BOTTOM_Z + U_WEB_T + 0.5, sections=64)
    stem = cyl_z(outer_d, U_WEB_T, z=U_WEB_BOTTOM_Z + U_WEB_T / 2, sections=64)
    body = trimesh.boolean.union([flange, stem])
    pocket = cyl_z(3.22, 2.15, z=U_WEB_BOTTOM_Z + 1.075, sections=64)
    return clean(trimesh.boolean.difference([body, pocket]))


magnet_bushing_installed = magnet_bushing(4.15)
magnet_print = magnet_bushing_installed.copy()
magnet_print.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
magnet_print = ground(magnet_print)
magnet_print.export(MAGNET_OUT)

# Three tiny fit choices on one strip: 4.00 / 4.15 / 4.30 mm stem OD.
fit_items = []
for i, od in enumerate((4.00, 4.15, 4.30)):
    item = magnet_bushing(od)
    item.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    item = ground(item)
    item.apply_translation([i * 10.0, 0, 0])
    fit_items.append(item)
fit_set = trimesh.util.concatenate(fit_items)
fit_set.apply_translation([-10.0, 0, 0])
fit_set.export(FIT_OUT)

# Compact combined print plate: carrier, three bushing variants and the three
# SS49E body fit pockets.
plate_carrier = carrier_print.copy()
plate_carrier.apply_translation([0, 0, 0])
plate_fit = fit_set.copy()
plate_fit.apply_translation([0, 32, 0])
plate_hall_fit = hall_fit_set.copy()
plate_hall_fit.apply_translation([0, -31, 0])
plate_retainer = retainer_print.copy()
plate_retainer.apply_translation([0, -44, 0])
plate = trimesh.util.concatenate([plate_carrier, plate_fit, plate_hall_fit, plate_retainer])
plate.apply_translation([
    -(plate.bounds[0][0] + plate.bounds[1][0]) / 2,
    -(plate.bounds[0][1] + plate.bounds[1][1]) / 2,
    -plate.bounds[0][2],
])
plate.export(PLATE_OUT)


# ---------------------------------------------------------------------------
# Review assembly in the real vertical J1 orientation.
# ---------------------------------------------------------------------------
motor = boxc(42.3, 42.3, 48.0, z=24.0)
gearbox = cyl_z(36.0, 35.0, z=65.5, sections=96)
boss = cyl_z(CM36_BOSS_D, CM36_BOSS_H, z=CM36_FACE_Z + CM36_BOSS_H / 2, sections=96)
shaft = cyl_z(SHAFT_D, 16.0, z=CM36_FACE_Z + 8.0, sections=64)
hub = cyl_z(COUPLING_HUB_D, 10.0, z=90.0, sections=80)
flange = cyl_z(COUPLING_FLANGE_D, 2.0, z=96.0, sections=80)
u_web = boxc(48.0, 43.0, U_WEB_T, z=U_WEB_BOTTOM_Z + U_WEB_T / 2)
u_side_a = boxc(48.0, 2.5, 96.0, y=-22.75, z=U_WEB_BOTTOM_Z + U_WEB_T + 48.0)
u_side_b = boxc(48.0, 2.5, 96.0, y=22.75, z=U_WEB_BOTTOM_Z + U_WEB_T + 48.0)

magnet = cyl_z(3.0, 2.0, INDEX_X, INDEX_Y, U_WEB_BOTTOM_Z + 1.0, sections=64)
sensors = [
    box_rot_z(4.1, 3.0, 1.6, c[0], c[1], HALL_TOP_Z - 0.80,
              LOCAL_ANGLE_DEG)
    for c in sensor_centres
]

# Existing cage review mesh transformed from design X-axis to vertical Z-axis.
cage_path = ROOT.parent / "base_motor_vise_cage_v1" / "base_vise_cage_v1_ASSEMBLY_REVIEW_ONLY.stl"
cage = trimesh.load_mesh(cage_path)
cage.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
cage.apply_translation([0, 0, 24.0])

assembly = trimesh.util.concatenate([
    cage, motor, gearbox, boss, shaft, hub, flange, u_web, u_side_a, u_side_b,
    carrier, retainer, magnet_bushing_installed, magnet, *sensors,
])
assembly.export(ASSEMBLY_OUT)


# ---------------------------------------------------------------------------
# Review image: home position and rotated position explain the index action.
# ---------------------------------------------------------------------------
def rgba(value, alpha=1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def draw_mesh(ax, mesh, color, alpha=1.0, edge="#20252b", lw=0.05):
    ax.add_collection3d(Poly3DCollection(
        mesh.triangles,
        facecolor=rgba(color, alpha),
        edgecolor=rgba(edge, min(1.0, alpha + 0.1)),
        linewidth=lw,
    ))


def set_view(ax, bounds, elev=20, azim=-48):
    b = np.asarray(bounds, float)
    center = b.mean(axis=0)
    span = max(b[1] - b[0]) * 0.60
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(center[2] - span, center[2] + span)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def rotate_about_z(mesh, degrees):
    result = mesh.copy()
    result.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(degrees), [0, 0, 1]))
    return result


fig = plt.figure(figsize=(19, 11), facecolor="#f3f6f9")
gs = fig.add_gridspec(2, 3, width_ratios=[1.2, 1.2, 0.9], hspace=0.04, wspace=0.02)

fixed_parts = [
    (cage, "#e69a32", 0.22), (motor, "#282c30", 0.98),
    (gearbox, "#3158a4", 0.98), (boss, "#89939d", 1.0),
    (carrier, "#2ba86b", 0.98),
    (retainer, "#ff8a32", 0.98),
    (sensors[0], "#17271d", 1.0), (sensors[1], "#111820", 1.0),
]
rotating_parts = [
    (shaft, "#b8c0c7", 1.0), (hub, "#7e8790", 1.0),
    (flange, "#a4abb1", 1.0), (u_web, "#55a9da", 0.82),
    (u_side_a, "#55a9da", 0.36), (u_side_b, "#55a9da", 0.36),
    (magnet_bushing_installed, "#f4b942", 1.0), (magnet, "#d7333f", 1.0),
]

for col, angle, title in ((0, 0, "НУЛЬ: магнит между SS49E-A и SS49E-B"),
                          (1, 72, "ПОВОРОТ: магнит ушёл, оба SS49E неподвижны")):
    ax = fig.add_subplot(gs[:, col], projection="3d")
    for mesh, color, alpha in fixed_parts:
        draw_mesh(ax, mesh, color, alpha)
    for mesh, color, alpha in rotating_parts:
        draw_mesh(ax, rotate_about_z(mesh, angle), color, alpha)
    set_view(ax, [[-48, -48, -5], [48, 48, 205]], elev=18, azim=-50)
    ax.set_title(title, fontsize=12, weight="bold")

ax = fig.add_subplot(gs[0, 2], projection="3d")
for mesh, color, alpha in (
    (boss, "#89939d", 1.0), (shaft, "#b8c0c7", 1.0),
    (hub, "#7e8790", 1.0), (flange, "#a4abb1", 1.0),
    (carrier, "#2ba86b", 1.0),
    (retainer, "#ff8a32", 1.0),
    (sensors[0], "#17271d", 1.0), (sensors[1], "#111820", 1.0),
    (u_web, "#55a9da", 0.38), (magnet_bushing_installed, "#f4b942", 1.0),
    (magnet, "#d7333f", 1.0),
):
    draw_mesh(ax, mesh, color, alpha)
set_view(ax, [[-26, -26, 80], [26, 26, 104]], elev=18, azim=-45)
ax.set_title("КРУПНО: один магнит между двумя датчиками · зазор Z = 1,8 мм",
             fontsize=11, weight="bold")

ax = fig.add_subplot(gs[1, 2])
ax.axis("off")
notes = (
    "ЧТО ПЕЧАТАТЬ\n"
    "• 1× зелёный кронштейн DUAL SS49E\n"
    "• 1× оранжевая рамка + 2× M3×6\n"
    "• 1× жёлтая втулка магнита\n"
    "• сначала лучше комплект 4.00/4.15/4.30\n\n"
    "КУДА КРЕПИТЬ\n"
    "• кронштейн: неподвижный торец CM36\n"
    "• 4× M3 по окружности 27,5 мм\n"
    "• магнит: готовое Ø4,2 в дне U\n"
    "  координата (11;11), радиус 15,6 мм\n\n"
    "КАК РАБОТАЕТ\n"
    "• U и магнит вращаются вместе\n"
    "• два SS49E остаются на редукторе\n"
    "• ноль = калиброванное OUT_A − OUT_B = 0\n"
    "• между индексами угол считаем по STEP\n\n"
    "ВАЖНО\n"
    "Это индекс, не абсолютный энкодер.\n"
    "Оба корпуса положить плашмя, лицом\n"
    "к магниту и прижать рамкой на 2×M3."
)
ax.text(0.02, 0.98, notes, va="top", fontsize=10.2, family="DejaVu Sans Mono",
        bbox=dict(boxstyle="round,pad=.7", facecolor="white", edgecolor="#9ba9b5"))

fig.suptitle("J1 · ДИФФЕРЕНЦИАЛЬНЫЙ ИНДЕКС · 2× SS49E + 1 ВРАЩАЮЩИЙСЯ МАГНИТ",
             fontsize=16, weight="bold", y=.985)
fig.savefig(REVIEW_OUT, dpi=175, bbox_inches="tight")
plt.close(fig)

# Separate close-up so the printable geometry is easy to inspect on a phone.
fig = plt.figure(figsize=(18, 12), facecolor="#f3f6f9")
ax = fig.add_subplot(2, 2, 1, projection="3d")
draw_mesh(ax, carrier_print, "#2ba86b", 1.0)
set_view(ax, carrier_print.bounds, elev=28, azim=-48)
ax.set_title("НЕПОДВИЖНЫЙ КРОНШТЕЙН 2× SS49E\nкарманы, 6 пазов выводов, сервисный карман, стяжка",
             fontsize=12, weight="bold")

ax = fig.add_subplot(2, 2, 2, projection="3d")
draw_mesh(ax, retainer_print, "#ff8a32", 1.0)
set_view(ax, retainer_print.bounds, elev=30, azim=-45)
ax.set_title("ПРИЖИМНАЯ РАМКА ДВУХ ДАТЧИКОВ\n2 закрытых окна + 2 отверстия M3",
             fontsize=12, weight="bold")

ax = fig.add_subplot(2, 2, 3, projection="3d")
display_fit = fit_set.copy()
draw_mesh(ax, display_fit, "#f4b942", 1.0)
set_view(ax, display_fit.bounds, elev=26, azim=-45)
ax.set_title("ТРИ ПРОБНЫЕ ВТУЛКИ МАГНИТА D3×2\nстержень Ø4,00 / Ø4,15 / Ø4,30 мм", fontsize=12, weight="bold")

ax = fig.add_subplot(2, 2, 4, projection="3d")
draw_mesh(ax, hall_fit_set, "#7856b8", 1.0)
set_view(ax, hall_fit_set.bounds, elev=28, azim=-48)
ax.set_title("ТЕСТ КАРМАНА SS49E\n4,40×3,30 / 4,60×3,50 / 4,80×3,70 мм",
             fontsize=12, weight="bold")

fig.suptitle("J1 DUAL HALL INDEX V2 · ДЕТАЛИ, КОТОРЫЕ ПЕЧАТАЮТСЯ", fontsize=17, weight="bold", y=.98)
fig.text(.5, .035,
         "Сначала проверь посадку датчика и втулки. Кольцо печатается плоско без поддержек.",
         ha="center", fontsize=11,
         bbox=dict(boxstyle="round,pad=.55", facecolor="white", edgecolor="#9ba9b5"))
fig.savefig(PARTS_OUT, dpi=175, bbox_inches="tight")
plt.close(fig)


# ---------------------------------------------------------------------------
# Lightweight interactive explanation (concept geometry, exact dimensions in
# the info card).  The slider rotates only U + magnet.
# ---------------------------------------------------------------------------
html = r'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,"><title>J1 Dual Hall Index V2</title>
<style>
html,body{margin:0;height:100%;overflow:hidden;background:#0d1521;color:#eaf2fa;font-family:Arial,sans-serif}
#ui{position:absolute;z-index:3;left:18px;top:18px;width:340px;background:#111d2dcc;border:1px solid #31445c;border-radius:14px;padding:15px;backdrop-filter:blur(8px)}
h1{font-size:18px;margin:0 0 10px}.row{margin:10px 0}input{width:100%}.ok{color:#56d889}.warn{color:#ffc857}.small{font-size:13px;line-height:1.42;color:#c5d2df}b{color:white}
.toggle{display:flex;gap:8px;align-items:center;margin:8px 0}.toggle input{width:auto}.buttons{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.buttons button{border:1px solid #46617e;background:#203047;color:#eaf2fa;border-radius:7px;padding:7px 9px;cursor:pointer}.a{color:#ffdf45}.b{color:#e582ff}
#tag{padding:8px;border-radius:8px;background:#203047;margin-top:8px;text-align:center;font-weight:bold}
</style></head><body><div id="ui"><h1>J1 · Дифференциальный Hall-индекс</h1>
<div class="row"><label>Поворот U-скобы: <b id="deg">0°</b></label><input id="rot" type="range" min="-180" max="180" value="0"></div>
<div id="tag" class="ok">МАГНИТ МЕЖДУ A И B · НУЛЕВОЙ ИНДЕКС</div>
<div class="toggle"><input id="showU" type="checkbox" checked><label for="showU">Показывать прозрачную U-скобу</label></div>
<div class="toggle"><input id="showFrame" type="checkbox" checked><label for="showFrame">Показывать оранжевую прижимную рамку</label></div>
<div class="toggle"><input id="showSensors" type="checkbox" checked><label for="showSensors">Показывать оба датчика A и B</label></div>
<div class="buttons"><button id="detail">Вид карманов сверху</button><button id="explode">Разнести детали</button><button id="overall">Общий вид</button></div>
<div class="small"><p><b class="ok">Зелёное</b> — неподвижный кронштейн на торце CM36.<br><b style="color:#58b5e8">Голубое</b> — вращающаяся U-скоба.<br><b style="color:#ff4b55">Красное</b> — магнит D3×2.</p>
<p><b class="a">Жёлтый A</b> и <b class="b">фиолетовый B</b> — два отдельных SS49E. <b style="color:#ff8a32">Оранжевая рамка</b> прижимает оба корпуса двумя M3×6.</p><p><b>Сборка:</b> положить A и B маркировкой к магниту → ножки в шесть зелёных каналов → сверху рамка → равномерно затянуть 2×M3×6.</p></div></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script>
const scene=new THREE.Scene();scene.background=new THREE.Color(0x0d1521);
const camera=new THREE.PerspectiveCamera(38,innerWidth/innerHeight,.1,1000);camera.position.set(125,105,125);camera.lookAt(0,0,80);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(devicePixelRatio);document.body.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xe8f4ff,0x253347,2.1));const dl=new THREE.DirectionalLight(0xffffff,2.3);dl.position.set(80,-50,160);scene.add(dl);
const mat=(c,o=1)=>new THREE.MeshStandardMaterial({color:c,transparent:o<1,opacity:o,roughness:.58,metalness:.08,side:THREE.DoubleSide});
const addBox=(g,s,p,c,o=1)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(...s),mat(c,o));m.position.set(...p);g.add(m);return m};
const addBoxRot=(g,s,p,c,a,o=1)=>{const m=addBox(g,s,p,c,o);m.rotation.z=a*Math.PI/180;return m};
const addCyl=(g,d,h,p,c)=>{const m=new THREE.Mesh(new THREE.CylinderGeometry(d/2,d/2,h,64),mat(c));m.rotation.x=Math.PI/2;m.position.set(...p);g.add(m);return m};
const fixed=new THREE.Group(),rotating=new THREE.Group();scene.add(fixed,rotating);
addBox(fixed,[42.3,42.3,48],[0,0,24],0x262b31);addCyl(fixed,36,35,[0,0,65.5],0x3158a4);addCyl(fixed,22,1.6,[0,0,83.8],0x929aa1);
const carrierGeom=new THREE.BufferGeometry();carrierGeom.setAttribute('position',new THREE.Float32BufferAttribute([__CARRIER_VERTICES__],3));carrierGeom.setIndex([__CARRIER_INDICES__]);carrierGeom.computeVertexNormals();
const carrierMesh=new THREE.Mesh(carrierGeom,mat(0x2ba86b,.96));fixed.add(carrierMesh);const carrierEdges=new THREE.LineSegments(new THREE.EdgesGeometry(carrierGeom,28),new THREE.LineBasicMaterial({color:0x0c5f39}));fixed.add(carrierEdges);
const sensorVisual=new THREE.Group();fixed.add(sensorVisual);addBoxRot(sensorVisual,[4.1,3,1.6],[12.91,9.09,94.4],0xffdf45,-45);addBoxRot(sensorVisual,[4.1,3,1.6],[9.09,12.91,94.4],0xe582ff,-45);
const retainerGeom=new THREE.BufferGeometry();retainerGeom.setAttribute('position',new THREE.Float32BufferAttribute([__RETAINER_VERTICES__],3));retainerGeom.setIndex([__RETAINER_INDICES__]);retainerGeom.computeVertexNormals();const retainerMesh=new THREE.Mesh(retainerGeom,mat(0xff8a32,.96));fixed.add(retainerMesh);const retainerEdges=new THREE.LineSegments(new THREE.EdgesGeometry(retainerGeom,25),new THREE.LineBasicMaterial({color:0x7d2b00}));fixed.add(retainerEdges);
function label(txt,color,p){const c=document.createElement('canvas');c.width=128;c.height=64;const x=c.getContext('2d');x.fillStyle='rgba(13,21,33,.88)';x.fillRect(0,0,128,64);x.strokeStyle=color;x.lineWidth=4;x.strokeRect(3,3,122,58);x.fillStyle=color;x.font='bold 38px Arial';x.textAlign='center';x.textBaseline='middle';x.fillText(txt,64,34);const s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),depthTest:false}));s.position.set(...p);s.scale.set(9,4.5,1);s.renderOrder=20;sensorVisual.add(s)}
label('A','#ffdf45',[15.5,6.5,102]);label('B','#e582ff',[6.5,15.5,102]);
addCyl(rotating,8,16,[0,0,91],0xb8c0c7);addCyl(rotating,14.1,10,[0,0,90],0x7e8790);addCyl(rotating,21.8,2,[0,0,96],0xa4abb1);
addBox(rotating,[48,43,2.5],[0,0,98.25],0x58b5e8,.23);addBox(rotating,[48,2.5,96],[0,-22.75,147.5],0x58b5e8,.18);addBox(rotating,[48,2.5,96],[0,22.75,147.5],0x58b5e8,.18);
addCyl(rotating,6.6,1,[11,11,100],0xf4b942);addCyl(rotating,3,2,[11,11,98],0xd7333f);
const grid=new THREE.GridHelper(220,22,0x33465f,0x223146);scene.add(grid);
let down=false,px=0,py=0,yaw=.75,pitch=.62;renderer.domElement.onpointerdown=e=>{down=true;px=e.clientX;py=e.clientY};onpointerup=()=>down=false;onpointermove=e=>{if(!down)return;yaw+=(e.clientX-px)*.006;pitch=Math.max(.15,Math.min(1.35,pitch+(e.clientY-py)*.005));px=e.clientX;py=e.clientY};
function cam(){camera.position.set(145*Math.cos(yaw)*Math.cos(pitch),145*Math.sin(yaw)*Math.cos(pitch),70+145*Math.sin(pitch));camera.lookAt(0,0,82)}
const slider=document.getElementById('rot'),deg=document.getElementById('deg'),tag=document.getElementById('tag');slider.oninput=()=>{const a=+slider.value;rotating.rotation.z=a*Math.PI/180;deg.textContent=a+'°';const near=Math.abs(a)<7;tag.textContent=near?'МАГНИТ МЕЖДУ A И B · НУЛЕВОЙ ИНДЕКС':'МАГНИТ ВНЕ ПАРЫ ДАТЧИКОВ';tag.className=near?'ok':'warn'};
document.getElementById('showU').onchange=e=>rotating.visible=e.target.checked;document.getElementById('showFrame').onchange=e=>{retainerMesh.visible=e.target.checked;retainerEdges.visible=e.target.checked};document.getElementById('showSensors').onchange=e=>sensorVisual.visible=e.target.checked;document.getElementById('detail').onclick=()=>{yaw=.78;pitch=1.31;rotating.visible=false;document.getElementById('showU').checked=false};let exploded=false;document.getElementById('explode').onclick=e=>{exploded=!exploded;sensorVisual.position.z=exploded?7:0;retainerMesh.position.z=exploded?18:0;retainerEdges.position.z=exploded?18:0;rotating.visible=false;document.getElementById('showU').checked=false;if(exploded){yaw=.78;pitch=.58}e.target.textContent=exploded?'Собрать детали':'Разнести детали'};document.getElementById('overall').onclick=()=>{yaw=.75;pitch=.62;rotating.visible=true;document.getElementById('showU').checked=true};
onresize=()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)};(function loop(){cam();renderer.render(scene,camera);requestAnimationFrame(loop)})();
</script></body></html>'''

carrier_vertices_js = ",".join(f"{v:.4f}" for v in np.asarray(carrier.vertices).reshape(-1))
carrier_indices_js = ",".join(str(int(i)) for i in np.asarray(carrier.faces).reshape(-1))
retainer_vertices_js = ",".join(f"{v:.4f}" for v in np.asarray(retainer.vertices).reshape(-1))
retainer_indices_js = ",".join(str(int(i)) for i in np.asarray(retainer.faces).reshape(-1))
html = html.replace("__CARRIER_VERTICES__", carrier_vertices_js)
html = html.replace("__CARRIER_INDICES__", carrier_indices_js)
html = html.replace("__RETAINER_VERTICES__", retainer_vertices_js)
html = html.replace("__RETAINER_INDICES__", retainer_indices_js)

# Keep the interactive review fully self-contained.  A local file:// page in
# Edge may block storage/network access for CDN scripts, leaving the UI visible
# but the WebGL model blank.  Embedding the vendored Three.js build avoids any
# browser security exception and makes the file usable without internet.
three_js = THREE_JS_PATH.read_text(encoding="utf-8")
three_js = "\n".join(
    line for line in three_js.splitlines() if "sourceMappingURL=" not in line
)
offline_three_tag = (
    "<script>\n"
    "const __threeConsoleWarn = console.warn;"
    "console.warn = (...a) => { if (!String(a[0]).includes('Scripts \\\"build/three.js\\\"')) __threeConsoleWarn(...a); };\n"
    + three_js.replace("</script>", "<\\/script>")
    + "\nconsole.warn = __threeConsoleWarn;\n</script>"
)
html = html.replace(
    '<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>',
    offline_three_tag,
)
HTML_OUT.write_text(html, encoding="utf-8")


guide = """# J1 Dual Hall Index V2 — печать, проводка и сборка

Узел задаёт одну повторяемую точку механического нуля нижней оси J1. Один
вращающийся магнит проходит между двумя неподвижными линейными датчиками SS49E.
Ноль ищется не по одному жёсткому порогу, а по калиброванному пересечению двух
аналоговых сигналов. Это уменьшает влияние высоты магнита, температуры и его
реальной силы. Это всё ещё индекс, а не непрерывный абсолютный энкодер.

## Реальные размеры, под которые построена модель

- редуктор CM36: Ø36×35 мм, выступ торца Ø22×1,6 мм;
- четыре резьбы M3 по окружности Ø27,5 мм;
- металлическая муфта: хаб Ø14,1, фланец Ø21,8×2 мм;
- дно U-скобы 48×43×2,5 мм;
- готовое отверстие Ø4,2 в точке (11;11), радиус 15,56 мм;
- два голых SS49E: номинальный корпус 4,1×3,0×1,6 мм;
- один аксиально намагниченный неодимовый магнит D3×2 мм.

## Что печатать сначала

1. `hall_j1_SS49E_body_pocket_fit_test_3_sizes_PETG.stl` — три кармана
   4,40×3,30 / 4,60×3,50 / 4,80×3,70 мм. Производственный кронштейн использует
   средний. Датчик должен входить пальцами без изгиба корпуса.
2. `hall_j1_magnet_bushing_fit_set_OD4p00_4p15_4p30_PETG.stl` — выбрать втулку,
   которая плотно входит в настоящее отверстие Ø4,2 без молотка.
3. После примерок можно печатать общий
   `PLATE_HALL_J1_DUAL_INDEX_V2_PRINT_ALL.stl` или отдельные выбранные детали.
   В общей пластине теперь есть основной кронштейн, прижимная рамка, три теста
   втулки магнита и три теста кармана датчика.

## Настройки печати

- PETG, сопло 0,4 мм, слой 0,20 мм;
- 4 стенки, заполнение 35–45%;
- поддержки не нужны;
- шов лучше отвернуть от карманов датчиков;
- для втулок минимальное время слоя 8–10 секунд.

## Что предусмотрено в кронштейне

- два раздельных верхних кармана под плоско уложенные SS49E;
- между карманами 0,8 мм пластика;
- отдельная оранжевая прижимная рамка толщиной 0,9 мм;
- два отверстия рамки Ø3,45 и два пилотных отверстия Ø2,60 в кронштейне под
  два винта M3×6, которые самонарезают резьбу в PETG;
- два закрытых окна рамки над чувствительными поверхностями датчиков;
- наружная перемычка рамки закрывает и защищает утопленные каналы ножек;
- шесть раздельных пазов под три вывода каждого датчика;
- наружный углублённый сервисный карман для пайки ответвлений;
- две сквозные прорези под стяжку 2,5 мм для разгрузки кабеля;
- все провода выходят наружу по неподвижной части и не проходят под кольцом,
  поэтому их не зажимает торцом редуктора.

## Как собрать датчики и кабель

Оба датчика ставить одинаковой стороной: плоская маркированная поверхность
смотрит вверх, к магниту. Сначала положить A и B в два отдельных кармана и
развести все шесть ножек по своим пазам. Затем наложить оранжевую рамку так,
чтобы два окна оказались над корпусами, и равномерно притянуть двумя M3×6.
Затягивать только до исчезновения люфта: тонкая рамка должна прижать корпуса, а
не раздавить их. Клей для удержания датчиков не требуется.

Для оригинального SS49E, если держать маркировкой к себе и выводами вниз: левый
вывод VCC, средний GND, правый OUT. У дешёвого клона распиновку всё равно
подтвердить его описанием или короткой проверкой до пайки.

В сервисном кармане сделать один четырёхжильный кабель:

- красный: VCC обоих SS49E вместе;
- чёрный: GND обоих SS49E вместе;
- жёлтый: OUT датчика A отдельно;
- белый: OUT датчика B отдельно.

Каждое соединение изолировать тонкой термоусадкой. После проверки уложить пайку
в карман, закрепить кабель маленькой стяжкой и только затем добавить немного
нейтрального силикона только в наружном сервисном кармане. Сами корпуса под
прижимной рамкой не заливать.

## Куда подключать в панели

Кабель входит через уже предусмотренный правый ввод `AUX` и подключается только
к ESP32 №2, которая занимается датчиками:

- красный → шина `F2 / 3V3-SENS` (3,3 В датчиковой ESP32);
- чёрный → шина `F3 / GND-SENS`;
- жёлтый OUT_A → `GPIO34` ESP32 №2;
- белый OUT_B → `GPIO35` ESP32 №2.

GPIO34 и GPIO35 — входы ADC1. Они не конфликтуют с TCA9548A: мультиплексор и
пять AS5600 остаются на GPIO21=SDA и GPIO22=SCL. Через TCA9548A SS49E не идут.
Питать их от 5 В нельзя: используем 3,3 В, чтобы аналоговый выход гарантированно
оставался в диапазоне входа ESP32. Земля датчиков и всей системы общая, но 3V3
двух разных ESP32 между собой не соединять.

### Как уложиться в три уже купленных F15

F15 имеет один вход и пять выходов. Если подключены все пять AS5600, свободного
выхода для TCA9548A и Hall-кабеля не остаётся. Два провода в один пружинный зажим
не заталкивать. Для текущей панели сделать два коротких изолированных жгута:

- выход №5 `F2 / 3V3-SENS` → один красный провод 0,5 мм² → под общей термоусадкой
  три ветви: VCC AS5600 №5, VIN TCA9548A и красный Hall J1;
- выход №5 `F3 / GND-SENS` → один чёрный провод 0,5 мм² → три ветви: GND AS5600
  №5, GND TCA9548A и чёрный Hall J1.

Токи здесь малы; смысл утолщённого короткого входного провода — механическая
прочность. Место каждой пайки закрыть отдельно, затем общей термоусадкой и
закрепить стяжкой в нижней части панели. Это оставляет на ESP32 по одному проводу
3V3 и GND. Если позже понадобится полностью разъёмный монтаж без двух спаек,
понадобятся ещё два распределителя 1→5 и новая раскладка панели.

## Механическая сборка

1. Снять муфту/U-скобу с выходного вала.
2. Установить кольцевой кронштейн на неподвижный торец CM36 вокруг Ø22.
3. Закрепить двумя или четырьмя M3, начиная с M3×6; вручную убедиться, что винт
   не упирается в дно резьбы редуктора.
4. Уложить два SS49E лицом вверх, вывести шесть ножек по своим пазам, поставить
   прижимную рамку и равномерно закрепить её двумя M3×6. После этого собрать
   четырёхжильный кабель по схеме выше.
5. Вернуть муфту и U-скобу. Вставить выбранную втулку в отверстие (11;11)
   изнутри U-скобы; карман магнита смотрит вниз.
6. Вклеить один D3×2 заподлицо небольшим количеством эпоксидки.
7. До подачи питания рукой медленно провернуть J1 и проверить отсутствие касания.
   Расчётный вертикальный зазор магнит–корпус датчиков 1,8 мм.

## Как прошивка должна искать ноль

Вдали от магнита запомнить фоновые уровни A0 и B0. При медленном подходе всегда
с одной стороны вычислять `DA=A-A0`, `DB=B-B0`, `D=DA-DB`. Пересечение D через
калиброванный ноль считать индексом только тогда, когда
`abs(DA)+abs(DB)` уже достаточно велико. Эта проверка обязательна: вдали от
магнита A и B тоже почти равны. Добавить усреднение, гистерезис и подтверждение
несколькими последовательными измерениями. После нахождения индекса установить
счётчик J1 в известный ноль; между индексами положение считается по STEP.
"""
GUIDE_OUT.write_text(guide, encoding="utf-8")


def report(name, mesh):
    print(name,
          "watertight=", mesh.is_watertight,
          "components=", len(mesh.split(only_watertight=False)),
          "extents=", np.round(mesh.extents, 2),
          "volume=", round(float(mesh.volume), 1))


for name, mesh in (
    ("CARRIER", carrier_print), ("SENSOR RETAINER", retainer_print),
    ("MAGNET BUSHING", magnet_print),
    ("MAGNET FIT SET", fit_set), ("HALL BODY FIT SET", hall_fit_set),
    ("PRINT PLATE", plate),
):
    report(name, mesh)

print("CALCULATED SENSOR-MAGNET GAP", round(U_WEB_BOTTOM_Z - HALL_TOP_Z, 2), "mm")
print("SENSOR CENTRE SEPARATION", HALL_SEPARATION, "mm")
print("INDEX RADIUS", round(INDEX_R, 2), "mm")
print("OUTPUT", ROOT)
