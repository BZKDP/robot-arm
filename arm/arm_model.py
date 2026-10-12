# -*- coding: utf-8 -*-
# Polnaya 3D-vizualizaciya 5-DOF robo-ruki: 2x STS3215 (baza+plecho) +
# 3x FB5118M (lokot+2 zapyastya) + zahvat. Render PNG (matplotlib) + GLB.
import numpy as np, trimesh
from trimesh.transformations import rotation_matrix as R

# --- razmery servo (mm) ---
STS = dict(l=45.2, w=24.7, h=35.0, col=[60,120,220])    # siniy
FB  = dict(l=40.1, w=20.1, h=38.9, col=[235,140,30])    # oranzhevyy
GRAY=[150,150,160]; DARK=[70,70,80]; GREEN=[70,180,90]

parts=[]   # (mesh, rgb)
def add(m, rgb):
    m.visual.face_colors = np.array(list(rgb)+[255], np.uint8)
    parts.append(m)

def obox(sx,sy,sz, center, ry=0.0, rgb=GRAY):
    m = trimesh.creation.box(extents=(sx,sy,sz))
    if ry: m.apply_transform(R(ry,[0,1,0]))
    m.apply_translation(center)
    add(m, rgb); return m

def servo(spec, center, ry=0.0):
    s=spec; obox(s['l'],s['w'],s['h'], center, ry, s['col'])

def link(p,q, w=16, th=12, rgb=GRAY):
    p=np.array(p,float); q=np.array(q,float); d=q-p; L=np.linalg.norm(d)
    ry=np.arctan2(-d[2], d[0])           # napravlenie v ploskosti XZ
    obox(L, w, th, (p+q)/2, ry, rgb)

# --- skelet ruki (tochki sustavov v ploskosti XZ, mm) ---
P_base = np.array([0,0,0])
J1 = np.array([0,0,46])      # baza-povorot (STS, vertikal)
J2 = np.array([0,0,64])      # plecho (STS, gorizont os)
J3 = np.array([62,0,150])    # lokot (FB)
J4 = np.array([158,0,168])   # zapyaste-naklon (FB)
J5 = np.array([206,0,168])   # zapyaste-povorot (FB)
TIP= np.array([250,0,166])   # zahvat

def ang(p,q):
    d=np.array(q,float)-np.array(p,float); return np.arctan2(-d[2], d[0])

# osnovanie
obox(95,95,6,(0,0,3), 0, DARK)
# J1 baza STS (stoit vertikalno)
servo(STS, (0,0,6+STS['h']/2))
# brekket povorota J1->J2 (potolshe!)
obox(40,46,10,(0,0,52), 0, GRAY)
# J2 plecho STS (os gorizontalnaya)
servo(STS, J2)
# zveno plecho->lokot + FB lokot
link(J2,J3, 18,14, GRAY); servo(FB, J3, ang(J2,J3))
# zveno lokot->zapyaste + FB
link(J3,J4, 16,12, GRAY); servo(FB, J4, ang(J3,J4))
# zapyaste-povorot FB
link(J4,J5, 14,11, GRAY); servo(FB, J5, ang(J4,J5))
# zahvat: ladon + 2 palca
obox(22,30,10, (J5[0]+18,0,J5[2]), 0, GREEN)
for sy in (-1,1):
    obox(34,6,8, (J5[0]+40, sy*9, J5[2]), 0, GREEN)

# ====== export GLB (vrashchat myshkoy) ======
scene = trimesh.Scene(parts)
scene.export('arm_assembly.glb')

# ====== render PNG (matplotlib, headless) ======
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def render(view, fname):
    fig=plt.figure(figsize=(9,9)); ax=fig.add_subplot(111, projection='3d')
    for m in parts:
        tris=m.triangles
        rgb=np.array(m.visual.face_colors[0][:3])/255.0
        pc=Poly3DCollection(tris, alpha=1.0)
        pc.set_facecolor(rgb); pc.set_edgecolor((0,0,0,0.12)); pc.set_linewidth(0.2)
        ax.add_collection3d(pc)
    allv=np.vstack([m.vertices for m in parts])
    mn=allv.min(0); mx=allv.max(0); ctr=(mn+mx)/2; rng=(mx-mn).max()/2*1.05
    ax.set_xlim(ctr[0]-rng,ctr[0]+rng); ax.set_ylim(ctr[1]-rng,ctr[1]+rng); ax.set_zlim(ctr[2]-rng,ctr[2]+rng)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev=view[0], azim=view[1])
    ax.set_xlabel('X'); ax.set_zlabel('Z (vverh)'); ax.set_title('5-DOF robo-ruka')
    plt.tight_layout(); plt.savefig(fname, dpi=110); plt.close()

render((18,-60),'arm_view1.png')
render((12,-110),'arm_view2.png')
render((90,-90),'arm_top.png')
print('OK: arm_assembly.glb + arm_view1/2/top.png ; parts', len(parts))
