#!/usr/bin/env python3
"""tente_draperie — Tente aux draperies rouges / Red Drapery Tent (1.26.0, market group E; reference:
scratchpad/ref2/tente_draperie_ref.png, picture 122).

A square red-and-cream merchant tent, one block (TentType group "tents"), about 10 blocks wide with its right awning,
the guy rope and the goods outside, the finial at about 6.8:

  - four big squared dark-wood posts with grey riveted iron bands, the two front ones tall with stacked cap blocks
    rising above the roof, the back ones lower; heavy eave beams, a capped block in the middle of the front eave;
  - the four-sided roof, sagging between the hips, red stripes sprinkled with small gold motifs alternating with cream
    stripes, rising to a small square CUPOLA framed by wooden corner blocks, hung with red gold-fringed panels, under a
    little red pyramid and a gold onion finial; thick ropes from the cupola down to the front post caps and a guy rope
    from the front-left post to a peg on the ground;
  - the gold-fringed RED DRAPES: two staggered rows of hanging panels under the front eave (red with a gold border, a
    gold fringe and a gold diamond motif, and cream ones), more panels on the sides;
  - a deep red-purple CURTAIN tied back with a gold band on the front-right post, a red patterned drape over the left
    side, red-and-cream striped back wall;
  - BUNTING on a rope from the front-right post to a pole on the right awning (red, purple, cream, gold pennants);
  - the right AWNING: red cloth with a gold border sagging over two posts, its outer edge fringed, a fruit stand under
    it (flower pots, a basket of red apples, a basket of lemons on crates);
  - inside: back shelves full of potions (orange, purple, red, green) and jars, the long counter (cheese blocks, a tub,
    potions, the BLUE runner with gold motifs and a dagged gold hem), bunches of grapes, lavender and herbs hanging from
    a rail under the front eave, four glowing lanterns;
  - outside left: ROLLED CARPETS standing against the front-left post (cream, red and purple with gold patterns),
    iron-banded barrels, cream sacks, a crate with a pot of herbs; in front: two crates with a basket of red flowers and
    a basket of oranges and apples; the RED patterned RUG in front of the counter.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in by the gap between
the counter's right end and the front-right post (under the tied curtain). No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_draperie.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_draperie.json, models/entity + blockbench/tente_draperie.bbmodel,
textures/entity/tente_draperie.png, textures/item/tente_draperie.png, interiors/tente_draperie_decor.json.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_e as pe  # noqa: E402

ml = pe.ml
NAME = "tente_draperie"
v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _scale = ml._rgb, ml._scale

RED, RED_DARK, CREAM = _rgb("881c2e"), _rgb("4e0e1a"), _rgb("e4cea4")
PLUM = _rgb("5e1a3a")           # the tied curtain's deep red-purple
BLUE = _rgb("3c4c8c")
GOLD = pe.GOLD

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 3.0, 2.3           # main posts at x = +-HW, z = +-HD
PD = 0.58                   # post section
EAVE = 3.5                  # top of the eave beams (the roof's lower edge)
FRONT_TOP, BACK_TOP = 4.45, 3.9
RW, RD = HW + 0.3, HD + 0.3  # the roof's eave half sizes
CUP = 0.64                  # the cupola's half size
CUP_Y0, CUP_Y1 = 5.15, 5.85  # the roof's top square / the cupola's top
EXT_X = 4.95                # the right awning's outer posts
EXT_Z = (1.85, -1.15)
COUNTER = (-2.5, 1.6, 0.9, 1.5)   # x0, x1, z0, z1
COUNTER_H = 1.0
NPC_SPOT = (0.3, -0.8)    # (x0, z0) of the free 1 x 1 x 2.2 place behind the counter
SHELF_Z = (-2.0, -1.5)


def add_regions(atlas):
    s = 3100
    atlas.add("dr_roof", 160, 96, pe.stripes([_scale(RED, 0.92), CREAM], 5, s, motif="cross", motif_step=(11, 14)))
    atlas.add("dr_rug", 128, 96, pe.rug("a8302e", "4a1436", "e89a30", "6a2a72", s + 1))
    atlas.add("dr_curtain", 64, 96, pe.stripes([PLUM, _scale(PLUM, 0.86)], 4, s + 2, motif="diamond", motif_col=_rgb("b07a40"), motif_step=(12, 16),
                                              fold=0.3, seams=False, hem=(GOLD, 5)))
    atlas.add("dr_pan_long", 48, 96, pe.panel(RED, s + 3, fringe=7, motif="diamond"))
    atlas.add("dr_pan_red", 48, 72, pe.panel(RED, s + 4, fringe=7, motif="diamond"))
    atlas.add("dr_pan_cream", 48, 72, pe.panel(CREAM, s + 5, fringe=7, motif=None, dark=_rgb("b89a6a")))
    atlas.add("dr_wall", 128, 64, pe.stripes([RED, CREAM], 6, s + 6, fold=0.25, hem=(GOLD, 4)))
    atlas.add("dr_drape_l", 64, 64, pe.panel(RED, s + 7, fringe=0, motif="diamond", fold=0.25))
    atlas.add("dr_awning", 128, 48, pe.stripes([RED, _scale(RED, 0.94)], 4, s + 8, fold=0.35, seams=False, hem=(GOLD, 4)))
    atlas.add("dr_runner", 48, 48, pe.panel(BLUE, s + 9, fringe=0, motif="diamond", dags=5))
    atlas.add("dr_cup", 48, 32, pe.panel(RED, s + 10, fringe=7, motif="cross" and None))
    atlas.add("dr_edge", 128, 16, pe.panel(RED, s + 11, fringe=7, motif=None))
    atlas.add("dr_awn_edge", 128, 16, pe.panel(_scale(RED, 0.8), s + 12, fringe=0, motif=None, dags=10))
    atlas.add("dr_roll_red", 32, 48, pe.carpet_roll("a42430", "e8a830", s + 13))
    atlas.add("dr_roll_plum", 32, 48, pe.carpet_roll("5a1e5a", "e0a030", s + 14))
    atlas.add("dr_roll_cream", 32, 48, pe.carpet_roll("e8dcc0", "c8b080", s + 15, cream=True))
    atlas.add("e_post", 64, 16, pe.wood("74482a", "3a2412", s + 16))
    atlas.add("e_grapes", 24, 40, pe.bunch("grapes", s + 17))
    atlas.add("e_lavender", 24, 40, pe.bunch("lavender", s + 18))
    atlas.add("e_herbs", 24, 40, pe.bunch("herbs", s + 19))
    atlas.add("e_fl_red", 32, 32, pe.flowers([_rgb("d02a2a"), _rgb("e84a3a")], s + 20))
    atlas.add("e_fl_pink", 32, 32, pe.flowers([_rgb("e070b0"), _rgb("c84a98"), _rgb("f090c8")], s + 21))
    atlas.add("e_oranges", 32, 32, pe.heap(["e88a20", "f0a830", "c83020", "e8c040"], s + 22))
    atlas.add("e_lemons", 32, 32, pe.heap(["f0d040", "e8c030", "f8e070"], s + 23, r=4))
    atlas.add("e_redapples", 32, 32, pe.heap(["c02020", "d83a2a", "a01818"], s + 24, r=4))
    atlas.add("e_sack_cream", 32, 32, pe.burlap("e0d0b0", s + 25))
    atlas.add("e_cheese", 32, 16, pe.cheese(s + 26))
    atlas.add("e_cheese_top", 16, 16, pe.cheese(s + 27))
    atlas.add("e_band", 32, 8, pe.iron_band(s + 28))
    atlas.add("e_gold_band", 16, 8, pe.panel(GOLD, s + 29, fringe=0, motif=None, gold=_rgb("a87018")))
    atlas.add("e_carpet_end", 16, 16, paint_spiral)
    atlas.add("e_soil", 16, 16, pe.heap(["3a2a1a", "4a3420"], s + 30, bg="2a1c10", r=2))
    for k, c in enumerate((RED, _rgb("6a2a7a"), CREAM, GOLD)):
        atlas.add("dr_pen_%d" % k, 16, 24, pe.panel(c, s + 40 + k, fringe=0, motif=None, point=0.45, gold=_scale(c, 0.7) if k == 3 else GOLD))
    print("atlas", atlas.size)


def paint_spiral(img):
    """A rolled carpet's end: a spiral of the carpet's layers."""
    w, h = img.size
    px = img.load()
    rng = random.Random(3131)
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5)
            a = math.atan2(y - h / 2, x - w / 2)
            ring = (d + a / (2 * math.pi) * 2.2) % 2.2
            c = _rgb("a42430") if ring < 1.4 else _rgb("e8c070")
            px[x, y] = ml._jitter(_scale(c, 1.0 - 0.02 * d), rng, 8) + (255,)


# ---------------------------------------------------------------- the build
def build(atlas, decor):
    rng = random.Random(122)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]    # FL, FR, BR, BL
    tops = [FRONT_TOP, FRONT_TOP, BACK_TOP, BACK_TOP]
    for k, (x, z) in enumerate(corners):
        pe.post(shell, det, "post_%d" % k, x, z, tops[k], d=PD, bands=(0.3, 1.55, 2.75, 3.85) if k < 2 else (0.3, 1.55, 2.75),
                caps=2 if k < 2 else 1, cap_w=0.84, solid_to=EAVE)
    by = EAVE - 0.17
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.34, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.3, extend=0.2)
    # the capped blocks in the middle of the front eave (where the swags meet) and their iron hooks
    box(shell, "mid_block", (-0.24, EAVE - 0.4, HD - 0.2), (0.24, EAVE + 0.32, HD + 0.2), {"all": "wood", "+2": "end_grain"})
    box(shell, "mid_block_top", (-0.18, EAVE + 0.32, HD - 0.15), (0.18, EAVE + 0.5, HD + 0.15), {"all": "wood_dark", "+2": "end_grain"})
    pe.band(det, "mid_block_band", 0.0, HD, 0.25, EAVE - 0.1, 0.12)
    # tie beam and rail for the hanging bunches, inner braces
    beam(shell, "tie_beam", (-HW, by - 0.05, 0.0), (HW, by - 0.05, 0.0), 0.22, "wood_dark", extend=0.1)
    beam(det, "herb_rail", (-HW, 2.68, 2.0), (0.4, 2.68, 2.0), 0.08, "wood_dark")
    for k, sx in enumerate((-1, 1)):
        beam(shell, "brace_f_%d" % k, (sx * (HW - 0.2), EAVE - 1.1, HD), (sx * (HW - 0.95), by - 0.12, HD), 0.15, "wood_dark", extend=0.04)
    # ---- the roof: four sagging faces, red stripes with gold crosses / cream, up to the cupola
    eave = [(-RW, EAVE, RD), (RW, EAVE, RD), (RW, EAVE, -RD), (-RW, EAVE, -RD)]
    topq = [(-CUP + 0.02, CUP_Y0, CUP - 0.02), (CUP - 0.02, CUP_Y0, CUP - 0.02), (CUP - 0.02, CUP_Y0, -CUP + 0.02), (-CUP + 0.02, CUP_Y0, -CUP + 0.02)]
    faces = pe.pyramid_roof(shell, "roof", eave, topq, "dr_roof", sag=0.42, nx=5, ny=4, hang=(0.32, "dr_edge"))
    # hip battens (the cloth is tied along the hips)
    for k in range(4):
        pe.ml.rope(det, "hip_%d" % k, v3(*topq[k]) + UP * 0.03, v3(*eave[k]) + UP * 0.03, d=0.06, segs=2)
    # ---- the cupola: wooden corner blocks, red gold-fringed panels, little pyramid, gold onion finial
    for k, (sx, sz) in enumerate(((-1, 1), (1, 1), (1, -1), (-1, -1))):
        x, z = sx * CUP, sz * CUP
        box(shell, "cup_post_%d" % k, (x - 0.12, CUP_Y0 - 0.12, z - 0.12), (x + 0.12, CUP_Y1, z + 0.12), {"all": "wood", "+2": "end_grain"})
        box(shell, "cup_block_%d" % k, (x - 0.17, CUP_Y1 - 0.3, z - 0.17), (x + 0.17, CUP_Y1 + 0.02, z + 0.17), {"all": "wood_dark", "+2": "end_grain"})
        box(shell, "cup_foot_%d" % k, (x - 0.17, CUP_Y0 - 0.12, z - 0.17), (x + 0.17, CUP_Y0 + 0.16, z + 0.17), {"all": "wood_dark", "+2": "end_grain"})
    for k, (n, c) in enumerate((((0, 0, 1), (0, CUP_Y1 - 0.06, CUP + 0.06)), ((1, 0, 0), (CUP + 0.06, CUP_Y1 - 0.06, 0)),
                                ((0, 0, -1), (0, CUP_Y1 - 0.06, -CUP - 0.06)), ((-1, 0, 0), (-CUP - 0.06, CUP_Y1 - 0.06, 0)))):
        pe.hang_panel(shell, "cup_panel_%d" % k, c, 2 * CUP - 0.2, 0.62, n, "dr_cup", wave=0.03, ny=2)
    pe.pyramid_roof(shell, "cup_roof", [(-CUP - 0.12, CUP_Y1, CUP + 0.12), (CUP + 0.12, CUP_Y1, CUP + 0.12), (CUP + 0.12, CUP_Y1, -CUP - 0.12),
                                        (-CUP - 0.12, CUP_Y1, -CUP - 0.12)], [(0, CUP_Y1 + 0.4, 0)] * 4, "dr_awning", sag=0.04, nx=2, ny=2)
    fy = CUP_Y1 + 0.34
    ml.octo(shell, "finial_base", (0, fy, 0), 0.12, 0.14, "gold")
    add_cube(shell, "finial_ball", (0, fy + 0.26, 0), ry(math.pi / 4), (0.26, 0.24, 0.26), "gold")
    add_cube(shell, "finial_ball2", (0, fy + 0.26, 0), EYE, (0.22, 0.28, 0.22), "gold")
    ml.octo(shell, "finial_neck", (0, fy + 0.38, 0), 0.06, 0.1, "gold")
    add_cube(shell, "finial_tip", (0, fy + 0.56, 0), EYE, (0.07, 0.24, 0.07), "gold")
    # ---- ropes from the cupola to the front post caps, a guy rope from the front-left post to the ground
    for k, (sx, sz) in enumerate(((-1, 1), (1, 1))):
        a = (sx * CUP, CUP_Y1 - 0.15, sz * CUP)
        b = (sx * HW, FRONT_TOP + 0.15, HD)
        pe.ml.rope(det, "cup_rope_%d" % k, a, b, d=0.09, sag=0.08, segs=3)
    ml.rope(det, "guy_rope", (-HW - 0.2, FRONT_TOP + 0.05, HD + 0.05), (-5.3, 0.02, 3.5), d=0.09, sag=0.12, segs=3)
    ml.tl.peg(det, "guy_peg", (-5.3, 0.0, 3.5), (-HW, FRONT_TOP, HD), length=0.5, d=0.12, region="wood")
    pe.rope_wrap(det, "guy_wrap", -HW, HD, FRONT_TOP - 0.38, PD / 2, turns=2)
    # ---- the hanging panels: two staggered rows draped over the front roof edge, more on the sides and the back
    zf = RD + 0.02
    back_row = [(-2.5, 1.0, "dr_pan_red", 1.05, 0.42), (-1.5, 1.0, "dr_pan_red", 1.15, 0.45), (0.6, 0.95, "dr_pan_cream", 1.3, 0.45),
                (1.6, 1.0, "dr_pan_red", 1.05, 0.4), (2.5, 0.95, "dr_pan_cream", 1.0, 0.38)]
    front_row = [(-2.0, 1.0, "dr_pan_long", 1.5, 0.25), (-0.55, 0.95, "dr_pan_cream", 1.05, 0.28), (1.1, 1.02, "dr_pan_long", 1.72, 0.22),
                 (2.1, 0.95, "dr_pan_red", 1.25, 0.24)]
    for row, (lst, lift, dz) in enumerate(((back_row, 0.05, 0.0), (front_row, 0.1, 0.07))):
        for k, (x, w, reg, h, up) in enumerate(lst):
            t = 1.0 - up / 2.0
            p = pe.roof_point(faces[0], x, t, axis=0) + UP * lift
            pe.drape_over(shell, "pan_%d_%d" % (row, k), p, (x, EAVE + 0.04 + lift * 0.5, zf + dz), w, h, (0, 0, 1), reg, wave=0.05 + 0.02 * row)
    for k, sx in enumerate((-1, 1)):
        for j, (z, reg, h) in enumerate(((1.25, "dr_pan_red", 1.15), (0.0, "dr_pan_cream", 1.0), (-1.25, "dr_pan_red", 1.2))):
            face = faces[3] if sx < 0 else faces[1]
            p = pe.roof_point(face, z, 0.8, axis=2) + UP * 0.05
            pe.drape_over(shell, "pan_s_%d_%d" % (k, j), p, (sx * (RW + 0.03), EAVE + 0.06, z), 1.05, h, (sx, 0, 0), reg, wave=0.05)
    for j, x in enumerate((-1.6, 0.0, 1.6)):
        p = pe.roof_point(faces[2], x, 0.8, axis=0) + UP * 0.05
        pe.drape_over(shell, "pan_back_%d" % j, p, (x, EAVE + 0.06, -RD - 0.03), 1.3, 0.95, (0, 0, -1), "dr_pan_red" if j != 1 else "dr_pan_cream",
                      wave=0.05)
    # ---- walls: striped back wall, the red patterned drape on the left side, the right side's back half
    pe.wall(shell, "wall_back", (-HW, 0, -HD - 0.1), (HW, 0, -HD - 0.1), 0.0, by - 0.15, -Z, "dr_wall", nx=6)
    collide((-HW, 0.0, -HD - 0.16, HW, by - 0.15, -HD - 0.04))
    pe.wall(shell, "wall_left", (-HW - 0.05, 0, -HD), (-HW - 0.05, 0, 0.9), 0.0, by - 0.15, -X, "dr_drape_l", nx=5, fold=0.07)
    collide((-HW - 0.12, 0.0, -HD, -HW + 0.02, by - 0.15, 0.9))
    pe.wall(shell, "wall_right", (HW + 0.05, 0, 0.0), (HW + 0.05, 0, -HD), 0.0, by - 0.15, X, "dr_curtain", nx=4, fold=0.07)
    collide((HW - 0.02, 0.0, -HD, HW + 0.12, by - 0.15, 0.0))
    # the deep red-purple curtain tied back on the front-right post (inside), a second one at the left front
    pe.drape(shell, det, "curtain_r", (HW - 0.25, by - 0.2, HD - 0.2), (HW - 1.05, by - 0.2, HD - 0.2), (HW - 0.35, 1.4, HD - 0.22),
             (HW - 0.3, 0.04, HD - 0.24), (HW - 0.8, 0.04, HD - 0.24), Z, "dr_curtain", nx=3)
    pe.drape(shell, det, "curtain_l", (-HW - 0.12, by - 0.2, 1.0), (-HW - 0.12, by - 0.2, HD - 0.3), (-HW - 0.14, 1.5, 1.9),
             (-HW - 0.12, 0.04, 1.75), (-HW - 0.12, 0.04, 2.0), -X, "dr_drape_l", nx=2)
    # ---- lanterns
    pe.lamp(shell, det, "lamp_l", (-2.1, 2.3, 2.0), size=0.36, chain_to=(-2.1, 2.66, 2.0))
    
    pe.lamp(shell, det, "lamp_c", (0.05, 2.62, 1.55), size=0.44, chain_to=(0.05, by - 0.12, 1.55))
    pe.lamp(shell, det, "lamp_in", (0.95, 2.4, 0.15), size=0.34, chain_to=(0.95, by - 0.1, 0.0))
    mount, tip = v3(HW + 0.29, 3.0, HD), v3(HW + 0.62, 3.0, HD)
    beam(det, "lamp_r_arm", mount, tip, 0.05, "iron", extend=0.02)
    beam(det, "lamp_r_brace", mount - UP * 0.35, tip - UP * 0.02, 0.04, "iron")
    pe.lamp(shell, det, "lamp_r", tip - UP * 0.48, size=0.38, chain_to=tip)
    # ---- the hanging bunches (grapes, lavender, herbs) from the rail under the front eave
    for k, (x, kind, ln) in enumerate(((-1.45, "e_herbs", 0.62), (-1.18, "e_grapes", 0.5), (-0.92, "e_lavender", 0.6), (-0.66, "e_herbs", 0.55),
                                       (-0.42, "e_grapes", 0.48), (-0.18, "e_lavender", 0.56))):
        ml.hanging_bunch(det, "bunch_%d" % k, (x, 2.64, 2.0), kind=kind, length=ln, width=0.26, string=0.04 + 0.04 * (k % 2))
    # ---- the right awning: posts, beams, the sagging red cloth with a gold border, fringed outer edge; bunting
    for k, z in enumerate(EXT_Z):
        top = pe.post(shell, det, "epost_%d" % k, EXT_X, z, 2.5, d=0.38, bands=(0.3, 1.4), caps=1, cap_w=0.5)
    ml.beam(shell, "epole", (EXT_X, 2.84, EXT_Z[0]), (EXT_X, 3.75, EXT_Z[0]), 0.1, "wood_dark")
    box(det, "epole_knob", (EXT_X - 0.07, 3.75, EXT_Z[0] - 0.07), (EXT_X + 0.07, 3.85, EXT_Z[0] + 0.07), "gold")
    for k, z in enumerate(EXT_Z):
        beam(shell, "ebeam_%d" % k, (HW, 2.95, z), (EXT_X, 2.38, z), 0.2, "beam", extend=0.12)
    beam(shell, "ebeam_side", (EXT_X, 2.4, EXT_Z[1]), (EXT_X, 2.4, EXT_Z[0]), 0.2, "beam", extend=0.12)
    z0, z1 = EXT_Z[1] - 0.35, EXT_Z[0] + 0.4

    def AW(s, t):   # s along z (front -> back, seen from the right), t from the main tent out to the outer posts
        z = z1 + (z0 - z1) * s
        x = HW + 0.32 + (EXT_X + 0.28 - HW - 0.32) * t
        y = 3.32 - 0.78 * t - 0.3 * math.sin(math.pi * t) * (0.75 + 0.25 * math.sin(math.pi * s)) - 0.05 * math.sin(s * math.pi * 3)
        return v3(x, y, z)
    loft(shell, "awning", AW, 4, 4, "dr_awning", th=0.035, overlap=0.03)

    def AWE(s, t):  # the outer edge falls a little, dagged
        p = AW(s, 1.0)
        return p - UP * (0.32 * t) + X * (0.04 * t)
    loft(shell, "awning_edge", AWE, 4, 1, "dr_awn_edge", th=0.025)

    def AWF(s, t):  # the front hem: a curved swag between the main post and the outer post
        p = AW(0.0, s)
        return p - UP * ((0.12 + 0.3 * math.sin(math.pi * s)) * t) + Z * (0.03 * t)
    loft(shell, "awning_front", AWF, 4, 1, "dr_awn_edge", th=0.025)
    pe.lamp(shell, det, "lamp_aw", (3.55, 2.2, EXT_Z[0]), size=0.34, chain_to=(3.55, 2.72, EXT_Z[0]))
    pe.bunting(det, "bunting", (HW + 0.3, FRONT_TOP + 0.1, HD), (EXT_X, 3.7, EXT_Z[0]), 0.28,
               ["dr_pen_0", "dr_pen_1", "dr_pen_2", "dr_pen_3"], n=6, size=(0.26, 0.4))
    # ---- the counter (cheese, a tub, potions) with the blue runner
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    box(shell, "runner", (-0.75, y, cz0 + 0.05), (0.5, y + 0.016, cz1 + 0.05), {"all": "cloth_blue"}, stretch=True, u_dir=X)
    ml.plate(shell, "runner_front", (-0.125, y - 0.36, cz1 + 0.065), 1.25, 0.74, "dr_runner", normal=(0, 0, 1), th=0.012, edge="cloth_blue")
    for k, (x, z) in enumerate(((-1.95, zc + 0.12), (-1.65, zc + 0.15), (-1.8, zc - 0.12))):
        pe.cheese_block(det, "cheese_%d" % k, (x, y, z), s=(0.28, 0.2, 0.24), yaw=0.2 * k)
    pe.cheese_block(det, "cheese_top", (-1.8, y + 0.2, zc + 0.02), s=(0.24, 0.18, 0.2), yaw=0.5)
    ml.barrel(shell, "tub", (-1.2, y, zc - 0.05), r=0.26, h=0.32, solid=False)
    for k, (dx, dz) in enumerate(((-0.08, -0.05), (0.08, 0.06))):
        pe.cheese_wheel(det, "tub_cheese_%d" % k, (-1.2 + dx, y + 0.32, zc + dz), r=0.12, h=0.1)
    pe.cheese_block(det, "cheese_r", (-0.9, y, zc + 0.15), s=(0.22, 0.16, 0.2), yaw=-0.3)
    for k, (x, c) in enumerate(((0.62, "orange"), (0.82, "purple"), (1.0, "orange"), (1.18, "purple"), (1.32, "red"))):
        ml.bottle(det, "cpot_%d" % k, (x, y, zc + 0.05 * (k % 2)), c, r=0.08, h=0.22 + 0.04 * (k % 2), shape="round" if k % 2 else "flask", neck_h=0.08)
    ml.bottle(det, "cpot_big", (0.25, y, zc - 0.12), "orange", r=0.1, h=0.2, shape="round")
    # ---- the back shelves: potions, jars, small casks
    levels = ml.shelf_unit(shell, "shelves", -HW + 0.4, HW - 0.4, SHELF_Z[0], SHELF_Z[1], levels=(0.62, 1.22, 1.82, 2.42), h=2.75,
                           back=True, uprights=4, detail=det)
    pots = ("orange", "purple", "red", "orange", "green", "purple", "red", "orange", "yellow")
    for j, (x0, x1, yy, zf_, zb) in enumerate(sorted(levels, key=lambda s: s[2])):
        zz = (zf_ + zb) / 2
        if j == 3:
            for i, xx in enumerate((x0 + 0.4, x0 + 1.2, x1 - 1.0, x1 - 0.3)):
                ml.barrel(det, "small_cask_%d" % i, (xx, yy, zz), r=0.14, h=0.26, staves=6, solid=False)
            continue
        n = 10
        for i in range(n):
            xx = x0 + 0.12 + (x1 - x0 - 0.24) * i / (n - 1)
            ml.bottle(det, "pot_%d_%d" % (j, i), (xx, yy, zz + 0.05 * ((i % 2) - 0.5)), pots[(i + 2 * j) % len(pots)], r=0.07 + 0.012 * (i % 3 == 0),
                      h=0.19 + 0.05 * (i % 2), shape=("round", "tall", "flask")[(i + j) % 3], neck_h=0.06)
    # ---- the RUG in front of the counter
    ml.rug(shell, "rug", -0.3, 2.62, 2.4, 4.5, y=0.0, region="dr_rug")
    # ---- front crates with the basket of red flowers and the basket of oranges and apples
    ml.crate(shell, "fcrate_0", (-1.55, 0.0, 2.95), size=(0.74, 0.62, 0.62), yaw=0.04, solid=True)
    ml.crate(shell, "fcrate_1", (-0.75, 0.0, 3.0), size=(0.72, 0.58, 0.6), yaw=-0.05, solid=True)
    ml.basket(det, "fl_basket", (-1.55, 0.62, 2.95), r=0.24, h=0.22, content="basket_top", handle=False)
    pe.plant(det, "fl_red", (-1.55, 0.62, 2.95), 0.6, 0.48, "e_fl_red", pot=None, pot_h=0.2)
    ml.basket(det, "fruit_basket", (-0.75, 0.58, 3.0), r=0.3, h=0.2, content="e_oranges", handle=True)
    # ---- outside left: rolled carpets against the front-left post, barrels, cream sacks, a crate with herbs
    for k, (x, z, r, h, reg, lean) in enumerate(((-3.38, 2.85, 0.19, 1.62, "dr_roll_cream", (0.12, -0.08)), (-3.72, 2.62, 0.2, 1.95, "dr_roll_red", (0.16, -0.05)),
                                                 (-3.92, 3.1, 0.18, 1.7, "dr_roll_plum", (0.3, -0.12)), (-2.82, 3.05, 0.17, 1.5, "dr_roll_red", (-0.05, -0.2)))):
        pe.rolled_carpet(shell, "roll_%d" % k, (x, 0.0, z), r, h, reg, lean=lean)
    collide((-4.1, 0.0, 2.42, -2.65, 1.6, 3.28))
    ml.barrel(shell, "lbarrel_0", (-4.1, 0.0, 3.9), r=0.36, h=0.9)
    ml.barrel(shell, "lbarrel_1", (-4.75, 0.0, 3.2), r=0.34, h=0.86)
    pe.round_sack(shell, det, "lsack_0", (-2.95, 0.0, 3.9), region="e_sack_cream", yaw=0.3, w=0.6, h=0.78)
    pe.round_sack(shell, det, "lsack_1", (-4.9, 0.0, 2.3), region="e_sack_cream", yaw=-0.4, w=0.56, h=0.74)
    decor.block("furnish:spruce_crate", -4.55, 0.0, 1.1, facing="front", alt="minecraft:barrel", fallback="crate")
    pe.plant(det, "lpot", (-4.55, 1.0, 1.1), 0.5, 0.42, "e_herbs", pot="e_post", pot_r=0.2, pot_h=0.22)
    decor.block("farmersdelight:rice_bag", -4.45, 0.0, 0.0, facing="front", fallback="sack")
    ml.crate(shell, "lcrate", (-3.95, 0.0, 1.6), size=(0.7, 0.62, 0.62), yaw=0.15, solid=True)
    ml.basket(det, "lcheese_tub", (-3.95, 0.62, 1.6), r=0.26, h=0.2, content="e_cheese_top", handle=False)
    # ---- the right awning's fruit stand: table, flower pots, apples, lemons on crates
    bh = pe.bench_table(shell, det, "stand", 3.25, 4.6, -0.8, 1.2, h=0.95)
    pe.plant(det, "rpot_0", (3.6, bh, 0.8), 0.5, 0.42, "e_fl_pink", pot="basket", pot_r=0.18, pot_h=0.2)
    pe.plant(det, "rpot_1", (4.2, bh, -0.4), 0.45, 0.4, "e_fl_red", pot="basket", pot_r=0.16, pot_h=0.18)
    ml.basket(det, "apples", (4.15, bh, 0.5), r=0.3, h=0.18, content="e_redapples", handle=False)
    ml.crate(det, "rbox", (3.6, bh, -0.3), size=(0.42, 0.3, 0.4), yaw=0.2, solid=False)
    decor.block("furnish:oak_crate", 3.55, 0.0, 2.0, facing="front", scale=0.8, alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "rcrate", (4.4, 0.0, 1.95), size=(0.78, 0.72, 0.7), yaw=-0.06, solid=True)
    ml.basket(det, "lemons", (4.35, 0.72, 1.95), r=0.3, h=0.18, content="e_lemons", handle=False)
    decor.block("landsoficaria:cypress_barrel", 3.85, 0.0, -1.75, facing="pos_x", alt="minecraft:barrel", fallback="barrel")
    pe.check_free(NAME, (NPC_SPOT[0], 0.0, NPC_SPOT[1], NPC_SPOT[0] + 1.0, 2.2, NPC_SPOT[1] + 1.0))
    return root


def item_icon(path):
    """16x16: the square red-and-cream tent with its cupola and gold finial, the red fringed panels, two posts."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, cream, gold, wood, dark = RED, CREAM, GOLD, (120, 80, 44), (50, 32, 18)
    p[7, 0] = p[8, 0] = gold + (255,)
    for x in range(6, 10):
        p[x, 1] = gold + (255,) if x in (7, 8) else (0, 0, 0, 0)
    for y in (2, 3):
        for x in range(6, 10):
            p[x, y] = (red if y == 2 else _scale(red, 0.8)) + (255,)
    for y in range(4, 8):
        half = 2 + (y - 4) * 1.7
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                k = int((dx / half + 1) * 2.5)
                p[x, y] = (red if k % 2 == 0 else cream) + (255,)
    for x in range(1, 15):
        p[x, 8] = (red if (x // 3) % 2 == 0 else cream) + (255,)
        p[x, 9] = (red if (x // 3) % 2 == 0 else cream) + (255,)
        if x % 2:
            p[x, 10] = gold + (255,)
    for y in range(1, 16):
        for x in (1, 14):
            if y > 2:
                p[x, y] = wood + (255,)
    for y in range(11, 15):
        for x in range(2, 14):
            p[x, y] = dark + (255,)
    for x in range(5, 11):
        p[x, 13] = (60, 76, 140, 255)
        p[x, 14] = (150, 104, 56, 255)
    for x in range(1, 15):
        p[x, 15] = (140, 30, 44, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
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
