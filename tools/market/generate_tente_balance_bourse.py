#!/usr/bin/env python3
"""tente_balance_bourse — Tente à la balance et à la bourse / Scales and Purse Tent (1.26.0, market tents group C;
reference: scratchpad/ref2/tente_balance_bourse_ref.png, picture 154).

A long red-and-cream striped marquee, one block (TentType group "tents"), about 9.5 blocks wide (the left porch and the
purse sign included) and 7 deep (the rug in front), the cross finial at about 7. Not the camp's tente_marchande (a gabled
tent with side extensions): here a rounded marquee with a pointed end, a lintel carrying the scales banner, a gallows
post carrying the purse sign, iron-banded posts on stone feet, a porch on the left:

  - the roof: a MARQUEE on a short ridge with rounded, cone-like ends, narrow regular red and cream stripes running down
    the slopes and radiating round the ends, a wooden CROSS FINIAL on the left peak, a capped finial on the right one,
    the striped valance with a stepped gold edge all round;
  - the frame: big squared posts of warm wood on grey stone feet with grey riveted iron bands and capped tops; a
    heavy LINTEL with iron plates over the front-left bay carries the crimson SCALES BANNER (gold border, gold V point);
  - two red swallow-tailed FLAGS on poles: on the back-left post and on the tall front-right post;
  - the tall front-right post is a gallows: its beam carries the hanging COIN-PURSE SIGN (a gold purse and a stack of
    coins on a dark board in a wooden frame);
  - thick twisted ROPES from the peaks down the posts, a long rope from the front-left post down to a short stone-footed
    rope post in front;
  - the left PORCH: a lower striped awning with a cream dagged edge on two posts, the tent's cloth sloping down under it,
    stacked iron-banded crates;
  - inside: the long COUNTER with crimson runners edged in gold (books, scrolls, a coin bag, potions, a standing
    lantern), the back SHELVES of potions (purple, blue, green, red) and jars, hanging ivy, an ivy bush by the post;
    lanterns hanging from the lintel, inside and on the right post;
  - in front: a barrel with a standing lantern, the big cream grain sack with red straps and a pile of books, stacked
    crates on the left, stacked chests and crates by the right post, the big crimson RUG with its gold border.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT), reached through the front-left
bay under the banner. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_balance_bourse.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_c as pc  # noqa: E402

ml = pc.ml
v3, norm, add_cube, beam, loft, Bone = pc.v3, pc.norm, pc.add_cube, pc.beam, pc.loft, pc.Bone
EYE, UP, X, Z = pc.EYE, pc.UP, pc.X, pc.Z
ry, rx = pc.ry, pc.rx
box, collide = pc.box, pc.collide
_rgb, _scale, _mix = pc._rgb, pc._scale, pc._mix

NAME = "tente_balance_bourse"
P = pc.Pal(red="b0262c", red_dark="64121a", red_light="d2463e", cream="ecdcc0", gold="eea62a", gold_dark="94600e", gold_light="ffdc80")

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
XL, XM, XR = -2.3, -0.45, 2.6   # front posts: left, middle (the lintel's right end), right (the gallows post)
ZF, ZB = 2.15, -2.15           # front / back post lines
EAVE = 3.0                     # eave beams
EY = 3.22                      # the roof's eave line
RA, RB = -1.5, 1.6             # the ridge
PEAK_L, PEAK_R = 5.25, 4.95    # cloth peaks
RZ = 2.55                      # the eave's half depth
CAP_L, CAP_R = 1.6, 1.3        # the rounded ends' reach in x beyond the ridge ends
LINTEL_Y = 3.38
PORCH_X = -4.0                 # the porch's outer posts
COUNTER = (-0.1, 1.55, 0.95, 1.5)    # a passage between its right end and the gallows post
COUNTER_H = 1.05
NPC_SPOT = (0.4, -0.55)        # (x0, z0) of the free 1 x 1 x 2.2 place behind the counter
SHELF_Z = (-1.95, -1.5)


def regions():
    red, rd, rl, cr, g, gd, gl = P.red, P.red_dark, P.red_light, P.cream, P.gold, P.gold_dark, P.gold_light
    return [
        ("c3_roof", 192, 80, pc.stripes_painter([red, cr], 8, 15401, fold=0.18, grad=(0.86, 1.05))),
        ("c3_cap", 128, 80, pc.stripes_painter([red, cr], 6, 15402, fold=0.18, grad=(0.86, 1.05))),
        ("c3_rug", 128, 96, pc.carpet_painter(red, rd, g, gd, 15403, style="dots", fringe=False)),
        ("c3_banner", 48, 112, pc.banner_painter(red, rd, g, gd, gl, 15404, point="v", border=3, emblem_y=0.34, emblem_w=0.78, body=0.7)),
        ("c3_wall", 96, 64, pc.stripes_painter([cr, red], 4, 15405, fold=0.22, grad=(0.78, 0.96))),
        ("c3_awning", 128, 48, pc.stripes_painter([red, cr], 8, 15406, fold=0.14, grad=(0.9, 1.05))),
        ("c3_sign", 64, 64, pc.sign_painter("purse", 15407, board="5e3a1e", board_dark="34200e", frame="8a5a2c", gold=g, gold_dark=gd, gold_light=gl)),
        ("c3_val", 192, 32, pc.valance_painter([cr, red], 8, 15408, kind="square", edge=g, edge_dark=gd, solid=0.45)),
        ("c3_runner", 40, 40, pc.runner_painter(red, rd, g, 15409, motif="meander")),
        ("c3_flag", 48, 24, pc.flag_painter(red, rd, g, 15410)),
        ("c3_awning_val", 128, 20, pc.valance_painter([cr, _scale(cr, 0.92)], 6, 15411, kind="square", edge=_scale(cr, 0.78), solid=0.42)),
        ("c_burlap", 32, 32, pc.burlap_painter("e4d4b6", 15412)),
        ("c_chest", 32, 32, pc.chest_painter(15413, base="8a5428", dark="40220c")),
        ("c_post", 64, 16, pc.wood_painter("b8783c", "62381a", 15414)),
        ("c_band", 32, 8, pc.band_painter(15415)),
    ]


# ---------------------------------------------------------------- roof
def ridge_y(x):
    u = (min(max(x, RA), RB) - RA) / (RB - RA)
    return PEAK_L + (PEAK_R - PEAK_L) * u - 0.18 * math.sin(math.pi * u)


def roof(shell, det):
    pc.skirt(shell, "roof_front", lambda s: v3(RA + (RB - RA) * s, ridge_y(RA + (RB - RA) * s), 0.0), lambda s: v3(RA + (RB - RA) * s, EY, RZ),
             "c3_roof", 8, 5, a=0.4, folds=8, sag=0.04, belly=0.1)
    pc.skirt(shell, "roof_back", lambda s: v3(RB - (RB - RA) * s, ridge_y(RB - (RB - RA) * s), 0.0), lambda s: v3(RB - (RB - RA) * s, EY, -RZ),
             "c3_roof", 8, 5, a=0.4, folds=8, sag=0.04, belly=0.1)

    def cap(name, x0, reach, th0, th1, peak):
        top = v3(x0, peak, 0.0)
        pc.skirt(shell, name, lambda s: top, lambda s: v3(x0 + reach * math.cos(th0 + (th1 - th0) * s), EY, RZ * math.sin(th0 + (th1 - th0) * s)),
                 "c3_cap", 6, 5, a=0.4, folds=6, sag=0.04, belly=0.1)
    cap("roof_left", RA, CAP_L, math.pi / 2, 3 * math.pi / 2, ridge_y(RA))
    cap("roof_right", RB, CAP_R, -math.pi / 2, math.pi / 2, ridge_y(RB))
    # the valance all round: the two straight sides and the two rounded ends
    def eave(s, part):
        if part == 0:
            return v3(RA + (RB - RA) * s, EY, RZ), Z
        if part == 2:
            return v3(RB - (RB - RA) * s, EY, -RZ), -Z
        th = (math.pi / 2 + math.pi * s) if part == 3 else (-math.pi / 2 + math.pi * s)
        x0, reach = (RA, CAP_L) if part == 3 else (RB, CAP_R)
        p = v3(x0 + reach * math.cos(th), EY, RZ * math.sin(th))
        return p, norm(v3(math.cos(th) / reach, 0, math.sin(th) / RZ))
    for part, n in ((0, 3), (1, 4), (2, 3), (3, 4)):
        def V(s, t, part=part):
            ss = s if part in (1, 2) else 1 - s
            ss = 1 - s if part in (0, 3) else s
            p, out = eave(ss if part in (1, 2) else ss, part)
            return p + out * (0.03 + 0.04 * t) - UP * (0.56 * t) + UP * 0.02
        loft(shell, "valance_%d" % part, (lambda s, t, V=V: V(1 - s, t)) if part in (0, 3) else V, n, 1, "c3_val", th=0.025)
    # finials: the wooden cross on the left peak, a capped block on the right one; rope coils on the gathered cloth
    for k, (x, peak) in enumerate(((RA, ridge_y(RA)), (RB, ridge_y(RB)))):
        box(shell, "peak_block_%d" % k, (x - 0.3, peak - 0.1, -0.3), (x + 0.3, peak + 0.22, 0.3), {"all": "wood", "+2": "end_grain"})
        box(det, "peak_block_top_%d" % k, (x - 0.22, peak + 0.22, -0.22), (x + 0.22, peak + 0.34, 0.22), {"all": "wood_dark", "+2": "end_grain"})
        pc.rope_coil(det, "peak_coil_%d" % k, x, 0.0, peak - 0.2, 0.34)
    x, peak = RA, ridge_y(RA)
    beam(shell, "cross_post", (x, peak + 0.34, 0), (x, peak + 1.15, 0), 0.16, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"})
    beam(shell, "cross_bar", (x - 0.3, peak + 0.85, 0), (x + 0.3, peak + 0.85, 0), 0.13, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"})
    box(det, "cross_tip", (x - 0.06, peak + 1.15, -0.06), (x + 0.06, peak + 1.25, 0.06), "gold")
    for k, sx in enumerate((-1, 1)):
        box(det, "cross_end_%d" % k, (x + sx * 0.3 - 0.06, peak + 0.79, -0.06), (x + sx * 0.3 + 0.06, peak + 0.91, 0.06), "gold")
    x, peak = RB, ridge_y(RB)
    beam(shell, "finial_r", (x, peak + 0.34, 0), (x, peak + 0.75, 0), 0.14, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"})
    box(det, "finial_r_cap", (x - 0.12, peak + 0.75, -0.12), (x + 0.12, peak + 0.87, 0.12), "gold")


# ---------------------------------------------------------------- the build
def build(decor):
    rng = random.Random(154)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    # ---- posts (stone feet, iron bands, capped tops), the tall gallows post, flag poles
    for k, (x, z, top) in enumerate(((XL, ZF, 3.62), (XM, ZF, 3.62), (XR, ZF, 5.25), (XR, ZB, 3.5), (XL, ZB, 3.5))):
        bands = (0.7, 1.7, EAVE - 0.45) + ((3.85, 4.75) if top > 4 else ())
        pc.banded_post(shell, det, "post_%d" % k, x, z, top, d=0.48, foot_h=0.52, bands=bands, cap=(0.6, 0.26), collide_to=min(top, EAVE))
    box(det, "post_2_cap_top", (XR - 0.2, 5.51, ZF - 0.2), (XR + 0.2, 5.62, ZF + 0.2), {"all": "wood_dark", "+2": "end_grain"})
    for k, (x, z, y0, y1, dirn) in enumerate(((XL, ZB, 3.76, 5.7, (-0.3, 0, 1.0)), (XR, ZF, 5.62, 6.35, (-0.2, 0, 1.0)))):
        beam(shell, "flag_pole_%d" % k, (x, y0, z), (x, y1, z), 0.1, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"})
        box(det, "flag_pole_%d_knob" % k, (x - 0.08, y1, z - 0.08), (x + 0.08, y1 + 0.12, z + 0.08), "gold")
        box(det, "flag_pole_%d_band" % k, (x - 0.07, y1 - 0.5, z - 0.07), (x + 0.07, y1 - 0.4, z + 0.07), "gold")
        pc.flag(shell, "flag_%d" % k, (x + 0.02, y1 - 0.05, z), (1.0, 0, -0.2) if k == 0 else (-1.0, 0, -0.25), 1.2, 0.56, "c3_flag", wave=0.12)
    # ---- eave beams, the front lintel with iron plates
    by = EAVE
    for k, ((xa, za), (xb, zb)) in enumerate((((XM, ZF), (XR, ZF)), ((XR, ZF), (XR, ZB)), ((XR, ZB), (XL, ZB)), ((XL, ZB), (XL, ZF)), ((XL, ZF), (XM, ZF)))):
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.28, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26, extend=0.2)
    beam(shell, "lintel", (XL - 0.45, LINTEL_Y, ZF + 0.12), (XM + 0.45, LINTEL_Y, ZF + 0.12), 0.4, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"},
         width=0.36)
    for k, x in enumerate((XL - 0.45, XM + 0.45)):
        box(shell, "lintel_end_%d" % k, (x - 0.16, LINTEL_Y - 0.25, ZF - 0.08), (x + 0.16, LINTEL_Y + 0.25, ZF + 0.32), {"all": "wood", "+2": "end_grain"})
    for k, x in enumerate((XL + 0.05, (XL + XM) / 2, XM - 0.05)):
        box(det, "lintel_plate_%d" % k, (x - 0.22, LINTEL_Y - 0.23, ZF + 0.29), (x + 0.22, LINTEL_Y + 0.23, ZF + 0.33), {"all": "c_band", "+3": "c_band"},
            stretch=True)
    for k, (p, q) in enumerate((((XM - 0.15, by - 0.85, ZF), (XM - 0.7, by - 0.12, ZF)), ((XR - 0.15, by - 0.85, ZF), (XR - 0.75, by - 0.12, ZF)),
                                ((XR, by - 0.85, ZB + 0.15), (XR, by - 0.12, ZB + 0.75)), ((XL, by - 0.85, ZB + 0.15), (XL, by - 0.12, ZB + 0.75)))):
        beam(shell, "brace_%d" % k, p, q, 0.14, "wood_dark", extend=0.04)
    for k, x in enumerate((RA, RB)):
        beam(shell, "tie_%d" % k, (x, by + 0.02, ZB), (x, by + 0.02, ZF), 0.22, "wood_dark", extend=0.1)
        beam(shell, "king_%d" % k, (x, by + 0.12, 0), (x, ridge_y(x) - 0.05, 0), 0.22, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"})
    beam(shell, "ridge_pole", (RA, ridge_y(RA) - 0.35, 0), (RB, ridge_y(RB) - 0.35, 0), 0.18, "wood_dark", extend=0.1)
    # ---- roof
    roof(shell, det)
    # ---- the scales banner under the lintel
    ml.banner(shell, "banner", ((XL + XM) / 2, LINTEL_Y - 0.2, ZF + 0.38), 1.12, 2.1, normal=(0, 0, 1), region="c3_banner", rod=True, wave=0.03,
              rod_region="iron", knobs="gold")
    # ---- ropes: peaks down to the posts, the long rope to the rope post in front
    for k, (a, b) in enumerate((((RA - 0.25, ridge_y(RA) - 0.25, 0.25), (XL, 3.75, ZF)), ((RA - 0.25, ridge_y(RA) - 0.3, -0.2), (XL, 3.65, ZB)),
                                ((RB + 0.25, ridge_y(RB) - 0.25, 0.2), (XR, 4.4, ZF)), ((RB + 0.25, ridge_y(RB) - 0.3, -0.2), (XR, 3.65, ZB)))):
        ml.rope(det, "rope_%d" % k, a, b, d=0.085, sag=0.25, segs=4)
        add_cube(det, "rope_knot_%d" % k, b + UP * 0.05, EYE, (0.16, 0.2, 0.16), "rope")
    pc.banded_post(shell, det, "rope_post", -2.75, 3.45, 0.62, d=0.24, foot_h=0.18, foot="stone", bands=(), cap=None, foot_w=0.2)
    box(shell, "rope_post_cap", (-2.89, 0.62, 3.31), (-2.61, 0.84, 3.59), "gold")
    ml.rope(det, "rope_long", (XL - 0.05, 3.62, ZF + 0.1), (-2.75, 0.72, 3.45), d=0.085, sag=0.06, segs=3)
    pc.guy(det, "guy_back", (XL, 3.4, ZB - 0.1), (XL + 0.6, 0.0, ZB - 0.95))
    pc.guy(det, "guy_back_r", (XR, 3.4, ZB - 0.1), (XR - 0.6, 0.0, ZB - 0.95))
    # ---- walls: the back, the right side (back half), the left side sloping out under the porch
    pc.wall(shell, "wall_back", (XL, 0, ZB - 0.07), (XR, 0, ZB - 0.07), 0.0, by - 0.12, -Z, "c3_wall", nx=6)
    collide((XL, 0.0, ZB - 0.13, XR, by - 0.12, ZB - 0.01))
    pc.wall(shell, "wall_right", (XR + 0.07, 0, 0.4), (XR + 0.07, 0, ZB), 0.0, by - 0.12, X, "c3_wall", nx=4)
    collide((XR + 0.01, 0.0, ZB, XR + 0.13, by - 0.12, 0.4))

    def LW(s, t):   # the left side: from the eave beam down and out to the ground under the porch
        z = ZB + (1.35 - ZB) * s
        x = XL - 0.05 - 0.75 * t
        y = (by - 0.1) * (1 - t)
        return v3(x - 0.06 * math.sin(math.pi * t), y, z + 0.05 * math.sin(s * math.pi * 6) * t)
    loft(shell, "wall_left", LW, 6, 3, "c3_wall", th=0.03)
    collide((XL - 0.8, 0.0, ZB, XL, 1.2, 1.35))
    collide((XL - 0.35, 1.2, ZB, XL, by - 0.12, 1.35))
    # ---- the left porch: striped awning on two posts, its dagged edge, crates under it
    for k, z in enumerate((2.0, -1.05)):
        pc.banded_post(shell, det, "porch_post_%d" % k, PORCH_X, z, 2.82, d=0.34, foot_h=0.42, bands=(0.55, 1.6, 2.4), cap=(0.44, 0.2), collide_to=2.82)
    beam(shell, "porch_beam_f", (XL, 2.62, 2.0), (PORCH_X, 2.62, 2.0), 0.22, "beam", extend=0.2)
    beam(shell, "porch_beam_s", (PORCH_X, 2.68, -1.05), (PORCH_X, 2.68, 2.0), 0.22, "beam", extend=0.2)

    def PA(s, t):
        z = 2.3 - (2.3 + 1.35) * s
        x = XL - 0.05 + (PORCH_X - 0.28 - XL + 0.05) * t
        y = by + 0.1 - (by + 0.1 - 2.78) * t - 0.08 * math.sin(math.pi * t) - 0.04 * math.sin(math.pi * ((s * 8) % 1.0))
        return v3(x, y, z)
    loft(shell, "porch_awning", PA, 8, 3, "c3_awning", th=0.035, overlap=0.03)
    pc.valance(shell, "porch_val_f", (PORCH_X - 0.28, 2.8, 2.32), (XL - 0.05, by + 0.12, 2.32), Z, h=0.4, region="c3_awning_val", n=2)
    pc.valance(shell, "porch_val_s", (PORCH_X - 0.3, 2.8, -1.35), (PORCH_X - 0.3, 2.8, 2.3), -X, h=0.4, region="c3_awning_val", n=3)
    pc.iron_crate(shell, det, "porch_crate_0", (-3.45, 0.0, 1.15), size=(0.8, 0.62, 0.7), yaw=0.06)
    pc.iron_crate(shell, det, "porch_crate_1", (-3.4, 0.62, 1.15), size=(0.66, 0.5, 0.6), yaw=-0.1)
    decor.block("furnish:spruce_crate", -3.5, 0.0, 0.1, facing="front", alt="minecraft:barrel", fallback="crate")
    # ---- lanterns: under the lintel, inside, on the right post, on the barrel, on the counter
    ml.lantern(shell, "lamp_lintel", (XM - 0.32, 2.55, ZF + 0.25), size=0.38, metal="iron", chain_to=(XM - 0.32, LINTEL_Y - 0.2, ZF + 0.25))
    ml.lantern(shell, "lamp_in", (0.15, 2.4, -0.55), size=0.34, metal="iron", chain_to=(0.15, by - 0.1, -0.55))
    pc.lantern_bracket(shell, det, "lamp_post", (XR - 0.25, 3.0, ZF + 0.05), (-0.35, 0, 1), drop=0.5, size=0.38)
    # ---- inside: the counter with its runners and goods, the back shelves of potions, ivy
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    for k, (x0, x1) in enumerate(((cx0 + 0.1, cx0 + 0.75), (cx0 + 0.98, cx0 + 1.6))):
        box(shell, "runner_top_%d" % k, (x0, y, cz0 + 0.02), (x1, y + 0.015, cz1 + 0.03), {"all": "cloth_red"}, stretch=True)
        ml.plate(shell, "runner_front_%d" % k, ((x0 + x1) / 2, y - 0.3, cz1 + 0.045), x1 - x0, 0.62, "c3_runner", normal=(0, 0, 1), th=0.012,
                 edge="cloth_red")
    pc.book_stack(det, "counter_books", (cx0 + 0.32, y + 0.015, zc), 4, rng, covers=("cloth_blue", "leather", "cloth_red", "leather_dark"), w=0.32, d=0.38)
    for k, (dx, dz, yaw) in enumerate(((0.32, -0.12, 0.1), (0.36, 0.12, -0.1))):
        pc.scroll(det, "counter_scroll_%d" % k, (cx0 + dx, y + 0.31 + 0.11 * k, zc + dz * 0.3), length=0.42, r=0.06, yaw=yaw + math.pi / 2 * 0)
    ml.sack(det, "coin_bag", (cx0 + 0.7, y, zc), s=0.3, yaw=0.3, region="stone")
    ml.bottle(det, "counter_potion_0", (cx0 + 1.12, y, zc - 0.1), "green", r=0.075, h=0.18, shape="round")
    ml.bottle(det, "counter_potion_1", (cx0 + 1.26, y, zc + 0.1), "purple", r=0.07, h=0.17, shape="round")
    pc.scroll(det, "counter_scroll_2", (cx0 + 0.98, y + 0.06, zc + 0.14), length=0.3, r=0.06, yaw=0.4)
    pc.standing_lantern(shell, det, "lamp_counter", (cx0 + 1.47, y, zc - 0.02), size=0.32)
    decor.block("furnish:book_pile", cx0 + 0.95, y, zc - 0.08, facing="front", scale=0.55, solid=False, fallback="leather")
    levels = ml.shelf_unit(shell, "shelves", -0.25, 2.2, SHELF_Z[0], SHELF_Z[1], levels=(0.55, 1.15, 1.75, 2.35), h=2.65, back=True, uprights=3, detail=det)
    for j, (x0, x1, yy, zf, zb) in enumerate(sorted(levels, key=lambda s: s[2])):
        zc2 = (zf + zb) / 2
        if j in (1, 2):
            pc.potion_row(det, "shelf_pot_%d" % j, x0 + 0.1, x1 - 0.1, yy, zc2, rng, ("purple", "blue", "green", "red", "orange", "blue", "purple"), n=8,
                          rmin=0.07, rmax=0.09)
        elif j == 3:
            for i in range(5):
                xx = x0 + 0.2 + (x1 - x0 - 0.4) * i / 4
                if i % 2:
                    ml.sack(det, "shelf_sack_%d" % i, (xx, yy, zc2), s=0.26, yaw=0.3 * i, region="c_burlap")
                else:
                    ml.bottle(det, "shelf_jar_%d" % i, (xx, yy, zc2), "orange" if i else "green", r=0.1, h=0.22, shape="tall", neck_h=0.05)
        else:
            for i, xx in enumerate((x0 + 0.3, x0 + 0.85, x1 - 0.75, x1 - 0.3)):
                ml.crate(det, "shelf_box_%d" % i, (xx, yy, zc2), size=(0.38, 0.26, 0.3), yaw=0.15 * i, solid=False)
    pc.ivy_hang(det, "ivy_lintel", (XM - 0.75, LINTEL_Y - 0.25, ZF + 0.05), 1.2, 0.6)
    pc.ivy_hang(det, "ivy_lintel_b", (XM - 0.95, LINTEL_Y - 0.25, ZF - 0.1), 0.9, 0.5, normal=(0.4, 0, 1))
    pc.ivy_bush(det, "ivy_post", (XR - 0.55, 0.0, ZF - 0.35), h=1.0, w=0.65, rng=rng)
    pc.ivy_hang(det, "ivy_post_up", (XR - 0.3, by - 0.2, ZF - 0.28), 0.8, 0.4, normal=(-1, 0, 0.3))
    # ---- in front: the barrel with its lantern, the big sack with books, crates on the left
    ml.barrel(shell, "barrel_front", (-1.72, 0.0, 3.02), r=0.4, h=0.95)
    pc.standing_lantern(shell, det, "lamp_barrel", (-1.72, 0.95, 3.02), size=0.42)
    pc.square_sack(shell, det, "big_sack", (-0.62, 0.0, 3.22), size=(0.9, 0.82, 0.72), yaw=0.05)
    for k, sx in enumerate((-0.2, 0.2)):
        box(det, "big_sack_strap_%d" % k, (-0.62 + sx - 0.04, 0.3, 3.22 - 0.375), (-0.62 + sx + 0.04, 0.84, 3.22 + 0.375), "cloth_red", stretch=True)
    decor.block("farmhouse_decorations:pile_of_books", -0.62, 0.82, 3.2, facing="front", scale=1.5, solid=False, fallback="leather")
    pc.iron_crate(shell, det, "crate_fl_0", (-3.55, 0.0, 2.75), size=(0.82, 0.66, 0.72), yaw=0.05)
    pc.iron_crate(shell, det, "crate_fl_1", (-3.5, 0.66, 2.7), size=(0.62, 0.5, 0.56), yaw=-0.12)
    ml.crate(shell, "crate_fl_x", (-2.82, 0.0, 2.65), size=(0.62, 0.55, 0.56), yaw=0.15)
    for k, (p, q) in enumerate((((-3.1, 0.05, 2.93), (-2.55, 0.5, 2.98)), ((-3.1, 0.5, 2.93), (-2.55, 0.05, 2.98)))):
        beam(det, "crate_fl_x_brace_%d" % k, p, q, 0.06, "wood_dark", width=0.03)
    # ---- by the right post: stacked chests and crates
    pc.iron_crate(shell, det, "chest_base", (3.55, 0.0, 1.55), size=(1.15, 0.7, 0.8), yaw=-0.04, region="c_chest", top="c_chest")
    pc.chest(shell, det, "chest_top", (3.55, 0.7, 1.55), size=(0.98, 0.62, 0.66), yaw=-0.04, wood="c_chest", domed=False, metal="iron")
    ml.crate(shell, "red_box", (3.6, 1.32, 1.55), size=(0.45, 0.3, 0.38), yaw=0.2, region="cloth_red", top="cloth_red")
    pc.iron_crate(shell, det, "crate_r_0", (4.45, 0.0, 1.0), size=(0.62, 0.58, 0.6), yaw=0.1, region="c_chest", top="c_chest")
    pc.iron_crate(shell, det, "crate_r_1", (4.5, 0.0, 1.85), size=(0.55, 0.5, 0.5), yaw=-0.08)
    decor.block("furnish:spruce_crate", 3.6, 0.0, 0.35, facing="front", alt="minecraft:barrel", fallback="crate")
    # ---- the purse sign on the gallows beam of the right post
    sy = 4.62
    beam(shell, "sign_beam", (XR - 0.1, sy, ZF), (4.75, sy, ZF), 0.3, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"}, width=0.3, extend=0.1)
    box(det, "sign_beam_plate", (XR + 0.22, sy - 0.17, ZF - 0.17), (XR + 0.36, sy + 0.17, ZF + 0.17), "c_band", stretch=True)
    beam(shell, "sign_brace", (XR + 0.24, sy - 0.85, ZF), (XR + 0.95, sy - 0.1, ZF), 0.16, "wood_dark", extend=0.04)
    scx = 4.05
    for k, dx in enumerate((-0.38, 0.38)):
        ml.rope(det, "sign_rope_%d" % k, (scx + dx, sy - 0.15, ZF), (scx + dx, sy - 0.45, ZF), d=0.04, segs=1, region="iron")
    box(shell, "sign", (scx - 0.56, sy - 1.55, ZF - 0.07), (scx + 0.56, sy - 0.43, ZF + 0.07), {"all": "c_chest", "+3": "c3_sign", "-3": "c3_sign"},
        stretch=True, u_dir=X, v_dir=-UP)
    # ---- the rug
    ml.rug(shell, "rug", -0.15, 3.05, 1.6, 4.3, y=0.0, region="c3_rug")
    return root


def item_icon(path):
    """16x16: the red-and-cream striped marquee with its cross finial, the banner and the purse sign."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, cr, gold = P.red, P.cream, P.gold
    wood = (150, 96, 50)
    for y in range(3, 10):
        half = 1.5 + (y - 3) * 1.0
        for x in range(0, 13):
            dx = x - 5.5
            if abs(dx) <= half:
                p[x, y] = (red if int(dx + 8) % 2 else cr) + (255,)
    p[5, 0] = p[5, 1] = p[5, 2] = wood + (255,)
    p[4, 1] = p[6, 1] = wood + (255,)
    for x in range(0, 13):
        p[x, 10] = (gold if x % 2 else red) + (255,)
    for x in (0, 12):
        for y in range(10, 16):
            p[x, y] = wood + (255,)
    for y in range(11, 15):
        for x in range(1, 12):
            p[x, y] = (60, 36, 22, 255)
    for y in range(10, 14):
        for x in range(2, 5):
            p[x, y] = red + (255,)
    p[3, 11] = gold + (255,)
    for y in range(2, 16):
        p[12, y] = wood + (255,)
    for x in range(12, 16):
        p[x, 3] = wood + (255,)
    for y in range(5, 9):
        for x in range(13, 16):
            p[x, y] = (90, 58, 30, 255)
    p[14, 6] = p[14, 7] = gold + (255,)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    pc.add_regions(atlas, regions())
    decor = ml.Decor()
    root = build(decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)
    print("atlas", atlas.size)


if __name__ == "__main__":
    main()
