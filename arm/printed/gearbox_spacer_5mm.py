# -*- coding: utf-8 -*-
"""
ПРОСТАВКА 5мм: редуктор CM36 <-> стенка U-скобы БЕЗ СВЕРЛЕНИЯ скобы.
- карман O20 x4.5 под неподвижную ступицу (она не проходит в отв. 14мм)
- 4x M3 ПОТАЙ на BC27 -> в штатные резьбы торца редуктора (заподлицо!)
- 4x O4.3 на кресте 32мм: (+-16,0),(0,+-16) = СЕТКА 8мм скобы -> М4+гайки
- центральное сквозное O14.5 (совпадает с отверстием стенки, проход носика муфты)
Печать: плоской стороной вниз. PETG, 100%, слой 0.2.
"""
import trimesh, numpy as np

D_OUT   = 52.0   # внешний диаметр диска
T       = 5.0    # толщина
POCKET_D= 20.4   # карман ступицы O19
POCKET_T= 4.5
THRU_D  = 14.5   # сквозное (= отверстию стенки)
GB_BC   = 25.2   # резьбы торца редуктора — ЗАМЕРЕНО штангелем 02.08 (25.2, М3)
M3_D    = 3.4
CSK_D   = 6.4    # потай конус под M3
GRID    = 16.0   # крест сетки скобы
M4_D    = 4.4

OUT = r".\arm\printed\gearbox_spacer_5mm_PETG.stl"

def cyl(d,h,z0,x=0,y=0,sec=96):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c

body = cyl(D_OUT, T, 0)
cuts = [cyl(THRU_D, T+2, -1),                 # сквозной проход
        cyl(POCKET_D, POCKET_T+0.01, T-POCKET_T)]  # карман ступицы (сторона редуктора = верх)
for k in range(4):                             # M3 утопленная головка на BC27
    a=np.radians(45+90*k); x,y=GB_BC/2*np.cos(a),GB_BC/2*np.sin(a)
    cuts.append(cyl(M3_D, T+2, -1, x, y, 32))
    cuts.append(cyl(CSK_D, 1.9, -0.05, x, y, 32))   # цековка со стороны стенки
for k in range(4):                             # M4 крест 32 (сетка скобы)
    a=np.radians(90*k); cuts.append(cyl(M4_D, T+2, -1, GRID*np.cos(a), GRID*np.sin(a), 32))

part = trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->", OUT, "| watertight:", part.is_watertight, "| ext:", np.round(part.extents,2))
