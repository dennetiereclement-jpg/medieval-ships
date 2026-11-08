#!/usr/bin/env python3
"""tente_lion_chapiteau — Chapiteau royal au lion / Royal Lion Marquee (1.26.0, market tents group B; reference:
scratchpad/ref2/tente_lion_chapiteau_ref.png, picture 109).

A long rounded royal-blue marquee of Lion Port, one block (TentType group "tents"), about 10.5 blocks wide with its stakes
and the banner arm, 6.8 deep, the gold finial at about 6.9:

  - ONE elongated rounded marquee (a squircle plan, 8.4 x 5.4 at the eaves): the roof curves up from the eave to a
    raised oval crown centred over the whole length, a blue and gold crenellated band round the crown, a short rounded
    cap and a stacked GOLD FINIAL; wide blue and cream stripes edged with thin gold seams, a cream hem above the valance;
    a blue LION PANEL with a gold border and a pointed bottom lies on the front of the roof; the front valance over the
    shop opening is a blue band with GOLD CRENELS, the rest of the eave a blue / cream valance with gold-edged dags;
  - dark wooden posts with gold bands, gold finials on the corner posts poking through the roof; the post between the
    curtained left part and the shop opening has a capped top; the front-right corner post rises as the tall BANNER POST
    with a cross-arm and a brace, carrying a big blue LION BANNER with a gold tassel;
  - the left part of the front is closed by BLUE CURTAINS sprinkled with gold diamonds (and the left end, all round to
    the back), then open on a shelf of jars with hanging herbs; the shop opening on the right: three glowing lanterns
    under the crenellated valance, a gold rope swag;
  - inside: dark plank back wall with a blue curtain gathered by a gold tie in the middle, a shelf of jars, bottles and
    books and a shelf of glowing potions (pink, purple, cyan), the COUNTER under a cream cloth with dags and the blue
    lion runner, an ARMILLARY SPHERE, books, a scroll, a standing lantern and gold bars on it, a small chest of red gems
    and a crate of gold in front of it, the blue RUG with the gold border and the faded lion;
  - outside: a planter of purple flowers on a crate, the big iron-banded CHEST, stacked crates, cream bales and a sack,
    gold-banded stakes and guy ropes.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in between the
boundary post and the counter's left end. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_lion_chapiteau.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_lion_chapiteau.json, models/entity + blockbench/tente_lion_chapiteau.bbmodel,
textures/entity/tente_lion_chapiteau.png, textures/item/tente_lion_chapiteau.png, interiors/tente_lion_chapiteau_decor.json.
"""
import math
import os
import random
import sys

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
CX, CZ = 3.5, 2.2             # corner posts at (+-CX, +-CZ) (the front-right one is the banner post)
BX = -1.2                     # the boundary post between the curtained left part and the shop opening (front)
EAVE_Y, EHX, EHZ, EN = 3.55, 4.15, 2.72, 5.0     # the eave ring (squircle exponent EN)
CROWN_Y, CHX, CHZ = 5.75, 1.05, 0.56             # the oval crown ring (top of the roof)
DRUM_H = 0.26
APEX = 6.35
BEAM_Y = 3.35
COUNTER = (-0.25, 2.65, 0.95, 1.55)
COUNTER_H = 1.05
NPC_SPOT = (0.4, -0.12)       # (x0, z0) of the merchant's free 1 x 1 x 2.2 place
BANNER_TOP = 6.0
SHOP_X0 = BX                  # the shop opening from x = SHOP_X0 to x = CX (front)
CURTAIN_X1 = -2.35            # the front curtain from the left corner to x = CURTAIN_X1, then the jar shelf opening


def zfront(x):
    """z of the eave ring's front edge at x."""
    return EHZ * max(0.0, 1.0 - abs(x / EHX) ** EN) ** (1.0 / EN)


def theta_front(x):
    """The squircle parameter theta of the front edge point at x (0 < theta < pi)."""
    c = math.copysign(abs(x / EHX) ** (EN / 2.0), x)
    return math.acos(max(-1.0, min(1.0, c)))


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
        ("c_roof", 16 * 14, 80, pb.paint_roof(14, 10903, seam=GOLD, hem=11, hem_col=CREAM, fold=0.14)),
        ("c_rug", 128, 96, pb.paint_rug(10904, "lion", faded=0.4)),
        ("c_banner", 40, 96, pb.paint_banner("lion", 10905, start=0.8, tassel=True)),
        ("c_panel", 48, 64, pb.paint_banner("lion", 10906, start=0.66, stepped=True)),
        ("c_roof_top", 16 * 8, 48, pb.paint_roof(8, 10907, seam=GOLD, fold=0.12)),
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

    # ---- posts: dark wood, gold bands; gold finials on the corners, the boundary post, the tall banner post
    for k, (x, z) in enumerate(((-CX, CZ), (CX, -CZ), (-CX, -CZ))):
        pb.sq_post(shell, det, "post_%d" % k, x, z, 4.25, d=0.42, bands=(1.2, 3.15), cap="gold", region="b_post_dark", band_region="gold",
                   collide_to=BEAM_Y)
    pb.sq_post(shell, det, "post_mid", BX, CZ + 0.1, 4.15, d=0.44, bands=(1.2, 3.15, 3.9), cap="block", region="b_post_dark",
               cap_region="wood_dark", band_region="gold", collide_to=BEAM_Y)
    x, z = CX, CZ
    pb.sq_post(shell, det, "banner_post", x, z, BANNER_TOP, d=0.46, bands=(1.2, 3.1, 4.6), cap="block", region="b_post_dark",
               cap_region="wood_dark", band_region="gold", collide_to=BEAM_Y)
    beam(shell, "banner_arm", (x - 0.2, BANNER_TOP - 0.22, z), (x + 1.9, BANNER_TOP - 0.22, z), 0.24, {"all": "b_post_dark", "+1": "end_grain",
                                                                                                       "-1": "end_grain"}, width=0.24)
    beam(shell, "banner_brace", (x + 0.22, BANNER_TOP - 1.05, z), (x + 0.95, BANNER_TOP - 0.32, z), 0.15, "b_post_dark")
    box(det, "banner_arm_cap", (x + 1.75, BANNER_TOP - 0.38, z - 0.15), (x + 1.95, BANNER_TOP - 0.04, z + 0.15), {"all": "wood_dark", "+2": "end_grain"})
    bxc = x + 1.12
    ml.banner(shell, "banner", (bxc, BANNER_TOP - 0.38, z + 0.02), 1.0, 2.4, normal=(0, 0, 1), region="c_banner", rod=True, wave=0.03)
    for k, dx in enumerate((-0.38, 0.38)):
        add_cube(det, "banner_ring_%d" % k, (bxc + dx, BANNER_TOP - 0.36, z + 0.02), EYE, (0.05, 0.12, 0.05), "iron")
    # beams under the eave
    ring = [(-CX, CZ), (CX, CZ), (CX, -CZ), (-CX, -CZ)]
    for k in range(4):
        (xa, za), (xb, zb) = ring[k], ring[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, BEAM_Y, za), (xb, BEAM_Y, zb), 0.28, {"all": "b_post_dark", "+1": "end_grain", "-1": "end_grain"},
             width=0.24, extend=0.14)

    # ---- the roof: one long rounded tier up to the oval crown, the crown band, the cap, the finial
    pb.ring_roof(shell, "roof", (CROWN_Y, CHX, CHZ), (EAVE_Y, EHX, EHZ), "c_roof", nx=28, ny=4, a=0.7, droop=0.06, phase=math.pi / 2 + math.pi / 14,
                 fold=0.035, profile="dome")

    def D(s, t):
        xx, zz = pb.squircle(2 * math.pi * (1 - s) + math.pi / 2, CHX, CHZ)
        return v3(xx, CROWN_Y + DRUM_H * (1 - t) - 0.02, zz)
    loft(shell, "drum", D, 14, 1, "c_drum", th=0.04)
    pb.ring_roof(shell, "roof_top", (APEX, 0.35, 0.05), (CROWN_Y + DRUM_H, CHX + 0.05, CHZ + 0.05), "c_roof_top", nx=12, ny=2, a=0.4,
                 droop=0.0, phase=math.pi / 2 + math.pi / 8, fold=0.02, profile="dome")
    box(shell, "finial_collar", (-0.22, APEX - 0.08, -0.2), (0.22, APEX + 0.1, 0.2), "gold")
    box(shell, "finial_cube", (-0.17, APEX + 0.1, -0.17), (0.17, APEX + 0.44, 0.17), {"all": "gold", "+2": "gold"})
    box(det, "finial_small", (-0.11, APEX + 0.44, -0.11), (0.11, APEX + 0.66, 0.11), "gold")
    beam(det, "finial_spike", (0, APEX + 0.66, 0), (0, APEX + 0.98, 0), 0.07, "gold")

    # the lion panel lying on the front of the roof (front centre: theta = pi/2)
    def roofpt(x, t):
        xt, zt = pb.squircle(math.pi / 2, CHX, CHZ)
        xb, zb = pb.squircle(math.pi / 2, EHX, EHZ)
        y = CROWN_Y - (CROWN_Y - EAVE_Y) * pb.dome(t, 0.7) - 0.5 * 0.06 * math.sin(math.pi * t)
        return v3(x, y, zt + (zb - zt) * t - 0.06 * math.sin(math.pi * t))

    def PANEL(s, t):
        return roofpt(-0.56 + 1.12 * s, 0.03 + 0.8 * t) + v3(0, 0.07, 0.06)
    loft(shell, "lion_panel", PANEL, 1, 3, "c_panel", th=0.02, u_hint=X)
    box(det, "panel_rod", (-0.62, CROWN_Y + 0.02, CHZ + 0.02), (0.62, CROWN_Y + 0.1, CHZ + 0.12), "gold")

    # ---- valances: gold crenels over the shop opening, dags round the rest of the eave
    xa, xb = SHOP_X0 - 0.25, CX + 0.25
    pb.valance_curve(shell, "valance_front", lambda s: v3(xa + (xb - xa) * s, EAVE_Y - 0.02, zfront(xa + (xb - xa) * s) + 0.05), Z, h=0.56,
                     region="c_val", nx=4, flare=0.04)
    th0, th1 = theta_front(xa) - 0.02, theta_front(xb) + 2 * math.pi + 0.02

    def E(s):
        th = th0 + (th1 - th0) * s
        xx, zz = pb.squircle(th, EHX + 0.03, EHZ + 0.03, EN)
        return v3(xx, EAVE_Y - 0.03, zz)
    pb.valance_curve(shell, "valance_round", E, v3(0, 0, 0), h=0.44, region="c_val_dag", nx=20, flare=0.0)
    pb.swag(det, "gold_swag", (BX + 0.2, BEAM_Y - 0.2, CZ + 0.32), (CX - 0.2, BEAM_Y - 0.2, CZ + 0.3), sag=0.34, d=0.07, segs=6, knots=True,
            region="gold")
    # lanterns under the front valance, a standing one on the counter
    for k, x in enumerate((-0.55, 0.3, 3.0)):
        drop = 0.62 if k != 1 else 0.48
        ml.lantern(shell, "lamp_%d" % k, (x, BEAM_Y - drop, CZ - 0.05), size=0.36, metal="iron", chain_to=(x, BEAM_Y - 0.12, CZ - 0.05))

    # ---- walls: dark plank back wall with a gathered blue curtain, blue curtains at the ends and the closed left front
    box(shell, "back_wall", (-CX, 0.0, -CZ - 0.08), (CX, BEAM_Y - 0.1, -CZ + 0.02), {"all": "c_back"}, stretch=True, u_dir=X)
    collide((-CX, 0.0, -CZ - 0.08, CX, BEAM_Y - 0.1, -CZ + 0.02))
    pb.drape(shell, det, "back_drape", (0.6, BEAM_Y - 0.14, -CZ + 0.12), (1.8, BEAM_Y - 0.14, -CZ + 0.12), (1.2, 1.55, -CZ + 0.18),
             (0.85, 0.02, -CZ + 0.12), (1.55, 0.02, -CZ + 0.12), Z, region="b_curtain_blue", nx=3, tie_region="gold")
    pb.wall(shell, "right_wall", (CX + 0.05, 0, CZ - 0.3), (CX + 0.05, 0, -CZ), 0.0, BEAM_Y - 0.1, X, "b_curtain_blue", nx=5)
    collide((CX, 0.0, -CZ, CX + 0.1, BEAM_Y - 0.1, CZ - 0.3))
    pb.wall(shell, "left_wall", (-CX - 0.05, 0, -CZ), (-CX - 0.05, 0, CZ), 0.0, BEAM_Y - 0.1, -X, "b_curtain_blue", nx=5)
    collide((-CX - 0.1, 0.0, -CZ, -CX, BEAM_Y - 0.1, CZ))
    pb.wall(shell, "front_curtain", (-CX + 0.1, 0, CZ + 0.06), (CURTAIN_X1, 0, CZ + 0.06), 0.0, BEAM_Y - 0.05, Z, "b_curtain_blue", nx=3,
            fold=0.07)
    collide((-CX, 0.0, CZ - 0.02, CURTAIN_X1, BEAM_Y - 0.05, CZ + 0.12))
    beam(det, "curtain_edge", (CURTAIN_X1, BEAM_Y - 0.1, CZ + 0.1), (CURTAIN_X1 - 0.05, 0.05, CZ + 0.1), 0.06, "gold")
    # the shelf of jars in the opening at the left of the shop, herbs hanging over it
    lv = ml.shelf_unit(shell, "jar_shelf", CURTAIN_X1 + 0.05, BX - 0.35, 0.5, 0.9, levels=(0.7, 1.35, 1.95), h=2.25, back=True, uprights=2,
                       detail=det)
    for i, (xa_, xb_, yy, zf, zb) in enumerate(lv):
        zc = (zf + zb) / 2
        for j in range(3):
            if (i + j) % 2:
                wb.jar(det, "w_jar_%d_%d" % (i, j), (xa_ + 0.14 + 0.25 * j, yy, zc), r=0.08, h=0.2 + 0.03 * j)
            else:
                ml.bottle(det, "w_bot_%d_%d" % (i, j), (xa_ + 0.14 + 0.25 * j, yy, zc), ("green", "cyan", "green")[j % 3], r=0.065, h=0.2,
                          shape="tall")
    for k, x in enumerate((CURTAIN_X1 + 0.3, BX - 0.55)):
        ml.hanging_bunch(det, "w_herbs_%d" % k, (x, BEAM_Y - 0.2 - 0.15 * k, CZ - 0.1), kind="herbs", length=0.6, width=0.34)

    # ---- the back shelves: jars, bottles and books at the left, glowing potions at the right, hanging herbs
    lvl = ml.shelf_unit(shell, "shelf_l", -0.45, 0.55, -CZ + 0.12, -CZ + 0.5, levels=(0.6, 1.2, 1.8, 2.4), h=2.7, back=False, uprights=2,
                        detail=det)
    for i, (xa_, xb_, yy, zf, zb) in enumerate(lvl):
        zc = (zf + zb) / 2
        if i == 2:
            wb.book_row(det, "books_%d" % i, xa_, xb_, yy, zf - 0.02, 0.24, rng, colors=("red", "green", "brown"))
            continue
        for j in range(3):
            xx = xa_ + 0.14 + j * (xb_ - xa_ - 0.28) / 2
            if (i + j) % 2:
                wb.jar(det, "jar_%d_%d" % (i, j), (xx, yy, zc), r=0.075, h=0.2)
            else:
                ml.bottle(det, "bot_%d_%d" % (i, j), (xx, yy, zc), "green", r=0.06, h=0.22, shape="tall")
    lvr = ml.shelf_unit(shell, "shelf_r", 1.85, 3.1, -CZ + 0.12, -CZ + 0.5, levels=(0.6, 1.2, 1.8, 2.4), h=2.7, back=False, uprights=2,
                        detail=det)
    pb.potion_rows(det, "pot_r", lvr, rng, ("pink", "purple", "cyan", "pink", "purple", "green"))
    for k, x in enumerate((-0.25, 0.25)):
        ml.hanging_bunch(det, "herbs_%d" % k, (x, BEAM_Y - 0.15, -CZ + 0.35), kind="herbs", length=0.5 + 0.1 * (k % 2), width=0.3)
    decor.block("farmhouse_decorations:pile_of_books", 0.05, 2.7 + 0.1, -CZ + 0.3, facing="front", fallback="leather", solid=False)

    # ---- the counter: cream cloth with dags, the lion runner, its goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    mid = (cx0 + cx1) / 2
    box(shell, "cloth_top", (cx0 - 0.03, y, cz0 - 0.03), (cx1 + 0.03, y + 0.015, cz1 + 0.05), {"all": "cloth_beige"}, stretch=True, u_dir=X)
    for k, (xa_, xb_) in enumerate(((cx0 - 0.03, mid - 0.6), (mid + 0.6, cx1 + 0.03))):
        ml.plate(shell, "cloth_front_%d" % k, ((xa_ + xb_) / 2, y - 0.17, cz1 + 0.06), xb_ - xa_, 0.36, "c_cloth", normal=(0, 0, 1), th=0.012)
    ml.plate(shell, "runner", (mid, y - 0.5, cz1 + 0.075), 1.2, 1.0, "c_runner", normal=(0, 0, 1), th=0.012)
    box(shell, "runner_top", (mid - 0.6, y + 0.016, cz0 + 0.1), (mid + 0.6, y + 0.024, cz1 + 0.08), {"all": "cloth_blue"}, stretch=True, u_dir=X)
    pb.armillary(shell, det, "armillary", (cx0 + 0.35, y, zc), r=0.24)
    wb.book_stack(det, "books", (cx0 + 0.9, y + 0.02, zc), 2, rng, w=0.4, d=0.3, th=0.11, colors=("green", "red"))
    pb.scroll(det, "scroll", (mid + 0.1, y + 0.08, zc + 0.05), length=0.48, r=0.06, yaw=0.15)
    ml.plate(det, "scroll_open", (mid + 0.1, y + 0.03, zc + 0.18), 0.4, 0.2, "beige", normal=(0, 1, 0), up=(0, 0, -1), th=0.008)
    ml.lantern(shell, "lamp_counter", (mid + 0.75, y + 0.24, zc), size=0.32, metal="iron")
    pb.gold_bars(det, "gold_bars", (cx1 - 0.4, y + 0.02, zc), n=3, yaw=0.2)
    for k, (dx, c) in enumerate(((cx1 - 0.12, "purple"), (cx1 - 0.08, "pink"))):
        ml.bottle(det, "c_pot_%d" % k, (dx, y, zc - 0.15 + 0.26 * k), c, r=0.055, h=0.16, glow=True)
    # in front of the counter: a small chest of red gems, a crate of gold
    pb.chest(shell, det, "gem_chest", (mid - 0.95, 0.0, cz1 + 0.35), w=0.48, d=0.36, h=0.36, solid=False)
    for k in range(3):
        add_cube(det, "gem_%d" % k, (mid - 1.06 + 0.1 * k, 0.37, cz1 + 0.35 + 0.04 * (k % 2)), ry(0.5 * k), (0.08, 0.06, 0.08), "potion_red")
    ml.crate(shell, "gold_crate", (mid + 1.0, 0.0, cz1 + 0.32), size=(0.5, 0.36, 0.4), solid=False)
    pb.gold_bars(det, "gold_crate_bars", (mid + 1.0, 0.36, cz1 + 0.32), n=3, yaw=0.0)

    ml.rug(shell, "rug", 0.0, 3.25, 1.7, 3.8, y=0.0, region="c_rug")

    # ---- outside left: planter of flowers on a crate, the big chest, crates, bales, stakes and ropes
    ml.crate(shell, "planter_base", (-1.95, 0.0, 1.95), size=(0.74, 0.7, 0.5), solid=True)
    pb.planter(shell, det, "planter", (-1.95, 0.7, 1.95), w=0.72, d=0.46, h=0.34, plant="flowers_purple", n=3)
    pb.chest(shell, det, "big_chest", (-2.0, 0.0, 3.05), w=0.98, d=0.66, h=0.72)
    decor.block("furnish:spruce_crate", -4.0, 0.0, 3.0, facing="front", scale=0.85, alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "l_crate_top", (-4.0, 0.85, 3.0), size=0.62, yaw=0.1, solid=True)
    for k, (dx, dy, dz) in enumerate(((0.0, 0.0, 0.0), (0.42, 0.0, 0.05), (0.2, 0.36, 0.02))):
        ml.rbox(shell, "l_bale_%d" % k, (-3.35 + dx, dy, 3.45 + dz), (0.4, 0.36, 0.42), 0.1 * k, "b_sack", solid=(dy == 0), stretch=True)
    stake(shell, det, "stake_a", -2.85, 3.75)
    stake(shell, det, "stake_b", -4.85, 2.2)
    ml.rope(det, "guy_a", (-2.9, EAVE_Y - 0.4, zfront(-2.9) + 0.05), (-2.85, 0.5, 3.75), d=0.06, sag=0.05, segs=2)
    ml.rope(det, "guy_b", (-EHX + 0.05, EAVE_Y - 0.35, 1.2), (-4.85, 0.5, 2.2), d=0.06, sag=0.05, segs=2)
    # ---- outside right: crates and bales under the banner, a stake and rope from the banner post
    ml.crate(shell, "r_crate_0", (4.35, 0.0, 1.35), size=0.82, yaw=-0.05, solid=True)
    decor.block("furnish:spruce_crate", 4.35, 0.0, 0.45, facing="front", scale=0.8, alt="minecraft:barrel", fallback="crate")
    for k, (dx, dy, dz) in enumerate(((0.0, 0.0, 0.0), (0.42, 0.0, -0.05), (0.2, 0.36, 0.0))):
        ml.rbox(shell, "r_bale_%d" % k, (4.1 + dx, dy, 2.55 + dz), (0.4, 0.36, 0.42), -0.1 * k, "b_sack", solid=(dy == 0), stretch=True)
    decor.block("farmersdelight:rice_bag", 4.35, 0.82, 1.35, facing="front", scale=0.55, fallback="sack", solid=False)
    stake(shell, det, "stake_c", 5.35, 2.4)
    ml.rope(det, "guy_c", (CX + 0.25, 4.6, CZ), (5.35, 0.5, 2.4), d=0.06, sag=0.06, segs=2)
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
