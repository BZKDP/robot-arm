# -*- coding: utf-8 -*-
"""
Generate printable V1 parts for one open robot-arm joint module.

Target hardware:
- NEMA17 42 mm motor
- CM36-style planetary gearbox, about 36 mm body diameter
- 8 mm gearbox output shaft
- AS5600 board + 6x2 mm diametric magnet
- GX12-8 panel connector

This is a quick open prototype frame, not the final load-bearing joint.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


OUT_DIR = Path(__file__).resolve().parent


P = {
    # Measured/assumed hardware dimensions in mm.
    "motor_square": 42.3,
    "motor_connector_clearance_width": 54.0,
    "gearbox_diameter": 36.0,
    "gearbox_body_length": 40.0,
    "motor_body_length": 42.0,
    "body_length_motor_plus_gearbox": 82.0,
    "total_length_with_output_shaft": 100.0,
    "shaft_diameter": 8.0,
    # Print-fit clearances.
    "motor_gap_y": 56.0,
    "axis_z": 31.0,
}


def mat_translate(center):
    m = np.eye(4)
    m[:3, 3] = center
    return m


def box(name, extents, center):
    mesh = trimesh.creation.box(extents=extents)
    mesh.apply_translation(center)
    mesh.metadata["name"] = name
    return mesh


def cylinder(name, radius, height, center, axis="z", sections=96):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    if axis == "x":
        mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], [1, 0, 0]))
    elif axis == "y":
        mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], [0, 1, 0]))
    elif axis != "z":
        raise ValueError(axis)
    mesh.apply_translation(center)
    mesh.metadata["name"] = name
    return mesh


def boolean_union(meshes, name):
    meshes = [m for m in meshes if m is not None]
    try:
        out = trimesh.boolean.union(meshes, engine="manifold")
        if out is not None:
            out.metadata["name"] = name
            return out
    except BaseException as exc:
        print(f"union fallback for {name}: {exc}")
    out = trimesh.util.concatenate(meshes)
    out.merge_vertices()
    out.metadata["name"] = name
    return out


def boolean_difference(base, cuts, name):
    cuts = [c for c in cuts if c is not None]
    try:
        out = trimesh.boolean.difference([base] + cuts, engine="manifold")
        if out is not None:
            out.metadata["name"] = name
            return out
    except BaseException as exc:
        print(f"difference fallback for {name}: {exc}")
    base.metadata["name"] = name
    return base


def export_mesh(mesh, filename):
    if hasattr(mesh, "unique_faces"):
        mesh.update_faces(mesh.unique_faces())
    if hasattr(mesh, "nondegenerate_faces"):
        mesh.update_faces(mesh.nondegenerate_faces())
    mesh.merge_vertices()
    mesh.fix_normals()
    path = OUT_DIR / filename
    mesh.export(path)
    print(f"{filename}: watertight={mesh.is_watertight}, extents={np.round(mesh.extents, 2)}, file={path}")
    return path


def make_open_frame():
    # Coordinate system:
    # X = motor axis, rear motor side negative, output shaft positive.
    # Y = module width, Z = height from print bed.
    axis_z = P["axis_z"]

    parts = []
    parts.append(box("base_plate", [140, 80, 5], [15, 0, 2.5]))

    # Two tall side cheeks. Internal gap is wide enough for the motor connector side.
    parts.append(box("left_side_cheek", [108, 7, 32], [0, -31.5, 22]))
    parts.append(box("right_side_cheek", [108, 7, 32], [0, 31.5, 22]))

    # Rear and front bottom cross braces; top stays open.
    parts.append(box("rear_cross_brace", [8, 68, 12], [-54, 0, 11]))
    parts.append(box("front_cross_brace", [8, 68, 12], [50, 0, 11]))

    # Gearbox lower cradle: shallow V-like support made from two small rails.
    parts.append(box("motor_left_low_saddle", [48, 6, 7], [-25, -15.5, 9.5]))
    parts.append(box("motor_right_low_saddle", [48, 6, 7], [-25, 15.5, 9.5]))
    parts.append(box("gearbox_left_low_saddle", [52, 6, 7], [24, -15.5, 9.5]))
    parts.append(box("gearbox_right_low_saddle", [52, 6, 7], [24, 15.5, 9.5]))

    # AS5600 holder plate. Mount the board on the inner face, facing the shaft magnet.
    parts.append(box("as5600_vertical_plate", [6, 44, 46], [70, 0, axis_z]))
    parts.append(box("as5600_bottom_gusset", [26, 38, 5], [59, 0, 7.5]))

    # GX12-8 side panel; panel-mount hole is cut later.
    parts.append(box("gx12_side_panel", [38, 6, 36], [-34, 45, 28]))
    parts.append(box("gx12_panel_gusset", [36, 18, 6], [-34, 37, 10]))

    body = boolean_union(parts, "joint_module_open_frame_v1")

    cuts = []
    # Base mounting holes, M4 clearance.
    for x in (-45, 75):
        for y in (-30, 30):
            cuts.append(cylinder("m4_base_hole", 2.25, 10, [x, y, 2.5], axis="z", sections=48))

    # Zip-tie slots through base: two straps around motor/gearbox.
    for x in (-30, 22):
        for y in (-24, 24):
            cuts.append(box("zip_slot", [8, 8, 12], [x, y, 2.5]))

    # AS5600 mounting holes, loose 3.2 mm. Spacing is deliberately generic for first fit.
    for y in (-10, 10):
        for z in (axis_z - 10, axis_z + 10):
            cuts.append(cylinder("as5600_mount_hole", 1.65, 12, [70, y, z], axis="x", sections=32))
    # Center peephole helps align the AS5600 chip with the magnet.
    cuts.append(cylinder("as5600_center_window", 4.0, 12, [70, 0, axis_z], axis="x", sections=48))

    # GX12 panel connector hole.
    cuts.append(cylinder("gx12_12mm_hole", 6.25, 12, [-34, 45, 28], axis="y", sections=64))

    return boolean_difference(body, cuts, "joint_module_open_frame_v1")


def make_magnet_cap():
    # Print upright. Bottom hole pushes onto 8 mm output shaft; top pocket gets the AS5600 magnet.
    body = cylinder("shaft_magnet_cap_8mm_v1", 7.0, 13.0, [0, 0, 6.5], axis="z", sections=96)
    cuts = [
        cylinder("shaft_bore_8_3", 4.15, 9.4, [0, 0, 4.7], axis="z", sections=96),
        cylinder("magnet_pocket_6_2", 3.15, 2.6, [0, 0, 11.7], axis="z", sections=96),
        cylinder("m3_set_screw_pilot", 1.6, 18, [0, 0, 5.0], axis="x", sections=32),
    ]
    return boolean_difference(body, cuts, "shaft_magnet_cap_8mm_v1")


def make_output_flange_hub():
    # Optional rotating hub: more useful when we start attaching the next link.
    parts = [
        cylinder("hub_barrel", 10.5, 15.0, [0, 0, 7.5], axis="z", sections=128),
        cylinder("front_flange", 21.0, 5.0, [0, 0, 13.0], axis="z", sections=128),
    ]
    body = boolean_union(parts, "output_hub_8mm_flange_as5600_v1")
    cuts = [
        cylinder("shaft_bore_8_3", 4.15, 13.0, [0, 0, 6.5], axis="z", sections=96),
        cylinder("magnet_pocket_6_2", 3.15, 2.6, [0, 0, 15.2], axis="z", sections=96),
        cylinder("m3_set_screw_pilot", 1.6, 26, [0, 0, 6.0], axis="x", sections=32),
    ]
    # Four M4 clearance holes around flange face.
    for a in np.linspace(0, 2 * np.pi, 4, endpoint=False) + np.pi / 4:
        cuts.append(cylinder("m4_link_hole", 2.25, 8, [15 * np.cos(a), 15 * np.sin(a), 13.0], axis="z", sections=40))
    return boolean_difference(body, cuts, "output_hub_8mm_flange_as5600_v1")


def make_preview(meshes):
    fig = plt.figure(figsize=(11, 7), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    colors = ["#93c5fd", "#fca5a5", "#86efac"]
    offsets = [0, 95, 135]
    for idx, mesh in enumerate(meshes):
        m = mesh.copy()
        m.apply_translation([offsets[idx], 0, 0])
        collection = Poly3DCollection(m.triangles, linewidths=0.05, alpha=0.92)
        collection.set_facecolor(colors[idx % len(colors)])
        collection.set_edgecolor("#334155")
        ax.add_collection3d(collection)
    ax.set_xlim(-70, 170)
    ax.set_ylim(-65, 65)
    ax.set_zlim(0, 80)
    ax.set_xlabel("X mm")
    ax.set_ylabel("Y mm")
    ax.set_zlabel("Z mm")
    ax.view_init(elev=25, azim=-55)
    ax.set_title("joint_module_v1 STL preview")
    fig.tight_layout()
    path = OUT_DIR / "joint_module_v1_preview.png"
    fig.savefig(path, dpi=150)
    print(f"preview={path}")
    return path


def write_readme(paths):
    readme = OUT_DIR / "README_PRINT_THIS_FIRST.md"
    readme.write_text(
        "\n".join(
            [
                "# Joint module V1 print pack",
                "",
                "Printer target: Creality Ender 3 V3 SE / 220x220x250 mm.",
                "",
                "Files:",
                "- joint_module_open_frame_v1.stl: open frame for NEMA17 + CM36 gearbox + AS5600 + GX12-8.",
                "- shaft_magnet_cap_8mm_v1.stl: small 8 mm shaft cap with magnet pocket; print this first for AS5600 testing.",
                "- output_hub_8mm_flange_as5600_v1.stl: optional rotating output hub with 4x M4 link holes and magnet pocket.",
                "",
                "Recommended first print:",
                "- Material: PLA+ or PETG.",
                "- Layer height: 0.20 mm.",
                "- Walls: 4.",
                "- Infill: 35-45%.",
                "- Supports: off for the open frame; the small horizontal holes can bridge.",
                "- Brim: on for the open frame if bed adhesion is weak.",
                "",
                "Important:",
                "- This is V1 for fitting and bench tests, not the final heavy-load joint.",
                "- AS5600 board mounts on the inner side of the vertical sensor plate.",
                "- Magnet goes into the 6.2 mm pocket; the magnet face must be centered on the shaft axis.",
                "- The 8.3 mm shaft hole is intentionally loose. Use the M3 pilot hole as a set screw/tap point.",
                "",
                "Generated files:",
                *[f"- {p.name}" for p in paths],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"readme={readme}")


def main():
    frame = make_open_frame()
    cap = make_magnet_cap()
    hub = make_output_flange_hub()
    paths = [
        export_mesh(frame, "joint_module_open_frame_v1.stl"),
        export_mesh(cap, "shaft_magnet_cap_8mm_v1.stl"),
        export_mesh(hub, "output_hub_8mm_flange_as5600_v1.stl"),
    ]
    make_preview([frame, cap, hub])
    write_readme(paths)


if __name__ == "__main__":
    main()
