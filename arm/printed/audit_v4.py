# -*- coding: utf-8 -*-
import numpy as np, trimesh
B=r".\arm\printed"
def holes(mesh,z,normal=[0,0,1],origin_axis=2):
    o=[0,0,0]; o[origin_axis]=z
    s=mesh.section(plane_origin=o,plane_normal=normal)
    if s is None: print("  no section"); return
    p2,_=s.to_2D()
    for poly in p2.polygons_full:
        for i in poly.interiors:
            xs,ys=np.array(i.coords).T
            cx,cy=(xs.min()+xs.max())/2,(ys.min()+ys.max())/2
            dx,dy=xs.max()-xs.min(),ys.max()-ys.min()
            print(f"  hole c=({cx:6.2f},{cy:6.2f}) size {dx:.2f}x{dy:.2f}")

m=trimesh.load(B+r"\flange_bridge_v4_PETG.stl")
print("=== MOST bounds",np.round(m.bounds,1).tolist())
print("z=1 (skvoznye: centr 9.2, sloty, bolty 4.4 na +-21.5):"); holes(m,1.0)
print("z=1.5 (cekovki 8.4 na +-21.5):"); holes(m,1.5)
print("z=7 (pazy gaek mufty):"); holes(m,7.0)

c=trimesh.load(B+r"\nut_cassette_v4_x2_PETG.stl")
print("=== KASSETA bounds",np.round(c.bounds,1).tolist())
print("z=0.5 (karman shayby 9.8 na y=8.5/51.5):"); holes(c,0.5)
print("z=2.5 (hex gayki AF7.35):"); holes(c,2.5)
print("z=9 (kanal 4.6 + prutok 9.2 na 30):"); holes(c,9.0)

j=trimesh.load(B+r"\drill_jig_v4_PETG.stl")
print("=== KONDUKTOR bounds",np.round(j.bounds,1).tolist())
print("x=12 (napravl. v stenke: 4.3@8.5, 8.3@30, 4.3@51.5, z=10.2):")
holes(j,12,normal=[1,0,0],origin_axis=0)
