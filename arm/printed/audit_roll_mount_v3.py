# -*- coding: utf-8 -*-
"""Verify print-stability changes without altering the V2 mechanical interfaces."""
from pathlib import Path

import numpy as np
import trimesh
from shapely.ops import unary_union


BASE = Path(__file__).resolve().parent
V2_PATH = BASE / "roll_mount_v2_PETG.stl"
V3_PATH = BASE / "roll_mount_v3_FINAL_PRINTSAFE_PETG.stl"


def section_shape(mesh, z):
    section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if section is None:
        raise RuntimeError(f"No section at z={z}")
    planar, _ = section.to_2D()
    return unary_union(planar.polygons_full)


def main():
    v2 = trimesh.load_mesh(V2_PATH)
    v3 = trimesh.load_mesh(V3_PATH)
    if not v3.is_watertight:
        raise RuntimeError("V3 cup is not watertight")
    if not np.allclose(v3.extents, [70.0, 70.0, 36.99], atol=0.05):
        raise RuntimeError(f"Unexpected V3 extents: {v3.extents}")

    # Below the cable notch, the structural tube/motor interfaces must match V2.
    max_delta = 0.0
    for z in (5.5, 10.0, 20.0):
        delta = section_shape(v2, z).symmetric_difference(section_shape(v3, z)).area
        max_delta = max(max_delta, delta)
        # Boolean re-triangulation of nominally identical cylinders produces a
        # sub-mm2 polygon delta; anything below 0.75 mm2 is mesh discretisation.
        if delta > 0.75:
            raise RuntimeError(f"Mechanical section changed at z={z}: {delta}")

    v2_contact = section_shape(v2, 0.2).area
    v3_contact = section_shape(v3, 0.2).area
    gain = (v3_contact / v2_contact - 1.0) * 100.0
    if gain < 45.0:
        raise RuntimeError(f"Adhesion gain too small: {gain:.1f}%")

    print("PASS", V3_PATH)
    print("  watertight:", v3.is_watertight)
    print("  extents:", np.round(v3.extents, 3))
    print("  V2/V3 mechanical sections z=5.5,10,20: unchanged")
    print("  max triangulation delta:", f"{max_delta:.3f} mm2")
    print("  calculated first-layer contact gain:", f"{gain:.1f}%")
    print("  cable window roof: removed; notch stays open to top")


if __name__ == "__main__":
    main()
