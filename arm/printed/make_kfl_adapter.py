# -*- coding: utf-8 -*-
"""
ПЛАНКА KFL08 -> стенка goBILDA-скобы (крепёж KFL 37мм НЕ совпадает с сеткой 8мм!).
Пластина 64x28x6:
  - 2x Ø4.4 на (+-18.5, 0) под болты KFL08, с ШЕСТИГРАННЫМИ гнёздами гаек M4
    заподлицо со стороны стенки (гайки не мешают прилеганию);
  - поле крепёжных Ø4.4 по сетке 8мм: (+-16,0), (+-16,+-8), (0,+-8), (+-8,+-8) —
    вкручивай те, что совпали с реальными отверстиями стенки (болт изнутри скобы,
    гайка со стороны планки в цековке Ø8);
  - центр Ø10 — проход прутка-оси Ø8 в KFL08.
Печать: плашмя, PETG/PLA, слой 0.2, стенки 4, 60%.
"""
import numpy as np, trimesh

OUT=r".\arm\printed\kfl_adapter_v2_PETG.stl"
W,Hh,T=64.0,28.0,6.0
def cyl(d,h,z0,x=0,y=0,sec=48):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c

body=trimesh.creation.box(extents=[W,Hh,T]); body.apply_translation([0,0,T/2])
cuts=[cyl(10,T+2,-1)]
for s in (-1,1):                                # KFL08: болт + гнездо гайки к стенке
    cuts.append(cyl(4.4,T+2,-1,s*18.5,0))
    n=cyl(8.4,3.2,-0.01,s*18.5,0,6); cuts.append(n)
for x,y in [(-16,0),(16,0),(-16,8),(16,8),(-16,-8),(16,-8),(0,8),(0,-8),(-8,8),(8,8),(-8,-8),(8,-8)]:
    cuts.append(cyl(4.4,T+2,-1,x,y))
    cuts.append(cyl(8.2,2.6,T-2.6+0.01,x,y))     # цековка гайки/головки со стороны KFL
part=trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->",OUT,"| watertight:",part.is_watertight,"| ext:",np.round(part.extents,1))
