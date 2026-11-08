#!/usr/bin/env python3
"""tente_imperiale — Tente marchande impériale / Imperial Merchant Tent (1.26.0, Lion Port market, group A; reference
scratchpad/ref2/tente_imperiale_ref.png, the top-left tent of the board tentes_065_planche.png).

A tall, rich blue and cream marquee, one block (TentType group "tents"), about 9 x 7.5 blocks (crates, chests and the
rug included), the back flag at about 8.3:

  - a steep bell-shaped marquee roof (wide cream and blue gores with gold seams) rising to a tall gold finial with a
    small blue pennant; gold spike finials on the four corner posts above the roof corners; a small gold crown on the
    front-right hip;
  - a GOLD VALANCE all round (blue fleurs-de-lis between gold rules, square gold teeth), a worn cream under-valance in
    rags along the front;
  - three blue LION BANNERS: a long one hanging down each side near the front, and a shorter one with a gold fringe in
    front, off the centre; blue curtains drawn back at the entrance;
  - LANTERNS on iron brackets off the two front posts; a FLAG POLE rising behind the back-right corner from a stepped
    wooden base, flying the blue and gold swallow-tailed flag with a cross;
  - inside: two counters (gold candlesticks, a goblet, books, small chests, scrolls, a little gold lion) with the
    merchant's place behind the left one, the back shelves of gold plates, jars and books, blue walls;
  - outside: a stack of crates on the left, the pale stone strongbox with gold clasps and a gold helm on it, the golden
    horse figurine, a lance leaning on the left post with a guy rope, the chest with the gold cross on the right with
    scrolls and books on it, the blue RUG with the golden lion medallion in front of the entrance.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the left counter (NPC_SPOT); players walk in by the
entrance and the gap between the two counters. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_imperiale.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_imperiale.json, models/entity + blockbench/tente_imperiale.bbmodel,
textures/entity/tente_imperiale.png, textures/item/tente_imperiale.png, interiors/tente_imperiale_decor.json.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_a as pa  # noqa: E402

ml = pa.ml
np = pa.np
v3, norm, add_cube, beam, loft, Bone = pa.v3, pa.norm, pa.add_cube, pa.beam, pa.loft, pa.Bone
EYE, UP, X, Z = pa.EYE, pa.UP, pa.X, pa.Z
ry, rx, rz = pa.ry, pa.rx, pa.rz
box, collide = pa.box, pa.collide
BLUE, CREAM, GOLD = pa.BLUE, pa.CREAM, pa.GOLD

NAME = "tente_imperiale"
# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 3.0, 2.7            # corner posts
EAVE = 3.5                   # top of the eave beams
EY = 3.55                    # the roof's lower edge
AY = 6.1                     # the roof's apex
W, D = HW + 0.3, HD + 0.3
BULGE = 0.22                 # the eaves bow out between the corners: a rounder marquee
FLAG_X, FLAG_Z, FLAG_TOP = HW + 0.15, -HD - 0.15, 7.7
COUNTER_L = (-2.5, -0.6, 0.0, 0.6)    # x0, x1, z0, z1
COUNTER_R = (0.6, 2.5, 0.0, 0.6)
COUNTER_H = 1.0
NPC_SPOT = (-1.85, -1.25)    # (x0, z0) of the free 1 x 1 x 2.2 place behind the left counter (the merchant)


def imperial_flag(seed):
    """The back flag: blue, a gold border, a gold saltire with a cross, a swallow tail (cut out), along u."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        pa.weave(img, BLUE, rng)
        px = img.load()
        for y in range(h):
            for x in range(w):
                t = x / w
                cy = abs(y + 0.5 - h / 2)
                if t > 0.72 and cy < (t - 0.72) / 0.28 * (h * 0.45):
                    px[x, y] = pa.CLEAR
                elif cy > h / 2 - 2.5 or x < 2:
                    px[x, y] = pa._jitter(GOLD, rng, 8) + (255,)
                elif t < 0.72 and (abs((x - 0.36 * w) / (0.36 * w) - (y - h / 2) / (h / 2)) < 0.12 or
                                   abs((x - 0.36 * w) / (0.36 * w) + (y - h / 2) / (h / 2)) < 0.12):
                    px[x, y] = pa._jitter(GOLD, rng, 10) + (255,)
                elif cy < 1.5 and t < 0.72:
                    px[x, y] = pa._jitter(pa.GOLD_L, rng, 10) + (255,)
    return p


def stone_chest(seed):
    """The strongbox: pale dressed stone, darker joints, gold corner clasps."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        base = pa._rgb("d2cbbd")
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                c = pa._scale(base, 0.7) if e == 0 else base
                if (y % 10 == 0) or ((x + (y // 10) * 7) % 14 == 0):
                    c = pa._scale(base, 0.82)
                if (x < 5 or x >= w - 5) and (y < 5 or y >= h - 5) and e > 0:
                    c = GOLD
                px[x, y] = pa._jitter(c, rng, 6) + (255,)
    return p


def regions(atlas):
    pa.add_regions(atlas, "im", [
        ("roof", 128, 96, pa.stripes([CREAM, BLUE], 4, 6501, seam=GOLD, fold=0.15)),
        ("rug", 96, 128, pa.rug(6502, medallion="lion")),
        ("banner", 40, 112, pa.banner(6503, emblem="lion", bottom="point", box=(0.12, 0.1, 0.88, 0.5))),
        ("banner_c", 40, 72, pa.banner(6504, emblem="lion", bottom="pointfringe", box=(0.12, 0.1, 0.88, 0.6))),
        ("wall", 128, 64, pa.plain(6505, pa._scale(BLUE, 0.85), folds=8, depth=0.22)),
        ("curtain", 48, 64, pa.plain(6506, BLUE, folds=4, depth=0.24)),
        ("flag", 96, 40, imperial_flag(6507)),
        ("pennant", 48, 16, pa.lion_flag(6508, tail=True)),
        ("valance", 256, 32, pa.gold_valance(10, 6509)),
        ("rags", 128, 24, pa.torn_valance(6510)),
        ("stone", 32, 32, pa.stone(6511)),
        ("strongbox", 32, 32, stone_chest(6512)),
        ("chest", 32, 32, pa.chest_wood(6513, base=pa._rgb("6e4220"))),
        ("cross_plate", 16, 16, pa.banner(6514, field=pa._rgb("6e4220"), border=pa._rgb("6e4220"), emblem="cross", bottom="flat",
                                         box=(0.05, 0.05, 0.95, 0.95), fold=False)),
        ("books", 64, 16, pa.books(6515)),
        ("post", 64, 16, pa.post_wood(6516, base=pa._rgb("7a4a24"))),
        ("roll_c", 16, 16, pa.roll_end(6517, pa.CREAM_D, core=pa._rgb("8a6a40"))),
    ])


def candlestick(bone, name, foot, h=0.32):
    f = v3(*foot)
    pa.ml.octo(bone, name + "_base", f, 0.07, 0.04, "gold")
    add_cube(bone, name + "_stem", f + UP * (h / 2), EYE, (0.035, h, 0.035), "gold")
    add_cube(bone, name + "_cup", f + UP * h, EYE, (0.08, 0.04, 0.08), "gold")
    add_cube(bone, name + "_candle", f + UP * (h + 0.07), EYE, (0.04, 0.1, 0.04), "wax")
    add_cube(bone, "glow_" + name + "_flame", f + UP * (h + 0.15), ry(math.pi / 4), (0.025, 0.05, 0.025), "flame")


def horse(bone, name, foot, s=1.0, yaw=0.0):
    """A golden horse figurine (a chess knight): a round plinth, the neck rising forward, the head bent down, the mane."""
    f = v3(*foot)
    R = ry(yaw)
    pa.ml.octo(bone, name + "_plinth", f, 0.24 * s, 0.12 * s, "gold", yaw=yaw)
    pa.ml.octo(bone, name + "_plinth2", f + UP * 0.12 * s, 0.19 * s, 0.08 * s, "gold", yaw=yaw)
    add_cube(bone, name + "_chest", f + UP * 0.35 * s, R, (0.24 * s, 0.3 * s, 0.3 * s), "gold")
    add_cube(bone, name + "_neck", f + R @ v3(0, 0.6 * s, 0.05 * s), R @ rx(-0.35), (0.2 * s, 0.34 * s, 0.22 * s), "gold")
    add_cube(bone, name + "_head", f + R @ v3(0, 0.76 * s, 0.17 * s), R @ rx(0.5), (0.17 * s, 0.14 * s, 0.32 * s), "gold")
    add_cube(bone, name + "_mane", f + R @ v3(0, 0.66 * s, -0.08 * s), R @ rx(-0.3), (0.08 * s, 0.36 * s, 0.08 * s), "trim_gold")
    for k, sx in enumerate((-0.05, 0.05)):
        add_cube(bone, "%s_ear_%d" % (name, k), f + R @ v3(sx * s, 0.88 * s, 0.07 * s), R, (0.04 * s, 0.08 * s, 0.04 * s), "gold")


def build(atlas, decor):
    rng = random.Random(65)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    PR = dict(stone_region="im_stone", post_region="im_post")
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]
    for k, (x, z) in enumerate(corners):
        pa.post(shell, det, "post_%d" % k, x, z, EY + 0.3, d=0.4, stone_w=0.6, stone_h=0.42, bands=(1.3, 2.6), cap=0.5, cap_region="gold",
                finial="big", collide_top=EAVE, **PR)
    by = EAVE - 0.15
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.32, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.28, extend=0.12)
    for k, (p, q) in enumerate((((-HW + 0.18, EAVE - 1.15, HD), (-HW + 0.95, by - 0.1, HD)), ((HW - 0.18, EAVE - 1.15, HD), (HW - 0.95, by - 0.1, HD)))):
        beam(shell, "brace_%d" % k, p, q, 0.15, "wood_dark", extend=0.05)
    beam(shell, "tie_beam", (-HW, by, -0.3), (HW, by, -0.3), 0.2, "wood_dark", extend=0.1)
    beam(shell, "king_post", (0, by, -0.3), (0, AY - 0.2, 0), 0.18, "wood_dark")
    # ---- the steep marquee roof, gold seams, the hip cords, the apex finial and its pennant
    pa.hip_roof(shell, "roof", (0, AY, 0), [(-W, EY, D), (W, EY, D), (W, EY, -D), (-W, EY, -D)], "im_roof", nx=4, ny=8, a=0.3, droop=0.12, bulge=BULGE)
    for k, (cx, cz) in enumerate(((-W, D), (W, D), (W, -D), (-W, -D))):
        pts = [v3(cx * (i / 5), AY - (AY - EY) * pa.bell(i / 5, 0.3) + 0.04, cz * (i / 5)) for i in range(6)]
        for i in range(5):
            beam(det, "hip_%d_%d" % (k, i), pts[i], pts[i + 1], 0.07, "gold", width=0.1, extend=0.03)
        if k == 1:   # the small gold crown on the front-right hip
            c = pts[3] + v3(0, 0.1, 0)
            pa.ml.octo(shell, "crown_band", c, 0.17, 0.12, "gold")
            for j in range(5):
                a = j * 2 * math.pi / 5
                add_cube(det, "crown_pt_%d" % j, c + v3(math.cos(a) * 0.14, 0.18, math.sin(a) * 0.14), ry(math.pi / 4), (0.05, 0.12, 0.05), "gold")
    box(shell, "apex_collar", (-0.2, AY - 0.1, -0.2), (0.2, AY + 0.14, 0.2), "gold", stretch=False)
    beam(shell, "apex_pole", (0, AY + 0.1, 0), (0, AY + 1.05, 0), 0.07, "wood_dark")
    pa.finial_spike(shell, "apex_finial", (0, AY + 0.05, 0), h=0.9, w=0.3)

    def PF(s, t):
        return v3(0.05 + 1.2 * s, AY + 1.0 - 0.36 * t - 0.12 * s, 0.12 * math.sin(s * math.pi * 1.5))
    loft(shell, "apex_pennant", PF, 3, 1, "im_pennant", th=0.02)
    # ---- the gold valance all round, the cream rags under the front one
    for k, (c0, c1, o) in enumerate((((-W, EY, D + 0.02), (W, EY, D + 0.02), Z), ((W + 0.02, EY, D), (W + 0.02, EY, -D), X),
                                     ((W, EY, -D - 0.02), (-W, EY, -D - 0.02), -Z), ((-W - 0.02, EY, -D), (-W - 0.02, EY, D), -X))):
        pa.valance(shell, "valance_%d" % k, c0, c1, o, h=0.72, region="im_valance", segs=6, sag=0.03, flare=0.05, bulge=BULGE)
    pa.valance(shell, "rags", (-HW + 0.3, EY - 0.62, D - 0.12), (HW - 0.3, EY - 0.62, D - 0.12), Z, h=0.5, region="im_rags", segs=4, flare=0.02,
               bulge=BULGE * 0.8)
    # ---- banners: long ones down the two sides near the front, the fringed one in front off the centre
    ml.banner(shell, "banner_l", (-W - 0.12 - BULGE * math.sin(math.pi * (1.3 + D) / (2 * D)), EY - 0.05, 1.3), 1.0, 3.0, normal=(-1, 0, 0), region="im_banner", rod=True, wave=0.04, rod_region="gold")
    ml.banner(shell, "banner_r", (W + 0.12 + BULGE * math.sin(math.pi * (1.3 + D) / (2 * D)), EY - 0.05, 1.3), 1.0, 3.0, normal=(1, 0, 0), region="im_banner", rod=True, wave=0.04, rod_region="gold")
    ml.banner(shell, "banner_c", (0.65, EY - 0.05, D + 0.12 + BULGE * math.sin(math.pi * (0.65 + W) / (2 * W))), 1.05, 1.85, normal=(0, 0, 1), region="im_banner_c", rod=True, wave=0.03, rod_region="gold")
    # ---- walls (blue), curtains drawn back at the entrance
    pa.wall(shell, "wall_back", (-HW, 0, -HD - 0.06), (HW, 0, -HD - 0.06), 0.0, by - 0.15, -Z, "im_wall", nx=8)
    collide((-HW, 0.0, -HD - 0.12, HW, by - 0.15, -HD))
    for k, sx in enumerate((-1, 1)):
        x = sx * (HW + 0.06)
        a, b = (x, 0, -HD), (x, 0, 0.9)
        if sx > 0:
            a, b = b, a
        pa.wall(shell, "wall_side_%d" % k, a, b, 0.0, by - 0.15, v3(sx, 0, 0), "im_wall", nx=6)
        collide((x - 0.06, 0.0, -HD, x + 0.06, by - 0.15, 0.9))
        pa.drape_tied(shell, det, "curtain_side_%d" % k, (x, by - 0.12, 0.95), (x, by - 0.12, HD - 0.3), (x - sx * 0.02, 1.4, HD - 0.45),
                      (x, 0.03, HD - 0.75), (x, 0.03, HD - 0.3), v3(sx, 0, 0), "im_curtain", nx=2)
        xa, xb = sx * (HW - 0.3), sx * (HW - 1.35)
        pa.drape_tied(shell, det, "curtain_front_%d" % k, (xa, by - 0.15, HD - 0.12), (xb, by - 0.15, HD - 0.12), (sx * (HW - 0.4), 1.3, HD - 0.16),
                      (sx * (HW - 0.3), 0.03, HD - 0.16), (sx * (HW - 0.95), 0.03, HD - 0.16), Z, "im_curtain", nx=3)
    # ---- lanterns on iron brackets off the front posts
    pa.lantern_bracket(det, shell, "lamp_l", (-HW + 0.2, 2.95, HD + 0.1), (1, 0, 0.35), y_drop=0.6, size=0.46, arm=0.55)
    pa.lantern_bracket(det, shell, "lamp_r", (HW + 0.2, 2.95, HD), (1, 0, 0.1), y_drop=0.6, size=0.46, arm=0.6)
    # ---- the flag pole behind the back-right corner, its stepped base
    box(shell, "flag_base", (FLAG_X - 0.3, EY - 0.3, FLAG_Z - 0.3), (FLAG_X + 0.3, EY + 0.25, FLAG_Z + 0.3), {"all": "wood", "+2": "end_grain"}, stretch=False)
    box(shell, "flag_base2", (FLAG_X - 0.22, EY + 0.25, FLAG_Z - 0.22), (FLAG_X + 0.22, EY + 0.45, FLAG_Z + 0.22), "wood_dark", stretch=False)
    box(det, "flag_base_band", (FLAG_X - 0.31, EY - 0.05, FLAG_Z - 0.31), (FLAG_X + 0.31, EY + 0.05, FLAG_Z + 0.31), "gold", stretch=False)
    beam(shell, "flag_pole", (FLAG_X, EY + 0.45, FLAG_Z), (FLAG_X, FLAG_TOP, FLAG_Z), 0.13, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    pa.finial_spike(shell, "flag_finial", (FLAG_X, FLAG_TOP, FLAG_Z), h=0.42, w=0.18)
    box(det, "flag_ring", (FLAG_X - 0.1, FLAG_TOP - 1.0, FLAG_Z - 0.1), (FLAG_X + 0.1, FLAG_TOP - 0.92, FLAG_Z + 0.1), "gold", stretch=False)

    def FF(s, t):
        return v3(FLAG_X + 0.07 + 1.9 * s, FLAG_TOP - 0.1 - 0.85 * t - 0.15 * s + 0.07 * math.sin(s * math.pi * 2.2),
                  FLAG_Z + 0.2 * math.sin(s * math.pi * 1.3))
    loft(shell, "flag", FF, 5, 1, "im_flag", th=0.025)
    # ---- inside: the two counters and their goods, the back shelves
    for side, (cx0, cx1, cz0, cz1) in (("l", COUNTER_L), ("r", COUNTER_R)):
        top = ml.counter(shell, "counter_" + side, cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
        y = top[1]
        ml.table_cloth(shell, "cloth_" + side, cx0 + 0.15, cx1 - 0.15, cz0 - 0.02, cz1 + 0.02, y, hang=0.3, region="cloth", edge="cloth_hang")
        y += 0.015
        if side == "l":
            candlestick(det, "candle_l0", (cx0 + 0.25, y, cz0 + 0.3))
            pa.chest(shell, det, "casket_l", (cx0 + 0.75, y, cz0 + 0.3), w=0.4, d=0.28, h=0.26, region="im_chest", solid=False)
            pa.book_stack(det, "books_l", (cx0 + 1.25, y, cz0 + 0.3), n=3, rng=rng)
            add_cube(det, "goblet_l", (cx1 - 0.25, y + 0.1, cz0 + 0.3), EYE, (0.08, 0.2, 0.08), "gold")
            add_cube(det, "goblet_l_cup", (cx1 - 0.25, y + 0.22, cz0 + 0.3), EYE, (0.13, 0.08, 0.13), "gold")
        else:
            horse(det, "statuette", (cx0 + 0.3, y, cz0 + 0.3), s=0.42, yaw=-0.4)
            pa.cloth_roll(det, "scroll_r0", (cx0 + 0.85, y + 0.06, cz0 + 0.25), length=0.45, r=0.055, yaw=0.3, region="cloth_beige", end="im_roll_c")
            pa.cloth_roll(det, "scroll_r1", (cx0 + 0.9, y + 0.17, cz0 + 0.3), length=0.45, r=0.055, yaw=0.1, region="cloth_beige", end="im_roll_c")
            pa.chest(shell, det, "casket_r", (cx0 + 1.35, y, cz0 + 0.3), w=0.4, d=0.28, h=0.26, region="im_chest", solid=False)
            candlestick(det, "candle_r0", (cx1 - 0.2, y, cz0 + 0.3))
    levels = ml.shelf_unit(shell, "shelves", -HW + 0.4, HW - 0.4, -HD + 0.12, -HD + 0.6, levels=(0.55, 1.15, 1.75, 2.35), h=2.65, back=True,
                           uprights=5, detail=det)
    for j, (x0, x1, yy, zf, zb) in enumerate(sorted(levels, key=lambda s: s[2])):
        zc = (zf + zb) / 2
        if j == 0:
            for i in range(4):
                pa.chest(shell, det, "shelf_chest_%d" % i, (x0 + 0.5 + i * 1.35, yy, zc), w=0.5, d=0.32, h=0.3, region="im_chest", solid=False)
        elif j == 1:
            for i in range(8):   # gold plates standing on edge
                pa.plate(det, "plate_%d" % i, (x0 + 0.3 + i * 0.68, yy + 0.16, zc - 0.08), 0.3, 0.3, "gold", normal=(0, 0, 1), th=0.02)
        elif j == 2:
            pa.book_row(det, "sbooks_0", x0 + 0.1, x0 + 1.6, yy, zc, h=0.3, region="im_books")
            pa.potion_row(det, "spots", x0 + 2.1, x1 - 0.2, yy, zc, ("red", "blue", "purple", "yellow"), rng, n=12)
        else:
            for i in range(6):
                candlestick(det, "scandle_%d" % i, (x0 + 0.4 + i * 0.95, yy, zc), h=0.22)
    # ---- the rug with the golden lion medallion
    ml.rug(shell, "rug", -1.55, 2.25, 1.45, 4.45, y=0.0, region="im_rug")
    # ---- outside left: crates, the stone strongbox with a gold helm, the golden horse, the lance and its guy rope
    decor.block("furnish:dark_oak_crate", -4.05, 0.0, 1.45, facing="front", alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "crate_l_top", (-4.05, 1.0, 1.45), size=0.66, yaw=0.12, solid=True)
    ml.crate(shell, "crate_l_side", (-4.05, 0.0, 0.45), size=(0.8, 0.62, 0.7), yaw=-0.08, solid=True)
    ml.crate(det, "crate_l_small", (-4.15, 0.62, 0.45), size=(0.4, 0.3, 0.36), yaw=0.3, solid=False)
    sb = v3(-2.2, 0.0, 3.25)
    box(shell, "strongbox", (sb[0] - 0.5, 0.0, sb[2] - 0.36), (sb[0] + 0.5, 0.72, sb[2] + 0.36), {"all": "im_strongbox"}, solid=True)
    box(shell, "strongbox_lid", (sb[0] - 0.54, 0.72, sb[2] - 0.4), (sb[0] + 0.54, 0.84, sb[2] + 0.4), {"all": "im_strongbox"})
    box(det, "strongbox_clasp", (sb[0] - 0.08, 0.45, sb[2] + 0.36), (sb[0] + 0.08, 0.7, sb[2] + 0.4), "gold", stretch=False)
    hc = sb + v3(0, 0.84, 0)
    pa.ml.octo(shell, "helm", hc, 0.2, 0.3, "gold")
    add_cube(det, "helm_top", hc + UP * 0.34, ry(math.pi / 4), (0.22, 0.1, 0.22), "gold")
    add_cube(det, "helm_slit", hc + v3(0, 0.2, 0.2), EYE, (0.24, 0.04, 0.03), "black_iron")
    add_cube(det, "helm_crest", hc + v3(0, 0.45, -0.02), EYE, (0.04, 0.16, 0.28), "cloth_blue")
    horse(shell, "horse", (-1.1, 0.0, 3.35), s=1.05, yaw=0.5)
    collide((-1.38, 0.0, 3.08, -0.82, 0.95, 3.62))
    ml.spear(det, "lance", (-HW - 0.6, 0.0, HD + 0.55), up=norm(v3(0.18, 1.0, -0.12)), length=3.2)
    ml.rope(det, "guy_l", (-HW - 0.05, EY + 0.2, HD + 0.05), (-HW - 1.4, 0.05, HD + 1.0), d=0.05, sag=0.08, segs=3)
    ml.rope(det, "guy_r", (HW + 0.05, EY + 0.2, HD + 0.05), (HW + 1.3, 0.05, HD + 0.9), d=0.05, sag=0.08, segs=3)
    for k, (x, z) in enumerate(((-HW - 1.4, HD + 1.0), (HW + 1.3, HD + 0.9))):
        box(det, "peg_%d" % k, (x - 0.06, 0.0, z - 0.06), (x + 0.06, 0.3, z + 0.06), {"all": "wood", "+2": "end_grain"}, stretch=False)
    # ---- outside right: the chest with the gold cross, scrolls and books on it
    ch = v3(3.95, 0.0, 2.25)
    pa.chest(shell, det, "cross_chest", ch, w=0.95, d=0.62, h=0.72, region="im_chest", trim="black_iron")
    pa.plate(det, "cross_chest_emblem", ch + v3(0, 0.38, 0.33), 0.3, 0.3, "im_cross_plate", normal=(0, 0, 1), th=0.01)
    pa.plate(det, "cross_chest_gold", ch + v3(0, 0.38, 0.336), 0.22, 0.22, "gold", normal=(0, 0, 1), th=0.004)
    pa.book_stack(det, "chest_books", ch + v3(-0.2, 0.74, 0), n=3, rng=rng)
    pa.cloth_roll(det, "chest_scroll_0", ch + v3(0.22, 0.8, -0.05), length=0.5, r=0.06, yaw=0.2, region="cloth_beige", end="im_roll_c")
    pa.cloth_roll(det, "chest_scroll_1", ch + v3(0.25, 0.8, 0.12), length=0.5, r=0.06, yaw=-0.1, region="cloth_beige", end="im_roll_c")
    decor.block("landsoficaria:blue_storage_vase", 3.95, 0.0, 1.05, facing="front", alt="minecraft:decorated_pot", fallback="cloth_blue")
    return root


def item_icon(path):
    """16x16: a tall blue / cream marquee, gold valance, gold finials, a blue lion banner in front."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    for y in range(1, 9):
        half = 0.6 + (y - 1) * 0.92
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                stripe = int((dx / max(half, 0.5)) * 2 + 2) % 2
                p[x, y] = (CREAM if stripe == 0 else BLUE) + (255,)
    p[7, 0] = p[8, 0] = GOLD + (255,)
    for x in range(0, 16):
        p[x, 9] = GOLD + (255,)
        if x % 2 == 0:
            p[x, 10] = GOLD + (255,)
    for x in (0, 15):
        p[x, 8] = GOLD + (255,)
        for y in range(9, 16):
            p[x, y] = (110, 70, 36, 255)
    for y in range(10, 15):
        for x in range(1, 15):
            if p[x, y][3] == 0:
                p[x, y] = (36, 30, 50, 255)
    for y in range(10, 14):
        for x in range(8, 11):
            p[x, y] = BLUE + (255,)
    p[9, 11] = GOLD + (255,)
    p[9, 14] = BLUE + (255,)
    for x in range(1, 15):
        p[x, 15] = (BLUE if 4 <= x <= 11 else (90, 70, 45)) + (255,)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    pa.setup(NAME)
    atlas = ml.Atlas(NAME, colour="blue")
    regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)
    print("atlas", atlas.size, "NPC spot", NPC_SPOT)


if __name__ == "__main__":
    main()
