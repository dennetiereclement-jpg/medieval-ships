#!/usr/bin/env python3
"""tente_fleur_de_lys — Tente à la fleur de lys / Fleur-de-lis Tent (1.26.0, market group E; reference:
scratchpad/ref2/tente_fleur_de_lys_ref.png, picture 139).

A tall pointed red-and-cream marquee, one block (TentType group "tents"), about 9 blocks wide with the two lantern arms
and the goods outside, the gold spire at about 7.3:

  - a HIGH four-sided pointed roof, sagging between its hips, wide wine-red and cream stripes radiating from the apex,
    a gold spire on top with a wooden spreader bar and its knobs below it;
  - the BIG FLEUR-DE-LIS BANNER: wine red, gold border, two gold fleurs-de-lis, it lies on the front roof slope from
    near the apex and hangs on below the eave to a V point with a long gold fringe;
  - red SWAGS with long GOLD FRINGES draped along the eaves (two across the front, meeting under the banner), gold
    TASSELS where they are hooked up;
  - square wooden posts, the two front ones with a CROSSBAR at the top (brace and a hanging lantern on the outer arm),
    rope lashings round the posts; CREAM DRAPES tied back with ropes on both front posts; the sides are red-and-cream
    skirts sloping out to the ground, guy ropes to pegs;
  - inside: a rail with GARLIC, RED PEPPERS, LAVENDER and a cream cloth hanging from it, a framed fleur-de-lis hanging
    on the back-left, red drapes on the back wall, the counter under a red cloth with a gold fringe (rolled cloths, a
    bowl of tomatoes, green bottles, a lamp, a sack), a shelf of CLOTH BOLTS (cream, red, blue), hanging blue and red
    fabrics, CHEESE on a crate, a chest with a folded blanket, barrels, a bell rope;
  - in front: a box of yellow flowers, an iron-bound chest painted red and gold, a sack, a wicker basket of grain, the
    RED RUG with a cream-and-gold border.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in round the
counter's left end. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_fleur_de_lys.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_fleur_de_lys.json, models/entity + blockbench/tente_fleur_de_lys.bbmodel,
textures/entity/tente_fleur_de_lys.png, textures/item/tente_fleur_de_lys.png, interiors/tente_fleur_de_lys_decor.json.
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
NAME = "tente_fleur_de_lys"
v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _scale = ml._rgb, ml._scale

WINE, CREAM = _rgb("6c1622"), _rgb("e4d2ae")
GOLD = _rgb("e8b040")

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 2.9, 2.3           # posts at x = +-HW, z = +-HD
PD = 0.5
EAVE = 3.55                 # the eave beams' top = the roof's lower edge
RW, RD = HW + 0.25, HD + 0.25
APEX = 6.55
POST_TOP = 4.35             # the front posts (crossbars at the top)
COUNTER = (-1.25, 1.25, 0.55, 1.15)
COUNTER_H = 1.0
NPC_SPOT = (-0.6, -0.75)
BAR_Y = 4.05                # the front posts' crossbars


def paint_banner(img):
    """The big banner: wine red, gold border, a V point with a long gold fringe, two gold fleurs-de-lis (one on the
    roof part, one on the hanging part)."""
    w, h = img.size
    pe.panel(WINE, 3901, fringe=10, motif=None, point=0.1, gold=GOLD)(img)
    s = int(w * 0.66)
    pe.fleur(img, ((w - s) // 2, int(h * 0.12), s, int(s * 1.12)), GOLD, _scale(WINE, 0.5))
    s2 = int(w * 0.58)
    pe.fleur(img, ((w - s2) // 2, int(h * 0.62), s2, int(s2 * 1.12)), GOLD, _scale(WINE, 0.5))


def paint_swag(img):
    """The eave swags: wine red folds, a gold braid band, a long gold fringe (cut-out)."""
    rng = random.Random(3902)
    w, h = img.size
    pe.weave(img, WINE, rng)
    px = img.load()
    body = int(h * 0.56)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            k = 0.82 + 0.22 * math.sin(math.pi * ((x * 6.0 / w) % 1.0)) - 0.12 * (y < 3)
            px[x, y] = _scale((r, g, b), k) + (255,)
    for y in range(body - 4, body):
        for x in range(w):
            px[x, y] = ml._jitter(_scale(GOLD, 0.9 if y in (body - 4, body - 1) else 1.08), rng, 8) + (255,)
    pe.fringe_rows(px, w, h, body, GOLD, rng, tassel=4)


def paint_tassel(img):
    """A gold tassel (cut-out): a knot on top, a flared skirt of threads."""
    rng = random.Random(3903)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (0, 0, 0, 0)
    for y in range(h):
        t = y / (h - 1)
        if t < 0.25:
            half = w * 0.18 + 2 * math.sin(math.pi * t / 0.25)
        elif t < 0.35:
            half = w * 0.14
        else:
            half = w * 0.18 + (w * 0.3) * (t - 0.35) / 0.65
        for x in range(w):
            dx = abs(x - (w - 1) / 2)
            if dx <= half and not (t > 0.4 and x % 2 == 1 and y > h - 3):
                k = 1.1 - 0.35 * (dx / max(1, half)) - (0.15 if (t > 0.35 and x % 2) else 0)
                px[x, y] = ml._jitter(_scale(GOLD, k), rng, 8) + (255,)


def paint_chest(img):
    """The front chest's painted planks: deep red with a gold lozenge, iron frame edges."""
    rng = random.Random(3904)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), _rgb("6a2a26"), _rgb("3a1410"), 8, rng, joints=False, knots=0.05, grain=0.1, shade=0.05)
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3:
                px[x, y] = ml._jitter(_rgb("4a4c52"), rng, 6) + (255,)
            elif abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5) in (6, 7):
                px[x, y] = ml._jitter(GOLD, rng, 8) + (255,)
    for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        px[x, y] = (170, 170, 176, 255)


def add_regions(atlas):
    s = 3900
    atlas.add("fl_roof", 160, 96, pe.stripes([WINE, CREAM], 5, s + 10, fold=0.16))
    atlas.add("fl_banner", 48, 160, paint_banner)
    atlas.add("fl_rug", 128, 96, pe.rug("8a1e26", "5a1218", "e8b848", "d8c49a", s + 11))
    atlas.add("fl_curtain", 48, 96, pe.stripes([CREAM, _scale(CREAM, 0.9)], 3, s + 12, fold=0.4, seams=False))
    atlas.add("fl_wall", 128, 64, pe.stripes([WINE, CREAM], 6, s + 13, fold=0.25))
    atlas.add("fl_skirt", 128, 64, pe.stripes([WINE, _scale(WINE, 0.86)], 6, s + 34, fold=0.35, seams=False, hem=(_scale(WINE, 0.6), 3)))
    atlas.add("fl_back", 64, 64, pe.stripes([_scale(WINE, 0.8), _scale(WINE, 0.72)], 4, s + 14, fold=0.4, seams=False))
    atlas.add("fl_swag", 128, 32, paint_swag)
    atlas.add("fl_cloth_hang", 64, 32, pe.panel(WINE, s + 15, fringe=10, motif=None, gold=GOLD))
    atlas.add("fl_sign", 32, 40, pe.framed_sign("6a1a26", s + 16))
    atlas.add("fl_chest", 32, 32, paint_chest)
    atlas.add("fl_rag", 24, 32, pe.panel(_rgb("e0cc98"), s + 17, fringe=5, motif=None, gold=_rgb("c8a868"), fold=0.3))
    atlas.add("fl_fab_blue", 24, 64, pe.stripes([_rgb("36508a"), _rgb("2e4478")], 2, s + 18, fold=0.4, seams=False, hem=(GOLD, 3)))
    atlas.add("fl_fab_red", 24, 64, pe.stripes([_rgb("8a2028"), _rgb("701a22")], 2, s + 19, fold=0.4, seams=False, hem=(GOLD, 3)))
    atlas.add("e_post", 64, 16, pe.wood("8a5428", "4a2a12", s + 20))
    atlas.add("e_garlic", 24, 40, pe.bunch("garlic", s + 21))
    atlas.add("e_peppers", 24, 40, pe.bunch("peppers", s + 22))
    atlas.add("e_lavender", 24, 40, pe.bunch("lavender", s + 23))
    atlas.add("e_fl_yellow", 32, 32, pe.flowers([_rgb("f0c020"), _rgb("e8a818"), _rgb("f8d850")], s + 24))
    atlas.add("e_tomatoes", 32, 32, pe.heap(["d02a1a", "e83a2a", "b01e14"], s + 25, r=4))
    atlas.add("e_grain", 32, 32, pe.heap(["d8b060", "c89848", "e8c878"], s + 26, bg="a87838", r=2))
    atlas.add("e_cheese", 32, 16, pe.cheese(s + 27))
    atlas.add("e_cheese_top", 16, 16, pe.cheese(s + 28))
    atlas.add("e_band", 32, 8, pe.iron_band(s + 29))
    atlas.add("e_tassel", 16, 24, paint_tassel)
    atlas.add("e_bolt_cream", 16, 16, pe.carpet_roll("e8dcc0", "c8a878", s + 30, cream=True))
    atlas.add("e_sack", 32, 32, pe.burlap("c8b090", s + 31))
    atlas.add("e_soil", 16, 16, pe.heap(["3a2a1a", "4a3420"], s + 32, bg="2a1c10", r=2))
    atlas.add("e_gold_band", 16, 8, pe.panel(GOLD, s + 33, fringe=0, motif=None, gold=_rgb("a87018")))
    print("atlas", atlas.size)


def roof_banner(bone, name, face, xc, w, t0, hang, region, ny_roof=4, ny_hang=2):
    """The big banner: it lies on the front roof face from parameter t0 down to the eave (ny_roof rows), then hangs
    `hang` straight down (ny_hang rows); one loft, its texture running over the whole length."""
    n = ny_roof + ny_hang
    f = ny_roof / n
    cache = {}

    def on_roof(s, t):
        key = (round(s, 4), round(t, 4))
        if key not in cache:
            x = xc + (s - 0.5) * w
            p = pe.roof_point(face, x, t0 + (1.0 - t0) * t, axis=0)
            cache[key] = p + UP * 0.05 + Z * 0.02
        return cache[key]

    def P(s, t):
        if t <= f + 1e-9:
            return on_roof(s, t / f)
        e = on_roof(s, 1.0)
        u = (t - f) / (1 - f)
        return e + Z * (0.04 + 0.05 * math.sin(math.pi * u)) - UP * (hang * u)
    loft(bone, name, P, 2, n, region, th=0.02, u_hint=X, v_hint=-UP)


# ---------------------------------------------------------------- the build
def build(atlas, decor):
    rng = random.Random(139)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]
    for k, (x, z) in enumerate(corners):
        top = POST_TOP if k < 2 else EAVE + 0.15
        pe.post(shell, det, "post_%d" % k, x, z, top, d=PD, bands=(0.25, 2.1) if k < 2 else (0.25,), caps=1 if k < 2 else 0, cap_w=0.6,
                solid_to=EAVE, cap_region="wood_dark")
    by = EAVE - 0.16
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.3, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.28, extend=0.18)
    beam(shell, "tie_beam", (-HW, by - 0.04, 0.0), (HW, by - 0.04, 0.0), 0.2, "wood_dark", extend=0.08)
    beam(shell, "king_post", (0, by, 0.0), (0, APEX - 0.4, 0.0), 0.18, "wood_dark")
    # the front posts' crossbars with braces (a lantern hangs from each outer arm), rope lashings
    for k, sx in enumerate((-1, 1)):
        x = sx * HW
        beam(shell, "bar_%d" % k, (x - sx * 0.25, BAR_Y, HD), (x + sx * 1.15, BAR_Y, HD), 0.24, {"all": "beam", "+1": "end_grain", "-1": "end_grain"},
             width=0.24)
        beam(shell, "bar_brace_%d" % k, (x + sx * 0.2, BAR_Y - 0.75, HD), (x + sx * 0.75, BAR_Y - 0.08, HD), 0.14, "wood_dark", extend=0.04)
        pe.rope_wrap(det, "bar_lash_%d" % k, x, HD, BAR_Y - 0.06, PD / 2, turns=2, th=0.08)
        pe.rope_wrap(det, "post_lash_%d" % k, x, HD, 2.55, PD / 2, turns=3, th=0.09)
        pe.rope_wrap(det, "post_foot_%d" % k, x, HD, 0.75, PD / 2, turns=1, th=0.12)
        tip = v3(x + sx * 1.0, BAR_Y - 0.12, HD)
        ml.rope(det, "lamp_rope_%d" % k, tip, tip - UP * 0.32, d=0.04)
        pe.lamp(shell, det, "lamp_%d" % k, tip - UP * 0.56, size=0.4, chain_to=None)
    # ---- the high pointed roof, stripes radiating from the apex
    eave = [(-RW, EAVE, RD), (RW, EAVE, RD), (RW, EAVE, -RD), (-RW, EAVE, -RD)]
    faces = pe.pyramid_roof(shell, "roof", eave, [(0, APEX, 0)] * 4, "fl_roof", sag=0.42, nx=5, ny=9)
    for k in range(4):
        ml.rope(det, "hip_%d" % k, v3(0, APEX, 0), v3(*eave[k]) + UP * 0.03, d=0.06, segs=3)
    # the spire, the spreader bar with its knobs below it
    ml.octo(shell, "spire_base", (0, APEX - 0.1, 0), 0.16, 0.22, "wood_dark")
    ml.octo(shell, "spire_collar", (0, APEX + 0.12, 0), 0.12, 0.1, "gold")
    add_cube(shell, "spire_bulb", (0, APEX + 0.36, 0), ry(math.pi / 4), (0.22, 0.32, 0.22), "gold")
    add_cube(shell, "spire_tip", (0, APEX + 0.7, 0), EYE, (0.08, 0.38, 0.08), "gold")
    sy = APEX - 0.32
    beam(shell, "spreader", (-1.05, sy, 0.0), (1.05, sy, 0.0), 0.16, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, sx in enumerate((-1, 1)):
        box(shell, "spreader_knob_%d" % k, (sx * 1.05 - 0.12, sy - 0.12, -0.12), (sx * 1.05 + 0.12, sy + 0.12, 0.12), {"all": "wood_dark", "+2": "end_grain"})
        add_cube(det, "spreader_peg_%d" % k, (sx * 1.05, sy + 0.2, 0), EYE, (0.08, 0.16, 0.08), "wood")
    beam(shell, "cross_post", (-0.75, sy, 0.0), (-0.75, sy + 0.6, 0.0), 0.12, "wood_dark")
    beam(shell, "cross_arm", (-0.95, sy + 0.4, 0.0), (-0.55, sy + 0.4, 0.0), 0.1, "wood_dark")
    # ---- the big fleur-de-lis banner: on the front slope from near the apex, then hanging below the eave
    roof_banner(shell, "banner", faces[0], 0.05, 1.28, 0.12, 1.85, "fl_banner")
    beam(det, "banner_rod", (-0.66, APEX - 0.5, 0.42), (0.76, APEX - 0.5, 0.42), 0.06, "wood_dark")
    # ---- swags with gold fringes along the eaves, tassels at the hooks
    zf = RD + 0.06
    pe.swag(shell, "swag_fl", (-RW - 0.05, EAVE + 0.08, zf), (-0.55, EAVE + 0.08, zf), 0.3, 0.85, Z, "fl_swag", nx=5)
    pe.swag(shell, "swag_fr", (0.65, EAVE + 0.08, zf), (RW + 0.05, EAVE + 0.08, zf), 0.3, 0.85, Z, "fl_swag", nx=5)
    for k, sx in enumerate((-1, 1)):
        xs = sx * (RW + 0.06)
        pe.swag(shell, "swag_side_%d" % k, (xs, EAVE + 0.08, RD if sx < 0 else -RD), (xs, EAVE + 0.08, -RD if sx < 0 else RD), 0.3, 0.75,
                v3(sx, 0, 0), "fl_swag", nx=6)
    pe.swag(shell, "swag_back", (RW, EAVE + 0.08, -RD - 0.06), (-RW, EAVE + 0.08, -RD - 0.06), 0.3, 0.75, -Z, "fl_swag", nx=6)
    for k, x in enumerate((-RW, -0.55, 0.65, RW)):
        pe.tassel(det, "tassel_%d" % k, (x, EAVE + 0.02, zf + 0.06), h=0.42, w=0.16)
        add_cube(det, "tassel_cord_%d" % k, (x, EAVE - 0.0, zf + 0.06), EYE, (0.04, 0.1, 0.04), "gold")
    # ---- the side skirts (red-and-cream, sloping out to the ground), the back wall, guy ropes
    for k, sx in enumerate((-1, 1)):
        za, zb = (-HD, 1.15) if sx < 0 else (1.0, -HD)

        def SK(s, t, sx=sx, za=za, zb=zb):
            z = za + (zb - za) * s
            x = sx * (HW + 0.12 + 0.55 * t)
            return v3(x, (EAVE - 0.2) * (1 - t) + 0.02 * t, z) + v3(sx, 0, 0) * (0.05 * math.sin(s * math.pi * 6) * t)
        loft(shell, "skirt_%d" % k, SK, 6, 2, "fl_skirt", th=0.03)
        collide((min(sx * HW, sx * (HW + 0.7)), 0.0, min(za, zb), max(sx * HW, sx * (HW + 0.7)), 2.0, max(za, zb)))
    pe.wall(shell, "wall_back", (HW, 0, -HD - 0.08), (-HW, 0, -HD - 0.08), 0.0, by - 0.12, -Z, "fl_wall", nx=6)
    collide((-HW, 0.0, -HD - 0.14, HW, by - 0.12, -HD - 0.02))
    pe.wall(shell, "drape_back", (-HW + 0.3, 0, -HD + 0.1), (HW - 0.3, 0, -HD + 0.1), 0.0, by - 0.25, Z, "fl_back", nx=8, fold=0.07)
    for k, (top, ground) in enumerate((((-HW - 0.2, POST_TOP - 0.2, HD), (-4.6, 0.0, 3.4)), ((HW + 0.2, POST_TOP - 0.2, HD), (4.55, 0.0, 3.5)),
                                       ((-HW, EAVE - 0.1, -HD), (-4.3, 0.0, -3.2)), ((HW, EAVE - 0.1, -HD), (4.3, 0.0, -3.2)))):
        ml.rope(det, "guy_%d" % k, top, ground, d=0.07, sag=0.1, segs=3)
        ml.tl.peg(det, "guy_peg_%d" % k, ground, top, length=0.45, d=0.1, region="wood")
    # ---- cream drapes tied back with ropes on the two front posts (an outer one hanging from the crossbar, an inner one)
    for k, sx in enumerate((-1, 1)):
        x = sx * HW
        pe.drape(shell, det, "drape_out_%d" % k, (x + sx * 1.05, BAR_Y - 0.12, HD + 0.08), (x + sx * 0.25, BAR_Y - 0.12, HD + 0.08),
                 (x + sx * 0.3, 1.5, HD + 0.12), (x + sx * 0.35, 0.04, HD + 0.14), (x + sx * 0.8, 0.04, HD + 0.2), Z, "fl_curtain", nx=3,
                 tie_region="rope", tie_size=(0.34, 0.14, 0.24))
        pe.drape(shell, det, "drape_in_%d" % k, (x - sx * 0.28, by - 0.15, HD - 0.05), (x - sx * 1.05, by - 0.15, HD - 0.05),
                 (x - sx * 0.32, 1.45, HD - 0.12), (x - sx * 0.3, 0.04, HD - 0.12), (x - sx * 0.62, 0.04, HD - 0.15), Z, "fl_curtain", nx=3,
                 tie_region="rope", tie_size=(0.3, 0.12, 0.2))
    # ---- inside: the rail with the hanging garlic, peppers, lavender and a cloth; the framed fleur; hanging fabrics
    beam(shell, "rail", (-HW + 0.2, 2.72, 1.55), (HW - 0.2, 2.72, 1.55), 0.12, "wood")
    for k, x in enumerate((-2.3, -0.9, 0.6, 2.2)):
        pe.rope_wrap(det, "rail_lash_%d" % k, x, 1.55, 2.66, 0.07, turns=1, th=0.06)
    for k, (x, kind, ln, wd) in enumerate(((-2.05, "e_lavender", 0.62, 0.3), (-1.72, "e_lavender", 0.55, 0.28), (-1.35, "e_garlic", 0.56, 0.28),
                                           (-0.35, "e_peppers", 0.62, 0.28), (1.65, "e_lavender", 0.5, 0.26))):
        ml.hanging_bunch(det, "bunch_%d" % k, (x, 2.66, 1.55), kind=kind, length=ln, width=wd, string=0.06)
    pe.lamp(shell, det, "lamp_in", (0.95, 2.2, 1.55), size=0.34, chain_to=(0.95, 2.66, 1.55))
    pe.hang_panel(det, "rag", (-0.8, 2.68, 1.6), 0.36, 0.5, (0, 0, 1), "fl_rag", wave=0.04, ny=2)
    ml.plate(shell, "sign", (-1.9, 2.0, -HD + 0.22), 0.62, 0.78, "fl_sign", normal=(0, 0, 1), th=0.04, edge="wood_dark")
    beam(det, "sign_rope", (-2.1, 2.55, -HD + 0.22), (-1.7, 2.55, -HD + 0.22), 0.03, "rope")
    for k, (x, reg) in enumerate(((1.15, "fl_fab_red"), (1.42, "fl_fab_blue"), (1.68, "fl_fab_red"))):
        pe.hang_panel(shell, "fabric_%d" % k, (x, 2.5, -1.25 + 0.03 * k), 0.26, 1.55, (0, 0, 1), reg, wave=0.04, ny=2)
    beam(det, "fabric_rod", (0.95, 2.52, -1.25), (1.9, 2.52, -1.25), 0.05, "wood_dark")
    # the bolt shelf on the right (cream, red, blue cloth bolts)
    levels = ml.shelf_unit(shell, "bolt_shelf", 1.95, 2.75, -1.6, -0.6, levels=(0.55, 1.05, 1.55, 2.05), h=2.35, back=False, uprights=2, detail=det)
    regs = ("e_bolt_cream", "cloth_red", "e_bolt_cream", "cloth_blue", "cloth_red")
    for j, (x0, x1, yy, zf_, zb) in enumerate(sorted(levels, key=lambda s: s[2])):
        for i in range(2):
            pe.bolt(det, "bolt_%d_%d" % (j, i), ((x0 + x1) / 2, yy + 0.1 + 0.19 * i, (zf_ + zb) / 2), length=0.95, r=0.1, yaw=math.pi / 2,
                    region=regs[(i + j) % len(regs)], end="cloth_white")
    # ---- the counter with the red cloth with a gold fringe and its goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    box(shell, "cloth", (-0.4, y, cz0 + 0.02), (1.3, y + 0.016, cz1 + 0.06), {"all": "cloth_red"}, stretch=True, u_dir=X)
    ml.plate(shell, "cloth_front", (0.45, y - 0.3, cz1 + 0.07), 1.72, 0.62, "fl_cloth_hang", normal=(0, 0, 1), th=0.012, edge="cloth_red")
    for k, (x, dz) in enumerate(((-1.0, 0.05), (-0.78, 0.07))):
        pe.bolt(det, "roll_%d" % k, (x, y + 0.12, zc + dz), length=0.36, r=0.11, yaw=math.pi / 2 + 0.1, region="e_bolt_cream", end="cloth_white")
    ml.crate(det, "roll_tray", (-0.89, y, zc + 0.06), size=(0.5, 0.06, 0.42), solid=False)
    ml.basket(det, "tomato_bowl", (-0.3, y, zc), r=0.22, h=0.1, content="e_tomatoes", handle=False)
    decor.block("farmhouse_decorations:kerosene_lantern", 0.15, y, zc, facing="front", scale=1.1, glow=True, alt="minecraft:lantern",
                fallback="lantern", solid=False)
    for k, x in enumerate((0.45, 0.62, 0.79)):
        decor.block("farmhouse_decorations:wine_bottle", x, y, zc - 0.05 + 0.04 * k, facing="front", scale=1.25, fallback="potion_green", solid=False)
    ml.sack(det, "counter_sack", (1.05, y, zc - 0.05), s=0.36, yaw=0.3, region="e_sack")
    # ---- the cheese crate, the chest with a folded blanket, the barrel with rolled cloth, the bell rope
    decor.block("furnish:spruce_crate", 1.55, 0.0, 0.35, facing="front", scale=0.85, alt="minecraft:barrel", fallback="crate")
    for k, (dx, dz, yaw) in enumerate(((-0.18, 0.12, 0.1), (0.15, 0.1, -0.2), (0.0, -0.15, 0.3))):
        pe.cheese_block(det, "cheese_%d" % k, (1.55 + dx, 0.85, 0.35 + dz), s=(0.26, 0.2, 0.24), yaw=yaw)
    pe.cheese_block(det, "cheese_top", (1.52, 1.05, 0.38), s=(0.24, 0.18, 0.2), yaw=0.4)
    ml.crate(shell, "chest", (2.25, 0.0, 1.0), size=(0.8, 0.58, 0.56), yaw=-0.1, region="fl_chest", top="crate_top", solid=True)
    pe.folded_stack(det, "blanket", (2.25, 0.58, 1.0), 0.72, 0.5, ["cloth_dark", "cloth_blue"], h=0.08, yaw=-0.1)
    ml.barrel(shell, "rbarrel", (2.45, 0.0, 2.0), r=0.38, h=0.92)
    pe.bolt(det, "rbarrel_roll", (2.45, 1.02, 2.0), length=0.62, r=0.1, yaw=0.2, region="cloth_red", end="e_bolt_cream")
    ml.rope(det, "bell_rope", (2.05, by - 0.12, 1.75), (2.05, 0.35, 1.75), d=0.07)
    ml.crate(det, "bell_rope_coil", (2.05, 0.0, 1.75), size=(0.24, 0.32, 0.24), region="rope", top="rope", solid=False)
    # ---- the left barrel inside, the left goods
    ml.barrel(shell, "lbarrel", (-2.35, 0.0, 1.25), r=0.38, h=0.92)
    ml.barrel(shell, "lbarrel_back", (-2.3, 0.0, -1.4), r=0.36, h=0.88)
    decor.block("landsoficaria:cypress_barrel", -2.3, 0.88, -1.4, facing="front", scale=0.6, alt="minecraft:barrel", fallback="barrel", solid=False)
    # ---- in front: the yellow flower box, the red-and-gold chest, a sack, the basket of grain; the rug
    ml.crate(shell, "flower_box", (-3.6, 0.0, 2.95), size=(0.8, 0.55, 0.62), yaw=0.08, top="e_soil", solid=True)
    pe.plant(det, "yellow_fl", (-3.6, 0.55, 2.95), 0.8, 0.5, "e_fl_yellow", pot=None, pot_h=0.0)
    ml.crate(shell, "fchest", (-2.25, 0.0, 3.2), size=(0.95, 0.66, 0.68), yaw=0.05, region="fl_chest", top="crate_top", solid=True)
    for k, s_ in enumerate((-0.32, 0.32)):
        add_cube(det, "fchest_band_%d" % k, (-2.25 + s_, 0.34, 3.2), ry(0.05), (0.07, 0.7, 0.71), "iron")
    pe.bolt(det, "fchest_roll", (-2.3, 0.75, 3.15), length=0.7, r=0.09, yaw=0.1, region="e_bolt_cream", end="cloth_white")
    pe.round_sack(shell, det, "fsack", (-1.55, 0.0, 3.45), region="e_sack", yaw=0.25, w=0.6, h=0.8)
    ml.basket(shell, "grain_basket", (-0.85, 0.0, 3.3), r=0.36, h=0.42, content="e_grain", handle=True, solid=True)
    ml.rug(shell, "rug", -0.65, 2.0, 2.05, 4.15, y=0.0, region="fl_rug")
    decor.block("farmersdelight:rice_bag", 3.55, 0.0, 1.55, facing="front", fallback="sack")
    pe.check_free(NAME, (NPC_SPOT[0], 0.0, NPC_SPOT[1], NPC_SPOT[0] + 1.0, 2.2, NPC_SPOT[1] + 1.0))
    return root


def item_icon(path):
    """16x16: the high pointed red-and-cream roof with the gold spire and the fleur banner, the gold-fringed swags,
    two posts with their crossbars and lanterns."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    wine, cream, gold, wood, dark = WINE, CREAM, GOLD, (130, 84, 44), (50, 32, 18)
    p[7, 0] = p[8, 0] = gold + (255,)
    for y in range(1, 9):
        half = 0.6 + (y - 1) * 0.95
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                k = int((dx / max(half, 0.6) + 1) * 2.5)
                p[x, y] = (wine if k % 2 == 0 else cream) + (255,)
    for y in range(3, 12):   # the banner
        for x in (7, 8):
            p[x, y] = (wine if y < 11 else gold) + (255,)
    p[7, 5] = p[8, 5] = gold + (255,)
    p[7, 8] = p[8, 8] = gold + (255,)
    for x in range(1, 15):
        p[x, 9] = wine + (255,) if x not in (7, 8) else p[x, 9]
        if x % 2 and x not in (7, 8):
            p[x, 10] = gold + (255,)
    for y in range(3, 16):
        for x in (1, 14):
            p[x, y] = wood + (255,)
    for x in (0, 2, 13, 15):
        p[x, 3] = wood + (255,)
    p[0, 5] = p[15, 5] = (255, 200, 90, 255)
    for y in range(11, 15):
        for x in range(2, 14):
            if p[x, y][3] == 0:
                p[x, y] = dark + (255,)
    for x in range(4, 12):
        p[x, 13] = (140, 30, 40, 255)
    for x in range(1, 15):
        p[x, 15] = (130, 30, 38, 255)
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
