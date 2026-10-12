# -*- coding: utf-8 -*-
"""
Раздельные листы печати (после развала общей плиты):
  PLATE_1_J2_SET.stl  — комплект узла J2: адаптер + мост + козырёк AS5600 + 2 втулки + кондуктор
  PLATE_2_ROLL_CUP.stl — стакан roll (NEMA17), одна деталь
"""
import numpy as np, trimesh

def load(n): return trimesh.load(n)
def pack(specs, out):
    items=[]
    for name,cnt,flip in specs:
        for _ in range(cnt):
            m=load(name).copy()
            if flip: m.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
            m.apply_translation([-m.bounds[0][0],-m.bounds[0][1],-m.bounds[0][2]])
            items.append(m)
    items.sort(key=lambda m:-(m.extents[1]))
    GAP=8.0; MAXW=200.0
    x=0;y=0;rowH=0;placed=[]
    for m in items:
        w,d=m.extents[0],m.extents[1]
        if x>0 and x+w>MAXW: x=0;y+=rowH+GAP;rowH=0
        m.apply_translation([x,y,0]); placed.append(m); x+=w+GAP; rowH=max(rowH,d)
    plate=trimesh.util.concatenate(placed)
    b=plate.bounds
    plate.apply_translation([-(b[0][0]+b[1][0])/2,-(b[0][1]+b[1][1])/2,0])
    plate.export(out)
    print("OK ->",out,"| XY:",np.round(plate.extents[:2],0),"| detali:",len(placed))

pack([("gearbox_adapter_J2_v2.stl",1,False),
      ("flange_bridge_PETG.stl",1,False),
      ("as5600_bracket_PETG.stl",1,False),
      ("drill_jig_v3_PETG.stl",1,True),
      ("tube_spacers_x2_PETG.stl",1,False)],
     r".\arm\printed\PLATE_1_J2_SET.stl")

pack([("roll_mount_PETG.stl",1,False)],
     r".\arm\printed\PLATE_2_ROLL_CUP.stl")
