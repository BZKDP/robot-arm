# -*- coding: utf-8 -*-
"""Four-position Hall index for the CM36 output used at J1 and J4.

The stationary PETG cartridge bolts to the four M3 holes on the CM36 face.
Four analogue SS49E sensors sit at 90 degree intervals on the existing
15.56 mm magnet track.  One D3x2 axially magnetised magnet rotates in the
existing 4.2 mm hole of the metal U/output bracket.

This is an absolute four-landmark index plus step-count correction.  It is
not a continuous absolute encoder between landmarks.
"""
from pathlib import Path

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
ARM_PRINTED = ROOT.parent

CARRIER_OUT = ROOT / "hall_quad_CM36_cartridge_4xSS49E_PETG.stl"
RETAINER_OUT = ROOT / "hall_quad_retainer_ring_4xSS49E_M3_PETG.stl"
MAGNET_OUT = ROOT / "hall_quad_magnet_bushing_D3x2_OD4p15_PETG.stl"
HALL_FIT_OUT = ROOT / "hall_quad_SS49E_body_pocket_fit_test_3_sizes_PETG.stl"
MAGNET_FIT_OUT = ROOT / "hall_quad_magnet_bushing_fit_set_OD4p00_4p15_4p30_PETG.stl"
ONE_JOINT_OUT = ROOT / "PLATE_HALL_QUAD_INDEX_V3_ONE_JOINT_PRINT.stl"
TWO_JOINT_OUT = ROOT / "PLATE_HALL_QUAD_INDEX_V3_TWO_JOINTS_PRINT.stl"
ASSEMBLY_OUT = ROOT / "HALL_QUAD_INDEX_V3_ASSEMBLY_REVIEW_ONLY.stl"
HTML_OUT = ROOT / "HALL_QUAD_INDEX_V3_INTERACTIVE_3D.html"
GUIDE_OUT = ROOT / "HALL_QUAD_INDEX_V3_PRINT_WIRING_ASSEMBLY_RU.md"
SHOPPING_OUT = ROOT / "HALL_QUAD_INDEX_V3_SHOPPING_LIST_RU.md"

J4_ROOT = ARM_PRINTED / "j4_roll_quad_hall_v6"
J4_ROOT.mkdir(parents=True, exist_ok=True)
J4_REAR_OUT = J4_ROOT / "j4_roll_v6_rear_cup_M5X80_PETG.stl"
J4_KEY_OUT = J4_ROOT / "j4_roll_v6_rear_square_key_PETG.stl"
J4_TOP_OUT = J4_ROOT / "j4_roll_v6_front_frame_TOP_PETG.stl"
J4_BOTTOM_OUT = J4_ROOT / "j4_roll_v6_front_frame_BOTTOM_PETG.stl"
J4_SPACERS_OUT = J4_ROOT / "j4_roll_v6_tube_spacers_x2_PETG.stl"
J4_CARRIER_OUT = J4_ROOT / "j4_roll_v6_hall_cartridge_4xSS49E_PETG.stl"
J4_RETAINER_OUT = J4_ROOT / "j4_roll_v6_hall_retainer_ring_PETG.stl"
J4_MAGNET_OUT = J4_ROOT / "j4_roll_v6_magnet_bushing_D3x2_PETG.stl"
J4_PLATE_OUT = J4_ROOT / "PLATE_J4_ROLL_V6_M5X80_PLUS_QUAD_HALL_PRINT_ALL.stl"
J4_HTML_OUT = J4_ROOT / "J4_ROLL_V6_QUAD_HALL_INTERACTIVE_3D.html"
J4_GUIDE_OUT = J4_ROOT / "J4_ROLL_V6_QUAD_HALL_PRINT_AND_ASSEMBLY_RU.md"
J4_WIRING_OUT = J4_ROOT / "J4_QUAD_HALL_WIRING_AND_CALIBRATION_RU.md"
J4_SHOPPING_OUT = J4_ROOT / "J4_QUAD_HALL_SHOPPING_LIST_RU.md"

# Shared real geometry, mm.
CM36_FACE_Z = 83.0
CM36_BOSS_D = 22.0
CM36_M3_BC = 27.5
CM36_M3_CLEAR = 3.55
COUPLING_HUB_D = 14.1
COUPLING_FLANGE_D = 21.8
U_WEB_BOTTOM_Z = 97.0
U_WEB_T = 2.5
INDEX_X = 11.0
INDEX_Y = 11.0
INDEX_R = float(np.hypot(INDEX_X, INDEX_Y))

# SS49E flat TO-92-style body, nominal 4.1 x 3.0 x 1.6 mm.
HALL_BODY_X = 4.60          # tangential pocket width
HALL_BODY_Y = 3.50          # radial pocket length
HALL_BODY_DEPTH = 1.70       # nominal 1.60; leaves 0.10 mm for package spread
HALL_TOP_Z = 95.2
SENSOR_ANGLES = (45.0, 135.0, 225.0, 315.0)

CARRIER_D = 46.0
CARRIER_INNER_D = 22.8
CARRIER_BOTTOM_Z = CM36_FACE_Z
CARRIER_TOP_Z = HALL_TOP_Z
CARRIER_H = CARRIER_TOP_Z - CARRIER_BOTTOM_Z

RETAINER_OD = 45.2
RETAINER_ID = 23.6
RETAINER_T = 0.90
RETAINER_SCREW_R = 19.7


def boxc(sx, sy, sz, x=0.0, y=0.0, z=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_translation([x, y, z])
    return mesh


def box_rot_z(sx, sy, sz, x=0.0, y=0.0, z=0.0, angle_deg=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(angle_deg), [0, 0, 1]
    ))
    mesh.apply_translation([x, y, z])
    return mesh


def cyl_z(d, h, x=0.0, y=0.0, z=0.0, sections=64):
    mesh = trimesh.creation.cylinder(radius=d / 2, height=h, sections=sections)
    mesh.apply_translation([x, y, z])
    return mesh


def clean(mesh):
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    trimesh.repair.fix_normals(mesh)
    return mesh


def largest(mesh):
    return clean(max(mesh.split(only_watertight=False), key=lambda item: abs(item.volume)))


def ground(mesh):
    result = mesh.copy()
    result.apply_translation([0, 0, -result.bounds[0][2]])
    return result


def place_min(mesh, x, y):
    result = ground(mesh)
    result.apply_translation([x - result.bounds[0][0], y - result.bounds[0][1], 0])
    return result


def centred_plate(items):
    plate = trimesh.util.concatenate(items)
    plate.apply_translation([
        -(plate.bounds[0][0] + plate.bounds[1][0]) / 2,
        -(plate.bounds[0][1] + plate.bounds[1][1]) / 2,
        -plate.bounds[0][2],
    ])
    return clean(plate)


# ---------------------------------------------------------------------------
# Fixed full-height annular cartridge.  A continuous wall is stronger and
# easier to print than four thin towers.  Counterbores keep M3x12 heads below
# the sensor retainer.  The rotating O21.8 flange has 0.5 mm radial clearance.
# ---------------------------------------------------------------------------
outer = cyl_z(CARRIER_D, CARRIER_H, z=CARRIER_BOTTOM_Z + CARRIER_H / 2, sections=128)
inner = cyl_z(CARRIER_INNER_D, CARRIER_H + 2.0,
              z=CARRIER_BOTTOM_Z + CARRIER_H / 2, sections=128)
cuts = [inner]

# CM36 mounting: M3x12 DIN 912 enters from the top counterbore.
for angle in (0.0, 90.0, 180.0, 270.0):
    a = np.deg2rad(angle)
    x = (CM36_M3_BC / 2) * np.cos(a)
    y = (CM36_M3_BC / 2) * np.sin(a)
    cuts.append(cyl_z(CM36_M3_CLEAR, CARRIER_H + 2.0,
                      x, y, CARRIER_BOTTOM_Z + CARRIER_H / 2, sections=48))
    cuts.append(cyl_z(6.25, 3.35, x, y, CARRIER_TOP_Z - 1.675, sections=48))

sensor_centres = []
for angle in SENSOR_ANGLES:
    a = np.deg2rad(angle)
    radial = np.array([np.cos(a), np.sin(a)])
    tangent = np.array([-np.sin(a), np.cos(a)])
    centre = radial * INDEX_R
    sensor_centres.append(centre)
    rotation = angle - 90.0  # local +Y points radially outward

    # Sensor body finishes about 0.1 mm below the top and is clamped by the
    # orange ring with a 0.10-0.20 mm Kapton/PET shim if the clone is thin.
    cuts.append(box_rot_z(
        HALL_BODY_X, HALL_BODY_Y, HALL_BODY_DEPTH + 0.50,
        centre[0], centre[1], CARRIER_TOP_Z + 0.25 - HALL_BODY_DEPTH / 2,
        rotation,
    ))

    # Three independent pin/wire grooves, 1.27 mm pitch.  They run fully to
    # the outer wall so each sensor has an obvious three-wire exit.
    for pin_offset in (-1.30, 0.0, 1.30):
        groove_centre = centre + tangent * pin_offset + radial * 4.85
        cuts.append(box_rot_z(
            0.82, 7.0, 1.72,
            groove_centre[0], groove_centre[1], CARRIER_TOP_Z - 0.70,
            rotation,
        ))

    # Shallow solder/service bay outside the body.  It leaves a visible lip at
    # the outer wall and prevents the three solder joints touching each other.
    bay_centre = centre + radial * 3.10
    cuts.append(box_rot_z(
        5.8, 2.1, 1.72,
        bay_centre[0], bay_centre[1], CARRIER_TOP_Z - 0.70,
        rotation,
    ))

# Four pilot holes for M3x6 retainer screws.  They sit between sensor pockets.
retainer_screw_centres = []
for angle in (0.0, 90.0, 180.0, 270.0):
    a = np.deg2rad(angle)
    x, y = RETAINER_SCREW_R * np.cos(a), RETAINER_SCREW_R * np.sin(a)
    retainer_screw_centres.append((x, y))
    cuts.append(cyl_z(2.60, 6.5, x, y, CARRIER_TOP_Z - 3.25, sections=48))

carrier = largest(trimesh.boolean.difference([outer] + cuts))
carrier_print = ground(carrier)
carrier_print.export(CARRIER_OUT)


# One-piece retainer: four sensor windows, four carrier screw access holes and
# four M3 clamping holes.  It remains a single ring after all openings.
ret_outer = cyl_z(RETAINER_OD, RETAINER_T, z=RETAINER_T / 2, sections=128)
ret_inner = cyl_z(RETAINER_ID, RETAINER_T + 1.0, z=RETAINER_T / 2, sections=128)
ret_cuts = [ret_inner]
for angle, centre in zip(SENSOR_ANGLES, sensor_centres):
    ret_cuts.append(box_rot_z(
        3.30, 2.30, RETAINER_T + 1.0,
        centre[0], centre[1], RETAINER_T / 2, angle - 90.0,
    ))
for angle in (0.0, 90.0, 180.0, 270.0):
    a = np.deg2rad(angle)
    # Access to recessed CM36 screw heads.
    ret_cuts.append(cyl_z(6.55, RETAINER_T + 1.0,
                          (CM36_M3_BC / 2) * np.cos(a),
                          (CM36_M3_BC / 2) * np.sin(a),
                          RETAINER_T / 2, sections=48))
for x, y in retainer_screw_centres:
    ret_cuts.append(cyl_z(3.50, RETAINER_T + 1.0, x, y,
                          RETAINER_T / 2, sections=48))
retainer = largest(trimesh.boolean.difference([ret_outer] + ret_cuts))
retainer_print = ground(retainer)
retainer_print.export(RETAINER_OUT)


# Rotating magnet bushing: stem goes into the existing 4.2 mm U/output hole;
# the D3x2 magnet is glued from below and ends flush with the rotating face.
def magnet_bushing(outer_d=4.15):
    flange = cyl_z(6.6, 1.0, z=U_WEB_BOTTOM_Z + U_WEB_T + 0.5, sections=64)
    stem = cyl_z(outer_d, U_WEB_T, z=U_WEB_BOTTOM_Z + U_WEB_T / 2, sections=64)
    body = trimesh.boolean.union([flange, stem])
    pocket = cyl_z(3.22, 2.15, z=U_WEB_BOTTOM_Z + 1.075, sections=64)
    return largest(trimesh.boolean.difference([body, pocket]))


magnet_installed = magnet_bushing(4.15)
magnet_print = magnet_installed.copy()
magnet_print.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
magnet_print = ground(magnet_print)
magnet_print.export(MAGNET_OUT)


# Cheap calibration pieces bracket clone packages and printer flow.
hall_fit_items = []
for i, (px, py) in enumerate(((4.40, 3.30), (4.60, 3.50), (4.80, 3.70))):
    base = boxc(8.6, 7.4, 3.0, x=i * 11.0, z=1.5)
    pocket = boxc(px, py, 2.15, x=i * 11.0, z=2.45)
    lead_exit = boxc(3.4, 3.8, 2.15, x=i * 11.0, y=3.2, z=2.45)
    hall_fit_items.append(largest(trimesh.boolean.difference([base, pocket, lead_exit])))
hall_fit = trimesh.util.concatenate(hall_fit_items)
hall_fit.apply_translation([-11.0, 0, 0])
hall_fit.export(HALL_FIT_OUT)

mag_fit_items = []
for i, od in enumerate((4.00, 4.15, 4.30)):
    item = magnet_bushing(od)
    item.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    item = ground(item)
    item.apply_translation([i * 10.0, 0, 0])
    mag_fit_items.append(item)
magnet_fit = trimesh.util.concatenate(mag_fit_items)
magnet_fit.apply_translation([-10.0, 0, 0])
magnet_fit.export(MAGNET_FIT_OUT)


# Production plates: no calibration coupons mixed into final parts.
one_joint = centred_plate([
    place_min(carrier_print, 0, 0),
    place_min(retainer_print, 53, 0),
    place_min(magnet_print, 102, 18),
])
one_joint.export(ONE_JOINT_OUT)

two_joint = centred_plate([
    place_min(carrier_print, 0, 0), place_min(retainer_print, 53, 0),
    place_min(magnet_print, 102, 18),
    place_min(carrier_print, 0, 53), place_min(retainer_print, 53, 53),
    place_min(magnet_print, 102, 71),
])
two_joint.export(TWO_JOINT_OUT)


# Review assembly in J1 orientation.
motor = boxc(42.3, 42.3, 48.0, z=24.0)
gearbox = cyl_z(36.0, 35.0, z=65.5, sections=96)
boss = cyl_z(CM36_BOSS_D, 1.6, z=83.8, sections=96)
shaft = cyl_z(8.0, 16.0, z=91.0, sections=64)
hub = cyl_z(COUPLING_HUB_D, 10.0, z=90.0, sections=80)
flange = cyl_z(COUPLING_FLANGE_D, 2.0, z=96.0, sections=80)
u_web = boxc(48.0, 43.0, U_WEB_T, z=U_WEB_BOTTOM_Z + U_WEB_T / 2)
magnet = cyl_z(3.0, 2.0, INDEX_X, INDEX_Y, U_WEB_BOTTOM_Z + 1.0, sections=64)
sensor_solids = []
for angle, centre in zip(SENSOR_ANGLES, sensor_centres):
    sensor_solids.append(box_rot_z(4.1, 3.0, 1.6, centre[0], centre[1],
                                   HALL_TOP_Z - 0.80, angle - 90.0))
retainer_installed = retainer.copy()
retainer_installed.apply_translation([0, 0, HALL_TOP_Z])
assembly = trimesh.util.concatenate([
    motor, gearbox, boss, shaft, hub, flange, u_web, carrier,
    retainer_installed, magnet_installed, magnet, *sensor_solids,
])
assembly.export(ASSEMBLY_OUT)


# ---------------------------------------------------------------------------
# Self-contained J4 roll print package.  The proven V5 cage geometry is reused
# unchanged and combined with one production quad-Hall set.
# ---------------------------------------------------------------------------
roll_sources = {
    J4_REAR_OUT: ARM_PRINTED / "roll_cage_v5_M5X80_rear_cup_NO_MOTOR_SCREWS_PETG.stl",
    J4_KEY_OUT: ARM_PRINTED / "roll_cage_v5_M5X80_rear_square_key_PETG.stl",
    J4_TOP_OUT: ARM_PRINTED / "roll_cage_v5_M5X80_front_frame_TOP_PETG.stl",
    J4_BOTTOM_OUT: ARM_PRINTED / "roll_cage_v5_M5X80_front_frame_BOTTOM_PETG.stl",
    J4_SPACERS_OUT: ARM_PRINTED / "tube_spacers_x2_PETG.stl",
}
roll_meshes = {}
for target, source in roll_sources.items():
    mesh = trimesh.load_mesh(source)
    mesh.export(target)
    roll_meshes[target] = mesh
carrier_print.export(J4_CARRIER_OUT)
retainer_print.export(J4_RETAINER_OUT)
magnet_print.export(J4_MAGNET_OUT)

rear = roll_meshes[J4_REAR_OUT]
key = roll_meshes[J4_KEY_OUT]
front_top = roll_meshes[J4_TOP_OUT]
front_bottom = roll_meshes[J4_BOTTOM_OUT]
spacers = roll_meshes[J4_SPACERS_OUT]

# Compact layout with generous edge margin even on a nominal 220 x 220 bed.
j4_plate = centred_plate([
    place_min(rear, 0, 0),
    place_min(front_top, 96, 0),
    place_min(front_bottom, 96, 47),
    place_min(key, 0, 96),
    place_min(carrier_print, 62, 96),
    place_min(retainer_print, 116, 96),
    place_min(spacers, 169, 96),
    place_min(magnet_print, 179, 112),
])
j4_plate.export(J4_PLATE_OUT)


def report(name, mesh):
    print(
        f"{name}: watertight={mesh.is_watertight} "
        f"components={len(mesh.split(only_watertight=False))} "
        f"extents={np.round(mesh.extents, 2).tolist()} "
        f"volume={round(float(mesh.volume), 1)}"
    )


report("CARRIER", carrier_print)
report("RETAINER", retainer_print)
report("MAGNET BUSHING", magnet_print)
report("ONE JOINT PLATE", one_joint)
report("TWO JOINT PLATE", two_joint)
report("J4 COMPLETE PLATE", j4_plate)


# Offline interactive review.  All important dimensions are visible and the
# slider rotates the one magnet past all four fixed sensors.
three_path = ARM_PRINTED / "hall_j1_dual_index_v2" / "three.r160.min.js"
three_js = three_path.read_text(encoding="utf-8")
html = r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Hall Quad Index V3</title>
<style>*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#09111d;color:#eaf2ff;font:14px Segoe UI,Arial}canvas{display:block}.panel{position:fixed;z-index:2;background:#101c2ddd;border:1px solid #29415e;border-radius:14px;backdrop-filter:blur(7px);box-shadow:0 10px 35px #0008}.ui{left:16px;top:16px;width:365px;padding:16px}.legend{right:16px;top:16px;width:330px;padding:16px}.title{font-size:20px;font-weight:800;color:#63dcff}.sub{color:#a8bdd5;line-height:1.38;margin:6px 0 12px}.row{margin:12px 0}.row label{display:flex;justify-content:space-between;margin-bottom:6px}.row input{width:100%}.pill{display:inline-block;padding:4px 8px;border-radius:999px;background:#18304c;color:#83e8ff}.cards{display:grid;gap:8px}.card{padding:9px 10px;border-radius:10px;background:#14263c;line-height:1.3}.green{color:#5ee5a0}.orange{color:#ffad5a}.red{color:#ff666e}.cyan{color:#63dcff}button{background:#1d4167;color:#fff;border:1px solid #3d6d99;border-radius:9px;padding:8px 10px;cursor:pointer;margin:3px}.warn{margin-top:10px;padding:9px;background:#3a2817;border-radius:9px;color:#ffd9a8}</style></head><body>
<div class="panel ui"><div class="title">J1 / J4 · QUAD HALL INDEX V3</div><div class="sub">Четыре неподвижных SS49E через 90° и один вращающийся магнит D3×2. Одинаковая кассета для обоих CM36.</div><div class="row"><label>Поворот сустава <b id="ang">0°</b></label><input id="joint" type="range" min="0" max="360" value="0"></div><div class="row"><label>Разнести детали <b id="expv">0 мм</b></label><input id="explode" type="range" min="0" max="18" value="0"></div><div><button id="auto">▶ Автовращение</button><button id="top">Вид сверху</button><button id="iso">Изометрия</button></div><div class="warn">Это 4 абсолютные контрольные позиции на оборот. Между ними угол ведётся по STEP, а индекс исправляет накопленную ошибку.</div></div>
<div class="panel legend"><div class="title">Что где находится</div><div class="cards"><div class="card"><span class="green">Зелёное кольцо</span> — неподвижная PETG-кассета на 4×M3 торца CM36.</div><div class="card"><span class="orange">Оранжевое кольцо</span> — один прижим 4 датчиков, 4×M3×6.</div><div class="card"><span class="cyan">Голубые элементы</span> — четыре SS49E, центры R15,56 мм.</div><div class="card"><span class="red">Красное</span> — один магнит D3×2 во вращающейся втулке.</div><div class="card">Каждый датчик имеет 3 отдельные канавки. На сустав выходит 6 линий: 3V3, GND и OUT0…OUT3.</div></div></div>
<script>__THREE__</script><script>
const scene=new THREE.Scene();scene.background=new THREE.Color(0x09111d);const camera=new THREE.PerspectiveCamera(43,innerWidth/innerHeight,.1,1000);camera.position.set(78,72,80);const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;document.body.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xcde9ff,0x1a2230,2.0));const dl=new THREE.DirectionalLight(0xffffff,2.2);dl.position.set(70,90,100);dl.castShadow=true;scene.add(dl);const grid=new THREE.GridHelper(160,32,0x26425e,0x17283b);grid.rotation.x=Math.PI/2;grid.position.z=82;scene.add(grid);
const M={motor:new THREE.MeshStandardMaterial({color:0x252a31,roughness:.55}),gb:new THREE.MeshStandardMaterial({color:0x315ca8,metalness:.45,roughness:.38}),metal:new THREE.MeshStandardMaterial({color:0x9ba6b0,metalness:.75,roughness:.25}),carrier:new THREE.MeshStandardMaterial({color:0x27ad70,roughness:.6}),ret:new THREE.MeshStandardMaterial({color:0xff902f,roughness:.6}),bush:new THREE.MeshStandardMaterial({color:0xff902f,roughness:.6,transparent:true,opacity:.48}),sensor:new THREE.MeshStandardMaterial({color:0x4fd3ff,roughness:.35}),mag:new THREE.MeshStandardMaterial({color:0xd72e3a,metalness:.25,roughness:.32}),u:new THREE.MeshStandardMaterial({color:0x48a9dc,metalness:.3,roughness:.38,transparent:true,opacity:.72}),wire:new THREE.MeshStandardMaterial({color:0x181b20})};
function mesh(g,m,p=[0,0,0]){const q=new THREE.Mesh(g,m);q.position.set(...p);q.castShadow=q.receiveShadow=true;scene.add(q);return q}function box(x,y,z,m,p){return mesh(new THREE.BoxGeometry(x,y,z),m,p)}function cyl(d,h,m,p){const q=mesh(new THREE.CylinderGeometry(d/2,d/2,h,64),m,p);q.rotation.x=Math.PI/2;return q}function ring(od,id,h,m,z){const s=new THREE.Shape();s.absarc(0,0,od/2,0,Math.PI*2);const hole=new THREE.Path();hole.absarc(0,0,id/2,0,Math.PI*2,true);s.holes.push(hole);const q=mesh(new THREE.ExtrudeGeometry(s,{depth:h,bevelEnabled:false}),m,[0,0,z]);return q}
box(42.3,42.3,48,M.motor,[0,0,24]);cyl(36,35,M.gb,[0,0,65.5]);cyl(22,1.6,M.metal,[0,0,83.8]);cyl(8,16,M.metal,[0,0,91]);cyl(14.1,10,M.metal,[0,0,90]);cyl(21.8,2,M.metal,[0,0,96]);
const carrier=ring(46,22.8,12.2,M.carrier,83);const retainer=ring(45.2,23.6,.9,M.ret,95.2);const fixed=[];const R=Math.sqrt(242);for(const a of [45,135,225,315]){const t=a*Math.PI/180,x=R*Math.cos(t),y=R*Math.sin(t);const s=box(4.6,3.5,1.6,M.sensor,[x,y,94.4]);s.rotation.z=t-Math.PI/2;fixed.push(s);for(const off of [-1.27,0,1.27]){const tx=x-Math.sin(t)*off+Math.cos(t)*5,ty=y+Math.cos(t)*off+Math.sin(t)*5;const w=box(.45,7,.45,M.wire,[tx,ty,94.25]);w.rotation.z=t-Math.PI/2;fixed.push(w)}}
const rot=new THREE.Group();scene.add(rot);const uw=new THREE.Mesh(new THREE.BoxGeometry(48,43,2.5),M.u);uw.position.z=98.25;rot.add(uw);const hub=new THREE.Mesh(new THREE.CylinderGeometry(3.3,3.3,3.5,48),M.bush);hub.rotation.x=Math.PI/2;hub.position.set(11,11,99.25);rot.add(hub);const mag=new THREE.Mesh(new THREE.CylinderGeometry(1.5,1.5,2,48),M.mag);mag.rotation.x=Math.PI/2;mag.position.set(11,11,98);rot.add(mag);
for(const a of [0,90,180,270]){const t=a*Math.PI/180;const h=cyl(3.55,12.2,M.metal,[13.75*Math.cos(t),13.75*Math.sin(t),89.1]);h.material=new THREE.MeshStandardMaterial({color:0x1b232c,metalness:.7})}
let dragging=false,px=0,py=0,yaw=.75,pitch=.78,dist=125,auto=false;renderer.domElement.onpointerdown=e=>{dragging=true;px=e.clientX;py=e.clientY};onpointerup=()=>dragging=false;onpointermove=e=>{if(!dragging)return;yaw-=(e.clientX-px)*.008;pitch=Math.max(.1,Math.min(1.5,pitch+(e.clientY-py)*.008));px=e.clientX;py=e.clientY};renderer.domElement.onwheel=e=>dist=Math.max(65,Math.min(220,dist+e.deltaY*.08));function cam(){camera.position.set(dist*Math.cos(yaw)*Math.sin(pitch),dist*Math.sin(yaw)*Math.sin(pitch),86+dist*Math.cos(pitch));camera.lookAt(0,0,79)}
const joint=document.getElementById('joint'),explode=document.getElementById('explode');joint.oninput=()=>{rot.rotation.z=+joint.value*Math.PI/180;document.getElementById('ang').textContent=joint.value+'°'};explode.oninput=()=>{const e=+explode.value;retainer.position.z=95.2+e;for(const s of fixed)s.position.z+=e-(s.userData.e||0);for(const s of fixed)s.userData.e=e;rot.position.z=e*1.7;document.getElementById('expv').textContent=e+' мм'};document.getElementById('auto').onclick=()=>auto=!auto;document.getElementById('top').onclick=()=>{yaw=0;pitch=.05;dist=130};document.getElementById('iso').onclick=()=>{yaw=.75;pitch=.78;dist=125};
let last=performance.now();function tick(now){const dt=(now-last)/1000;last=now;if(auto){joint.value=(+joint.value+dt*35)%360;joint.oninput()}cam();renderer.render(scene,camera);requestAnimationFrame(tick)}requestAnimationFrame(tick);onresize=()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)};
</script></body></html>'''.replace("__THREE__", three_js)
HTML_OUT.write_text(html, encoding="utf-8")
J4_HTML_OUT.write_text(html.replace("<title>Hall Quad Index V3</title>", "<title>J4 Roll V6 · Quad Hall Index</title>").replace("J1 / J4 · QUAD HALL INDEX V3", "J4 ROLL V6 · QUAD HALL INDEX"), encoding="utf-8")


guide = f'''# QUAD HALL INDEX V3 — печать, проводка и сборка

## Что выбрано

- 4× аналоговый SS49E на J1 через 90°.
- 4× аналоговый SS49E на J4 через 90°.
- 1× магнит D3×2, аксиально намагниченный, на каждый сустав.
- 1× ADS1115 на каждый сустав: A0…A3 принимают четыре аналоговых выхода.
- Оба ADS1115 подключаются к уже купленному TCA9548A на сенсорной ESP32.

Это даёт четыре абсолютных контрольных положения на оборот (0/90/180/270° после калибровки). Между метками положение считается по STEP. Это индексная коррекция, не непрерывный абсолютный энкодер.

## Печать

PETG, сопло 0,4 мм, слой 0,20 мм, 5 стенок, 35–45% infill, без поддержек.

- На один сустав: `{ONE_JOINT_OUT.name}`.
- На два сустава сразу: `{TWO_JOINT_OUT.name}`.
- Сначала отдельно желательно: `{HALL_FIT_OUT.name}` и `{MAGNET_FIT_OUT.name}`.

## Крепёж на один сустав

- 4× M3×12 DIN 912 — кассета к торцу CM36.
- 4× M3×6 DIN 912 — прижимное кольцо в пластик.
- 1× капля эпоксидки/фиксатор для магнита.

## Установка датчиков

1. Плоская маркированная сторона каждого SS49E смотрит вверх к магниту.
2. Выводы согнуть только после примерки корпуса; уложить по одному в три отдельные радиальные канавки.
3. Если конкретный клон корпуса тоньше кармана, положить поверх корпуса прокладку Kapton/PET 0,10–0,20 мм; датчик не должен двигаться под прижимом.
4. Для каждого SS49E: VCC=3V3, GND=GND, OUT=свой отдельный канал ADS1115.
5. На суставе объединить только VCC и GND. Получится шестижильный жгут: 3V3, GND, OUT0, OUT1, OUT2, OUT3.
6. Перед окончательной затяжкой проверить, что магнит нигде не цепляет при полном обороте.

## Калибровка

Для каждого из четырёх датчиков сохранить базовый уровень без магнита и пик при проходе магнита. Центр метки определять по максимуму отклонения от базового уровня, направление — по порядку срабатываний каналов.
'''
GUIDE_OUT.write_text(guide, encoding="utf-8")
J4_WIRING_OUT.write_text(guide, encoding="utf-8")

shopping = '''# Что купить для J1 + J4

## Электроника

- Установлено будет **8× SS49E**: 4 на J1 и 4 на J4. Уже есть 6, поэтому минимум докупить 2; разумно купить 4 и оставить 2 запасных. Поиск: `Honeywell SS49E линейный аналоговый датчик Холла TO-92`.
- **2× ADS1115**, по одному на сустав. Поиск: `ADS1115 модуль АЦП 16 бит 4 канала I2C`.
- **2× магнит неодимовый D3x2 мм, аксиальная намагниченность**; лучше упаковку 10 шт. Поиск: `магнит неодимовый 3x2 мм диск аксиальный`.
- По желанию 8× керамический 100 нФ для локальной развязки питания у длинных проводов. Поиск: `конденсатор керамический 0.1 мкФ 100 нФ`.

## Крепёж двух суставов

- 8× M3×12 DIN 912.
- 8× M3×6 DIN 912.
- Тонкая Kapton/PET-плёнка 0,10–0,20 мм для поджима слишком тонких клонов корпуса.

## Провод

- От каждого сустава до панели: 6 жил — 3V3, GND, OUT0, OUT1, OUT2, OUT3.
- В панели: ADS1115 → TCA9548A → сенсорная ESP32 по I2C.
'''
SHOPPING_OUT.write_text(shopping, encoding="utf-8")
J4_SHOPPING_OUT.write_text(shopping, encoding="utf-8")

j4_guide = f'''# J4 ROLL V6 + QUAD HALL — что печатать

Главный единый файл: `{J4_PLATE_OUT.name}`.

В нём 9 тел: задний стакан, квадратный ключ, две половины передней рамки, два трубных спейсера, Hall-кассета, прижимное кольцо и магнитная втулка.

Габарит пластины: {j4_plate.extents[0]:.1f} × {j4_plate.extents[1]:.1f} мм. На столе 220×220 остаётся нормальный запас; brim у заднего стакана уже встроен в модель.

Клетка: 4× M5×80 + увеличенные шайбы M5 + стопорные гайки M5. Hall: 4× M3×12, 4× M3×6, 4× SS49E, 1× магнит D3×2.

Датчики и магнит устанавливать по инструкции `{J4_WIRING_OUT.name}` из этой же папки.
'''
J4_GUIDE_OUT.write_text(j4_guide, encoding="utf-8")

print("Generated:", ROOT)
print("Generated J4 package:", J4_ROOT)
