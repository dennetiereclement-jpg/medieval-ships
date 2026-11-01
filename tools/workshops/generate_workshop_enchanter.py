#!/usr/bin/env python3
"""workshop_enchanter — Atelier de l'enchanteur / Enchanter's Workshop (reference: scratchpad/ref/workshop_enchanter_ref.png).

A wooden pavilion on a low plank platform: four thick posts (the front ones on stone bases, ivy climbing the left
one) carrying a purple canopy with gold-pointed valances, a hanging sign "Enchanteur" with a book icon between two
lanterns, purple banners with gold stars, a central enchanting altar (dark stone, cyan diamond corners, purple cloth
with gold points) with an open glowing book and purple sparks, bookshelves full of coloured books with candles,
a potion shelf, blue and purple crystal clusters, a writing desk with parchment, quill and ink, a golden arcane
circle on the back wall, iron-banded chests with piles of books, a barrel, and a purple rug with gold borders running
from the altar down the steps onto the ground.

Usage:  python3 tools/workshops/generate_workshop_enchanter.py      (WS_OUT=<file>: write only the model there)
Writes: blockbench/workshop_enchanter.bbmodel, the assets copy, textures/entity/workshops_b.png,
        textures/item/workshop_enchanter.png, workshops/workshop_enchanter.json.
Workshop-local coordinates: y up, +z = front (the player works from there), the anchor block at (0, 0, 0) under the
altar (the altar stands on the platform, the player climbs the step in front of it).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_b as wl  # noqa: E402

NAME = "workshop_enchanter"
UP, v3 = wl.UP, wl.v3
PX, PZF, PZB = 3.2, 1.05, -2.45      # post lines: x = +-PX, front z, back z
PLAT_Y = 0.5                          # platform top
PLAT = (-2.9, 2.9, -2.45, 1.3)        # x0, x1, z0, z1
STEP = (-1.35, 1.35, 1.3, 1.85, 0.25)  # x0, x1, z0, z1, top
EAVE_Y = 3.7                          # top of the eave beams
POST_TOP = 4.25
RIDGE_Y, RIDGE_Z, RIDGE_HALF = 4.8, -0.7, 2.0
EAVE = (-3.62, 3.62, -2.85, 1.45, 3.93)  # canopy lower edge: x0, x1, z0, z1, y
ALTAR = v3(0.0, PLAT_Y, -0.05)
WALL_Z = -2.42                        # front face of the back wall
BOOK_Y = PLAT_Y + 0.98


def structure(root, detail, rng):
    s = wl.Bone("structure", parent=root)
    # stone bases under the front posts (and a lower block in front of the left one), small feet under the back ones
    wl.stone_block(s, "base_l", (-3.78, 0, 0.45), (-2.7, 1.0, 1.62), course=0.5, relief=0.035, seed=1, region="stone_bricks", top="stone_slab")
    wl.stone_block(s, "base_l2", (-3.8, 0, 1.62), (-2.85, 0.55, 2.35), course=0.55, relief=0.03, seed=2, region="cobble")
    wl.stone_block(s, "base_r", (2.7, 0, 0.45), (3.72, 0.95, 1.62), course=0.475, relief=0.035, seed=3)
    for k, x in enumerate((-PX, PX)):
        wl.stone_block(s, "base_b_%d" % k, (x - 0.35, 0, PZB - 0.35), (x + 0.35, 0.6, PZB + 0.35), course=0.6, seed=4 + k, region="cobble")
    # the four posts with block capitals and finials above the canopy
    for k, (x, z) in enumerate(((-PX, PZF), (PX, PZF), (-PX, PZB), (PX, PZB))):
        y0 = 0.95 if z == PZF else 0.6
        wl.post(s, "post_%d" % k, (x, y0, z), (x, POST_TOP, z), d=0.42, region="wood")
        wl.add_cube(s, "post_base_%d" % k, (x, y0 + 0.08, z), wl.EYE, (0.52, 0.16, 0.52), {"all": "wood_dark", "+2": "end_grain"})
        wl.add_cube(s, "post_cap_%d" % k, (x, EAVE_Y - 0.55, z), wl.EYE, (0.54, 0.22, 0.54), {"all": "wood_dark", "+2": "end_grain"})
        wl.add_cube(s, "finial_%d" % k, (x, POST_TOP + 0.2, z), wl.EYE, (0.56, 0.4, 0.56), {"all": "wood", "+2": "end_grain"})
        wl.add_cube(s, "finial_top_%d" % k, (x, POST_TOP + 0.5, z), wl.EYE, (0.34, 0.2, 0.34), {"all": "wood_dark", "+2": "end_grain"})
        wl.add_cube(s, "finial_knob_%d" % k, (x, POST_TOP + 0.66, z), wl.EYE, (0.16, 0.14, 0.16), "gold")
    # eave beams round the top, knee braces
    th = 0.34
    for e, (a, b) in {"f": ((-PX - 0.4, PZF), (PX + 0.4, PZF)), "b": ((-PX - 0.4, PZB), (PX + 0.4, PZB))}.items():
        wl.beam(s, "eave_" + e, (a[0], EAVE_Y - th / 2, a[1]), (b[0], EAVE_Y - th / 2, b[1]), th,
                {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, width=0.3)
    for e, x in (("l", -PX), ("r", PX)):
        wl.beam(s, "eave_" + e, (x, EAVE_Y - th / 2 - 0.02, PZF + 0.4), (x, EAVE_Y - th / 2 - 0.02, PZB - 0.4), th * 0.95,
                {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, width=0.28)
    for k, (x, z) in enumerate(((-PX, PZF), (PX, PZF), (-PX, PZB), (PX, PZB))):
        sx = -1 if x > 0 else 1
        sz = -1 if z > 0 else 1
        wl.beam(s, "brace_x_%d" % k, (x + sx * 0.15, EAVE_Y - 1.05, z), (x + sx * 0.85, EAVE_Y - 0.3, z), 0.2, "wood", width=0.2, extend=0.06)
        wl.beam(s, "brace_z_%d" % k, (x, EAVE_Y - 1.05, z + sz * 0.15), (x, EAVE_Y - 0.3, z + sz * 0.85), 0.2, "wood", width=0.2, extend=0.06)
    # the ridge and its king posts, a centre finial over the front
    wl.beam(s, "ridge", (-RIDGE_HALF - 0.2, RIDGE_Y - 0.12, RIDGE_Z), (RIDGE_HALF + 0.2, RIDGE_Y - 0.12, RIDGE_Z), 0.18, "wood_dark", width=0.18)
    for k, x in enumerate((-RIDGE_HALF, RIDGE_HALF)):
        wl.beam(s, "king_%d" % k, (x, EAVE_Y, RIDGE_Z), (x, RIDGE_Y - 0.15, RIDGE_Z), 0.16, "wood_dark", width=0.16)
        wl.add_cube(s, "ridge_knob_%d" % k, (x * 1.12, RIDGE_Y + 0.12, RIDGE_Z), wl.EYE, (0.3, 0.3, 0.3), {"all": "wood", "+2": "end_grain"})
        wl.add_cube(s, "ridge_knob_top_%d" % k, (x * 1.12, RIDGE_Y + 0.33, RIDGE_Z), wl.EYE, (0.14, 0.14, 0.14), "gold")
    for k in (-1, 1):
        wl.beam(s, "tie_%d" % k, (k * RIDGE_HALF, EAVE_Y - 0.1, PZF), (k * RIDGE_HALF, EAVE_Y - 0.1, PZB), 0.16, "wood_dark", width=0.16)
        wl.collide((EAVE[0], EAVE_Y - 0.4, EAVE[2], EAVE[1], RIDGE_Y, EAVE[3]))


def canopy(root, detail, rng):
    c = wl.Bone("canopy", parent=root)
    x0, x1, z0, z1, y = EAVE
    r0, r1 = v3(-RIDGE_HALF, RIDGE_Y, RIDGE_Z), v3(RIDGE_HALF, RIDGE_Y, RIDGE_Z)
    fl, fr, bl, br = v3(x0, y, z1), v3(x1, y, z1), v3(x0, y, z0), v3(x1, y, z0)
    wl.tl.canvas_panel(c, "cloth_f", r0, r1, fl, fr, sag=0.24, nx=6, ny=3, region="cloth_purple", th=0.04, ripple=0.07)
    wl.tl.canvas_panel(c, "cloth_b", r1, r0, br, bl, sag=0.24, nx=6, ny=3, region="cloth_purple", th=0.04, ripple=0.07)
    wl.tl.canvas_panel(c, "cloth_l", r0 + v3(0.001, 0, 0), r0, bl, fl, sag=0.12, nx=3, ny=3, region="cloth_purple", th=0.04, ripple=0.07)
    wl.tl.canvas_panel(c, "cloth_r", r1, r1 + v3(0.001, 0, 0), fr, br, sag=0.12, nx=3, ny=3, region="cloth_purple", th=0.04, ripple=0.07)
    # valances with gold points along the four eaves, a little outside the cloth's edge
    edges = (("f", fl, fr, v3(0, 0, 1)), ("b", br, bl, v3(0, 0, -1)), ("l", bl, fl, v3(-1, 0, 0)), ("r", fr, br, v3(1, 0, 0)))
    for e, a, b, out in edges:
        L = float(abs((b - a)[0]) + abs((b - a)[2]))
        n = max(1, int(round(L / 3.0)))
        for k in range(n):
            s0, s1 = k / n, (k + 1) / n

            def P(s, t, s0=s0, s1=s1, a=a, b=b, out=out):
                g = s0 + (s1 - s0) * s                       # along the whole edge: the valance dips between the posts
                p = a + (b - a) * g
                return p + out * (0.06 + 0.04 * t) - UP * (0.06 + 0.62 * t) - UP * (0.22 * math.sin(math.pi * g))
            wl.loft(c, "valance_%s_%d" % (e, k), P, 6, 1, "valance", th=0.025)
    # the gold trim along the cloth's lower edge
    for e, a, b, out in edges:
        wl.beam(c, "trim_" + e, a + out * 0.05 - UP * 0.06, b + out * 0.05 - UP * 0.06, 0.06, "gold", width=0.05, extend=0.05)


def platform(root, detail, rng):
    p = wl.Bone("platform", parent=root)
    x0, x1, z0, z1 = PLAT
    wl.platform(p, "deck", x0, x1, z0, z1, PLAT_Y, th=0.1, plank_w=0.42, along="z", region="plank", solid=False, joists=False)
    # skirt boards round the platform, a sill under them
    wl.box(p, "skirt_f", (x0, 0.0, z1 - 0.06), (x1, PLAT_Y - 0.1, z1), {"all": "plank_dark"}, u_dir=wl.X)
    wl.box(p, "skirt_l", (x0, 0.0, z0), (x0 + 0.06, PLAT_Y - 0.1, z1), {"all": "plank_dark"}, u_dir=wl.Z)
    wl.box(p, "skirt_r", (x1 - 0.06, 0.0, z0), (x1, PLAT_Y - 0.1, z1), {"all": "plank_dark"}, u_dir=wl.Z)
    wl.box(p, "skirt_b", (x0, 0.0, z0), (x1, PLAT_Y - 0.1, z0 + 0.06), {"all": "plank_dark"}, u_dir=wl.X)
    wl.box(p, "sill_f", (x0 - 0.04, 0.0, z1 - 0.02), (x1 + 0.04, 0.1, z1 + 0.04), {"all": "wood_dark"})
    wl.collide((x0, 0.0, z0, x1, PLAT_Y, z1))
    # the step in front: a block of planks
    sx0, sx1, sz0, sz1, sy = STEP
    wl.box(p, "step", (sx0, 0.0, sz0), (sx1, sy, sz1), {"all": "plank", "+1": "end_grain", "-1": "end_grain"}, u_dir=wl.X)
    wl.collide((sx0, 0.0, sz0, sx1, sy, sz1))
    # the rug: on the platform under the altar, over the step's edges, down on the ground in front
    wl.rug(p, "rug_top", -1.25, 1.25, -1.05, z1 - 0.02, PLAT_Y)
    wl.plate(p, "rug_lip", (0, PLAT_Y - 0.12, z1 + 0.012), 2.5, 0.26, "rug", normal=(0, 0, 1), th=0.02, both=False, back="purple_paint")
    wl.rug(p, "rug_step", -1.2, 1.2, sz0, sz1 - 0.02, sy, sub=(0.0, 0.0, 1.0, 0.45))
    wl.plate(p, "rug_step_lip", (0, sy - 0.12, sz1 + 0.012), 2.4, 0.26, "rug", normal=(0, 0, 1), th=0.02, both=False, back="purple_paint")
    wl.rug(p, "rug_ground", -1.3, 1.3, sz1 + 0.03, 2.8, 0.0)


def altar(root, detail, rng):
    a = wl.Bone("altar", parent=root)
    c = ALTAR
    hw, d0, d1 = 0.75, -0.6, 0.55
    wl.box(a, "altar_plinth", (c[0] - hw - 0.08, c[1], c[2] + d0 - 0.08), (c[0] + hw + 0.08, c[1] + 0.12, c[2] + d1 + 0.08),
           {"all": "altar_stone"})
    wl.box(a, "altar_body", (c[0] - hw, c[1] + 0.12, c[2] + d0), (c[0] + hw, c[1] + 0.86, c[2] + d1), {"all": "altar_stone"})
    wl.box(a, "altar_top", (c[0] - hw - 0.08, c[1] + 0.86, c[2] + d0 - 0.08), (c[0] + hw + 0.08, c[1] + 0.96, c[2] + d1 + 0.08),
           {"all": "altar_stone"})
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        p = c + v3(sx * (hw + 0.02), 0.91, d1 + 0.02 if sz > 0 else d0 - 0.02)
        wl.add_cube(a, "glow_diamond_%d" % k, p, wl.EYE, (0.28, 0.28, 0.28), {"all": "diamond"}, stretch=True)
        wl.add_cube(a, "glow_diamond_low_%d" % k, c + v3(sx * (hw + 0.02), 0.08, d1 + 0.03 if sz > 0 else d0 - 0.03), wl.EYE,
                    (0.2, 0.16, 0.2), {"all": "diamond"}, stretch=True)
    wl.collide((c[0] - hw - 0.1, c[1], c[2] + d0 - 0.1, c[0] + hw + 0.1, c[1] + 0.98, c[2] + d1 + 0.1))
    # the purple cloth over the top, hanging with gold points at the front and both sides
    yt = c[1] + 0.96
    wl.box(a, "cloth_top", (c[0] - 0.6, yt, c[2] + d0 + 0.06), (c[0] + 0.6, yt + 0.02, c[2] + d1 + 0.09), {"all": "cloth_purple"})
    wl.plate(a, "cloth_front", (c[0], yt - 0.26, c[2] + d1 + 0.1), 1.2, 0.54, "altar_cloth", normal=(0, 0, 1), th=0.015)
    for s in (-1, 1):
        wl.plate(a, "cloth_side_%d" % s, (c[0] + s * (hw + 0.1), yt - 0.2, c[2] + (d0 + d1) / 2), 0.8, 0.42, "altar_cloth", normal=(s, 0, 0),
                 th=0.015)
    # the glowing open book on a small slanted rest, sparks floating over it
    tilt = 0.32
    wl.add_cube(a, "book_rest", c + v3(0, yt - c[1] + 0.02 + 0.3 * math.sin(tilt) / 2 + 0.03, 0), wl.gg.rx(tilt), (0.66, 0.08, 0.5),
                {"all": "wood_dark"})
    wl.add_cube(a, "book_rest_foot", c + v3(0, yt - c[1] + 0.06, -0.12), wl.EYE, (0.5, 0.08, 0.26), {"all": "wood_dark"})
    wl.open_book(a, "book", (c[0], yt + 0.06, c[2]), w=1.0, d=0.66, yaw=0.0, cover="book_purple", glow=True, tilt=tilt)
    for k in range(10):
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.05, 0.38)
        h = rng.uniform(0.25, 1.1)
        s = rng.uniform(0.035, 0.07)
        wl.add_cube(detail, "glow_spark_%d" % k, c + v3(math.cos(ang) * r, yt + 0.1 + h, math.sin(ang) * r * 0.7), wl.ry(ang),
                    (s, s * 1.6, s), {"all": "spark"}, stretch=True)
    # things left on the platform round the altar: books, a scroll, a potion, a small crystal
    wl.book_stack(detail, "floor_books", (-1.05, PLAT_Y, -0.75), 3, rng, w=0.38, d=0.3, th=0.09)
    wl.book_flat(detail, "floor_book_open", (-0.95, PLAT_Y, 1.0), 0.36, 0.06, 0.28, "red", yaw=0.5)
    wl.parchment(detail, "floor_scroll", (0.85, PLAT_Y + 0.025, -1.05), w=0.24, d=0.36, yaw=-0.7)
    wl.bottle(detail, "floor_potion", (-1.1, PLAT_Y, 0.35), "purple", r=0.08, h=0.18)
    wl.crystal_cluster(detail, "floor_crystal", (-1.15, PLAT_Y, -0.2), "blue", rng, n=4, h=0.3, w=0.08, spread=0.07)


def shelves(root, detail, rng):
    s = wl.Bone("shelves", parent=root)
    y0 = PLAT_Y
    # the back wall: dark purple-brown planks between the back posts, two framing posts and a rail
    n = 18
    W = 2 * PX - 0.3
    for k in range(n):
        x = -W / 2 + (k + 0.5) * W / n
        wl.add_cube(s, "wall_%d" % k, (x, (y0 + EAVE_Y - 0.3) / 2, WALL_Z - 0.05), wl.EYE, (W / n * 0.98, EAVE_Y - 0.3 - y0, 0.1),
                    {"all": "wood_purple", "+1": "end_grain", "-1": "end_grain"}, u_dir=UP)
    wl.collide((-PX, y0, WALL_Z - 0.1, PX, EAVE_Y - 0.3, WALL_Z))
    for k, x in enumerate((-1.55, 0.15, 1.55)):
        wl.add_cube(s, "wall_post_%d" % k, (x, (y0 + EAVE_Y - 0.3) / 2, WALL_Z + 0.06), wl.EYE, (0.22, EAVE_Y - 0.3 - y0, 0.14), "wood")
    wl.beam(s, "wall_rail", (-PX, 3.3, WALL_Z + 0.07), (PX, 3.3, WALL_Z + 0.07), 0.18, "wood", width=0.14)

    def case(name, x0, x1, zb, depth, levels, top, side="wood", back=True):
        """A bookcase from the platform: two sides, a top, shelves at the given heights."""
        for k, x in enumerate((x0, x1)):
            wl.add_cube(s, "%s_side_%d" % (name, k), (x, (y0 + top) / 2, zb + depth / 2), wl.EYE, (0.12, top - y0, depth),
                        {"all": side, "+2": "end_grain"}, u_dir=UP)
        wl.add_cube(s, name + "_top", ((x0 + x1) / 2, top + 0.04, zb + depth / 2), wl.EYE, (x1 - x0 + 0.22, 0.08, depth + 0.08),
                    {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"}, u_dir=wl.X)
        for k, y in enumerate(levels):
            wl.add_cube(s, "%s_board_%d" % (name, k), ((x0 + x1) / 2, y - 0.03, zb + depth / 2), wl.EYE, (x1 - x0, 0.06, depth),
                        {"all": "plank"}, u_dir=wl.X)
        if back:
            wl.add_cube(s, name + "_back", ((x0 + x1) / 2, (y0 + top) / 2, zb + 0.02), wl.EYE, (x1 - x0, top - y0, 0.04), "plank_dark", u_dir=UP)
        wl.collide((x0 - 0.06, y0, zb, x1 + 0.06, top + 0.08, zb + depth))

    # the left bookcase (forward, two rows of books, candles on top)
    lx0, lx1, lz = -2.78, -1.68, -1.45
    case("case_l", lx0, lx1, lz, 0.46, (y0 + 0.08, y0 + 0.82, y0 + 1.56), y0 + 2.3)
    for k, y in enumerate((y0 + 0.08, y0 + 0.82, y0 + 1.56)):
        wl.book_row(detail, "books_l_%d" % k, lx0 + 0.06, lx1 - 0.06, y, lz + 0.44, 0.36, rng, hmin=0.38, hmax=0.55, wmin=0.08, wmax=0.13)
    for k, (dx, h) in enumerate(((0.18, 0.42), (0.45, 0.3), (0.7, 0.36))):
        wl.candle(detail, "case_l_candle_%d" % k, (lx0 + dx, y0 + 2.34, lz + 0.25), h=h, r=0.07)
    wl.book_stack(detail, "case_l_top_books", (lx0 + 0.92, y0 + 2.34, lz + 0.22), 2, rng, w=0.3, d=0.26)
    # the potion shelf at the back left (three levels of bottles)
    px0, px1 = -1.45, -0.72
    case("case_p", px0, px1, WALL_Z, 0.4, (y0 + 1.0, y0 + 1.62, y0 + 2.24), y0 + 2.75)
    pots = (("blue", "round"), ("purple", "round"), ("yellow", "flask"), ("green", "tall"), ("blue", "round"), ("pink", "round"),
            ("teal", "flask"), ("purple", "tall"), ("red", "round"))
    for k, (col, shape) in enumerate(pots):
        lvl = k // 3
        x = px0 + 0.16 + 0.22 * (k % 3)
        wl.bottle(detail, "potion_%d" % k, (x, y0 + 1.0 + 0.62 * lvl, WALL_Z + 0.2), col, r=0.085, h=0.2, shape=shape, neck_h=0.08)
    wl.book_row(detail, "books_p", px0 + 0.06, px1 - 0.06, y0 + 0.3, WALL_Z + 0.38, 0.3, rng, hmin=0.4, hmax=0.5, wmin=0.08, wmax=0.12)
    wl.add_cube(s, "case_p_low", ((px0 + px1) / 2, y0 + 0.27, WALL_Z + 0.2), wl.EYE, (px1 - px0, 0.06, 0.4), "plank")
    wl.candle(detail, "case_p_candle_0", (px0 + 0.2, y0 + 2.79, WALL_Z + 0.2), h=0.3, r=0.06)
    wl.candle(detail, "case_p_candle_1", (px0 + 0.48, y0 + 2.79, WALL_Z + 0.22), h=0.2, r=0.055)
    # the back banner (compass star) right of the potion shelf, behind the altar's left
    wl.banner(s, "banner_back", (-0.35, 3.15, WALL_Z + 0.16), 0.84, 1.62, "banner_compass", normal=(0, 0, 1))
    # the right bookcase (three rows), blue crystals on top
    rx0, rx1 = 0.35, 1.38
    case("case_r", rx0, rx1, WALL_Z, 0.42, (y0 + 0.08, y0 + 0.76, y0 + 1.44), y0 + 2.12)
    for k, y in enumerate((y0 + 0.08, y0 + 0.76, y0 + 1.44)):
        wl.book_row(detail, "books_r_%d" % k, rx0 + 0.06, rx1 - 0.06, y, WALL_Z + 0.4, 0.34, rng, hmin=0.36, hmax=0.52, wmin=0.08, wmax=0.13)
    wl.crystal_cluster(s, "crystal_blue", ((rx0 + rx1) / 2 + 0.1, y0 + 2.2, WALL_Z + 0.22), "blue", rng, n=7, h=0.7, w=0.14, spread=0.17)
    wl.book_stack(detail, "case_r_top_books", (rx0 + 0.2, y0 + 2.2, WALL_Z + 0.22), 2, rng, w=0.3, d=0.24)
    # the narrow candle shelf at the right and the arcane circle above it
    wl.shelf(s, "candle_shelf", 1.62, 2.5, WALL_Z, y0 + 1.25, depth=0.36, brackets=2)
    wl.shelf(s, "candle_shelf_2", 1.62, 2.5, WALL_Z, y0 + 0.7, depth=0.36, brackets=2)
    wl.candle(s, "candle_r", (1.85, y0 + 1.25, WALL_Z + 0.2), h=0.36, r=0.08)
    wl.bottle(detail, "shelf_potion", (2.15, y0 + 1.25, WALL_Z + 0.2), "purple", r=0.08, h=0.2)
    wl.crystal_cluster(detail, "crystal_shelf", (2.35, y0 + 1.25, WALL_Z + 0.18), "purple", rng, n=4, h=0.3, w=0.08, spread=0.06)
    wl.book_row(detail, "books_cs", 1.66, 2.45, y0 + 0.7, WALL_Z + 0.34, 0.28, rng, hmin=0.3, hmax=0.42)
    ac = v3(2.1, 2.78, WALL_Z + 0.05)
    wl.plate(s, "arcane", ac + v3(0, 0, 0.03), 1.3, 1.3, "arcane", normal=(0, 0, 1), th=0.01, both=False)
    R = 0.62
    for k in range(16):
        a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        wl.beam(detail, "arcane_ring_%d" % k, ac + v3(math.cos(a0) * R, math.sin(a0) * R, 0.06), ac + v3(math.cos(a1) * R, math.sin(a1) * R, 0.06),
                0.06, "gold", width=0.05, up=wl.Z, extend=0.02)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        wl.add_cube(detail, "arcane_stud_%d" % k, ac + v3(math.cos(a) * R, math.sin(a) * R, 0.09), wl.ry(0) @ wl.gg.rz(math.pi / 4),
                    (0.11, 0.11, 0.06), "gold")
    wl.add_cube(detail, "arcane_core", ac + v3(0, 0, 0.08), wl.gg.rz(math.pi / 4), (0.14, 0.14, 0.05), "gold")


def desk(root, detail, rng):
    d = wl.Bone("desk", parent=root)
    y0 = PLAT_Y
    x0, x1, z0, z1 = 1.25, 2.7, -0.72, 0.1
    wl.table(d, "desk", x0, x1, z0, z1, y0 + 0.86, top_th=0.12, leg=0.16, top_region="plank", leg_region="wood")
    wl.COLLIDERS[-1] = (x0, y0, z0, x1, y0 + 0.86, z1)
    yt = y0 + 0.86
    wl.parchment(detail, "parchment", (2.1, yt, -0.28), w=0.42, d=0.52, yaw=-0.25)
    wl.quill_ink(detail, "quill", (2.45, yt, -0.5), yaw=0.6)
    wl.book_stack(d, "desk_books", (1.55, yt, -0.35), 3, rng, w=0.4, d=0.3, th=0.09, colors=("purple", "red", "purple", "blue"))
    wl.book(detail, "desk_book_up", (1.47, yt + 0.27, -0.42), 0.09, 0.32, 0.24, "teal", tilt=0.25)
    wl.candle(detail, "desk_candle", (2.55, yt, -0.05), h=0.22, r=0.055)
    # a small chest under the desk, a small side table behind with books
    wl.chest(d, "desk_chest", (1.8, y0, -0.25), w=0.62, h=0.45, d=0.45, yaw=0.0, solid=False)
    st = (0.95, -1.0)
    wl.table(d, "side_table", st[0] - 0.32, st[0] + 0.32, st[1] - 0.3, st[1] + 0.3, y0 + 0.72, top_th=0.08, leg=0.1, top_region="plank_dark",
             leg_region="wood_dark", apron=False)
    wl.COLLIDERS[-1] = (st[0] - 0.32, y0, st[1] - 0.3, st[0] + 0.32, y0 + 0.72, st[1] + 0.3)
    wl.book_stack(detail, "side_books", (st[0] - 0.05, y0 + 0.72, st[1]), 3, rng, w=0.36, d=0.26)
    wl.bottle(detail, "side_potion", (st[0] + 0.2, y0 + 0.72, st[1] + 0.12), "blue", r=0.07, h=0.16)
    # the purple crystal cluster on the platform right of the altar
    wl.crystal_cluster(d, "crystal_purple", (1.1, y0, 0.55), "purple", rng, n=7, h=0.62, w=0.14, spread=0.16)
    wl.collide((0.92, y0, 0.37, 1.28, y0 + 0.5, 0.73))


def left_side(root, detail, rng):
    l = wl.Bone("left", parent=root)
    y0 = PLAT_Y
    # the chest on the platform left of the altar with piles of books, the big chest on the ground at the front left
    wl.chest(l, "chest_p", (-1.85, y0, 0.55), w=0.95, h=0.66, d=0.62, yaw=0.08)
    h1 = wl.book_stack(detail, "chest_p_books", (-2.02, y0 + 0.66, 0.5), 4, rng, w=0.4, d=0.3, th=0.09)
    wl.book_stack(detail, "chest_p_books_b", (-1.62, y0 + 0.66, 0.62), 2, rng, w=0.36, d=0.28, th=0.09, yaw=0.3)
    wl.book(detail, "chest_p_open", (-1.67, y0 + 0.66 + 0.18, 0.62), 0.1, 0.3, 0.26, "green", tilt=-0.5)
    wl.chest(l, "chest_g", (-2.3, 0.0, 2.1), w=1.05, h=0.78, d=0.7, yaw=-0.06)
    wl.book_stack(detail, "chest_g_books", (-2.4, 0.78, 2.07), 3, rng, w=0.42, d=0.32, th=0.1, colors=("purple", "red", "yellow"))
    # a pile of books and a scroll on the left stone base
    wl.book_stack(detail, "base_books", (-3.3, 1.0, 1.3), 3, rng, w=0.4, d=0.3, th=0.09)
    wl.parchment(detail, "base_scroll", (-3.05, 1.0, 0.72), w=0.22, d=0.34, yaw=0.9)
    # ivy on the left post, the left stone bases and the chest
    for k, (p, L, w, n) in enumerate((
            ((-PX + 0.22, 3.4, PZF + 0.23), 2.4, 0.45, (0, 0, 1)),
            ((-PX - 0.22, 3.6, PZF), 2.6, 0.45, (-1, 0, 0)),
            ((-3.3, 1.0, 1.64), 0.95, 0.9, (0, 0, 1)),
            ((-3.8, 1.0, 1.05), 0.95, 1.0, (-1, 0, 0)),
            ((-3.82, 0.55, 1.95), 0.55, 0.7, (-1, 0, 0)),
            ((-2.95, 0.78, 2.47), 0.7, 0.35, (0, 0, 1)),
            ((PX + 0.22, 1.6, PZF + 0.1), 0.65, 0.3, (1, 0, 0)),
            ((-PX + 0.05, EAVE_Y - 0.2, PZF + 0.18), 1.3, 1.0, (0, 0, 1)))):
        wl.vine(detail, "ivy_%d" % k, p, L, w, normal=n, region="ivy")


def right_side(root, detail, rng):
    r = wl.Bone("right", parent=root)
    wl.barrel(r, "barrel", (3.3, 0.0, 2.15), r=0.46, h=1.08, staves=10)
    wl.crate(r, "crate", (3.3, 0.95, 1.05), s=0.5, yaw=0.2, solid=False)
    wl.collide((2.95, 0.95, 0.75, 3.65, 1.45, 1.35))
    wl.bottle(detail, "barrel_potion", (3.35, 1.08, 2.1), "green", r=0.08, h=0.18)


def lights(root, detail, rng):
    g = wl.Bone("lights", parent=root)
    # two lanterns hanging from the front beam, the sign between them on two chains
    yb = EAVE_Y - 0.34
    for k, x in enumerate((-2.35, 2.4)):
        top = v3(x, yb, PZF + 0.05)
        wl.add_cube(g, "lamp_hook_%d" % k, top - UP * 0.04, wl.EYE, (0.08, 0.08, 0.08), "iron_dark")
        wl.lantern(g, "lamp_%d" % k, top - UP * 0.68, size=0.5, chain_to=top)
        wl.add_cube(g, "lamp_cap_%d" % k, top - UP * 0.3, wl.EYE, (0.3, 0.06, 0.3), "iron_dark")
    sc = v3(0.1, 3.42, EAVE[3] + 0.18)
    sw, sh = 3.3, 0.76
    wl.plate(g, "sign", sc, sw, sh, "sign", normal=(0, 0, 1), th=0.06, both=False, back="wood_purple")
    for k, (a, b) in enumerate((((-sw / 2 - 0.06, sh / 2 + 0.06), (sw / 2 + 0.06, sh / 2 + 0.06)),
                                ((-sw / 2 - 0.06, -sh / 2 - 0.06), (sw / 2 + 0.06, -sh / 2 - 0.06)),
                                ((-sw / 2 - 0.06, -sh / 2 - 0.06), (-sw / 2 - 0.06, sh / 2 + 0.06)),
                                ((sw / 2 + 0.06, -sh / 2 - 0.06), (sw / 2 + 0.06, sh / 2 + 0.06)))):
        wl.beam(g, "sign_frame_%d" % k, sc + v3(a[0], a[1], 0), sc + v3(b[0], b[1], 0), 0.12, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"},
                width=0.12, up=wl.Z if k < 2 else wl.X, extend=0.06)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        wl.add_cube(g, "sign_stud_%d" % k, sc + v3(sx * (sw / 2 + 0.06), sy * (sh / 2 + 0.06), 0.06), wl.EYE, (0.16, 0.16, 0.06), "gold")
    for k, x in enumerate((-1.15, 1.35)):
        wl.chain(detail, "sign_chain_%d" % k, (x, 4.2, sc[2] - 0.05), (x, sc[1] + sh / 2 + 0.1, sc[2]), link=0.08)
        wl.add_cube(g, "sign_ring_%d" % k, (x, sc[1] + sh / 2 + 0.1, sc[2]), wl.EYE, (0.1, 0.06, 0.06), "iron_dark")
    # banners with gold stars: inside the left front post, outside the right one
    for k, (x, rod) in enumerate(((-PX + 0.68, (-PX + 0.21, -PX + 1.16)), (PX + 0.56, (PX + 0.21, PX + 1.05)))):
        wl.banner(g, "banner_%d" % k, (x, 2.92, PZF + 0.1), 0.82, 1.5, "banner_star", normal=(0, 0, 1), rod=False)
        wl.beam(g, "banner_rod_%d" % k, (rod[0], 2.96, PZF + 0.12), (rod[1], 2.96, PZF + 0.12), 0.06, "wood_dark", width=0.06)
        wl.add_cube(g, "banner_knob_%d" % k, (rod[1], 2.96, PZF + 0.12), wl.EYE, (0.1, 0.1, 0.1), "gold")


def build():
    rng = random.Random(41)
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    structure(root, detail, rng)
    canopy(root, detail, rng)
    platform(root, detail, rng)
    altar(root, detail, rng)
    shelves(root, detail, rng)
    desk(root, detail, rng)
    left_side(root, detail, rng)
    right_side(root, detail, rng)
    lights(root, detail, rng)
    return root


def icon(path):
    """32x32: an open purple book glowing on a dark altar, purple sparks."""
    im, d = wl.new_icon(32)
    d.rectangle([6, 22, 25, 30], fill=(52, 38, 66, 255), outline=(110, 80, 140, 255))
    d.rectangle([4, 20, 27, 22], fill=(60, 44, 74, 255))
    for x in (4, 25):
        d.rectangle([x, 20, x + 2, 22], fill=(90, 230, 230, 255))
    d.polygon([(3, 18), (15, 14), (16, 19), (5, 21)], fill=(90, 40, 130, 255))
    d.polygon([(28, 18), (16, 14), (16, 19), (26, 21)], fill=(90, 40, 130, 255))
    d.polygon([(4, 16), (15, 12), (15, 18), (5, 19)], fill=(255, 244, 210, 255))
    d.polygon([(27, 16), (16, 12), (16, 18), (26, 19)], fill=(255, 244, 210, 255))
    for k in range(3):
        d.line([(7, 15 + k * 1), (13, 13 + k * 1)], fill=(120, 80, 170, 255))
        d.line([(18, 13 + k * 1), (24, 15 + k * 1)], fill=(120, 80, 170, 255))
    for x, y in ((9, 7), (15, 4), (21, 8), (12, 10), (19, 2), (24, 5)):
        d.rectangle([x, y, x + 1, y + 1], fill=(200, 120, 255, 255))
    d.point((15, 8), fill=(240, 200, 255, 255))
    wl.save_icon(im, path)


def main():
    wl.setup(NAME)
    root = build()
    b = ALTAR + v3(0, 1.0 + 0.25, 0)
    particles = [
        {"type": "enchant", "pos": (b[0], b[1] + 0.4, b[2]), "chance": 0.7, "count": 2},
        {"type": "portal", "pos": (b[0], b[1] + 0.2, b[2]), "chance": 0.25, "count": 1},
        {"type": "end_rod", "pos": (0.98, PLAT_Y + 0.7, 0.55), "chance": 0.04, "count": 1},
    ]
    wl.export(root, NAME, particles=particles, icon=icon, visible_box=(10, 6, 0))


if __name__ == "__main__":
    main()
