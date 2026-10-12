#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Avtokalibrovka znakov slezheniya cherez API: dvigaem serv -> smotrim kuda uehalo lico.
import urllib.request, json, time
BASE="http://ROBOT_HOST:8200"
def get(p): return json.load(urllib.request.urlopen(BASE+p, timeout=5))
def post(p,o):
    r=urllib.request.Request(BASE+p, data=json.dumps(o).encode(), headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r, timeout=5))
def sign(v): return 1 if v>=0 else -1
def read_err(dur=2.5):
    xs=[]; ys=[]; t0=time.time()
    while time.time()-t0<dur:
        s=get("/pos")
        if s["face"]: xs.append(s["err_xy"][0]); ys.append(s["err_xy"][1])
        time.sleep(0.12)
    if len(xs)>=3:
        xs.sort(); ys.sort(); return (xs[len(xs)//2], ys[len(ys)//2], len(xs))
    return None
def cur(idn): return get("/pos")["raw"][str(idn)]

cfg=get("/config"); YAW=cfg["tilt"]["id"]; TILT=cfg["pan"]["id"]
print("YAW servo id=%d (povorot), TILT servo id=%d (naklon)"%(YAW,TILT))
post("/track",{"on":False}); time.sleep(0.5)
base=read_err(3.0)
print("baseline:",base)
if not base: print("!!! NET LICA - syad pered kameroy rovno"); raise SystemExit

# --- YAW ---
c0=cur(YAW); e0=read_err(2.0)
post("/move",{"id":YAW,"pos":c0+100,"spd":500}); time.sleep(1.5)
e1=read_err(2.0)
post("/move",{"id":YAW,"pos":c0,"spd":500}); time.sleep(1.2)
if e0 and e1:
    gx=(e1[0]-e0[0])/100.0; yaw_sign=-sign(gx)
    print("YAW: err_x %.3f->%.3f g=%.5f => yaw_sign=%d"%(e0[0],e1[0],gx,yaw_sign))
else:
    yaw_sign=1; print("YAW: lico poteryalos, ostavil sign=1")

# --- TILT ---
c0=cur(TILT); e0=read_err(2.0)
post("/move",{"id":TILT,"pos":c0+100,"spd":500}); time.sleep(1.5)
e1=read_err(2.0)
post("/move",{"id":TILT,"pos":c0,"spd":500}); time.sleep(1.2)
if e0 and e1:
    gy=(e1[1]-e0[1])/100.0; tilt_sign=-sign(gy)
    print("TILT: err_y %.3f->%.3f g=%.5f => tilt_sign=%d"%(e0[1],e1[1],gy,tilt_sign))
else:
    tilt_sign=1; print("TILT: lico poteryalos, ostavil sign=1")

r=post("/trackcfg",{"yaw_sign":yaw_sign,"tilt_sign":tilt_sign})
print("SET:", {k:r["track_cfg"][k] for k in ("yaw_sign","tilt_sign")})
