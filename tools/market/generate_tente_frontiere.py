#!/usr/bin/env python3
"""tente_frontiere — Tente marchande de frontière / Frontier Merchant Tent (1.26.0, market group F; reference:
scratchpad/ref2/tente_frontiere_ref.png, the top-right tent of the board tentes_065_planche.png).

A rustic frontier trading tent, one block (TentType group "tents", the integrator's list MARKET_TENTS):

  - a HIPPED roof (ridge along x, four sagging slopes) of worn crimson canvas patched with cream hide pieces and an
    olive patch, ragged red edges on the sides and the back, a tattered beige rag valance along the open front;
  - a rustic frame: six weathered dark posts (four corners and the middle of each side) with iron bands, pointed gold
    finials on the front posts and iron spikes on the others, rough eave beams, hip rafters up to the ridge, little
    carved wooden totems on the two ridge ends;
  - a big HORNED ANIMAL SKULL (bull) on the top of the front slope, its crescent horns rising above the ridge;
  - FURS and HIDES: a big white shaggy fur thrown over the front-left corner of the roof and hanging down the corner,
    a cowhide down the corner post, a cowhide on the left side, tan hides on the right side and inside;
  - two red banners with the white frontier RUNE (a spiked diamond) and a gold fringe under the front beam, a round
    wooden shield with CROSSED AXES on the left middle post, a lit lantern on an iron arm of the front-right post;
  - red canvas walls at the back and the back half of the sides, the front halves drawn back as red drapes tied to
    the front posts; guy ropes to pegs, two spears / staffs leaning on the left side;
  - inside: back shelves with candle lanterns, rolled and folded pelts, horns and jars; the counter with stacked furs,
    a ledger, a coin box and a pile of books; a weapon rack (axes and spears) along the left wall; a sack and a barrel;
    the red rug with cream rings in the open front;
  - outside along the left side: an iron-banded crate with a gold lock, a plank crate, a barrel, the big chest with
    an open ledger on it, a chopping block with an axe; on the right, a crate topped with fur bundles.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT), reached on foot round the left
end of the counter. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_frontiere.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_frontiere.json, models/entity + blockbench/tente_frontiere.bbmodel,
textures/entity/tente_frontiere.png, textures/item/tente_frontiere.png, interiors/tente_frontiere_decor.json.
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
NAME = "tente_frontiere"
v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _scale = ml._rgb, ml._scale

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 3.6, 3.4            # posts: x = +-HW, z = +-HD (corners) and (+-HW, 0) (middle of the sides)
EAVE = 3.1                   # top of the eave beams
EY = EAVE + 0.06             # the roof's eave line
W, D = HW + 0.3, HD + 0.3    # the roof's eave half length / half depth
RIDGE, RL = 4.8, 2.2         # ridge height, half length
COUNTER = (-1.25, 2.7, -1.66, -1.08)   # x0, x1, z0, z1
COUNTER_H = 1.0
SHELF_Z = (-3.18, -2.78)
NPC_SPOT = (0.6, -2.73)      # (x0, z0) of the free 1 x 1 x 2.2 place behind the counter

RED, RED_DARK = _rgb("8e2a22"), _rgb("5a1712")
CREAM, OLIVE = _rgb("e4d6b8"), _rgb("6e6c30")
FUR, FUR_DARK = _rgb("e8dcc2"), _rgb("8a7458")
TAN, TAN_DARK = _rgb("c49a64"), _rgb("74522e")
GOLDF = _rgb("d8a83e")


# ---------------------------------------------------------------- textures
def paint_shield(img):
    """A round wooden shield (cut-out disc): planks, an iron rim and boss, white crossed axes."""
    from PIL import Image, ImageDraw
    rng = random.Random(3109)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), _rgb("8a5a30"), _rgb("4a2e14"), 5, rng, joints=False, knots=0.1, grain=0.12, shade=0.06, vertical=True)
    S = 4
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    pf.crossed_axes(ImageDraw.Draw(big), w * S * 0.14, h * S * 0.14, w * S * 0.86, h * S * 0.86, S)
    img.alpha_composite(big.resize((w, h), Image.LANCZOS))
    px = img.load()
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + 0.5 - w / 2, y + 0.5 - h / 2) / (w / 2)
            r, g, b, a = px[x, y]
            if d > 1.0:
                px[x, y] = (0, 0, 0, 0)
            elif d > 0.86:
                px[x, y] = (84, 84, 90, 255) if (x + y) % 5 else (150, 150, 156, 255)
            else:
                px[x, y] = (r, g, b, 255)


def paint_pelts(img):
    """The side of a stack of folded pelts: wavy bands of browns, greys and cream fur."""
    rng = random.Random(3110)
    w, h = img.size
    px = img.load()
    cols = [_rgb("8a6440"), _rgb("d8ccb2"), _rgb("5a4634"), _rgb("a89a86"), _rgb("b08050"), _rgb("e8dcc6")]
    for y in range(h):
        for x in range(w):
            band = int((y + 1.2 * math.sin(x * 0.5 + y)) / max(1, h / 6)) % len(cols)
            px[x, y] = ml._jitter(_scale(cols[band], 0.88 + 0.2 * abs(math.sin(x * 1.3 + band))), rng, 8) + (255,)


def paint_ledger(img):
    """An open ledger: two cream pages with ink lines, a dark spine."""
    rng = random.Random(3111)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("e8dcbc")
            if abs(x - w / 2) < 1:
                c = _rgb("5a3a20")
            elif y % 3 == 1 and 2 < x < w - 3 and abs(x - w / 2) > 2 and rng.random() < 0.8:
                c = _rgb("6a5a48")
            elif x < 1 or x >= w - 1:
                c = _rgb("7a4a28")
            px[x, y] = ml._jitter(c, rng, 5) + (255,)


def lock_emblem(d, x0, y0, x1, y1, S):
    """The gold lock plate of the crates: a shield-shaped plate with a keyhole."""
    w, h = x1 - x0, y1 - y0
    gold, dark = (226, 176, 70), (120, 80, 24)
    d.polygon([(x0 + w * 0.25, y0 + h * 0.1), (x0 + w * 0.75, y0 + h * 0.1), (x0 + w * 0.75, y0 + h * 0.6), (x0 + w * 0.5, y0 + h * 0.9),
               (x0 + w * 0.25, y0 + h * 0.6)], fill=gold, outline=dark)
    d.ellipse([x0 + w * 0.42, y0 + h * 0.28, x0 + w * 0.58, y0 + h * 0.44], fill=dark)
    d.rectangle([x0 + w * 0.47, y0 + h * 0.4, x0 + w * 0.53, y0 + h * 0.62], fill=dark)


def add_regions(atlas):
    """This tent's regions, packed in the free band of the 512 px atlas (three rows)."""
    atlas.add("fr_roof", 256, 128, pf.patchwork(RED, 3101, patches=((CREAM, 3, 4, 9), (OLIVE, 2, 7, 12), (RED_DARK, 6, 5, 11),
                                                                    (_rgb("c8b890"), 2, 3, 6)), folds=6, shade=(0.8, 1.02)))
    atlas.add("fr_rug", 128, 96, pf.rug(_rgb("962820"), _rgb("4e1410"), _rgb("d8c09a"), 3102, rings=2, fringe=_rgb("e8dcbc")))
    atlas.add("fr_banner", 48, 96, pf.banner(_rgb("962622"), _rgb("d8b878"), pf.rune, 3103, fringe=GOLDF, point="dags",
                                             emblem_box=(0.1, 0.1, 0.9, 0.62)))
    atlas.add("fr_drape", 64, 96, pf.patchwork(RED, 3104, patches=((CREAM, 2, 5, 9), (RED_DARK, 3, 4, 8)), folds=3, shade=(0.8, 1.0)))
    atlas.add("fr_wall", 128, 64, pf.patchwork(_scale(RED, 0.92), 3105, patches=((CREAM, 3, 5, 10), (RED_DARK, 4, 5, 9)), folds=5,
                                               shade=(0.78, 0.98)))
    atlas.add("fr_fur", 96, 64, pf.fur(FUR, FUR_DARK, 3106, shag=18, spots=(_rgb("c8b08a"), 5, 4, 9)))
    atlas.add("fr_cow", 64, 64, pf.fur(_rgb("e0d0b0"), _rgb("9a8460"), 3107, spots=(_rgb("5a3e2a"), 7, 4, 9), shag=10))
    atlas.add("fr_tan", 64, 48, pf.fur(TAN, TAN_DARK, 3108, shag=8))
    atlas.add("fr_skull", 32, 32, pf.skull_face(3112))
    atlas.add("fr_crate", 32, 32, pf.crate_face(_rgb("8a5c34"), _rgb("462c16"), 3113, emblem=lock_emblem))
    atlas.add("fr_shield", 32, 32, paint_shield)
    atlas.add("fr_post", 64, 16, pf.wood(_rgb("5e4430"), _rgb("2e2016"), 3114, plank=16))
    atlas.add("fr_flap", 160, 32, pf.patchwork(_rgb("c2a87c"), 3115, patches=((_rgb("9a7e54"), 5, 4, 8), (_rgb("dccaa4"), 3, 4, 7)), rags=20,
                                               stains=4, shade=(0.9, 1.0)))
    atlas.add("fr_flap_red", 160, 24, pf.patchwork(RED, 3116, patches=((CREAM, 3, 3, 6),), rags=12, shade=(0.85, 0.95)))
    atlas.add("fr_bone", 32, 16, pf.canvas(_rgb("e6dcc4"), 3117, stains=0, shade=(0.92, 1.04), folds=3, fold_k=0.08))
    atlas.add("fr_pelts", 32, 16, paint_pelts)
    atlas.add("fr_ledger", 32, 16, paint_ledger)
    atlas.add("fr_beam", 64, 16, pf.wood(_rgb("76563a"), _rgb("3a2a1a"), 3118, plank=16))
    atlas.add("f_flame", 8, 8, pf.flames(3119))
    if atlas.size != 512:
        raise AssertionError("the atlas grew to %d px: repack the regions" % atlas.size)


# ---------------------------------------------------------------- pieces
def post(shell, det, name, x, z, top, finial="gold", d=0.36):
    """A weathered squared post: a stone-and-wood foot, the post, three iron bands, an iron cap and a pointed finial
    (gold for the front posts, an iron spike for the others); collides from the ground up to the eave."""
    box(shell, name + "_foot", (x - 0.27, 0.0, z - 0.27), (x + 0.27, 0.32, z + 0.27), {"all": "wood_dark", "+2": "end_grain"})
    beam(shell, name, (x, 0.3, z), (x, top, z), d, {"all": "fr_post", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((0.26, 1.35, EAVE - 0.55)):
        box(det, "%s_band_%d" % (name, k), (x - d / 2 - 0.02, y, z - d / 2 - 0.02), (x + d / 2 + 0.02, y + 0.08, z + d / 2 + 0.02), "iron")
    box(shell, name + "_cap", (x - 0.24, top, z - 0.24), (x + 0.24, top + 0.12, z + 0.24), "iron")
    reg = "gold" if finial == "gold" else "black_iron"
    ml.octo(det, name + "_fin", (x, top + 0.12, z), 0.13, 0.14, reg)
    add_cube(det, name + "_fin_tip", (x, top + 0.4, z), ry(math.pi / 4), (0.14, 0.28, 0.14), reg)
    add_cube(det, name + "_fin_point", (x, top + 0.6, z), ry(math.pi / 4), (0.07, 0.12, 0.07), reg)
    collide((x - 0.2, 0.0, z - 0.2, x + 0.2, EAVE, z + 0.2))


def totem(shell, det, name, x, y, z):
    """A little carved wooden totem on a ridge end: a stubby post, a carved head with a beak, a gold tip."""
    box(shell, name, (x - 0.1, y - 0.2, z - 0.1), (x + 0.1, y + 0.36, z + 0.1), {"all": "fr_post", "+2": "end_grain"})
    box(shell, name + "_head", (x - 0.13, y + 0.36, z - 0.13), (x + 0.13, y + 0.6, z + 0.13), {"all": "wood", "+2": "end_grain"})
    box(det, name + "_beak", (x - 0.04, y + 0.42, z + 0.13), (x + 0.04, y + 0.5, z + 0.26), "gold")
    box(det, name + "_eyes", (x - 0.1, y + 0.5, z + 0.131), (x + 0.1, y + 0.54, z + 0.14), "black_iron")
    add_cube(det, name + "_tip", (x, y + 0.66, z), ry(math.pi / 4), (0.08, 0.12, 0.08), "gold")


def pelt_stack(bone, name, foot, w, d, n, yaw=0.0):
    """A stack of n folded pelts (each a little offset and turned), fur bands on the sides."""
    foot = v3(*foot)
    y = 0.0
    for k in range(n):
        th = 0.07 + 0.02 * (k % 2)
        add_cube(bone, "%s_%d" % (name, k), foot + UP * (y + th / 2) + v3(0.02 * math.sin(k * 2.1), 0, 0.02 * math.cos(k * 1.7)),
                 ry(yaw + 0.08 * math.sin(k * 1.9)), (w * (1 - 0.04 * k), th, d * (1 - 0.04 * k)),
                 {"all": "fr_pelts", "+2": ("fr_fur" if k % 2 == 0 else "fr_tan"), "-2": "fr_tan"}, stretch=True)
        y += th
    return y


def roll(bone, name, c, length, r, yaw, region):
    """A rolled pelt lying on its side (two boxes turned 45 degrees about its axis)."""
    c = v3(*c)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(yaw) @ rx(a), (length, 2 * r * 0.83, 2 * r * 0.83), {"all": region, "+1": "fr_pelts", "-1": "fr_pelts"},
                 stretch=True)


def hanging_hide(bone, name, top_a, top_b, length, normal, region, wave=0.07, nx=2, ny=2):
    """A hide hanging from the edge top_a - top_b (nailed to a beam), rippling a little towards `normal`."""
    a, b, n = v3(*top_a), v3(*top_b), norm(v3(*normal))

    def P(s, t):
        return a + (b - a) * s - UP * (length * t) + n * (wave * math.sin(math.pi * t) * (0.6 + 0.4 * math.sin(s * 5.0)) + 0.03)
    loft(bone, name, P, nx, ny, region, th=0.03)


# ---------------------------------------------------------------- the build
def build(atlas, decor):
    rng = random.Random(31)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    # ---- the frame: six posts, eave beams, hip rafters, the ridge pole and its totems
    posts = [(-HW, HD, "gold"), (HW, HD, "gold"), (HW, -HD, "iron"), (-HW, -HD, "iron"), (-HW, 0.0, "iron"), (HW, 0.0, "iron")]
    for k, (x, z, fin) in enumerate(posts):
        post(shell, det, "post_%d" % k, x, z, EAVE + (0.62 if fin == "gold" else 0.5), finial=fin)
    by = EAVE - 0.12
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.24, {"all": "fr_beam", "+1": "end_grain", "-1": "end_grain"}, width=0.22,
             extend=0.2)
    for k, (x, z) in enumerate(corners):
        rx_ = -RL if x < 0 else RL
        beam(shell, "hip_rafter_%d" % k, (x, by + 0.1, z), (rx_, RIDGE - 0.2, 0.0), 0.13, "wood_dark", extend=0.05)
    for k, sx in enumerate((-1, 1)):
        beam(shell, "side_rafter_%d" % k, (sx * HW, by + 0.1, 0.0), (sx * RL, RIDGE - 0.2, 0.0), 0.13, "wood_dark", extend=0.05)
    beam(shell, "ridge_pole", (-RL - 0.1, RIDGE - 0.1, 0), (RL + 0.1, RIDGE - 0.1, 0), 0.18, {"all": "fr_beam", "+1": "end_grain", "-1": "end_grain"})
    for k, sx in enumerate((-1, 1)):
        totem(shell, det, "totem_%d" % k, sx * RL, RIDGE + 0.05, 0.0)
    # ---- the hipped roof: front / back slopes, left / right hips, all sagging; ragged edges
    C = (0.0, 2.0, 0.0)
    P_front = pf.roof_face(shell, "roof_front", (-RL, RIDGE, 0), (RL, RIDGE, 0), (-W, EY, D), (W, EY, D), "fr_roof", nx=6, ny=4, sag=0.26,
                           concave=0.35, folds=3, fold=0.06, centre=C, droop=0.22)
    P_back = pf.roof_face(shell, "roof_back", (RL, RIDGE, 0), (-RL, RIDGE, 0), (W, EY, -D), (-W, EY, -D), "fr_roof", nx=6, ny=4, sag=0.26,
                          concave=0.35, folds=3, fold=0.06, centre=C, droop=0.22)
    P_left = pf.roof_face(shell, "roof_left", (-RL, RIDGE, 0), (-RL, RIDGE, 0), (-W, EY, -D), (-W, EY, D), "fr_roof", nx=4, ny=4, sag=0.2,
                          concave=0.35, centre=C, droop=0.18)
    P_right = pf.roof_face(shell, "roof_right", (RL, RIDGE, 0), (RL, RIDGE, 0), (W, EY, D), (W, EY, -D), "fr_roof", nx=4, ny=4, sag=0.2,
                           concave=0.35, centre=C, droop=0.18)
    pf.flap(shell, "flap_front", P_front, 0.62, "fr_flap", nx=4, out=0.05)
    pf.flap(shell, "flap_back", P_back, 0.42, "fr_flap_red", nx=3)
    pf.flap(shell, "flap_left", P_left, 0.42, "fr_flap_red", nx=3)
    pf.flap(shell, "flap_right", P_right, 0.42, "fr_flap_red", nx=3)
    # ---- the horned skull on the top of the front slope
    pf.bull_skull(shell, det, "skull", (0.45, RIDGE + 0.32, 0.42), facing=(0, 0, 1), s=1.1, tilt=0.32)
    # ---- furs and hides
    # the big white shaggy fur over the front-left corner of the roof, hanging down past the eave
    pf.drape_on(shell, "fur_front", P_front, 0.0, 0.42, 0.3, 1.0, "fr_fur", nx=3, ny=2, lift=0.06, hang=0.6, centre=C)
    pf.drape_on(shell, "fur_hip", P_left, 0.55, 1.0, 0.3, 1.0, "fr_fur", nx=2, ny=2, lift=0.06, hang=0.75, centre=C)
    # a cowhide down the front-left corner, another on the left side, tan hides on the right side and inside
    hanging_hide(shell, "cow_corner", (-W - 0.08, EY - 0.1, D - 0.5), (-W + 0.45, EY - 0.1, D + 0.12), 2.0, (-1, 0, 1), "fr_cow")
    hanging_hide(shell, "cow_left", (-HW - 0.16, by - 0.05, -HD + 0.4), (-HW - 0.16, by - 0.05, -0.4), 2.0, (-1, 0, 0), "fr_cow", nx=3)
    hanging_hide(shell, "tan_left", (-HW - 0.16, by - 0.05, 0.45), (-HW - 0.16, by - 0.05, 1.6), 1.45, (-1, 0, 0), "fr_tan")
    hanging_hide(shell, "tan_right", (HW + 0.16, by - 0.05, -0.45), (HW + 0.16, by - 0.05, -HD + 0.5), 1.55, (1, 0, 0), "fr_tan")
    hanging_hide(shell, "tan_in", (-HW + 0.3, by - 0.16, HD - 0.18), (-HW + 0.95, by - 0.16, HD - 0.18), 0.95, (0, 0, 1), "fr_tan")
    # ---- walls: the back and the back half of the sides; the front halves drawn back as red drapes
    wall_top = by - 0.1
    pf.hang_wall(shell, "wall_back", (-HW, 0, -HD + 0.16), (HW, 0, -HD + 0.16), 0.0, wall_top, -Z, "fr_wall", nx=6)
    collide((-HW, 0.0, -HD + 0.1, HW, wall_top, -HD + 0.22))
    for k, sx in enumerate((-1, 1)):
        x = sx * (HW - 0.16)
        pf.hang_wall(shell, "wall_side_%d" % k, (x, 0, -HD), (x, 0, 0.9), 0.0, wall_top, v3(sx, 0, 0), "fr_wall", nx=5)
        collide((x - 0.06, 0.0, -HD, x + 0.06, wall_top, 0.9))
        pf.tied_drape(shell, det, "drape_%d" % k, (x, wall_top, 0.9), (x, wall_top, HD - 0.25), (x, 1.3, HD - 0.32), (x, 0.03, HD - 0.62),
                      (x, 0.03, HD - 0.2), v3(sx, 0, 0), "fr_drape", nx=3)
    # ---- banners (rune) under the front roof edge, the crossed-axes shield on the left middle post
    for k, bx in enumerate((-HW + 0.95, HW - 0.95)):
        ml.banner(shell, "banner_%d" % k, (bx, EY - 0.1, D + 0.1), 0.9, 1.75, normal=(0, 0, 1), region="fr_banner", rod=True, rod_region="wood_dark",
                  knobs="gold")
    ml.plate(shell, "shield", (-HW - 0.24, 2.1, 0.0), 0.8, 0.8, "fr_shield", normal=(-1, 0, 0), th=0.05)
    add_cube(det, "shield_boss", (-HW - 0.3, 2.1, 0.0), EYE, (0.06, 0.16, 0.16), "iron")
    # ---- lantern on an iron arm on the front-right post (outer side), guy ropes and pegs, leaning spears
    pf.lantern_arm(shell, det, "lamp_fr", (HW + 0.2, 2.75, HD), (1, 0, 0), drop=0.5, size=0.4)
    for k, (top, peg) in enumerate((((-HW, EAVE + 0.3, -HD), (-HW - 1.85, 0.0, -HD - 0.3)), ((-HW, EAVE + 0.3, 0.0), (-HW - 1.95, 0.0, 0.35)),
                                     ((HW, EAVE + 0.3, -HD), (HW + 1.6, 0.0, -HD - 0.3)), ((HW, EAVE + 0.4, HD), (HW + 1.25, 0.0, HD + 0.6)))):
        pf.guy(det, "guy_%d" % k, top, peg, sag=0.05, d=0.06)
    pf.leaning_pole(shell, "spear_0", (-HW - 1.5, 0.0, -HD + 0.85), (-HW - 0.22, 3.0, -HD + 0.65), d=0.08, wrap="leather", head="steel")
    pf.leaning_pole(shell, "staff_1", (-HW - 1.25, 0.0, -0.75), (-HW - 0.22, 2.6, -0.42), d=0.08, wrap="leather_dark")
    ml.lantern(shell, "lamp_in", (-0.6, 2.7, -0.1), size=0.34, metal="iron", chain_to=(-0.6, RIDGE - 0.18, 0.0))
    # ---- inside: the back shelves (candle lanterns, pelts, horns, jars)
    sx0, sx1 = -HW + 0.75, HW - 0.75
    levels = ml.shelf_unit(shell, "shelves", sx0, sx1, SHELF_Z[0], SHELF_Z[1], levels=(0.55, 1.15, 1.75), h=2.25, back=True, uprights=4, detail=det)
    lv = sorted(levels, key=lambda s: s[2])
    zc = (SHELF_Z[0] + SHELF_Z[1]) / 2
    for i, x in enumerate((-1.75, -0.25, 1.25)):
        ml.lantern(shell, "shelf_lamp_%d" % i, (x, 2.25 + 0.16, zc), size=0.22, metal="iron")
    for i, x in enumerate((-2.2, -1.0, 0.5, 2.0)):
        pf.candle(det, "candle_%d" % i, (x, lv[2][2], zc + 0.05), h=0.16)
    for i, x in enumerate((-1.15, 0.45, 2.05)):   # candle lanterns on the middle shelf too (the warm back of the picture)
        ml.lantern(shell, "shelf_lamp_mid_%d" % i, (x, lv[1][2] + 0.14, zc + 0.03), size=0.2, metal="iron")
    for i, x in enumerate((-1.9, 1.7)):           # two lanterns hanging from the back beam above the shelves
        ml.lantern(shell, "back_lamp_%d" % i, (x, 2.62, -HD + 0.55), size=0.3, metal="iron", chain_to=(x, by - 0.1, -HD + 0.55))
    x0, x1, y2, _, _ = lv[2]
    for i, x in enumerate((-1.45, 0.15, 1.6)):
        roll(det, "roll_hi_%d" % i, (x, y2 + 0.08, zc), 0.5, 0.08, 0.0, ("fr_fur", "fr_tan", "fr_cow")[i])
    x0, x1, y1, _, _ = lv[1]
    pelt_stack(det, "shelf_pelts_0", (-1.8, y1, zc), 0.6, 0.3, 4)
    pelt_stack(det, "shelf_pelts_1", (1.0, y1, zc), 0.55, 0.3, 3)
    for i, (x, col) in enumerate(((-0.7, "green"), (-0.45, "red"), (1.9, "yellow"))):
        ml.bottle(det, "jar_%d" % i, (x, y1, zc), col, r=0.07, h=0.18, shape="tall")
    x0, x1, y0, _, _ = lv[0]
    pelt_stack(det, "shelf_pelts_2", (-1.4, y0, zc), 0.7, 0.32, 5)
    pelt_stack(det, "shelf_pelts_3", (0.2, y0, zc), 0.6, 0.32, 4)
    for i, x in enumerate((1.35, 1.9)):   # little horns lying on the low shelf
        beam(det, "shelf_horn_%d" % i, (x - 0.18, y0 + 0.05, zc), (x + 0.15, y0 + 0.16, zc + 0.04), 0.07, "fr_bone")
    # ---- the counter: stacked furs, a ledger, a coin box, a pile of books (mod)
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    yt = top[1]
    zc = (cz0 + cz1) / 2
    box(shell, "counter_fur", (cx0 + 0.05, yt, cz0 + 0.02), (cx0 + 1.0, yt + 0.025, cz1 + 0.12), {"all": "fr_fur"}, stretch=True)
    ml.plate(shell, "counter_fur_hang", (cx0 + 0.5, yt - 0.25, cz1 + 0.13), 0.95, 0.5, "fr_fur", normal=(0, 0, 1), th=0.02)
    pelt_stack(det, "counter_pelts", (cx0 + 0.45, yt + 0.025, zc - 0.05), 0.55, 0.42, 4, yaw=0.15)
    ml.plate(det, "ledger", (0.95, yt + 0.02, zc + 0.05), 0.42, 0.28, "fr_ledger", normal=(0, 1, 0), up=(0, 0, -1), th=0.02)
    box(det, "coin_box", (1.55, yt, zc - 0.12), (1.85, yt + 0.16, zc + 0.08), {"all": "crate", "+2": "gold_ingot"})
    decor.block("farmhouse_decorations:pile_of_books", 2.3, yt, zc, facing="front", fallback="leather", solid=False)
    roll(det, "counter_roll", (0.3, yt + 0.1, zc - 0.1), 0.5, 0.1, 0.3, "fr_cow")
    # ---- the weapon rack along the left wall (axes and spears)
    rxw = -HW + 0.55
    ml.weapon_rack(shell, "rack", (rxw, 0.0, -HD + 0.95), (rxw, 0.0, 0.3), h=1.8, normal=(1, 0, 0), items=("axe", "spear", "axe", "axe", "spear"),
                   detail=det)
    # ---- the right inside: a lying barrel (mod), a sack (mod), a low pile of hides
    decor.block("landsoficaria:loaded_cypress_barrel", HW - 0.75, 0.0, -0.75, facing="front", scale=0.85, alt="minecraft:barrel", fallback="barrel")
    decor.block("farmersdelight:rice_bag", HW - 0.75, 0.0, 1.2, facing="neg_x", scale=0.7, fallback="sack")
    pelt_stack(shell, "floor_pelts", (HW - 0.8, 0.0, 0.25), 0.7, 0.6, 5, yaw=0.2)
    collide((HW - 1.15, 0.0, -0.1, HW - 0.45, 0.4, 0.6))
    # ---- the rug with cream rings in the open front
    ml.rug(shell, "rug", -1.9, 2.1, 0.35, 3.25, y=0.0, region="fr_rug")
    # ---- outside along the left side: crates, barrel, the chest with the ledger, a chopping block with an axe
    ox = -HW - 0.8
    decor.block("furnish:spruce_crate", ox, 0.0, -HD + 1.2, facing="neg_x", scale=0.8, alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "crate_l", (ox, 0.0, -0.45), size=(0.88, 0.82, 0.88), yaw=0.0, region="fr_crate", top="crate_top")
    ml.barrel(shell, "barrel_l", (ox - 0.2, 0.0, 0.62), r=0.33, h=0.86)
    pf.iron_chest(shell, det, "chest", (ox, 0.0, 1.85), w=1.15, d=0.75, h=0.8, yaw=-math.pi / 2, face="fr_crate", wood_reg="crate")
    ml.plate(det, "chest_ledger", (ox, 0.84, 1.85), 0.56, 0.4, "fr_ledger", normal=(0, 1, 0), up=(1, 0, 0), th=0.03)
    box(det, "chest_ledger_cover", (ox - 0.2, 0.8, 1.6), (ox + 0.2, 0.83, 2.1), "leather_dark")
    ml.octo(shell, "block", (ox + 0.1, 0.0, HD + 0.2), 0.26, 0.5, {"all": "wood", "+2": "end_grain"})
    collide((ox - 0.15, 0.0, HD - 0.05, ox + 0.35, 0.5, HD + 0.45))
    ml.axe(det, "block_axe", (ox + 0.3, 0.48, HD + 0.2), up=(0.5, 0.86, 0.1), facing=(0, 0, 1), length=0.75)
    # ---- outside right: a crate topped with fur bundles
    ml.crate(shell, "crate_r", (HW + 0.8, 0.0, HD - 0.6), size=(0.8, 0.76, 0.8), yaw=0.1, region="fr_crate", top="crate_top")
    roll(det, "crate_r_roll_0", (HW + 0.8, 0.86, HD - 0.65), 0.6, 0.11, 0.1, "fr_fur")
    roll(det, "crate_r_roll_1", (HW + 0.78, 0.86, HD - 0.41), 0.55, 0.09, 0.2, "fr_tan")
    return root


def item_icon(path):
    """16x16: a red hipped tent with a white fur on its left corner and the horned skull on top."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, dark, fur, bone, wood = RED, RED_DARK, FUR, (232, 222, 196), (90, 64, 40)
    for y in range(4, 11):
        half = 3 + (y - 4) * 0.8
        for x in range(16):
            if abs(x - 7.5) <= half:
                p[x, y] = (red if (x + y) % 5 else dark) + (255,)
    for y in range(6, 12):
        for x in range(1, 6 - (y - 6) // 2):
            p[x, y] = fur + (255,)
    for y in range(11, 16):
        for x in (2, 13):
            p[x, y] = wood + (255,)
        for x in range(3, 13):
            p[x, y] = (40, 26, 18, 255)
    for x in range(5, 11):
        p[x, 15] = (150, 40, 30, 255)
    for x, y in ((7, 3), (8, 3), (7, 4), (8, 4), (5, 2), (10, 2), (4, 1), (11, 1)):
        p[x, y] = bone + (255,)
    p[9, 12] = p[9, 13] = (150, 36, 30, 255)
    im.save(path)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    add_regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)


if __name__ == "__main__":
    main()
