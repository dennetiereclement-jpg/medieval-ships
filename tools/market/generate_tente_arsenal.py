#!/usr/bin/env python3
"""tente_arsenal — Tente marchande de l'arsenal / Arsenal Merchant Tent (1.26.0, market group F; reference:
scratchpad/ref2/tente_arsenal_ref.png, the bottom-right tent of the board tentes_065_planche.png).

A steampunk workshop marquee, one block (TentType group "tents", the integrator's list MARKET_TENTS):

  - a pointed, sweeping marquee roof of rust-orange and cream stripes (twelve stripes radiating from the peak),
    stained, a crenellated valance of orange and cream tabs, some painted with little gears;
  - an iron-clad frame: four heavy posts of orange wood sheathed in riveted steel plates and brackets, iron caps and
    brass finials (the back-left one taller, carrying the banner arm), riveted steel girders for eave beams, a big
    BRASS GEAR (and a smaller one) bolted on the front girder;
  - on top: an iron-and-brass crown on the peak, COPPER PIPES with brass flanges and elbows running from the crown
    (one rising and bending into it on the left, one stepping down the right slope) to a riveted iron BOILER with a
    domed top, brass bands and a little CHIMNEY whose brass cap lets out a rare puff of smoke;
  - a brown BANNER with the golden GEAR emblem and a gold fringe on a brass pipe arm of the back-left post, a lit
    lantern hanging from an iron bracket by the front-left post, braided ropes to pegs on both sides;
  - rust canvas walls at the back and the back half of the sides;
  - inside: back shelves with glowing lamps, brass gadgets, cogs and bottles; the central workbench counter with a
    vice, a little brass machine, gears and a lamp; a workbench and a tool board along the left wall; the
    orange-brown rug with a gear;
  - outside: a riveted iron pressure TANK with a dome and a valve and a barrel at the back left, big crates with
    gold gear emblems along the left side, crates and a golden-bronze chest at the front right.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the central counter (NPC_SPOT), reached on foot round
either end of the counter. No trade system; the boiler's rare smoke puff is a client-side random display particle
(nothing ticks).

Usage:  python3 tools/market/generate_tente_arsenal.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_arsenal.json, models/entity + blockbench/tente_arsenal.bbmodel,
textures/entity/tente_arsenal.png, textures/item/tente_arsenal.png, interiors/tente_arsenal_decor.json.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_f as pf  # noqa: E402

ml = pf.ml
NAME = "tente_arsenal"
v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _scale = ml._rgb, ml._scale

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 3.6, 3.4            # posts at x = +-HW, z = +-HD
EAVE = 3.4                   # top of the steel girders
EY = 3.65                    # the roof's eave line
W, D = HW + 0.35, HD + 0.35  # the roof's eave half length / half depth
APEX = 6.4                   # the peak (under the crown)
COUNTER = (-1.45, 1.75, -1.66, -1.08)   # x0, x1, z0, z1
COUNTER_H = 1.0
SHELF_Z = (-3.18, -2.78)
NPC_SPOT = (-0.35, -2.74)    # (x0, z0) of the free 1 x 1 x 2.2 place behind the counter
BOILER = (2.5, 1.35)         # (x, z) of the boiler on the right slope
CHIMNEY_TOP = None           # set by build (the smoke puff)

ORANGE, ORANGE_DARK = _rgb("c2602c"), _rgb("7a3416")
CREAM = _rgb("eadcc0")
RUST = _rgb("8a4622")
GOLDF = _rgb("dca23a")
BRASS = [(0, (110, 70, 20)), (0.45, (190, 140, 50)), (0.8, (236, 196, 100)), (1, (255, 236, 170))]
COPPER = [(0, (90, 40, 20)), (0.45, (170, 92, 50)), (0.8, (214, 140, 90)), (1, (246, 200, 160))]


def add_regions(atlas):
    """This tent's regions, packed in the free band of the 512 px atlas."""
    atlas.add("ar_roof", 192, 128, pf.stripes([ORANGE, CREAM], 3301, n=4, shade=(0.84, 1.04), fold=0.2))
    atlas.add("ar_rug", 128, 96, pf.rug(_rgb("8e4a24"), _rgb("4a240e"), _rgb("d8a040"), 3302,
                                        motif=lambda d, x0, y0, x1, y1, S: pf.gear_emblem(d, x0 + (x1 - x0) * 0.2, y0, x1 - (x1 - x0) * 0.2, y1, S,
                                                                                          colour=(222, 164, 64), dark=(120, 70, 20))))
    atlas.add("ar_banner", 48, 96, pf.banner(_rgb("5e3018"), GOLDF, lambda d, x0, y0, x1, y1, S: pf.gear_emblem(d, x0, y0, x1, y1, S, teeth=10),
                                             3303, fringe=GOLDF, point="v", emblem_box=(0.12, 0.16, 0.88, 0.6)))
    atlas.add("ar_wall", 128, 64, pf.patchwork(RUST, 3304, patches=((_rgb("6a3418"), 6, 4, 9), (_rgb("a85a2e"), 4, 4, 8)), folds=5,
                                               shade=(0.7, 0.92)))
    atlas.add("ar_valance", 192, 32, pf.crenels([ORANGE, CREAM], _rgb("6a3214"), 3305, n=12, depth=0.62,
                                                deco=lambda d, x0, y0, x1, y1, S: pf.gear_emblem(d, x0, y0, x1, y1, S, colour=(214, 150, 50),
                                                                                                 dark=(110, 64, 20), teeth=8),
                                                deco_every=3))
    atlas.add("ar_gear", 64, 64, pf.gear_disc((220, 160, 56), (110, 66, 20), 3306, teeth=12, spokes=5))
    atlas.add("ar_steel", 64, 32, pf.steel(_rgb("4e5056"), 3307, rivets=6, plates=2, rust=_rgb("8a4a22"), rust_n=4))
    atlas.add("ar_crate", 32, 32, pf.crate_face(_rgb("8a5a30"), _rgb("40260e"), 3308, emblem=lambda d, x0, y0, x1, y1, S: pf.gear_emblem(
        d, x0, y0, x1, y1, S, colour=(228, 172, 64), dark=(110, 66, 20), teeth=8)))
    atlas.add("ar_brass", 32, 32, pf.metal(BRASS, 3309))
    atlas.add("ar_copper", 32, 32, pf.metal(COPPER, 3310))
    atlas.add("ar_tank", 32, 32, pf.steel(_rgb("44464c"), 3311, rivets=4, plates=2))
    atlas.add("ar_post", 64, 16, pf.wood(_rgb("a8622e"), _rgb("4e2a10"), 3312, plank=16))
    atlas.add("f_flame", 8, 8, pf.flames(3313))
    if atlas.size != 512:
        raise AssertionError("the atlas grew to %d px: repack the regions" % atlas.size)


# ---------------------------------------------------------------- pieces
def iron_post(shell, det, name, x, z, top, d=0.48, finial=True):
    """A heavy post: orange wood sheathed in riveted steel plates at the foot, the middle and under the cap, steel
    corner brackets, an iron cap and a brass finial; collides from the ground up to the eave."""
    box(shell, name + "_foot", (x - 0.34, 0.0, z - 0.34), (x + 0.34, 0.42, z + 0.34), {"all": "ar_steel", "+2": "black_iron"}, stretch=True)
    beam(shell, name, (x, 0.4, z), (x, top, z), d, {"all": "ar_post", "+1": "end_grain", "-1": "end_grain"})
    for k, (y0, y1) in enumerate(((0.4, 0.95), (1.75, 2.05), (EAVE - 0.55, EAVE + 0.05))):
        box(det if k == 1 else shell, "%s_plate_%d" % (name, k), (x - d / 2 - 0.03, y0, z - d / 2 - 0.03), (x + d / 2 + 0.03, y1, z + d / 2 + 0.03),
            {"all": "ar_steel", "+2": "black_iron", "-2": "black_iron"}, stretch=True)
    box(shell, name + "_cap", (x - 0.32, top, z - 0.32), (x + 0.32, top + 0.2, z + 0.32), {"all": "ar_steel", "+2": "black_iron"}, stretch=True)
    box(det, name + "_cap2", (x - 0.22, top + 0.2, z - 0.22), (x + 0.22, top + 0.3, z + 0.22), "black_iron")
    if finial:
        ml.octo(det, name + "_fin", (x, top + 0.3, z), 0.11, 0.12, "ar_brass")
        add_cube(det, name + "_fin_tip", (x, top + 0.56, z), ry(math.pi / 4), (0.15, 0.3, 0.15), "ar_brass")
        add_cube(det, name + "_fin_pt", (x, top + 0.76, z), ry(math.pi / 4), (0.07, 0.12, 0.07), "ar_brass")
    collide((x - 0.3, 0.0, z - 0.3, x + 0.3, EAVE, z + 0.3))


def girder(shell, det, name, a, b, h=0.36, w=0.24):
    """A riveted steel girder from a to b (its top centre line), its flanges darker."""
    a, b = v3(*a), v3(*b)
    beam(shell, name, a - UP * h / 2, b - UP * h / 2, h, {"all": "ar_steel", "+1": "black_iron", "-1": "black_iron"}, width=w, extend=0.25)
    beam(det, name + "_top", a, b, 0.06, "black_iron", width=w + 0.08, extend=0.28)
    beam(det, name + "_bot", a - UP * h, b - UP * h, 0.06, "black_iron", width=w + 0.08, extend=0.28)


def boiler(shell, det, name, foot, r=0.48, h=0.8):
    """The riveted iron boiler: an octagonal tank with brass bands, a domed top (two smaller octagons), a little
    chimney with a brass cap, rivets in the texture; returns the chimney's top point."""
    foot = v3(*foot)
    ml.octo(shell, name + "_tank", foot, r, h, "ar_tank")
    for k, y in enumerate((0.08, h - 0.14)):
        ml.octo(det, "%s_band_%d" % (name, k), foot + UP * y, r + 0.03, 0.07, "ar_brass")
    ml.octo(shell, name + "_dome0", foot + UP * h, r * 0.86, 0.14, "ar_tank")
    ml.octo(shell, name + "_dome1", foot + UP * (h + 0.14), r * 0.58, 0.12, "ar_brass")
    c0 = foot + UP * (h + 0.26)
    ml.octo(shell, name + "_chimney", c0, 0.16, 0.7, "black_iron")
    ml.octo(det, name + "_chimney_ring", c0 + UP * 0.25, 0.19, 0.07, "ar_brass")
    ml.octo(shell, name + "_chimney_cap", c0 + UP * 0.7, 0.23, 0.14, "ar_brass")
    ml.octo(det, name + "_chimney_lip", c0 + UP * 0.84, 0.18, 0.05, "black_iron")
    for k in range(4):   # the cradle legs down onto the roof frame
        a = math.pi / 4 + k * math.pi / 2
        p = foot + v3(math.cos(a) * r * 0.8, 0, math.sin(a) * r * 0.8)
        beam(det, "%s_leg_%d" % (name, k), p, p - UP * 0.35 + v3(math.cos(a), 0, math.sin(a)) * 0.08, 0.06, "black_iron")
    add_cube(det, name + "_gauge", foot + UP * (h * 0.55) + v3(0, 0, r + 0.02), EYE, (0.16, 0.16, 0.05), {"all": "ar_brass", "+3": "white"})
    return c0 + UP * 0.9


def tank(shell, det, name, foot, r=0.42, h=0.8):
    """The riveted iron pressure tank: an octagonal body with brass bands and plates, a dome, a valve wheel."""
    foot = v3(*foot)
    box(shell, name + "_base", foot + v3(-r - 0.04, 0, -r - 0.04), foot + v3(r + 0.04, 0.1, r + 0.04), "black_iron")
    ml.octo(shell, name + "_body", foot + UP * 0.1, r, h, "ar_tank")
    for k, y in enumerate((0.2, h - 0.05)):
        ml.octo(det, "%s_band_%d" % (name, k), foot + UP * y, r + 0.03, 0.07, "ar_brass")
    ml.octo(shell, name + "_dome0", foot + UP * (h + 0.1), r * 0.85, 0.12, "ar_tank")
    ml.octo(shell, name + "_dome1", foot + UP * (h + 0.22), r * 0.55, 0.1, "ar_tank")
    beam(det, name + "_valve_stem", foot + UP * (h + 0.32), foot + UP * (h + 0.45), 0.05, "ar_brass")
    add_cube(det, name + "_valve", foot + UP * (h + 0.47), EYE, (0.2, 0.03, 0.2), "ar_brass")
    for k, a in enumerate((0.0, math.pi / 2)):
        add_cube(det, "%s_plate_%d" % (name, k), foot + UP * (h * 0.5) + v3(math.sin(a), 0, math.cos(a)) * (r + 0.02), ry(a), (0.18, 0.26, 0.03),
                 "ar_brass")
    collide((foot[0] - r, 0.0, foot[2] - r, foot[0] + r, h + 0.5, foot[2] + r))


def gadget(det, name, foot, s=1.0):
    """A little brass machine: a base, a drum, a gear on its side, a small funnel."""
    foot = v3(*foot)
    box(det, name + "_base", foot + v3(-0.16, 0, -0.12) * s, foot + v3(0.16, 0.06, 0.12) * s, "black_iron")
    ml.octo(det, name + "_drum", foot + UP * 0.06 * s, 0.09 * s, 0.16 * s, "ar_brass")
    ml.plate(det, name + "_gear", foot + v3(0.12, 0.15, 0.0) * s, 0.2 * s, 0.2 * s, "ar_gear", normal=(1, 0, 0), th=0.02)
    beam(det, name + "_funnel", foot + UP * 0.22 * s, foot + v3(-0.05, 0.36, 0) * s, 0.05 * s, "ar_copper")


# ---------------------------------------------------------------- the build
def build(atlas, decor):
    global CHIMNEY_TOP
    rng = random.Random(33)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]   # FL, FR, BR, BL
    tops = [EAVE + 0.45, EAVE + 0.35, EAVE + 0.35, EAVE + 0.75]
    for k, (x, z) in enumerate(corners):
        iron_post(shell, det, "post_%d" % k, x, z, tops[k])
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        girder(shell, det, "girder_%d" % k, (xa, EAVE, za), (xb, EAVE, zb))
    # ---- the roof: a sweeping pointed marquee, a crenellated valance
    apex = (0.0, APEX, 0.0)
    C = (0.0, 2.0, 0.0)
    faces = []
    for k, ((xa, za), (xb, zb)) in enumerate((((-W, D), (W, D)), ((W, D), (W, -D)), ((W, -D), (-W, -D)), ((-W, -D), (-W, D)))):
        P = pf.roof_face(shell, "roof_%d" % k, apex, apex, (xa, EY, za), (xb, EY, zb), "ar_roof", nx=4, ny=6, sag=0.2, concave=0.75, centre=C,
                         droop=0.12)
        faces.append(P)
        pf.flap(shell, "valance_%d" % k, P, 0.62, "ar_valance", nx=4, out=0.04, sway=0.0)
    # ---- the crown on the peak and the copper pipes to the boiler
    ml.octo(shell, "crown_ring", (0, APEX - 0.2, 0), 0.32, 0.22, "black_iron")
    ml.octo(shell, "crown", (0, APEX + 0.02, 0), 0.24, 0.36, "ar_brass")
    ml.octo(det, "crown_band", (0, APEX + 0.16, 0), 0.27, 0.06, "black_iron")
    ml.octo(shell, "crown_cap", (0, APEX + 0.38, 0), 0.16, 0.16, "black_iron")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        add_cube(det, "crown_prong_%d" % k, (math.cos(a) * 0.2, APEX + 0.48, math.sin(a) * 0.2), ry(a), (0.07, 0.2, 0.07), "ar_brass")
    add_cube(det, "crown_spike", (0, APEX + 0.68, 0), ry(math.pi / 4), (0.08, 0.3, 0.08), "black_iron")
    # pipe A: rises from the left slope and bends into the crown
    pf.pipe(shell, det, "pipe_a", [(-0.95, 5.32, 0.15), (-0.95, APEX + 0.35, 0.15), (-0.24, APEX + 0.35, 0.15)], 0.12)
    # pipe B: from the crown down the right slope in steps to the boiler
    bx, bz = BOILER
    pf.pipe(shell, det, "pipe_b", [(0.24, APEX + 0.1, 0.0), (1.1, APEX + 0.1, 0.0), (1.1, 5.95, 0.0), (1.1, 5.95, bz), (bx - 0.42, 5.95, bz),
                                   (bx - 0.42, 5.3, bz)], 0.12)
    tb = bx / W
    roof_y = faces[1](0.5 - bz / (2 * D * tb), tb)[1]
    CHIMNEY_TOP = boiler(shell, det, "boiler", (bx, roof_y + 0.12, bz), r=0.62, h=0.86)
    # ---- gears on the front girder, the banner on its brass arm, the lantern, ropes
    gy = EAVE - 0.2
    pf.gear_plate(shell, det, "gear_big", (-1.75, gy, HD + 0.2), (0, 0, 1), 0.62, "ar_gear", "ar_brass")
    pf.gear_plate(shell, det, "gear_small", (-0.85, gy + 0.12, HD + 0.18), (0, 0, 1), 0.32, "ar_gear", "ar_brass")
    ay = tops[3] - 0.15
    pf.pipe(shell, det, "banner_arm", [(-HW - 0.25, ay, -HD), (-HW - 1.55, ay, -HD)], 0.07, region="ar_brass", flange="ar_copper", elbow=False)
    add_cube(det, "banner_arm_valve", (-HW - 1.6, ay + 0.12, -HD), EYE, (0.14, 0.14, 0.14), "ar_brass")
    ml.banner(shell, "banner", (-HW - 0.9, ay - 0.1, -HD + 0.1), 1.0, 2.0, normal=(0, 0, 1), region="ar_banner", rod=False)
    pf.lantern_arm(shell, det, "lamp_fl", (-HW + 0.28, 2.95, HD + 0.1), (1, 0, 0.3), drop=0.55, size=0.44, length=0.5)
    for k, (top, peg) in enumerate((((HW, EAVE + 0.2, HD), (HW + 1.35, 0.0, HD + 0.55)), ((-HW - 1.55, ay, -HD), (-HW - 2.25, 0.0, -HD + 0.7)),
                                     ((HW, EAVE + 0.2, -HD), (HW + 1.3, 0.0, -HD - 0.5)))):
        pf.guy(det, "guy_%d" % k, top, peg, sag=0.04, d=0.07)
    pf.leaning_pole(shell, "pole_l", (-HW - 2.35, 0.0, -HD + 1.1), (-HW - 1.6, 2.6, -HD + 0.45), d=0.08, wrap="leather")
    # ---- walls: rust canvas at the back and the back half of the sides
    wall_top = EAVE - 0.38
    pf.hang_wall(shell, "wall_back", (-HW, 0, -HD + 0.12), (HW, 0, -HD + 0.12), 0.0, wall_top, -Z, "ar_wall", nx=6)
    collide((-HW, 0.0, -HD + 0.06, HW, wall_top, -HD + 0.18))
    for k, sx in enumerate((-1, 1)):
        x = sx * (HW - 0.12)
        zf = -0.9 if sx < 0 else 0.3
        pf.hang_wall(shell, "wall_side_%d" % k, (x, 0, -HD), (x, 0, zf), 0.0, wall_top, v3(sx, 0, 0), "ar_wall", nx=4)
        collide((x - 0.06, 0.0, -HD, x + 0.06, wall_top, zf))
    # ---- inside: the back shelves (glowing lamps, brass gadgets, cogs, bottles)
    sx0, sx1 = -HW + 0.7, HW - 0.7
    levels = ml.shelf_unit(shell, "shelves", sx0, sx1, SHELF_Z[0], SHELF_Z[1], levels=(0.6, 1.2, 1.8), h=2.35, back=True, uprights=4, detail=det)
    lv = sorted(levels, key=lambda s: s[2])
    zc = (SHELF_Z[0] + SHELF_Z[1]) / 2
    for i, x in enumerate((-1.7, 0.1, 1.85)):
        ml.lantern(shell, "shelf_lamp_%d" % i, (x, lv[1][2] + 0.17, zc), size=0.24, metal="iron")
    for j, (x0, x1, y, _, _) in enumerate(lv):
        n = 6
        for i in range(n):
            x = x0 + 0.25 + (x1 - x0 - 0.5) * i / (n - 1)
            if j == 1 and i in (0, 3, 5):
                continue
            kind = (i + 2 * j) % 3
            if kind == 0:
                gadget(det, "gad_%d_%d" % (j, i), (x, y, zc), s=1.0)
            elif kind == 1:
                ml.plate(det, "cog_%d_%d" % (j, i), (x, y + 0.14, zc - 0.05), 0.26, 0.26, "ar_gear", normal=(0, 0, 1), th=0.03)
            else:
                ml.bottle(det, "oil_%d_%d" % (j, i), (x, y, zc), ("orange", "yellow", "green")[(i + j) % 3], r=0.07, h=0.18, shape="tall")
    decor.block("mebahelcreaturesdwarven:dwemer_metal_pipe_gear", 0.1, lv[2][2], zc, facing="pos_x", scale=0.5, fallback="ar_brass", solid=False)
    # ---- the central counter (workbench): vice, gadget, gears, a lamp (mod)
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    yt = top[1]
    zc = (cz0 + cz1) / 2
    ml.plate(shell, "counter_plate", (zc * 0 + (cx0 + cx1) / 2, yt - 0.42, cz1 + 0.06), cx1 - cx0 - 0.1, 0.5, "ar_steel", normal=(0, 0, 1), th=0.02)
    box(det, "vice_base", (cx0 + 0.2, yt, zc - 0.1), (cx0 + 0.45, yt + 0.12, zc + 0.12), "black_iron")
    box(det, "vice_jaw", (cx0 + 0.24, yt + 0.12, zc - 0.06), (cx0 + 0.41, yt + 0.28, zc + 0.02), "black_iron")
    beam(det, "vice_screw", (cx0 + 0.32, yt + 0.18, zc + 0.02), (cx0 + 0.32, yt + 0.18, zc + 0.3), 0.04, "steel")
    gadget(det, "counter_gadget", (0.05, yt, zc), s=1.5)
    for i, x in enumerate((0.75, 1.0)):
        ml.plate(det, "counter_cog_%d" % i, (x, yt + 0.012, zc + 0.05 * i), 0.24 - 0.06 * i, 0.24 - 0.06 * i, "ar_gear", normal=(0, 1, 0), up=(0, 0, -1),
                 th=0.02)
    decor.block("farmhouse_decorations:kerosene_lantern", 1.45, yt, zc, facing="front", glow=True, alt="minecraft:lantern", fallback="lantern", solid=False)
    # ---- along the left wall: a workbench (mod) and a tool board (mod)
    decor.block("farmhouse_decorations:workbench", -HW + 0.62, 0.0, -1.5, facing="pos_x", scale=0.9, fallback="crate")
    decor.block("farmhouse_decorations:tool_board", -HW + 0.25, 1.55, -1.5, facing="pos_x", scale=0.9, fallback="plank_dark", solid=False)
    # ---- a tall cabinet at the inside left front: drawers, a lamp, gadgets
    kx0, kx1, kz0, kz1 = -HW + 0.35, -HW + 1.0, -0.55, 0.45
    ml.shelf_unit(shell, "cabinet", kx0, kx1, kz0, kz1, levels=(0.7, 1.3), h=1.85, back=False, uprights=2, detail=det,
                             solid=False)
    box(shell, "cabinet_body", (kx0, 0.0, kz0), (kx1, 0.64, kz1), {"all": "ar_crate", "+2": "plank"}, stretch=True)
    collide((kx0 - 0.05, 0.0, kz0, kx1 + 0.05, 1.85, kz1))
    ml.lantern(shell, "cabinet_lamp", ((kx0 + kx1) / 2, 1.85 + 0.2, (kz0 + kz1) / 2), size=0.26, metal="iron")
    gadget(det, "cabinet_gadget", ((kx0 + kx1) / 2, 1.3, (kz0 + kz1) / 2), s=1.2)
    ml.bottle(det, "cabinet_oil", ((kx0 + kx1) / 2, 0.7, (kz0 + kz1) / 2 + 0.2), "orange", r=0.08, h=0.2, shape="tall")
    # ---- the rug with the gear
    ml.rug(shell, "rug", -1.7, 2.0, -0.75, 3.05, y=0.0, region="ar_rug")
    # ---- outside left: the pressure tank, a barrel, big crates with gear emblems
    tank(shell, det, "tank", (-HW - 1.0, 0.0, -HD + 0.75), r=0.5, h=0.85)
    ml.barrel(shell, "barrel_bl", (-HW - 1.05, 0.0, -HD - 0.45), r=0.34, h=0.88)
    for k, z in enumerate((-0.75, 0.45, 1.65)):
        ml.crate(shell, "crate_l_%d" % k, (-HW - 0.62, 0.0, z), size=(0.9, 0.86, 0.95), yaw=0.0, region="ar_crate", top="crate_top")
    gadget(det, "crate_gadget", (-HW - 0.62, 0.86, 0.45), s=1.4)
    # ---- outside front right: crates and the golden-bronze chest (mod)
    ml.crate(shell, "crate_r_0", (HW + 0.75, 0.0, HD - 0.35), size=(0.85, 0.8, 0.85), yaw=0.08, region="ar_crate", top="crate_top")
    ml.crate(shell, "crate_r_1", (HW + 0.75, 0.8, HD - 0.35), size=(0.6, 0.5, 0.6), yaw=-0.1, region="ar_crate", top="crate_top")
    decor.block("mebahelcreaturesdwarven:dwemer_chest", HW + 0.75, 0.0, HD - 1.4, facing="neg_x", scale=0.85, alt="minecraft:chest", fallback="ar_brass")
    decor.block("furnish:spruce_crate", HW - 0.75, 0.0, 1.6, facing="neg_x", scale=0.75, alt="minecraft:barrel", fallback="crate")
    return root


def item_icon(path):
    """16x16: an orange-and-cream striped marquee with a crenellated valance, a gear and a little chimney."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    for y in range(2, 10):
        half = 0.8 + (y - 2) * 0.95
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                stripe = int((dx / max(half, 0.5)) * 3 + 3) % 2
                p[x, y] = (ORANGE if stripe == 0 else CREAM) + (255,)
    p[7, 1] = p[8, 1] = (70, 70, 76, 255)
    p[7, 0] = p[8, 0] = GOLDF + (255,)
    for y in range(3, 7):
        p[12, y] = (60, 60, 66, 255)
    p[12, 2] = (200, 160, 60, 255)
    for x in range(0, 16):
        p[x, 10] = (ORANGE if (x // 2) % 2 == 0 else CREAM) + (255,)
        if x % 3:
            p[x, 11] = (ORANGE if (x // 2) % 2 == 0 else CREAM) + (255,)
    for y in range(10, 16):
        for x in (1, 14):
            p[x, y] = (80, 82, 88, 255)
        for x in range(2, 14):
            if y > 11:
                p[x, y] = (46, 32, 22, 255)
    for (x, y) in ((4, 12), (5, 12), (4, 13), (5, 13), (6, 12), (3, 13)):
        p[x, y] = GOLDF + (255,)
    for x in range(3, 13):
        p[x, 15] = (140, 72, 36, 255)
    im.save(path)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="brown")
    add_regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13,
              particles=[ml.particle("smoke", CHIMNEY_TOP, chance=0.15, count=2)])


if __name__ == "__main__":
    main()
