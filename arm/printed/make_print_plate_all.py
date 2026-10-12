# -*- coding: utf-8 -*-
"""
ЕДИНЫЙ ЛИСТ ПЕЧАТИ роборуки (J2 + roll + J5) -> PLATE_ROBOARM_ALL.stl
Ориентации: кондуктор ПЕРЕВЁРНУТ отверстием вверх (иначе мост 20мм провисает),
остальное — в своей печатной ориентации (плоской/фланцем вниз). Всё на z=0.
Раскладка: полки, зазор 7мм, влезает в 210x210.
"""
import numpy as np, trimesh
BASE=r".\arm\printed"
def load(name): return trimesh.load(BASE+"\\"+name)

items=[]
def add(name, n=1, flipX=False, label=""):
    for _ in range(n):
        m=load(name).copy()
        if flipX:
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
        m.apply_translation([-m.bounds[0][0],-m.bounds[0][1],-m.bounds[0][2]])  # на z=0, угол в 0
        items.append((label or name, m))

add("gearbox_adapter_J2_v2.stl",2,label="adapter")   # ОБА: J2 и J5
add("flange_bridge_PETG.stl",2,label="bridge")
add("drill_jig_v3_PETG.stl",1,flipX=True,label="drill_jig(flip)")
add("roll_mount_PETG.stl",1,label="roll_cup")
add("wrist_mount_N14_PETG.stl",1,label="wrist_cup_N14")
add("as5600_bracket_PETG.stl",2,label="as5600_bracket")
add("tube_spacers_x2_PETG.stl",3,label="spacers")   # 6 втулок: J2 труба, roll стакан, J5 труба

# полочная раскладка
GAP=7.0; MAXW=210.0
placed=[]; x=0; y=0; rowH=0
# сортируем по убыванию глубины, чтобы плотнее
items.sort(key=lambda it: -(it[1].extents[1]))
for name,m in items:
    w,d=m.extents[0],m.extents[1]
    if x>0 and x+w>MAXW:
        x=0; y+=rowH+GAP; rowH=0
    m.apply_translation([x,y,0])
    placed.append(m)
    x+=w+GAP; rowH=max(rowH,d)

plate=trimesh.util.concatenate(placed)
b=plate.bounds
plate.apply_translation([-(b[0][0]+b[1][0])/2,-(b[0][1]+b[1][1])/2,0])  # центр стола
plate.export(BASE+r"\PLATE_ROBOARM_ALL.stl")
print("OK -> PLATE_ROBOARM_ALL.stl")
print("габарит XY:", np.round(plate.extents[:2],0), "| высота:", round(plate.extents[2],1),
      "| деталей:", len(placed))
