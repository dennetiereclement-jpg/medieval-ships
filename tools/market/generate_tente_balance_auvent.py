#!/usr/bin/env python3
"""tente_balance_auvent — Tente à la balance et à l'auvent / Scales Tent with Awning (1.26.0, market tents group D;
reference: scratchpad/ref2/tente_balance_auvent_ref.png, picture 080).

A red-and-cream merchant tent of the scales (balance) merchants, one block (TentType group "tents"), seen in the picture
from the front left:

  - the MAIN TENT on the left: a hipped roof on a short ridge between two tall ridge posts with golden finials, the
    ridge wrapped in red cloth with iron brackets; the cloth falls from the ridge in broad irregular cream and red
    stripes, bunched round the left ridge post (the cone look of the picture), down to a cream valance with red dags
    under the eaves; four corner posts with iron bands and golden finials; thick twisted ropes along the hip edges and
    swagged along the front eave; the LEFT WALL is closed, cream canvas flaring out on the ground, with a big red scales
    banner on it; the back and right walls are closed; the front is open between cream drapes tied to the posts;
  - a big red SCALES BANNER laid on the front slope of the roof, hanging from a crossbar near the right ridge post;
    small scales banners on brackets on the back-left post and on the awning's front-right post;
  - the long red patterned AWNING on the front right: from the main tent's front eave down to a front beam on two
    posts with finials, red with cream bands and a gold meander, edged with a dagged valance of red, gold and cream
    tabs; a lantern hangs under it and another from its front beam;
  - under the awning the COUNTER (running front to back, its front facing the carpet on the left): a red runner with a
    gold border and a pointed hem, an open book, potion bottles, a ribboned parcel, a scroll; the merchant stands
    behind it (NPC_SPOT); at the front a planter box of purple flowers, crates and a cream canvas bale at the posts;
  - inside the main tent: back shelves of potions (blue, purple, pink, green), books, cloth rolls and small sacks, a
    gold-trimmed chest, crates, an open sack of grain, a crate under a red cloth, a lantern in the opening and one on
    the front-left post;
  - outside the left wall: a big iron-banded crate with cloth rolls on it, crates of red and green produce (Farmer's
    Delight crates when the mod is installed), a rice sack;
  - the RED-AND-GOLD carpet in front of the main tent's opening, along the counter.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter under the awning; players reach it through
the gap at the front of the awning (between the bale and the flower box), from the awning's open right side, or
through the main tent. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_balance_auvent.py   (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_balance_auvent.json, models/entity + blockbench/tente_balance_auvent.bbmodel,
textures/entity/tente_balance_auvent.png, textures/item/tente_balance_auvent.png, interiors/tente_balance_auvent_decor.json.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_d as pd  # noqa: E402

ml = pd.ml
NAME = "tente_balance_auvent"
v3, norm, add_cube, beam, loft, Bone = pd.v3, pd.norm, pd.add_cube, pd.beam, pd.loft, pd.Bone
EYE, UP, X, Z = pd.EYE, pd.UP, pd.X, pd.Z
ry, rx, rz = pd.ry, pd.rx, pd.rz
box, collide = pd.box, pd.collide
_rgb, _jitter, _scale, _mix = pd._rgb, pd._jitter, pd._scale, pd._mix

PAL = pd.Pal(cream="eec29c", red="ab3430", red_dark="64190f", red_light="c8483c", gold="ec9c3c", gold_dark="8a5414",
             gold_light="fcd27a", wood="7a4a26", wood_dark="3e2412", finial="e69232")

# ---------------------------------------------------------------- dimensions (design coordinates, +z = the front;
# the whole tent is moved at the end so that its extent is centred on the anchor block: see SHIFT)
XL, XR, ZF, ZB = -4.0, 1.0, 1.0, -2.8      # the main tent's corner posts
EAVE = 3.3                                 # top of the eave beams
EY = EAVE + 0.02                           # the roof's eave line
OV = 0.32                                  # roof overhang beyond the posts
RIDGE = 5.0
ZR = (ZF + ZB) / 2                         # the ridge line (z)
CX, DX = -3.2, 0.2                         # the two ridge posts (x)
AX0, AX1, AZ = -1.5, 2.2, 4.4              # the awning's front posts F (AX0) and G (AX1), the back-right post H (AX1, ZF)
AY_BACK, AY_FRONT = EAVE - 0.22, 2.45      # the awning: under the main eave -> top of its front beam
COUNTER = (-1.45, -0.8, 1.5, 3.9)          # x0, x1, z0, z1 (it runs front to back, its front facing -x)
COUNTER_H = 1.05
RUG = (-3.75, -1.62, 1.15, 4.95)           # x0, x1, z0, z1
NPC = (-0.55, 2.0)                         # (x0, z0) of the merchant's free 1 x 1 x 2.2 place (design coordinates)


# ---------------------------------------------------------------- textures
def paint_awning(img):
    """The awning: deep red, two cream bands along its length, gold diamond chain and meander near the front edge."""
    rng = random.Random(8001)
    pd.weave(img, PAL.red, rng, stains=2)
    w, h = img.size
    px = img.load()
    bands = ((0.16, 0.06, PAL.cream), (0.5, 0.07, PAL.cream), (0.78, 0.03, PAL.gold))
    for y in range(h):
        fy = y / h
        for x in range(w):
            r, g, b, a = px[x, y]
            c = (r, g, b)
            for c0, hw, col in bands:
                if abs(fy - c0) < hw:
                    c = _jitter(_scale(col, 0.96 + 0.06 * math.sin(x * 0.4)), rng, 8)
            # a gold meander between the bands
            ly = y - int(h * 0.62)
            if 0 <= ly < 7:
                lx = x % 8
                if (ly in (0, 6)) or (lx == 0 and ly < 5) or (lx == 4 and ly > 1) or (ly == 3 and 1 <= lx <= 4):
                    c = _jitter(PAL.gold, rng, 10)
            # small gold lozenges on the back half
            if 0.27 < fy < 0.42 and (x % 16, y % 14) in ((8, 5), (7, 6), (9, 6), (8, 7)):
                c = _jitter(PAL.gold, rng, 10)
            # long soft folds across the cloth
            k = 0.9 + 0.1 * math.sin(math.pi * ((x * 6.0 / w) % 1.0))
            px[x, y] = _scale(c, k * (0.92 + 0.12 * fy)) + (255,)


def paint_ridge(img):
    """The red cloth wrapped round the ridge pole: dark red, darker wrap lines."""
    rng = random.Random(8002)
    pd.weave(img, _scale(PAL.red, 0.86), rng, stains=0)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            if (x + y // 2) % 9 == 0:
                r, g, b, a = px[x, y]
                px[x, y] = _scale((r, g, b), 0.7) + (255,)


def paint_greens(img):
    rng = random.Random(8003)
    w, h = img.size
    ml._heap(img, (0, 0, w, h), [_rgb("7ab83a"), _rgb("5a9a2a"), _rgb("9ad04a")], rng, bg=_rgb("4a3a20"), r=3)


def produce_crate_painter(cols, seed):
    """Stand-in of a Farmer's Delight crate (drawn only without the mod): crate planks, a heap of produce on the
    upper third of each face."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), _rgb("8a5a2c"), _rgb("4a2c12"), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
        ml._heap(img, (0, 0, w, h // 3 + 2), cols, rng, bg=_rgb("4a3a20"), r=3)
        px = img.load()
        for x in range(w):
            for y in (0, h - 1):
                px[x, y] = (60, 40, 22, 255)
            for y in range(h // 3 + 2, h // 3 + 4):
                px[x, y] = (70, 46, 24, 255)
    return paint


def add_regions(atlas):
    """This tent's regions, packed by hand in rows of the 512 px atlas (see the module notes; no doubling)."""
    s = 8100
    # row 1 (y 224, after the shell regions): 96 high
    atlas.add("pd_roof", 224, 96, pd.stripes_painter(PAL, [(0.12, "r"), (0.2, "c"), (0.14, "r"), (0.2, "c"), (0.12, "r"), (0.12, "c"),
                                                          (0.1, "r")], s + 1, fold=0.16))
    atlas.add("pd_rug", 160, 96, pd.rug_painter(PAL, s + 2, motif="key"))
    atlas.add("pd_banner", 32, 88, pd.banner_painter(PAL, s + 3, point="v", stars=True, border=2, body=0.78))
    # row 2: 96 high
    atlas.add("pd_awning", 192, 96, paint_awning)
    atlas.add("pd_banner_roof", 64, 88, pd.banner_painter(PAL, s + 4, point="v", stars=True, border=3, body=0.8))
    atlas.add("pd_hip", 160, 64, pd.stripes_painter(PAL, [(0.24, "c"), (0.14, "r"), (0.22, "c"), (0.12, "r"), (0.28, "c")], s + 5,
                                                    fold=0.18))
    atlas.add("pd_wall", 96, 64, pd.canvas_painter(PAL, s + 6, folds=5, hem=PAL.red_dark))
    # row 3: 64 high
    atlas.add("pd_runner", 48, 64, pd.runner_painter(PAL, s + 7, point="v"))
    atlas.add("pd_drape", 32, 64, pd.canvas_painter(PAL, s + 8, folds=3, hem=PAL.gold))
    atlas.add("pd_valance", 192, 24, pd.valance_painter(PAL, s + 9, [(1.0, "c", 1.0), (0.5, "d", 0.75), (1.0, "c", 0.9), (0.5, "r", 0.7)] * 4,
                                                        band=0.4, band_colour="c", band_line=PAL.red_dark))
    atlas.add("pd_valance_aw", 192, 28, pd.valance_painter(PAL, s + 10, [(1.0, "r", 1.0), (0.8, "g", 0.75), (1.0, "r", 0.9), (0.8, "c", 0.7)] * 4,
                                                           band=0.36, band_colour="r", band_line=PAL.gold))
    atlas.add("pd_burlap", 32, 32, pd.burlap_painter(s + 11))
    atlas.add("pd_finial", 16, 16, pd.finial_painter(PAL, s + 12))
    # row 4: 32 high
    atlas.add("pd_chest", 32, 32, pd.chest_painter(PAL, s + 13))
    atlas.add("pd_flowers", 48, 32, pd.flowers_painter(_rgb("b040d0"), _rgb("70208c"), _rgb("f0d040"), s + 14, n=7))
    atlas.add("pd_greens", 32, 32, paint_greens)
    atlas.add("pd_fb_red", 32, 32, produce_crate_painter([_rgb("c42c22"), _rgb("e04a30"), _rgb("8a1a14")], s + 20))
    atlas.add("pd_fb_green", 32, 32, produce_crate_painter([_rgb("7ab83a"), _rgb("5a9a2a"), _rgb("9ad04a")], s + 21))
    atlas.add("pd_post", 64, 16, pd.wood_painter(PAL.wood, PAL.wood_dark, s + 15))
    atlas.add("pd_ridge", 64, 16, paint_ridge)
    atlas.add("pd_grain", 32, 16, pd.grain_painter(s + 16))
    atlas.add("pd_book", 32, 16, pd.book_painter(s + 17))
    atlas.add("pd_parcel", 16, 16, pd.parcel_painter(s + 18))
    atlas.add("pd_band", 32, 8, pd.band_painter(s + 19))
    if atlas.size != 512:
        raise AssertionError("the atlas grew to %d px: repack the regions" % atlas.size)


# ---------------------------------------------------------------- roof geometry
def drop(t, a=0.45):
    """The roof's profile (fraction of the drop at t from the ridge): steep at the ridge, flatter at the eave."""
    return a * t + (1 - a) * (1 - (1 - t) ** 2)


C3, D3 = v3(CX, RIDGE, ZR), v3(DX, RIDGE, ZR)
FL, FR = v3(XL - OV, EY, ZF + OV), v3(XR + OV, EY, ZF + OV)
BR, BL = v3(XR + OV, EY, ZB - OV), v3(XL - OV, EY, ZB - OV)


EDROOP = 0.16   # the eaves sag between the corner posts (curved valances)


def roof_surface(top0, top1, bot0, bot1, folds, depth=0.05, sag=0.1, droop=EDROOP):
    """A roof face from the ridge edge top0-top1 down to the eave edge bot0-bot1: the drop profile, a sag in the
    middle, `folds` soft folds across (the stripes bellying), the eave edge sagging by `droop` between the corners."""
    def P(s, t):
        a = top0 + (top1 - top0) * s
        b = bot0 + (bot1 - bot0) * s - UP * (droop * math.sin(math.pi * s))
        p = a + (b - a) * t
        y = a[1] - (a[1] - b[1]) * drop(t) - sag * math.sin(math.pi * t) * (0.6 + 0.4 * math.sin(math.pi * s))
        p = v3(p[0], y, p[2])
        if folds:
            frac = (s * folds) % 1.0
            # push the fold in along the face's normal (up / outwards)
            n = norm(np.cross(b - a + v3(0, 0.001, 0), top1 - top0 + v3(1e-4, 0, 1e-4)))
            if n[1] < 0:
                n = -n
            p = p - n * depth * math.sin(math.pi * frac) * math.sin(math.pi * min(1.0, t * 1.3))
        return p
    return P


FRONT = roof_surface(C3, D3, FL, FR, 7)


def front_at(x, t):
    """The point of the front roof face at world x and slope parameter t (solves s along the trapezoid)."""
    a0, a1 = C3[0] + (FL[0] - C3[0]) * t, D3[0] + (FR[0] - D3[0]) * t
    s = (x - a0) / (a1 - a0)
    return FRONT(min(max(s, 0.0), 1.0), t)


def front_normal(x, t):
    p0, p1 = front_at(x, max(0.0, t - 0.02)), front_at(x, min(1.0, t + 0.02))
    q0, q1 = front_at(x - 0.05, t), front_at(x + 0.05, t)
    n = norm(np.cross(q1 - q0, p1 - p0))
    return -n if n[1] < 0 else n


# ---------------------------------------------------------------- the build
def build(atlas, decor):
    rng = random.Random(80)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)

    # ---- main tent posts, eave beams, tie beams, ridge posts and ridge
    corners = {"A": (XL, ZB), "B": (XL, ZF), "E": (XR, ZF), "K": (XR, ZB)}
    for k, (x, z) in corners.items():
        pd.post(shell, det, "post_" + k, x, z, EAVE + 0.36, d=0.34, foot=(0.42, 0.46), bands=(1.05, EAVE - 0.6), collide_top=EAVE)
    by = EAVE - 0.24   # the eave beams stay under the drooping cloth
    ring = [corners["B"], corners["E"], corners["K"], corners["A"]]
    for k in range(4):
        (xa, za), (xb, zb) = ring[k], ring[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.24, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"}, extend=0.2)
    for k, x in enumerate((CX, DX)):
        beam(shell, "tie_%d" % k, (x, by, ZB + 0.12), (x, by, ZF), 0.2, "wood_dark", extend=0.0)
        # a king post standing on the tie beam (no collision from the ground), rising through the ridge
        pd.post(shell, det, "ridge_post_%d" % k, x, ZR, RIDGE + 0.42, d=0.3, foot=(0.0, 0.0), bands=(RIDGE - 0.32,), cap_w=0.42, tall=1.35,
                base=by + 0.1, solid=False)
    beam(shell, "ridge_pole", (CX - 0.42, RIDGE - 0.08, ZR), (DX + 0.42, RIDGE - 0.08, ZR), 0.3, {"all": "pd_ridge", "+1": "pd_post", "-1": "pd_post"},
         width=0.34)
    for k, x in enumerate((CX + 0.55, (CX + DX) / 2, DX - 0.55, CX - 0.3, DX + 0.3)):
        box(det, "ridge_bracket_%d" % k, (x - 0.06, RIDGE - 0.26, ZR - 0.19), (x + 0.06, RIDGE + 0.1, ZR + 0.19), "iron")

    # ---- the roof: front and back faces, the two hips (cloth bunched round the ridge posts)
    loft(shell, "roof_front", FRONT, 14, 5, "pd_roof", th=0.04, overlap=0.05)
    loft(shell, "roof_back", roof_surface(D3, C3, BR, BL, 7), 14, 5, "pd_roof", th=0.04, overlap=0.05)
    # (the hip faces share the eave corners and the ridge ends with the front and back faces; ropes cover the seams)
    eps = v3(0, 0, 0.02)
    loft(shell, "roof_hip_l", roof_surface(C3 - eps, C3 + eps, BL, FL, 5, depth=0.07, sag=0.12), 8, 4, "pd_hip", th=0.04, overlap=0.03)
    loft(shell, "roof_hip_r", roof_surface(D3 + eps, D3 - eps, FR, BR, 5, depth=0.07, sag=0.12), 8, 4, "pd_hip", th=0.04, overlap=0.03)
    # rafters under the cloth, following the concave front and back faces (the back face is the front one turned
    # half round about the tent's centre)
    xc = (XL + XR) / 2
    for k, x in enumerate((CX + 0.4, DX - 0.4)):
        for j, back in enumerate((False, True)):
            pts = []
            for t in (0.06, 0.35, 0.7, 0.93):
                p = front_at(2 * xc - x if back else x, t) - UP * 0.17
                pts.append(v3(2 * xc - p[0], p[1], 2 * ZR - p[2]) if back else p)
            for i in range(3):
                beam(shell, "rafter_%d_%d_%d" % (k, j, i), pts[i], pts[i + 1], 0.12, "wood_dark", extend=0.03)
    # the valance under the eaves (cream with red dags)
    for k, (a, b, o) in enumerate(((FL, FR, Z), (FR, BR, X), (BR, BL, -Z), (BL, FL, -X))):
        pd.valance(shell, "valance_%d" % k, a, b, o, h=0.5, region="pd_valance", tab_len=2.0, droop=EDROOP)
    # thick ropes along the hip edges (ridge post tops -> corner post tops) and swagged along the front eave
    # (the hip ropes lie on the seams between the faces and the hips, from the ridge post tops to the eave corners)
    back = roof_surface(D3, C3, BR, BL, 7)
    for k, (P, sv, top) in enumerate(((FRONT, 0.0, C3), (FRONT, 1.0, D3), (back, 0.0, D3), (back, 1.0, C3))):
        pts = [v3(top[0], RIDGE + 0.32, top[2])] + [P(sv, t) + UP * 0.07 for t in (0.04, 0.25, 0.5, 0.75, 1.0)]
        for i in range(len(pts) - 1):
            beam(det, "hip_rope_%d_%d" % (k, i), pts[i], pts[i + 1], 0.11, "rope", extend=0.05)
    ml.rope(det, "eave_swag_0", (XL + 0.1, EAVE + 0.12, ZF + OV + 0.05), (XL + 1.45, EAVE + 0.12, ZF + OV + 0.05), d=0.1, sag=0.28, segs=4)
    ml.rope(det, "eave_swag_1", (XL + 1.45, EAVE + 0.12, ZF + OV + 0.05), (AX0 - 0.1, EAVE + 0.12, ZF + OV + 0.05), d=0.1, sag=0.28, segs=4)
    add_cube(det, "eave_knot", (XL + 1.45, EAVE + 0.1, ZF + OV + 0.06), EYE, (0.18, 0.2, 0.15), "rope")
    for k, (x, z) in enumerate((corners["B"], corners["A"], corners["E"], corners["K"])):
        pd.rope_wrap(det, "post_coil_%d" % k, x, z, EAVE + 0.14, 0.17, turns=2)
    for k, x in enumerate((XL + 0.75, -1.9, XR - 0.75)):
        box(det, "eave_strap_%d" % k, (x - 0.06, by - 0.15, ZF - 0.15), (x + 0.06, by + 0.15, ZF + 0.15), "iron")

    # ---- the big scales banner on the front slope, hanging from a crossbar near the right ridge post
    bxc, bw = -0.85, 1.25
    t0, t1 = 0.1, 0.86

    def BAN(s, t):
        tt = t0 + (t1 - t0) * t
        x = bxc + (s - 0.5) * bw
        return front_at(x, tt) + front_normal(x, tt) * (0.07 + 0.03 * math.sin(math.pi * s))
    loft(shell, "roof_banner", BAN, 1, 4, "pd_banner_roof", th=0.02, u_hint=X)
    bar0, bar1 = front_at(bxc - bw / 2 - 0.25, 0.08), front_at(bxc + bw / 2 + 0.25, 0.08)
    nb = front_normal(bxc, 0.08)
    beam(shell, "banner_bar", bar0 + nb * 0.12, bar1 + nb * 0.12, 0.12, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"})
    for k, p in enumerate((bar0, bar1)):
        add_cube(det, "banner_bar_knob_%d" % k, p + nb * 0.12, EYE, (0.16, 0.16, 0.16), "pd_finial")
    beam(shell, "banner_bar_strut", bar1 + nb * 0.12, (DX + 0.05, RIDGE + 0.05, ZR + 0.12), 0.1, "iron")
    # a rope from the crossbar's left end down the front slope to the front-left post (as in the picture)
    pts = [front_at(bxc - bw / 2 - 0.25 + (XL - 0.1 - (bxc - bw / 2 - 0.25)) * f, 0.08 + 0.92 * f) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
    for k in range(4):
        beam(det, "slope_rope_%d" % k, pts[k] + front_normal(pts[k][0], 0.08 + 0.23 * k) * 0.1,
             pts[k + 1] + front_normal(pts[k + 1][0], 0.08 + 0.23 * (k + 1)) * 0.1, 0.1, "rope", extend=0.04)

    # ---- walls: the closed left wall (flaring on the ground) with its banner, back and right walls
    wy = by - 0.12
    pd.wall(shell, "wall_left", (XL - 0.07, 0, ZB), (XL - 0.07, 0, ZF), 0.0, wy, -X, region="pd_wall", nx=7, fold=0.07, flare=0.45)
    collide((XL - 0.5, 0.0, ZB, XL - 0.03, wy, ZF))
    pd.wall(shell, "wall_back", (XR, 0, ZB - 0.07), (XL, 0, ZB - 0.07), 0.0, wy, -Z, region="pd_wall", nx=6, fold=0.05, flare=0.15)
    collide((XL, 0.0, ZB - 0.22, XR, wy, ZB - 0.03))
    pd.wall(shell, "wall_right", (XR + 0.07, 0, ZF - 0.2), (XR + 0.07, 0, ZB), 0.0, wy, X, region="pd_wall", nx=5, fold=0.05, flare=0.12)
    collide((XR + 0.03, 0.0, ZB, XR + 0.19, wy, ZF - 0.2))
    ml.banner(shell, "wall_banner", (XL - 0.3, 3.0, ZR + 0.1), 1.0, 2.15, normal=(-1, 0, 0), region="pd_banner", rod=True, wave=0.03,
              rod_region="pd_post", knobs="pd_finial")
    # drapes tied back inside the front posts
    for k, sx in enumerate((1, -1)):
        x = XL if sx > 0 else XR
        pd.drape(shell, det, "drape_%d" % k, (x + sx * 0.24, wy, ZF - 0.12), (x + sx * 1.05, wy, ZF - 0.12), (x + sx * 0.3, 1.35, ZF - 0.14),
                 (x + sx * 0.22, 0.03, ZF - 0.14), (x + sx * 0.66, 0.03, ZF - 0.14), Z, region="pd_drape")

    # ---- the awning: posts, beams, the patterned cloth, its dagged valance
    for k, (x, z) in enumerate(((AX0, AZ), (AX1, AZ))):
        pd.post(shell, det, "apost_%d" % k, x, z, AY_FRONT + 0.32, d=0.3, foot=(0.38, 0.4), bands=(0.95, AY_FRONT - 0.5), collide_top=AY_FRONT + 0.32)
    pd.post(shell, det, "apost_h", AX1, ZF, AY_BACK + 0.3, d=0.28, foot=(0.36, 0.38), bands=(1.0,), collide_top=AY_BACK + 0.3)
    fb = AY_FRONT - 0.1
    beam(shell, "a_beam_front", (AX0, fb, AZ), (AX1, fb, AZ), 0.2, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"}, extend=0.22)
    beam(shell, "a_beam_left", (AX0, fb, AZ), (AX0, AY_BACK - 0.08, ZF + 0.12), 0.18, "pd_post", extend=0.1)
    beam(shell, "a_beam_right", (AX1, fb, AZ), (AX1, AY_BACK - 0.08, ZF + 0.12), 0.18, "pd_post", extend=0.1)
    beam(shell, "a_beam_back", (XR, AY_BACK - 0.08, ZF), (AX1, AY_BACK - 0.08, ZF), 0.2, "pd_post", extend=0.1)
    for k, x in enumerate((AX0, AX1)):
        box(det, "a_bracket_%d" % k, (x - 0.19, fb - 0.13, AZ - 0.19), (x + 0.19, fb + 0.13, AZ + 0.19), {"all": "pd_band", "+2": "iron", "-2": "iron"},
            stretch=True)
    ax0, ax1, az0, az1 = AX0 - 0.2, AX1 + 0.2, ZF + 0.08, AZ + 0.3
    slope = (AY_BACK - (AY_FRONT + 0.08)) / (AZ - az0)

    def AW(s, t):
        x = ax0 + (ax1 - ax0) * s
        z = az0 + (az1 - az0) * t
        y = AY_BACK - slope * (z - az0) - 0.12 * math.sin(math.pi * min(t * 1.08, 1.0)) * (0.6 + 0.4 * math.sin(math.pi * s))
        frac = (s * 6) % 1.0
        return v3(x, y - 0.04 * math.sin(math.pi * frac) * math.sin(math.pi * t), z)
    loft(shell, "awning", AW, 12, 3, "pd_awning", th=0.035, overlap=0.03)
    ye = AW(0.5, 1.0)[1]
    pd.valance(shell, "a_valance_front", (ax0, ye, az1 + 0.01), (ax1, ye, az1 + 0.01), Z, h=0.44, region="pd_valance_aw", tab_len=1.4)
    pd.valance(shell, "a_valance_left", (ax0 - 0.01, AW(0, 0.05)[1], az0 + 0.25), (ax0 - 0.01, AW(0, 1.0)[1], az1), -X, h=0.4, region="pd_valance_aw",
               tab_len=1.4)
    pd.valance(shell, "a_valance_right", (ax1 + 0.01, AW(1, 1.0)[1], az1), (ax1 + 0.01, AW(1, 0.05)[1], az0 + 0.25), X, h=0.4, region="pd_valance_aw",
               tab_len=1.4)

    # ---- scales banners on brackets: back-left post (small, outwards), awning front-right post (bigger, outwards)
    for k, (x, z, sx, y, w, h) in enumerate(((XL, ZB, -1, 2.75, 0.44, 1.0), (AX1, AZ, 1, 2.25, 0.62, 1.4))):
        tip = v3(x + sx * (w + 0.45), y, z)
        beam(shell, "flag_arm_%d" % k, (x + sx * 0.15, y, z), tip, 0.1, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"}, extend=0.05)
        beam(det, "flag_arm_brace_%d" % k, (x + sx * 0.17, y - 0.45, z), (x + sx * 0.6, y - 0.03, z), 0.06, "iron")
        add_cube(det, "flag_arm_knob_%d" % k, tip + X * sx * 0.06, EYE, (0.13, 0.13, 0.13), "pd_finial")
        bc = v3(x + sx * (w / 2 + 0.32), y - 0.07, z + 0.02)
        ml.banner(shell, "post_banner_%d" % k, bc, w, h, normal=(0, 0, 1), region="pd_banner", rod=False, wave=0.03)
        for j, dx in enumerate((-w / 2 + 0.05, w / 2 - 0.05)):
            add_cube(det, "post_banner_%d_ring_%d" % (k, j), bc + X * dx + UP * 0.05, EYE, (0.05, 0.12, 0.05), "iron")

    # ---- lanterns: in the opening (from the front eave), on the front-left post, under the awning, on its front beam
    ml.lantern(shell, "lamp_open", (-2.75, 2.45, ZF + 0.02), size=0.36, metal="iron", chain_to=(-2.75, by - 0.12, ZF + 0.02))
    beam(det, "lamp_b_arm", (XL + 0.17, 1.82, ZF), (XL + 0.48, 1.82, ZF), 0.05, "iron", extend=0.02)
    beam(det, "lamp_b_brace", (XL + 0.17, 1.5, ZF), (XL + 0.46, 1.8, ZF), 0.04, "iron")
    ml.lantern(shell, "lamp_post", (XL + 0.48, 1.52, ZF), size=0.26, metal="iron", chain_to=(XL + 0.48, 1.8, ZF))
    zl = 2.75
    yl = AY_BACK - 0.08 - (AY_BACK - 0.08 - fb) * (zl - ZF - 0.12) / (AZ - ZF - 0.12)
    ml.lantern(shell, "lamp_awning", (AX0 + 0.05, yl - 0.62, zl), size=0.34, metal="iron", chain_to=(AX0 + 0.05, yl - 0.1, zl))
    ml.lantern(shell, "lamp_front", (1.45, fb - 0.62, AZ), size=0.36, metal="iron", chain_to=(1.45, fb - 0.1, AZ))

    # ---- the counter (front to back, its front facing -x) with its runner and goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    box(shell, "counter_cloth", (cx0 - 0.04, y, cz0 + 0.25), (cx0 + 0.3, y + 0.015, cz1 - 0.25), {"all": "cloth_red"}, stretch=True, u_dir=Z)
    ml.plate(shell, "runner", (cx0 - 0.06, y - 0.42, (cz0 + cz1) / 2), cz1 - cz0 - 0.55, 0.86, "pd_runner", normal=(-1, 0, 0), th=0.012,
             edge="cloth_red")
    for k, (z, hgt) in enumerate(((cz0 + 0.12, 0.55), (cz1 - 0.12, 0.55))):
        box(det, "counter_band_%d" % k, (cx0 - 0.02, 0.12, z - 0.05), (cx1 + 0.02, 0.12 + hgt, z + 0.05), "iron")
    xm = (cx0 + cx1) / 2
    pd.open_book(det, "book", (xm, y + 0.015, 3.3), yaw=math.pi / 2)
    ml.bottle(det, "flask", (xm + 0.05, y, 2.82), "orange", r=0.1, h=0.2, shape="round", neck_h=0.09)
    ml.bottle(det, "flask_blue", (xm - 0.08, y, 2.55), "blue", r=0.075, h=0.18, shape="tall", neck_h=0.07)
    ml.bottle(det, "flask_red", (xm + 0.12, y, 2.45), "red", r=0.06, h=0.14, shape="round", neck_h=0.05)
    pd.parcel(det, "parcel_0", (xm, y, 2.1), size=(0.42, 0.24, 0.34), yaw=0.1)
    pd.parcel(det, "parcel_1", (xm + 0.02, y + 0.24, 2.12), size=(0.3, 0.16, 0.26), yaw=-0.25)
    pd.scroll(det, "counter_scroll", (xm - 0.05, y + 0.06, 1.72), length=0.42, r=0.06, yaw=math.pi / 2 + 0.2)
    ml.crate(det, "counter_box", (xm + 0.05, y, 3.72), size=(0.3, 0.16, 0.24), yaw=0.2, solid=False)

    # ---- the carpet (along the counter, in front of the main tent's opening): its texture runs along z
    rx0, rx1, rz0, rz1 = RUG
    add_cube(shell, "rug", ((rx0 + rx1) / 2, 0.015, (rz0 + rz1) / 2), EYE, (rx1 - rx0, 0.03, rz1 - rz0), {"all": "cloth", "+2": "pd_rug", "-2": None},
             stretch=True, u_dir=Z, v_dir=-X)

    # ---- inside the main tent: back shelves and their goods, a chest, crates, the grain sack, a crate under a cloth
    levels = ml.shelf_unit(shell, "shelves", XL + 0.42, XR - 0.42, ZB + 0.18, ZB + 0.68, levels=(0.55, 1.15, 1.75, 2.35), h=2.68,
                           back=True, uprights=5, detail=det)
    pots = ("blue", "purple", "pink", "green", "cyan", "purple", "blue", "orange", "pink", "green")
    for j, (x0, x1, yy, zf, zb) in enumerate(levels):
        zc = (zf + zb) / 2
        if j in (1, 2):
            n = 12
            for i in range(n):
                if j == 2 and 6 <= i <= 8:
                    continue
                xx = x0 + 0.14 + (x1 - x0 - 0.28) * i / (n - 1)
                ml.bottle(det, "pot_%d_%d" % (j, i), (xx, yy, zc + 0.05 * ((i % 2) - 0.5)), pots[(i + 3 * j) % len(pots)], r=0.075 + 0.02 * (i % 3 == 0),
                          h=0.19 + 0.05 * (i % 2), shape="round" if i % 3 else "tall", neck_h=0.07)
            if j == 2:
                for i, dx in enumerate((0.0, 0.32)):
                    pd.scroll(det, "shelf_roll_%d" % i, (x0 + 2.3 + dx, yy + 0.08, zc), length=0.36, r=0.075, yaw=math.pi / 2, region="cloth_beige")
        elif j == 0:
            for i, (dx, reg) in enumerate(((0.25, "cloth_beige"), (0.5, "cloth_red"), (0.75, "cloth_beige"), (1.0, "cloth_beige"))):
                pd.scroll(det, "roll_%d" % i, (x0 + dx, yy + 0.09, zc), length=0.42, r=0.085, yaw=math.pi / 2, region=reg)
            ml.sack(det, "low_sack_0", (x1 - 0.45, yy, zc), s=0.34, yaw=-0.2)
            ml.sack(det, "low_sack_1", (x1 - 0.85, yy, zc), s=0.3, yaw=0.3)
            ml.crate(det, "low_box", (x0 + 1.75, yy, zc), size=(0.48, 0.32, 0.36), solid=False)
        else:
            xx = x0 + 0.1
            for i in range(14):
                bw = 0.07 + 0.025 * rng.random()
                bh = 0.24 + 0.1 * rng.random()
                reg = ("cloth_red", "leather", "cloth_dark", "cloth_red", "leather_dark", "cloth_blue")[i % 6]
                box(det, "book_%d" % i, (xx, yy, zc - 0.1), (xx + bw, yy + bh, zc + 0.12), {"all": reg, "+2": "white", "-2": "white"})
                xx += bw + 0.012
            decor.block("furnish:book_pile", x1 - 1.0, yy, zc, facing="front", scale=0.8, fallback="leather", solid=False)
            pd.scroll(det, "shelf_scroll", (x1 - 0.3, yy + 0.07, zc), length=0.36, r=0.06, yaw=math.pi / 2)
    pd.chest(shell, det, "chest", (-2.05, 0.0, ZB + 1.12), w=0.84, d=0.56, h=0.6)
    collide((-2.47, 0.0, ZB + 0.84, -1.63, 0.6, ZB + 1.4))
    decor.block("furnish:spruce_crate", -3.3, 0.0, ZB + 1.25, facing="front", scale=0.8, alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "in_crate_top", (-3.3, 0.8, ZB + 1.25), size=0.5, yaw=0.25, content="produce", solid=False)
    pd.grain_sack(shell, det, "grain_sack", (-3.3, 0.0, 1.62), r=0.36, h=0.6, yaw=0.2)
    collide((-3.66, 0.0, 1.26, -2.94, 0.6, 1.98))
    ml.crate(shell, "cloth_crate", (-3.5, 0.0, 0.42), size=(0.62, 0.55, 0.55), yaw=0.0, solid=True)
    box(shell, "cloth_crate_cloth", (-3.83, 0.55, 0.13), (-3.17, 0.57, 0.71), {"all": "cloth_red"}, stretch=True)
    ml.plate(shell, "cloth_crate_flap", (-3.5, 0.37, 0.72), 0.66, 0.38, "pd_runner", normal=(0, 0, 1), th=0.01, edge="cloth_red")
    ml.crate(shell, "greens_crate", (-2.6, 0.0, 0.55), size=(0.5, 0.36, 0.42), yaw=-0.15, content="pd_greens", solid=True)

    # ---- outside the left wall: the big crate with cloth rolls, produce crates, a rice sack
    bcx, bcz, bs = -5.12, -0.5, 1.08
    ml.crate(shell, "big_crate", (bcx, 0.0, bcz), size=bs, yaw=0.08, solid=True)
    for j, s_ in enumerate((-1, 1)):
        add_cube(det, "big_crate_band_%d" % j, (bcx + s_ * 0.34, bs / 2, bcz), ry(0.08), (0.07, bs + 0.02, bs + 0.02), "iron")
        add_cube(det, "big_crate_hband_%d" % j, (bcx, bs / 2 + s_ * 0.3, bcz), ry(0.08), (bs + 0.02, 0.07, bs + 0.02), "iron")
    for i, (dz, reg) in enumerate(((-0.32, "cloth_beige"), (0.0, "pd_burlap"), (0.32, "cloth_beige"))):
        pd.scroll(det, "big_roll_%d" % i, (bcx, bs + 0.12, bcz + dz), length=0.92, r=0.13, yaw=0.08, region=reg)
    pd.scroll(det, "big_roll_top", (bcx, bs + 0.33, bcz - 0.16), length=0.8, r=0.12, yaw=0.0, region="cloth_beige")
    ml.rope(det, "big_crate_rope", (bcx - 0.4, bs + 0.4, bcz + 0.15), (bcx + 0.4, bs + 0.4, bcz + 0.25), d=0.06, sag=0.15, segs=3)
    decor.block("farmersdelight:tomato_crate", -4.92, 0.0, 0.7, facing="front", scale=0.8, fallback="pd_fb_red")
    decor.block("farmersdelight:cabbage_crate", -5.42, 0.0, 1.45, facing="front", scale=0.66, fallback="pd_fb_green")
    decor.block("farmersdelight:rice_bag", -5.2, 0.0, -1.55, facing="front", scale=0.72, fallback="pd_burlap")

    # ---- under the awning, at the front: a crate and a canvas bale at the left post, the flower box, a small crate
    ml.crate(shell, "front_crate", (-0.95, 0.0, 4.82), size=(0.62, 0.55, 0.55), yaw=0.12, solid=True)
    for j, s_ in enumerate((-1, 1)):
        add_cube(det, "front_crate_band_%d" % j, (-0.95 + s_ * 0.2, 0.28, 4.82), ry(0.12), (0.05, 0.57, 0.57), "iron")
    ml.rbox(shell, "bale", (-0.15, 0.0, 4.95), (0.6, 0.62, 0.5), -0.08, {"all": "pd_burlap", "+2": "cloth_beige"}, solid=True, stretch=True)
    for j, s_ in enumerate((-1, 1)):
        add_cube(det, "bale_band_%d" % j, (-0.15 + s_ * 0.18, 0.31, 4.95), ry(-0.08), (0.05, 0.64, 0.52), "iron")
    pd.flower_box(shell, det, "flower_box", (1.5, 0.0, 4.18), w=1.05, d=0.5, h=0.55, flowers="pd_flowers", fh=0.9)
    ml.crate(shell, "small_crate", (2.7, 0.0, 4.82), size=(0.42, 0.34, 0.38), yaw=0.3, solid=True)
    return root


def item_icon(path):
    """16x16: the striped main tent with its finials and dark opening on the left, the red awning with gold dags on
    its post on the right, a scales banner on the closed left part."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, cream, gold, dark = PAL.red, PAL.cream, PAL.gold, (40, 26, 16)
    wood, wood_d = (128, 82, 42), (84, 52, 26)

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            p[x, y] = tuple(c) + (255,)
    for y in range(1, 7):          # the main roof: a trapezoid from the short ridge down to the eaves, in stripes
        x0, x1 = 3 - (y - 1) * 3 // 5, 7 + (y - 1) * 3 // 5
        for x in range(x0, x1 + 1):
            put(x, y, red if ((x - 2) // 2) % 2 == 0 else cream)
    for x in (3, 7):               # the ridge posts' finials
        put(x, 0, gold)
    for x in range(0, 11):         # the valance: cream with red dags
        put(x, 7, cream)
        if x % 3 == 1:
            put(x, 8, red)
    for y in range(8, 15):         # walls: the closed left part with the banner, the dark opening
        for x in range(0, 3):
            put(x, y, cream)
        for x in range(3, 9):
            put(x, y, dark)
    for y in range(9, 12):
        put(1, y, red)
    put(1, 10, gold)
    for y in range(7, 16):         # the front posts
        put(2, y, wood)
        put(9, y, wood_d)
    put(2, 6, gold)
    put(9, 6, gold)
    for x in range(9, 16):         # the awning sloping out to the right, gold dags under it
        y = 6 + (x - 9) // 3
        put(x, y, red)
        put(x, y + 1, red if x % 2 else cream)
        if x % 2 == 0:
            put(x, y + 2, gold)
    for y in range(9, 16):         # its front post and finial
        put(14, y, wood)
    put(14, 7, gold)
    for x in range(10, 14):        # the counter under it, with its red runner
        put(x, 12, (170, 116, 60))
        put(x, 13, wood_d)
        put(x, 14, wood_d)
    put(11, 13, red)
    put(12, 13, red)
    for x in range(3, 9):          # the red carpet in front of the opening
        put(x, 15, _scale(red, 0.85))
    put(5, 11, (240, 200, 80))     # a lantern in the opening
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


SHIFT = None   # (dx, dz) applied to the design coordinates (set by main)


def main():
    global SHIFT
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    add_regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    SHIFT = pd.centre_offsets(root, decor)
    pd.shift_all(root, decor, *SHIFT)
    print("shift %.2f %.2f -> NPC place x %.2f..%.2f z %.2f..%.2f" % (SHIFT[0], SHIFT[1], NPC[0] + SHIFT[0], NPC[0] + SHIFT[0] + 1,
                                                                      NPC[1] + SHIFT[1], NPC[1] + SHIFT[1] + 1))
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)


if __name__ == "__main__":
    main()
