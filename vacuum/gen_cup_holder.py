# -*- coding: utf-8 -*-
"""
Универсальный держатель вакуумной присоски (L-кронштейн).
- Отверстие под панельную резьбу присоски (по умолчанию M6 -> 6.5 мм), фиксируется родной гайкой присоски.
- Вертикальная стенка с 2x M3 для крепления к захвату руки / серво-кронштейну / уголку.
- Косынка-ребро для жёсткости.
Печать: PLA/PETG, 0.2 мм, 3 периметра, 20-30% заполнение. Без поддержек.
Меняй параметры ниже и запускай:  python gen_cup_holder.py
"""
import os
import numpy as np
import trimesh

# ---------- ПАРАМЕТРЫ (мм) ----------
T          = 5.0    # толщина стенок
ARM_LEN    = 38.0   # вылет горизонтальной полки (под присоску)
ARM_W      = 16.0   # ширина детали
VERT_H     = 26.0   # высота вертикальной стенки
CUP_HOLE_D = 6.5    # отверстие под резьбу присоски (M6=6.5, M5=5.3)
CUP_X      = ARM_LEN - 11.0  # положение присоски от угла
M3         = 3.4    # отверстия крепления
MNT_Z1     = 8.0    # высота 1-го крепёжного отверстия
MNT_Z2     = 18.0   # высота 2-го крепёжного отверстия
GUS        = 12.0   # размер косынки-ребра
OUT_DIR    = os.path.dirname(os.path.abspath(__file__))
# ------------------------------------

def box(sx, sy, sz, pos):
    b = trimesh.creation.box(extents=(sx, sy, sz))
    b.apply_translation(pos)
    return b

def cyl_z(r, h, pos):
    c = trimesh.creation.cylinder(radius=r, height=h, sections=48)
    c.apply_translation(pos)
    return c

def cyl_x(r, h, pos):
    c = trimesh.creation.cylinder(radius=r, height=h, sections=48)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    c.apply_translation(pos)
    return c

# тело: горизонтальная полка + вертикальная стенка
horiz = box(ARM_LEN, ARM_W, T, (ARM_LEN/2, 0, T/2))
vert  = box(T, ARM_W, VERT_H, (T/2, 0, VERT_H/2))

# косынка (треугольная призма) для жёсткости
tri = np.array([[T, T], [T + GUS, T], [T, T + GUS]])
gusset = trimesh.creation.extrude_polygon(
    trimesh.path.polygons.Polygon(tri), height=ARM_W)
gusset.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]))
gusset.apply_translation((0, ARM_W/2, 0))

body = trimesh.boolean.union([horiz, vert, gusset], engine='manifold')

# отверстия
holes = [
    cyl_z(CUP_HOLE_D/2, T*3, (CUP_X, 0, T/2)),
    cyl_x(M3/2, T*3, (T/2, 0, MNT_Z1)),
    cyl_x(M3/2, T*3, (T/2, 0, MNT_Z2)),
]
part = trimesh.boolean.difference([body] + holes, engine='manifold')

out = os.path.join(OUT_DIR, "cup_holder_arm.stl")
part.export(out)
print("STL:", out)
print("watertight:", part.is_watertight)
print("bbox (мм):", np.round(part.bounds[1] - part.bounds[0], 1))
print("объём (см^3):", round(part.volume/1000.0, 1))
