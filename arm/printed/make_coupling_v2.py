# -*- coding: utf-8 -*-
"""
МУФТА-ФЛАНЕЦ v2 + ОПОРА ОСИ v2 — крепление к goBILDA-балке БЕЗ СВЕРЛЕНИЯ.
Реальность узла J2 (замеры 03.08): вал редуктора торчит за стенку всего ~8.5мм
=> высокий хаб с хомутом БЕССМЫСЛЕН (не достаёт до вала). Правильная деталь:
низкий диск Ø40 x 8, носик Ø13.6 x 2 (в Ø14 балки), сквозной D-бор — вал входит
со стороны носика, момент держит D-профиль, осевую фиксацию даёт ось напротив.
Крепёж: 4 x M4 на (+-8,+-8) = 4 отверстия ВОКРУГ Ø14 балки; гайки M4 в
слайд-карманах в толще диска (болт из-за стенки балки, снаружи не торчит ничего).

  python make_coupling_v2.py          -> coupling_v2_PETG.stl   (D-бор 8.15/6.05 на вал)
  python make_coupling_v2.py --axle   -> axle_clamp_v2_PETG.stl (бор 8.2 + стяжка M3, пруток-ось)

ПРОВЕРКА ПЕРЕД ПЕЧАТЬЮ (штангель на балке): вокруг Ø14 есть 4 круглых отверстия
по диагоналям; расстояние центр-центр противоположных = 22.6; диаметр >= 4.2.
Печать: диском ВНИЗ (носик вверх), PETG, слой 0.2, стенки 6, 100%, поддержек нет.
"""
import sys
import numpy as np
import trimesh

AXLE = "--axle" in sys.argv

SHAFT_D   = 8.15 if not AXLE else 8.25
SHAFT_AF  = 6.05                      # лыски (только муфта)
FLG_D     = 40.0
FLG_H     = 8.0
NOSE_D    = 13.6
NOSE_L    = 2.0                       # стенка балки ~2.5: фланец гарантированно прижмётся
MAG_D     = 6.6                       # канал магнита насквозь (датчик с обратной стороны)
M4_HOLE   = 4.4
M4_POS    = 8.0                       # (+-8,+-8)
NUT_W     = 7.4                       # гайка M4 s7 (+0.4)
NUT_D     = 8.4
NUT_H     = 3.6
BORE_DEEP = FLG_H + NOSE_L            # D-бор сквозной через носик и диск
M3_HOLE   = 3.4                       # стяжка split (только ось)
M3NUT_AF  = 5.9
OUT = (r".\arm\printed\axle_clamp_v2_PETG.stl" if AXLE
       else r".\arm\printed\coupling_v2_PETG.stl")

def cyl(d,h,z0,x=0,y=0,sec=96):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c
def boxc(sx,sy,sz,x,y,z0):
    b=trimesh.creation.box(extents=[sx,sy,sz])
    b.apply_translation([x,y,z0+sz/2]); return b

# диск на столе (z=0..8); носик сверху ТОЛЬКО у муфты (ось центруется болтами-бутербродом)
if AXLE:
    body = cyl(FLG_D,FLG_H,0)
else:
    body = trimesh.boolean.union([cyl(FLG_D,FLG_H,0), cyl(NOSE_D,NOSE_L+0.01,FLG_H-0.005)])

cuts=[]
# сквозной D-бор (вал заходит СВЕРХУ, со стороны носика — от балки)
bore = cyl(SHAFT_D, BORE_DEEP+2, -1)
if not AXLE:
    f1 = boxc(SHAFT_D,(SHAFT_D-SHAFT_AF)/2+2, BORE_DEEP+4, 0,
              SHAFT_AF/2+((SHAFT_D-SHAFT_AF)/2+2)/2, -1.5)
    f2 = f1.copy(); f2.apply_translation([0,-2*f1.center_mass[1],0])
    bore = trimesh.boolean.difference([bore,f1,f2])
cuts.append(bore)

# 4xM4 (+-8,+-8): БУТЕРБРОД «ось|балка|муфта» одними болтами M4x20.
# Муфта: слайд-карманы под ГАЙКИ. Ось: цековки Ø8 под ГОЛОВКИ (со свободной стороны).
for sx in (-1,1):
    for sy in (-1,1):
        x,y = sx*M4_POS, sy*M4_POS
        cuts.append(cyl(M4_HOLE, FLG_H+NOSE_L+4, -1, x, y, 32))
        if not AXLE:
            ang=np.arctan2(y,x)
            L=FLG_D/2-np.hypot(x,y)+4
            slot=boxc(L, NUT_W, NUT_H, 0,0,0)
            slot.apply_translation([L/2-0.01,0,0])
            slot.apply_transform(trimesh.transformations.rotation_matrix(ang,[0,0,1]))
            slot.apply_translation([x,y,(FLG_H-NUT_H)/2])
            cuts.append(slot)
            cuts.append(cyl(NUT_D, NUT_H, (FLG_H-NUT_H)/2, x, y, 6))
        else:
            cuts.append(cyl(8.2, 4.0, FLG_H-4.0+0.01, x, y, 32))   # цековка головки

if AXLE:
    # стяжка прутка: пропил от бора до края + 1xM3 поперёк на x=15 (мимо цековок М4)
    XT=15.0
    cuts.append(boxc(FLG_D/2+2, 1.8, FLG_H+2, (FLG_D/2+2)/2+2.5, 0, -1))
    h=trimesh.creation.cylinder(radius=M3_HOLE/2,height=FLG_D,sections=32)
    h.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
    h.apply_translation([XT, 0, FLG_H/2]); cuts.append(h)
    yc=float(np.sqrt((FLG_D/2)**2-XT**2))          # поверхность диска на x=15
    for s,rad,sec in ((1,3.2,32),(-1,M3NUT_AF/np.sqrt(3),6)):
        cs=trimesh.creation.cylinder(radius=rad, height=3.2, sections=sec)
        cs.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
        cs.apply_translation([XT, s*(yc-3.2/2+0.6), FLG_H/2])
        cuts.append(cs)

part=trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->",OUT,"| watertight:",part.is_watertight,"| ext:",np.round(part.extents,1))
