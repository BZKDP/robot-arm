# -*- coding: utf-8 -*-
"""Печатный лист J1+J2 одним STL (Ender 3 V3 SE, стол 220x220):
   1) муфта VERT (J1, без носика)  2) муфта с носиком (J2)  3) проставка (J2)"""
import trimesh, numpy as np
BASE = r".\arm\printed"
a = trimesh.load(BASE + r"\flange_coupling_8mm_VERT_PETG.stl")
b = trimesh.load(BASE + r"\flange_coupling_8mm_PETG.stl")
c = trimesh.load(BASE + r"\gearbox_spacer_5mm_PETG.stl")
def ground(m):  # положить на z=0
    m.apply_translation([-m.bounds[0][0], -m.bounds[0][1], -m.bounds[0][2]]); return m
a, b, c = ground(a), ground(b), ground(c)
a.apply_translation([0, 0, 0])       # 26x42
b.apply_translation([46, 0, 0])      # 26x42, зазор 20мм
c.apply_translation([92, 0, 0])      # диск 52
plate = trimesh.util.concatenate([a, b, c])
plate.export(BASE + r"\PLATE_J1J2_PETG.stl")
print("OK -> PLATE_J1J2_PETG.stl | габарит:", np.round(plate.extents, 1),
      "| watertight-части:", a.is_watertight, b.is_watertight, c.is_watertight)
