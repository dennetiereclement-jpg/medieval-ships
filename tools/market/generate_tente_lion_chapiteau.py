#!/usr/bin/env python3
"""tente_lion_chapiteau — Chapiteau royal au lion / Royal Lion Marquee (1.26.0, market tents group B; reference:
scratchpad/ref2/tente_lion_chapiteau_ref.png, picture 109).

A rounded royal-blue marquee of Lion Port, one block (TentType group "tents"), about 10 blocks wide with its left wing,
its stakes and the banner arm, 6.7 deep, the gold finial at about 7.5:

  - the main marquee: a ROUNDED roof in two tiers (a squircle plan): the lower tier curves up from the eave to a raised
    crown, a blue and gold crenellated band round the crown, the steep upper tier and a stacked GOLD FINIAL; wide blue
    and cream stripes edged with thin gold seams, a cream hem above the valance; a blue LION PANEL with a gold border
    and a pointed bottom lies on the front of the roof; the front valance is a blue band with GOLD CRENELS, the rest of
    the eave a blue / cream valance with gold-edged dags;
  - dark wooden posts with gold bands; the front-right post rises as a tall separate BANNER POST with a cross-arm and a
    brace, carrying a big blue LION BANNER with a gold tassel; three glowing lanterns hang under the front valance, a gold
    rope swag below it;
  - a lower LEFT WING with a striped roof sloping out, gold-capped posts, a dagged valance and BLUE CURTAINS sprinkled
    with gold diamonds (closed on its left, open on the right on a shelf of jars with hanging herbs); gold-banded stakes
    and ropes in front and at the right;
  - inside: dark plank back wall with a blue curtain gathered by a gold tie in the middle, potion shelves (pink, purple,
    cyan, glowing) and jar shelves, the COUNTER under a cream cloth with dags and the blue lion runner, an ARMILLARY
    SPHERE, books, a scroll, a standing lantern and gold bars on it, a small chest of red gems and a crate of gold in
    front of it, the blue RUG with the gold border and the faded lion;
  - outside: a planter of purple flowers, the big iron-banded CHEST, stacked crates, cream bales and sacks.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in between the
front-left post and the counter's left end. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_lion_chapiteau.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_lion_chapiteau.json, models/entity + blockbench/tente_lion_chapiteau.bbmodel,
textures/entity/tente_lion_chapiteau.png, textures/item/tente_lion_chapiteau.png, interiors/tente_lion_chapiteau_decor.json.
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
NAME = "tente_lion_chapiteau"
v3, norm, add_cube, beam, loft, Bone = pb.v3, pb.norm, pb.add_cube, pb.beam, pb.loft, pb.Bone
EYE, UP, X, Z = pb.EYE, pb.UP, pb.X, pb.Z
ry, box, collide = pb.ry, pb.box, pb.collide
NAVY, CREAM, GOLD = pb.NAVY, pb.CREAM, pb.GOLD

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 2.5, 2.3             # main posts
EAVE_Y, EHX, EHZ, EN = 3.55, 3.0, 2.75, 5.0     # the eave ring (squircle exponent EN)
CROWN_Y, CHX, CHZ = 5.3, 0.82, 0.68              # the crown ring (top of the lower tier)
DRUM_H = 0.26
APEX = 5.95
BEAM_Y = 3.35
WX = -4.9                     # the left wing's outer posts
WZ0, WZ1 = -1.5, HD
WY_IN, WY_OUT = 3.78, 2.82
COUNTER = (-1.3, 2.0, 0.95, 1.55)
COUNTER_H = 1.05
NPC_SPOT = (0.0, -0.12)       # (x0, z0) of the merchant's free 1 x 1 x 2.2 place
BANNER_TOP = 5.95


def zfront(x):
    """z of the eave ring's front edge at x."""
    return EHZ * max(0.0, 1.0 - abs(x / EHX) ** EN) ** (1.0 / EN)


def paint_drum(img):
    rng = random.Random(10901)
    pb.weave(img, NAVY, rng)
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if y < 2 or y >= h - 2:
                px[x, y] = ml._jitter(GOLD, rng, 8) + (255,)
            elif 4 <= y < h - 4 and (x % 10) in (3, 4, 5, 6):
                px[x, y] = ml._jitter(GOLD if y % 4 < 2 or (x % 10) in (4, 5) else pb.GOLD_D, rng, 8) + (255,)


def paint_planks(img):
    rng = random.Random(10902)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), pb.WOOD_DARK, pb.WOOD_DARK_D, max(4, w // 8), rng, joints=True, knots=0.06, grain=0.14, shade=0.12)


def regions(atlas):
    own = [
        ("c_roof", 16 * 12, 80, pb.paint_roof(12, 10903, seam=GOLD, hem=7, hem_col=CREAM, fold=0.14)),
        ("c_rug", 128, 96, pb.paint_rug(10904, "lion", faded=0.4)),
        ("c_banner", 40, 96, pb.paint_banner("lion", 10905, start=0.8, tassel=True)),
        ("c_panel", 48, 64, pb.paint_banner("lion", 10906, start=0.66, stepped=True)),
        ("c_roof_top", 16 * 8, 48, pb.paint_roof(8, 10907, seam=GOLD, fold=0.12)),
        ("c_wing", 24 * 6, 48, pb.paint_roof(6, 10908, seam=GOLD, hem=5, hem_col=CREAM, fold=0.12)),
        ("c_runner", 48, 56, pb.paint_runner("lion", 10909)),
        ("c_back", 64, 48, paint_planks),
        ("c_cloth", 64, 24, pb.paint_cloth_top(10910)),
        ("c_val", 160, 28, pb.paint_valance(8, 10911, shape="crenel", band=0.55)),
        ("c_val_dag", 192, 24, pb.paint_valance(8, 10912, cols=(NAVY, CREAM), shape="dag")),
        ("c_drum", 96, 12, paint_drum),
        "b_post_dark", "b_band", "b_chest", "b_globe", "b_sack", "b_curtain_blue",
    ]
    pb.add_regions(atlas, own, m1=["herbs", "flowers_purple", "soil", "potion_pink", "potion_purple", "potion_cyan", "potion_green",
                                   "glass", "cork", "jar", "jar_top", "linen", "book_green", "book_red", "book_brown", "book_top", "parchment"])


def stake(shell, det, name, x, z, h=0.6):
    pb.guy_stake(shell, det, name, x, z, h=h, region="b_post_dark", gold=True)
    collide((x - 0.1, 0.0, z - 0.1, x + 0.1, h, z + 0.1))


# ---------------------------------------------------------------- the build
def build(decor):
    rng = random.Random(109)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)

    # ---- posts: dark wood, gold bands; the front-right one is the tall banner post
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]
    for k, (x, z) in enumerate(corners):
        if k == 1:
            continue
        pb.sq_post(shell, det, "post_%d" % k, x, z, 4.2 if k == 0 else 4.25, d=0.44, bands=(1.2, 3.15, 3.95) if k == 0 else (1.2, 3.15),
                   cap="block" if k == 0 else "gold", region="b_post_dark", cap_region="wood_dark", band_region="gold", collide_to=BEAM_Y)
    x, z = corners[1]
    pb.sq_post(shell, det, "banner_post", x, z, BANNER_TOP, d=0.46, bands=(1.2, 3.1, 4.7), cap="block", region="b_post_dark",
               cap_region="wood_dark", band_region="gold", collide_to=BEAM_Y)
    beam(shell, "banner_arm", (x - 0.2, BANNER_TOP - 0.22, z), (4.35, BANNER_TOP - 0.22, z), 0.24, {"all": "b_post_dark", "+1": "end_grain",
                                                                                                    "-1": "end_grain"}, width=0.24)
    beam(shell, "banner_brace", (x + 0.22, BANNER_TOP - 1.05, z), (x + 0.95, BANNER_TOP - 0.32, z), 0.15, "b_post_dark")
    box(det, "banner_arm_cap", (4.22, BANNER_TOP - 0.38, z - 0.15), (4.42, BANNER_TOP - 0.04, z + 0.15), {"all": "wood_dark", "+2": "end_grain"})
    ml.banner(shell, "banner", (3.5, BANNER_TOP - 0.38, z + 0.02), 1.0, 2.5, normal=(0, 0, 1), region="c_banner", rod=True, wave=0.03)
    for k, dx in enumerate((-0.38, 0.38)):
        add_cube(det, "banner_ring_%d" % k, (3.5 + dx, BANNER_TOP - 0.36, z + 0.02), EYE, (0.05, 0.12, 0.05), "iron")
    # beams under the eave
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, BEAM_Y, za), (xb, BEAM_Y, zb), 0.28, {"all": "b_post_dark", "+1": "end_grain", "-1": "end_grain"},
             width=0.24, extend=0.14)

    # ---- the main roof: lower tier, crown band, upper tier, finial
    pb.ring_roof(shell, "roof", (CROWN_Y, CHX, CHZ), (EAVE_Y, EHX, EHZ), "c_roof", nx=24, ny=4, a=0.8, droop=0.06, phase=math.pi / 2 + math.pi / 12,
                 fold=0.035, profile="dome")

    def D(s, t):
        xx, zz = pb.squircle(2 * math.pi * (1 - s) + math.pi / 2, CHX, CHZ)
        return v3(xx, CROWN_Y + DRUM_H * (1 - t) - 0.02, zz)
    loft(shell, "drum", D, 12, 1, "c_drum", th=0.04)
    pb.ring_roof(shell, "roof_top", (APEX, 0.0, 0.0), (CROWN_Y + DRUM_H, CHX + 0.05, CHZ + 0.05), "c_roof_top", nx=12, ny=2, a=0.4,
                 droop=0.0, phase=math.pi / 2 + math.pi / 8, fold=0.02, profile="dome")
    box(shell, "finial_collar", (-0.2, APEX - 0.08, -0.2), (0.2, APEX + 0.1, 0.2), "gold")
    box(shell, "finial_cube", (-0.17, APEX + 0.1, -0.17), (0.17, APEX + 0.44, 0.17), {"all": "gold", "+2": "gold"})
    box(det, "finial_small", (-0.11, APEX + 0.44, -0.11), (0.11, APEX + 0.66, 0.11), "gold")
    beam(det, "finial_spike", (0, APEX + 0.66, 0), (0, APEX + 0.98, 0), 0.07, "gold")
    # the lion panel lying on the front of the lower tier
    s_front = 0.0   # roof P's s for the front centre (theta = pi/2): see ring_roof's phase

    def roofpt(x, t):
        th = math.pi / 2
        xt, zt = pb.squircle(th, CHX, CHZ)
        xb, zb = pb.squircle(th, EHX, EHZ)
        y = CROWN_Y - (CROWN_Y - EAVE_Y) * pb.dome(t, 0.8) - 0.5 * 0.06 * math.sin(math.pi * t)
        return v3(x, y, zt + (zb - zt) * t - 0.06 * math.sin(math.pi * t))

    def PANEL(s, t):
        tt = 0.03 + 0.8 * t
        p = roofpt(-0.56 + 1.12 * s, tt)
        return p + v3(0, 0.07, 0.06)
    loft(shell, "lion_panel", PANEL, 1, 3, "c_panel", th=0.02, u_hint=X)
    box(det, "panel_rod", (-0.62, CROWN_Y + 0.02, CHZ + 0.02), (0.62, CROWN_Y + 0.1, CHZ + 0.12), "gold")

    # ---- valances: the gold crenels along the front, dags round the rest of the eave
    pb.valance_curve(shell, "valance_front", lambda s: v3(-2.55 + 5.1 * s, EAVE_Y - 0.02, zfront(-2.55 + 5.1 * s) + 0.05), Z, h=0.56,
                     region="c_val", nx=4, flare=0.04)
    th0, th1 = math.radians(129.0), math.radians(360 + 51.0)

    def E(s):
        th = th0 + (th1 - th0) * s
        xx, zz = pb.squircle(th, EHX + 0.03, EHZ + 0.03, EN)
        return v3(xx, EAVE_Y - 0.03, zz)
    pb.valance_curve(shell, "valance_round", E, v3(0, 0, 0), h=0.44, region="c_val_dag", nx=16, flare=0.0)
    pb.swag(det, "gold_swag", (-HW + 0.2, BEAM_Y - 0.2, HD + 0.26), (HW - 0.2, BEAM_Y - 0.2, HD + 0.26), sag=0.32, d=0.07, segs=6,
            knots=True, region="gold")
    # lanterns under the front valance, a standing one on the counter
    for k, x in enumerate((-1.65, -0.8, 2.0)):
        drop = 0.62 if k != 1 else 0.48
        ml.lantern(shell, "lamp_%d" % k, (x, BEAM_Y - drop, HD - 0.05), size=0.36, metal="iron", chain_to=(x, BEAM_Y - 0.12, HD - 0.05))

    # ---- walls: dark plank back wall with a gathered blue curtain, blue curtain sides
    box(shell, "back_wall", (-HW, 0.0, -HD - 0.08), (HW, BEAM_Y - 0.1, -HD + 0.02), {"all": "c_back"}, stretch=True, u_dir=X)
    collide((-HW, 0.0, -HD - 0.08, HW, BEAM_Y - 0.1, -HD + 0.02))
    pb.drape(shell, det, "back_drape", (-0.6, BEAM_Y - 0.14, -HD + 0.12), (0.6, BEAM_Y - 0.14, -HD + 0.12), (0.0, 1.55, -HD + 0.18),
             (-0.35, 0.02, -HD + 0.12), (0.35, 0.02, -HD + 0.12), Z, region="b_curtain_blue", nx=3, tie_region="gold")
    pb.wall(shell, "right_wall", (HW + 0.05, 0, HD - 0.3), (HW + 0.05, 0, -HD), 0.0, BEAM_Y - 0.1, X, "b_curtain_blue", nx=5)
    collide((HW, 0.0, -HD, HW + 0.1, BEAM_Y - 0.1, HD - 0.3))
    pb.wall(shell, "left_back_wall", (-HW - 0.05, 0, -HD), (-HW - 0.05, 0, WZ0), 0.0, BEAM_Y - 0.1, -X, "b_curtain_blue", nx=1)
    collide((-HW - 0.1, 0.0, -HD, -HW, BEAM_Y - 0.1, WZ0))

    # ---- the left wing: sloping striped roof, gold-capped posts, dagged valance, curtains, a shelf of jars
    for k, z in enumerate((WZ1, WZ0)):
        pb.sq_post(shell, det, "wpost_%d" % k, WX, z, WY_OUT + 0.25, d=0.36, bands=(1.0, 2.3), cap="gold", region="b_post_dark",
                   band_region="gold", collide_to=WY_OUT)
        beam(shell, "w_beam_%d" % k, (-HW, WY_IN - 0.2, z), (WX, WY_OUT - 0.2, z), 0.22, "b_post_dark", extend=0.12)
    beam(shell, "w_side", (WX, WY_OUT - 0.12, WZ0), (WX, WY_OUT - 0.12, WZ1), 0.22, "b_post_dark", extend=0.14)
    xo = WX - 0.3

    def W(s, t):
        z = (WZ0 - 0.25) + (WZ1 - WZ0 + 0.55) * (1 - s)
        x = -HW - 0.1 + (xo + HW + 0.1) * t
        frac = ((1 - s) * 6) % 1.0
        y = WY_IN + 0.05 - (WY_IN - WY_OUT + 0.1) * t - 0.1 * math.sin(math.pi * t) - 0.04 * math.sin(math.pi * frac)
        return v3(x, y, z)
    loft(shell, "wing_roof", W, 6, 3, "c_wing", th=0.035, overlap=0.03)
    yo = W(0, 1)[1]
    pb.valance(shell, "w_val_front", (-HW - 0.1, WY_IN - 0.02, WZ1 + 0.3), (xo, yo - 0.02, WZ1 + 0.3), Z, h=0.42, region="c_val_dag", nx=2)
    pb.valance(shell, "w_val_side", (xo - 0.02, yo - 0.02, WZ1 + 0.3), (xo - 0.02, yo - 0.02, WZ0 - 0.25), -X, h=0.42, region="c_val_dag", nx=2)
    pb.wall(shell, "w_wall_side", (WX - 0.05, 0, WZ0), (WX - 0.05, 0, WZ1), 0.0, WY_OUT - 0.25, -X, "b_curtain_blue", nx=4)
    collide((WX - 0.1, 0.0, WZ0, WX, WY_OUT - 0.25, WZ1))
    pb.wall(shell, "w_wall_back", (-HW, 0, WZ0 - 0.05), (WX, 0, WZ0 - 0.05), 0.0, WY_OUT - 0.25, -Z, "b_curtain_blue", nx=3)
    collide((WX, 0.0, WZ0 - 0.1, -HW, WY_OUT - 0.25, WZ0))
    pb.wall(shell, "w_curtain_front", (WX + 0.15, 0, WZ1 + 0.06), (-3.55, 0, WZ1 + 0.06), 0.0, WY_OUT - 0.22, Z, "b_curtain_blue", nx=3, fold=0.07)
    collide((WX, 0.0, WZ1 - 0.02, -3.55, WY_OUT - 0.22, WZ1 + 0.12))
    beam(det, "w_curtain_edge", (-3.55, WY_OUT - 0.25, WZ1 + 0.1), (-3.6, 0.05, WZ1 + 0.1), 0.06, "gold")
    lv = ml.shelf_unit(shell, "w_shelf", -3.55, -2.7, 0.5, 0.9, levels=(0.7, 1.35, 1.95), h=2.25, back=True, uprights=2, detail=det)
    for i, (xa, xb, yy, zf, zb) in enumerate(lv):
        zc = (zf + zb) / 2
        for j in range(3):
            if (i + j) % 2:
                wb.jar(det, "w_jar_%d_%d" % (i, j), (xa + 0.14 + 0.27 * j, yy, zc), r=0.08, h=0.2 + 0.03 * j)
            else:
                ml.bottle(det, "w_bot_%d_%d" % (i, j), (xa + 0.14 + 0.27 * j, yy, zc), ("green", "cyan", "green")[j % 3],
                          r=0.065, h=0.2, shape="tall")
    for k, x in enumerate((-3.35, -2.95)):
        ml.hanging_bunch(det, "w_herbs_%d" % k, (x, WY_IN - 0.45 - 0.2 * k, WZ1 - 0.05), kind="herbs", length=0.6, width=0.34)

    # ---- the back shelves: jars and bottles at the left, glowing potions at the right, hanging herbs
    lvl = ml.shelf_unit(shell, "shelf_l", -2.2, -0.75, -HD + 0.12, -HD + 0.5, levels=(0.6, 1.2, 1.8, 2.4), h=2.7, back=False, uprights=2,
                        detail=det)
    for i, (xa, xb, yy, zf, zb) in enumerate(lvl):
        zc = (zf + zb) / 2
        if i == 2:
            wb.book_row(det, "books_%d" % i, xa, xb, yy, zf - 0.02, 0.24, rng, colors=("red", "green", "brown"))
            continue
        for j in range(4):
            xx = xa + 0.14 + j * (xb - xa - 0.28) / 3
            if (i + j) % 2:
                wb.jar(det, "jar_%d_%d" % (i, j), (xx, yy, zc), r=0.075, h=0.2)
            else:
                ml.bottle(det, "bot_%d_%d" % (i, j), (xx, yy, zc), "green", r=0.06, h=0.22, shape="tall")
    lvr = ml.shelf_unit(shell, "shelf_r", 0.75, 2.2, -HD + 0.12, -HD + 0.5, levels=(0.6, 1.2, 1.8, 2.4), h=2.7, back=False, uprights=2,
                        detail=det)
    pb.potion_rows(det, "pot_r", lvr, rng, ("pink", "purple", "cyan", "pink", "purple", "green"))
    for k, x in enumerate((-1.9, -1.4, -1.0)):
        ml.hanging_bunch(det, "herbs_%d" % k, (x, BEAM_Y - 0.15, -HD + 0.35), kind="herbs", length=0.5 + 0.1 * (k % 2), width=0.3)
    decor.block("farmhouse_decorations:pile_of_books", -1.5, 2.7 + 0.1, -HD + 0.3, facing="front", fallback="leather", solid=False)

    # ---- the counter: cream cloth with dags, the lion runner, its goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    box(shell, "cloth_top", (cx0 - 0.03, y, cz0 - 0.03), (cx1 + 0.03, y + 0.015, cz1 + 0.05), {"all": "cloth_beige"}, stretch=True, u_dir=X)
    for k, (xa, xb) in enumerate(((cx0 - 0.03, -0.2), (1.0, cx1 + 0.03))):
        ml.plate(shell, "cloth_front_%d" % k, ((xa + xb) / 2, y - 0.17, cz1 + 0.06), xb - xa, 0.36, "c_cloth", normal=(0, 0, 1), th=0.012)
    ml.plate(shell, "runner", (0.4, y - 0.5, cz1 + 0.075), 1.2, 1.0, "c_runner", normal=(0, 0, 1), th=0.012)
    box(shell, "runner_top", (-0.2, y + 0.016, cz0 + 0.1), (1.0, y + 0.024, cz1 + 0.08), {"all": "cloth_blue"}, stretch=True, u_dir=X)
    pb.armillary(shell, det, "armillary", (-0.95, y, (cz0 + cz1) / 2), r=0.24)
    wb.book_stack(det, "books", (-0.4, y + 0.02, (cz0 + cz1) / 2), 2, rng, w=0.4, d=0.3, th=0.11, colors=("green", "red"))
    pb.scroll(det, "scroll", (0.2, y + 0.08, (cz0 + cz1) / 2 + 0.05), length=0.48, r=0.06, yaw=0.15)
    ml.plate(det, "scroll_open", (0.2, y + 0.03, (cz0 + cz1) / 2 + 0.18), 0.4, 0.2, "beige", normal=(0, 1, 0), up=(0, 0, -1), th=0.008)
    ml.lantern(shell, "lamp_counter", (0.85, y + 0.24, (cz0 + cz1) / 2), size=0.32, metal="iron")
    pb.gold_bars(det, "gold_bars", (1.5, y + 0.02, (cz0 + cz1) / 2), n=3, yaw=0.2)
    for k, (dx, c) in enumerate(((1.82, "purple"), (1.92, "pink"))):
        ml.bottle(det, "c_pot_%d" % k, (dx, y, (cz0 + cz1) / 2 - 0.15 + 0.12 * k), c, r=0.055, h=0.16, glow=True)
    # in front of the counter: a small chest of red gems, a crate of gold
    pb.chest(shell, det, "gem_chest", (-0.75, 0.0, cz1 + 0.35), w=0.48, d=0.36, h=0.36, solid=False)
    for k in range(3):
        add_cube(det, "gem_%d" % k, (-0.86 + 0.1 * k, 0.37, cz1 + 0.35 + 0.04 * (k % 2)), ry(0.5 * k), (0.08, 0.06, 0.08), "potion_red")
    ml.crate(shell, "gold_crate", (1.55, 0.0, cz1 + 0.32), size=(0.5, 0.36, 0.4), solid=False)
    pb.gold_bars(det, "gold_crate_bars", (1.55, 0.36, cz1 + 0.32), n=3, yaw=0.0)

    ml.rug(shell, "rug", -0.5, 2.6, 1.7, 3.75, y=0.0, region="c_rug")

    # ---- outside left: planter of flowers on a crate, the big chest, crates, bales, stakes and ropes
    ml.crate(shell, "planter_base", (-3.15, 0.0, 2.15), size=(0.78, 0.7, 0.5), solid=True)
    pb.planter(shell, det, "planter", (-3.15, 0.7, 2.15), w=0.74, d=0.46, h=0.34, plant="flowers_purple", n=3)
    pb.chest(shell, det, "big_chest", (-2.7, 0.0, 3.07), w=0.98, d=0.66, h=0.72)
    decor.block("furnish:spruce_crate", -4.6, 0.0, 3.15, facing="front", scale=0.85, alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "l_crate_top", (-4.6, 0.85, 3.15), size=0.62, yaw=0.1, solid=True)
    for k, (dx, dy, dz) in enumerate(((0.0, 0.0, 0.0), (0.42, 0.0, 0.05), (0.2, 0.36, 0.02))):
        ml.rbox(shell, "l_bale_%d" % k, (-4.05 + dx, dy, 3.6 + dz), (0.4, 0.36, 0.42), 0.1 * k, "b_sack", solid=(dy == 0), stretch=True)
    stake(shell, det, "stake_a", -3.05, 3.8)
    stake(shell, det, "stake_b", -5.65, 3.0)
    ml.rope(det, "guy_a", (-3.5, WY_IN - 0.45, WZ1 + 0.32), (-3.05, 0.5, 3.8), d=0.06, sag=0.05, segs=2)
    ml.rope(det, "guy_b", (WX - 0.05, WY_OUT + 0.15, WZ1), (-5.65, 0.5, 3.0), d=0.06, sag=0.05, segs=2)
    # ---- outside right: crates and bales under the banner, a stake and rope from the banner post
    ml.crate(shell, "r_crate_0", (3.25, 0.0, 1.3), size=0.85, yaw=-0.05, solid=True)
    decor.block("furnish:spruce_crate", 3.3, 0.0, 0.35, facing="front", scale=0.8, alt="minecraft:barrel", fallback="crate")
    for k, (dx, dy, dz) in enumerate(((0.0, 0.0, 0.0), (0.42, 0.0, -0.05), (0.2, 0.36, 0.0))):
        ml.rbox(shell, "r_bale_%d" % k, (3.3 + dx, dy, 2.45 + dz), (0.4, 0.36, 0.42), -0.1 * k, "b_sack", solid=(dy == 0), stretch=True)
    decor.block("farmersdelight:rice_bag", 3.25, 0.85, 1.3, facing="front", scale=0.55, fallback="sack", solid=False)
    stake(shell, det, "stake_c", 4.4, 3.2)
    ml.rope(det, "guy_c", (HW + 0.25, 4.7, HD), (4.4, 0.5, 3.2), d=0.06, sag=0.06, segs=2)
    return root


def item_icon(path):
    pb.stall_icon(path, roof="dome")


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
