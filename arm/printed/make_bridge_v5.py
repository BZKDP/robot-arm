# -*- coding: utf-8 -*-
"""
BRIDGE V5 / T5 for the measured 8 mm metal flange coupling.

Why V5 exists:
- the physical V4/T5 print still did not let all four flange screws line up;
- the last V4 generator accidentally reverted the flange hardware to M4 even
  though the digital-caliper branch established M3 flange screws;
- the user requested the flange hole pattern to move about 10% farther apart.

The flange interface is deliberately tolerant instead of being a single guessed
bolt circle:
  radial screw-centre range R=7.50..10.50 mm -> BC=15.0..21.0 mm.
This keeps the measured BC=16.5 mm, includes +10% (18.15 mm), and leaves extra
outward travel for real-part/print variation.  Slots are 4.0 mm wide for M3.

The already proven tube interface is unchanged:
- bridge 40 x 56 x 5 mm;
- tube bolts M4 at +/-21.5 mm, through holes 4.4 mm;
- head counterbores 8.4 x 3.0 mm on the coupling side;
- centre clearance 9.2 mm.

Outputs:
- flange_bridge_v5_T5_PETG.stl      final bridge to reprint;
- TEST_FLANGE_PATTERN_V5.stl        optional quick fit coupon;
- PLATE_BRIDGE_V5.stl               same final bridge, print-oriented alias.
"""

from pathlib import Path

import numpy as np
import trimesh


BASE = Path(r".\arm\printed")

W, L, T = 40.0, 56.0, 5.0
TUBE_BOLT_OFFSET = 21.5
CENTRE_D = 9.2
TUBE_HOLE_D = 4.4
TUBE_COUNTERBORE_D = 8.4
TUBE_COUNTERBORE_H = 3.0

# Metal flange -> bridge: M3, with a deliberately wide radial fit window.
FLANGE_SLOT_D = 4.0
FLANGE_R_IN = 7.50
FLANGE_R_OUT = 10.50
M3_NUT_POCKET_AF = 6.0
M3_NUT_POCKET_H = 2.8


def cyl(diameter, height, z0, x=0.0, y=0.0, sections=64):
    mesh = trimesh.creation.cylinder(
        radius=diameter / 2.0, height=height, sections=sections
    )
    mesh.apply_translation([x, y, z0 + height / 2.0])
    return mesh


def centred_box(sx, sy, sz, x=0.0, y=0.0, z0=0.0):
    mesh = trimesh.creation.box(extents=[sx, sy, sz])
    mesh.apply_translation([x, y, z0 + sz / 2.0])
    return mesh


def radial_slot(angle_rad, diameter, r_in, r_out, height, z0):
    """Capsule-shaped through slot whose centre can move from r_in to r_out."""
    ux, uy = np.cos(angle_rad), np.sin(angle_rad)
    bridge = trimesh.creation.box(extents=[r_out - r_in, diameter, height])
    bridge.apply_transform(
        trimesh.transformations.rotation_matrix(angle_rad, [0, 0, 1])
    )
    r_mid = (r_in + r_out) / 2.0
    bridge.apply_translation([r_mid * ux, r_mid * uy, z0 + height / 2.0])
    return trimesh.boolean.union(
        [
            cyl(diameter, height, z0, r_in * ux, r_in * uy, 32),
            cyl(diameter, height, z0, r_out * ux, r_out * uy, 32),
            bridge,
        ]
    )


def radial_nut_rail(angle_rad, r_in, r_out, z0):
    """Rectangular anti-rotation rail for an M3 nut over the whole slot range."""
    ux, uy = np.cos(angle_rad), np.sin(angle_rad)
    rail_length = (r_out - r_in) + M3_NUT_POCKET_AF
    rail = trimesh.creation.box(
        extents=[rail_length, M3_NUT_POCKET_AF, M3_NUT_POCKET_H]
    )
    rail.apply_transform(
        trimesh.transformations.rotation_matrix(angle_rad, [0, 0, 1])
    )
    r_mid = (r_in + r_out) / 2.0
    rail.apply_translation(
        [r_mid * ux, r_mid * uy, z0 + M3_NUT_POCKET_H / 2.0]
    )
    return rail


def make_flange_interface_cuts(thickness):
    cuts = [cyl(CENTRE_D, thickness + 2.0, -1.0)]
    for angle_deg in (45, 135, 225, 315):
        angle = np.radians(angle_deg)
        cuts.append(
            radial_slot(
                angle,
                FLANGE_SLOT_D,
                FLANGE_R_IN,
                FLANGE_R_OUT,
                thickness + 2.0,
                -1.0,
            )
        )
        cuts.append(
            radial_nut_rail(
                angle,
                FLANGE_R_IN,
                FLANGE_R_OUT,
                thickness - M3_NUT_POCKET_H,
            )
        )
    return cuts


def make_bridge():
    body = centred_box(W, L, T)
    cuts = make_flange_interface_cuts(T)
    for sign in (-1, 1):
        y = sign * TUBE_BOLT_OFFSET
        cuts.append(cyl(TUBE_HOLE_D, T + 2.0, -1.0, 0.0, y, 40))
        cuts.append(
            cyl(
                TUBE_COUNTERBORE_D,
                TUBE_COUNTERBORE_H,
                -0.01,
                0.0,
                y,
                48,
            )
        )
    return trimesh.boolean.difference([body] + cuts)


def make_coupon():
    # Large enough for the real 21.8 mm flange and fingers/nuts, but fast to print.
    coupon_w = coupon_l = 30.0
    body = centred_box(coupon_w, coupon_l, T)
    return trimesh.boolean.difference([body] + make_flange_interface_cuts(T))


def main():
    bridge = make_bridge()
    coupon = make_coupon()

    bridge_path = BASE / "flange_bridge_v5_T5_PETG.stl"
    alias_path = BASE / "PLATE_BRIDGE_V5.stl"
    coupon_path = BASE / "TEST_FLANGE_PATTERN_V5.stl"

    bridge.export(bridge_path)
    bridge.export(alias_path)
    coupon.export(coupon_path)

    print("BRIDGE", bridge_path)
    print("  watertight:", bridge.is_watertight)
    print("  extents:", np.round(bridge.extents, 3))
    print(
        "  flange slot BC window:",
        f"{2 * FLANGE_R_IN:.2f}..{2 * FLANGE_R_OUT:.2f} mm",
    )
    print("  requested +10% BC:", f"{16.5 * 1.10:.2f} mm")
    print("COUPON", coupon_path, "watertight:", coupon.is_watertight)


if __name__ == "__main__":
    main()
