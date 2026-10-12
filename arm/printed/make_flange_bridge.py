# -*- coding: utf-8 -*-
"""
ПЛАСТИНА-МОСТ: металлическая фланцевая муфта 8мм (фланец Ø32) -> труба 20x20.
Заменяет печатную муфту v3: на валу теперь СТАЛЬ (setscrew в лыску), пластик
только передаёт момент с фланца на трубу.

Стек: вал -> метал.муфта -> фланец Ø32 -> 4xМ4x8 (болты из фланца, гайки в
карманах пластины заподлицо) -> ПЛАСТИНА 40x46x8 -> 2xМ4x30 на (0,+-16)
СКВОЗЬ трубу (головы утоплены в глубоких цековках ПОД фланцем) -> гайки+шайбы.

!!! ПЕРЕД ПЕЧАТЬЮ подставить реальные замеры муфты:
    FL_BC  = расстояние центр-центр ПРОТИВОПОЛОЖНЫХ отверстий фланца
    FL_D   = диаметр отверстий фланца (+0.3 зазор уже внутри)
Запуск: python make_flange_bridge.py [BC] [D]   (напр. python make_flange_bridge.py 24 4.5)
Печать: плашмя стороной ФЛАНЦА вверх?? нет — стороной ТРУБЫ вниз (карманы гаек
мостиком, норм), PETG, слой 0.2, стенки 5, 100%.
"""
import sys
import numpy as np, trimesh

FL_BC = float(sys.argv[1]) if len(sys.argv)>1 else 15.0   # ЗАМЕР 24.08 по фото: фланец Ø22, BC~15
FL_D  = (float(sys.argv[2]) if len(sys.argv)>2 else 3.2) + 0.3   # отверстия под М3

W,L,T = 40.0, 46.0, (float(sys.argv[3]) if len(sys.argv)>3 else 8.0)
HUB_D = 9.2           # центр: только ПРОХОД ПРУТКА Ø8 (хаб муфты смотрит К РЕДУКТОРУ,
                      # сквозь пластину НЕ идёт — иначе болтам BC15 не остаётся тела!)
M4    = 4.4
# гайки фланцевых болтов: М3 при FL_D<4.2, иначе М4
FN_AF, FN_H = (5.9, 2.8) if FL_D < 4.2 else (7.4, 3.2)
TUBE_BOLTS = 16.0     # (0,+-16) — как кондуктор drill_jig_v3
CSK_D, CSK_H = 8.4, 3.0   # цековка голов М4x30 (фланец Ø22 до них не достаёт — просто аккуратность)

OUT=r".\arm\printed\flange_bridge_PETG.stl"
def cyl(d,h,z0,x=0,y=0,sec=64):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=sec)
    c.apply_translation([x,y,z0+h/2]); return c

# z=0 — сторона ФЛАНЦА (низ), z=T — сторона ТРУБЫ (верх)
body=trimesh.creation.box(extents=[W,L,T]); body.apply_translation([0,0,T/2])
cuts=[cyl(HUB_D,T+2,-1)]
R_IN, R_OUT = 7.6, 9.4   # СЛОТЫ v-final: покрывают BC 15.2..18.8 — сядет при любом реальном круге
for a in (45,135,225,315):
    ar=np.radians(a); ux,uy=np.cos(ar),np.sin(ar)
    # радиальный слот шириной FL_D: два цилиндра + перемычка
    slot=trimesh.boolean.union([
        cyl(FL_D,T+2,-1,R_IN*ux,R_IN*uy,24),
        cyl(FL_D,T+2,-1,R_OUT*ux,R_OUT*uy,24),
        (lambda b:(b.apply_transform(trimesh.transformations.rotation_matrix(ar,[0,0,1])),
                   b.apply_translation([(R_IN+R_OUT)/2*ux,(R_IN+R_OUT)/2*uy,T/2]),b)[-1])(
            trimesh.creation.box(extents=[R_OUT-R_IN,FL_D,T+2]))])
    cuts.append(slot)
    # продолговатое гнездо гайки (гайка скользит вдоль радиуса, не проворачивается)
    ng=trimesh.creation.box(extents=[R_OUT-R_IN+FN_AF,FN_AF,FN_H])
    ng.apply_transform(trimesh.transformations.rotation_matrix(ar,[0,0,1]))
    ng.apply_translation([(R_IN+R_OUT)/2*ux,(R_IN+R_OUT)/2*uy,T-FN_H/2+0.01])
    cuts.append(ng)
for s in (-1,1):                                  # 2 болта сквозь трубу
    cuts.append(cyl(M4,T+2,-1,0,s*TUBE_BOLTS,32))
    cuts.append(cyl(CSK_D,CSK_H,-0.01,0,s*TUBE_BOLTS,32))              # глубокая цековка снизу
part=trimesh.boolean.difference([body]+cuts)
part.export(OUT)
print("OK ->",OUT,"| BC =",FL_BC,"| watertight:",part.is_watertight,"| ext:",np.round(part.extents,1))

# --- распорные втулки в трубу (x2): гайку тянуть через них, стенки не сомнёт ---
SP_OUT=r".\arm\printed\tube_spacers_x2_PETG.stl"
sp=[]
for i in (0,1):
    s=trimesh.boolean.difference([cyl(8.0,16.6,0,i*14), cyl(4.5,18,-0.5,i*14)])
    sp.append(s)
spm=trimesh.util.concatenate(sp)
spm.export(SP_OUT)
print("OK ->",SP_OUT,"| vtulki 8x16.6, bor 4.5 (vnutr. prosvet truby 17)")
