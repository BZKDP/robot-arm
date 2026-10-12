# -*- coding: utf-8 -*-
"""Electronics carrier V2 preview for the robot arm.

Hardware represented by this revision:
  * 2 ordinary 30-pin ESP32 DevKit boards;
  * 5 LERDGE TMC2209 stepper drivers;
  * 2 CH-22/12P-1/1 terminal strips;
  * 3 F15 (1-in / 5-out) power distribution blocks;
  * 1 CJMCU-9548 / TCA9548A multiplexer board;
  * 1 REXANT ASW-17D 12 V / 35 A illuminated rocker switch;
  * 5 separate four-core AS5600 sensor cables and one AUX cable.

The purchased parts have not yet been physically caliper-checked, therefore
all outputs deliberately contain PREVIEW in their names.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import FancyBboxPatch, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely.geometry import box as shapely_box


ROOT = Path(__file__).resolve().parent
TOP_OUT = ROOT / "electronics_carrier_V2_PREVIEW_TOP_Ender3V3SE.stl"
TRAY_OUT = ROOT / "electronics_carrier_V2_PREVIEW_TRAY_Ender3V3SE.stl"
ASSEMBLY_OUT = ROOT / "electronics_carrier_V2_PREVIEW_ASSEMBLY_REVIEW_ONLY.stl"
SWITCH_TEST_OUT = ROOT / "electronics_carrier_V2_SWITCH_FIT_TEST.stl"
REVIEW_OUT = ROOT / "ELECTRONICS_CARRIER_V2_PREVIEW_3D_REVIEW.png"

# Ender-3 V3 SE bed is 220 x 220 mm.  Each printable part is 200 x 160 mm.
OUTER_X = 200.0
OUTER_Y = 160.0
CORNER_R = 7.0
TOP_T = 3.0
TRAY_H = 40.0
TRAY_FLOOR = 3.0
TRAY_WALL = 3.0

# Two ordinary ESP32 DevKit V1 30-pin boards.  USB sockets face the front.
ESP_X = (-65.0, 65.0)
ESP_Y = -50.0
ESP_BOARD_X = 28.5
ESP_BOARD_Y = 51.5
ESP_ROW_SPACING = 25.4
ESP_SLOT_X = 3.8
ESP_SLOT_Y = 40.0

# Five LERDGE TMC2209 modules.
DRIVER_X = (-56.0, -28.0, 0.0, 28.0, 56.0)
DRIVER_Y = 8.0
DRIVER_BOARD_X = 15.5
DRIVER_BOARD_Y = 20.5
DRIVER_ROW_SPACING = 12.7
DRIVER_SLOT_X = 4.2
DRIVER_SLOT_Y = 19.6
DRIVER_TOTAL_Z = 13.0

# Two CH-22/12P-1/1 blocks from the supplied seller drawing.
TERMINAL_X = (-42.5, 42.5)
TERMINAL_Y = 48.8
TERMINAL_L = 75.6
TERMINAL_W = 41.6
TERMINAL_H = 15.0
TERMINAL_HOLE_SPACING = 70.0

# CJMCU-9548 / HW-617.  Sources agree on 31.5 x about 22 mm but disagree on
# mounting-hole diameter, therefore no mounting hole is relied upon.
TCA_X = 0.0
TCA_Y = -20.0
TCA_BOARD_X = 22.0
TCA_BOARD_Y = 31.5
TCA_ROW_SPACING = 17.78

# REXANT ASW-17D exact supplied drawing.  Printed clearance is added to the
# nominal 34.2 x 20.2 panel opening; the separate coupon tests three fits.
SWITCH_X = 0.0
SWITCH_Y = -56.0
SWITCH_CUT_X = 34.5
SWITCH_CUT_Y = 20.5
SWITCH_BEZEL_X = 38.5
SWITCH_BEZEL_Y = 22.5
SWITCH_BODY_X = 28.0
SWITCH_BODY_Y = 20.2
SWITCH_BELOW_PANEL = 33.0

# Three F15 1-in / 5-out splitters are held in universal lower-bay cradles.
# Their supplied image gives 39.8 x 29 x 14.5 mm.
F15_XY = ((-62.0, -8.0), (43.0, -8.0), (43.0, 28.0))
F15_BODY_X = 39.8
F15_BODY_Y = 29.0
F15_BODY_Z = 14.5

POWER_X, POWER_Y = -87.0, 43.0
CAP_X, CAP_Y = -82.0, -29.0

# Five AS5600 cables plus one four-core differential Hall J1 cable opening.
SENSOR_EXIT_Y = (-52.0, -32.0, -12.0, 8.0, 28.0)
AUX_EXIT_Y = 50.0

# Five screws avoid the large terminal blocks at the rear.
SCREWS = ((-91, -72), (0, -72), (91, -72), (-91, 72), (91, 72))


def boxc(sx, sy, sz, x=0.0, y=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_translation([x, y, z0 + sz / 2])
    return mesh


def cyl(d, h, z0, x=0.0, y=0.0, sections=48):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=h, sections=sections)
    mesh.apply_translation([x, y, z0 + h / 2])
    return mesh


def rounded_rect(width, depth, radius):
    return shapely_box(
        -width / 2 + radius,
        -depth / 2 + radius,
        width / 2 - radius,
        depth / 2 - radius,
    ).buffer(radius, join_style=1)


def rounded_plate(width, depth, radius, height, z0=0.0):
    mesh = trimesh.creation.extrude_polygon(rounded_rect(width, depth, radius), height)
    if z0:
        mesh.apply_translation([0, 0, z0])
    return mesh


def clean(mesh):
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    return mesh


def corner_cradle(cx, cy, body_x, body_y, z0, height=4.5, wall=1.6, arm=8.0, gap=0.8):
    """Four removable-part corner stops; the centre and cable sides stay open."""
    pieces = []
    hx = body_x / 2 + gap
    hy = body_y / 2 + gap
    for sx in (-1, 1):
        for sy in (-1, 1):
            pieces.append(boxc(wall, arm, height, cx + sx * hx, cy + sy * (hy - arm / 2), z0))
            pieces.append(boxc(arm, wall, height, cx + sx * (hx - arm / 2), cy + sy * hy, z0))
    return pieces


# ---------------------------------------------------------------------------
# Removable upper carrier
# ---------------------------------------------------------------------------
top_base = rounded_plate(OUTER_X, OUTER_Y, CORNER_R, TOP_T)
top_cuts = []

for x, y in SCREWS:
    top_cuts.append(cyl(3.6, TOP_T + 2, -1, x, y))

# Two complete ESP32 pin rows and generous USB plug mouths.
for cx in ESP_X:
    top_cuts.append(boxc(22.0, 13.0, TOP_T + 2, cx, -77.0, -1))
    for x in (cx - ESP_ROW_SPACING / 2, cx + ESP_ROW_SPACING / 2):
        top_cuts.append(boxc(ESP_SLOT_X, ESP_SLOT_Y, TOP_T + 2, x, ESP_Y, -1))

# Five driver pin-row openings.
for cx in DRIVER_X:
    for x in (cx - DRIVER_ROW_SPACING / 2, cx + DRIVER_ROW_SPACING / 2):
        top_cuts.append(boxc(DRIVER_SLOT_X, DRIVER_SLOT_Y, TOP_T + 2, x, DRIVER_Y, -1))

# Terminal-strip mounting and wire-drop slots.
for cx in TERMINAL_X:
    for x in (cx - TERMINAL_HOLE_SPACING / 2, cx + TERMINAL_HOLE_SPACING / 2):
        top_cuts.append(cyl(3.6, TOP_T + 2, -1, x, TERMINAL_Y))
    top_cuts.append(boxc(62.0, 4.0, TOP_T + 2, cx, TERMINAL_Y - 24.3, -1))
    top_cuts.append(boxc(62.0, 4.0, TOP_T + 2, cx, TERMINAL_Y + 24.3, -1))

# Exact bought rocker position.
top_cuts.append(boxc(SWITCH_CUT_X, SWITCH_CUT_Y, TOP_T + 2, SWITCH_X, SWITCH_Y, -1))

# TCA board: the two 2.54 mm header rows pass through; zip-tie slots remain
# available at both board ends.  This ignores the disputed M2/M3 holes.
for x in (TCA_X - TCA_ROW_SPACING / 2, TCA_X + TCA_ROW_SPACING / 2):
    top_cuts.append(boxc(3.5, 28.8, TOP_T + 2, x, TCA_Y, -1))
for y in (TCA_Y - 18.0, TCA_Y + 18.0):
    top_cuts.append(boxc(12.0, 3.2, TOP_T + 2, TCA_X, y, -1))

# Power feed into the protected lower bay and general lacing slots.
top_cuts.append(boxc(12.0, 7.0, TOP_T + 2, POWER_X, POWER_Y - 9.0, -1))
for x, y in ((-91, -50), (-39, -50), (39, -50), (91, -50), (-76, -18), (76, -18)):
    top_cuts.append(boxc(3.2, 10.0, TOP_T + 2, x, y, -1))

top = trimesh.boolean.difference([top_base] + top_cuts)
features = [top]

# ESP32 supports and side guides.
for cx in ESP_X:
    features.extend([
        boxc(ESP_BOARD_X - 2.0, 2.2, 1.2, cx, ESP_Y + ESP_BOARD_Y / 2 - 1.1, TOP_T - 0.02),
        boxc(4.0, 2.2, 1.2, cx - 10.5, ESP_Y - ESP_BOARD_Y / 2 + 1.1, TOP_T - 0.02),
        boxc(4.0, 2.2, 1.2, cx + 10.5, ESP_Y - ESP_BOARD_Y / 2 + 1.1, TOP_T - 0.02),
    ])
    for sx in (-1, 1):
        for sy in (-1, 1):
            features.append(boxc(
                1.5, 5.0, 3.2,
                cx + sx * (ESP_BOARD_X / 2 + 0.8),
                ESP_Y + sy * (ESP_BOARD_Y / 2 - 3.0), TOP_T - 0.02,
            ))

# Driver supports.
for cx in DRIVER_X:
    for sy in (-1, 1):
        features.append(boxc(
            DRIVER_BOARD_X - 1.0, 1.5, 1.2,
            cx, DRIVER_Y + sy * (DRIVER_BOARD_Y / 2 - 0.75), TOP_T - 0.02,
        ))
    for sx in (-1, 1):
        for sy in (-1, 1):
            features.append(boxc(
                1.2, 3.2, 3.0,
                cx + sx * (DRIVER_BOARD_X / 2 + 0.7),
                DRIVER_Y + sy * (DRIVER_BOARD_Y / 2 - 2.0), TOP_T - 0.02,
            ))

# TCA edge guides, intentionally not a tight snap pocket.
for sx in (-1, 1):
    features.append(boxc(1.4, 20.0, 2.6, TCA_X + sx * (TCA_BOARD_X / 2 + 0.7), TCA_Y, TOP_T - 0.02))
for sy in (-1, 1):
    features.append(boxc(8.0, 1.4, 2.6, TCA_X, TCA_Y + sy * (TCA_BOARD_Y / 2 + 0.7), TOP_T - 0.02))

top = clean(trimesh.boolean.union(features))
top.export(TOP_OUT)


# ---------------------------------------------------------------------------
# Lower protected wiring tray
# ---------------------------------------------------------------------------
tray_outer = rounded_plate(OUTER_X, OUTER_Y, CORNER_R, TRAY_H)
tray_inner = rounded_plate(
    OUTER_X - 2 * TRAY_WALL,
    OUTER_Y - 2 * TRAY_WALL,
    max(2.0, CORNER_R - TRAY_WALL),
    TRAY_H - TRAY_FLOOR + 2,
    TRAY_FLOOR,
)
tray_shell = trimesh.boolean.difference([tray_outer, tray_inner])

tray_parts = [tray_shell]
for x, y in SCREWS:
    tray_parts.append(cyl(8.0, TRAY_H - TRAY_FLOOR, TRAY_FLOOR - 0.02, x, y))

# Three labelled-in-document F15 cradles: 3V3-MOT, 3V3-SENS, GND-SENS.
for cx, cy in F15_XY:
    tray_parts.extend(corner_cradle(cx, cy, F15_BODY_X, F15_BODY_Y, TRAY_FLOOR - 0.02))

# Capacitor saddle rails; the cable tie provides the actual retention.
tray_parts.extend([
    boxc(2.0, 21.0, 4.0, CAP_X - 9.0, CAP_Y, TRAY_FLOOR - 0.02),
    boxc(2.0, 21.0, 4.0, CAP_X + 9.0, CAP_Y, TRAY_FLOOR - 0.02),
])

tray = trimesh.boolean.union(tray_parts)
tray_cuts = []

for x, y in SCREWS:
    tray_cuts.append(cyl(2.8, TRAY_H + 2, -1, x, y))

# Rear: five independent NEMA motor cables.
for x in DRIVER_X:
    tray_cuts.append(boxc(12.0, 10.0, 13.0, x, OUTER_Y / 2 - 1.0, 22.0))
    for dx in (-4.5, 4.5):
        tray_cuts.append(boxc(3.0, 8.0, TRAY_FLOOR + 2, x + dx, 65.0, -1.0))

# Front: two independent USB-C cables, so both ESP32s can be connected to PC.
for cx in ESP_X:
    tray_cuts.append(boxc(22.0, 10.0, 14.0, cx, -OUTER_Y / 2 + 1.0, 21.0))
    for dx in (-9.0, 9.0):
        tray_cuts.append(boxc(3.0, 9.0, TRAY_FLOOR + 2, cx + dx, -67.0, -1.0))

# Left wall: main 12 V input.
tray_cuts.append(boxc(12.0, 18.0, 14.0, -OUTER_X / 2 + 1.0, POWER_Y, 21.0))
for y in (POWER_Y - 7.0, POWER_Y + 7.0):
    tray_cuts.append(boxc(9.0, 3.0, TRAY_FLOOR + 2, -87.0, y, -1.0))

# Right wall: five separate four-core AS5600 leads, plus an AUX/service exit.
for y in SENSOR_EXIT_Y:
    tray_cuts.append(boxc(11.0, 9.0, 12.0, OUTER_X / 2 - 1.0, y, 22.0))
    for dy in (-3.5, 3.5):
        tray_cuts.append(boxc(8.0, 2.2, TRAY_FLOOR + 2, 87.0, y + dy, -1.0))
tray_cuts.append(boxc(11.0, 9.0, 12.0, OUTER_X / 2 - 1.0, AUX_EXIT_Y, 22.0))
for dy in (-3.5, 3.5):
    tray_cuts.append(boxc(8.0, 2.2, TRAY_FLOOR + 2, 87.0, AUX_EXIT_Y + dy, -1.0))

# F15 cable-tie slots.  They do not assume an undocumented screw-hole pitch.
for cx, cy in F15_XY:
    for x in (cx - 13.5, cx + 13.5):
        tray_cuts.append(boxc(3.0, 8.0, TRAY_FLOOR + 2, x, cy, -1.0))

# Capacitor tie slots.
for x in (CAP_X - 6.5, CAP_X + 6.5):
    tray_cuts.append(boxc(3.0, 20.0, TRAY_FLOOR + 2, x, CAP_Y, -1.0))

tray = clean(trimesh.boolean.difference([tray] + tray_cuts))
tray.export(TRAY_OUT)

top_assembled = top.copy()
top_assembled.apply_translation([0, 0, TRAY_H])
assembly = trimesh.util.concatenate([tray, top_assembled])
assembly.export(ASSEMBLY_OUT)


# Three real-world fit candidates for the snap-in rocker.  From left to right:
# nominal 34.2x20.2, +0.3 mm, +0.6 mm.  Plate thickness equals the final top.
coupon = boxc(128.0, 38.0, TOP_T, 0, 0, 0)
coupon_cuts = []
for cx, dx in zip((-42.0, 0.0, 42.0), (0.0, 0.3, 0.6)):
    coupon_cuts.append(boxc(34.2 + dx, 20.2 + dx, TOP_T + 2, cx, 0, -1))
coupon = clean(trimesh.boolean.difference([coupon] + coupon_cuts))
coupon.export(SWITCH_TEST_OUT)


# ---------------------------------------------------------------------------
# Review-only component models and overview PNG
# ---------------------------------------------------------------------------
def esp32_visual(cx, z0):
    parts = [(boxc(ESP_BOARD_X, ESP_BOARD_Y, 1.6, cx, ESP_Y, z0), "#1767a8", 1.0)]
    parts.append((boxc(18.0, 25.0, 2.8, cx, ESP_Y + 8.0, z0 + 1.6), "#c4c8cb", 1.0))
    parts.append((boxc(10.0, 7.0, 3.4, cx, ESP_Y - ESP_BOARD_Y / 2 - 1.4, z0 + 0.4), "#aeb4b9", 1.0))
    return parts


def driver_visual(cx, z0):
    parts = [(boxc(DRIVER_BOARD_X, DRIVER_BOARD_Y, 1.6, cx, DRIVER_Y, z0), "#252a2f", 1.0)]
    parts.append((boxc(10.5, 10.5, DRIVER_TOTAL_Z - 1.6, cx, DRIVER_Y, z0 + 1.6), "#a7adb2", 1.0))
    return parts


def components(z_deck):
    support_z = z_deck + TOP_T + 1.2
    result = []
    for x in ESP_X:
        result.extend(esp32_visual(x, support_z))
    for x in DRIVER_X:
        result.extend(driver_visual(x, support_z))
    for x in TERMINAL_X:
        result.append((boxc(TERMINAL_L, TERMINAL_W, TERMINAL_H, x, TERMINAL_Y, z_deck + TOP_T), "#f2f3f0", 0.96))
    result.append((boxc(TCA_BOARD_X, TCA_BOARD_Y, 1.6, TCA_X, TCA_Y, support_z), "#7036a3", 1.0))
    result.append((boxc(SWITCH_BEZEL_X, SWITCH_BEZEL_Y, 6.2, SWITCH_X, SWITCH_Y, z_deck + TOP_T), "#b8292e", 1.0))
    result.append((boxc(SWITCH_BODY_X, SWITCH_BODY_Y, SWITCH_BELOW_PANEL, SWITCH_X, SWITCH_Y,
                        z_deck + TOP_T - SWITCH_BELOW_PANEL), "#232527", 0.82))
    for (x, y), color in zip(F15_XY, ("#ee9b31", "#55a99e", "#4f5d69")):
        result.append((boxc(F15_BODY_X, F15_BODY_Y, F15_BODY_Z, x, y, TRAY_FLOOR), color, 0.88))
    return result


def rgba(value, alpha=1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def draw_mesh(ax, mesh, color, alpha=1.0, edge="#24282c", lw=0.035):
    tris = mesh.triangles
    if len(tris) > 18000:
        tris = tris[::int(np.ceil(len(tris) / 18000))]
    ax.add_collection3d(Poly3DCollection(
        tris, facecolor=rgba(color, alpha), edgecolor=rgba(edge, min(1.0, alpha + 0.15)), linewidth=lw,
    ))


def set_view(ax, bounds, elev=29, azim=-52, zscale=0.48):
    bounds = np.asarray(bounds, float)
    center = bounds.mean(axis=0)
    span = max(bounds[1] - bounds[0]) * 0.55
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(center[2] - span * zscale, center[2] + span * zscale)
    ax.set_box_aspect((1, 1, zscale * 1.45))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


fig = plt.figure(figsize=(20, 12), facecolor="#f2f5f8")
gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1.25, 0.92], hspace=0.12, wspace=0.05)

ax = fig.add_subplot(gs[:, :2], projection="3d")
draw_mesh(ax, tray, "#9ca8b5", 0.58)
draw_mesh(ax, top_assembled, "#d7dee5", 0.88)
for mesh, color, alpha in components(TRAY_H):
    draw_mesh(ax, mesh, color, alpha)
set_view(ax, [[-110, -90, -2], [110, 90, 74]])
ax.set_title(
    "V2 PREVIEW · 200 × 160 × 43 мм · 2× ESP32 · 5× TMC2209\n"
    "2× CH-22 · 3× F15 · TCA9548A · ASW-17D · 5× AS5600 CABLE",
    fontsize=13, weight="bold",
)

ax = fig.add_subplot(gs[0, 2])
ax.set_aspect("equal"); ax.set_xlim(-100, 100); ax.set_ylim(-80, 80); ax.axis("off")
ax.add_patch(FancyBboxPatch((-100, -80), 200, 160, boxstyle="round,pad=0,rounding_size=7",
                            fc="#e7edf2", ec="#69798a", lw=2))
for i, x in enumerate(ESP_X, 1):
    ax.add_patch(Rectangle((x - ESP_BOARD_X/2, ESP_Y - ESP_BOARD_Y/2), ESP_BOARD_X, ESP_BOARD_Y,
                           fc="#1767a8", ec="#0b3559"))
    ax.text(x, ESP_Y, f"ESP{i}\n" + ("MOTORS" if i == 1 else "SENSORS"), ha="center", va="center",
            color="white", fontsize=7, weight="bold")
for i, x in enumerate(DRIVER_X, 1):
    ax.add_patch(Rectangle((x - DRIVER_BOARD_X/2, DRIVER_Y - DRIVER_BOARD_Y/2), DRIVER_BOARD_X,
                           DRIVER_BOARD_Y, fc="#2b3035", ec="black"))
    ax.text(x, DRIVER_Y, f"J{i}", ha="center", va="center", color="white", fontsize=7, weight="bold")
for i, x in enumerate(TERMINAL_X):
    ax.add_patch(Rectangle((x - TERMINAL_L/2, TERMINAL_Y - TERMINAL_W/2), TERMINAL_L, TERMINAL_W,
                           fc="#f2f3f0", ec="#66717a"))
    ax.text(x, TERMINAL_Y, "+12 V" if i == 0 else "GND", ha="center", va="center", fontsize=8, weight="bold")
ax.add_patch(Rectangle((TCA_X-TCA_BOARD_X/2, TCA_Y-TCA_BOARD_Y/2), TCA_BOARD_X, TCA_BOARD_Y,
                       fc="#7036a3", ec="#34194c"))
ax.text(TCA_X, TCA_Y, "TCA\n9548", ha="center", va="center", color="white", fontsize=7, weight="bold")
ax.add_patch(Rectangle((SWITCH_X-SWITCH_BEZEL_X/2, SWITCH_Y-SWITCH_BEZEL_Y/2), SWITCH_BEZEL_X,
                       SWITCH_BEZEL_Y, fc="#b8292e", ec="#3d1113"))
ax.text(SWITCH_X, SWITCH_Y, "12V ON/OFF", ha="center", va="center", color="white", fontsize=7, weight="bold")
ax.text(97, -2, "S1\nS2\nS3\nS4\nS5\nHALL-J1", ha="center", va="center", fontsize=7, weight="bold")
ax.set_title("ВИД СВЕРХУ", fontsize=12, weight="bold")

ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
notes = (
    "ЧТО ИЗМЕНИЛОСЬ В V2\n"
    "• две обычные ESP32, два отдельных USB-C\n"
    "• TCA9548A между ESP датчиков и 5× AS5600\n"
    "• справа 5 отдельных вводов S1–S5 + HALL-J1\n"
    "• три внутренних F15:\n"
    "  1) 3V3-MOT → VIO пяти драйверов\n"
    "  2) 3V3-SENS → VCC пяти AS5600\n"
    "  3) GND-SENS → GND пяти AS5600\n"
    "• 3V3 двух ESP32 между собой НЕ соединять\n"
    "• общая GND системы обязательна\n"
    "• ASW-17D: окно 34,5 × 20,5 мм\n"
    "• короб 40 мм: клеммы выключателя помещаются\n\n"
    "РАЗМЕРЫ-ОСНОВАНИЯ\n"
    "• F15: 39,8 × 29 × 14,5 мм (фото продавца)\n"
    "• CJMCU-9548: 31,5 × 21,4–22 мм\n"
    "• ASW-17D: рамка 38,5 × 22,5 мм\n"
    "• CH-22: 75,6 × 41,6 × 15 мм\n\n"
    "PREVIEW: до прихода деталей не печатать весь корпус.\n"
    "Сначала проверить ESP32 и тест окна выключателя."
)
ax.text(0.02, 0.98, notes, va="top", fontsize=10.2, family="DejaVu Sans Mono",
        bbox=dict(boxstyle="round,pad=.7", facecolor="white", edgecolor="#aab5c0"))

fig.suptitle("МОНТАЖНАЯ КАССЕТА РОБОРУКИ · V2 PREVIEW", fontsize=19, weight="bold", y=.985)
fig.savefig(REVIEW_OUT, dpi=170, bbox_inches="tight")
plt.close(fig)


def report(name, mesh):
    print(name, "watertight=", mesh.is_watertight, "extents=", np.round(mesh.extents, 2),
          "components=", len(mesh.split(only_watertight=False)), "volume=", round(float(mesh.volume), 1))


report("TOP", top)
report("TRAY", tray)
report("ASSEMBLY", assembly)
report("SWITCH TEST", coupon)
print("INTERNAL CLEARANCE", TRAY_H - TRAY_FLOOR, "mm")
print("OUTPUT", REVIEW_OUT)
