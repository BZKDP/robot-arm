# -*- coding: utf-8 -*-
"""
СТАКАН КИСТИ: торец трубы J5 (20x20) -> зад мотора NEMA14 (J6).
Как roll_mount, но под NEMA14: фланец 42x42x5, крепёж 26x26 Ø3.4 (сквозные винты
корпуса NEMA14, заменить на М3x35-40), центр Ø23 (провода), карман 20.4 глубиной 28,
2 отв. М4 сквозь трубу (+ втулки!).
Печать: фланцем вниз, без поддержек.
"""
import numpy as np, trimesh
OUT=r".\arm\printed\wrist_mount_N14_PETG.stl"
def cyl(d,h,z0,x=0,y=0,sec=48):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c
def boxc(sx,sy,sz,x,y,z0):
    b=trimesh.creation.box(extents=[sx,sy,sz]); b.apply_translation([x,y,z0+sz/2]); return b

FL=42.0; FT=5.0; POCKET=20.4; WALL=4.5; DEPTH=28.0
body=trimesh.boolean.union([boxc(FL,FL,FT,0,0,0),
                            boxc(POCKET+2*WALL,POCKET+2*WALL,DEPTH,0,0,FT-0.01)])
cuts=[boxc(POCKET,POCKET,DEPTH+2,0,0,FT+1.5), cyl(23,FT+4,-1)]
for sx in (-1,1):
    for sy in (-1,1):
        cuts.append(cyl(3.4,FT+4,-1,sx*13,sy*13,32))          # NEMA14: 26x26 М3
for s in (-1,1):
    h=trimesh.creation.cylinder(radius=2.2,height=POCKET+2*WALL+4,sections=32)
    h.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
    h.apply_translation([0,0,FT+8+(8 if s>0 else 0)])
    cuts.append(h)
cuts.append(boxc(12,POCKET+2*WALL+4,8,0,0,FT+16))             # окно провода
part=trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->",OUT,"| watertight:",part.is_watertight,"| ext:",np.round(part.extents,1))
