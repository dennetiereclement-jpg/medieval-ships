#!/usr/bin/env python3
"""tent_command — the big command tent (reference: scratchpad/ref/tent1_command_ref.png).

A raised plank platform ringed by rustic railings, four heavy corner posts leaning outwards and poking through the
corners of a big hip roof of worn beige canvas: the canvas sags between the hip rafters, its eaves droop between
the corners and a long torn fringe hangs all round; a king post rises through the roof to a finial, tie beams with
knee braces join the posts, sagging eave beams follow the cloth, lantern booms stick out of the front posts with
guy ropes to pegs, a big ship's wheel stands at the centre on its pedestal. Furniture: the decoration mods' desk
(strategy table) with maps, a book pile and a lamp on it, a chair, stools, a bench, a war chest, a crate and a
barrel, a chained lantern hanging from the king post, a pinned map board hung behind the desk.

Usage:  python3 tools/tents/generate_tent_command.py      (TENT_OUT=<file>: write only the model there, for previews)
Writes: blockbench/tent_command.bbmodel, the assets copy, textures/entity/tents.png, textures/item/tent_command.png,
        interiors/tent_command_decor.json, tents/tent_command.json (extent + collision boxes for TentType).
Tent-local coordinates: y up, +z = front (entrance), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tentlib as tl  # noqa: E402

NAME = "tent_command"
FLOOR_Y = 0.55         # top of the platform (a raised deck on heavy beams)
HALF_X, HALF_Z = 4.2, 3.5   # platform half sizes
POST_FOOT = (3.45, 2.85)    # |x|, |z| of the corner posts at the ground
POST_TOP = (4.3, 5.5, 3.55)   # |x|, y, |z| of the corner post tops (leaning outwards)
EAVE = (4.6, 5.2, 3.8)        # |x|, y, |z| of the roof corners
APEX = (0.0, 7.25, -0.4)
DESK_Z = -2.0
WHEEL = (0.0, 2.2, 1.65)
v3, UP, EYE = tl.v3, tl.UP, tl.EYE


def post_at(sx, sz, y):
    """Point on the leaning corner post (sx, sz = +-1) at height y."""
    foot = v3(sx * POST_FOOT[0], 0.0, sz * POST_FOOT[1])
    top = v3(sx * POST_TOP[0], POST_TOP[1], sz * POST_TOP[2])
    return foot + (top - foot) * (y / POST_TOP[1])


def hip_roof(bone, apex, corners, dip=0.9, sag=0.3, nx=7, ny=5, fringe=0.55, half_top=0.15):
    """Hip roof over the four `corners` (fl, fr, br, bl): one lofted panel per side from a short edge at the apex to
    the side's eave; the cloth sags between the hip rafters and the eave droops by `dip` in the middle of the side;
    a torn fringe hangs on below the eave."""
    apex = v3(*apex)
    n = len(corners)
    for k in range(n):
        c0, c1 = v3(*corners[k]), v3(*corners[(k + 1) % n])
        along = tl.norm(c1 - c0)
        t0, t1 = apex - along * half_top, apex + along * half_top
        reg = "canvas" if k % 2 == 0 else "canvas_b"

        def P(s, t, c0=c0, c1=c1, t0=t0, t1=t1):
            top = t0 + (t1 - t0) * s
            edge = c0 + (c1 - c0) * s
            p = top * (1 - t) + edge * t
            w = math.sin(math.pi * s)
            p = p - UP * (dip * w * t * t + sag * w * math.sin(math.pi * t))
            p = p - UP * (0.05 * t * t * math.sin(s * math.pi * 5.0 + 0.3 * k))
            return p

        tl.loft(bone, "roof_%d" % k, P, nx, ny, reg, th=0.035)

        # the fringe hangs nearly straight down (gravity), a plain band of cloth then the torn strips, uneven lengths
        def F(s, t, P=P):
            d = tl.norm(tl.norm(P(s, 1.0) - P(s, 0.9)) * 0.3 - UP)
            return P(s, 1.0) + d * (fringe * t) + UP * (0.03 * math.sin(s * 13.0))

        tl.loft(bone, "roof_%d_hem" % k, F, nx, 1, reg, th=0.03)

        def G(s, t, F=F):
            length = fringe * (0.85 + 0.35 * math.sin(s * 9.0 + k))
            return F(s, 1.0) + (F(s, 1.0) - F(s, 0.0)) / fringe * (length * t)

        tl.loft(bone, "roof_%d_fringe" % k, G, nx + 2, 1, "fringe", th=0.026)


def ship_wheel(bone, center, radius=0.85, n_rim=16, n_spokes=8):
    """A big wooden ship's wheel standing in the x-y plane (facing the front)."""
    c = v3(*center)
    pts = [c + v3(math.cos(2 * math.pi * k / n_rim) * radius, math.sin(2 * math.pi * k / n_rim) * radius, 0) for k in range(n_rim + 1)]
    for k in range(n_rim):
        tl.beam(bone, "wheel_rim_%d" % k, pts[k], pts[k + 1], 0.11, "wood_dark", extend=0.025)
    for k in range(n_spokes):
        a = 2 * math.pi * k / n_spokes + math.pi / n_spokes
        d = v3(math.cos(a), math.sin(a), 0)
        tl.beam(bone, "wheel_spoke_%d" % k, c + d * 0.12, c + d * (radius + 0.3), 0.075, "wood")
        tl.add_cube(bone, "wheel_handle_%d" % k, c + d * (radius + 0.22), EYE, (0.11, 0.11, 0.11), "wood_dark")
    tl.add_cube(bone, "wheel_hub", c, EYE, (0.32, 0.32, 0.28), {"all": "wood_dark", "+3": "iron", "-3": "iron"})
    tl.add_cube(bone, "wheel_boss", c, EYE, (0.14, 0.14, 0.36), "iron")


def icon_command(path):
    """16x16 icon: a wide hip roof with a torn edge on four posts over a plank platform."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    cloth, dark, wood, plank = (201, 180, 138, 255), (141, 122, 86, 255), (110, 76, 40, 255), (128, 92, 52, 255)
    for y in range(2, 8):
        half = 1.5 + (y - 2) * 1.3
        for x in range(16):
            d = abs(x - 7.5)
            if d <= half:
                p[x, y] = dark if abs(d - half) < 0.7 or y == 7 else cloth
    for x in range(1, 15):   # torn fringe
        if (x * 7) % 3 != 0:
            p[x, 8] = dark
    p[7, 1] = wood
    p[8, 1] = wood
    for y in range(8, 14):   # four posts
        for x in (1, 14):
            p[x, y] = wood
        for x in (5, 10):
            p[x, y] = (90, 62, 32, 255)
    for x in range(0, 16):   # platform and railing
        p[x, 14] = plank
        p[x, 15] = (80, 58, 34, 255)
        if x % 2 == 0:
            p[x, 12] = plank
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def build():
    root = tl.Bone(NAME)
    frame = tl.Bone("frame", parent=root)
    cloth = tl.Bone("canvas", parent=root)
    detail = tl.Bone("detail", parent=root)
    furn = tl.Bone("furniture", parent=root)

    # ---- platform: planks on joists, a beam skirt, a step at the entrance
    tl.platform(root, "floor", -HALF_X, HALF_X, -HALF_Z, HALF_Z, FLOOR_Y, th=0.12, plank_w=0.52, along="z")
    for k, xx in enumerate((-HALF_X + 0.15, HALF_X - 0.15)):
        tl.add_cube(frame, "skirt_%d" % k, (xx, 0.2, 0), EYE, (0.3, 0.4, HALF_Z * 2), "wood_dark")
        tl.add_cube(frame, "sill_%d" % k, (xx * 0.6, 0.11, 0), EYE, (0.26, 0.22, HALF_Z * 2 - 0.4), "wood_dark")
    for k, zz in enumerate((-HALF_Z + 0.15, HALF_Z - 0.15)):
        tl.add_cube(frame, "skirt_z_%d" % k, (0, 0.2, zz), EYE, (HALF_X * 2 - 0.1, 0.4, 0.3), "wood_dark")
    for k, (xx, zz) in enumerate(((-2.1, -1.2), (2.1, -1.2), (-2.1, 1.2), (2.1, 1.2), (0, 0))):
        tl.add_cube(frame, "pier_%d" % k, (xx, 0.18, zz), EYE, (0.3, 0.36, 0.3), "wood_dark")
    tl.add_cube(detail, "step", (2.0, 0.14, HALF_Z + 0.4), EYE, (1.8, 0.28, 0.8), "plank", u_dir=v3(1, 0, 0))
    tl.collide((1.1, 0.0, HALF_Z, 2.9, 0.28, HALF_Z + 0.8))

    # ---- four heavy corner posts leaning outwards, caps above the roof
    corners = ((-1, 1), (1, 1), (1, -1), (-1, -1))   # fl, fr, br, bl
    for sx, sz in corners:
        nm = "%s%s" % ("r" if sx > 0 else "l", "f" if sz > 0 else "b")
        foot, top = post_at(sx, sz, 0.0) - UP * 0.1, post_at(sx, sz, POST_TOP[1])
        tl.post(frame, "post_" + nm, foot, top, d=0.5)
        tl.add_cube(frame, "cap_" + nm, top + UP * 0.16, EYE, (0.64, 0.22, 0.64), {"all": "wood_dark", "+2": "end_grain"})
        tl.add_cube(frame, "cap2_" + nm, top + UP * 0.36, EYE, (0.42, 0.24, 0.42), {"all": "wood_dark", "+2": "end_grain"})
        # iron band and rope lashing near the eave
        tl.add_cube(detail, "band_" + nm, post_at(sx, sz, 4.7), EYE, (0.56, 0.14, 0.56), "iron")
        tl.rope(detail, "lash_" + nm, post_at(sx, sz, 4.95) + v3(-sx * 0.3, 0, sz * 0.3),
                post_at(sx, sz, 5.1) + v3(sx * 0.3, 0, -sz * 0.3), d=0.07)

    # ---- tie beams and knee braces between the posts (sides and back), a higher lintel at the front
    TIE_Y = 3.45
    for (a, b), nm in (((( -1, 1), (-1, -1)), "l"), (((1, 1), (1, -1)), "r"), (((1, -1), (-1, -1)), "b")):
        pa, pb = post_at(a[0], a[1], TIE_Y), post_at(b[0], b[1], TIE_Y)
        tl.pole(frame, "tie_" + nm, pa, pb, d=0.2, extend=0.1)
        for k, (p, q) in enumerate(((pa, pb), (pb, pa))):
            lo = post_at(*(a if k == 0 else b), 2.55)
            tl.pole(frame, "brace_%s_%d" % (nm, k), lo, p + tl.norm(q - p) * 1.0 - UP * 0.05, d=0.13, region="wood_dark")
    pa, pb = post_at(-1, 1, 4.45), post_at(1, 1, 4.45)
    tl.pole(frame, "lintel_f", pa, pb, d=0.18, extend=0.1)
    for k, (p, q, s) in enumerate(((pa, pb, -1), (pb, pa, 1))):
        tl.pole(frame, "brace_f_%d" % k, post_at(s, 1, 3.6), p + tl.norm(q - p) * 0.95 - UP * 0.05, d=0.13, region="wood_dark")

    # ---- king post through the roof to a finial, bracket for the hanging lantern
    tl.post(frame, "king_post", (APEX[0], FLOOR_Y - 0.2, APEX[2]), (APEX[0], APEX[1] + 0.45, APEX[2]), d=0.26)
    tl.add_cube(frame, "finial", (APEX[0], APEX[1] + 0.62, APEX[2]), EYE, (0.36, 0.16, 0.36), {"all": "wood_dark", "+2": "end_grain"})
    tl.add_cube(frame, "finial_2", (APEX[0], APEX[1] + 0.82, APEX[2]), EYE, (0.18, 0.26, 0.18), "gold")
    tl.pole(frame, "bracket", (APEX[0] + 0.1, 3.95, APEX[2]), (APEX[0] + 0.85, 3.95, APEX[2]), d=0.1, region="wood_dark")
    tl.pole(frame, "bracket_brace", (APEX[0] + 0.12, 3.45, APEX[2]), (APEX[0] + 0.7, 3.9, APEX[2]), d=0.08, region="wood_dark")

    # ---- roof: hip rafters, sagging eave beams under the cloth edge, the canvas and its fringe
    eave_corners = [(sx * EAVE[0], EAVE[1], sz * EAVE[2]) for sx, sz in corners]
    for k, c in enumerate(eave_corners):
        tl.pole(frame, "rafter_%d" % k, v3(*APEX) - UP * 0.1, v3(*c) - UP * 0.06, d=0.14)
    for k in range(4):
        c0, c1 = v3(*eave_corners[k]), v3(*eave_corners[(k + 1) % 4])
        tl.rope(frame, "eave_%d" % k, c0 - UP * 0.15, c1 - UP * 0.15, d=0.14, sag=0.75, segs=4, region="wood")
    hip_roof(cloth, APEX, eave_corners)
    # a few short ropes tying the cloth to the eave beams
    for k in range(4):
        c0, c1 = v3(*eave_corners[k]), v3(*eave_corners[(k + 1) % 4])
        for s in (0.25, 0.75):
            p = c0 + (c1 - c0) * s - UP * (0.75 * 4 * s * (1 - s) + 0.15)
            tl.rope(detail, "tie_rope_%d_%d" % (k, int(s * 4)), p + UP * 0.25, p - UP * 0.12, d=0.05)

    # ---- railings round the platform, the entrance gap at the front right (x 1.0..3.0)
    rx, rz = HALF_X - 0.22, HALF_Z - 0.22
    tl.railing(root, "rail_l", (-rx, FLOOR_Y, -rz), (-rx, FLOOR_Y, rz), h=1.1, post_every=1.35, d=0.14)
    tl.railing(root, "rail_r", (rx, FLOOR_Y, -rz), (rx, FLOOR_Y, rz), h=1.1, post_every=1.35, d=0.14)
    tl.railing(root, "rail_b", (-rx + 0.3, FLOOR_Y, -rz), (rx - 0.3, FLOOR_Y, -rz), h=1.1, post_every=1.35, d=0.14)
    tl.railing(root, "rail_f1", (-rx + 0.3, FLOOR_Y, rz), (1.0, FLOOR_Y, rz), h=1.1, post_every=1.35, d=0.14)
    tl.railing(root, "rail_f2", (3.0, FLOOR_Y, rz), (rx - 0.3, FLOOR_Y, rz), h=1.1, post_every=1.35, d=0.14)

    # ---- lantern booms on the front posts, guy ropes to pegs
    for sx, nm in ((1, "r"), (-1, "l")):
        base = post_at(sx, 1, 3.7)
        end = base + v3(sx * 1.0, 0.12, 0.25)
        tl.pole(frame, "boom_" + nm, base - v3(sx * 0.1, 0, 0), end, d=0.12, region="wood_dark")
        tl.pole(frame, "boom_brace_" + nm, post_at(sx, 1, 3.05), end - v3(sx * 0.25, 0.08, 0.06), d=0.08, region="wood_dark")
        tl.lantern(detail, "lantern_" + nm, end - UP * 0.75, size=0.32, chain_to=end - UP * 0.04)
        tl.guy(detail, "guy_" + nm, end + v3(sx * 0.02, -0.05, 0.02), (sx * 4.95, 0.0, 3.6), sag=0.03)

    # ---- the ship's wheel on its pedestal (the model's own furniture)
    tl.post(furn, "pedestal", (WHEEL[0], FLOOR_Y - 0.1, WHEEL[2] - 0.3), (WHEEL[0], WHEEL[1] - 0.1, WHEEL[2] - 0.3), d=0.24, solid=False)
    tl.pole(furn, "pedestal_brace", (WHEEL[0], FLOOR_Y, WHEEL[2] - 1.0), (WHEEL[0], WHEEL[1] - 0.55, WHEEL[2] - 0.35), d=0.12, region="wood_dark")
    tl.pole(furn, "pedestal_foot", (WHEEL[0], FLOOR_Y + 0.06, WHEEL[2] - 1.1), (WHEEL[0], FLOOR_Y + 0.06, WHEEL[2] + 0.2), d=0.14, region="wood_dark")
    tl.pole(furn, "axle", (WHEEL[0], WHEEL[1], WHEEL[2] - 0.45), (WHEEL[0], WHEEL[1], WHEEL[2] + 0.1), d=0.12, region="iron")
    ship_wheel(furn, WHEEL, radius=0.85)
    tl.collide((WHEEL[0] - 1.0, FLOOR_Y, WHEEL[2] - 0.55, WHEEL[0] + 1.0, WHEEL[1] + 1.15, WHEEL[2] + 0.25))

    # ---- maps on the desk (desk top at FLOOR_Y + 1.016), a pinned map board hung behind the desk
    top = FLOOR_Y + 1.02
    tl.add_cube(furn, "map_a", (-0.15, top + 0.012, DESK_Z + 0.05), tl.gg.ry(0.18), (1.0, 0.022, 0.72), {"all": "linen", "+2": "map", "-2": "map"})
    tl.add_cube(furn, "map_b", (0.45, top + 0.03, DESK_Z + 0.1), tl.gg.ry(-0.35), (0.75, 0.02, 0.56), {"all": "linen", "+2": "map", "-2": "map"})
    tl.beam(furn, "map_roll", (-1.25, top + 0.06, DESK_Z - 0.3), (-0.55, top + 0.06, DESK_Z - 0.1), 0.11, {"all": "map", "+1": "linen", "-1": "linen"})
    for k, (x, z, reg) in enumerate(((-0.35, DESK_Z - 0.1, "red_paint"), (0.05, DESK_Z + 0.2, "iron"), (0.3, DESK_Z - 0.15, "gold"), (-0.1, DESK_Z + 0.25, "red_paint"))):
        tl.add_cube(furn, "marker_%d" % k, (x, top + 0.07, z), EYE, (0.08, 0.1, 0.08), reg)
    bz = -HALF_Z + 0.08
    tl.add_cube(furn, "board", (0.9, 2.25, bz), EYE, (1.5, 1.1, 0.05), {"all": "linen", "+3": "map", "-3": "map"})
    for k, (dx, dy, sz) in enumerate(((0, 0.58, (1.6, 0.07, 0.08)), (0, -0.58, (1.6, 0.07, 0.08)), (-0.78, 0, (0.07, 1.2, 0.08)), (0.78, 0, (0.07, 1.2, 0.08)))):
        tl.add_cube(furn, "board_frame_%d" % k, (0.9 + dx, 2.25 + dy, bz), EYE, sz, "wood_dark")
    for k, x in enumerate((0.25, 1.55)):
        s = (x + EAVE[0]) / (2 * EAVE[0])
        y_eave = EAVE[1] - 0.15 - 0.75 * 4 * s * (1 - s)
        tl.rope(detail, "board_rope_%d" % k, (x, 2.8, bz), (x, y_eave - 0.05, -EAVE[2] + 0.2), d=0.05)

    # ---- furniture of the decoration mods (stand-ins when a mod is missing)
    decor = tl.Decor()
    decor.block("farmhouse_decorations:desk", 0.0, FLOOR_Y, DESK_Z, facing="front", fallback="crate")
    decor.block("farmhouse_decorations:pile_of_books", 1.05, top, DESK_Z + 0.05, facing="neg_x", scale=1.0, fallback="books", solid=False)
    decor.block("furnish:book_pile", -0.95, top, DESK_Z + 0.2, facing="pos_x", scale=0.9, fallback="books", solid=False)
    decor.block("farmhouse_decorations:kerosene_lantern", 1.25, top, DESK_Z - 0.3, facing="front", glow=True,
                alt="minecraft:lantern", fallback="lantern", solid=False)
    decor.block("furnish:spruce_chair", 0.0, FLOOR_Y, DESK_Z - 0.95, facing="front", fallback="crate")
    decor.block("furnish:spruce_stool", -0.9, FLOOR_Y, DESK_Z + 1.05, facing="back", fallback="crate")
    decor.block("furnish:spruce_stool", 1.0, FLOOR_Y, DESK_Z + 1.1, facing="back", scale=0.95, fallback="crate")
    decor.block("furnish:spruce_bench", -3.45, FLOOR_Y, 0.4, facing="neg_x", fallback="crate")
    decor.block("mebahelcreaturesdwarven:dwemer_chest", -3.35, FLOOR_Y, -2.85, facing="pos_x", alt="minecraft:chest", fallback="crate")
    decor.block("furnish:spruce_crate", 3.4, FLOOR_Y, -2.85, facing="front", scale=0.9, fallback="crate")
    decor.block("landsoficaria:cypress_barrel", 3.4, FLOOR_Y, -1.85, facing="neg_x", scale=0.9, alt="minecraft:barrel", fallback="barrel")
    decor.block("farmhouse_decorations:chained_kerosene_lantern", APEX[0] + 0.72, 2.95, APEX[2], facing="front", glow=True,
                fallback="lantern", solid=False)
    decor.fallbacks(root)
    return root, decor


def main():
    tl.setup(NAME)
    root, decor = build()
    tl.export(root, NAME, decor, icon=icon_command, visible_box=(10, 8, 0))


if __name__ == "__main__":
    main()
