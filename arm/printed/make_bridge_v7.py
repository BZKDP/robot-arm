# -*- coding: utf-8 -*-
"""Final bridge V7/T5: another +5% after the V6 physical adjustment."""
from pathlib import Path

import numpy as np

import make_bridge_v5 as geometry


BASE = Path(__file__).resolve().parent
V6_TARGET_BC = 16.5 * 1.10 * 1.10
V7_TARGET_BC = V6_TARGET_BC * 1.05

# Nominal BC = 21.0 mm.  The whole fit window is shifted outward compared with
# V6, while the proven tube interface remains completely unchanged.
geometry.FLANGE_R_IN = 9.00
geometry.FLANGE_R_OUT = 12.00


def main():
    bridge = geometry.make_bridge()
    bridge_path = BASE / "flange_bridge_v7_FINAL_T5_PETG.stl"
    alias_path = BASE / "PLATE_BRIDGE_V7_FINAL.stl"

    bridge.export(bridge_path)
    bridge.export(alias_path)

    print("BRIDGE V7 FINAL", bridge_path)
    print("  watertight:", bridge.is_watertight)
    print("  extents:", np.round(bridge.extents, 3))
    print("  V6 target BC:", f"{V6_TARGET_BC:.3f} mm")
    print("  another +5% target BC:", f"{V7_TARGET_BC:.3f} mm")
    print("  V7 nominal BC: 21.000 mm")
    print("  V7 slot BC window: 18.00..24.00 mm")
    print("  tube interface: unchanged at +/-21.5 mm")


if __name__ == "__main__":
    main()

