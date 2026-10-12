# -*- coding: utf-8 -*-
"""
Адаптер РЕДУКТОР(выход) -> goBILDA U-скоба.  (роборука J2)
Замеры пользователя 03.08.2026:
  вал Ø8 (лыска 5.9, L=16), выступ-подшипник Ø22 (торчит ~1мм), хаба нет,
  на выходном торце 4x M3 по КРУГУ Ø27.5 (крест N/E/S/W).
Схема адаптера:
  - Ø22.4 x1.8 карман-центровка на выступ (соосность держит он).
  - 4x M3 сквозь на BC27.5 (крест) + цековка головки со стороны скобы (заподлицо).
  - центр Ø9 сквозь под вал.
  - со стороны скобы: бобышка Ø13.8 x3 заходит в Ø14 скобы (центровка) +
    4x M4 на (±16,±16) = узлы сетки goBILDA 8мм (диагональ, не мешают М3-кресту).
Печать: плоской (сторона редуктора) вниз, PETG/PLA, слой 0.2, стенки 4, 40%.
"""
import trimesh, numpy as np

OUT   = r".\arm\printed\gearbox_adapter_J2.stl"
D_OUT = 54.0
T     = 5.0
PILOT_D, PILOT_DEEP = 22.4, 1.8      # карман под выступ Ø22
SHAFT_D = 9.0
GB_BC = 27.5                         # круг М3 редуктора
M3_D, M3_HEAD_D, M3_HEAD_H = 3.4, 6.2, 3.0
REG_D, REG_H = 13.8, 3.0             # бобышка-центровка в Ø14 скобы
M4_D = 4.5
M4_POS = 16.0                        # (±16,±16) сетка goBILDA

def cyl(d,h,z0,x=0,y=0,sec=96):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c

# тело + бобышка-центровка (сторона скобы = верх, z=T..T+REG_H)
body = trimesh.boolean.union([cyl(D_OUT,T,0), cyl(REG_D,REG_H,T)])

cuts=[cyl(SHAFT_D, T+REG_H+2, -1),                 # вал насквозь
      cyl(PILOT_D, PILOT_DEEP+0.01, -0.005)]       # карман выступа (низ = сторона редуктора)

# 4x M3 крестом (совпадает с редуктором), головка утоплена со стороны скобы
for a in (0,90,180,270):
    x,y = (GB_BC/2)*np.cos(np.radians(a)), (GB_BC/2)*np.sin(np.radians(a))
    cuts.append(cyl(M3_D, T+REG_H+2, -1, x, y, 32))
    cuts.append(cyl(M3_HEAD_D, M3_HEAD_H+1, T-M3_HEAD_H, x, y, 32))   # цековка сверху

# 4x M4 к скобе на (±16,±16) + карман гайки снизу (сторона редуктора)
for sx in (-1,1):
    for sy in (-1,1):
        x,y = sx*M4_POS, sy*M4_POS
        cuts.append(cyl(M4_D, T+REG_H+2, -1, x, y, 32))
        n=trimesh.creation.cylinder(radius=7.6/np.sqrt(3)/2*2, height=3.0, sections=6)  # гайка М4 s7
        n=trimesh.creation.cylinder(radius=7.6/2/np.cos(np.pi/6), height=3.0, sections=6)
        n.apply_translation([x,y,3.0/2-0.01]); cuts.append(n)

part = trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->", OUT, "| watertight:", part.is_watertight, "| ext:", np.round(part.extents,1))
