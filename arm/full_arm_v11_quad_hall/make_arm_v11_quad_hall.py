# -*- coding: utf-8 -*-
"""Upgrade the detailed V10 arm viewer to the final quad-Hall J1/J4 layout."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
ARM = ROOT.parent
SOURCE = ARM / "full_arm_v10_detail" / "ARM_V10_FULL_DETAIL_INTERACTIVE_3D.html"
OUT = ROOT / "ARM_V11_FULL_DETAIL_QUAD_HALL_INTERACTIVE_3D.html"
README = ROOT / "ARM_V11_QUAD_HALL_CHANGES_RU.md"

html = SOURCE.read_text(encoding="utf-8")
html = html.replace("ARM V10", "ARM V11")
html = html.replace("Полная детализация V10", "Полная детализация V11")
html = html.replace("Робо-рука v10", "Робо-рука v11")
html = html.replace("Рука v10", "Рука v11")
html = html.replace(
    "Основа v8: реальные отверстия, муфты и крепёж. Добавлены новый J3, перенесённый roll, клетки M5×80 и датчики.",
    "Полная механика руки и окончательная схема индекса: по 4×SS49E на J1 и J4, один магнит на каждый сустав.",
)

# Annulus extruded along the arm's local Y axis.
annulus_helper = r'''function annulusY(od,id,h,m,g,y){const s=new THREE.Shape();s.absarc(0,0,od/2,0,Math.PI*2);const p=new THREE.Path();p.absarc(0,0,id/2,0,Math.PI*2,true);s.holes.push(p);const q=new THREE.Mesh(new THREE.ExtrudeGeometry(s,{depth:h,bevelEnabled:false}),m);q.rotation.x=-Math.PI/2;q.position.y=y;g.add(q);return q}
'''
html, count = re.subn(
    r"(function label3\(.*?return s\}\n)",
    lambda match: match.group(1) + annulus_helper,
    html,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("Could not insert annulusY helper")

# BOM descriptions.
html = re.sub(
    r"hallJ1:\{n:'.*?',d:'.*?',s:'.*?'\},",
    "hallJ1:{n:'J1: QUAD INDEX — 4×SS49E',d:'Четыре неподвижных аналоговых датчика через 90°, один магнит D3×2 вращается вместе с U-скобой. Один ADS1115 читает четыре выхода.',s:'🖨 v3'},",
    html,
    count=1,
)
html = re.sub(
    r"rollCage:\{n:'.*?',d:'.*?',s:'.*?'\},",
    "rollCage:{n:'J4 roll — клетка M5×80',d:'Задний стакан, квадратный ключ, разъёмная передняя рамка и четыре внешних M5×80.',s:'🖨 v6'},\n hallJ4:{n:'J4: QUAD INDEX — 4×SS49E',d:'Та же кассета CM36, что на J1: четыре позиции на оборот и отдельный ADS1115.',s:'🖨 v3'},",
    html,
    count=1,
)

j1_quad = r'''// Неподвижная QUAD-Hall кассета J1: четыре SS49E через 90 градусов.
const hallJ1=G('hallJ1');scene.add(hallJ1);
annulusY(46,22.8,11.8,mat.hall,hallJ1,103.0);annulusY(45.2,23.6,.9,mat.newj,hallJ1,114.8);
for(const a of [45,135,225,315]){const t=a*Math.PI/180,x=15.56*Math.cos(t),z=15.56*Math.sin(t);const s=box(4.6,1.8,3.5,(a===45||a===225)?mat.sensorA:mat.sensorB,x,113.9,z,hallJ1);s.rotation.y=-(a+90)*Math.PI/180;for(const o of [-1.30,0,1.30]){const tx=x-Math.sin(t)*o+Math.cos(t)*5.1,tz=z+Math.cos(t)*o+Math.sin(t)*5.1;wireBetween(hallJ1,[tx,113.2,tz],[tx,108.5,tz],.28,mat.wire)}}
for(const a of [0,90,180,270]){const t=a*Math.PI/180;boltY(hallJ1,3,12,13.75*Math.cos(t),109,13.75*Math.sin(t),-1);boltY(hallJ1,3,6,19.7*Math.cos(t),115.5,19.7*Math.sin(t),-1)}
const hallLab=label3('J1 · 4× SS49E · QUAD',0x63e6a1,260);hallLab.position.set(58,116,18);hallJ1.add(hallLab);'''
html, count = re.subn(
    r"//[^\n]*Hall[^\n]*J1[^\n]*\nconst hallJ1=G\('hallJ1'\);.*?hallJ1\.add\(hallLab\);",
    j1_quad,
    html,
    count=1,
    flags=re.S,
)
if count != 1:
    # Fallback uses only stable ASCII identifiers.
    html, count = re.subn(
        r"const hallJ1=G\('hallJ1'\);.*?hallJ1\.add\(hallLab\);",
        j1_quad,
        html,
        count=1,
        flags=re.S,
    )
if count != 1:
    raise RuntimeError("Could not replace J1 Hall geometry")

# Move the J1 magnet to the real existing U-bottom hole (11,11), R15.56.
html, count = re.subn(
    r"cylY\(3,2,mat\.mag,0,114\.8,15\.6,bJ1\);",
    "cylY(3,2,mat.mag,11,116.8,11,bJ1);",
    html,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not move J1 magnet")

# Insert the same fixed cartridge on J4 and put its magnet into the rotating
# output group.  The roll cage itself remains unchanged.
j4_old = r""" const gb=G('gb71');root.add(gb);cylY(36,35,mat.gb,0,84,0,gb);cylY(22,1.6,mat.face,0,102.3,0,gb);cylY(8,16,mat.shaft,0,110,0,gb);
 const mc=G('mcoup');root.add(mc);coupY(mc,104);const rot=new THREE.Group();rot.position.set(0,116,0);root.add(rot);"""
j4_new = r""" const gb=G('gb71');root.add(gb);cylY(36,35,mat.gb,0,84,0,gb);cylY(22,1.6,mat.face,0,102.3,0,gb);cylY(8,16,mat.shaft,0,110,0,gb);
 const hall=G('hallJ4');root.add(hall);annulusY(46,22.8,11.8,mat.hall,hall,102.3);annulusY(45.2,23.6,.9,mat.newj,hall,114.1);
 for(const a of [45,135,225,315]){const t=a*Math.PI/180,x=15.56*Math.cos(t),z=15.56*Math.sin(t);const s=box(4.6,1.8,3.5,(a===45||a===225)?mat.sensorA:mat.sensorB,x,113.2,z,hall);s.rotation.y=-(a+90)*Math.PI/180;for(const o of [-1.30,0,1.30]){const tx=x-Math.sin(t)*o+Math.cos(t)*5.1,tz=z+Math.cos(t)*o+Math.sin(t)*5.1;wireBetween(hall,[tx,112.5,tz],[tx,108,tz],.28,mat.wire)}}
 for(const a of [0,90,180,270]){const t=a*Math.PI/180;boltY(hall,3,12,13.75*Math.cos(t),108.2,13.75*Math.sin(t),-1);boltY(hall,3,6,19.7*Math.cos(t),114.8,19.7*Math.sin(t),-1)}
 const hLab=label3('J4 · 4× SS49E · QUAD',0x63e6a1,260);hLab.position.set(-65,116,17);hall.add(hLab);
 const mc=G('mcoup');root.add(mc);coupY(mc,104);const rot=new THREE.Group();rot.position.set(0,116,0);root.add(rot);cylY(3,2,mat.mag,11,.8,11,rot);"""
if j4_old not in html:
    raise RuntimeError("Could not find J4 gearbox block")
html = html.replace(j4_old, j4_new, 1)

html = html.replace(
    "'pcb','rollCage','chan5'",
    "'pcb','rollCage','hallJ4','chan5'",
    1,
)
html = html.replace(
    "['hallJ1','pcb'].includes(g.userData.bom)",
    "['hallJ1','hallJ4','pcb'].includes(g.userData.bom)",
    1,
)
html = html.replace(
    "двойной Hall-индекс J1",
    "QUAD Hall-индексы J1 и J4",
)

OUT.write_text(html, encoding="utf-8")
README.write_text(
    """# ARM V11 — изменения датчиков

- J1: 4×SS49E через 90°, один вращающийся D3×2.
- J4: идентичная кассета 4×SS49E, один вращающийся D3×2.
- На каждый сустав предусмотрен ADS1115; оба идут через TCA9548A во вторую ESP32.
- Печатная механика находится в `printed/hall_quad_index_v3` и `printed/j4_roll_quad_hall_v6`.
""",
    encoding="utf-8",
)
print(OUT)
