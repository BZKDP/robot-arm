# -*- coding: utf-8 -*-
"""Render the current J1/J2/J5 printed-part set for visual engineering review."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


BASE = Path(r".\arm\printed")
OUTPUT = BASE / "_current_parts_review.png"

PARTS = [
    ("Gearbox adapter J2/J5 v2", "gearbox_adapter_J2_v2.stl"),
    ("Bridge V7/T5 — final +5%", "flange_bridge_v7_FINAL_T5_PETG.stl"),
    ("Nut cassette v4 (two parts)", "nut_cassette_v4_x2_PETG.stl"),
    ("Tube drill jig v4", "drill_jig_v4_PETG.stl"),
    ("Roll cup V3 — print-stable NEMA17", "roll_mount_v3_FINAL_PRINTSAFE_PETG.stl"),
    ("Wrist cup — NEMA14 (prototype; needs V2)", "wrist_mount_N14_PETG.stl"),
    ("AS5600 canopy", "as5600_bracket_PETG.stl"),
]


def draw(ax, mesh, title):
    triangles = mesh.triangles
    # Large boolean meshes can be visually reviewed with a representative face set.
    if len(triangles) > 14000:
        step = int(np.ceil(len(triangles) / 14000))
        triangles = triangles[::step]
    collection = Poly3DCollection(
        triangles,
        facecolor="#e5a343",
        edgecolor="#674116",
        linewidth=0.08,
        alpha=0.96,
    )
    ax.add_collection3d(collection)
    centre = mesh.bounds.mean(axis=0)
    span = max(mesh.extents) / 2.0 * 1.15
    ax.set_xlim(centre[0] - span, centre[0] + span)
    ax.set_ylim(centre[1] - span, centre[1] + span)
    ax.set_zlim(centre[2] - span * 0.55, centre[2] + span * 0.75)
    ax.view_init(elev=30, azim=-48)
    ax.set_title(
        f"{title}\n{mesh.extents[0]:.1f} × {mesh.extents[1]:.1f} × {mesh.extents[2]:.1f} mm",
        fontsize=10,
    )
    ax.set_axis_off()


def main():
    fig = plt.figure(figsize=(18, 12))
    for index, (title, filename) in enumerate(PARTS, start=1):
        path = BASE / filename
        mesh = trimesh.load_mesh(path)
        if not mesh.is_watertight:
            raise RuntimeError(f"Not watertight: {path}")
        ax = fig.add_subplot(2, 4, index, projection="3d")
        draw(ax, mesh, title)

    ax = fig.add_subplot(2, 4, 8)
    ax.axis("off")
    ax.text(
        0.02,
        0.96,
        "CURRENT REVIEW SET\n\n"
        "Exact joint:\n"
        "gearbox + adapter v2\n"
        "metal flange coupling\n"
        "bridge V7/T5\n"
        "20x20 tube + cassette\n"
        "OD8 support axle\n"
        "diagonal flange bearing\n"
        "AS5600 canopy\n\n"
        "Roll and wrist cups are separate\n"
        "end-of-link modules.\n\n"
        "All seven STL meshes: watertight.",
        va="top",
        family="monospace",
        fontsize=12,
    )
    fig.suptitle("ROBOARM — CURRENT PRINTED PARTS VISUAL REVIEW", fontsize=16, weight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT, dpi=180)
    plt.close(fig)
    print("PASS", OUTPUT)


if __name__ == "__main__":
    main()
