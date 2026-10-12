# -*- coding: utf-8 -*-
"""
Адаптер редуктор->goBILDA-скоба, V2 (крепёж за 3 отверстия Ø14, шаг 24мм).
Замеры пользователя: выступ Ø22 (торчит 1мм), вал Ø8/L16, 4xM3 круг Ø27.5,
скоба: ряд отверстий Ø14, центр-центр соседних = 24мм.
Схема:
  СТОРОНА РЕДУКТОРА (низ, z=0): карман Ø22.4x1.8 (центровка на выступ) +
     4xM3 сквозь на круге Ø27.5 крестом (в резьбу редуктора) + цековка головок сверху.
  СТОРОНА СКОБЫ (верх, z=T): 3 бобышки Ø13.8xBOSS_H в отверстия Ø14 (шаг 24):
     центральная с бором Ø9 (вал насквозь), 2 крайние с бором M4 (болт+гайка за скобой).
  Гайка M4 (s7) в карман на низу у крайних бобышек (снаружи габарита редуктора).
Печать: сторона редуктора (плоская) вниз, бобышки вверх; PLA/PETG слой 0.2 стенки4 40%.
"""
import trimesh, numpy as np
from shapely.geometry import box as sbox

OUT = r".\arm\printed\gearbox_adapter_J2_v2.stl"
T        = 5.0
BOSS_D   = 13.8
BOSS_H   = 4.0
PITCH    = 24.0            # шаг Ø14 отверстий скобы
PILOT_D, PILOT_DEEP = 22.4, 1.8
SHAFT_D  = 9.0
GB_BC    = 27.5           # круг M3 редуктора
M3_D, M3_HEAD_D, M3_HEAD_H = 3.4, 6.2, 3.0
M4_D     = 4.3
NUT_AF, NUT_H = 7.2, 3.0  # гайка M4 под ключ 7

def cyl(d,h,z0,x=0,y=0,sec=64):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c

def hexnut(af,h,z0,x,y):
    n=trimesh.creation.cylinder(radius=af/np.sqrt(3),height=h,sections=6)
    n.apply_translation([x,y,z0+h/2]); return n

# --- тело: скруглённый прямоугольник 68x40, толщина T ---
outline = sbox(-28,-14,28,14).buffer(6.0, join_style=1)
body = trimesh.creation.extrude_polygon(outline, T)

# --- 3 бобышки на верх (сторона скобы) ---
parts=[body]
for cx in (-PITCH,0,PITCH):
    parts.append(cyl(BOSS_D, BOSS_H, T-0.01, cx, 0))
solid = trimesh.boolean.union(parts)

cuts=[]
# центр: карман под выступ (низ) + вал насквозь
cuts.append(cyl(PILOT_D, PILOT_DEEP+0.01, -0.005))
cuts.append(cyl(SHAFT_D, T+BOSS_H+2, -1, 0, 0))
# 4xM3 крест Ø27.5 (в редуктор), головка утоплена со стороны скобы (верх)
for a in (0,90,180,270):
    x,y=(GB_BC/2)*np.cos(np.radians(a)),(GB_BC/2)*np.sin(np.radians(a))
    cuts.append(cyl(M3_D, T+2, -1, x, y, 32))
    cuts.append(cyl(M3_HEAD_D, M3_HEAD_H+2, T-M3_HEAD_H, x, y, 32))
# крайние бобышки: бор M4 насквозь + карман гайки снизу
for cx in (-PITCH, PITCH):
    cuts.append(cyl(M4_D, T+BOSS_H+2, -1, cx, 0))
    cuts.append(hexnut(NUT_AF, NUT_H, -0.005, cx, 0))

part = trimesh.boolean.difference([solid]+cuts)
part.export(OUT)
print("OK ->", OUT, "| watertight:", part.is_watertight, "| ext:", np.round(part.extents,1))
