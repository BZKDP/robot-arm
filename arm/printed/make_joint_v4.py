# -*- coding: utf-8 -*-
"""
СТЫК v4 — болты трубы вынесены ЗА муфту (юзер не мог крутить: муфта нависала).
Было: трубные болты на +-16 от оси. Стало: +-21.5 (от торца трубы: 8.5 и 51.5).
Старые отверстия трубы (14/46) остаются пустыми — не мешают.

1) flange_bridge_v4  40 x 56 x 8: слоты муфты как были; трубные Ø4.4 на (0,+-21.5)
   с цековками Ø8.4x3 со стороны муфты; центр Ø9.2; пазы гаек муфтиных болтов.
2) nut_cassette_v4 x2  16.6 x 60 x 16.6: гнёзда ГАЙКА+ШАЙБА на 8.5/51.5 от торца:
   карман шайбы Ø9.6x1.0 у стенки + hex 7.35x3.4 (гайка плотно) + канал 4.6;
   пруток Ø9.2 на 30. Вставляешь шайбы и гайки ЗАРАНЕЕ, задвигаешь с торца.
3) drill_jig_v4: направляющие Ø4.3 на 8.5 и 51.5 + Ø8.3 на 30 (для трубы J5 —
   сверлится сразу правильно; на готовой трубе J2 досверлить только 2 новых).
Всё одним листом: PLATE_JOINT_V4.stl (кондуктор перевёрнут).
Болты мост->труба: М4x16 (мост 8 + стенка 1.5 + шайба 1 + гайка 3.2).
"""
import numpy as np, trimesh
BASE=r".\arm\printed"

def cyl(d,h,z0,x=0,y=0,sec=48):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c
def boxc(sx,sy,sz,x,y,z0):
    b=trimesh.creation.box(extents=[sx,sy,sz]); b.apply_translation([x,y,z0+sz/2]); return b
def hexp(af,h,z0,x=0,y=0):
    n=trimesh.creation.cylinder(radius=af/np.sqrt(3),height=h,sections=6)
    n.apply_translation([x,y,z0+h/2]); return n

TB=21.5   # трубные болты от оси

# ---------- 1. МОСТ v4 ----------
W,L,T=40.0,56.0,5.0   # L=56: край цековки (21.5+4.2=25.7) -> стенка 2.3
# T=5 (вар. Б 27.08): труба уезжает на 3 к муфте -> зазор труба-стенка Б = 4.7мм,
# подшипник крепится ОБЫЧНЫМИ М4х16 изнутри (голова 4 < 4.7), потай и зенковка не нужны.
# ЦЕНА: болты муфты М3 подрезать до ~7 (или М3х6), пруток резать 36 (33 впритык ок).
FL_D=4.4; FN_AF,FN_H=7.4,3.2
body=boxc(W,L,T,0,0,0)
cuts=[cyl(9.2,T+2,-1)]
R_IN,R_OUT=7.6,9.4
for a in (45,135,225,315):
    ar=np.radians(a); ux,uy=np.cos(ar),np.sin(ar)
    slot=trimesh.boolean.union([cyl(FL_D,T+2,-1,R_IN*ux,R_IN*uy,24),
        cyl(FL_D,T+2,-1,R_OUT*ux,R_OUT*uy,24),
        (lambda b:(b.apply_transform(trimesh.transformations.rotation_matrix(ar,[0,0,1])),
                   b.apply_translation([8.5*ux,8.5*uy,T/2]),b)[-1])(
            trimesh.creation.box(extents=[R_OUT-R_IN,FL_D,T+2]))])
    cuts.append(slot)
    ng=trimesh.creation.box(extents=[R_OUT-R_IN+FN_AF,FN_AF,FN_H])
    ng.apply_transform(trimesh.transformations.rotation_matrix(ar,[0,0,1]))
    ng.apply_translation([8.5*ux,8.5*uy,T-FN_H/2+0.01]); cuts.append(ng)
for s in (-1,1):
    cuts.append(cyl(4.4,T+2,-1,0,s*TB,32))
    cuts.append(cyl(8.4,3.0,-0.01,0,s*TB,32))
bridge=trimesh.boolean.difference([body]+cuts)
bridge.export(BASE+r"\flange_bridge_v4_PETG.stl")
print("MOST v4 | wt:",bridge.is_watertight,"| ext:",np.round(bridge.extents,1))

# ---------- 2. КАССЕТА v4 (гайка+шайба) ----------
CW,CL,CH=16.6,60.0,16.6
def cassette(dx):
    b=boxc(CW,CL,CH,dx,CL/2,0)                      # y: 0..60 (0=торец трубы)
    cc=[]
    for y in (8.5,51.5):
        cc.append(cyl(9.8,1.1,-0.01,dx,y))          # карман ШАЙБЫ (Ø9 x 0.8) у стенки
        cc.append(hexp(7.35,3.5,1.05,dx,y))         # гнездо ГАЙКИ (s7) плотно
        cc.append(cyl(4.6,CH,4.4,dx,y))             # канал хвоста болта
    cc.append(cyl(9.2,CH+2,-1,dx,30.0))             # пруток на 30
    return trimesh.boolean.difference([b]+cc)
cass=trimesh.util.concatenate([cassette(0),cassette(24)])
cass.export(BASE+r"\nut_cassette_v4_x2_PETG.stl")
print("KASSETA v4 x2 | ext:",np.round(cass.extents,1))

# ---------- 3. КОНДУКТОР v4 ----------
TU=20.4; WALL=5.0; JL=66.0; H=TU+2*WALL
jig=boxc(H,JL,TU+WALL,0,JL/2-4,0)                  # y: -4..62
cav=boxc(TU,JL,TU+2,0,JL/2,-1.99)                  # полость y: 0..62 -> стенка-УПОР на y=-4..0

cuts=[cav]
for y,d in [(8.5,4.3),(30.0,8.3),(51.5,4.3)]:
    g=trimesh.creation.cylinder(radius=d/2,height=H+4,sections=48)
    g.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
    g.apply_translation([0,y,TU/2]); cuts.append(g)
jig=trimesh.boolean.difference([jig]+cuts)
jig.export(BASE+r"\drill_jig_v4_PETG.stl")
print("KONDUKTOR v4 | ext:",np.round(jig.extents,1))

# ---------- ЛИСТ ----------
items=[]
for m,flip in [(bridge,False),(cass,False),(jig,True)]:
    mm=m.copy()
    if flip: mm.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
    mm.apply_translation([-mm.bounds[0][0],-mm.bounds[0][1],-mm.bounds[0][2]])
    items.append(mm)
x=0;placed=[]
for mm in items:
    mm.apply_translation([x,0,0]); placed.append(mm); x+=mm.extents[0]+8
plate=trimesh.util.concatenate(placed)
b=plate.bounds; plate.apply_translation([-(b[0][0]+b[1][0])/2,-(b[0][1]+b[1][1])/2,0])
plate.export(BASE+r"\PLATE_JOINT_V4.stl")
print("LIST -> PLATE_JOINT_V4.stl | XY:",np.round(plate.extents[:2],0))
