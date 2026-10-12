#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "models")
def load(n):
    v = trimesh.load(os.path.join(MD, n + ".stl"), process=False).vertices
    return v[np.random.choice(len(v), min(1800,len(v)), replace=False)]
STATIC=["base_link","pan_motor"]; PANG=["pan_tilt_bracket","tilt_motor"]
TILTG=["payload_link_end_mount-flat","camera-front-v2-print","camera-back-v2-print"]
pts={n:load(n) for n in STATIC+PANG+TILTG}
def rod(a,th):
    a=np.array(a,float); a/=np.linalg.norm(a); c,s=np.cos(th),np.sin(th); x,y,z=a
    return np.array([[c+x*x*(1-c),x*y*(1-c)-z*s,x*z*(1-c)+y*s],
                     [y*x*(1-c)+z*s,c+y*y*(1-c),y*z*(1-c)-x*s],
                     [z*x*(1-c)-y*s,z*y*(1-c)+x*s,c+z*z*(1-c)]])
TP=np.array([5.0,-35.8,72.0]); AX=[0,1,0]
views={"tvoy rakurs (3/4)":(12,-72),"FRONT (smotret tak)":(8,180)}
fig=plt.figure(figsize=(15,8))
i=0
for vn,(el,az) in views.items():
    for th in [0,35]:
        i+=1; ax=fig.add_subplot(2,2,i,projection="3d")
        R=rod(AX,np.radians(th))
        for n in STATIC+PANG:
            P=pts[n]; ax.scatter(P[:,0],P[:,1],P[:,2],s=2,c="#888")
        for n in TILTG:
            P=(R@(pts[n]-TP).T).T+TP
            c="#16c" if "camera" in n else "#c85a2a"
            ax.scatter(P[:,0],P[:,1],P[:,2],s=3,c=c)
        ax.set_box_aspect((1,1,1)); ax.set_xlim(-40,70); ax.set_ylim(-80,0); ax.set_zlim(-10,110)
        ax.view_init(el,az); ax.set_title("%s | tilt %d"%(vn,th))
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"axis_check.png")
plt.tight_layout(); plt.savefig(out,dpi=95); print("saved")
