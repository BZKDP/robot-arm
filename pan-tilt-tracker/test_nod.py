# -*- coding: utf-8 -*-
# Trigger /nod i zamer profilya naklona id2 -> proverka odinakovosti kivkov.
import urllib.request, json, time
BASE = "http://ROBOT_HOST:8200"
def post(p): urllib.request.urlopen(urllib.request.Request(BASE+p, data=b"{}", headers={"Content-Type":"application/json"}), timeout=4).read()
def p2(): return json.load(urllib.request.urlopen(BASE+"/pos", timeout=3))["raw"]["2"]

base = p2(); print("base id2 =", base)
post("/nod")
seq = []; t0 = time.time()
while time.time()-t0 < 6.0:
    seq.append((round(time.time()-t0,2), p2())); time.sleep(0.07)
# pechataem i ishchem ekstremumy (peaks vniz / vverh)
vals = [v for _,v in seq]
print("profil id2:", " ".join(str(v) for v in vals))
# lokalnye max (vniz) i min (vverh)
downs=[]; ups=[]
for i in range(1,len(vals)-1):
    if vals[i]>=vals[i-1] and vals[i]>vals[i+1] and vals[i]>base+40: downs.append(vals[i])
    if vals[i]<=vals[i-1] and vals[i]<vals[i+1] and vals[i]<base-40: ups.append(vals[i])
print("VNIZ-piki (dolzhny byt odinakovye):", downs)
print("VVERH-piki (dolzhny byt odinakovye):", ups)
print("vernulsya k base?", vals[-1], "vs", base)
