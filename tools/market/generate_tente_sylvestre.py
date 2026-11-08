#!/usr/bin/env python3
"""tente_sylvestre — Tente marchande sylvestre / Sylvan Merchant Tent (1.26.0, market group F; reference:
scratchpad/ref2/tente_sylvestre_ref.png, the bottom-left tent of the board tentes_065_planche.png).

An elven merchant tent grown rather than built, one block (TentType group "tents", the integrator's list MARKET_TENTS):

  - an ORGANIC FRAME: four gnarled tree-trunk posts with spreading roots, mossy bark, leaning a little; big curved
    BRANCH ARCHES springing from post to post on the four sides, the front one rising to a high crook near the right
    and ending in a curled hook, a branch stub beyond the back-left post (it carries the banner) and a curled arm on
    the front-right post (it carries a lantern);
  - a pointed, sweeping (concave) pavilion roof of GREEN and CREAM stripes mottled like leaves, its edges arching up
    between the posts under the branches, a leafy dagged hem, a gold finial on the peak;
  - mottled cream-and-green canvas walls flaring out to the ground at the back and the sides, a big mottled drape
    tied back to the front-left post, a smaller one at the front-right, green curtains with gold ties inside the back
    corners, a green panel with a golden leaf rune hanging at the front of the left side;
  - WISTERIA: purple clusters hanging from the front arch and near the front-right post; ivy and vines all over the
    branches and posts;
  - a cream BANNER with the green TREE emblem and a gold fringe on the back-left branch, hanging LANTERNS (inside the
    front arch, on the front-right arm) and a glowing GREEN CRYSTAL lantern on a slim staff by the front-left post;
  - inside: back shelves with candles, books, potions and pots of plants; the right counter with the big glowing
    CYAN CRYSTAL, potions and purple crystals; a left table with jars and herbs; the dark blue rug with a golden rune;
  - outside along the left side: the desk with an open book, a green book and a pile of books, a crate topped with a
    basket of moss and flowers.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the right counter (NPC_SPOT), reached on foot round the
counter's left end. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_sylvestre.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_sylvestre.json, models/entity + blockbench/tente_sylvestre.bbmodel,
textures/entity/tente_sylvestre.png, textures/item/tente_sylvestre.png, interiors/tente_sylvestre_decor.json.
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
NAME = "tente_sylvestre"
v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _scale = ml._rgb, ml._scale

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 3.1, 3.6            # tree posts at x = +-HW, z = +-HD
EAVE = 3.35                  # where the arches spring from the posts
EY = 3.3                     # the roof's corners
W, D = HW + 0.45, HD + 0.35  # the roof's eave half length / half depth
APEX = 6.7                   # the peak (the finial above it)
ARCH = 0.65                  # how much the roof edge rises between the posts
COUNTER = (0.2, 2.45, -1.9, -1.32)   # the right counter: x0, x1, z0, z1
COUNTER_H = 1.0
SHELF_Z = (-3.42, -3.02)
NPC_SPOT = (0.9, -2.96)      # (x0, z0) of the free 1 x 1 x 2.2 place behind the right counter

GREEN, GREEN_DARK = _rgb("5a8a30"), _rgb("2c4a1a")
CREAM = _rgb("e6dcbc")
BARK, BARK_DARK, MOSS = _rgb("7a5232"), _rgb("3a2414"), _rgb("6a8a2a")
GOLDF = _rgb("d4a640")


def add_regions(atlas):
    """This tent's regions, packed in the free band of the 512 px atlas."""
    atlas.add("sy_roof", 192, 128, pf.stripes([GREEN, CREAM], 3201, n=4, mottle=(GREEN, CREAM), mottle_n=14, shade=(0.84, 1.04), fold=0.18))
    atlas.add("sy_rug", 128, 96, pf.rug(_rgb("283466"), _rgb("161c3c"), _rgb("c8a040"), 3202, motif=pf.leaf_rune))
    atlas.add("sy_banner", 48, 96, pf.banner(CREAM, _rgb("b89a58"), pf.tree, 3203, fringe=GOLDF, point="dags", emblem_box=(0.12, 0.1, 0.88, 0.7)))
    atlas.add("sy_rune", 48, 96, pf.banner(_scale(GREEN, 0.9), _rgb("2c4a1a"), pf.leaf_rune, 3204, fringe=_rgb("c8b07a"), point="v",
                                           emblem_box=(0.2, 0.18, 0.8, 0.66)))
    atlas.add("sy_drape", 64, 96, pf.patchwork(CREAM, 3205, patches=((GREEN, 16, 3, 7), (_rgb("8aa45a"), 8, 2, 5)), stitches=False, folds=3,
                                               shade=(0.84, 1.02)))
    atlas.add("sy_wall", 128, 64, pf.patchwork(_scale(CREAM, 0.86), 3206, patches=((_rgb("6a8a40"), 9, 2, 6), (_rgb("9aae6a"), 8, 2, 5)), stitches=False, folds=5,
                                               shade=(0.78, 0.98)))
    atlas.add("sy_bark", 64, 32, pf.bark(BARK, BARK_DARK, 3207, moss=MOSS, moss_n=7))
    atlas.add("sy_wisteria", 32, 64, pf.wisteria(3208))
    atlas.add("sy_curtain", 32, 64, pf.canvas(_rgb("3e6a26"), 3209, folds=3, fold_k=0.3, hem=GOLDF, shade=(0.8, 1.0)))
    atlas.add("sy_hem", 192, 24, pf.stripes([GREEN, CREAM], 3210, n=4, dag=12, mottle=(GREEN, CREAM), mottle_n=6))
    atlas.add("sy_crystal", 16, 32, pf.crystal_tex((190, 255, 246), (30, 160, 170), 3211))
    atlas.add("sy_crystal_g", 16, 16, pf.crystal_tex((200, 255, 170), (40, 150, 60), 3212))
    atlas.add("sy_leaf", 32, 32, pf.canvas(_rgb("5a8a34"), 3213, stains=0))
    atlas.add("f_flame", 8, 8, pf.flames(3214))
    if atlas.size != 512:
        raise AssertionError("the atlas grew to %d px: repack the regions" % atlas.size)


# ---------------------------------------------------------------- pieces
def tree_post(shell, det, name, foot, top, lean, d0=0.62, d1=0.42, roots=4, rng=None):
    """A gnarled tree-trunk post: a slightly S-bent trunk from foot to top (tapering d0 -> d1), spreading roots at the
    foot, a knot; collides as a column."""
    foot, top, lean = v3(*foot), v3(*top), v3(*lean)
    mid1 = foot + (top - foot) * 0.35 + lean * 0.12
    mid2 = foot + (top - foot) * 0.7 - lean * 0.06
    pf.branch(shell, name, [foot, mid1, mid2, top], d0, d1, "sy_bark", n=4)
    rng = rng or random.Random(1)
    for k in range(roots):
        a = 2 * math.pi * k / roots + rng.uniform(-0.3, 0.3) + 0.4
        out = v3(math.cos(a), 0, math.sin(a))
        p0 = foot + UP * 0.45 + out * 0.08
        p1 = foot + out * (0.55 + 0.15 * rng.random()) + UP * 0.05
        beam(shell, "%s_root_%d" % (name, k), p0, p1, 0.17, {"all": "sy_bark", "+1": "end_grain", "-1": "end_grain"}, extend=0.05)
        add_cube(det, "%s_rootmoss_%d" % (name, k), p1 + UP * 0.02, ry(-a), (0.14, 0.05, 0.16), "sy_leaf")
    add_cube(det, name + "_knot", mid1 + v3(0.2, 0.2, 0.05), ry(0.5), (0.12, 0.16, 0.12), "sy_bark")
    collide((foot[0] - 0.3, 0.0, foot[2] - 0.3, foot[0] + 0.3, EAVE, foot[2] + 0.3))


def ivy_on(det, name, pts, every=2, length=0.6, rng=None):
    """Ivy draped along a branch (points of its curve): little leaf plates and hanging strands."""
    rng = rng or random.Random(5)
    for k in range(0, len(pts) - 1, every):
        p = (pts[k] + pts[k + 1]) / 2
        d = norm(pts[k + 1] - pts[k])
        side = norm(np.cross(d, UP)) if abs(d[1]) < 0.95 else X
        ml.vine(det, "%s_%d" % (name, k), p + UP * 0.12 + side * 0.05, length * (0.6 + 0.8 * rng.random()), 0.34, normal=side)


def wisteria(det, name, top, length=0.9, w=0.34):
    """A wisteria cluster: two crossed cut-out planes and a little stem."""
    ml.crossed(det, name, v3(*top) - UP * length / 2, w, length, "sy_wisteria", yaw=0.3)


# ---------------------------------------------------------------- the build
def build(atlas, decor):
    rng = random.Random(32)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]   # FL, FR, BR, BL
    leans = [(-0.3, 0, 0.2), (0.25, 0, 0.25), (0.2, 0, -0.25), (-0.25, 0, -0.2)]
    for k, (x, z) in enumerate(corners):
        tree_post(shell, det, "post_%d" % k, (x, 0, z), (x, EAVE, z), leans[k], rng=rng)
    # ---- branch arches (front: rising to a high crook near the right, ending in a hook)
    T = [v3(x, EAVE - 0.05, z) for x, z in corners]
    fz = HD + 0.18
    front = pf.branch(shell, "arch_front", [T[0], (-1.6, EAVE + 0.75, fz), (0.3, EAVE + 1.55, fz), (1.75, EAVE + 2.3, fz),
                                            (1.55, EAVE + 2.75, fz - 0.05), (1.1, EAVE + 2.85, fz - 0.1)], 0.42, 0.18, "sy_bark", n=10)
    leg = pf.branch(shell, "arch_front_leg", [T[1], (HW - 0.45, EAVE + 1.0, fz), (2.15, EAVE + 1.85, fz), (1.8, EAVE + 2.25, fz)], 0.3, 0.24,
                    "sy_bark", n=5)
    side_l = pf.branch(shell, "arch_left", [T[3], (-HW - 0.2, EAVE + 0.9, -0.5), (-HW - 0.15, EAVE + 0.75, 1.2), T[0]], 0.3, 0.28, "sy_bark", n=6)
    side_r = pf.branch(shell, "arch_right", [T[1], (HW + 0.2, EAVE + 0.8, 1.0), (HW + 0.2, EAVE + 0.9, -0.8), T[2]], 0.3, 0.28, "sy_bark", n=6)
    back = pf.branch(shell, "arch_back", [T[2], (1.2, EAVE + 1.0, -HD - 0.2), (-1.2, EAVE + 1.0, -HD - 0.2), T[3]], 0.3, 0.28, "sy_bark", n=6)
    # the stub beyond the back-left post (carries the banner) and the curled arm of the front-right post (a lantern)
    stub = pf.branch(shell, "stub_bl", [T[3] + UP * 0.25, (-HW - 0.7, EAVE + 0.4, -HD + 0.05), (-HW - 1.35, EAVE + 0.45, -HD + 0.1),
                                        (-HW - 1.55, EAVE + 0.75, -HD + 0.1)], 0.26, 0.14, "sy_bark", n=4)
    arm = pf.branch(shell, "arm_fr", [T[1] - UP * 0.15, (HW + 0.55, EAVE - 0.05, HD + 0.05), (HW + 1.1, EAVE + 0.0, HD + 0.05),
                                      (HW + 1.28, EAVE + 0.3, HD + 0.05)], 0.22, 0.12, "sy_bark", n=4)
    # ---- the roof: a sweeping pointed pavilion, edges arching up between the posts, a leafy hem, the gold finial
    apex = (0.0, APEX, 0.0)
    C = (0.0, 2.0, 0.0)
    faces = []
    for k, ((xa, za), (xb, zb)) in enumerate((((-W, D), (W, D)), ((W, D), (W, -D)), ((W, -D), (-W, -D)), ((-W, -D), (-W, D)))):
        P = pf.roof_face(shell, "roof_%d" % k, apex, apex, (xa, EY, za), (xb, EY, zb), "sy_roof", nx=4, ny=5, sag=0.14, concave=0.85,
                         centre=C, droop=-ARCH)
        faces.append(P)
        pf.flap(shell, "hem_%d" % k, P, 0.32, "sy_hem", nx=4, out=0.05)
    ml.octo(shell, "finial_collar", (0, APEX - 0.15, 0), 0.2, 0.22, "gold")
    ml.octo(det, "finial_ball", (0, APEX + 0.07, 0), 0.13, 0.2, "gold")
    add_cube(det, "finial_spike", (0, APEX + 0.45, 0), ry(math.pi / 4), (0.12, 0.42, 0.12), "gold")
    add_cube(det, "finial_tip", (0, APEX + 0.72, 0), ry(math.pi / 4), (0.06, 0.14, 0.06), "gold")
    # ---- walls: mottled canvas flaring out at the back and the sides; drapes at the front; green curtains inside
    wall_top = EY - 0.2
    pf.hang_wall(shell, "wall_back", (-HW, 0, -HD), (HW, 0, -HD), 0.0, wall_top, -Z, "sy_wall", nx=6, flare=0.35)
    collide((-HW, 0.0, -HD - 0.2, HW, wall_top, -HD + 0.05))
    pf.hang_wall(shell, "wall_left", (-HW, 0, -HD), (-HW, 0, -0.1), 0.0, wall_top, -X, "sy_wall", nx=4, flare=0.45)
    collide((-HW - 0.25, 0.0, -HD, -HW + 0.05, wall_top, -0.1))
    pf.hang_wall(shell, "wall_right", (HW, 0, 1.2), (HW, 0, -HD), 0.0, wall_top, X, "sy_wall", nx=5, flare=0.45)
    collide((HW - 0.05, 0.0, -HD, HW + 0.25, wall_top, 1.2))
    # the big mottled drape tied to the front-left post, a smaller one at the front-right
    pf.tied_drape(shell, det, "drape_l", (-HW - 0.05, wall_top + 0.2, -0.15), (-HW + 0.1, wall_top + 0.35, HD + 0.1), (-HW + 0.05, 1.3, HD - 0.1),
                  (-HW - 0.8, 0.03, HD - 1.75), (-HW - 0.08, 0.03, HD - 0.28), v3(-1, 0, 0.2), "sy_drape", nx=4, tie_region="gold")
    collide((-HW - 0.55, 0.0, HD - 1.6, -HW + 0.05, 1.0, HD - 0.75))
    pf.tied_drape(shell, det, "drape_r", (HW + 0.05, wall_top + 0.25, 1.15), (HW - 0.1, wall_top + 0.3, HD + 0.05), (HW - 0.05, 1.25, HD - 0.1),
                  (HW + 0.5, 0.03, HD - 1.4), (HW + 0.05, 0.03, HD - 0.3), v3(1, 0, 0.3), "sy_drape", nx=2, tie_region="gold")
    for k, sx in enumerate((-1, 1)):
        x = sx * (HW - 0.35)
        pf.tied_drape(shell, det, "curtain_%d" % k, (x, wall_top - 0.05, -HD + 0.15), (x - sx * 0.95, wall_top - 0.05, -HD + 0.15),
                      (x - sx * 0.2, 1.3, -HD + 0.22), (x, 0.03, -HD + 0.2), (x - sx * 0.55, 0.03, -HD + 0.2), v3(0, 0, 1), "sy_curtain", nx=2,
                      tie_region="gold")
    # the green panel with the golden leaf rune at the front of the left side
    ml.banner(shell, "rune_panel", (-HW - 0.3, wall_top + 0.45, HD - 0.62), 0.85, 2.05, normal=(-1, 0, 0.35), region="sy_rune", rod=False)
    # ---- the banner with the tree on the back-left stub; ivy and vines; wisteria
    ml.banner(shell, "banner", (-HW - 0.95, EAVE + 0.3, -HD + 0.16), 0.82, 1.9, normal=(-0.35, 0, 1), region="sy_banner", rod=True,
              rod_region="sy_bark", knobs=None)
    for nm, pts in (("front", front), ("leg", leg), ("left", side_l), ("right", side_r), ("back", back), ("stub", stub)):
        ivy_on(det, "ivy_" + nm, pts, every=2, length=0.55, rng=rng)
    for k, (x, z) in enumerate(corners):
        for j, (dx, dz) in enumerate(((0.26, 0), (0, 0.26) if z > 0 else (0, -0.26))):
            ml.vine(det, "post_ivy_%d_%d" % (k, j), (x + dx * np.sign(x), EAVE - 0.1, z + dz), 1.3 + 0.5 * j, 0.36,
                    normal=(np.sign(x) if dx else 0, 0, np.sign(z) if dz else 0))
    Pf = pf.curve([T[0], (-1.6, EAVE + 0.75, fz), (0.3, EAVE + 1.55, fz), (1.75, EAVE + 2.3, fz)], 20)
    for k, i in enumerate((1, 2, 3, 4, 5)):
        wisteria(det, "wisteria_l_%d" % k, Pf[i] - UP * 0.1 + v3(0, 0, -0.05), length=1.15 + 0.3 * (k % 2), w=0.56)
    for k, (x, y) in enumerate(((2.55, EAVE + 0.9), (2.85, EAVE + 0.55), (3.1, EAVE + 0.2))):
        wisteria(det, "wisteria_r_%d" % k, (x, y, fz - 0.05), length=1.15 + 0.25 * (k % 2), w=0.54)
    # ---- lanterns: inside the front arch, on the front-right arm; the green crystal lantern on its staff
    ml.lantern(shell, "lamp_front", (-0.35, 2.75, HD - 0.1), size=0.42, metal="iron", chain_to=(-0.35, EAVE + 1.12, fz))
    ml.lantern(shell, "lamp_arm", (HW + 1.0, EAVE - 0.6, HD + 0.05), size=0.42, metal="iron", chain_to=(HW + 1.0, EAVE - 0.02, HD + 0.05))
    sx_, sz_ = -HW - 0.3, HD + 0.45
    beam(shell, "staff", (sx_, 0.0, sz_), (sx_, 2.45, sz_), 0.09, {"all": "sy_bark", "+1": "end_grain", "-1": "end_grain"})
    beam(det, "staff_hook", (sx_, 2.45, sz_), (sx_ + 0.3, 2.55, sz_), 0.06, "sy_bark")
    box(shell, "staff_foot", (sx_ - 0.14, 0.0, sz_ - 0.14), (sx_ + 0.14, 0.18, sz_ + 0.14), {"all": "stone", "+2": "stone_top"})
    collide((sx_ - 0.14, 0.0, sz_ - 0.14, sx_ + 0.14, 2.4, sz_ + 0.14))
    lc = v3(sx_ + 0.3, 2.2, sz_)
    beam(det, "green_lamp_chain", lc + UP * 0.12, lc + UP * 0.34, 0.03, "iron")
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(shell, "green_lamp_cage_%d" % k, lc, ry(a), (0.2, 0.26, 0.2), {"all": None, "+2": "iron", "-2": "iron"})
    pf.crystal(shell, "green_lamp", lc - UP * 0.12, 0.26, 0.12, "sy_crystal_g")
    # ---- inside: the back shelves (candles, books, potions, plants)
    sx0, sx1 = -HW + 0.75, HW - 0.75
    levels = ml.shelf_unit(shell, "shelves", sx0, sx1, SHELF_Z[0], SHELF_Z[1], levels=(0.6, 1.2, 1.8), h=2.3, back=True, uprights=4, detail=det)
    lv = sorted(levels, key=lambda s: s[2])
    zc = (SHELF_Z[0] + SHELF_Z[1]) / 2
    for j, (x0, x1, y, _, _) in enumerate(lv):
        n = 7
        for i in range(n):
            x = x0 + 0.2 + (x1 - x0 - 0.4) * i / (n - 1)
            kind = (i + j) % 4
            if kind == 0:
                pf.candle(det, "candle_%d_%d" % (j, i), (x, y, zc + 0.05), h=0.14 + 0.04 * (i % 2))
            elif kind == 1:
                ml.bottle(det, "pot_%d_%d" % (j, i), (x, y, zc), ("green", "cyan", "purple", "yellow")[(i + j) % 4], r=0.07, h=0.17, shape="round")
            elif kind == 2:
                for b in range(3):
                    box(det, "book_%d_%d_%d" % (j, i, b), (x - 0.12 + 0.08 * b, y, zc - 0.1), (x - 0.06 + 0.08 * b, y + 0.24 + 0.03 * b, zc + 0.1),
                        {"all": ("cloth_dark", "leather", "cloth_red")[b], "+2": "white"})
            else:
                ml.octo(det, "plantpot_%d_%d" % (j, i), (x, y, zc), 0.08, 0.1, "barrel")
                ml.crossed(det, "plant_%d_%d" % (j, i), (x, y + 0.2, zc), 0.26, 0.24, "herbs")
    # ---- the right counter: the big cyan crystal, potions, purple crystals (vanilla amethyst clusters)
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    yt = top[1]
    zc = (cz0 + cz1) / 2
    box(det, "crystal_base", (1.55, yt, zc - 0.18), (1.95, yt + 0.12, zc + 0.18), {"all": "plank", "+2": "sy_leaf"})
    pf.crystal(shell, "crystal_big", (1.75, yt + 0.12, zc), 0.7, 0.24, "sy_crystal")
    pf.crystal(det, "crystal_s0", (1.55, yt + 0.12, zc + 0.08), 0.35, 0.12, "sy_crystal", tilt=(0.25, 0.3))
    pf.crystal(det, "crystal_s1", (1.95, yt + 0.12, zc - 0.05), 0.3, 0.1, "sy_crystal", tilt=(-0.2, -0.35))
    for i, (x, col) in enumerate(((0.45, "purple"), (0.7, "green"), (2.25, "pink"), (2.45, "purple"))):
        ml.bottle(det, "cpot_%d" % i, (x, yt, zc + 0.05 * (i % 2)), col, r=0.08, h=0.18, shape="round" if i % 2 else "flask", glow=(col == "purple"))
    decor.block("minecraft:amethyst_cluster", 1.1, yt, zc, facing="front", scale=0.5, glow=True, solid=False, fallback="potion_purple",
                bounds=(0.1875, 0.8125, 0.0, 0.4375, 0.1875, 0.8125))
    ml.table_cloth(shell, "counter_cloth", cx0 + 0.05, cx1 - 0.05, cz0 + 0.05, cz1 + 0.04, yt, hang=0.3, region="cloth", edge="cloth_hang",
                   sides=("front",))
    # ---- the left table with jars and herbs, a storage vase (mod)
    ml.counter(shell, "table_l", -HW + 0.45, -HW + 1.05, -1.9, 0.2, h=0.9, detail=det)
    for i, z in enumerate((-1.6, -1.15, -0.7, -0.25)):
        ml.bottle(det, "ljar_%d" % i, (-HW + 0.75, 0.9, z), ("green", "yellow", "cyan", "green")[i], r=0.09, h=0.2, shape="tall")
        ml.hanging_bunch(det, "lherb_%d" % i, (-HW + 0.75, wall_top - 0.3, z + 0.2), kind="herbs_dry" if i % 2 else "herbs", length=0.45)
    decor.block("landsoficaria:green_storage_vase", -HW + 0.75, 0.0, 0.85, facing="front", scale=0.7, fallback="cloth")
    # ---- the dark blue rug with the golden rune
    ml.rug(shell, "rug", -1.6, 1.9, -0.6, 3.0, y=0.0, region="sy_rug")
    # ---- outside along the left side: the desk with books, a crate with a basket of moss and flowers
    dx0, dx1, dz0, dz1 = -HW - 1.35, -HW - 0.55, HD - 1.85, HD - 0.45
    dtop = ml.counter(shell, "desk", dx0, dx1, dz0, dz1, h=0.95, detail=det)
    decor.block("farmhouse_decorations:pile_of_books", (dx0 + dx1) / 2, 0.95, dz0 + 0.3, facing="neg_x", fallback="leather", solid=False)
    ml.plate(det, "open_book", ((dx0 + dx1) / 2, 0.97, (dz0 + dz1) / 2 + 0.15), 0.4, 0.3, "beige", normal=(0, 1, 0), up=(1, 0, 0), th=0.03)
    box(det, "open_book_cover", ((dx0 + dx1) / 2 - 0.16, 0.95, (dz0 + dz1) / 2 - 0.08), ((dx0 + dx1) / 2 + 0.16, 0.965, (dz0 + dz1) / 2 + 0.38), "leather")
    box(det, "green_book", ((dx0 + dx1) / 2 - 0.1, 0.95, dz1 - 0.35), ((dx0 + dx1) / 2 + 0.06, 1.35, dz1 - 0.05), {"all": "cloth_dark", "+3": "sy_leaf",
                                                                                                                      "-1": "sy_leaf"})
    decor.block("furnish:spruce_crate", -HW - 0.95, 0.0, -0.75, facing="neg_x", scale=0.85, alt="minecraft:barrel", fallback="crate")
    decor.block("farmersdelight:wooden_basket", -HW - 0.95, 0.85, -0.75, facing="front", scale=0.55, fallback="basket", solid=False)
    ml.crossed(det, "basket_moss", (-HW - 0.95, 1.18, -0.75), 0.42, 0.28, "ivy")
    ml.crossed(det, "basket_flowers", (-HW - 0.85, 1.25, -0.65), 0.3, 0.3, "sy_wisteria")
    return root


def item_icon(path):
    """16x16: a green-and-cream pointed tent under a brown branch arch, a purple wisteria cluster, a gold finial."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    for y in range(2, 11):
        half = 0.6 + (y - 2) * 0.85
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                stripe = int((dx / max(half, 0.5)) * 2 + 2) % 2
                p[x, y] = (GREEN if stripe == 0 else CREAM) + (255,)
    p[7, 0] = p[8, 0] = p[7, 1] = p[8, 1] = GOLDF + (255,)
    bark = (110, 74, 44)
    for x in range(1, 15):
        y = 9 - int(2.2 * math.sin(math.pi * (x - 1) / 13))
        p[x, y] = bark + (255,)
    for y in range(9, 16):
        p[1, y] = p[2, y] = bark + (255,)
        p[13, y] = p[14, y] = bark + (255,)
    for y in range(10, 16):
        for x in range(3, 13):
            p[x, y] = (34, 30, 22, 255)
    for x in range(4, 12):
        p[x, 15] = (40, 52, 102, 255)
    for (x, y) in ((4, 9), (4, 10), (5, 10), (4, 11), (11, 9), (11, 10)):
        p[x, y] = (170, 120, 214, 255)
    p[9, 12] = p[9, 13] = (120, 240, 230, 255)
    im.save(path)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="green")
    add_regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)


if __name__ == "__main__":
    main()
