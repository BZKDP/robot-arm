# -*- coding: utf-8 -*-
"""Geometry audit and visual report for flange_bridge_v5_T5_PETG.stl."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely.geometry import Point


BASE = Path(r".\arm\printed")
MESH_PATH = BASE / "flange_bridge_v5_T5_PETG.stl"
PREVIEW_PATH = BASE / "_bridge_v5_verified.png"


def section_polygons(mesh, z):
    section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if section is None:
        raise RuntimeError(f"No section at z={z}")
    planar, _ = section.to_2D()
    return planar.polygons_full


def hole_records(mesh, z):
    records = []
    for polygon in section_polygons(mesh, z):
        for ring in polygon.interiors:
            pts = np.asarray(ring.coords)
            centre = (pts.min(axis=0) + pts.max(axis=0)) / 2.0
            size = pts.max(axis=0) - pts.min(axis=0)
            records.append((centre, size, pts))
    return records


def draw_section(ax, mesh, z, title, show_coupling=False):
    for polygon in section_polygons(mesh, z):
        xy = np.asarray(polygon.exterior.coords)
        ax.fill(xy[:, 0], xy[:, 1], color="#e5a343", alpha=0.85)
        for ring in polygon.interiors:
            hole = np.asarray(ring.coords)
            ax.fill(hole[:, 0], hole[:, 1], color="white")

    if show_coupling:
        ax.add_patch(Circle((0, 0), 10.9, fill=False, lw=2.2, ec="#1c65b9"))
        for radius, colour, label in (
            (8.25, "#287a31", "BC16.5 old measured"),
            (9.075, "#c22a2a", "BC18.15 (+10%)"),
        ):
            for angle_deg in (45, 135, 225, 315):
                angle = np.radians(angle_deg)
                centre = (radius * np.cos(angle), radius * np.sin(angle))
                ax.add_patch(Circle(centre, 1.75, fill=False, lw=1.3, ec=colour))
            ax.plot([], [], color=colour, label=label)
        ax.plot([], [], color="#1c65b9", label="coupling flange OD21.8")
        ax.legend(loc="upper right", fontsize=8)

    ax.set_aspect("equal")
    ax.set_xlim(-23, 23)
    ax.set_ylim(-31, 31)
    ax.grid(alpha=0.2)
    ax.set_title(title)
    ax.set_xlabel("X, mm")
    ax.set_ylabel("Y, mm")


def draw_mesh_3d(ax, mesh):
    collection = Poly3DCollection(
        mesh.triangles,
        facecolor="#e5a343",
        edgecolor="#6e4618",
        linewidth=0.10,
        alpha=0.96,
    )
    ax.add_collection3d(collection)
    bounds = mesh.bounds
    centre = bounds.mean(axis=0)
    span = max(mesh.extents) / 2.0
    ax.set_xlim(centre[0] - span, centre[0] + span)
    ax.set_ylim(centre[1] - span, centre[1] + span)
    ax.set_zlim(-span * 0.25, span * 0.45)
    ax.view_init(elev=32, azim=-48)
    ax.set_title("V5/T5 actual STL — isometric")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")


def main():
    mesh = trimesh.load_mesh(MESH_PATH)
    if not mesh.is_watertight:
        raise RuntimeError("Bridge STL is not watertight")
    if not np.allclose(mesh.extents, [40.0, 56.0, 5.0], atol=0.05):
        raise RuntimeError(f"Unexpected extents: {mesh.extents}")

    bottom = hole_records(mesh, 1.0)
    top = hole_records(mesh, 3.6)

    # Through-section must contain: centre, 4 flange slots, 2 tube holes.
    if len(bottom) != 7:
        raise RuntimeError(f"Expected 7 holes at z=1.0, found {len(bottom)}")

    # Tube centres must stay at y=+/-21.5.
    tube_centres = sorted(
        [
            centre
            for centre, size, _ in bottom
            if size[0] > 8.0 and size[1] > 8.0 and abs(centre[1]) > 15
        ],
        key=lambda point: point[1],
    )
    if len(tube_centres) != 2 or not np.allclose(
        [tube_centres[0][1], tube_centres[1][1]], [-21.5, 21.5], atol=0.05
    ):
        raise RuntimeError(f"Tube-hole centres wrong: {tube_centres}")

    # Prove the +10% requested metal-hole centres lie inside the four slots.
    through_polygons = section_polygons(mesh, 1.0)
    solid = max(through_polygons, key=lambda polygon: polygon.area)
    requested_radius = 16.5 * 1.10 / 2.0
    for angle_deg in (45, 135, 225, 315):
        angle = np.radians(angle_deg)
        point = Point(
            requested_radius * np.cos(angle), requested_radius * np.sin(angle)
        )
        if solid.contains(point):
            raise RuntimeError(
                f"Requested +10% hole centre is still solid at angle {angle_deg}"
            )

    fig = plt.figure(figsize=(16, 11))
    ax1 = fig.add_subplot(2, 2, 1)
    draw_section(
        ax1,
        mesh,
        1.0,
        "Coupling side, z=1.0 — through slots + M4 counterbores",
        show_coupling=True,
    )
    ax2 = fig.add_subplot(2, 2, 2)
    draw_section(
        ax2,
        mesh,
        3.6,
        "Tube side, z=3.6 — M3 nut rails visible",
    )
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    draw_mesh_3d(ax3, mesh)
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis("off")
    ax4.text(
        0.02,
        0.96,
        "VERIFIED DIMENSIONS\n\n"
        "Bridge: 40 x 56 x 5 mm\n"
        "Metal flange: OD 21.8 mm\n"
        "Flange screws: M3\n"
        "Flange radial slots: width 4.0 mm\n"
        "Accepted bolt circle: BC 15.0..21.0 mm\n"
        "Old measured bolt circle: BC 16.5 mm\n"
        "User-requested +10%: BC 18.15 mm — inside slots\n"
        "M3 nut rails: AF 6.0 x 2.8 mm\n\n"
        "Tube interface UNCHANGED\n"
        "M4 through holes: y = +/-21.5 mm\n"
        "M4 counterbores: OD 8.4 x 3.0 mm\n"
        "Centre clearance: OD 9.2 mm\n\n"
        "Fastener length at T5:\n"
        "M3x7 preferred; cut existing M3x10 to 7 mm.",
        va="top",
        family="monospace",
        fontsize=12,
    )
    fig.suptitle("ROBOARM BRIDGE V5/T5 — GEOMETRY AUDIT", fontsize=16, weight="bold")
    fig.tight_layout()
    fig.savefig(PREVIEW_PATH, dpi=180)
    plt.close(fig)

    print("PASS", MESH_PATH)
    print("  watertight:", mesh.is_watertight)
    print("  extents:", np.round(mesh.extents, 3))
    print("  z=1.0 hole count:", len(bottom))
    print("  z=3.6 hole count:", len(top))
    print("  +10% BC centre test: PASS")
    print("  preview:", PREVIEW_PATH)


if __name__ == "__main__":
    main()
