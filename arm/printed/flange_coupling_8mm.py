# -*- coding: utf-8 -*-
"""
Временная ПЕЧАТНАЯ фланцевая муфта 8мм (PETG) для робо-руки.
Момент передаётся D-ПРОФИЛЕМ (вал O8 с 2 лысками 5.9), НЕ винтами.
Зажим: разрезной хомут, 2 болта М3х16 насквозь + гайки в карманах.
Фланец: 4 отв. на кресте BC16 + 4 отв. на диагонали BC22.63 -> попадают
в сетку 8мм скоб/балок goBILDA-типа (сверлить не надо, болты М4).
Модель в ОРИЕНТАЦИИ ДЛЯ ПЕЧАТИ: фланец на столе, хаб вверх.
В сборке переворачивается: хаб вниз (на вал), фланец сверху.
Запуск: python flange_coupling_8mm.py -> flange_coupling_8mm_PETG.stl
"""
import trimesh
import numpy as np

# ---------- ПАРАМЕТРЫ (мм) ----------
SHAFT_D   = 8.15    # бор под вал O8 (+0.15 посадка PETG)
SHAFT_AF  = 6.05    # между лысками (вал 5.9 +0.15)
MAG_D     = 6.6     # карман под штатный магнит O5 (+зазор)
# ХАБ КОМПАКТНЫЙ O20: головки М3 винтов редуктора (BC27) начинаются на R10.75 -
# всё вращающееся у стенки должно быть < R10.4. Хомут-болты ВНУТРИ габарита.
HUB_D     = 20.0    # наружный хаба (зона вращения у стенки!)
HUB_H     = 15.0    # высота хаба
NOSE_D    = 13.6    # НОСИК: проходит сквозь отв. 14мм стенки = опора скольжения
NOSE_L    = 3.3     # длина носика (стенка 2.5 + до ступицы, зазор 0.2)
FLG_X     = 26.0    # фланец прямоугольный (X - вдоль ушей)
FLG_Y     = 42.0    # вдоль линий крепежа
FLG_H     = 5.0     # толщина фланца
TOTAL_H   = FLG_H + HUB_H + NOSE_L # 23.3 (носик сверху при печати)
BORE_DEEP = 10.0    # глубина D-бора от торца носика (полный охват вала)
MAG_POCKET= TOTAL_H - BORE_DEEP    # карман магнита: от стола до дна бора
SLIT_W    = 2.0     # пропил хомута (от бора до края, одна сторона)
M3_HOLE   = 3.3
M3_R      = 6.4     # болты хомута: расстояние центра от оси (внутри O20!)
NUT_AF    = 5.7     # гайка М3 под ключ 5.5 (+0.2)
NUT_H     = 2.8
M4_HOLE   = 4.4     # отверстия фланца под М4
# крепёж на точках сетки 8мм: (+-8, +-16) - свободно от хаба и ушей,
# и это 2 параллельные линии с шагом 32 = ровно под 2 балки!

import sys
VERT = "--vert" in sys.argv          # версия для вертикальных узлов J1/J4: БЕЗ носика
if VERT:
    NOSE_L = 0.0
    TOTAL_H = FLG_H + HUB_H
    MAG_POCKET = TOTAL_H - BORE_DEEP
OUT = (r".\arm\printed\flange_coupling_8mm_VERT_PETG.stl" if VERT
       else r".\arm\printed\flange_coupling_8mm_PETG.stl")

def cyl(d, h, z0, x=0, y=0, sec=96):
    c = trimesh.creation.cylinder(radius=d/2, height=h, sections=sec)
    c.apply_translation([x, y, z0 + h/2])
    return c

def boxc(sx, sy, sz, x, y, z0):
    b = trimesh.creation.box(extents=[sx, sy, sz])
    b.apply_translation([x, y, z0 + sz/2])
    return b

# ---------- ТЕЛО (компактный split-collar, всё внутри O20) ----------
parts = [boxc(FLG_X, FLG_Y, FLG_H, 0, 0, 0),    # фланец на столе (прямоуг.)
         cyl(HUB_D, HUB_H, FLG_H)]              # хаб
if NOSE_L > 0:
    parts.append(cyl(NOSE_D, NOSE_L + 0.01, FLG_H + HUB_H))  # носик (в отв. 14мм стенки)
body = trimesh.boolean.union(parts)

cuts = []

# D-бор (вал входит с ВЕРХА печати = низ сборки): глубина BORE_DEEP
dbore = cyl(SHAFT_D, BORE_DEEP + 1, MAG_POCKET)
flat1 = boxc(SHAFT_D, (SHAFT_D - SHAFT_AF)/2 + 2, BORE_DEEP + 2, 0,
             SHAFT_AF/2 + ((SHAFT_D - SHAFT_AF)/2 + 2)/2, MAG_POCKET - 0.5)
flat2 = flat1.copy(); flat2.apply_translation([0, -2*flat1.center_mass[1], 0])
dvol = trimesh.boolean.difference([dbore, flat1, flat2])   # D-профиль как объём
cuts.append(dvol)

# карман магнита (сквозь фланец до дна бора)
cuts.append(cyl(MAG_D, MAG_POCKET + 0.1, -0.05))

# пропил хомута: от бора наружу с ОДНОЙ стороны (+X), верх..фланец
cuts.append(boxc(HUB_D/2 + 2, SLIT_W, HUB_H + 0.1, (HUB_D/2 + 2)/2 + 1.5, 0, FLG_H + 0.05))

# 2 стяжных болта М3 ВНУТРИ габарита O20: поперёк пропила (вдоль Y) на x=M3_R
for zc in (FLG_H + 4.0, FLG_H + 11.0):
    h = trimesh.creation.cylinder(radius=M3_HOLE/2, height=HUB_D + 2, sections=32)
    h.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
    h.apply_translation([M3_R, 0, zc])
    cuts.append(h)
    # цековка головки (D5.8) с +Y стороны и карман гайки с -Y
    cb = trimesh.creation.cylinder(radius=2.9, height=3, sections=32)
    cb.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
    yc = float(np.sqrt(max((HUB_D/2)**2 - M3_R**2, 1)))   # поверхность хаба у x=M3_R
    cb.apply_translation([M3_R, yc - 1.2, zc])
    cuts.append(cb)
    n = trimesh.creation.cylinder(radius=NUT_AF/np.sqrt(3), height=NUT_H, sections=6)
    n.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
    n.apply_translation([M3_R, -(yc - NUT_H/2 - 1.0), zc])
    cuts.append(n)

# отверстия фланца: (+-8, +-16) - точки сетки 8мм скоб/балок
for sx in (-1, 1):
    for sy in (-1, 1):
        cuts.append(cyl(M4_HOLE, FLG_H + 2, -1, sx*8, sy*16, sec=32))

part = trimesh.boolean.difference([body] + cuts)
part.export(OUT)
print("OK ->", OUT)
print("watertight:", part.is_watertight, "| размер XYZ:", np.round(part.extents, 2))
