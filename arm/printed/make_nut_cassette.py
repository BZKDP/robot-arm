# -*- coding: utf-8 -*-
"""
КАССЕТА-РАСПОРКА v2 (C+): полнотелый брусок в просвет трубы 20x20.
- заполняет просвет 17x17 -> затяжка и нагрузка идут на ОБЕ стенки, труба не мнётся;
- 2 шестигранных гнезда: гайки М4 напротив отверстий трубы (14 и 46 от торца),
  за гнездом канал Ø4.6 — хвост болта М4x16 уходит внутрь бруска;
- отверстие Ø9 поперёк на 30мм — проход прутка-оси НАСКВОЗЬ бруска;
- вставляется с нижнего торца трубы до совпадения гнёзд с отверстиями.
Болт: М4x16: голова в цековке моста (сторона муфты) -> мост 8 -> стенка 1.5 -> гайка.
Снаружи дальней грани трубы — НИЧЕГО. Печать: лёжа, 60-100%, ~30 мин. 2 шт на листе.
"""
import numpy as np, trimesh

OUT=r".\arm\printed\nut_cassette_x2_PETG.stl"
W,L,H=16.6,50.0,16.6           # просвет трубы 17x17
def one(dx):
    body=trimesh.creation.box(extents=[W,L,H]); body.apply_translation([dx,L/2,H/2])
    cuts=[]
    for y in (14.0,46.0):
        n=trimesh.creation.cylinder(radius=7.5/np.sqrt(3),height=4.0,sections=6)   # гнездо гайки
        n.apply_translation([dx,y,4.0/2-0.01]); cuts.append(n)
        c=trimesh.creation.cylinder(radius=2.3,height=H,sections=24)               # канал хвоста
        c.apply_translation([dx,y,H/2+2]); cuts.append(c)
    p=trimesh.creation.cylinder(radius=4.6,height=H+2,sections=48)                  # пруток Ø8 насквозь
    p.apply_translation([dx,30.0,H/2]); cuts.append(p)
    return trimesh.boolean.difference([body]+cuts)
m=trimesh.util.concatenate([one(0),one(24)])
m.export(OUT)
print("OK ->",OUT,"| ext:",np.round(m.extents,1))
