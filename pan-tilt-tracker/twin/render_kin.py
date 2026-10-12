#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Tochnaya kinematika kak v brauzere: yaw(inner) vnutri tilt(outer). Render na uglah.
import os, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); MD=os.path.join(HERE,"static","models")
CFG=json.load(open(os.path.join(HERE,"config.json"),encoding="utf-8"))
def load(n):
    v=trimesh.load(os.path.join(MD,n+".stl"),process=False).vertices
    return v[np.random.choice(len(v),min(1400,len(v)),replace=False)]
P={n:load(n) for n in CFG["static_parts"]+CFG["pan_parts"]+CFG["tilt_parts"]}
def rod(a,th):
    a=np.array(a,float); a/=np.linalg.norm(a); c,s=np.cos(th),np.sin(th); x,y,z=a
    return np.array([[c+x*x*(1-c),x*y*(1-c)-z*s,x*z*(1-c)+y*s],
                     [y*x*(1-c)+z*s,c+y*y*(1-c),y*z*(1-c)-x*s],
                     [z*x*(1-c)-y*s,z*y*(1-c)+x*s,c+z*z*(1-c)]])
PP=np.array(CFG["pan"]["pivot"]); PA=CFG["pan"]["axis"]
TP=np.array([7.9,-35.6,71.4]); TA=[1,0,0]   # TEST: yaw vokrug realnoy osi krepleniya (X)
def pose(tilt_deg,yaw_deg):
    Rt=rod(PA,np.radians(tilt_deg)); Ry=rod(TA,np.radians(yaw_deg)); out={}
    for n in CFG["static_parts"]: out[n]=P[n]
    for n in CFG["pan_parts"]:    out[n]=(Rt@(P[n]-PP).T).T+PP
    for n in CFG["tilt_parts"]:                       # snachala yaw vokrug TP, potom tilt vokrug PP
        v=(Ry@(P[n]-TP).T).T+TP; out[n]=(Rt@(v-PP).T).T+PP
    return out
COL={"base_link":"#888","pan_motor":"#444","pan_tilt_bracket":"#c85a2a","tilt_motor":"#222",
     "payload_link_end_mount-flat":"#e07a3a","camera-front-v2-print":"#16c","camera-back-v2-print":"#19f"}
cases=[(0,0,"naklon0 povorot0"),(0,45,"povorot +45"),(0,-45,"povorot -45"),(45,0,"naklon +45")]
fig=plt.figure(figsize=(18,15))
for i,(t,y,tt) in enumerate(cases):
    d=pose(t,y); ax=fig.add_subplot(2,2,i+1,projection="3d")
    for n in d: ax.scatter(d[n][:,0],d[n][:,1],d[n][:,2],s=5,c=COL[n])
    ax.scatter(*TP,s=140,c="lime",marker="x")
    ax.set_box_aspect((1,1,1)); ax.set_xlim(-40,55); ax.set_ylim(-80,0); ax.set_zlim(20,120)
    ax.view_init(16,-58); ax.set_title(tt)
out=os.path.join(HERE,"kin_check.png"); plt.tight_layout(); plt.savefig(out,dpi=90); print("saved")
