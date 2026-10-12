# -*- coding: utf-8 -*-
"""Final serviceable electronics carrier for one ESP32 and five LERDGE TMC2209.

The printable concept has two parts:
  * a removable upper carrier with through-slots for all module pins;
  * a lower 21 mm wiring bay for solder joints, power buses and cable routing.

The two printable STL files are sized for the Creality Ender-3 V3 SE bed.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import FancyBboxPatch, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely.geometry import box as shapely_box


ROOT = Path(__file__).resolve().parent
TOP_OUT = ROOT / "electronics_carrier_FINAL_TOP_Ender3V3SE.stl"
TRAY_OUT = ROOT / "electronics_carrier_FINAL_TRAY_Ender3V3SE.stl"
ASSEMBLY_OUT = ROOT / "electronics_carrier_FINAL_ASSEMBLY_REVIEW_ONLY.stl"
REVIEW_OUT = ROOT / "ELECTRONICS_CARRIER_FINAL_3D_REVIEW.png"

# Overall printable envelope: both parts fit individually on a 220 x 220 bed.
OUTER_X = 200.0
OUTER_Y = 140.0
CORNER_R = 7.0
TOP_T = 3.2
TRAY_H = 24.0
TRAY_FLOOR = 3.0
TRAY_WALL = 3.0

# User/project hardware.
ESP_X = -64.0
ESP_Y = -40.0
ESP_BOARD_X = 28.5       # generous nominal envelope for 30-pin DevKit clones
ESP_BOARD_Y = 51.5
ESP_ROW_SPACING = 25.4
ESP_SLOT_X = 3.8
ESP_SLOT_Y = 40.0

DRIVER_X = (-56.0, -28.0, 0.0, 28.0, 56.0)
DRIVER_Y = 0.0
DRIVER_BOARD_X = 15.5    # official LERDGE dimension
DRIVER_BOARD_Y = 20.5    # official LERDGE dimension
DRIVER_ROW_SPACING = 12.7
DRIVER_SLOT_X = 4.2
DRIVER_SLOT_Y = 19.6
DRIVER_TOTAL_Z = 13.0    # user's measurement with heatsink

# Two CH-22/12P-1/1 terminal strips bought by the user.  Dimensions come from
# the supplied product drawing.  Each of the 12 channels is isolated from the
# next channel; the common +12 V / GND buses therefore live in the lower bay.
TERMINAL_X = (-42.0, 42.0)
TERMINAL_Y = 38.0
TERMINAL_L = 75.6
TERMINAL_W = 41.6
TERMINAL_H = 15.0
TERMINAL_HOLE_SPACING = 70.0
TERMINAL_HOLE_D = 3.4

POWER_X, POWER_Y = -86.0, 0.0
CAP_X, CAP_Y = 84.0, 0.0
SENSOR_X, SENSOR_Y = 42.0, -40.0
SENSOR_W, SENSOR_H = 76.0, 43.0

SCREWS = ((-92, -62), (0, -62), (92, -62), (-92, 62), (0, 62), (92, 62))


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


# ---------------------------------------------------------------------------
# Removable top carrier
# ---------------------------------------------------------------------------
top_base = rounded_plate(OUTER_X, OUTER_Y, CORNER_R, TOP_T)
top_cuts = []

# Six M3 clearance holes attach the carrier to the tray posts.
for x, y in SCREWS:
    top_cuts.append(cyl(3.6, TOP_T + 2, -1, x, y))

# The opening is sized for the moulded body of a USB-C cable, not only the
# metal tongue of the socket.  It remains deliberately generous for clones.
top_cuts.append(boxc(22.0, 14.0, TOP_T + 2, ESP_X, -66.5, -1))

# ESP32 two 15-pin rows: pins and solder joints remain accessible below.
for x in (ESP_X - ESP_ROW_SPACING / 2, ESP_X + ESP_ROW_SPACING / 2):
    top_cuts.append(boxc(ESP_SLOT_X, ESP_SLOT_Y, TOP_T + 2, x, ESP_Y, -1))

# Five LERDGE modules, each with two 2x8 pin rows.
for cx in DRIVER_X:
    for x in (cx - DRIVER_ROW_SPACING / 2, cx + DRIVER_ROW_SPACING / 2):
        top_cuts.append(boxc(DRIVER_SLOT_X, DRIVER_SLOT_Y, TOP_T + 2, x, DRIVER_Y, -1))

# CH-22 mounting holes and two long wire-drop slots per strip.  The front and
# rear rows can both turn down into the protected lower wiring bay.
for cx in TERMINAL_X:
    for x in (cx - TERMINAL_HOLE_SPACING / 2, cx + TERMINAL_HOLE_SPACING / 2):
        top_cuts.append(cyl(3.6, TOP_T + 2, -1, x, TERMINAL_Y))
    top_cuts.append(boxc(62.0, 4.0, TOP_T + 2, cx, 13.7, -1))
    top_cuts.append(boxc(62.0, 4.0, TOP_T + 2, cx, 62.3, -1))

# Universal power-input wire drop.  The capacitor is deliberately moved into
# the lower bay and strapped horizontally, so its uncertain body diameter and
# lead pitch cannot spoil the printed fit.
top_cuts.append(boxc(12.0, 7.0, TOP_T + 2, POWER_X, POWER_Y - 9.0, -1))

# Future sensor interface: zip-tie/perf slots, deliberately not tied to one PCB.
for x in (SENSOR_X - 28, SENSOR_X - 9, SENSOR_X + 10, SENSOR_X + 29):
    top_cuts.append(boxc(3.4, 18.0, TOP_T + 2, x, SENSOR_Y, -1))
for y in (SENSOR_Y - 16, SENSOR_Y + 16):
    top_cuts.append(boxc(54.0, 3.4, TOP_T + 2, SENSOR_X + 1, y, -1))

# Cable-lacing slots around the controller and driver signal side.
for x, y in ((-89, -41), (-39, -41), (-70, -8), (-42, -8), (76, -9), (88, -9)):
    top_cuts.append(boxc(3.2, 10.0, TOP_T + 2, x, y, -1))

top = trimesh.boolean.difference([top_base] + top_cuts)

# Raised support pads leave underside components and solder joints clear.
features = [top]

# ESP32 supports: antenna end, plus two USB-end corner pads. Side blocks guide
# clones without requiring an exact outer PCB width.
features.extend([
    boxc(ESP_BOARD_X - 2.0, 2.2, 1.2, ESP_X, ESP_Y + ESP_BOARD_Y / 2 - 1.1, TOP_T - 0.02),
    boxc(4.0, 2.2, 1.2, ESP_X - 10.5, ESP_Y - ESP_BOARD_Y / 2 + 1.1, TOP_T - 0.02),
    boxc(4.0, 2.2, 1.2, ESP_X + 10.5, ESP_Y - ESP_BOARD_Y / 2 + 1.1, TOP_T - 0.02),
])
for sx in (-1, 1):
    for sy in (-1, 1):
        features.append(boxc(
            1.5, 5.0, 3.2,
            ESP_X + sx * (ESP_BOARD_X / 2 + 0.8),
            ESP_Y + sy * (ESP_BOARD_Y / 2 - 3.0),
            TOP_T - 0.02,
        ))

# Driver end supports and guide towers. Pads are only under the short ends, so
# both long pin rows remain completely open from below.
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
                DRIVER_Y + sy * (DRIVER_BOARD_Y / 2 - 2.0),
                TOP_T - 0.02,
            ))

# The CH-22 strips are fixed through their own Ø3.4 mounting ears with M3
# screws.  No hard snap pocket is used: the product drawing does not specify
# the ear outline tightly enough for a reliable press fit.

# Universal power-input corner guides.
for sx in (-1, 1):
    for sy in (-1, 1):
        features.append(boxc(1.5, 4.0, 2.5, POWER_X + sx * 13.2, POWER_Y + sy * 9.0, TOP_T - 0.02))

top = clean(trimesh.boolean.union(features))
top.export(TOP_OUT)


# ---------------------------------------------------------------------------
# Lower wiring tray
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

# Six posts support the removable carrier.
tray_parts = [tray_shell]
for x, y in SCREWS:
    tray_parts.append(cyl(8.0, TRAY_H - TRAY_FLOOR, TRAY_FLOOR - 0.02, x, y))
tray = trimesh.boolean.union(tray_parts)

tray_cuts = []
for x, y in SCREWS:
    tray_cuts.append(cyl(2.8, TRAY_H + 2, -1, x, y))

# Back-wall motor cable exits, one per driver.
for x in DRIVER_X:
    tray_cuts.append(boxc(12.0, 10.0, 12.0, x, OUTER_Y / 2 - 1.0, 14.0))
    # Paired floor slots accept a zip tie for strain relief.
    for dx in (-4.5, 4.5):
        tray_cuts.append(boxc(3.0, 8.0, TRAY_FLOOR + 2, x + dx, 57.0, -1.0))

# Front USB-C opening and two internal strain-relief slots.  The user can pass
# a complete cable plug through the top mouth and clamp the cable jacket.
tray_cuts.append(boxc(22.0, 10.0, 13.0, ESP_X, -OUTER_Y / 2 + 1.0, 13.0))
for dx in (-9.0, 9.0):
    tray_cuts.append(boxc(3.0, 9.0, TRAY_FLOOR + 2, ESP_X + dx, -57.0, -1.0))

# Left power-input opening: ample room for the red/black 12 V pair or a small
# two-core sleeved cable.  Two floor slots hold a cable tie on the outer jacket.
tray_cuts.append(boxc(10.0, 16.0, 12.0, -OUTER_X / 2 + 1.0, POWER_Y, 13.0))
for y in (-6.0, 6.0):
    tray_cuts.append(boxc(9.0, 3.0, TRAY_FLOOR + 2, -87.0, y, -1.0))

# Universal horizontal capacitor cradle in the lower bay.  Two floor slots
# accept a cable tie around 12-18 mm diameter, ~20-30 mm long capacitors.
for x in (CAP_X - 8.0, CAP_X + 8.0):
    tray_cuts.append(boxc(3.0, 20.0, TRAY_FLOOR + 2, x, CAP_Y, -1.0))

# Five future sensors plus one spare service/AUX exit in the right wall.
for y in (-55, -41, -27, -13, 1, 15):
    tray_cuts.append(boxc(10.0, 8.0, 10.0, OUTER_X / 2 - 1.0, y, 14.0))
    for dy in (-3.0, 3.0):
        tray_cuts.append(boxc(8.0, 2.2, TRAY_FLOOR + 2, 87.0, y + dy, -1.0))

# Bottom ventilation under each driver bay.
for x in DRIVER_X:
    tray_cuts.append(boxc(10.0, 20.0, TRAY_FLOOR + 2, x, DRIVER_Y, -1))

tray = clean(trimesh.boolean.difference([tray] + tray_cuts))
tray.export(TRAY_OUT)

# Two disconnected bodies in assembled position; useful only for review.
top_assembled = top.copy()
top_assembled.apply_translation([0, 0, TRAY_H])
assembly = trimesh.util.concatenate([tray, top_assembled])
assembly.export(ASSEMBLY_OUT)


# ---------------------------------------------------------------------------
# Accurate-enough visual component models, never exported as printable parts.
# ---------------------------------------------------------------------------
def esp32_visual(z0):
    parts = []
    board = boxc(ESP_BOARD_X, ESP_BOARD_Y, 1.6, ESP_X, ESP_Y, z0)
    parts.append((board, "#1767a8", 1.0))
    parts.append((boxc(18.0, 25.0, 2.8, ESP_X, ESP_Y + 8.0, z0 + 1.6), "#c4c8cb", 1.0))
    parts.append((boxc(10.0, 7.0, 3.4, ESP_X, ESP_Y - ESP_BOARD_Y / 2 - 1.4, z0 + 0.4), "#aeb4b9", 1.0))
    for x in (ESP_X - ESP_ROW_SPACING / 2, ESP_X + ESP_ROW_SPACING / 2):
        for yy in np.linspace(ESP_Y - 17.78, ESP_Y + 17.78, 15):
            parts.append((boxc(0.7, 0.7, 8.0, x, yy, z0 - 7.8), "#d7ad3c", 1.0))
    return parts


def driver_visual(cx, z0):
    parts = [(boxc(DRIVER_BOARD_X, DRIVER_BOARD_Y, 1.6, cx, DRIVER_Y, z0), "#252a2f", 1.0)]
    heatsink_h = DRIVER_TOTAL_Z - 1.6
    parts.append((boxc(10.5, 10.5, heatsink_h, cx, DRIVER_Y, z0 + 1.6), "#a7adb2", 1.0))
    for x in (cx - DRIVER_ROW_SPACING / 2, cx + DRIVER_ROW_SPACING / 2):
        for yy in np.linspace(DRIVER_Y - 8.89, DRIVER_Y + 8.89, 8):
            parts.append((boxc(0.7, 0.7, 8.0, x, yy, z0 - 7.8), "#d7ad3c", 1.0))
    return parts


def components(z_deck):
    support_z = z_deck + TOP_T + 1.2
    result = []
    result.extend(esp32_visual(support_z))
    for x in DRIVER_X:
        result.extend(driver_visual(x, support_z))
    for i, x in enumerate(TERMINAL_X):
        result.append((boxc(TERMINAL_L, TERMINAL_W, TERMINAL_H, x, TERMINAL_Y, z_deck + TOP_T), "#f2f3f0", 0.95))
        for yy in (TERMINAL_Y - 13.0, TERMINAL_Y + 13.0):
            for xx in np.linspace(x - 27.5, x + 27.5, 12):
                result.append((boxc(3.2, 11.0, 2.0, xx, yy, z_deck + TOP_T + TERMINAL_H), "#f2a12b", 1.0))
    result.append((boxc(25.0, 22.0, 12.0, POWER_X, POWER_Y, z_deck + TOP_T), "#30363c", 1.0))
    return result


def rgba(value, alpha=1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def draw_mesh(ax, mesh, color, alpha=1.0, edge="#24282c", lw=0.04):
    tris = mesh.triangles
    if len(tris) > 16000:
        tris = tris[::int(np.ceil(len(tris) / 16000))]
    ax.add_collection3d(Poly3DCollection(
        tris,
        facecolor=rgba(color, alpha),
        edgecolor=rgba(edge, min(1.0, alpha + 0.15)),
        linewidth=lw,
    ))


def set_view(ax, bounds, elev=28, azim=-52, zscale=0.48):
    bounds = np.asarray(bounds, float)
    center = bounds.mean(axis=0)
    span = max(bounds[1] - bounds[0]) * 0.55
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(center[2] - span * zscale, center[2] + span * zscale)
    ax.set_box_aspect((1, 1, zscale * 1.4))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


# Review sheet.
fig = plt.figure(figsize=(19, 12), facecolor="#f2f5f8")
gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1.25, 0.9], hspace=0.12, wspace=0.05)

ax = fig.add_subplot(gs[:, :2], projection="3d")
draw_mesh(ax, tray, "#9ca8b5", 0.82)
draw_mesh(ax, top_assembled, "#d7dee5", 0.90)
for mesh, color, alpha in components(TRAY_H):
    draw_mesh(ax, mesh, color, alpha)
set_view(ax, [[-110, -80, -2], [110, 80, 68]], elev=31, azim=-54, zscale=0.46)
ax.set_title(
    "СОБРАННЫЙ МАКЕТ · 200 × 140 × 42,2 мм · ПОД ENDER-3 V3 SE\n"
    "ESP32 30 pin · 5× LERDGE TMC2209 · 2× CH-22/12P-1/1 · зона датчиков",
    fontsize=14, weight="bold",
)

ax = fig.add_subplot(gs[0, 2])
ax.set_aspect("equal")
ax.set_xlim(-100, 100); ax.set_ylim(-70, 70); ax.axis("off")
ax.add_patch(FancyBboxPatch((-100, -70), 200, 140, boxstyle="round,pad=0,rounding_size=7", fc="#e7edf2", ec="#69798a", lw=2))
ax.add_patch(Rectangle((ESP_X - ESP_BOARD_X/2, ESP_Y - ESP_BOARD_Y/2), ESP_BOARD_X, ESP_BOARD_Y, fc="#1767a8", ec="#0b3559"))
ax.text(ESP_X, ESP_Y, "ESP32\n30 PIN", ha="center", va="center", color="white", weight="bold")
for i, x in enumerate(DRIVER_X, 1):
    ax.add_patch(Rectangle((x - DRIVER_BOARD_X/2, DRIVER_Y - DRIVER_BOARD_Y/2), DRIVER_BOARD_X, DRIVER_BOARD_Y, fc="#2b3035", ec="black"))
    ax.text(x, DRIVER_Y, f"J{i}", ha="center", va="center", color="white", weight="bold")
for i, x in enumerate(TERMINAL_X):
    ax.add_patch(Rectangle((x - TERMINAL_L/2, TERMINAL_Y - TERMINAL_W/2), TERMINAL_L, TERMINAL_W, fc="#f2f3f0", ec="#66717a"))
    ax.text(x, TERMINAL_Y, "+12 V · 6 ВЫХОДОВ" if i == 0 else "GND · 6 ВЫХОДОВ", ha="center", va="center", color="#202830", fontsize=7, weight="bold")
ax.add_patch(Rectangle((SENSOR_X-SENSOR_W/2, SENSOR_Y-SENSOR_H/2), SENSOR_W, SENSOR_H, fill=False, ec="#1c756b", lw=1.4, ls="--"))
ax.text(SENSOR_X, SENSOR_Y, "ПУСТОЕ МЕСТО\nПРОРЕЗИ ПОД СТЯЖКИ", ha="center", va="center", fontsize=8, weight="bold")
ax.text(ESP_X, -67, "USB-C ↓", ha="center", va="center", fontsize=9)
ax.set_title("ВИД СВЕРХУ И ФУНКЦИОНАЛЬНЫЕ ЗОНЫ", fontsize=12, weight="bold")

ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
notes = (
    "ТОЧНЫЕ ИСХОДНЫЕ РАЗМЕРЫ\n"
    "• LERDGE: 20,5 × 15,5 мм\n"
    "• драйвер с радиатором: 13 мм (замер)\n"
    "• ESP32: DevKit V1, 30 pin\n"
    "• CH-22: 75,6 × 41,6 × 15 мм; отверстия Ø3,4 / 70 мм\n"
    "• шаг всех штырей: 2,54 мм\n\n"
    "КАК ЭТО СОБИРАЕТСЯ\n"
    "• платы кладутся сверху\n"
    "• пины уходят в длинные прорези\n"
    "• вся пайка находится в нижнем отсеке 21 мм\n"
    "• верх снимается на шести M3\n"
    "• USB-C доступен через передний вырез 22 мм\n"
    "• у каждого мотора отдельный задний выход\n"
    "• 5 датчиков + один AUX выходят справа\n"
    "• у всех внешних кабелей есть пазы под стяжки\n\n"
    "ПИТАНИЕ\n"
    "Левая CH-22 = +12 V, правая CH-22 = GND.\n"
    "Каналы CH-22 изолированы друг от друга,\n"
    "поэтому общие шины закрыты в нижнем отсеке.\n"
    "На каждой колодке: 5 драйверов + один запас.\n"
    "Конденсатор 470 мкФ / 50 В лежит снизу\n"
    "и фиксируется стяжкой независимо от диаметра.\n\n"
    "ВАЖНО\n"
    "Печатать только два STL с FINAL_TOP и FINAL_TRAY.\n"
    "ASSEMBLY_REVIEW_ONLY предназначен только для просмотра."
)
ax.text(0.02, 0.98, notes, va="top", fontsize=10.5, family="DejaVu Sans Mono",
        bbox=dict(boxstyle="round,pad=.7", facecolor="white", edgecolor="#aab5c0"))

fig.suptitle("МОНТАЖНАЯ КАССЕТА РОБОРУКИ · ФИНАЛЬНАЯ КОМПОНОВКА", fontsize=19, weight="bold", y=.985)
fig.savefig(REVIEW_OUT, dpi=170, bbox_inches="tight")
plt.close(fig)


def report(name, mesh):
    print(name, "watertight=", mesh.is_watertight, "extents=", np.round(mesh.extents, 2),
          "components=", len(mesh.split(only_watertight=False)), "volume=", round(float(mesh.volume), 1))


report("TOP", top)
report("TRAY", tray)
report("ASSEMBLY", assembly)
print("LERDGE pocket basis:", DRIVER_BOARD_Y, "x", DRIVER_BOARD_X, "mm; rows", DRIVER_ROW_SPACING, "mm")
print("ESP32 nominal:", ESP_BOARD_Y, "x", ESP_BOARD_X, "mm; rows", ESP_ROW_SPACING, "mm")
print("OUTPUT", REVIEW_OUT)
