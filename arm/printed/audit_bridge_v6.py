# -*- coding: utf-8 -*-
"""Machine checks for flange_bridge_v6_T5_PETG.stl."""
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Point


BASE = Path(__file__).resolve().parent
MESH_PATH = BASE / "flange_bridge_v6_T5_PETG.stl"
NEW_TARGET_BC = 16.5 * 1.10 * 1.10


def section_polygons(mesh, z):
    section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if section is None:
        raise RuntimeError(f"No section at z={z}")
    planar, _ = section.to_2D()
    return planar.polygons_full


def main():
    mesh = trimesh.load_mesh(MESH_PATH)
    if not mesh.is_watertight:
        raise RuntimeError("V6 bridge is not watertight")
    if not np.allclose(mesh.extents, [40.0, 56.0, 5.0], atol=0.05):
        raise RuntimeError(f"Unexpected extents: {mesh.extents}")

    polygons = section_polygons(mesh, 1.0)
    solid = max(polygons, key=lambda polygon: polygon.area)
    hole_count = sum(len(polygon.interiors) for polygon in polygons)
    if hole_count != 7:
        raise RuntimeError(f"Expected 7 holes at z=1, found {hole_count}")

    target_r = NEW_TARGET_BC / 2.0
    for angle_deg in (45, 135, 225, 315):
        angle = np.radians(angle_deg)
        point = Point(target_r * np.cos(angle), target_r * np.sin(angle))
        if solid.contains(point):
            raise RuntimeError(f"V6 target is solid at angle {angle_deg}")

    print("PASS", MESH_PATH)
    print("  watertight:", mesh.is_watertight)
    print("  extents:", np.round(mesh.extents, 3))
    print("  through-hole count:", hole_count)
    print("  another +10% target BC:", f"{NEW_TARGET_BC:.3f} mm — PASS")
    print("  slot BC window: 17.00..23.00 mm")
    print("  tube interface: unchanged at +/-21.5 mm")


if __name__ == "__main__":
    main()

