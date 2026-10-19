#!/usr/bin/env python3
"""Printable 奶蛙 figurine: sitting, clutching its belly, laughing.

Units are millimetres. The mesh is a single solid, trimmed flat on the
bottom so it sits on a print bed.
"""

from __future__ import annotations

import os

import manifold3d as m3d
import numpy as np
import trimesh

M = m3d.Manifold
ADD = m3d.OpType.Add
SUB = m3d.OpType.Subtract

# Geodesic spheres round to a multiple of 4. 64 keeps the figurine smooth
# without making the booleans unwieldy.
SEG = 64
SEG_S = 32


def sphere(r: float, c, seg: int = SEG) -> M:
    return M.sphere(r, seg).translate([float(c[0]), float(c[1]), float(c[2])])


def ellipsoid(radii, c, seg: int = SEG) -> M:
    return M.sphere(1.0, seg).scale([float(radii[0]), float(radii[1]), float(radii[2])]).translate(
        [float(c[0]), float(c[1]), float(c[2])]
    )


def _rotation_from_z(direction: np.ndarray) -> np.ndarray:
    z = np.array([0.0, 0.0, 1.0])
    d = direction / np.linalg.norm(direction)
    cross = np.cross(z, d)
    s = np.linalg.norm(cross)
    c = float(np.dot(z, d))
    if s < 1e-8:
        if c > 0:
            return np.eye(3)
        return np.diag([1.0, -1.0, -1.0])
    axis = cross / s
    # Rodrigues
    k = np.array(
        [
            [0.0, -axis[2], axis[1]],
            [axis[2], 0.0, -axis[0]],
            [-axis[1], axis[0], 0.0],
        ]
    )
    return np.eye(3) + k * s + (k @ k) * (1.0 - c)


def capsule(p0, p1, r: float, seg: int = SEG_S) -> M:
    a = np.asarray(p0, dtype=float)
    b = np.asarray(p1, dtype=float)
    d = b - a
    length = float(np.linalg.norm(d))
    if length < 1e-6:
        return sphere(r, a, seg)
    rot = _rotation_from_z(d)
    # 3x4 matrix: rotation columns, then translation of the start point.
    mat = np.zeros((3, 4), dtype=float)
    mat[:, :3] = rot
    mat[:, 3] = a
    tube = M.cylinder(length, r, r, seg, center=False).transform(mat.tolist())
    return tube + sphere(r, a, seg) + sphere(r, b, seg)


def rotate_around(solid: M, euler_deg, pivot) -> M:
    px, py, pz = (float(pivot[0]), float(pivot[1]), float(pivot[2]))
    return solid.translate([-px, -py, -pz]).rotate(list(euler_deg)).translate([px, py, pz])


def build() -> M:
    """Y- is the face. Z is up. One round body, thrown back in a laugh."""

    # A milk frog is almost a single cream-colored ball.
    body = ellipsoid((27.0, 25.0, 23.5), (0.0, 0.5, 31.0))
    # Extra belly the hands can press into, and a rump so the sit has weight.
    belly = ellipsoid((18.0, 16.0, 15.0), (0.0, -8.0, 27.0))
    rump = ellipsoid((18.0, 14.0, 13.0), (0.0, 10.0, 24.0))
    # Fills the pocket under the belly so the sit prints as one solid.
    crotch = ellipsoid((14.0, 16.0, 10.0), (0.0, -2.0, 12.0), SEG_S)

    eyes = []
    pupils = []
    for sx in (-1.0, 1.0):
        # Bulging eyes on the upper front of the head.
        c = (sx * 9.2, -14.5, 45.5)
        eyes.append(ellipsoid((7.0, 6.2, 6.4), c))
        # Lowered lid: the eye reads as a laughing squint, not a stare.
        eyes.append(ellipsoid((7.4, 4.2, 3.4), (c[0], c[1] - 1.6, c[2] + 3.6), SEG_S))
        # Wide horizontal pupil, classic frog, sunk into the front surface.
        pupils.append(ellipsoid((2.5, 1.15, 0.85), (c[0], c[1] - 5.5, c[2] - 0.6), 28))

    nostrils = [
        sphere(0.95, (-2.7, -23.4, 40.6), 24),
        sphere(0.95, (2.7, -23.4, 40.6), 24),
    ]

    # Open grin. The cutter only bites a few millimetres into the face,
    # and the plug puts back the upper half so the corners turn up.
    mouth_cut = ellipsoid((15.0, 6.4, 8.4), (0.0, -24.2, 32.2))
    mouth_plug = ellipsoid((11.4, 5.8, 5.4), (0.0, -23.4, 36.8))
    tongue = ellipsoid((8.2, 4.6, 2.3), (0.0, -24.8, 29.2), SEG_S)

    arms = []
    for sx in (-1.0, 1.0):
        # Elbows out, palms flat on the lower belly.
        shoulder = (sx * 17.5, -2.0, 30.0)
        elbow = (sx * 26.5, -8.0, 21.5)
        wrist = (sx * 9.5, -18.5, 17.5)
        arms.append(capsule(shoulder, elbow, 4.6))
        arms.append(capsule(elbow, wrist, 3.9))
        arms.append(ellipsoid((6.2, 4.4, 3.6), (sx * 6.2, -20.2, 17.2), SEG_S))
        for fx, fz in ((3.4, 1.5), (1.5, -0.2), (2.6, -1.8)):
            root = (sx * 4.8, -20.6, 16.8 + fz)
            tip = (sx * fx, -25.4, 16.0 + fz)
            arms.append(capsule(root, tip, 1.8, 24))
        arms.append(capsule((sx * 9.2, -18.6, 19.6), (sx * 6.2, -23.6, 21.0), 1.9, 24))

    legs = []
    for sx in (-1.0, 1.0):
        hip = (sx * 9.0, 5.0, 16.0)
        knee = (sx * 22.0, 1.0, 11.5)
        ankle = (sx * 16.0, -16.0, 7.5)
        legs.append(capsule(hip, knee, 6.4))
        legs.append(capsule(knee, ankle, 5.2))
        legs.append(ellipsoid((7.2, 10.5, 3.8), (sx * 15.5, -22.5, 5.4), SEG_S))
        for spread in (-4.4, 0.0, 4.4):
            root = (sx * 15.5 + spread * 0.25, -29.0, 4.4)
            tip = (sx * 15.5 + spread, -35.5, 3.4)
            legs.append(capsule(root, tip, 1.85, 24))

    parts = [body, belly, rump, crotch, tongue] + eyes + arms + legs
    solid = M.batch_boolean(parts, ADD)
    opening = mouth_cut - mouth_plug
    solid = M.batch_boolean([solid, opening] + nostrils + pupils, SUB)

    # Thrown backward around the hips: the laugh, not a bow.
    solid = rotate_around(solid, (-13.0, 0.0, 0.0), (0.0, 2.0, 14.0))

    bb = solid.bounding_box()
    solid = solid.translate([0.0, 0.0, -bb[2] - 1.6])
    solid = solid.trim_by_plane([0.0, 0.0, 1.0], 0.0)

    bb = solid.bounding_box()
    cx = (bb[0] + bb[3]) * 0.5
    cy = (bb[1] + bb[4]) * 0.5
    plinth = ellipsoid(
        ((bb[3] - bb[0]) * 0.42 + 6.0, (bb[4] - bb[1]) * 0.40 + 5.0, 2.8),
        (cx, cy, 1.2),
        SEG,
    )
    plinth = plinth.trim_by_plane([0.0, 0.0, 1.0], 0.0).trim_by_plane([0.0, 0.0, -1.0], -3.0)
    solid = (solid + plinth).trim_by_plane([0.0, 0.0, 1.0], 0.0)

    # Comfortable desk size. Scale about the origin, then sit it back on z=0.
    bb = solid.bounding_box()
    height = bb[5] - bb[2]
    s = 80.0 / height
    solid = solid.scale([s, s, s])
    bb = solid.bounding_box()
    solid = solid.translate([0.0, 0.0, -bb[2]])

    # Boolean seams can leave a paper-thin shell in front of the mouth.
    pieces = solid.decompose()
    solid = max(pieces, key=lambda piece: piece.volume())
    return solid


def to_trimesh(solid: M) -> trimesh.Trimesh:
    mesh = solid.to_mesh()
    vertices = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    faces = np.asarray(mesh.tri_verts, dtype=np.int64)
    tri = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    tri.update_faces(tri.unique_faces())
    tri.remove_unreferenced_vertices()
    tri.fix_normals()
    return tri


def _shade_view(tri: trimesh.Trimesh, view, up, width: int, height: int):
    """Orthographic shaded render. Returns a PIL image of the given pixel size."""
    from PIL import Image, ImageDraw

    view = np.asarray(view, dtype=float)
    view = view / np.linalg.norm(view)
    up = np.asarray(up, dtype=float)
    right = np.cross(up, view)
    right = right / np.linalg.norm(right)
    up = np.cross(view, right)

    v = tri.vertices
    faces = tri.faces
    tris = v[faces]
    centers = tris.mean(axis=1)
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
    light = np.array([0.22, -0.48, 0.78], dtype=float)
    light /= np.linalg.norm(light)
    shade = 0.30 + 0.70 * np.clip(normals @ light, 0.0, 1.0)
    cream = np.array([238, 230, 208])
    colors = np.clip(cream * shade[:, None], 0, 255).astype(np.uint8)

    all_x = v @ right
    all_y = v @ up
    min_x, max_x = float(all_x.min()), float(all_x.max())
    min_y, max_y = float(all_y.min()), float(all_y.max())
    span = max(max_x - min_x, max_y - min_y, 1e-6)
    pad = 18
    scale = min((width - 2 * pad) / (max_x - min_x), (height - 2 * pad) / (max_y - min_y))
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    order = np.argsort(centers @ view)
    for i in order:
        pts = []
        for p in tris[i]:
            sx = (float(p @ right) - cx) * scale + width / 2.0
            sy = height / 2.0 - (float(p @ up) - cy) * scale
            pts.append((sx, sy))
        draw.polygon(pts, fill=tuple(int(c) for c in colors[i]))
    return image, scale


def render_sheet(tri: trimesh.Trimesh, path: str) -> None:
    """Three orthographic views with overall millimetre dimensions."""
    from PIL import Image, ImageDraw, ImageFont

    size = tri.bounds[1] - tri.bounds[0]
    width_mm, depth_mm, height_mm = (float(size[0]), float(size[1]), float(size[2]))
    sheet = Image.new("RGB", (2200, 1280), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 28)
        font_s = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 22)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 40)
    except OSError:
        font = font_s = font_b = ImageFont.load_default()

    draw.text((48, 28), "奶蛙  ·  捧腹大笑", fill=(30, 30, 30), font=font_b)
    draw.text(
        (48, 84),
        "3D 打印模型    单位 mm    单件实心    底面已修平，可直接放在热床上",
        fill=(70, 70, 70),
        font=font,
    )

    panels = [
        ((80, 180, 700, 980), np.array([0.0, -1.0, 0.0]), np.array([0.0, 0.0, 1.0]), "正视图", f"宽 {width_mm:.1f}    高 {height_mm:.1f}"),
        ((760, 180, 1380, 980), np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]), "侧视图", f"深 {depth_mm:.1f}    高 {height_mm:.1f}"),
        ((1440, 180, 2060, 980), np.array([0.0, 0.0, 1.0]), np.array([0.0, -1.0, 0.0]), "俯视图", f"宽 {width_mm:.1f}    深 {depth_mm:.1f}"),
    ]
    for (x0, y0, x1, y1), view, up, title, dims in panels:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=16, outline=(210, 210, 210), width=2, fill=(250, 248, 244))
        view_img, _scale = _shade_view(tri, view, up, x1 - x0 - 24, y1 - y0 - 90)
        sheet.paste(view_img, (x0 + 12, y0 + 12))
        draw.text((x0 + 16, y1 - 68), title, fill=(20, 20, 20), font=font)
        draw.text((x0 + 16, y1 - 36), dims, fill=(80, 80, 80), font=font_s)

    draw.text(
        (48, 1040),
        f"外形尺寸   宽 {width_mm:.1f} mm   ×   深 {depth_mm:.1f} mm   ×   高 {height_mm:.1f} mm",
        fill=(20, 20, 20),
        font=font,
    )
    draw.text(
        (48, 1090),
        "建议   层高 0.20 mm    填充 10%–15%    嘴巴比下巴、手臂下沿如有悬空，用树状支撑",
        fill=(70, 70, 70),
        font=font_s,
    )
    draw.text(
        (48, 1132),
        "底座约 3 mm。手指和脚趾已加粗，避免细小结构在打印时断开。模型为单一封闭实体。",
        fill=(70, 70, 70),
        font=font_s,
    )
    sheet.save(path)


def main() -> None:
    out_dir = os.path.dirname(os.path.abspath(__file__))
    solid = build()
    tri = to_trimesh(solid)
    stl_path = os.path.join(out_dir, "milk_frog_laugh.stl")
    sheet_path = os.path.join(out_dir, "milk_frog_blueprint.png")
    tri.export(stl_path)
    render_sheet(tri, sheet_path)
    preview, _ = _shade_view(
        tri,
        np.array([0.58, -0.74, 0.32]),
        np.array([0.0, 0.0, 1.0]),
        1200,
        1200,
    )
    preview_path = os.path.join(out_dir, "milk_frog_preview.png")
    preview.save(preview_path)

    bb = tri.bounds
    size = bb[1] - bb[0]
    print(f"watertight={tri.is_watertight} winding={tri.is_winding_consistent}")
    print(f"components={len(tri.split(only_watertight=False))} euler={tri.euler_number}")
    print(f"volume_mm3={tri.volume:.1f} area_mm2={tri.area:.1f}")
    print(f"triangles={len(tri.faces)} vertices={len(tri.vertices)}")
    print(f"size_mm=({size[0]:.1f}, {size[1]:.1f}, {size[2]:.1f})  X Y Z")
    print(f"bounds_min={bb[0].round(2).tolist()}")
    print(f"bounds_max={bb[1].round(2).tolist()}")
    print(f"wrote {stl_path}")
    print(f"wrote {sheet_path}")
    print(f"wrote {preview_path}")


if __name__ == "__main__":
    main()
