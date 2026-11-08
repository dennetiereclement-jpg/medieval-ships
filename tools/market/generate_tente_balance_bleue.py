#!/usr/bin/env python3
"""tente_balance_bleue — Tente bleue à la balance / Blue Scales Tent (1.26.0, market tents group B; reference:
scratchpad/ref2/tente_balance_bleue_ref.png, picture 130).

A blue and cream money-changer's tent of Lion Port, one block (TentType group "tents"), about 10 blocks wide with its left
awning, its pegs and the gallows sign, 6.8 deep, the ridge posts at about 6.5:

  - the main tent: a SHORT RIDGE carried by two tall squared RIDGE POSTS with stepped caps (a rope wrapped round the
    ridge pole), a hipped roof falling steeply from the ridge and flaring out towards the eaves, wide blue and cream
    stripes, a blue and cream valance with gold-edged dags; a blue SCALES BANNER with a gold border and castellated
    bottom lies on the front slope from the ridge; twisted ROPES run down the hips to the front posts;
  - big squared posts with iron bands and stepped caps; the front-right one rises as a GALLOWS: a beam with a knee brace
    carries a blue shield SIGN with the gold scales on two rings; ropes run to pegged stakes;
  - a lower LEFT AWNING, striped, with a dagged valance and a cream cloth hanging at its outer corner, two capped posts
    and guy ropes to pegged stakes: crates with sacks, a lantern standing on a crate, hanging herbs;
  - the COUNTER at the front under a blue cloth with gold borders and stars, the hanging pentagon panel with the gold
    scales, books, a scroll, a pot of wheat and an iron-banded chest on it; the merchant's place behind it, a narrow
    shelf of bottles at the back, two lanterns hanging under the front eave, deep blue canvas walls;
  - in front: a big tied cream sack, a crate of red apples, a planter crate of greens and wheat, the blue RUG with a gold
    key pattern border and a gold diamond medallion.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in between the
counter's right end and the right post (the gallows). No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_balance_bleue.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_balance_bleue.json, models/entity + blockbench/tente_balance_bleue.bbmodel,
textures/entity/tente_balance_bleue.png, textures/item/tente_balance_bleue.png, interiors/tente_balance_bleue_decor.json.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_b as pb  # noqa: E402

ml, p1, wb = pb.ml, pb.p1, pb.wb
NAME = "tente_balance_bleue"
v3, norm, add_cube, beam, loft, Bone = pb.v3, pb.norm, pb.add_cube, pb.beam, pb.loft, pb.Bone
EYE, UP, X, Z = pb.EYE, pb.UP, pb.X, pb.Z
ry, box, collide = pb.ry, pb.box, pb.collide
NAVY, CREAM, GOLD = pb.NAVY, pb.CREAM, pb.GOLD

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 2.6, 2.3             # main posts
EAVE = 3.42                   # eave beams (top)
RW, RD, RY = 2.95, 2.65, 3.62   # roof eave corners
RIDGE_X, RIDGE_Z, RIDGE_Y = 1.65, -1.05, 5.45
POST_TOP = 4.05
GALLOWS_TOP = 5.85
AX = -4.7                     # left awning outer posts
AZ0, AZ1 = -1.2, HD
AY_IN, AY_OUT = 3.38, 2.72
COUNTER = (-1.4, 1.5, 1.45, 2.05)
COUNTER_H = 1.0
NPC_SPOT = (0.0, 0.38)        # (x0, z0) of the merchant's free 1 x 1 x 2.2 place
SHELF = (-0.9, 0.9, -2.25, -1.85)


def paint_wall(img):
    """The canvas walls: deep blue cloth with soft vertical folds and a gold hem (the picture's dark blue sides; the
    stripes stay on the roof)."""
    rng = random.Random(13001)
    pb.stripes(img, 6, (pb._scale(NAVY, 0.8), NAVY), rng, fold=0.2)
    px = img.load()
    w, h = img.size
    for y in range(h - 3, h):
        for x in range(w):
            px[x, y] = ml._jitter(GOLD if y > h - 3 else pb.GOLD_D, rng, 8) + (255,)


def paint_cap(img):
    """The stepped post caps' faces: warm wood with a darker inset square frame."""
    rng = random.Random(13002)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), pb.WOOD, pb.WOOD_D, h, rng, joints=False, knots=0.0, grain=0.12, shade=0.08)
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e in (3, 4):
                px[x, y] = ml._jitter(pb.WOOD_D, rng, 5) + (255,)
            elif e == 0:
                px[x, y] = ml._jitter(ml._scale(pb.WOOD, 1.15), rng, 5) + (255,)


def paint_cloth_front(img):
    """The counter's blue cloth hanging along its front: gold border on the sides and the bottom, gold stars."""
    rng = random.Random(13003)
    w, h = img.size
    pb.weave(img, NAVY, rng)
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, w - 1 - x, h - 1 - y)
            if e < 2:
                px[x, y] = ml._jitter(GOLD, rng, 8) + (255,)
            elif e == 2:
                px[x, y] = ml._jitter(pb.NAVY_D, rng, 4) + (255,)
    for cx in range(10, w - 6, 18):
        cy = h // 2 + (4 if (cx // 18) % 2 else -4)
        for (i, j) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            px[cx + i, cy + j] = ml._jitter(GOLD, rng, 8) + (255,)


def regions(atlas):
    own = [
        ("s_roof", 32 * 7, 80, pb.paint_roof(7, 13004, fold=0.16)),
        ("s_rug", 112, 80, pb.paint_rug(13005, "meander")),
        ("s_banner", 48, 80, pb.paint_banner("scales", 13006, bottom="dags", start=0.8)),
        ("s_roof3", 32 * 3, 80, pb.paint_roof(3, 13007, fold=0.16, offset=1)),
        ("s_sign", 48, 56, pb.paint_sign_board("scales", 13008)),
        ("s_runner", 56, 48, pb.paint_runner("scales", 13009, star_dots=True)),
        ("s_wall", 96, 48, paint_wall),
        ("s_awning", 24 * 6, 48, pb.paint_roof(6, 13010, fold=0.12)),
        ("s_cloth", 96, 24, paint_cloth_front),
        ("s_val", 224, 28, pb.paint_valance(7, 13011, cols=(CREAM, NAVY), shape="pent", band=0.4)),
        ("s_cap", 16, 16, paint_cap),
        "b_post", "b_band", "b_chest", "b_sack", "b_wheat", "b_drape",
    ]
    pb.add_regions(atlas, own, m1=["herbs", "sprout", "potion_green", "potion_purple", "glass", "cork", "jar", "jar_top", "linen", "book_red",
                                   "book_brown", "book_blue", "book_top", "parchment"])


def cap_post(shell, det, name, x, z, top, d=0.46, bands=(), collide_to=None):
    """A squared warm-wood post with iron bands and the picture's stepped cap (a big block with an inset square frame,
    a smaller block on it)."""
    pb.sq_post(shell, det, name, x, z, top, d=d, bands=bands, cap=None, region="b_post", collide_to=collide_to)
    c = d / 2 + 0.11
    box(shell, name + "_cap", (x - c, top, z - c), (x + c, top + 0.42, z + c), {"all": "s_cap", "+2": "end_grain"}, stretch=True)
    box(shell, name + "_cap_top", (x - c + 0.1, top + 0.42, z - c + 0.1), (x + c - 0.1, top + 0.6, z + c - 0.1), {"all": "wood", "+2": "end_grain"})
    box(det, name + "_collar", (x - d / 2 - 0.04, top - 0.12, z - d / 2 - 0.04), (x + d / 2 + 0.04, top, z + d / 2 + 0.04), "wood_dark")


# ---------------------------------------------------------------- the build
def build(decor):
    rng = random.Random(130)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)

    # ---- posts: main four (the front-right one is the gallows), the two ridge posts, the awning posts
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]
    for k, (x, z) in enumerate(corners):
        if k == 1:
            cap_post(shell, det, "gallows", x, z, GALLOWS_TOP, d=0.46, bands=(0.35, 1.7, 3.1), collide_to=EAVE)
        else:
            cap_post(shell, det, "post_%d" % k, x, z, POST_TOP, d=0.46, bands=(0.35, 1.7, 3.1), collide_to=EAVE)
    for k, sx in enumerate((-1, 1)):
        x = sx * RIDGE_X
        cap_post(shell, det, "ridge_post_%d" % k, x, RIDGE_Z, RIDGE_Y + 0.25, d=0.36, bands=(1.6,), collide_to=EAVE)
    beam(shell, "ridge_pole", (-RIDGE_X - 0.25, RIDGE_Y - 0.08, RIDGE_Z), (RIDGE_X + 0.25, RIDGE_Y - 0.08, RIDGE_Z), 0.22,
         {"all": "b_post", "+1": "end_grain", "-1": "end_grain"})
    for i in range(7):   # the rope wrapped round the ridge pole
        x = -RIDGE_X + 0.15 + i * (2 * RIDGE_X - 0.3) / 6
        add_cube(det, "ridge_wrap_%d" % i, (x, RIDGE_Y - 0.08, RIDGE_Z), rz_(0.5), (0.07, 0.3, 0.3), "rope")
    by = EAVE - 0.16
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.3, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26,
             extend=0.16)
    for k, (p, q) in enumerate((((-HW + 0.2, EAVE - 1.1, HD), (-HW + 0.9, by - 0.12, HD)), ((HW - 0.2, EAVE - 1.1, HD), (HW - 0.9, by - 0.12, HD)))):
        beam(shell, "brace_%d" % k, p, q, 0.15, "wood_dark", extend=0.05)
    # the gallows: beam, knee brace, end block, the shield sign on two rings
    gx, gz = corners[1]
    gy = GALLOWS_TOP - 0.3
    beam(shell, "gallows_beam", (gx - 0.2, gy, gz), (4.35, gy, gz), 0.3, {"all": "b_post", "+1": "end_grain", "-1": "end_grain"}, width=0.3)
    beam(shell, "gallows_brace", (gx + 0.22, gy - 1.0, gz), (gx + 0.95, gy - 0.15, gz), 0.17, "b_post")
    box(shell, "gallows_end", (4.05, gy - 0.22, gz - 0.2), (4.45, gy + 0.22, gz + 0.2), {"all": "s_cap", "+2": "end_grain"}, stretch=True)
    pb.band(det, "gallows_band", gx, gz, 0.26, gy - 0.5, 0.13)
    sx0 = 3.55
    for k, dx in enumerate((-0.32, 0.32)):
        add_cube(det, "sign_ring_%d" % k, (sx0 + dx, gy - 0.32, gz), EYE, (0.06, 0.24, 0.12), "iron")
        add_cube(det, "sign_hook_%d" % k, (sx0 + dx, gy - 0.18, gz), EYE, (0.1, 0.06, 0.16), "iron")
    box(shell, "sign", (sx0 - 0.5, gy - 1.72, gz - 0.04), (sx0 + 0.5, gy - 0.44, gz + 0.04), {"all": None, "+3": "s_sign", "-3": "s_sign"},
        stretch=True, u_dir=X, v_dir=-UP)

    # ---- the hipped roof with the short ridge
    a0, a1 = v3(-RIDGE_X, RIDGE_Y, RIDGE_Z), v3(RIDGE_X, RIDGE_Y, RIDGE_Z)
    rc = [v3(-RW, RY, RD), v3(RW, RY, RD), v3(RW, RY, -RD), v3(-RW, RY, -RD)]
    tops = [(a0, a1), (a1, a1), (a1, a0), (a0, a0)]
    outs = [Z, X, -Z, -X]
    edges = []
    for k in range(4):
        long_side = k in (0, 2)
        P = pb.hip_side(shell, "roof_%d" % k, tops[k][0], tops[k][1], rc[k], rc[(k + 1) % 4], "s_roof" if long_side else "s_roof3",
                        nx=7 if long_side else 3, ny=8, droop=0.12, a=0.22, edge_sag=0.1, folds=0.04)
        edges.append(P)
        pb.valance_curve(shell, "valance_%d" % k, lambda s, P=P: P(s, 1.0), outs[k], h=0.44, region="s_val", nx=4 if long_side else 2)
    # the scales banner lying on the front slope from the ridge
    P0 = edges[0]

    def B(s, t):
        u = 0.5 + (0.55 + (-0.47 + 0.94 * s)) / (2 * RW) * 0.0
        xs = 0.55 - 0.47 + 0.94 * s
        # find the roof point under xs at the slope fraction tt: interpolate along the front side
        tt = 0.02 + 0.6 * t
        top_s = (xs + RIDGE_X) / (2 * RIDGE_X)
        eave_s = (xs + RW) / (2 * RW)
        ss = top_s * (1 - tt) + eave_s * tt
        p = P0(min(1.0, max(0.0, ss)), tt)
        return v3(xs, p[1] + 0.06, p[2] + 0.05)
    loft(shell, "roof_banner", B, 1, 4, "s_banner", th=0.02, u_hint=X)
    box(det, "roof_banner_rod", (0.55 - 0.55, RIDGE_Y + 0.02, RIDGE_Z + 0.12), (0.55 + 0.55, RIDGE_Y + 0.12, RIDGE_Z + 0.24), "gold")
    # ropes down the hips from the ridge post tops to the front post tops
    for k, sx in enumerate((-1, 1)):
        pb.swag(det, "hip_rope_%d" % k, (sx * RIDGE_X, RIDGE_Y + 0.1, RIDGE_Z + 0.12), (sx * (HW + 0.05), POST_TOP - 0.1, HD + 0.05), sag=0.1, d=0.11,
                segs=5, knots=True)
    pb.swag(det, "ridge_rope_l", (-RIDGE_X, RIDGE_Y + 0.1, RIDGE_Z), (AX, AY_OUT + 0.3, AZ0), sag=0.15, d=0.1, segs=5, knots=False)
    pb.swag(det, "front_rope_l", (-HW - 0.05, POST_TOP - 0.15, HD + 0.05), (AX, AY_OUT + 0.3, AZ1 + 0.05), sag=0.2, d=0.1, segs=4, knots=True)

    # ---- the left awning: striped roof, valances, a cream cloth at its outer corner, capped posts, guy ropes
    for k, z in enumerate((AZ1, AZ0)):
        cap_post(shell, det, "apost_%d" % k, AX, z, AY_OUT + 0.15, d=0.36, bands=(0.3, 1.9), collide_to=AY_OUT)
        beam(shell, "aw_beam_%d" % k, (-HW, AY_IN - 0.18, z), (AX, AY_OUT - 0.18, z), 0.22, "beam", extend=0.12)
    beam(shell, "aw_side", (AX, AY_OUT - 0.1, AZ0), (AX, AY_OUT - 0.1, AZ1), 0.22, "beam", extend=0.15)
    xo = AX - 0.3

    def A(s, t):
        z = (AZ0 - 0.25) + (AZ1 - AZ0 + 0.6) * (1 - s)
        x = -HW - 0.02 + (xo + HW + 0.02) * t
        frac = ((1 - s) * 6) % 1.0
        y = AY_IN + 0.04 - (AY_IN - AY_OUT + 0.08) * t - 0.1 * math.sin(math.pi * t) - 0.04 * math.sin(math.pi * frac)
        return v3(x, y, z)
    loft(shell, "awning", A, 6, 3, "s_awning", th=0.035, overlap=0.03)
    yo = A(0, 1)[1]
    pb.valance(shell, "aw_val_front", (-HW - 0.05, AY_IN - 0.02, AZ1 + 0.35), (xo, yo - 0.02, AZ1 + 0.35), Z, h=0.44, region="s_val", nx=2)
    pb.valance(shell, "aw_val_side", (xo - 0.02, yo - 0.02, AZ1 + 0.35), (xo - 0.02, yo - 0.02, AZ0 - 0.25), -X, h=0.44, region="s_val", nx=2)
    pb.wall(shell, "aw_cloth", (xo + 0.05, 0, AZ1 + 0.3), (xo + 0.05, 0, AZ1 - 0.75), 0.6, yo - 0.3, -X, "b_drape", nx=3, fold=0.08)
    pb.wall(shell, "aw_wall", (AX, 0, AZ0 - 0.05), (-HW, 0, AZ0 - 0.05), 0.0, AY_OUT - 0.25, -Z, "s_wall", nx=3)
    collide((AX, 0.0, AZ0 - 0.11, -HW, AY_OUT - 0.25, AZ0 + 0.01))
    for k, (top, peg) in enumerate((((AX - 0.1, AY_OUT + 0.4, AZ1), (-5.45, 0.0, 3.05)), ((AX - 0.1, AY_OUT + 0.4, AZ0), (-5.5, 0.0, -1.75)),
                                    ((HW + 0.15, POST_TOP - 0.2, HD), (3.95, 0.0, 3.1)))):
        pb.guy_stake(shell, det, "stake_%d" % k, peg[0], peg[2], h=0.5)
        collide((peg[0] - 0.1, 0.0, peg[2] - 0.1, peg[0] + 0.1, 0.5, peg[2] + 0.1))
        ml.rope(det, "guy_%d" % k, top, (peg[0], 0.45, peg[2]), d=0.06, sag=0.05, segs=2)
    # the main tent's walls: striped back, blue right side, the left side behind the awning
    pb.wall(shell, "back_wall", (HW, 0, -HD - 0.06), (-HW, 0, -HD - 0.06), 0.0, by - 0.1, -Z, "s_wall", nx=6)
    collide((-HW, 0.0, -HD - 0.12, HW, by - 0.1, -HD))
    pb.wall(shell, "right_wall", (HW + 0.04, 0, HD - 0.35), (HW + 0.04, 0, -HD), 0.0, by - 0.1, X, "s_wall", nx=5)
    collide((HW - 0.02, 0.0, -HD, HW + 0.1, by - 0.1, HD - 0.35))
    pb.wall(shell, "left_wall", (-HW - 0.04, 0, -HD), (-HW - 0.04, 0, AZ0), 0.0, by - 0.1, -X, "s_wall", nx=1)
    collide((-HW - 0.1, 0.0, -HD, -HW + 0.02, by - 0.1, AZ0))

    # ---- lanterns under the front eave, herbs hanging at the left post
    for k, x in enumerate((-1.2, 1.75)):
        ml.lantern(shell, "lamp_%d" % k, (x, 2.72, HD - 0.25), size=0.38, metal="iron", chain_to=(x, by - 0.12, HD - 0.25))
    ml.hanging_bunch(det, "herbs_0", (-HW - 0.35, AY_IN - 0.35, AZ1 - 0.05), kind="herbs", length=0.62, width=0.4)

    # ---- the narrow back shelf of bottles, a barrel and a crate at the back
    lv = ml.shelf_unit(shell, "shelf", SHELF[0], SHELF[1], SHELF[2], SHELF[3], levels=(0.95, 1.55, 2.15), h=2.5, back=True, uprights=2, detail=det)
    for i, (xa, xb, yy, zf, zb) in enumerate(lv):
        zc = (zf + zb) / 2
        for j in range(5):
            xx = xa + 0.14 + j * (xb - xa - 0.28) / 4
            c = ("green", "purple", "purple", "green", "green")[(i + j) % 5]
            if i == 2 and j % 2:
                wb.jar(det, "jar_%d_%d" % (i, j), (xx, yy, zc), r=0.08, h=0.2)
            else:
                ml.bottle(det, "bot_%d_%d" % (i, j), (xx, yy, zc), c, r=0.065, h=0.24, shape="tall", glow=(c == "purple"))
    decor.block("landsoficaria:cypress_barrel", -1.75, 0.0, -1.65, facing="front", alt="minecraft:barrel", fallback="barrel")
    ml.crate(shell, "back_crate", (1.7, 0.0, -1.7), size=0.75, yaw=0.15, solid=True)
    ml.sack(det, "back_sack", (1.7, 0.75, -1.7), s=0.4, yaw=0.3, region="b_sack")

    # ---- the counter: blue cloth with gold borders and stars, the pentagon scales panel, its goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    box(shell, "cloth_top", (cx0 + 0.25, y, cz0 - 0.02), (cx1 - 0.15, y + 0.015, cz1 + 0.05), {"all": "cloth_blue"}, stretch=True, u_dir=X)
    ml.plate(shell, "cloth_front", ((cx0 + cx1) / 2 + 0.05, y - 0.26, cz1 + 0.06), cx1 - cx0 - 0.4, 0.54, "s_cloth", normal=(0, 0, 1), th=0.012)
    ml.plate(shell, "runner", (0.35, y - 0.45, cz1 + 0.075), 1.0, 0.86, "s_runner", normal=(0, 0, 1), th=0.012)
    zc = (cz0 + cz1) / 2
    wb.book_stack(det, "books_l", (cx0 + 0.25, y, zc), 4, rng, w=0.34, d=0.26, th=0.08, colors=("brown", "red", "brown", "blue"))
    pb.wheat_bundle(det, "wheat_pot", (cx0 + 0.75, y + 0.18, cz0 + 0.12), h=0.5, w=0.36)
    ml.octo(shell, "wheat_bucket", (cx0 + 0.75, y, cz0 + 0.12), 0.13, 0.2, {"all": "wood", "+2": "end_grain"})
    pb.scroll(det, "scroll_0", (cx0 + 1.25, y + 0.07, zc + 0.08), length=0.42, r=0.06, yaw=0.25)
    pb.scroll(det, "scroll_1", (cx0 + 1.35, y + 0.07, zc - 0.12), length=0.34, r=0.05, yaw=-0.3)
    pb.chest(shell, det, "counter_chest", (cx1 - 0.55, y, zc), w=0.6, d=0.42, h=0.42, solid=False)
    wb.book_stack(det, "books_r", (cx1 - 0.15, y, zc + 0.05), 2, rng, w=0.3, d=0.24, th=0.08, colors=("red", "brown"))

    # ---- the rug in front of the counter
    ml.rug(shell, "rug", -0.55, 2.35, 2.3, 3.85, y=0.0, region="s_rug")

    # ---- the left front: crates with sacks, a lantern on a crate, the big sack, the apple crate
    decor.block("furnish:spruce_crate", -3.95, 0.0, 1.5, facing="front", scale=0.9, alt="minecraft:barrel", fallback="crate")
    ml.sack(det, "crate_sack_0", (-4.15, 0.9, 1.45), s=0.42, yaw=0.3, region="b_sack")
    decor.block("farmersdelight:rice_bag", -3.72, 0.9, 1.55, facing="front", scale=0.5, fallback="sack", solid=False)
    ml.crate(shell, "lamp_crate", (-3.1, 0.0, 2.2), size=(0.72, 0.95, 0.66), yaw=0.05, solid=True)
    ml.lantern(shell, "lamp_crate_lantern", (-3.1, 0.95 + 0.25, 2.2), size=0.34, metal="iron")
    ml.crate(shell, "back_aw_crate", (-3.9, 0.0, 0.1), size=0.8, yaw=-0.1, solid=True)
    ml.sack(det, "back_aw_sack", (-3.9, 0.8, 0.1), s=0.45, yaw=0.5, region="b_sack")
    pb.big_sack(shell, det, "big_sack", (-2.8, 0.0, 3.0), yaw=0.25, w=0.68, h=0.95, solid=True)
    pb.produce_crate(shell, "apples", (-1.85, 0.0, 2.95), size=(0.66, 0.42, 0.55), content="apples", solid=True)
    for k, (dx, dz) in enumerate(((-0.14, -0.05), (0.12, 0.06), (0.0, 0.14), (0.18, -0.12))):
        add_cube(det, "apple_%d" % k, (-1.85 + dx, 0.45, 2.95 + dz), ry(0.4 * k), (0.15, 0.13, 0.15), "cloth_red")

    # ---- the right front: a planter crate of greens and wheat
    decor.block("farmersdelight:cabbage_crate", 3.25, 0.0, 2.6, facing="front", scale=0.72, fallback="produce")
    pb.wheat_bundle(det, "wheat_r", (3.4, 0.7, 2.55), h=0.55, w=0.4)
    wb.crossed(det, "greens_r", (3.1, 0.88, 2.65), 0.42, 0.36, "sprout")
    return root


def rz_(a):
    return ml.rz(a)


def item_icon(path):
    def extra(p):
        for x in (13, 14):
            p[x, 2] = (150, 98, 52, 255)
        p[14, 3] = pb.NAVY + (255,)
        p[14, 4] = pb.GOLD + (255,)
    pb.stall_icon(path, roof="ridge", extra=extra)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="blue")
    regions(atlas)
    decor = ml.Decor()
    root = build(decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)
    print("atlas", atlas.size)


if __name__ == "__main__":
    main()
