#!/usr/bin/env python3
"""tente_lion_drapee — Tente drapée au lion / Draped Lion Tent (1.26.0, market tents group B; reference:
scratchpad/ref2/tente_lion_drapee_ref.png, picture 095).

A square royal-blue and cream merchant tent of Lion Port, one block (TentType group "tents"), about 10 blocks wide with its
two side awnings, 6.5 deep, the flag at about 8.7:

  - the main tent: a concave four-sided pointed roof, wide blue and cream stripes radiating from the peak, its eave line
    curving down between the corners, a cream valance with gold-edged pointed dags all round; a tall wooden flag pole
    rises from the peak (rope collar, wooden blocks) and flies a blue LION FLAG with a gold border;
  - four big squared posts on light grey STONE FEET, iron bands, capped tops, iron straps where the eave beams meet them,
    knee braces; twisted ROPE swags along the front eave and down the awnings, rope coils and knotted tails on the posts;
  - two blue LION BANNERS (gold border, stepped pointed bottom, gold lion rampant) hanging from the front eave, CREAM
    DRAPES with a blue edge tied back against the two front posts, two glowing lanterns hanging inside under the eave;
  - two lower side AWNINGS, striped blue and cream, with blue / cream gold-edged dagged valances, on outer posts with
    stone feet and cross-bar caps, a lantern on an iron bracket at each outer post, ivy hanging at the right one;
    left: a counter under a blue cloth with the gold lion (red cloth rolls, folded linen, big potions, a small lantern),
    a shelf of jars, sacks and books behind it, a tied sack in front; right: crates of apples, greens and cheese, a
    barrel with a plant, a planter and a pot of purple flowers inside the right front corner;
  - inside: a low WOODEN FLOOR of planks, the blue RUG with the gold border and the faded gold lion, the back SHELVES full
    of glowing potions, jars, sacks and cloth rolls, an iron-banded CHEST on a crate at the left of the entrance, the
    merchant's COUNTER at the back right (cheese, apples, bottles) with the merchant's place behind it.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in past the chest and
round the counter's left end. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_lion_drapee.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_lion_drapee.json, models/entity + blockbench/tente_lion_drapee.bbmodel,
textures/entity/tente_lion_drapee.png, textures/item/tente_lion_drapee.png, interiors/tente_lion_drapee_decor.json.
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
NAME = "tente_lion_drapee"
v3, norm, add_cube, beam, loft, Bone = pb.v3, pb.norm, pb.add_cube, pb.beam, pb.loft, pb.Bone
EYE, UP, X, Z = pb.EYE, pb.UP, pb.X, pb.Z
ry, box, collide = pb.ry, pb.box, pb.collide
NAVY, CREAM, GOLD = pb.NAVY, pb.CREAM, pb.GOLD

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 2.75, 2.6            # main posts x = +-HW, z = +-HD
EAVE = 3.45                   # eave beams (their top)
POST_TOP = 4.1
RW, RD, RY = 3.12, 2.97, 3.62   # the main roof's eave corners (+-RW, RY, +-RD)
APEX = 5.2
AX = 4.9                     # outer posts of the awnings
AZ0, AZ1 = -1.2, HD           # awnings from z = AZ0 to AZ1
AY_IN, AY_OUT = 3.36, 2.92    # awning roof heights at the main post line and at the outer posts
FLOOR = 0.08
POLE_TOP = 7.45
COUNTER = (0.0, 2.3, -0.9, -0.3)   # x0, x1, z0, z1
COUNTER_H = 0.98
NPC_SPOT = (0.6, -1.98)       # (x0, z0) of the merchant's free 1 x 1 x 2.2 place
SHELF_Z = (-2.5, -2.05)
STRIPES = 5
AW_STRIPES = 4


def paint_wall(img):
    rng = random.Random(9501)
    pb.stripes(img, 6, (NAVY, CREAM), rng, fold=0.18)
    px = img.load()
    w, h = img.size
    for y in range(h - 3, h):
        for x in range(w):
            px[x, y] = ml._jitter(GOLD if y > h - 3 else pb.GOLD_D, rng, 8) + (255,)


def regions(atlas):
    own = [
        ("d_roof", 40 * STRIPES, 80, pb.paint_roof(STRIPES, 9502)),
        ("d_rug", 80, 128, pb.paint_rug(9503, "lion", faded=0.45)),
        ("d_banner", 48, 96, pb.paint_banner("lion", 9504)),
        ("d_wall", 96, 64, paint_wall),
        ("d_awning", 40 * AW_STRIPES, 48, pb.paint_roof(AW_STRIPES, 9505, fold=0.12)),
        ("d_runner", 56, 48, pb.paint_runner("lion", 9506)),
        ("d_flag", 64, 32, pb.paint_flag(9507)),
        ("d_val", 192, 24, pb.paint_valance(8, 9508, cols=(CREAM, CREAM), shape="dag")),
        ("d_val_aw", 192, 24, pb.paint_valance(8, 9509, cols=(NAVY, CREAM), shape="dag")),
        "b_post", "b_stone", "b_band", "b_chest", "b_cheese", "b_sack", "b_roll_red", "b_drape",
    ]
    pb.add_regions(atlas, own, m1=["flowers_purple", "pot_clay", "soil", "sprout", "potion_green", "potion_cyan", "potion_orange",
                                   "potion_purple", "potion_red", "potion_blue", "potion_yellow", "glass", "cork", "jar", "jar_top",
                                   "linen", "book_red", "book_blue", "book_brown", "book_green", "book_top"])


# ---------------------------------------------------------------- the build
def build(decor):
    rng = random.Random(95)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)

    # ---- the low plank floor (not solid: 1 px high) and the rug
    n = 12
    for k in range(n):
        x0 = -2.95 + 5.9 * k / n
        zf = 3.3 - 0.18 * ((k * 7) % 3)
        box(shell, "floor_%d" % k, (x0 + 0.01, 0.0, -2.85), (x0 + 5.9 / n - 0.01, FLOOR, zf), {"all": "plank", "+2": "plank"}, u_dir=Z)
    box(shell, "floor_edge", (-2.98, 0.0, 2.9), (2.98, FLOOR + 0.08, 3.08), {"all": "plank_dark"}, u_dir=X)
    box(shell, "floor_step", (-2.3, 0.0, 3.08), (2.1, FLOOR, 3.42), {"all": "plank"}, u_dir=X)
    ml.rug(shell, "rug", -0.8, 1.2, -0.15, 3.15, y=FLOOR, region="d_rug")

    # ---- posts: main four on stone feet, awning outer posts with cross-bar caps
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]
    for k, (x, z) in enumerate(corners):
        pb.sq_post(shell, det, "post_%d" % k, x, z, POST_TOP, d=0.44, stone=0.62, stone_w=0.66, bands=(1.55, 3.0), cap="block",
                   collide_to=EAVE)
    for k, (x, z) in enumerate(((-AX, AZ1), (-AX, AZ0), (AX, AZ1), (AX, AZ0))):
        pb.sq_post(shell, det, "apost_%d" % k, x, z, AY_OUT + 0.18, d=0.36, stone=0.55, stone_w=0.56, bands=(2.0,), cap="cross",
                   collide_to=AY_OUT)
    # eave beams with iron straps at the posts, knee braces
    by = EAVE - 0.16
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.3, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26,
             extend=0.18)
    for k, (x, z) in enumerate(corners):
        for j, (dx, dz) in enumerate(((0.235, 0), (0, 0.235))):
            sx = 1 if x < 0 else -1
            sz = 1 if z < 0 else -1
            box(det, "strap_%d_%d" % (k, j), (x + sx * dx - 0.03 - (0.12 if dz else 0), by - 0.2, z + sz * dz - 0.03 - (0.12 if dx else 0)),
                (x + sx * dx + 0.03 + (0.12 if dz else 0), by + 0.2, z + sz * dz + 0.03 + (0.12 if dx else 0)), "iron")
    for k, (p, q) in enumerate((((-HW + 0.2, EAVE - 1.15, HD), (-HW + 0.95, by - 0.12, HD)), ((HW - 0.2, EAVE - 1.15, HD), (HW - 0.95, by - 0.12, HD)),
                                ((-HW, EAVE - 1.15, -HD + 0.2), (-HW, by - 0.12, -HD + 0.95)), ((HW, EAVE - 1.15, -HD + 0.2), (HW, by - 0.12, -HD + 0.95)))):
        beam(shell, "brace_%d" % k, p, q, 0.15, "wood_dark", extend=0.05)
    beam(shell, "tie_beam", (-HW, by - 0.05, 2.25), (HW, by - 0.05, 2.25), 0.16, "wood_dark", extend=0.08)

    # ---- the main roof: four concave sides, stripes radiating from the peak, a curved eave line
    apex = v3(0, APEX, 0)
    rc = [v3(-RW, RY, RD), v3(RW, RY, RD), v3(RW, RY, -RD), v3(-RW, RY, -RD)]
    outs = [Z, X, -Z, -X]
    edges = []
    for k in range(4):
        P = pb.hip_side(shell, "roof_%d" % k, apex, apex, rc[k], rc[(k + 1) % 4], "d_roof", nx=STRIPES, ny=5, droop=0.1, a=0.5,
                        edge_sag=0.14, folds=0.04)
        edges.append(P)
        pb.valance_curve(shell, "valance_%d" % k, lambda s, P=P: P(s, 1.0), outs[k], h=0.46, region="d_val", nx=4)
    # the canvas gathered round the pole: a rope collar and a wooden block
    box(shell, "peak_cloth", (-0.26, APEX - 0.25, -0.26), (0.26, APEX + 0.08, 0.26), "cloth_beige", stretch=True)
    box(det, "peak_rope", (-0.3, APEX - 0.05, -0.3), (0.3, APEX + 0.1, 0.3), "rope")
    # ---- the flag pole and the lion flag
    beam(shell, "flag_pole", (0, APEX - 0.4, 0), (0, POLE_TOP, 0), 0.3, {"all": "b_post", "+1": "end_grain", "-1": "end_grain"})
    box(shell, "pole_block", (-0.3, APEX + 0.08, -0.3), (0.3, APEX + 0.42, 0.3), {"all": "wood", "+2": "end_grain"})
    pb.band(det, "pole_block_band", 0, 0, 0.31, APEX + 0.3, 0.07)
    box(shell, "pole_mid", (-0.25, POLE_TOP - 1.25, -0.25), (0.25, POLE_TOP - 1.0, 0.25), {"all": "wood", "+2": "end_grain"})
    box(shell, "pole_cap", (-0.32, POLE_TOP, -0.32), (0.32, POLE_TOP + 0.34, 0.32), {"all": "wood", "+2": "end_grain"})
    box(det, "pole_cap_top", (-0.2, POLE_TOP + 0.34, -0.2), (0.2, POLE_TOP + 0.5, 0.2), {"all": "wood_dark", "+2": "end_grain"})

    def F(s, t):
        return v3(0.16 + 2.0 * s, POLE_TOP - 0.05 - 0.98 * t - 0.2 * s * s + 0.09 * math.sin(s * math.pi * 2.2),
                  0.22 * math.sin(s * math.pi * 1.7) * s + 0.02 * t)
    loft(shell, "flag", F, 5, 1, "d_flag", th=0.025)

    # ---- banners on the front eave, rods with gold knobs
    for k, bx in enumerate((-1.15, 1.15)):
        s = (bx + RW) / (2 * RW)
        e = edges[0](s, 1.0)
        top = v3(bx, e[1] - 0.02, RD + 0.1)
        ml.banner(shell, "banner_%d" % k, top, 0.8, 1.5, normal=(0, 0, 1), region="d_banner", rod=True, wave=0.03)
    # ---- drapes tied back against the front posts (inside), lanterns hanging inside under the eave
    for k, sx in enumerate((-1, 1)):
        a, b = (sx * (HW - 0.12), by + 0.05, HD + 0.02), (sx * (HW - 1.8), by + 0.05, HD + 0.02)
        pb.drape(shell, det, "drape_%d" % k, a if sx < 0 else b, b if sx < 0 else a, (sx * (HW - 0.5), 1.62, HD + 0.08),
                 (sx * (HW - 0.15), FLOOR + 0.02, HD + 0.02) if sx < 0 else (sx * (HW - 1.2), FLOOR + 0.02, HD - 0.04),
                 (sx * (HW - 1.2), FLOOR + 0.02, HD - 0.04) if sx < 0 else (sx * (HW - 0.15), FLOOR + 0.02, HD + 0.02), Z,
                 region="b_drape", nx=4, tie_region="gold")
    for k, x in enumerate((-0.25, 1.9)):
        ml.lantern(shell, "lamp_in_%d" % k, (x, 2.7, 2.25), size=0.34, metal="iron", chain_to=(x, by - 0.12, 2.25))
    # ---- rope swags along the front eave, knotted tails and coils on the posts
    pb.swag(det, "swag_fl", (-HW, POST_TOP - 0.2, HD + 0.26), (-1.15, RY - 0.05, RD + 0.16), sag=0.26, d=0.12, segs=4)
    pb.swag(det, "swag_fm", (-1.15, RY - 0.05, RD + 0.16), (1.15, RY - 0.05, RD + 0.16), sag=0.3, d=0.12, segs=4)
    pb.swag(det, "swag_fr", (1.15, RY - 0.05, RD + 0.16), (HW, POST_TOP - 0.2, HD + 0.26), sag=0.26, d=0.12, segs=4)
    for k, sx in enumerate((-1, 1)):
        x = sx * HW
        ml.rope(det, "post_tail_%d" % k, (x - sx * 0.05, POST_TOP - 0.2, HD + 0.27), (x - sx * 0.12, 2.35, HD + 0.29), d=0.1, segs=2)
        for j, yk in enumerate((3.0, 2.45)):
            add_cube(det, "post_tail_knot_%d_%d" % (k, j), (x - sx * (0.08 + 0.03 * j), yk, HD + 0.28), EYE, (0.18, 0.2, 0.18), "rope")
        for j in range(2):
            y = POST_TOP - 0.42 - 0.12 * j
            box(det, "coil_%d_%d" % (k, j), (x - 0.29, y, HD - 0.29), (x + 0.29, y + 0.1, HD + 0.29), "rope")
        # rope down the awning front, from the main post top to the outer post
        pb.swag(det, "swag_aw_%d" % k, (x, POST_TOP - 0.25, HD + 0.2), (sx * AX, AY_OUT + 0.25, AZ1 + 0.2), sag=0.18, d=0.08, segs=3,
                knots=False)

    # ---- the awnings: sloping striped roofs, beams, braces, dagged valances, back walls
    for k, sx in enumerate((-1, 1)):
        for j, z in enumerate((AZ1, AZ0)):
            beam(shell, "aw_beam_%d_%d" % (k, j), (sx * HW, AY_IN - 0.18, z), (sx * AX, AY_OUT - 0.18, z), 0.22, "beam", extend=0.12)
            beam(shell, "aw_brace_%d_%d" % (k, j), (sx * AX, AY_OUT - 0.95, z), (sx * (AX - 0.65), AY_OUT - 0.25, z), 0.12, "wood_dark")
        beam(shell, "aw_side_%d" % k, (sx * AX, AY_OUT - 0.1, AZ0), (sx * AX, AY_OUT - 0.1, AZ1), 0.22, "beam", extend=0.15)
        xo = sx * (AX + 0.3)

        def A(s, t, sx=sx, xo=xo):
            z = (AZ0 - 0.25) + (AZ1 - AZ0 + 0.62) * s
            x = sx * (HW + 0.02) + (xo - sx * (HW + 0.02)) * t
            frac = (s * AW_STRIPES) % 1.0
            y = AY_IN + 0.04 - (AY_IN - AY_OUT + 0.08) * t - 0.1 * math.sin(math.pi * t) - 0.04 * math.sin(math.pi * frac)
            return v3(x, y, z)
        loft(shell, "awning_%d" % k, (lambda s, t, A=A: A(1 - s, t)) if sx < 0 else A, AW_STRIPES, 3, "d_awning", th=0.035, overlap=0.03)
        yo = A(0, 1)[1]
        pb.valance(shell, "aw_val_front_%d" % k, (sx * (HW + 0.05), AY_IN - 0.02, AZ1 + 0.38), (xo, yo - 0.02, AZ1 + 0.38), Z, h=0.42,
                   region="d_val_aw", nx=2)
        pb.valance(shell, "aw_val_side_%d" % k, (xo + sx * 0.02, yo - 0.02, AZ1 + 0.36), (xo + sx * 0.02, yo - 0.02, AZ0 - 0.24), v3(sx, 0, 0),
                   h=0.42, region="d_val_aw", nx=2)
        # back walls: the awning's back and the main tent's side behind it
        wa, wb_ = (sx * AX, 0, AZ0 - 0.05), (sx * HW, 0, AZ0 - 0.05)
        pb.wall(shell, "aw_wall_%d" % k, wa if sx < 0 else wb_, wb_ if sx < 0 else wa, 0.0, AY_OUT - 0.25, -Z, "d_wall", nx=3)
        collide((min(wa[0], wb_[0]), 0.0, AZ0 - 0.11, max(wa[0], wb_[0]), AY_OUT - 0.25, AZ0 + 0.01))
        x = sx * (HW + 0.03)
        pb.wall(shell, "side_wall_%d" % k, (x, 0, -HD) if sx < 0 else (x, 0, AZ0), (x, 0, AZ0) if sx < 0 else (x, 0, -HD), 0.0, by - 0.1,
                v3(sx, 0, 0), "d_wall", nx=3)
        collide((x - 0.06, 0.0, -HD, x + 0.06, by - 0.1, AZ0))
        # lantern on an iron bracket at the outer front post
        pb.bracket_lantern(shell, det, "aw_lamp_%d" % k, (sx * (AX - 0.18), AY_OUT - 0.55, AZ1 + 0.05), (-sx * 0.25, 0, 1), drop=0.52,
                           size=0.36, arm=0.42)
    # back wall of the main tent
    pb.wall(shell, "back_wall", (HW, 0, -HD - 0.06), (-HW, 0, -HD - 0.06), 0.0, by - 0.1, -Z, "d_wall", nx=6)
    collide((-HW, 0.0, -HD - 0.12, HW, by - 0.1, -HD))
    # ivy hanging at the right awning's front, near the main post
    for k, (x, ln, w, dz) in enumerate(((HW + 0.3, 1.45, 0.5, 0.25), (HW + 0.72, 1.0, 0.46, 0.27), (HW + 0.05, 0.9, 0.4, 0.3),
                                        (HW + 0.5, 1.7, 0.36, 0.22), (HW + 1.0, 0.7, 0.4, 0.26))):
        ml.vine(det, "ivy_%d" % k, (x, AY_IN - 0.05 - 0.22 * (x - HW), AZ1 + dz), ln, w, normal=(0, 0, 1))
    ml.vine(det, "ivy_side", (HW + 0.3, AY_IN - 0.1, AZ1 - 0.1), 1.1, 0.5, normal=(1, 0, 0))

    # ---- the back shelves: potions, jars, sacks, cloth rolls
    levels = ml.shelf_unit(shell, "shelves", -HW + 0.4, HW - 0.4, SHELF_Z[0], SHELF_Z[1], levels=(0.62, 1.22, 1.82, 2.42), h=2.8, back=True,
                           uprights=4, detail=det)
    lv = sorted(levels, key=lambda s: s[2])
    pb.potion_rows(det, "shelf_pot", [lv[1], lv[2]], rng, ("green", "cyan", "orange", "purple", "red", "blue", "yellow"))
    x0, x1, yy, zf, zb = lv[0]
    zc = (zf + zb) / 2
    for i, (dx, reg) in enumerate(((0.35, "b_roll_red"), (0.62, "cloth_blue"), (0.89, "b_roll_red"))):
        pb.scroll(det, "roll_%d" % i, (x0 + dx, yy + 0.09, zc), length=0.42, r=0.085, yaw=math.pi / 2, region=reg)
    for i, dx in enumerate((1.6, 2.1, 3.3)):
        ml.sack(det, "low_sack_%d" % i, (x0 + dx, yy, zc), s=0.34, yaw=0.3 * i, region="b_sack")
    ml.crate(det, "low_box", (x1 - 0.35, yy, zc), size=(0.45, 0.32, 0.36), solid=False)
    x0, x1, yy, zf, zb = lv[3]
    zc = (zf + zb) / 2
    for i in range(6):
        xx = x0 + 0.25 + i * (x1 - x0 - 0.5) / 5
        if i % 3 == 1:
            ml.sack(det, "top_sack_%d" % i, (xx, yy, zc), s=0.3, yaw=0.4 * i, region="b_sack")
        else:
            wb.jar(det, "top_jar_%d" % i, (xx, yy, zc), r=0.08 + 0.02 * (i % 2), h=0.2 + 0.04 * (i % 3))

    # ---- the counter at the back right, its goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    for k, (p, q) in enumerate((((cx0 + 0.15, 0.12, cz1 + 0.03), (cx1 - 0.15, COUNTER_H - 0.18, cz1 + 0.03)),
                                ((cx0 + 0.15, COUNTER_H - 0.18, cz1 + 0.03), (cx1 - 0.15, 0.12, cz1 + 0.03)))):
        beam(det, "counter_x_%d" % k, p, q, 0.06, "wood_dark", width=0.03)
    pb.cheese_pile(det, "cheese", (0.45, y, zc), n=3)
    pb.produce_crate(shell, "counter_apples", (1.2, y, zc), size=(0.5, 0.24, 0.4), content="apples", solid=False)
    for k, (dx, c) in enumerate(((1.75, "green"), (1.92, "orange"), (2.08, "purple"))):
        ml.bottle(det, "counter_pot_%d" % k, (dx, y, zc + 0.05 * (k % 2)), c, r=0.06, h=0.18, shape="round", glow=True)
    ml.sack(det, "counter_sack", (cx1 - 0.1, 0.0, cz1 + 0.35), s=0.4, yaw=0.3, region="b_sack")

    # ---- the chest on a crate at the left of the entrance
    decor.block("furnish:spruce_crate", -1.55, FLOOR, 1.95, facing="front", alt="minecraft:barrel", fallback="crate")
    pb.chest(shell, det, "chest", (-1.55, FLOOR + 1.0, 1.95), w=0.86, d=0.6, h=0.62)
    # a crate with sacks at the back left inside, a sack on the floor
    ml.crate(shell, "bl_crate", (-1.95, FLOOR, -1.55), size=0.75, yaw=0.1, solid=True)
    decor.block("farmersdelight:rice_bag", -1.95, FLOOR + 0.75, -1.55, facing="front", scale=0.6, fallback="sack", solid=False)
    ml.sack(det, "bl_sack", (-1.15, FLOOR, -1.75), s=0.42, yaw=-0.4, region="b_sack")
    # inside the right front corner: a crate with a pot of purple flowers, a planter of purple flowers
    ml.crate(shell, "fr_crate", (2.05, FLOOR, 1.05), size=0.62, yaw=-0.12, solid=True)
    p1.pot(det, "fr_pot", (2.05, FLOOR + 0.62, 1.05), r=0.13, h=0.18, plant="flowers_purple", ph=0.42, pw=0.46)
    pb.planter(shell, det, "planter", (1.75, FLOOR, 1.92), w=0.7, d=0.42, h=0.38, plant="flowers_purple", n=3)

    # ---- the left awning: counter under the lion cloth, shelf behind, a sack in front
    lx0, lx1, lz0, lz1 = -4.35, -3.0, 1.35, 2.25
    top = ml.counter(shell, "l_counter", lx0, lx1, lz0, lz1, h=0.95, detail=det)
    y = top[1]
    box(shell, "l_cloth", (lx0 - 0.02, y, lz0 - 0.02), (lx1 + 0.02, y + 0.015, lz1 + 0.06), {"all": "cloth_blue"}, stretch=True, u_dir=X)
    ml.plate(shell, "l_runner", ((lx0 + lx1) / 2, y - 0.38, lz1 + 0.07), 0.95, 0.8, "d_runner", normal=(0, 0, 1), th=0.012, edge="cloth_blue")
    for k, (dx, dy, dz) in enumerate(((0.0, 0.09, -0.12), (0.0, 0.09, 0.12), (0.0, 0.25, 0.0))):
        pb.scroll(det, "l_roll_%d" % k, (lx0 + 0.3 + dx, y + dy, (lz0 + lz1) / 2 + dz), length=0.5, r=0.085, yaw=0.0, region="b_roll_red")
    for k in range(2):
        for j in range(3):
            add_cube(det, "l_linen_%d_%d" % (k, j), (lx0 + 0.82, y + 0.05 + 0.1 * j, (lz0 + lz1) / 2 - 0.18 + 0.36 * k), ry(0.05 * j),
                     (0.42, 0.09, 0.3), "linen", stretch=True)
    for k, (dx, dz, c) in enumerate(((1.1, -0.15, "cyan"), (1.22, 0.15, "green"))):
        wb.octo(det, "glow_l_flask_%d" % k, (lx0 + dx, y, (lz0 + lz1) / 2 + dz), 0.11, 0.22, {"all": "potion_" + c}, stretch=True)
        add_cube(det, "l_flask_neck_%d" % k, (lx0 + dx, y + 0.28, (lz0 + lz1) / 2 + dz), EYE, (0.07, 0.12, 0.07), "glass", stretch=True)
    ml.lantern(shell, "l_lamp_small", (lx1 - 0.12, y + 0.16, lz1 - 0.15), size=0.2, metal="gold")
    lv2 = ml.shelf_unit(shell, "l_shelf", -4.3, -3.0, AZ0 + 0.05, AZ0 + 0.45, levels=(0.7, 1.35), h=1.9, back=False, uprights=2, detail=det)
    for i, (xa, xb, yy, zf, zb) in enumerate(lv2):
        zc = (zf + zb) / 2
        if i == 0:
            for j in range(3):
                ml.sack(det, "l_shelf_sack_%d" % j, (xa + 0.22 + 0.4 * j, yy, zc), s=0.32, yaw=0.5 * j, region="b_sack")
        else:
            for j in range(4):
                wb.jar(det, "l_shelf_jar_%d" % j, (xa + 0.15 + 0.3 * j, yy, zc), r=0.08, h=0.2)
    decor.block("farmhouse_decorations:pile_of_books", -3.4, 1.9, AZ0 + 0.25, facing="front", fallback="leather", solid=False)
    pb.big_sack(shell, det, "l_big_sack", (-4.0, 0.0, 3.05), yaw=0.3, w=0.56, h=0.8)
    collide((-4.3, 0.0, 2.75, -3.7, 0.56, 3.35))

    # ---- the right awning: crates of apples, greens and cheese, a barrel with a plant
    ml.crate(shell, "r_crate_0", (3.3, 0.0, 0.0), size=0.8, yaw=0.05, solid=True)
    pb.produce_crate(shell, "r_apples", (3.3, 0.8, 0.0), size=(0.7, 0.32, 0.55), content="apples", solid=True)
    decor.block("farmersdelight:cabbage_crate", 4.1, 0.0, 0.05, facing="front", scale=0.8, fallback="produce")
    ml.crate(shell, "r_crate_1", (3.45, 0.0, 1.45), size=0.72, yaw=-0.08, solid=True)
    pb.cheese_pile(det, "r_cheese", (3.45, 0.72, 1.45), n=3)
    decor.block("furnish:spruce_crate", 4.2, 0.0, 1.55, facing="front", scale=0.7, alt="minecraft:barrel", fallback="crate")
    pb.produce_crate(shell, "r_greens", (4.2, 0.7, 1.55), size=(0.6, 0.26, 0.5), content="produce", solid=True)
    ml.barrel(shell, "r_barrel", (3.05, 0.0, 3.05), r=0.32, h=0.8)
    p1.pot(det, "r_barrel_pot", (3.05, 0.8, 3.05), r=0.11, h=0.15, plant="sprout", ph=0.4, pw=0.42)
    return root


def item_icon(path):
    pb.stall_icon(path, roof="pyramid")


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
