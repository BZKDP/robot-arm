# -*- coding: utf-8 -*-
# FINAL "banka": 5-DOF, vylet ~30sm, obnimayushchiy zahvat, banka v zahvate.
# J1 baza STS | J2 plecho STS | J3 lokot FB | J4 zapyaste-naklon FB | J5 zapyaste-povorot FB | zahvat
import numpy as np, trimesh
from trimesh.transformations import rotation_matrix as R

STS=dict(l=45.2,w=24.7,h=35.0,col=[60,120,220]); FB=dict(l=40.1,w=20.1,h=38.9,col=[235,140,30])
GRAY=[150,150,160]; DARK=[70,70,80]; GREEN=[70,180,90]; CAN=[200,90,70]
parts=[]
def add(m,rgb): m.visual.face_colors=np.array(list(rgb)+[255],np.uint8); parts.append(m)
def obox(sx,sy,sz,c,ry=0.0,rgb=GRAY):
    m=trimesh.creation.box(extents=(sx,sy,sz))
    if ry: m.apply_transform(R(ry,[0,1,0]))
    m.apply_translation(c); add(m,rgb); return m
def servo(spec,c,ry=0.0):
    m=trimesh.creation.box(extents=(spec['l'],spec['w'],spec['h']))
    if ry: m.apply_transform(R(ry,[0,1,0]))
    m.apply_translation(c); add(m,spec['col']); return m
def link(p,q,w=18,th=13,rgb=GRAY):
    p=np.array(p,float);q=np.array(q,float);d=q-p;L=np.linalg.norm(d)
    obox(L,w,th,(p+q)/2,np.arctan2(-d[2],d[0]),rgb)
def ang(p,q):
    d=np.array(q,float)-np.array(p,float); return np.arctan2(-d[2],d[0])

# skelet, vylet ~300mm
J2=np.array([0,0,72]); J3=np.array([78,0,168]); J4=np.array([190,0,182]); J5=np.array([240,0,180])
# osnovanie TOLSTOE + baza STS
obox(110,110,8,(0,0,4),0,DARK)
servo(STS,(0,0,8+STS['h']/2))
obox(50,60,14,(0,0,55),0,GRAY)              # tolstyy povorotnyy brekket
servo(STS,J2)                                # plecho STS
link(J2,J3,20,15); servo(FB,J3,ang(J2,J3))   # lokot
link(J3,J4,17,12); servo(FB,J4,ang(J3,J4))   # zapyaste-naklon
link(J4,J5,15,11); servo(FB,J5,ang(J4,J5))   # zapyaste-povorot
# --- obnimayushchiy zahvat (2 izognutye gubki cradle) ---
palm=np.array([J5[0]+20,0,J5[2]])
obox(20,40,12,palm,0,GREEN)                  # ladon
for sy in (-1,1):
    # gubka: prischuchennyy k centru brusok (cradle pod cilindr)
    obox(46,8,10,(palm[0]+30,sy*22,palm[2]),0,GREEN)        # vneshnyaya chast
    obox(20,10,10,(palm[0]+50,sy*13,palm[2]),0.5*sy,GREEN)  # zagib k centru
# banka v zahvate (d44 h100, lyogkaya ~50g)
can=trimesh.creation.cylinder(radius=22,height=100,sections=36)
can.apply_translation((palm[0]+52,0,palm[2]+6)); add(can,CAN)

trimesh.Scene(parts).export('arm_can_final.glb')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
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
    ax.set_xlabel('X (mm)'); ax.set_zlabel('Z'); ax.set_title(title)
    plt.tight_layout(); plt.savefig(fname,dpi=110); plt.close()
render((16,-62),'final_view1.png','FINAL banka: 5-DOF, vylet 30sm, obnimayushchiy zahvat')
render((8,-95),'final_view2.png','Vid sboku')
print('OK parts',len(parts))
