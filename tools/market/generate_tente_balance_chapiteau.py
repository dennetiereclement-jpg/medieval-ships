#!/usr/bin/env python3
"""tente_balance_chapiteau — Grand chapiteau à la balance / Great Scales Marquee (1.26.0, market tents group C;
reference: scratchpad/ref2/tente_balance_chapiteau_ref.png, picture 048).

A big red-and-cream marquee, one block (TentType group "tents"), about 9 blocks wide (the main marquee and its striped
side awning) and 7.5 deep (the rug and the rolled carpets in front), the left king post at about 7.8:

  - the main roof: a HIPPED MARQUEE in deep crimson with blocky CREAM STEPPED PYRAMIDS rising from the eave and a cream
    stripe down from the peaks, steep at the top and flaring out flat to the eaves (a big top), soft folds between the
    seams; two KING POSTS of warm
    wood with grey riveted iron bands pierce it (the left one higher, a capped block on top; the right one carries a
    red swallow-tailed flag), the cloth gathered up to them;
  - the big SCALES BANNER (crimson, gold stepped border and stepped point, the gold scales) laid down the front slope;
  - deep U-shaped red SWAG VALANCES (festoons) with gold stepped dags along the front and the left side, the roof's
    cream pyramids above them;
  - the frame: big squared posts of warm orange wood on grey stone feet with riveted iron bands and capped tops, eave
    beams, a tall FLAG POST on the left side (red swallow-tailed flag), thick twisted ROPES from the king posts down to
    the posts, guy ropes to pegs behind;
  - the right AWNING in orange and cream stripes running front to back, sloping down to the front (its striped top seen
    from the front as in the picture), square-dagged edges, on two front posts and a back post, glowing LANTERNS on
    brackets on its front posts;
  - two big bunches of hanging HERBS under the front-left swag, over the counter;
  - the left side: open at the front with a side counter (potions) under a rod of hanging herbs, the back half
    closed by the striped wall with a red drape bearing the scales, a cream curtain tied to the flag post;
  - inside: the front-left COUNTER (potions, books, scroll), the back SHELVES (books, potions, bottles, jars), a red
    curtain tied at the left of the entrance and a cream one at the right, lanterns hanging from the front beam and
    inside;
  - in front: the iron-banded CHEST on a crate by the front-left post, two big ROLLED CARPETS (red and gold), burlap grain
    sacks and an iron-banded crate; the red RUG with its gold medallion and fringe running out of the entrance;
  - under the awning: the counter under a cream-and-red cloth with a gold lozenge (potions, books), a big iron-banded
    chest with an OPEN BOOK on a box, crates, a lying barrel, sacks.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the front-left counter (NPC_SPOT), reached from the
entrance. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_balance_chapiteau.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/<id>.json, models/entity + blockbench/<id>.bbmodel, textures/entity/<id>.png,
textures/item/<id>.png, interiors/<id>_decor.json.
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

NAME = "tente_balance_chapiteau"
P = pc.Pal(red="921c24", red_dark="520e14", red_light="b8323a", cream="dfc9a8", gold="eaa62c", gold_dark="8e5a12", gold_light="ffd884")
ORANGE = _rgb("e2962a")

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
XL, XR = -3.4, 1.5           # main posts: x
ZF, ZB = 2.4, -2.4           # main posts: z
EAVE = 3.15                  # eave beams (their axis)
EY = 3.42                    # the roof's eave line
OV = 0.4                     # roof overhang past the posts
RA, RB = -2.05, 0.25         # the ridge between the two king posts
PEAK_L, PEAK_R = 5.95, 5.6   # cloth peaks at the king posts
KING_L, KING_R = 6.6, 6.2    # king post tops
AX = 5.3                     # the awning's outer post line
AZ0, AZ1 = -1.5, 2.45        # the awning's back and front post lines
AY_IN, AY_OUT = 3.3, 2.78    # the awning's height at the main tent and at the outer posts
COUNTER = (-3.0, -1.25, 1.55, 2.1)
COUNTER_H = 1.05
SIDE_COUNTER = (-3.33, -2.8, 0.3, 1.5)
AW_COUNTER = (1.72, 2.9, 1.5, 2.07)
NPC_SPOT = (-2.65, 0.25)     # (x0, z0) of the free 1 x 1 x 2.2 place behind the front-left counter
SHELF_Z = (-2.2, -1.72)


# ---------------------------------------------------------------- textures
def regions():
    red, rd, rl, cr, g, gd, gl = P.red, P.red_dark, P.red_light, P.cream, P.gold, P.gold_dark, P.gold_light
    return [
        ("c1_roof", 192, 80, pc.pyramid_painter(red, cr, 4, 4801, top=0.36, bottom=0.97, steps=3, base=0.72, ridge=0.05, ridge_n=2)),
        ("c1_hip", 96, 80, pc.pyramid_painter(red, cr, 2, 4802, top=0.36, bottom=0.97, steps=3, base=0.72, ridge=0.05, ridge_n=2)),
        ("c1_rug", 80, 112, pc.carpet_painter(red, rd, g, gd, 4803, style="medallion")),
        ("c1_banner", 40, 112, pc.banner_painter(red, rd, g, gd, gl, 4804, point="steps", border=3, emblem_y=0.34, emblem_w=0.78, body=0.7)),
        ("c1_sidebanner", 24, 64, pc.banner_painter(red, rd, g, gd, gl, 4805, point="v", border=2, emblem_y=0.33, emblem_w=0.8, body=0.76)),
        ("c1_wall", 96, 56, pc.stripes_painter([red, cr], 6, 4806, fold=0.2, hem=g, hem_h=3, grad=(0.8, 0.95), ratio=0.3)),
        ("c1_awning", 112, 112, pc.stripes_painter([ORANGE, cr], 8, 4807, fold=0.14, grad=(0.9, 1.06))),
        ("c1_drape_red", 32, 56, pc.stripes_painter([red, _scale(red, 0.92)], 3, 4808, fold=0.34, seam=0.86, hem=g, hem_h=4, grad=(0.82, 1.0))),
        ("c1_drape_cream", 32, 56, pc.stripes_painter([cr, _scale(cr, 0.94)], 3, 4809, fold=0.3, seam=0.88, hem=red, hem_h=10, grad=(0.85, 1.0))),
        ("c1_runner", 48, 40, pc.runner_painter(red, rd, g, 4810, motif="diamond", top_col=cr)),
        ("c1_swag", 128, 32, pc.valance_painter([red], 4, 4811, kind="square", edge=g, edge_dark=gd, solid=0.62, motif=g, top=g)),
        ("c1_awning_val", 128, 20, pc.valance_painter([ORANGE, cr], 8, 4812, kind="square", edge=_scale(ORANGE, 0.75), solid=0.4)),
        ("c1_roll", 48, 24, pc.roll_painter(red, g, 4813)),
        ("c1_end", 16, 16, pc.spiral_painter(red, g)),
        ("c1_flag", 48, 24, pc.flag_painter(red, rd, g, 4814)),
        ("c_burlap", 32, 32, pc.burlap_painter("d0b48a", 4815)),
        ("c_chest", 32, 32, pc.chest_painter(4816, base="7e3c22", dark="3c1a0c")),
        ("c_post", 64, 16, pc.wood_painter("c0843e", "6a3e18", 4817)),
        ("c_band", 32, 8, pc.band_painter(4818)),
        ("c_pages", 32, 16, pc.pages_painter(4819)),
    ]


# ---------------------------------------------------------------- roof
def ridge_y(x):
    u = (x - RA) / (RB - RA)
    return PEAK_L + (PEAK_R - PEAK_L) * u - 0.24 * math.sin(math.pi * u)


def ridge_pt(x):
    xc = min(max(x, RA), RB)
    return v3(xc, ridge_y(xc), 0.0)


X0, X1, ZE = XL - OV, XR + OV, ZF + OV   # the eave rectangle


def roof(shell, det):
    ex = lambda s: X0 + (X1 - X0) * s  # noqa: E731
    front = pc.skirt(shell, "roof_front", lambda s: ridge_pt(ex(s)), lambda s: v3(ex(s), EY, ZE), "c1_roof", 14, 5, a=0.22, folds=8, sag=0.05,
                     belly=0.1, power=2.2)
    pc.skirt(shell, "roof_back", lambda s: ridge_pt(ex(1 - s)), lambda s: v3(ex(1 - s), EY, -ZE), "c1_roof", 14, 5, a=0.22, folds=8, sag=0.05,
             belly=0.1, power=2.2)
    pc.skirt(shell, "roof_left", lambda s: ridge_pt(RA), lambda s: v3(X0, EY, -ZE + 2 * ZE * s), "c1_hip", 5, 5, a=0.22, folds=4, sag=0.05, belly=0.1, power=2.2)
    pc.skirt(shell, "roof_right", lambda s: ridge_pt(RB), lambda s: v3(X1, EY, ZE - 2 * ZE * s), "c1_hip", 5, 5, a=0.22, folds=4, sag=0.05, belly=0.1, power=2.2)
    # the big scales banner laid down the front slope (right of the middle), just above the cloth
    s0, s1 = (-0.95 - X0) / (X1 - X0), (0.22 - X0) / (X1 - X0)
    t0, t1 = 0.05, 0.86

    def B(s, t):
        return pc.surface_offset(front, s0 + (s1 - s0) * s, t0 + (t1 - t0) * t, 0.045)
    loft(shell, "roof_banner", B, 2, 5, "c1_banner", th=0.02, overlap=0.02)
    return front


# ---------------------------------------------------------------- the build
def build(decor):
    rng = random.Random(48)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    # ---- main posts (stone feet, iron bands, capped tops), the left side's tall flag post
    corners = {"fl": (XL, ZF), "fr": (XR, ZF), "br": (XR, ZB), "bl": (XL, ZB)}
    for k, (x, z) in corners.items():
        pc.banded_post(shell, det, "post_" + k, x, z, 3.8, d=0.52, foot_h=0.55, bands=(0.72, 1.75, EAVE - 0.55), cap=(0.64, 0.3), collide_to=EAVE)
        box(det, "post_%s_cap_top" % k, (x - 0.2, 4.1, z - 0.2), (x + 0.2, 4.21, z + 0.2), {"all": "wood_dark", "+2": "end_grain"})
    pc.banded_post(shell, det, "post_ml", XL, 0.0, 5.25, d=0.42, foot_h=0.5, bands=(0.65, 1.8, 2.75, 3.95, 4.75), cap=(0.5, 0.26), collide_to=EAVE)
    pc.flag(shell, "flag_left", (XL - 0.05, 5.22, 0.0), (0.15, 0, 1.0), 1.25, 0.6, "c1_flag", wave=0.12)
    # ---- eave beams, tie beams carrying the king posts, braces
    by = EAVE
    for k, ((xa, za), (xb, zb)) in enumerate((((XL, ZF), (XR, ZF)), ((XR, ZF), (XR, ZB)), ((XR, ZB), (XL, ZB)), ((XL, ZB), (XL, ZF)))):
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.32, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.28, extend=0.3)
    for k, x in enumerate((RA, RB)):
        beam(shell, "tie_%d" % k, (x, by + 0.02, ZB), (x, by + 0.02, ZF), 0.24, "wood_dark", extend=0.1)
    beam(shell, "ridge_pole", (RA, PEAK_L - 0.45, 0), (RB, PEAK_R - 0.45, 0), 0.2, "wood_dark", extend=0.1)
    for k, (x, top, cap) in enumerate(((RA, KING_L, True), (RB, KING_R, False))):
        beam(shell, "king_%d" % k, (x, by + 0.14, 0), (x, top, 0), 0.38 if k == 0 else 0.32, {"all": "c_post", "+1": "end_grain", "-1": "end_grain"})
        for j, y in enumerate((ridge_y(x) + 0.08, top - 0.32)):
            pc.band(det, "king_%d_band_%d" % (k, j), x, 0.0, (0.38 if k == 0 else 0.32) / 2 + 0.03, y, 0.16)
        for j, sz in enumerate((-1, 1)):
            beam(shell, "rafter_%d_%d" % (k, j), (x, by + 0.1, sz * (ZF - 0.1)), (x, ridge_y(x) - 0.4, 0), 0.14, "wood_dark", extend=0.04)
        pc.rope_coil(det, "king_%d_coil" % k, x, 0.0, ridge_y(x) - 0.02, 0.26 if k == 0 else 0.22)
        if cap:
            box(shell, "king_cap", (x - 0.3, top, -0.3), (x + 0.3, top + 0.3, 0.3), {"all": "wood", "+2": "end_grain"})
            box(det, "king_cap_top", (x - 0.2, top + 0.3, -0.2), (x + 0.2, top + 0.42, 0.2), {"all": "wood_dark", "+2": "end_grain"})
            box(det, "king_cap_knob", (x - 0.12, top + 0.42, -0.12), (x + 0.12, top + 0.6, 0.12), {"all": "wood", "+2": "end_grain"})
        else:
            box(shell, "king_cap_r", (x - 0.24, top, -0.24), (x + 0.24, top + 0.22, 0.24), {"all": "wood", "+2": "end_grain"})
            beam(shell, "flag_pole_r", (x, top + 0.2, 0), (x, top + 0.95, 0), 0.1, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
            box(det, "flag_pole_r_knob", (x - 0.08, top + 0.95, -0.08), (x + 0.08, top + 1.08, 0.08), "gold")
            pc.flag(shell, "flag_right", (x + 0.03, top + 0.92, 0.0), (1.0, 0, 0.25), 1.3, 0.58, "c1_flag", wave=0.12)
    for k, (p, q) in enumerate((((XL + 0.2, EAVE - 1.0, ZF), (XL + 0.9, by - 0.12, ZF)), ((XR - 0.2, EAVE - 1.0, ZF), (XR - 0.9, by - 0.12, ZF)),
                                ((XL, EAVE - 1.0, ZB + 0.2), (XL, by - 0.12, ZB + 0.9)), ((XR, EAVE - 1.0, ZB + 0.2), (XR, by - 0.12, ZB + 0.9)))):
        beam(shell, "brace_%d" % k, p, q, 0.15, "wood_dark", extend=0.04)
    # ---- the roof and its scales banner, the swag valances
    roof(shell, det)
    for k, (a, b) in enumerate((((XL - 0.1, by + 0.1, ZF + 0.2), (-1.0, by + 0.1, ZF + 0.2)), ((-1.0, by + 0.1, ZF + 0.2), (XR + 0.1, by + 0.1, ZF + 0.2)))):
        pc.swag(shell, "swag_front_%d" % k, a, b, 0.42, "c1_swag", out=Z, sag=0.62, nx=4)
    for k, (a, b) in enumerate((((XL - 0.2, by + 0.1, ZF + 0.1), (XL - 0.2, by + 0.1, 0.0)), ((XL - 0.2, by + 0.1, 0.0), (XL - 0.2, by + 0.1, ZB - 0.1)))):
        pc.swag(shell, "swag_left_%d" % k, a, b, 0.42, "c1_swag", out=-X, sag=0.6, nx=4)
    # ---- ropes: king posts down to the posts, the flag post; guy ropes behind
    for k, (a, b) in enumerate((((RA - 0.15, KING_L - 0.45, 0.1), (XL, 4.0, ZF)), ((RA - 0.15, KING_L - 0.5, -0.05), (XL, 4.75, 0.0)),
                                ((RB + 0.12, KING_R - 0.3, 0.05), (XR, 4.0, ZB)), ((RB + 0.12, KING_R - 0.35, 0.1), (XR + 0.25, 3.95, ZF)))):
        ml.rope(det, "rope_%d" % k, a, b, d=0.08, sag=0.3, segs=4)
    for k, (x, z) in enumerate(((XL, ZB), (XR, ZB))):
        pc.guy(det, "guy_%d" % k, (x, 3.75, z - 0.1), (x + (0.5 if x < 0 else -0.5), 0.0, ZB - 0.95), sag=0.05, d=0.05)
    # ---- walls: the back, the back half of the sides (right side: up to the awning's back)
    pc.wall(shell, "wall_back", (XL, 0, ZB - 0.07), (XR, 0, ZB - 0.07), 0.0, by - 0.12, -Z, "c1_wall", nx=6)
    collide((XL, 0.0, ZB - 0.13, XR, by - 0.12, ZB - 0.01))
    pc.wall(shell, "wall_left", (XL - 0.07, 0, ZB), (XL - 0.07, 0, -0.15), 0.0, by - 0.12, -X, "c1_wall", nx=4)
    collide((XL - 0.13, 0.0, ZB, XL - 0.01, by - 0.12, -0.15))
    pc.wall(shell, "wall_right", (XR + 0.07, 0, -0.5), (XR + 0.07, 0, ZB), 0.0, by - 0.12, X, "c1_wall", nx=3)
    collide((XR + 0.01, 0.0, ZB, XR + 0.13, by - 0.12, -0.5))
    ml.banner(shell, "side_banner", (XL - 0.17, by - 0.2, -0.85), 0.62, 1.7, normal=(-1, 0, 0), region="c1_sidebanner", rod=True, wave=0.03)
    # curtains: cream tied to the flag post, red at the left of the entrance, cream at the right of the entrance
    pc.drape(shell, det, "drape_left", (XL - 0.12, by - 0.15, -0.2), (XL - 0.12, by - 0.15, 0.85), (XL - 0.16, 1.35, -0.05),
             (XL - 0.12, 0.03, -0.3), (XL - 0.12, 0.03, 0.15), -X, "c1_drape_cream", nx=3)
    pc.drape(shell, det, "drape_entr_l", (-1.05, by - 0.15, ZF - 0.12), (-0.35, by - 0.15, ZF - 0.12), (-0.97, 1.35, ZF - 0.16),
             (-1.1, 0.03, ZF - 0.14), (-0.75, 0.03, ZF - 0.14), Z, "c1_drape_red", nx=3)
    pc.drape(shell, det, "drape_entr_r", (XR - 0.62, by - 0.15, ZF - 0.12), (XR - 0.05, by - 0.15, ZF - 0.12), (XR - 0.22, 1.4, ZF - 0.16),
             (XR - 0.38, 0.03, ZF - 0.14), (XR - 0.12, 0.03, ZF - 0.14), Z, "c1_drape_cream", nx=3)
    # ---- the right awning (orange and cream stripes running front to back, as in the picture) sloping down to the
    #      front, on two front posts and a back post; lanterns on brackets on its front posts
    for k, (x, z) in enumerate(((3.1, AZ1), (AX, AZ1), (AX, AZ0))):
        top = (AY_OUT if z == AZ1 else AY_IN) + 0.38
        pc.banded_post(shell, det, "apost_%d" % k, x, z, top, d=0.36, foot_h=0.45, bands=(0.55, 1.5, top - 0.6), cap=(0.46, 0.22), collide_to=top)
    beam(shell, "a_beam_front", (XR, AY_OUT - 0.2, AZ1), (AX, AY_OUT - 0.2, AZ1), 0.22, "beam", extend=0.25)
    beam(shell, "a_beam_back", (XR, AY_IN - 0.2, AZ0), (AX, AY_IN - 0.2, AZ0), 0.22, "beam", extend=0.25)
    beam(shell, "a_beam_side", (AX, AY_IN - 0.08, AZ0), (AX, AY_OUT - 0.08, AZ1), 0.22, "beam", extend=0.2)
    za0, za1 = AZ0 - 0.3, AZ1 + 0.38     # the cloth's back and front edges

    def ay(z):
        return AY_IN + (AY_OUT - AY_IN) * (z - za0) / (za1 - za0)

    def AW(s, t):   # s across, from the main tent out to the outer posts; t from the back down to the front
        x = XR + 0.1 + (AX + 0.3 - XR - 0.1) * s
        z = za0 + (za1 - za0) * t
        y = ay(z) - 0.12 * math.sin(math.pi * t) - 0.05 * math.sin(math.pi * ((s * 8) % 1.0)) * math.sin(math.pi * min(1.0, t * 1.2)) + 0.06
        return v3(x, y, z)
    loft(shell, "awning", AW, 8, 3, "c1_awning", th=0.035, overlap=0.03)
    pc.valance(shell, "a_val_front", (XR + 0.1, AY_OUT + 0.04, za1), (AX + 0.3, AY_OUT + 0.04, za1), Z, h=0.42, region="c1_awning_val", n=3)
    pc.valance(shell, "a_val_side", (AX + 0.32, AY_OUT + 0.04, za1 - 0.02), (AX + 0.32, AY_IN + 0.04, za0), X, h=0.42, region="c1_awning_val", n=3)
    ml.rope(det, "a_rope", (RB + 0.1, KING_R - 0.4, -0.1), (AX + 0.25, AY_IN + 0.2, AZ0 - 0.2), d=0.07, sag=0.35, segs=4)
    for k, x in enumerate((3.1, AX)):
        pc.lantern_bracket(shell, det, "lamp_aw_%d" % k, (x, AY_OUT - 0.55, AZ1 + 0.19), (0.25 if k else -0.25, 0, 1), drop=0.55, size=0.36)
    # ---- lanterns under the front beam and inside
    for k, x in enumerate((-1.75, 0.85)):
        ml.lantern(shell, "lamp_front_%d" % k, (x, 2.5, ZF - 0.05), size=0.36, metal="iron", chain_to=(x, by - 0.15, ZF - 0.05))
    ml.lantern(shell, "lamp_in", (-0.6, 2.55, -0.4), size=0.34, metal="iron", chain_to=(-0.6, by - 0.1, -0.4))
    # ---- inside: front-left counter, side counter with herbs above, back shelves
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    ml.table_cloth(shell, "counter_cloth", cx0 + 0.05, cx1 - 0.05, cz0 + 0.02, cz1 + 0.02, y, hang=0.32, region="cloth_red", edge="c1_swag",
                   sides=("front",))
    for k, (x, col) in enumerate(((-2.72, "green"), (-2.44, "orange"))):
        ml.bottle(det, "big_potion_%d" % k, (x, y + 0.015, zc), col, r=0.11, h=0.26, shape="round", neck_h=0.08)
    pc.book_stack(det, "counter_books", (-1.95, y + 0.015, zc - 0.02), 3, rng)
    pc.scroll(det, "counter_scroll", (-1.5, y + 0.07, zc + 0.05), length=0.38, r=0.055, yaw=0.3)
    sx0, sx1, sz0, sz1 = SIDE_COUNTER
    stop = ml.counter(shell, "side_counter", sx0, sx1, sz0, sz1, h=COUNTER_H, detail=det)
    side_x = (sx0 + sx1) / 2
    for i, (z, col) in enumerate(((0.5, "green"), (0.83, "yellow"), (1.15, "blue"))):
        ml.bottle(det, "side_potion_%d" % i, (side_x, stop[1], z), col, r=0.1 - 0.015 * (i == 1), h=0.24, shape="round" if i != 1 else "tall", neck_h=0.08)
    pc.herbs_rod(shell, det, "herbs", (XL + 0.14, 2.85, 0.35), (XL + 0.14, 2.85, 1.25), 2, kinds=("herbs",), length=(0.62, 0.78), width=0.5, rng=rng)
    pc.herbs_rod(shell, det, "herbs_front", (XL + 0.3, 2.6, ZF - 0.3), (-2.15, 2.6, ZF - 0.3), 2, kinds=("herbs",), length=(0.78, 0.86), width=0.6,
                 rng=rng)
    levels = ml.shelf_unit(shell, "shelves", XL + 0.4, XR - 0.4, SHELF_Z[0], SHELF_Z[1], levels=(0.6, 1.2, 1.8, 2.4), h=2.7, back=True, uprights=4,
                           detail=det)
    lv = sorted(levels, key=lambda s: s[2])
    for j, (x0, x1, yy, zf, zb) in enumerate(lv):
        zc2 = (zf + zb) / 2
        if j in (1, 3):
            pc.potion_row(det, "shelf_pot_%d" % j, x0 + 0.1, x1 - 0.1, yy, zc2, rng, ("red", "blue", "green", "orange", "purple", "red"), n=10)
        elif j == 2:
            xx = x0 + 0.1
            for i in range(14):
                bw = 0.08 + 0.025 * rng.random()
                bh = 0.26 + 0.09 * rng.random()
                reg = ("cloth_red", "cloth_blue", "leather", "cloth_dark", "cloth_red", "leather_dark", "cloth_blue")[i % 7]
                box(det, "book_%d" % i, (xx, yy, zc2 - 0.12), (xx + bw, yy + bh, zc2 + 0.12), {"all": reg, "+2": "white", "-2": "white"})
                xx += bw + 0.012
                if i == 6:
                    xx += 0.45
            pc.book_stack(det, "shelf_books", (xx + 0.15, yy, zc2), 3, rng, w=0.24, d=0.26)
        else:
            for i, xx in enumerate((x0 + 0.3, x0 + 0.75, x1 - 0.7, x1 - 0.3)):
                ml.sack(det, "shelf_sack_%d" % i, (xx, yy, zc2), s=0.3, yaw=0.3 * i) if i % 2 == 0 else \
                    ml.crate(det, "shelf_box_%d" % i, (xx, yy, zc2), size=(0.36, 0.26, 0.32), yaw=0.2, solid=False)
    # ---- the rug out of the entrance
    ml.rug(shell, "rug", -0.75, 1.3, 0.55, 4.35, y=0.0, region="c1_rug")
    # ---- in front: chest on a crate, rolled carpets, sacks and an iron crate
    pc.iron_crate(shell, det, "chest_crate", (-2.62, 0.0, 2.85), size=(0.76, 0.52, 0.6), yaw=0.05)
    pc.chest(shell, det, "chest_front", (-2.62, 0.52, 2.85), size=(0.82, 0.58, 0.56), yaw=0.05)
    for k, (p0, p1) in enumerate((((-2.05, 0.31, 2.95), (-0.92, 0.31, 2.87)), ((-1.95, 0.31, 3.6), (-0.88, 0.31, 3.7)))):
        pc.carpet_roll(shell, "carpet_roll_%d" % k, p0, p1, 0.31, "c1_roll", "c1_end")
    collide((-2.1, 0.0, 2.6, -0.84, 0.62, 4.02))
    pc.square_sack(shell, det, "sack_l0", (-4.1, 0.0, 2.75), size=(0.66, 0.62, 0.52), yaw=0.15)
    pc.square_sack(shell, det, "sack_l1", (-3.9, 0.0, 3.32), size=(0.56, 0.5, 0.46), yaw=-0.2)
    pc.iron_crate(shell, det, "crate_l", (-3.32, 0.0, 3.15), size=(0.55, 0.6, 0.5), yaw=0.1)
    # ---- under the awning: the counter with the cream-and-red cloth, the big chest with the open book, crates, sacks
    ax0, ax1, az0, az1 = AW_COUNTER
    atop = ml.counter(shell, "aw_counter", ax0, ax1, az0, az1, h=1.0, detail=det)
    ay = atop[1]
    box(shell, "aw_cloth_top", (ax0, ay, az0), (ax1, ay + 0.015, az1 + 0.02), {"all": "beige"}, stretch=True)
    ml.plate(shell, "aw_cloth_front", ((ax0 + ax1) / 2, ay - 0.36, az1 + 0.03), ax1 - ax0 + 0.04, 0.74, "c1_runner", normal=(0, 0, 1), th=0.012,
             edge="beige")
    for k, (x, col) in enumerate(((2.0, "blue"), (2.22, "blue"), (2.62, "red"))):
        ml.bottle(det, "aw_potion_%d" % k, (x, ay + 0.015, (az0 + az1) / 2), col, r=0.075, h=0.18, shape="round" if k != 1 else "tall", neck_h=0.06)
    pc.book_stack(det, "aw_books", (1.82, ay + 0.015, (az0 + az1) / 2 - 0.05), 3, rng, covers=("cloth_red", "cloth_red", "leather"), w=0.3, d=0.36)
    ml.crate(det, "aw_box", (2.45, ay + 0.015, az0 + 0.12), size=(0.34, 0.24, 0.26), yaw=-0.1, solid=False)
    pc.chest(shell, det, "chest_aw", (4.2, 0.0, 1.88), size=(1.05, 0.66, 0.64), yaw=-0.03, domed=False)
    ml.crate(shell, "book_box", (4.23, 0.66, 1.83), size=(0.52, 0.18, 0.4), yaw=-0.03, solid=False)
    pc.open_book(det, "open_book", (4.23, 0.84, 1.83), w=0.5, d=0.34, yaw=-0.03, tilt=0.25)
    pc.iron_crate(shell, det, "aw_crate_0", (4.82, 0.0, 0.95), size=(0.62, 0.6, 0.6), yaw=0.08)
    pc.iron_crate(shell, det, "aw_crate_1", (4.84, 0.6, 0.95), size=(0.46, 0.4, 0.44), yaw=-0.1)
    ml.bottle(det, "aw_crate_potion", (4.82, 1.0, 0.95), "green", r=0.07, h=0.17, shape="round")
    decor.block("furnish:spruce_crate", 3.95, 0.0, -0.05, facing="front", alt="minecraft:barrel", fallback="crate")
    decor.block("landsoficaria:cypress_barrel", 4.82, 0.0, -0.6, facing="neg_x", alt="minecraft:barrel", fallback="barrel")
    decor.block("farmersdelight:rice_bag", 3.45, 0.0, 2.8, facing="front", scale=0.8, fallback="c_burlap")
    pc.square_sack(shell, det, "sack_aw", (2.72, 0.0, 2.75), size=(0.5, 0.52, 0.42), yaw=0.3)
    decor.block("furnish:book_pile", 4.55, 0.84, 1.98, facing="front", scale=0.7, solid=False, fallback="leather")
    ml.barrel(shell, "aw_barrel", (3.85, 0.0, -0.95), r=0.33, h=0.82)
    return root


def item_icon(path):
    """16x16: the red marquee with its cream flame stripes and two peaks, the orange awning on the right."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, cr, gold, orange = P.red, P.cream, P.gold, ORANGE
    wood = (150, 96, 50)
    for y in range(1, 10):
        half = 1.0 + (y - 1) * 0.85
        for x in range(0, 12):
            dx = x - 5.5
            if abs(dx) <= half:
                stripe = int((dx + 8) // 2) % 2
                c = cr if (stripe and y > 4) or y == 1 else red
                p[x, y] = c + (255,)
    for x in range(0, 12):
        p[x, 10] = (red if x % 3 else gold) + (255,)
    for y in range(7, 11):
        for x in range(11, 16):
            if y - 7 <= (x - 11) // 2 + 1:
                p[x, y] = (orange if x % 2 else cr) + (255,)
    for x in (0, 11, 15):
        for y in range(10, 16):
            p[x, y] = wood + (255,)
    for y in range(11, 15):
        for x in range(1, 11):
            p[x, y] = (60, 36, 22, 255)
    p[5, 0] = p[6, 0] = wood + (255,)
    p[3, 12] = p[4, 12] = gold + (255,)
    for x in range(1, 15):
        p[x, 15] = (red if 4 <= x <= 8 else (90, 60, 34)) + (255,)
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
