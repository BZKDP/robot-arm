# -*- coding: utf-8 -*-
"""J1 Hall index for the real CM36 + metal coupling + perforated U-bracket.

The fixed carrier bolts to the four unused M3 holes on the CM36 output face.
A tiny bushing places a D3x2 axially magnetised magnet in the existing 4.2 mm
hole at (11, 11) in the rotating U-bracket bottom.  The SS49E stays fixed and
sees the magnet once per J1 revolution (home/index, not continuous angle).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


ROOT = Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)

MOUNT_OUT = ROOT / "hall_j1_cm36_face_mount_SS49E_PETG.stl"
MAGNET_OUT = ROOT / "hall_j1_magnet_bushing_D3x2_OD4p15_PETG.stl"
FIT_OUT = ROOT / "hall_j1_magnet_bushing_fit_set_OD4p00_4p15_4p30_PETG.stl"
PLATE_OUT = ROOT / "PLATE_HALL_J1_INDEX_V1_PRINT_ALL.stl"
ASSEMBLY_OUT = ROOT / "HALL_J1_INDEX_V1_ASSEMBLY_REVIEW_ONLY.stl"
REVIEW_OUT = ROOT / "HALL_J1_INDEX_V1_REVIEW.png"
PARTS_OUT = ROOT / "HALL_J1_INDEX_V1_PARTS_REVIEW.png"
HTML_OUT = ROOT / "HALL_J1_INDEX_V1_INTERACTIVE_3D.html"
THREE_JS_PATH = ROOT / "three.r160.min.js"
GUIDE_OUT = ROOT / "HALL_J1_INDEX_V1_PRINT_AND_ASSEMBLY_RU.md"

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

# Honeywell SS49E flat TO-92-style body allowance.
HALL_BODY_X = 5.2
HALL_BODY_Y = 2.25
HALL_BODY_DEPTH = 1.95
HALL_TOP_Z = 95.2                 # 1.8 mm below flush D3x2 magnet


def boxc(sx, sy, sz, x=0.0, y=0.0, z=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
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

# Compact square tower at the diagonal index position.  Its top carries a
# horizontal SS49E body; the three legs leave through radial open channels.
tower_bottom = base_bottom + base_t - 0.15
tower_top = HALL_TOP_Z
tower = boxc(8.2, 8.2, tower_top - tower_bottom,
             INDEX_X, INDEX_Y, (tower_bottom + tower_top) / 2)

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

carrier_raw = trimesh.boolean.union([outer, tower, web_x, web_y])
cuts = [inner]

# Four through holes match the CM36 output-face M3 pattern.
for angle in (0, 90, 180, 270):
    a = np.deg2rad(angle)
    x = (CM36_M3_BC / 2) * np.cos(a)
    y = (CM36_M3_BC / 2) * np.sin(a)
    cuts.append(cyl_z(3.55, base_t + 1.4, x, y, base_bottom + base_t / 2, sections=48))

# Open pocket: SS49E lies flat with its sensing face upward.
cuts.append(boxc(HALL_BODY_X, HALL_BODY_Y, HALL_BODY_DEPTH + 0.5,
                 INDEX_X, INDEX_Y, HALL_TOP_Z - HALL_BODY_DEPTH / 2 + 0.2))

# Three lead channels open radially toward +Y.  The leads are gently bent only
# after the body is seated; glue/silicone provides strain relief.
for dx in (-1.27, 0.0, 1.27):
    cuts.append(boxc(0.72, 8.0, 2.1,
                     INDEX_X + dx, INDEX_Y + 5.0, HALL_TOP_Z - 0.75))

carrier = clean(trimesh.boolean.difference([carrier_raw] + cuts))
carrier_print = ground(carrier)
carrier_print.export(MOUNT_OUT)


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

# Compact combined print plate: carrier plus three bushing variants.
plate_carrier = carrier_print.copy()
plate_carrier.apply_translation([0, 0, 0])
plate_fit = fit_set.copy()
plate_fit.apply_translation([0, 32, 0])
plate = trimesh.util.concatenate([plate_carrier, plate_fit])
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
sensor = boxc(4.5, 1.65, 3.0, INDEX_X, INDEX_Y, HALL_TOP_Z - 0.82)

# Existing cage review mesh transformed from design X-axis to vertical Z-axis.
cage_path = ROOT.parent / "base_motor_vise_cage_v1" / "base_vise_cage_v1_ASSEMBLY_REVIEW_ONLY.stl"
cage = trimesh.load_mesh(cage_path)
cage.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
cage.apply_translation([0, 0, 24.0])

assembly = trimesh.util.concatenate([
    cage, motor, gearbox, boss, shaft, hub, flange, u_web, u_side_a, u_side_b,
    carrier, magnet_bushing_installed, magnet, sensor,
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
    (carrier, "#2ba86b", 0.98), (sensor, "#14241b", 1.0),
]
rotating_parts = [
    (shaft, "#b8c0c7", 1.0), (hub, "#7e8790", 1.0),
    (flange, "#a4abb1", 1.0), (u_web, "#55a9da", 0.82),
    (u_side_a, "#55a9da", 0.36), (u_side_b, "#55a9da", 0.36),
    (magnet_bushing_installed, "#f4b942", 1.0), (magnet, "#d7333f", 1.0),
]

for col, angle, title in ((0, 0, "НУЛЬ: магнит находится над SS49E"),
                          (1, 72, "ПОВОРОТ: магнит ушёл, SS49E неподвижен")):
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
    (carrier, "#2ba86b", 1.0), (sensor, "#111111", 1.0),
    (u_web, "#55a9da", 0.38), (magnet_bushing_installed, "#f4b942", 1.0),
    (magnet, "#d7333f", 1.0),
):
    draw_mesh(ax, mesh, color, alpha)
set_view(ax, [[-26, -26, 80], [26, 26, 104]], elev=18, azim=-45)
ax.set_title("КРУПНО: зазор датчик–магнит = 1,8 мм", fontsize=11, weight="bold")

ax = fig.add_subplot(gs[1, 2])
ax.axis("off")
notes = (
    "ЧТО ПЕЧАТАТЬ\n"
    "• 1× зелёный кронштейн SS49E\n"
    "• 1× жёлтая втулка магнита\n"
    "• сначала лучше комплект 4.00/4.15/4.30\n\n"
    "КУДА КРЕПИТЬ\n"
    "• кронштейн: неподвижный торец CM36\n"
    "• 4× M3 по окружности 27,5 мм\n"
    "• магнит: готовое Ø4,2 в дне U\n"
    "  координата (11;11), радиус 15,6 мм\n\n"
    "КАК РАБОТАЕТ\n"
    "• U и магнит вращаются вместе\n"
    "• SS49E остаётся на редукторе\n"
    "• один импульс/пик = механический ноль\n"
    "• между индексами угол считаем по STEP\n\n"
    "ВАЖНО\n"
    "SS49E — это индекс, не абсолютный угол.\n"
    "Корпус датчика положить плашмя, лицом\n"
    "к магниту; выводы вывести по 3 пазам."
)
ax.text(0.02, 0.98, notes, va="top", fontsize=10.2, family="DejaVu Sans Mono",
        bbox=dict(boxstyle="round,pad=.7", facecolor="white", edgecolor="#9ba9b5"))

fig.suptitle("J1 · НИЖНИЙ ИНДЕКС НА SS49E · НЕПОДВИЖНЫЙ ДАТЧИК + ВРАЩАЮЩИЙСЯ МАГНИТ",
             fontsize=16, weight="bold", y=.985)
fig.savefig(REVIEW_OUT, dpi=175, bbox_inches="tight")
plt.close(fig)

# Separate close-up so the printable geometry is easy to inspect on a phone.
fig = plt.figure(figsize=(16, 8.5), facecolor="#f3f6f9")
ax = fig.add_subplot(1, 2, 1, projection="3d")
draw_mesh(ax, carrier_print, "#2ba86b", 1.0)
set_view(ax, carrier_print.bounds, elev=28, azim=-48)
ax.set_title("НЕПОДВИЖНЫЙ КРОНШТЕЙН SS49E\n46 × 46 × 12,2 мм · 4×M3 BC27,5", fontsize=12, weight="bold")

ax = fig.add_subplot(1, 2, 2, projection="3d")
display_fit = fit_set.copy()
draw_mesh(ax, display_fit, "#f4b942", 1.0)
set_view(ax, display_fit.bounds, elev=26, azim=-45)
ax.set_title("ТРИ ПРОБНЫЕ ВТУЛКИ МАГНИТА D3×2\nстержень Ø4,00 / Ø4,15 / Ø4,30 мм", fontsize=12, weight="bold")

fig.suptitle("J1 HALL INDEX V1 · ДЕТАЛИ, КОТОРЫЕ ПЕЧАТАЮТСЯ", fontsize=17, weight="bold", y=.98)
fig.text(.5, .035,
         "Кольцо печатается плоско без поддержек. Втулка ставится изнутри U-скобы; карман магнита смотрит вниз.",
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
<title>J1 Hall Index V1</title>
<style>
html,body{margin:0;height:100%;overflow:hidden;background:#0d1521;color:#eaf2fa;font-family:Arial,sans-serif}
#ui{position:absolute;z-index:3;left:18px;top:18px;width:340px;background:#111d2dcc;border:1px solid #31445c;border-radius:14px;padding:15px;backdrop-filter:blur(8px)}
h1{font-size:18px;margin:0 0 10px}.row{margin:10px 0}input{width:100%}.ok{color:#56d889}.warn{color:#ffc857}.small{font-size:13px;line-height:1.42;color:#c5d2df}b{color:white}
#tag{padding:8px;border-radius:8px;background:#203047;margin-top:8px;text-align:center;font-weight:bold}
</style></head><body><div id="ui"><h1>J1 · Hall-индекс SS49E</h1>
<div class="row"><label>Поворот U-скобы: <b id="deg">0°</b></label><input id="rot" type="range" min="-180" max="180" value="0"></div>
<div id="tag" class="ok">МАГНИТ НАД ДАТЧИКОМ · НУЛЕВОЙ ИНДЕКС</div>
<div class="small"><p><b class="ok">Зелёное</b> — неподвижный кронштейн на торце CM36.<br><b style="color:#58b5e8">Голубое</b> — вращающаяся U-скоба.<br><b style="color:#ff4b55">Красное</b> — магнит D3×2.</p>
<p>Магнит стоит в готовом отверстии Ø4,2 на радиусе 15,6 мм. SS49E остаётся под его траекторией.</p></div></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script>
const scene=new THREE.Scene();scene.background=new THREE.Color(0x0d1521);
const camera=new THREE.PerspectiveCamera(38,innerWidth/innerHeight,.1,1000);camera.position.set(125,105,125);camera.lookAt(0,0,80);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(devicePixelRatio);document.body.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xe8f4ff,0x253347,2.1));const dl=new THREE.DirectionalLight(0xffffff,2.3);dl.position.set(80,-50,160);scene.add(dl);
const mat=(c,o=1)=>new THREE.MeshStandardMaterial({color:c,transparent:o<1,opacity:o,roughness:.58,metalness:.08,side:THREE.DoubleSide});
const addBox=(g,s,p,c,o=1)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(...s),mat(c,o));m.position.set(...p);g.add(m);return m};
const addCyl=(g,d,h,p,c)=>{const m=new THREE.Mesh(new THREE.CylinderGeometry(d/2,d/2,h,64),mat(c));m.rotation.x=Math.PI/2;m.position.set(...p);g.add(m);return m};
const fixed=new THREE.Group(),rotating=new THREE.Group();scene.add(fixed,rotating);
addBox(fixed,[42.3,42.3,48],[0,0,24],0x262b31);addCyl(fixed,36,35,[0,0,65.5],0x3158a4);addCyl(fixed,22,1.6,[0,0,83.8],0x929aa1);
addCyl(fixed,46,2.6,[0,0,84.3],0x2ba86b);addBox(fixed,[8.2,8.2,10.1],[11,11,90.1],0x2ba86b);addBox(fixed,[4.5,1.7,3],[11,11,94.35],0x101416);
addCyl(rotating,8,16,[0,0,91],0xb8c0c7);addCyl(rotating,14.1,10,[0,0,90],0x7e8790);addCyl(rotating,21.8,2,[0,0,96],0xa4abb1);
addBox(rotating,[48,43,2.5],[0,0,98.25],0x58b5e8,.74);addBox(rotating,[48,2.5,96],[0,-22.75,147.5],0x58b5e8,.35);addBox(rotating,[48,2.5,96],[0,22.75,147.5],0x58b5e8,.35);
addCyl(rotating,6.6,1,[11,11,100],0xf4b942);addCyl(rotating,3,2,[11,11,98],0xd7333f);
const grid=new THREE.GridHelper(220,22,0x33465f,0x223146);scene.add(grid);
let down=false,px=0,py=0,yaw=.75,pitch=.62;renderer.domElement.onpointerdown=e=>{down=true;px=e.clientX;py=e.clientY};onpointerup=()=>down=false;onpointermove=e=>{if(!down)return;yaw+=(e.clientX-px)*.006;pitch=Math.max(.15,Math.min(1.35,pitch+(e.clientY-py)*.005));px=e.clientX;py=e.clientY};
function cam(){camera.position.set(145*Math.cos(yaw)*Math.cos(pitch),145*Math.sin(yaw)*Math.cos(pitch),70+145*Math.sin(pitch));camera.lookAt(0,0,82)}
const slider=document.getElementById('rot'),deg=document.getElementById('deg'),tag=document.getElementById('tag');slider.oninput=()=>{const a=+slider.value;rotating.rotation.z=a*Math.PI/180;deg.textContent=a+'°';const near=Math.abs(a)<7;tag.textContent=near?'МАГНИТ НАД ДАТЧИКОМ · НУЛЕВОЙ ИНДЕКС':'МАГНИТ ВНЕ ДАТЧИКА';tag.className=near?'ok':'warn'};
onresize=()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)};(function loop(){cam();renderer.render(scene,camera);requestAnimationFrame(loop)})();
</script></body></html>'''

# Keep the interactive review fully self-contained.  A local file:// page in
# Edge may block storage/network access for CDN scripts, leaving the UI visible
# but the WebGL model blank.  Embedding the vendored Three.js build avoids any
# browser security exception and makes the file usable without internet.
three_js = THREE_JS_PATH.read_text(encoding="utf-8")
three_js = "\n".join(
    line for line in three_js.splitlines() if "sourceMappingURL=" not in line
)
offline_three_tag = "<script>\n" + three_js.replace("</script>", "<\\/script>") + "\n</script>"
html = html.replace(
    '<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>',
    offline_three_tag,
)
HTML_OUT.write_text(html, encoding="utf-8")


guide = """# J1 Hall Index V1 — печать и сборка

Этот узел даёт **одну точку механического нуля** нижней оси J1. Он не измеряет
непрерывный абсолютный угол: между прохождениями магнита положение считается по
шагам двигателя.

## На какие реальные детали рассчитано

- планетарный редуктор CM36: корпус Ø36×35 мм;
- неподвижный выступ торца Ø22×1,6 мм;
- четыре резьбы M3 по окружности Ø27,5 мм;
- металлическая муфта: хаб Ø14,1, фланец Ø21,8×2;
- дно U-скобы 48×43×2,5 мм;
- готовое отверстие U-скобы Ø4,2 в координате (11;11), радиус 15,56 мм;
- голый линейный Hall-датчик **SS49E, flat TO-92-style**;
- обычный аксиально намагниченный неодимовый магнит **D3×2 мм**.

## Что печатать

Для первой примерки печатать `PLATE_HALL_J1_INDEX_V1_PRINT_ALL.stl`. В ней:

1. неподвижный зелёный кронштейн датчика;
2. три втулки магнита со стержнем Ø4,00 / Ø4,15 / Ø4,30 мм.

Выбрать втулку, которая входит в реальное отверстие Ø4,2 плотно от руки. Не
забивать молотком. Основной отдельный файл сделан с Ø4,15 мм.

## Настройки печати

- PETG;
- сопло 0,4 мм;
- слой 0,20 мм;
- 4 стенки;
- заполнение 35–45%;
- поддержки не нужны;
- для маленьких втулок включить минимальное время слоя 8–10 секунд.

## Сборка

1. Снять муфту/U-скобу с выходного вала.
2. Положить кольцевой кронштейн на неподвижный торец CM36 вокруг выступа Ø22.
3. Закрепить двумя или четырьмя винтами M3. Начать с **M3×6**; проверить, что
   винт вошёл в резьбу, но не упёрся в дно. Длина резьбы конкретного редуктора
   должна быть проверена вручную.
4. Уложить SS49E плашмя в верхний карман, чувствительной плоскостью к U-скобе.
   Три вывода вывести по открытым пазам. Зафиксировать каплей нейтрального
   силикона или термоклея, не цианоакрилатом у самого корпуса.
5. Собрать муфту и U-скобу обратно.
6. В отверстие (11;11) U-скобы вставить выбранную втулку **изнутри скобы**.
   Карман магнита должен смотреть вниз, к SS49E.
7. Вклеить D3×2 в карман заподлицо. Начать с небольшого количества эпоксидки.
8. Медленно провернуть J1 рукой на 360° и убедиться, что минимальный механический
   зазор нигде не исчезает. Расчётный зазор магнит–корпус SS49E: 1,8 мм.

## Электрика

SS49E — аналоговый датчик. Проверить распиновку именно своего экземпляра по
маркировке/даташиту, не ориентироваться только по форме корпуса. Для оригинального
Honeywell SS49E питание допустимо 2,7–6,5 В; с ESP32 используем 3,3 В и читаем
аналоговый выход через ADC. Ноль определяется порогом и калибруется программно.

## Важное ограничение

Магнит D3×2 здесь является только индексом. После включения рука должна медленно
найти этот индекс, остановиться и установить счётчик J1 в известное нулевое
положение. Пропущенные шаги между индексами Hall-датчик сам не обнаруживает.
"""
GUIDE_OUT.write_text(guide, encoding="utf-8")


def report(name, mesh):
    print(name,
          "watertight=", mesh.is_watertight,
          "components=", len(mesh.split(only_watertight=False)),
          "extents=", np.round(mesh.extents, 2),
          "volume=", round(float(mesh.volume), 1))


for name, mesh in (
    ("CARRIER", carrier_print), ("MAGNET BUSHING", magnet_print),
    ("FIT SET", fit_set), ("PRINT PLATE", plate),
):
    report(name, mesh)

print("CALCULATED SENSOR-MAGNET GAP", round(U_WEB_BOTTOM_Z - HALL_TOP_Z, 2), "mm")
print("INDEX RADIUS", round(float(np.hypot(INDEX_X, INDEX_Y)), 2), "mm")
print("OUTPUT", ROOT)
