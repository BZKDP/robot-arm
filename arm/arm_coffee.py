# -*- coding: utf-8 -*-
# 3D-model "kofeynyy" konfig: 4-DOF + zahvat, vylet ~30 sm, derzhit stakan 0.5l.
# J1 baza-povorot FB5118M | J2 plecho SDVOENNOE 2xSTS3215 | J3 lokot FB | J4 zapyaste FB | zahvat
import numpy as np, trimesh
from trimesh.transformations import rotation_matrix as R

STS = dict(l=45.2, w=24.7, h=35.0, col=[60,120,220])    # siniy
FB  = dict(l=40.1, w=20.1, h=38.9, col=[235,140,30])    # oranzhevyy
GRAY=[150,150,160]; DARK=[70,70,80]; GREEN=[70,180,90]
parts=[]
def add(m,rgb): m.visual.face_colors=np.array(list(rgb)+[255],np.uint8); parts.append(m)
def obox(sx,sy,sz,c,ry=0.0,rgb=GRAY):
    m=trimesh.creation.box(extents=(sx,sy,sz))
    if ry: m.apply_transform(R(ry,[0,1,0]))
    m.apply_translation(c); add(m,rgb); return m
def servo(spec,c,ry=0.0,dy=0.0):
    m=trimesh.creation.box(extents=(spec['l'],spec['w'],spec['h']))
    if ry: m.apply_transform(R(ry,[0,1,0]))
    m.apply_translation((c[0],c[1]+dy,c[2])); add(m,spec['col']); return m
def link(p,q,w=18,th=13,rgb=GRAY):
    p=np.array(p,float);q=np.array(q,float);d=q-p;L=np.linalg.norm(d)
    ry=np.arctan2(-d[2],d[0]); obox(L,w,th,(p+q)/2,ry,rgb)
def ang(p,q):
    d=np.array(q,float)-np.array(p,float); return np.arctan2(-d[2],d[0])

# --- skelet (poza s vyletom ~30 sm) ---
J2=np.array([0,0,82])       # plecho
J3=np.array([95,0,185])     # lokot   (verhnyaya ruka ~138mm)
J4=np.array([212,0,178])    # zapyaste (predplechye ~117mm)
TIP=np.array([300,0,168])   # konec zahvata (vsego vylet ~30sm)

# osnovanie + baza-povorot FB (vertikal)
obox(105,105,7,(0,0,3.5),0,DARK)
servo(FB,(0,0,7+FB['h']/2))                       # J1 baza FB
obox(46,70,12,(0,0,58),0,GRAY)                    # tolstyy povorotnyy brekket
# J2 plecho: SDVOENNYE 2x STS (po oboim storonam osi) + brekket mezhdu
servo(STS,J2,dy= 18); servo(STS,J2,dy=-18)
obox(30,30,30,J2,0,GRAY)                           # spojka spary
# zveno plecho->lokot + FB lokot
link(J2,J3,20,15,GRAY); servo(FB,J3,ang(J2,J3))
# zveno lokot->zapyaste + FB zapyaste
link(J3,J4,17,12,GRAY); servo(FB,J4,ang(J3,J4))
# zahvat: ladon + 2 palca
a=ang(J4,TIP)
obox(26,34,11,(J4[0]+24,0,J4[2]-4),a,GREEN)
for sy in (-1,1):
    obox(40,7,9,(J4[0]+52,sy*10,J4[2]-7),a,GREEN)
# stakan 0.5l v zahvate (dlya masshtaba) ~ d66 h95
cup=trimesh.creation.cylinder(radius=33,height=95,sections=40)
cup.apply_translation((J4[0]+78,0,J4[2]-7+10)); add(cup,[210,210,225])

trimesh.Scene(parts).export('arm_coffee.glb')

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def render(view,fname,title):
    fig=plt.figure(figsize=(9,9)); ax=fig.add_subplot(111,projection='3d')
    for m in parts:
        pc=Poly3DCollection(m.triangles,alpha=1.0)
        pc.set_facecolor(np.array(m.visual.face_colors[0][:3])/255.0)
        pc.set_edgecolor((0,0,0,0.12)); pc.set_linewidth(0.2); ax.add_collection3d(pc)
    v=np.vstack([m.vertices for m in parts]); mn=v.min(0);mx=v.max(0);c=(mn+mx)/2;r=(mx-mn).max()/2*1.05
    ax.set_xlim(c[0]-r,c[0]+r);ax.set_ylim(c[1]-r,c[1]+r);ax.set_zlim(c[2]-r,c[2]+r)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev=view[0],azim=view[1])
    ax.set_xlabel('X (mm)'); ax.set_zlabel('Z vverh'); ax.set_title(title)
    plt.tight_layout(); plt.savefig(fname,dpi=110); plt.close()
render((16,-62),'coffee_view1.png','Kofeynyy konfig: 4-DOF, vylet ~30sm, stakan 0.5l')
render((10,-100),'coffee_view2.png','Vid sboku')
print('OK parts',len(parts))
