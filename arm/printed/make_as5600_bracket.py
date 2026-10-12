# -*- coding: utf-8 -*-
"""
КОЗЫРЁК AS5600 (x2): садится на болты ушей подшипника-ромба (Ø отв. 4.3 на межцентре 36),
под гайки. Столбики поднимают площадку над обоймой (обойма+ступица ~12.4 от стенки),
плата 20x20 ложится на площадку чипом ВНИЗ напротив магнита в торце прутка.
База: полоса 46x12x3 -> столбики к z=11.5 -> площадка 34x18x2 с окном 11x11 под чип
и 4 отв. Ø2.2 (сетка 16x16) под винтики платы (или двусторонний скотч).
Печать плашмя; мост площадки 22мм — PETG мостит легко.
"""
import numpy as np, trimesh
OUT=r".\arm\printed\as5600_bracket_PETG.stl"
def cyl(d,h,z0,x=0,y=0,sec=40):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c
def boxc(sx,sy,sz,x,y,z0):
    b=trimesh.creation.box(extents=[sx,sy,sz]); b.apply_translation([x,y,z0+sz/2]); return b

parts=[boxc(46,12,3,0,0,0),                       # полоса на уши (отв. на +-18)
       boxc(4,12,8.5,13,0,3-0.01),                # столбики
       boxc(4,12,8.5,-13,0,3-0.01),
       boxc(34,18,2,0,0,11.5-0.02)]               # площадка платы
body=trimesh.boolean.union(parts)
cuts=[cyl(4.3,5,-1,18,0), cyl(4.3,5,-1,-18,0)]    # на болты ушей
cuts.append(boxc(11,11,4,0,0,10.5))               # окно под чип (магнит смотрит сквозь)
for sx in (-1,1):
    for sy in (-1,1): cuts.append(cyl(2.2,6,9,sx*8,sy*8,24))   # винтики платы М2
part=trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->",OUT,"| watertight:",part.is_watertight,"| ext:",np.round(part.extents,1))
