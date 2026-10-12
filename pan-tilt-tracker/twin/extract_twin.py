#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Vytaskivaet detali iz Bambu-3mf v STL v PRAVILNYH sobrannyh koordinatah
# (transformacii komponentov iz 3D/3dmodel.model, a ne model_settings).
import zipfile, re, os, json
import numpy as np
from lxml import etree
import trimesh

SRC = r"example.3mf"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "models")
os.makedirs(OUT, exist_ok=True)

z = zipfile.ZipFile(SRC)
obj_file = [n for n in z.namelist() if n.startswith("3D/Objects/") and n.endswith(".model")][0]

# imena part po poryadku (objectid 1..7)
ms = z.read("Metadata/model_settings.config").decode("utf-8", "replace")
parts = re.findall(r'<part id="(\d+)"(.*?)</part>', ms, re.S)
names = {int(p): re.search(r'name" value="([^"]+)\.stl"', b).group(1) for p, b in parts}

# transformacii komponentov (3x4: 9 rotacii row-basis + 3 translyacii)
mdl = z.read("3D/3dmodel.model").decode("utf-8", "replace")
comps = re.findall(r'objectid="(\d+)"[^>]*transform="([^"]+)"', mdl)
xform = {}
for oid, t in comps:
    v = [float(x) for x in t.split()]
    if len(v) == 12:
        xform[int(oid)] = v

def apply_xform(V, v):
    R = np.array([[v[0], v[1], v[2]], [v[3], v[4], v[5]], [v[6], v[7], v[8]]])
    t = np.array([v[9], v[10], v[11]])
    return V @ R + t   # v' = v*R + t (3mf row-basis)

# parsim meshi
NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
meshes = {}
cur = None; verts = None; tris = None
for ev, el in etree.iterparse(z.open(obj_file), events=("start", "end")):
    tag = el.tag.replace(NS, "")
    if ev == "start" and tag == "object":
        cur = int(el.get("id")); verts = []; tris = []
    elif ev == "end":
        if tag == "vertex":
            verts.append((float(el.get("x")), float(el.get("y")), float(el.get("z"))))
        elif tag == "triangle":
            tris.append((int(el.get("v1")), int(el.get("v2")), int(el.get("v3"))))
        elif tag == "object":
            meshes[cur] = (np.array(verts), np.array(tris)); el.clear()

rig = {"parts": {}}
for oid in sorted(meshes):
    if oid not in names or oid not in xform:
        continue
    name = names[oid]
    V, F = meshes[oid]
    V = apply_xform(V, xform[oid])
    trimesh.Trimesh(vertices=V, faces=F, process=False).export(os.path.join(OUT, name + ".stl"))
    c = V.mean(axis=0)
    rig["parts"][name] = {"file": name + ".stl",
                          "centroid": c.tolist(),
                          "min": V.min(0).tolist(), "max": V.max(0).tolist()}
    print("%-32s tx=%s" % (name, np.round(xform[oid][9:12], 1).tolist()),
          "centroid", np.round(c, 1).tolist())

json.dump(rig, open(os.path.join(os.path.dirname(OUT), "rig_raw.json"), "w"), indent=2)
print("\nOK ->", OUT)
