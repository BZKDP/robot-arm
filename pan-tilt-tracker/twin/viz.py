#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Samoproverka: render sborki SPLOSHNYMI detalyami pri raznyh uglah,
# toy zhe kinematikoy chto v brauzere (yaw vnutri tilt). Chitayu config.json.
import os, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
np.random.seed(1)
HERE=os.path.dirname(os.path.abspath(__file__)); MD=os.path.join(HERE,"static","models")
CFG=json.load(open(os.path.join(HERE,"config.json"),encoding="utf-8"))
COL=CFG["colors"]
def load(n):
    m=trimesh.load(os.path.join(MD,n+".stl"),process=False)
    F=m.faces
    if len(F)>1100: F=F[np.random.choice(len(F),1100,replace=False)]
    return m.vertices, F
MESH={n:load(n) for n in CFG["static_parts"]+CFG["pan_parts"]+CFG["tilt_parts"]}
def rod(a,th):
    a=np.array(a,float); a/=np.linalg.norm(a); c,s=np.cos(th),np.sin(th); x,y,z=a
    return np.array([[c+x*x*(1-c),x*y*(1-c)-z*s,x*z*(1-c)+y*s],
                     [y*x*(1-c)+z*s,c+y*y*(1-c),y*z*(1-c)-x*s],
                     [z*x*(1-c)-y*s,z*y*(1-c)+x*s,c+z*z*(1-c)]])
PP=np.array(CFG["pan"]["pivot"]); PA=CFG["pan"]["axis"]
TP=np.array(CFG["tilt"]["pivot"]); TA=CFG["tilt"]["axis"]
def transformed(tilt_deg,yaw_deg):
    Rt=rod(PA,np.radians(tilt_deg)); Ry=rod(TA,np.radians(yaw_deg)); out={}
    for n in CFG["static_parts"]: out[n]=MESH[n][0]
    for n in CFG["pan_parts"]:    out[n]=(Rt@(MESH[n][0]-PP).T).T+PP
    for n in CFG["tilt_parts"]:
        v=(Ry@(MESH[n][0]-TP).T).T+TP; out[n]=(Rt@(v-PP).T).T+PP
    return out
BRIGHT={"base_link":"#8a93a0","pan_motor":"#777","pan_tilt_bracket":"#e0701f",
        "tilt_motor":"#999","payload_link_end_mount-flat":"#f0902f","camera-front-v2-print":"#1a7fc8","camera-back-v2-print":"#3aa0e0"}
def draw(ax,tilt,yaw,az,el=12):
    V=transformed(tilt,yaw)
    order=CFG["static_parts"]+CFG["pan_parts"]+CFG["tilt_parts"]
    for n in order:
        verts,F=V[n],MESH[n][1]
        pc=Poly3DCollection(verts[F],facecolor=BRIGHT[n],edgecolor='#333',linewidths=0.1,alpha=1.0)
        ax.add_collection3d(pc)
    ax.set_xlim(-45,60); ax.set_ylim(-85,5); ax.set_zlim(-20,110)
    ax.set_box_aspect((1,1,1)); ax.view_init(el,az); ax.set_axis_off()
# proverka POVOROTA vokrug centra: vid SVERHU, verhniy servo dolzhen krutitsya na meste
cases=[(0,-60,"POVOROT -60"),(0,0,"REST 0"),(0,60,"POVOROT +60")]
fig=plt.figure(figsize=(18,11))
for j,(t,y,tt) in enumerate(cases):
    ax=fig.add_subplot(2,3,j+1,projection="3d"); draw(ax,t,y,-90,80); ax.set_title(tt+" (SVERHU)",color="w")
    ax=fig.add_subplot(2,3,j+4,projection="3d"); draw(ax,t,y,-62,12); ax.set_title(tt+" (sboku)",color="w")
fig.patch.set_facecolor("#222")
out=os.path.join(HERE,"viz.png"); plt.tight_layout(); plt.savefig(out,dpi=95,facecolor="#222"); print("saved")
