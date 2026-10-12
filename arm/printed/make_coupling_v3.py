# -*- coding: utf-8 -*-
"""
УЗЕЛ J2 v3 — под РЕАЛЬНОЕ железо (10.08): звено = труба 20x20x1.5, ось = пруток Д16Т Ø8,
KFL08 уже прикручен к стенке напрямую (диагонально, планка НЕ нужна).

1) coupling_v3_PETG.stl — МУФТА-ПЛАНКА: 26x46x8, сквозной D-бор 8.15/6.05 (вал входит
   на ~7.5мм — муфта ставится в 1мм от стенки скобы), 2 отв. М4 на (0,+-16) с цековками
   голов со стороны скобы. Болты М4x30 идут СКВОЗЬ трубу, гайки+шайбы на дальней грани.
   Момент держит D-профиль; пруток внутри трубы может упираться в тыл муфты — они
   вращаются вместе, это НЕ трение.
2) drill_jig_v3_PETG.stl — КОНДУКТОР на трубу: П-скоба (внутр. 20.4), направляющие
   отверстия: Ø8.2 на оси (обе щеки) + 2xØ4.3 на +-16 (обе щеки). Надел, зажал рукой,
   просверлил насквозь — все 3 отверстия точно по осям.
Печать: обе плашмя, PETG, слой 0.2, стенки 6, 100% (кондуктор можно 40%).
"""
import numpy as np, trimesh

def cyl(d,h,z0,x=0,y=0,sec=64):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c
def boxc(sx,sy,sz,x,y,z0):
    b=trimesh.creation.box(extents=[sx,sy,sz])
    b.apply_translation([x,y,z0+sz/2]); return b

BASE=r".\arm\printed"

# ---------- 1. МУФТА-ПЛАНКА ----------
W,L,T = 26.0,46.0,8.0
SHAFT_D,SHAFT_AF = 8.15,6.05
M4,CSK_D,CSK_H = 4.4,8.2,3.4
body = boxc(W,L,T,0,0,0)
cuts=[]
bore = cyl(SHAFT_D,T+2,-1)
f1 = boxc(SHAFT_D,(SHAFT_D-SHAFT_AF)/2+2,T+4,0,SHAFT_AF/2+((SHAFT_D-SHAFT_AF)/2+2)/2,-2)
f2 = f1.copy(); f2.apply_translation([0,-2*f1.center_mass[1],0])
cuts.append(trimesh.boolean.difference([bore,f1,f2]))
for s in (-1,1):
    cuts.append(cyl(M4,T+2,-1,0,s*16))
    cuts.append(cyl(CSK_D,CSK_H,-0.01,0,s*16))        # цековка головы со стороны скобы (низ)
m=trimesh.boolean.difference([body]+cuts)
m.export(BASE+r"\coupling_v3_PETG.stl")
print("МУФТА v3 | watertight:",m.is_watertight,"| ext:",np.round(m.extents,1))

# ---------- 2. КОНДУКТОР ----------
TU=20.4          # внутр. под трубу 20
WALL=5.0
JL=56.0          # длина кондуктора вдоль трубы
H=TU+2*WALL
jig = boxc(H,JL,TU+WALL,0,0,0)                       # внешний блок (низ открыт)
cav = boxc(TU,JL+2,TU+2,0,0,-1.99)                   # полость под трубу (открыта вниз)
cuts=[cav]
# направляющие: ось прутка по центру длины, болтовые на +-16 от неё
for x,y,d in [(0,0,8.3),(0,16,4.3),(0,-16,4.3)]:
    g=trimesh.creation.cylinder(radius=d/2,height=H+4,sections=48)
    g.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
    g.apply_translation([0,y,TU/2]); cuts.append(g)   # ровно на центре трубы
j=trimesh.boolean.difference([jig]+cuts)
j.export(BASE+r"\drill_jig_v3_PETG.stl")
print("КОНДУКТОР | watertight:",j.is_watertight,"| ext:",np.round(j.extents,1))
