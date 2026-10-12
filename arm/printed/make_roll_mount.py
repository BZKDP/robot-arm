# -*- coding: utf-8 -*-
"""
СТАКАН ROLL-УЗЛА: торец трубы 20x20 -> зад мотора NEMA17.
- квадрокарман 20.4x20.4 глубиной 32 (труба входит), 2 отв. М4 сквозь (болты через трубу);
- фланец 50x50x5: 4 отв. Ø3.2 по квадрату 31x31 (штатные сквозные винты NEMA17,
  заменить на М3x45-50 — идут сквозь фланец в корпус мотора) + центр Ø23 (провода/вентиляция);
- окно сбоку кармана под выход провода трубной проводки.
Печать: фланцем вниз, PETG, слой 0.2, стенки 5, 60-100%.
"""
import numpy as np, trimesh

OUT=r".\arm\printed\roll_mount_PETG.stl"
def cyl(d,h,z0,x=0,y=0,sec=48):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c
def boxc(sx,sy,sz,x,y,z0):
    b=trimesh.creation.box(extents=[sx,sy,sz])
    b.apply_translation([x,y,z0+sz/2]); return b

FL=50.0; FT=5.0; POCKET=20.4; WALL=4.5; DEPTH=32.0
body=trimesh.boolean.union([
    boxc(FL,FL,FT,0,0,0),
    boxc(POCKET+2*WALL,POCKET+2*WALL,DEPTH,0,0,FT-0.01)])
cuts=[boxc(POCKET,POCKET,DEPTH+2,0,0,FT+1.5)]          # карман трубы (дно 1.5 над фланцем)
cuts.append(cyl(23,FT+4,-1))                            # центр фланца
for sx in (-1,1):
    for sy in (-1,1):
        cuts.append(cyl(3.4,FT+4,-1,sx*15.5,sy*15.5,32))   # NEMA17 31x31 M3
for s in (-1,1):                                        # 2xМ4 сквозь стакан+трубу
    h=trimesh.creation.cylinder(radius=2.2,height=POCKET+2*WALL+4,sections=32)
    h.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
    h.apply_translation([0,0,FT+9+ (8 if s>0 else 0)])
    cuts.append(h)
cuts.append(boxc(12,POCKET+2*WALL+4,10,0,0,FT+18))      # окно провода (обе боковые)
part=trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->",OUT,"| watertight:",part.is_watertight,"| ext:",np.round(part.extents,1))
