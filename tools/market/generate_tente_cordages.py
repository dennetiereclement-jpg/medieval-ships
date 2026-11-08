#!/usr/bin/env python3
"""tente_cordages — Tente rouge aux cordages / Red Rope Tent (1.26.0, market group E; reference:
scratchpad/ref2/tente_cordages_ref.png, picture 143).

A red merchant tent hung from a rope-lashed wooden scaffold, one block (TentType group "tents"), about 10.5 blocks wide
with its two awnings, the gold spire at about 7:

  - the main pointed pavilion roof, sagging between its hips, red sprinkled with small gold stars and fleurs-de-lis
    with one cream stripe per face, a gold spire; under its eaves a VALANCE of swagged panels, red and cream in turn,
    edged with a stepped gold border and dags, hooked up on rope rings;
  - the SCAFFOLD: tall squared posts lashed with thick rope at every joint, rope-wrapped crossbeams, a tall HOIST
    GANTRY behind the left half (two posts, two crossbeams, iron brackets) with PULLEYS and their ropes, a pulley and
    rope on the far-left post, many diagonal ROPES (from the gantry to the front-left post, guy ropes to pegs, the
    crossed ropes bracing the right awning);
  - the LEFT AWNING: a cream canopy with a dagged edge over a big RED CURTAIN with gold fleurs-de-lis falling to the
    ground and gathered on the far-left post, the far-left posts wrapped with rope;
  - the RIGHT AWNING: red with gold-edged dags, sloping down to its own posts;
  - the RED FLEUR-DE-LIS BANNER hanging from the front beam beside the front-left post;
  - inside: back shelves of pink and red potions, hanging bunches of herbs and flowers, the big lantern on its chain
    at the front, a lantern inside, a table of FOLDED CLOTH STACKS (blue, red, purple, teal) with a standing lantern,
    the counter under a red-and-gold cloth and a cream lace cloth (candles, a scroll, pots of violet flowers, a box);
  - in front: crates, an iron-bound CHEST, a burlap sack, a box of white flowers on a crate, a barrel heaped with red
    apples, a basket of green apples, the dark RED RUG with a cream border.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in between the
cloth table and the counter. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_cordages.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_cordages.json, models/entity + blockbench/tente_cordages.bbmodel,
textures/entity/tente_cordages.png, textures/item/tente_cordages.png, interiors/tente_cordages_decor.json.
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
NAME = "tente_cordages"
v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _scale = ml._rgb, ml._scale

RED, CREAM = _rgb("962220"), _rgb("e6cfa2")
GOLD = _rgb("e8a830")

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
X0, X1 = -2.2, 2.8          # the main tent's posts (x)
Z0, Z1 = -2.1, 2.0          # back / front post lines (z)
CX, CZ = (X0 + X1) / 2, (Z0 + Z1) / 2
PD = 0.46
EAVE = 3.35
APEX = 5.95
LX = -4.65                  # the left awning's outer posts
RX = 4.45                   # the right awning's outer posts
GX = (-1.95, -0.1)         # the gantry's posts (x), at z = GZ
GZ = -2.55
GTOP = 6.45
COUNTER = (0.35, 2.35, 0.45, 1.05)
COUNTER_H = 1.0
NPC_SPOT = (0.9, -1.05)
SHELF_Z = (-1.95, -1.5)


def paint_roof(img):
    """The roof faces: red sprinkled with small gold stars and fleurs-de-lis, one cream stripe (60-76 % across)."""
    w, h = img.size
    pe.stripes([RED], 1, 4301, motif="fleur", motif_step=(22, 24), fold=0.0, seams=False)(img)
    rng = random.Random(4302)
    px = img.load()
    for y in range(9, h - 4, 16):
        for x in range((y * 7) % 11 + 8, w - 3, 22):
            if px[x, y][0] > 120 and px[x, y][1] < 90:
                pe.glyph(px, w, h, x, y, "star" if (x + y) % 3 else "dot", GOLD, rng)
    a, b = int(w * 0.6), int(w * 0.76)
    sub = img.crop((a, 0, b, h))
    ml._weave(sub, (0, 0, b - a, h), CREAM, rng, stains=1)
    img.paste(sub, (a, 0))
    for y in range(h):
        for x in range(w):
            r, g, bb, al = px[x, y]
            k = 0.86 + 0.16 * (y / h) - (0.2 if x in (a, a + 1, b - 1, b) else 0.0)
            k *= 0.94 + 0.06 * math.sin(x * 0.4)
            px[x, y] = _scale((r, g, bb), k) + (255,)


def paint_curtain(img):
    """The left awning's big red curtain: folds, gold fleurs-de-lis scattered, a gold hem."""
    w, h = img.size
    pe.stripes([RED, _scale(RED, 0.86)], 6, 4303, motif=None, fold=0.4, seams=False, hem=(GOLD, 4))(img)
    rng = random.Random(4304)
    px = img.load()
    for row, y in enumerate(range(8, h - 10, 14)):
        for x in range(6 + (row % 2) * 8, w - 4, 16):
            pe.glyph(px, w, h, x, y, "fleur", GOLD, rng)


def add_regions(atlas):
    s = 4300
    atlas.add("co_roof", 128, 96, paint_roof)
    atlas.add("co_curtain", 96, 96, paint_curtain)
    atlas.add("co_rug", 128, 96, pe.rug("7a1c1e", "3a0e10", "e0c08a", "a83a2a", s + 1, medallion=True))
    atlas.add("co_banner", 40, 80, pe.panel(RED, s + 2, fringe=0, motif="fleur", point=0.22, key=True))
    atlas.add("co_val_red", 64, 32, pe.panel(RED, s + 3, fringe=0, motif=None, key=True, dags=3))
    atlas.add("co_val_cream", 64, 32, pe.panel(CREAM, s + 4, fringe=0, motif=None, key=True, dags=3, dark=_rgb("a88a60")))
    atlas.add("co_canopy", 96, 48, pe.stripes([CREAM, _scale(CREAM, 0.9)], 4, s + 5, fold=0.3, seams=False))
    atlas.add("co_can_edge", 96, 16, pe.panel(CREAM, s + 6, fringe=0, motif=None, dags=8, dark=_rgb("a88a60")))
    atlas.add("co_awning", 96, 48, pe.stripes([RED, _scale(RED, 0.92)], 4, s + 7, motif="star", motif_step=(12, 12), fold=0.3, seams=False))
    atlas.add("co_awn_edge", 96, 16, pe.panel(RED, s + 8, fringe=0, motif=None, dags=8))
    atlas.add("co_wall", 128, 64, pe.stripes([_scale(RED, 0.85), _scale(RED, 0.75)], 6, s + 9, fold=0.4, seams=False))
    atlas.add("co_lace", 32, 32, pe.panel(_rgb("e8e0d0"), s + 10, fringe=4, motif=None, gold=_rgb("c8c0b0"), dark=_rgb("b0a890"), fold=0.15))
    atlas.add("co_cloth", 64, 32, pe.panel(RED, s + 11, fringe=0, motif="diamond", key=True))
    atlas.add("e_post", 64, 16, pe.wood("7a4824", "3e2210", s + 12))
    atlas.add("e_herbs", 24, 40, pe.bunch("herbs", s + 13))
    atlas.add("e_herbs_fl", 24, 40, pe.bunch("herbs_flower", s + 14))
    atlas.add("e_lavender", 24, 40, pe.bunch("lavender", s + 15))
    atlas.add("e_fl_white", 32, 32, pe.flowers([_rgb("f4f0e4"), _rgb("f8e8c8"), _rgb("e8d8f0")], s + 16))
    atlas.add("e_fl_violet", 32, 32, pe.flowers([_rgb("a058c8"), _rgb("c070d8"), _rgb("e070b0")], s + 17))
    atlas.add("e_redapples", 32, 32, pe.heap(["c01e1e", "d83a2a", "a01818"], s + 18, r=4))
    atlas.add("e_greenapples", 32, 32, pe.heap(["6aa83a", "88c048", "c02a20"], s + 19, r=4))
    atlas.add("e_sack", 32, 32, pe.burlap("a88a60", s + 20))
    atlas.add("e_band", 32, 8, pe.iron_band(s + 21))
    atlas.add("e_soil", 16, 16, pe.heap(["3a2a1a", "4a3420"], s + 22, bg="2a1c10", r=2))
    atlas.add("e_gold_band", 16, 8, pe.panel(GOLD, s + 23, fringe=0, motif=None, gold=_rgb("a87018")))
    print("atlas", atlas.size)


# ---------------------------------------------------------------- the build
def lashed_post(shell, det, name, x, z, top, d=PD, caps=1, wraps=(), solid_to=None, bands=(0.3,)):
    t = pe.post(shell, det, name, x, z, top, d=d, bands=bands, caps=caps, cap_w=d + 0.2, solid_to=solid_to, cap_region="wood")
    for k, (y, n) in enumerate(wraps):
        pe.rope_wrap(det, "%s_wrap_%d" % (name, k), x, z, y, d / 2, turns=n, th=0.1)
    return t


def rope_beam(shell, det, name, a, b, d=0.26, wraps=(0.15, 0.85)):
    """A crossbeam lashed with rope near both ends (and wherever `wraps` says, as fractions of its length)."""
    a, b = v3(*a), v3(*b)
    beam(shell, name, a, b, d, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=d, extend=0.12)
    axis = norm(b - a)
    for k, f in enumerate(wraps):
        c = a + (b - a) * f
        R = ml.gg.frame_from(axis, UP)
        add_cube(det, "%s_wrap_%d" % (name, k), c, R, (0.22, d + 0.1, d + 0.1), "rope")


def build(atlas, decor):
    rng = random.Random(143)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    # ---- the main tent's posts (the front-left one tall, part of the scaffold) and eave beams
    lashed_post(shell, det, "post_fl", X0, Z1, 4.75, caps=2, wraps=((3.05, 2), (0.9, 2)), solid_to=EAVE, bands=(0.3, 1.9))
    lashed_post(shell, det, "post_fr", X1, Z1, 4.05, caps=1, wraps=((2.2, 3), (3.15, 1)), solid_to=EAVE, bands=(0.3, 1.4))
    lashed_post(shell, det, "post_br", X1, Z0, EAVE + 0.2, caps=1, wraps=(), solid_to=EAVE)
    lashed_post(shell, det, "post_bl", X0, Z0, EAVE + 0.2, caps=1, wraps=(), solid_to=EAVE)
    by = EAVE - 0.15
    corners = [(X0, Z1), (X1, Z1), (X1, Z0), (X0, Z0)]
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        rope_beam(shell, det, "eave_%d" % k, (xa, by, za), (xb, by, zb), d=0.28)
    beam(shell, "tie_beam", (X0, by - 0.04, CZ), (X1, by - 0.04, CZ), 0.2, "wood_dark", extend=0.08)
    beam(det, "herb_rail", (X0, 2.75, 1.5), (X1, 2.75, 1.5), 0.08, "wood_dark")
    # ---- the main roof: four sagging faces up to the spire
    RW0, RW1, RD0, RD1 = X0 - 0.25, X1 + 0.25, Z0 - 0.25, Z1 + 0.25
    eave = [(RW0, EAVE, RD1), (RW1, EAVE, RD1), (RW1, EAVE, RD0), (RW0, EAVE, RD0)]
    faces = pe.pyramid_roof(shell, "roof", eave, [(CX, APEX, CZ)] * 4, "co_roof", sag=0.58, nx=4, ny=8)
    for k in range(4):
        ml.rope(det, "hip_%d" % k, v3(CX, APEX, CZ), v3(*eave[k]) + UP * 0.04, d=0.07, segs=3)
    ml.octo(shell, "spire_base", (CX, APEX - 0.12, CZ), 0.17, 0.24, "gold")
    ml.octo(shell, "spire_mid", (CX, APEX + 0.12, CZ), 0.11, 0.24, "gold")
    add_cube(shell, "spire_cross", (CX, APEX + 0.3, CZ), ry(math.pi / 4), (0.34, 0.08, 0.08), "gold")
    add_cube(shell, "spire_tip", (CX, APEX + 0.62, CZ), EYE, (0.09, 0.5, 0.09), "gold")
    # ---- the valance: swagged red / cream panels with stepped gold borders and dags, hooked on rope rings
    def valance_side(name, a, b, out, n):
        a, b = v3(*a), v3(*b)
        for k in range(n):
            pa, pb = a + (b - a) * (k / n), a + (b - a) * ((k + 1) / n)
            pe.swag(shell, "%s_%d" % (name, k), pa, pb, 0.2, 0.6, out, "co_val_red" if k % 2 == 0 else "co_val_cream", nx=3, belly=0.06)
            if k:
                add_cube(det, "%s_ring_%d" % (name, k), pa + out * 0.06 - UP * 0.04, EYE, (0.14, 0.2, 0.14), "rope")
    valance_side("val_front", (RW0, EAVE + 0.06, RD1 + 0.05), (RW1, EAVE + 0.06, RD1 + 0.05), Z, 5)
    valance_side("val_right", (RW1 + 0.05, EAVE + 0.06, RD1), (RW1 + 0.05, EAVE + 0.06, RD0), X, 4)
    valance_side("val_back", (RW1, EAVE + 0.06, RD0 - 0.05), (RW0, EAVE + 0.06, RD0 - 0.05), -Z, 5)
    valance_side("val_left", (RW0 - 0.05, EAVE + 0.06, RD0), (RW0 - 0.05, EAVE + 0.06, RD1), -X, 4)
    # ---- walls: red back wall, red right side's back half
    pe.wall(shell, "wall_back", (X0, 0, Z0 - 0.08), (X1, 0, Z0 - 0.08), 0.0, by - 0.12, -Z, "co_wall", nx=6)
    collide((X0, 0.0, Z0 - 0.14, X1, by - 0.12, Z0 - 0.02))
    pe.wall(shell, "wall_right", (X1 + 0.06, 0, -0.2), (X1 + 0.06, 0, Z0), 0.0, by - 0.12, X, "co_wall", nx=4)
    collide((X1 - 0.02, 0.0, Z0, X1 + 0.12, by - 0.12, -0.2))
    pe.wall(shell, "wall_left", (X0 - 0.06, 0, Z0), (X0 - 0.06, 0, -0.4), 0.0, by - 0.12, -X, "co_wall", nx=4)
    collide((X0 - 0.12, 0.0, Z0, X0 + 0.02, by - 0.12, -0.4))
    # ---- the hoist gantry behind the left half: two posts, two crossbeams, brackets, pulleys
    for k, gx in enumerate(GX):
        lashed_post(shell, det, "gpost_%d" % k, gx, GZ, GTOP - 0.25, d=0.36, caps=1, wraps=((EAVE + 0.4, 1),), bands=(0.3,))
    rope_beam(shell, det, "gbeam_top", (GX[0] - 0.3, GTOP - 0.12, GZ), (GX[1] + 0.45, GTOP - 0.12, GZ), d=0.24, wraps=(0.12, 0.8))
    rope_beam(shell, det, "gbeam_mid", (GX[0], GTOP - 0.72, GZ), (GX[1], GTOP - 0.72, GZ), d=0.2, wraps=(0.5,))
    for k, gx in enumerate(GX):
        box(det, "gbracket_%d" % k, (gx - 0.22, GTOP - 0.52, GZ - 0.2), (gx + 0.22, GTOP - 0.45, GZ + 0.2), "iron")
    beam(shell, "garm", (GX[1] + 0.05, GTOP - 0.12, GZ), (GX[1] + 0.05, GTOP - 0.12, GZ + 0.9), 0.2, "beam", extend=0.08)
    pe.pulley(det, "pulley_g", (GX[1] + 0.05, GTOP - 0.48, GZ + 0.78), axis=(1, 0, 0), s=0.26)
    ml.rope(det, "pulley_g_rope", (GX[1] + 0.05, GTOP - 0.62, GZ + 0.74), (GX[1] + 0.05, APEX - 1.4, GZ + 0.95), d=0.05)
    pe.pulley(det, "pulley_g2", (GX[0] - 0.15, GTOP - 0.45, GZ + 0.12), axis=(0, 0, 1), s=0.24)
    # the long rope from the gantry down to the front-left post top, another to a peg behind
    ml.rope(det, "rope_gantry_post", (GX[0] - 0.15, GTOP - 0.6, GZ + 0.15), (X0, 4.65, Z1), d=0.1, sag=0.18, segs=4)
    ml.rope(det, "rope_gantry_back", (GX[1] + 0.4, GTOP - 0.12, GZ), (1.6, 0.0, -3.7), d=0.07, sag=0.1, segs=3)
    ml.tl.peg(det, "peg_gantry", (1.6, 0.0, -3.7), (GX[1], GTOP, GZ), length=0.45, d=0.1, region="wood")
    # ---- the left awning: far-left posts, the rope-wrapped beam, cream canopy, the big red curtain
    lashed_post(shell, det, "lpost_f", LX, Z1 - 0.1, 3.2, d=0.36, caps=1, wraps=((0.4, 2), (1.4, 2), (2.6, 2)), bands=())
    lashed_post(shell, det, "lpost_b", LX + 0.25, Z0 + 0.5, 2.85, d=0.34, caps=1, wraps=((2.3, 2),), bands=(0.3,))
    rope_beam(shell, det, "lbeam_front", (X0, 3.05, Z1 - 0.05), (LX, 2.95, Z1 - 0.1), d=0.24, wraps=(0.1, 0.5, 0.92))
    rope_beam(shell, det, "lbeam_back", (X0, 2.75, Z0 + 0.5), (LX + 0.25, 2.65, Z0 + 0.5), d=0.2, wraps=(0.9,))
    beam(shell, "lbeam_side", (LX, 2.85, Z1 - 0.1), (LX + 0.25, 2.6, Z0 + 0.5), 0.18, "beam", extend=0.08)
    cz0, cz1 = Z0 + 0.3, Z1 + 0.25

    def CAN(s, t):   # s along z (front -> back, seen from the left), t from the main tent out to the far-left posts
        z = cz1 + (cz0 - cz1) * s
        x = X0 - 0.2 + (LX - 0.2 - X0 + 0.2) * t
        y = 3.4 - 0.65 * t - 0.2 * math.sin(math.pi * t) - 0.04 * math.sin(s * math.pi * 3)
        return v3(x, y, z)
    loft(shell, "canopy", lambda s, t: CAN(1 - s, t), 4, 3, "co_canopy", th=0.035, overlap=0.03)

    def CANF(s, t):  # the dagged cream front edge
        p = CAN(0.0, s)
        return p - UP * (0.3 * t) + Z * (0.03 * t)
    loft(shell, "canopy_edge", CANF, 4, 1, "co_can_edge", th=0.025)
    # the big red curtain: hangs from the canopy's front edge, swept to the left and gathered on the far-left post
    top_a, top_b = CAN(0.0, 0.08) - UP * 0.25, CAN(0.0, 0.95) - UP * 0.25
    pe.drape(shell, det, "lcurtain", top_b, top_a, (LX + 0.3, 1.25, Z1 + 0.05), (LX + 0.2, 0.04, Z1 + 0.1), (LX + 1.1, 0.04, Z1 + 0.3), Z,
             "co_curtain", nx=4, tie_region="rope", tie_size=(0.36, 0.16, 0.26))
    pe.wall(shell, "lwall_back", (LX + 0.25, 0, Z0 + 0.45), (X0, 0, Z0 + 0.45), 0.0, 2.55, -Z, "co_curtain", nx=4)
    collide((LX + 0.25, 0.0, Z0 + 0.38, X0, 2.4, Z0 + 0.5))
    # the pulley and rope on the far-left post (the rope down to a coil on the ground)
    beam(shell, "larm", (LX, 3.05, Z1 - 0.1), (LX - 0.55, 3.05, Z1 - 0.1), 0.16, "beam")
    pe.pulley(det, "pulley_l", (LX - 0.45, 2.7, Z1 - 0.1), axis=(0, 0, 1), s=0.24)
    ml.rope(det, "pulley_l_rope", (LX - 0.45, 2.55, Z1 - 0.1), (LX - 0.45, 0.3, Z1 - 0.1), d=0.05)
    ml.crate(det, "rope_coil_l", (LX - 0.45, 0.0, Z1 - 0.1), size=(0.36, 0.26, 0.36), region="rope", top="rope", solid=False)
    # ---- the right awning: posts, the red dagged canopy, the crossed bracing ropes, the guy rope
    for k, z in enumerate((Z1 - 0.3, Z0 + 0.7)):
        lashed_post(shell, det, "rpost_%d" % k, RX, z, 2.95 - 0.2 * k, d=0.34, caps=1, wraps=((1.2, 1), (2.3, 2)), bands=(0.3,))
        beam(shell, "rbeam_%d" % k, (X1, 3.05, z), (RX, 2.65 - 0.2 * k, z), 0.2, "beam", extend=0.1)
    rz0, rz1 = Z0 + 0.4, Z1 + 0.05

    def RA(s, t):
        z = rz1 + (rz0 - rz1) * s
        x = X1 + 0.25 + (RX + 0.3 - X1 - 0.25) * t
        y = 3.3 - 0.75 * t - 0.15 * math.sin(math.pi * t) - 0.04 * math.sin(s * math.pi * 3)
        return v3(x, y, z)
    loft(shell, "r_awning", RA, 4, 3, "co_awning", th=0.035, overlap=0.03)
    loft(shell, "r_awning_edge", lambda s, t: RA(s, 1.0) - UP * (0.32 * t) + X * (0.04 * t), 4, 1, "co_awn_edge", th=0.025)
    loft(shell, "r_awning_front", lambda s, t: RA(0.0, s) - UP * ((0.2 + 0.14 * math.sin(math.pi * s)) * t) + Z * 0.03 * t, 3, 1, "co_awn_edge", th=0.025)
    for k, (a, b) in enumerate((((X1 + 0.2, 2.9, Z1), (RX - 0.1, 0.5, Z1 - 0.3)), ((X1 + 0.2, 0.5, Z1), (RX - 0.1, 2.5, Z1 - 0.3)))):
        ml.rope(det, "rbrace_%d" % k, a, b, d=0.07, sag=0.02, segs=2)
    ml.rope(det, "guy_r", (X1 + 0.2, 3.95, Z1), (5.0, 0.0, 3.2), d=0.08, sag=0.12, segs=3)
    ml.tl.peg(det, "peg_r", (5.0, 0.0, 3.2), (X1, 3.95, Z1), length=0.45, d=0.1, region="wood")
    pe.rope_wrap(det, "guy_r_knot", X1, Z1, 3.75, PD / 2, turns=1, th=0.11)
    # ---- the fleur-de-lis banner from the front beam beside the front-left post
    beam(det, "banner_rod", (X0 + 0.32, by - 0.22, Z1 + 0.2), (X0 + 1.22, by - 0.22, Z1 + 0.2), 0.06, "wood_dark")
    pe.hang_panel(shell, "banner", (X0 + 0.77, by - 0.2, Z1 + 0.22), 0.8, 1.55, (0, 0, 1), "co_banner", wave=0.03)
    # ---- lanterns: the big one on its chain at the front, one inside, one on a stand on the cloth table
    pe.lamp(shell, det, "lamp_front", (-0.85, 2.35, Z1 + 0.05), size=0.46, chain_to=(-0.85, by - 0.14, Z1 + 0.05))
    pe.lamp(shell, det, "lamp_in", (1.45, 2.5, -0.35), size=0.34, chain_to=(1.45, by - 0.1, CZ))
    pe.lamp(shell, det, "lamp_r", (2.25, 2.45, 1.5), size=0.3, chain_to=(2.25, 2.78, 1.5))
    # ---- hanging bunches of herbs and flowers
    for k, (x, kind, ln) in enumerate(((-0.2, "e_herbs_fl", 0.55), (0.1, "e_herbs", 0.62), (0.4, "e_herbs", 0.5), (0.7, "e_herbs_fl", 0.58),
                                       (2.0, "e_lavender", 0.5), (2.35, "e_herbs_fl", 0.55))):
        ml.hanging_bunch(det, "bunch_%d" % k, (x, 2.71, 1.5), kind=kind, length=ln, width=0.26, string=0.05 + 0.04 * (k % 2))
    # ---- the back shelves of potions
    levels = ml.shelf_unit(shell, "shelves", X0 + 0.35, X1 - 0.35, SHELF_Z[0], SHELF_Z[1], levels=(0.62, 1.22, 1.82, 2.42), h=2.7, back=True,
                           uprights=4, detail=det)
    cols = ("pink", "red", "pink", "purple", "red", "pink", "orange")
    for j, (x0, x1, yy, zf, zb) in enumerate(sorted(levels, key=lambda s: s[2])):
        zz = (zf + zb) / 2
        if j == 0:
            for i in range(4):
                ml.crate(det, "shelf_box_%d" % i, (x0 + 0.4 + i * (x1 - x0 - 0.8) / 3, yy, zz), size=(0.42, 0.32, 0.36), yaw=0.1 * (i % 2), solid=False)
            continue
        pe.potions_row(det, "pot_%d" % j, x0 + 0.05, x1 - 0.05, yy, zz, [cols[(i + j) % len(cols)] for i in range(len(cols))], n=9, big=(j == 2))
    # ---- the cloth table on the left with folded stacks and a standing lantern
    th_ = pe.bench_table(shell, det, "cloth_table", -1.95, -0.65, 0.55, 1.45, h=0.9)
    for k, (x, z, regs) in enumerate(((-1.62, 0.8, ["cloth_blue", "cloth_red", "cloth_blue", "potion_purple", "cloth_red"]),
                                      (-1.05, 0.8, ["cloth_red", "cloth_dark", "cloth_red", "cloth_blue"]),
                                      (-1.4, 1.2, ["potion_cyan", "cloth_red", "potion_purple"]))):
        pe.folded_stack(det, "stack_%d" % k, (x, th_, z), 0.46, 0.34, regs, h=0.075, yaw=0.05 * k)
    ml.octo(det, "lamp_stand", (-0.85, th_, 1.25), 0.05, 0.42, "wood_dark")
    pe.lamp(shell, det, "lamp_table", (-0.85, th_ + 0.6, 1.25), size=0.26)
    # ---- the counter with the red-and-gold cloth, the lace cloth, candles, a scroll, violet flowers, a box
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    box(shell, "cloth", (0.95, y, cz0 + 0.02), (1.95, y + 0.016, cz1 + 0.06), {"all": "cloth_red"}, stretch=True, u_dir=X)
    ml.plate(shell, "cloth_front", (1.45, y - 0.3, cz1 + 0.07), 1.0, 0.62, "co_cloth", normal=(0, 0, 1), th=0.012, edge="cloth_red")
    box(shell, "lace", (0.45, y + 0.004, cz0 + 0.05), (0.95, y + 0.02, cz1 + 0.06), {"all": "cloth_white"}, stretch=True, u_dir=X)
    ml.plate(shell, "lace_front", (0.7, y - 0.24, cz1 + 0.075), 0.5, 0.5, "co_lace", normal=(0, 0, 1), th=0.012, edge="cloth_white")
    for k, (x, z) in enumerate(((0.6, zc - 0.1), (2.15, zc - 0.05))):
        add_cube(det, "candle_%d" % k, (x, y + 0.12, z), EYE, (0.08, 0.24, 0.08), "wax")
        add_cube(det, "glow_flame_%d" % k, (x, y + 0.28, z), EYE, (0.04, 0.08, 0.04), "flame")
    pe.bolt(det, "scroll", (0.85, y + 0.06, zc + 0.12), length=0.42, r=0.06, yaw=0.3, region="beige", end="white")
    for k, x in enumerate((1.25, 1.65)):
        pe.plant(det, "violet_%d" % k, (x, y, zc - 0.08), 0.36, 0.32, "e_fl_violet", pot="basket", pot_r=0.12, pot_h=0.14)
    ml.crate(det, "counter_box", (1.95, y, zc - 0.1), size=(0.34, 0.24, 0.3), yaw=0.2, solid=False)
    # ---- the rug
    ml.rug(shell, "rug", -0.3, 2.6, 2.15, 4.0, y=0.0, region="co_rug")
    # ---- front left: crates, the iron-bound chest, the sack, the white flowers on a crate
    decor.block("furnish:spruce_crate", -2.95, 0.0, 3.05, facing="front", alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "fl_crate_top", (-2.95, 1.0, 3.05), size=0.62, yaw=0.15, solid=True)
    ml.barrel(shell, "fl_barrel", (-3.65, 0.0, 2.55), r=0.34, h=0.86)
    ml.crate(shell, "fl_crate_1", (-2.75, 0.0, 2.2), size=(0.8, 0.7, 0.6), yaw=-0.08, solid=True)
    ml.crate(shell, "chest", (-2.0, 0.0, 3.15), size=(0.82, 0.55, 0.58), yaw=0.04, region="crate", top="crate_top", solid=True)
    ml.rbox(shell, "chest_lid", (-2.0, 0.55, 3.15), (0.84, 0.14, 0.6), 0.04, {"all": "crate"}, stretch=True)
    for k, s_ in enumerate((-0.3, 0.3)):
        add_cube(det, "chest_band_%d" % k, (-2.0 + s_, 0.35, 3.15), ry(0.04), (0.08, 0.72, 0.62), "iron")
    add_cube(det, "chest_lock", (-2.0, 0.5, 3.46), ry(0.04), (0.14, 0.18, 0.04), "iron")
    pe.round_sack(shell, det, "fsack", (-1.28, 0.0, 3.38), region="e_sack", yaw=0.2, w=0.6, h=0.78)
    ml.crate(shell, "flower_crate", (-0.68, 0.0, 2.68), size=(0.6, 0.62, 0.58), yaw=-0.05, solid=True)
    ml.crate(det, "flower_box", (-0.68, 0.62, 2.68), size=(0.56, 0.18, 0.4), yaw=-0.05, top="e_soil", solid=False)
    pe.plant(det, "white_fl", (-0.68, 0.62, 2.68), 0.62, 0.44, "e_fl_white", pot=None, pot_h=0.14)
    # ---- front right: the barrel heaped with apples, the basket of green apples, a crate
    ml.barrel(shell, "apple_barrel", (3.35, 0.0, 1.85), r=0.38, h=0.9, content="e_redapples")
    ml.basket(shell, "green_basket", (4.05, 0.0, 2.45), r=0.36, h=0.38, content="e_greenapples", handle=True, solid=True)
    decor.block("farmersdelight:wooden_basket", 3.55, 0.0, 0.7, facing="front", scale=0.7, fallback="basket")
    ml.crate(shell, "r_crate", (3.6, 0.0, -0.4), size=(0.7, 0.62, 0.62), yaw=0.1, solid=True)
    decor.block("landsoficaria:cypress_barrel", -3.9, 0.0, -0.7, facing="neg_x", alt="minecraft:barrel", fallback="barrel")
    pe.check_free(NAME, (NPC_SPOT[0], 0.0, NPC_SPOT[1], NPC_SPOT[0] + 1.0, 2.2, NPC_SPOT[1] + 1.0))
    return root


def item_icon(path):
    """16x16: the pointed red roof with its cream stripe and gold spire, the gantry and ropes on the left, the banner."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, cream, gold, wood, rope, dark = RED, CREAM, GOLD, (120, 76, 40), (210, 170, 100), (50, 32, 18)
    p[10, 0] = gold + (255,)
    for y in range(1, 8):
        half = 0.6 + (y - 1) * 0.85
        for x in range(16):
            dx = x - 10
            if abs(dx) <= half:
                p[x, y] = (cream if 0.25 < dx / max(half, 0.6) < 0.6 else red) + (255,)
    for x in range(4, 16):
        p[x, 8] = (red if (x // 2) % 2 == 0 else cream) + (255,)
        if x % 2 == 0:
            p[x, 9] = gold + (255,)
    for y in range(1, 16):   # the gantry / scaffold post on the left
        p[2, y] = wood + (255,)
    for x in range(1, 7):
        p[x, 2] = wood + (255,)
    for k in range(6):       # the diagonal rope
        p[3 + k, 3 + k // 2] = rope + (255,)
    for y in range(9, 16):
        p[5, y] = wood + (255,)
        p[15, y] = wood + (255,)
    for y in range(9, 13):   # the banner
        for x in (6, 7):
            p[x, y] = red + (255,)
    p[6, 10] = gold + (255,)
    for y in range(10, 15):
        for x in range(8, 15):
            p[x, y] = dark + (255,)
    for x in range(1, 16):
        p[x, 15] = (120, 34, 30, 255)
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
