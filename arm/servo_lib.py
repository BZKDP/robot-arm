# -*- coding: utf-8 -*-
# Parametricheskaya biblioteka servo-brekketov dlya robo-ruki.
# Generit STL cherez trimesh + manifold (boolean). Vse razmery v mm.
import trimesh
import numpy as np

def box(sx, sy, sz, t=(0, 0, 0)):
    m = trimesh.creation.box(extents=(sx, sy, sz))
    m.apply_translation(t)
    return m

def cyl(r, h, t=(0, 0, 0), sections=64, axis='z'):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    if axis == 'x':
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    elif axis == 'y':
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]))
    m.apply_translation(t)
    return m

def diff(a, b):
    return trimesh.boolean.difference([a, b], engine='manifold')

def union(parts):
    return trimesh.boolean.union(parts, engine='manifold')

# --- Specifikacii servo (standartnyy razmer) ---
# FB5118M: korpus 40.1 x 20.1 x 38.9, shlic 25T/9.5mm, JR. Montazhnye otverstiya -
# standart "standard servo": pryamougolnik 49.5 x 10 mm, 4 otv. PROVERYAEM kuponom!
FB5118M = dict(
    body_l=40.1, body_w=20.1, body_h=38.9,
    hole_dx=49.5, hole_dy=10.0, hole_d=4.5,   # montazhnyy pryamougolnik + diametr
    shaft_off=10.0,                           # smeshenie vala ot centra korpusa (dlina)
    spline_d=9.5, horn_screw_d=2.3,           # 25T, vint kachalki M2.x
)

def test_coupon(spec=FB5118M, plate_t=4.0, path=None):
    """Ploskaya plastina dlya proverki montazhnyh otverstiy + footprint korpusa."""
    s = spec
    L = s['hole_dx'] + s['hole_d'] + 15    # zapas po dline
    W = max(s['body_w'] + 9, s['hole_dy'] + 14)
    plate = box(L, W, plate_t, (0, 0, plate_t/2))
    cuts = []
    # 4 montazhnyh otverstiya
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(s['hole_d']/2, plate_t+4,
                            (sx*s['hole_dx']/2, sy*s['hole_dy']/2, plate_t/2)))
    # sloty pod korpus servo (chtob telo proshlo, taby legli na plastinu)
    cuts.append(box(s['body_l']+0.6, s['body_w']+0.6, plate_t+4, (0, 0, plate_t/2)))
    # centralnoe otverstie pod val (proverit smeshenie)
    cuts.append(cyl(s['spline_d']/2+1.5, plate_t+4, (s['shaft_off'], 0, plate_t/2)))
    m = diff(plate, union(cuts))
    if path:
        m.export(path)
    return m

if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else 'test_coupon_fb5118m.stl'
    m = test_coupon(path=out)
    print('exported', out, 'verts', len(m.vertices), 'watertight', m.is_watertight)
