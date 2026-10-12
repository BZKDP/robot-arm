# -*- coding: utf-8 -*-
"""
Переходник-плита: КОРПУС редуктора CM36  <->  U-кронштейн / балка.
Через центр проходит выходной вал (к хабу на другой стороне).

!!! ВСЕ РАЗМЕРЫ НИЖЕ — ЗАГЛУШКИ (типовые для NEMA17-планетарки) !!!
Точные числа подставим, когда замеришь редуктор/кронштейн штангелем.
Меняй параметры здесь и запусти:  python adapter_plate.py
"""
import trimesh, numpy as np

# ---------- ПАРАМЕТРЫ (мм) — ПОКА ЗАГЛУШКИ ----------
PLATE       = 64.0   # сторона квадратной плиты
THK         = 6.0    # толщина плиты
SHAFT_BORE  = 9.0    # сквозное отверстие под выходной вал (Ø8 + зазор)

PILOT_D     = 36.5   # проточка-центровка под фланец редуктора (Ø корпуса)
PILOT_DEPTH = 2.5    # глубина проточки

GB_BCD      = 30.0   # окружность крепёжных отверстий редуктора
GB_HOLE     = 3.4    # Ø отверстий редуктора (M3 clearance)
GB_N        = 4      # сколько отверстий у редуктора

STR_OFF     = 24.0   # смещение крепёжных отв. к кронштейну от центра (квадрат)
STR_HOLE    = 4.5    # Ø отверстий к кронштейну (M4 clearance)

OUT = r".\arm\adapter_plate_PREVIEW.stl"
# ----------------------------------------------------

def cyl(d, h, z0, x=0.0, y=0.0):
    c = trimesh.creation.cylinder(radius=d/2.0, height=h, sections=96)
    c.apply_translation([x, y, z0 + h/2.0])
    return c

# плита: низ на z=0 (сторона к кронштейну), верх на z=THK (сторона к редуктору)
plate = trimesh.creation.box(extents=[PLATE, PLATE, THK])
plate.apply_translation([0, 0, THK/2.0])

cuts = []
cuts.append(cyl(SHAFT_BORE, THK + 2, -1))                    # сквозной вал
cuts.append(cyl(PILOT_D, PILOT_DEPTH + 1, THK - PILOT_DEPTH))# проточка на стороне редуктора

for i in range(GB_N):                                        # отверстия редуктора
    a = 2*np.pi*i/GB_N + np.pi/GB_N
    cuts.append(cyl(GB_HOLE, THK + 2, -1,
                    GB_BCD/2*np.cos(a), GB_BCD/2*np.sin(a)))

for sx in (-1, 1):                                           # отверстия к кронштейну
    for sy in (-1, 1):
        cuts.append(cyl(STR_HOLE, THK + 2, -1, sx*STR_OFF, sy*STR_OFF))

adapter = trimesh.boolean.difference([plate] + cuts)
adapter.export(OUT)
print("OK ->", OUT)
print("watertight:", adapter.is_watertight, "| verts:", len(adapter.vertices))
print("габарит (мм):", np.round(adapter.extents, 2))
