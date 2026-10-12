# -*- coding: utf-8 -*-
"""Bridge V6/T5: move the tested V5 flange pattern another 10% outward."""
from pathlib import Path

import numpy as np

import make_bridge_v5 as geometry


BASE = Path(__file__).resolve().parent
PREVIOUS_TARGET_BC = 16.5 * 1.10
NEW_TARGET_BC = PREVIOUS_TARGET_BC * 1.10

# Nominal BC = 20.0 mm; physical fit window BC = 17.0..23.0 mm.
geometry.FLANGE_R_IN = 8.50
geometry.FLANGE_R_OUT = 11.50


def main():
    bridge = geometry.make_bridge()
    coupon = geometry.make_coupon()

    bridge_path = BASE / "flange_bridge_v6_T5_PETG.stl"
    alias_path = BASE / "PLATE_BRIDGE_V6.stl"
    coupon_path = BASE / "TEST_FLANGE_PATTERN_V6_PLUS10.stl"

    bridge.export(bridge_path)
    bridge.export(alias_path)
    coupon.export(coupon_path)

    print("BRIDGE V6", bridge_path)
    print("  watertight:", bridge.is_watertight)
    print("  extents:", np.round(bridge.extents, 3))
    print("  previous V5 target BC:", f"{PREVIOUS_TARGET_BC:.3f} mm")
    print("  another +10% target BC:", f"{NEW_TARGET_BC:.3f} mm")
    print("  V6 nominal BC: 20.000 mm")
    print("  V6 slot BC window: 17.00..23.00 mm")
    print("COUPON V6", coupon_path, "watertight:", coupon.is_watertight)


if __name__ == "__main__":
    main()

