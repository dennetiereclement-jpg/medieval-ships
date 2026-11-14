#!/usr/bin/env python3
"""porte_grange (1.31.0): barn double door, 4 high x 2 wide. References: ref1 top row 3rd (plank lintel, posts,
lanterns on chains, iron-framed leaves with big X braces, ring handles), ref4 "4x2" 3rd, ref2 top row 3rd.

    python3 tools/doors/generate_porte_grange.py [--preview]

Writes models/entity/porte_grange.bbmodel, blockbench/porte_grange.bbmodel, textures/entity/porte_grange.png,
textures/item/porte_grange.png (see tools/doors/doorlib_medium.py for the units and the projection).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_medium as dm  # noqa: E402
from doorlib_medium import rgb, shade  # noqa: E402

WOOD = rgb("9a5b2c")        # leaf planks
WOOD_D = rgb("4e2a12")
FRAME = rgb("8c5428")       # posts, lintel
FRAME_L = rgb("b47038")
PLINTH = rgb("a8703c")
IRON = rgb("55555c")
IRON_L = rgb("a4a4aa")
BACK = rgb("7e4a24")        # back face planks (in the shade)

LEAF_TOP = 50

ICON = [
    "LLLLLLLLLLLLLLLL",
    "lLLLlLLLLLlLLLLl",
    ".PPhhhhhhhhhhPP.",
    "cPPIIIIIIIIIIPPc",
    "YPPIIWWIIWWIIPPY",
    "YPPIWIWIIWIWIPPY",
    "yPPIWWIIIIWWIPPy",
    ".PPIWWWIIWWWIPP.",
    ".PPIIIIRRIIIIPP.",
    ".PPIWWRWWRWWIPP.",
    ".PPIWWIRRIWWIPP.",
    ".PPIWIWIIWIWIPP.",
    ".PPIIWWIIWWIIPP.",
    ".PPIIWWIIWWIIPP.",
    ".ppIIIIIIIIIIpp.",
    ".ppIIIIIIIIIIpp.",
]
ICON_PAL = {"L": rgb("b47038"), "l": rgb("7a4520"), "P": rgb("8c5428"), "p": rgb("a8703c"), "h": rgb("5e3818"), "I": rgb("62626a"), "W": rgb("9a5b2c"), "R": rgb("2a2a2e"), "Y": rgb("ffc35a"), "y": rgb("3a3a3e"), "c": rgb("3a3a3e")}


def build():
    d = dm.Door("porte_grange", post=4, top=LEAF_TOP, seed=11)
    F, B = d.F, d.B
    d.material("wood_side", dm.tile_wood(shade(WOOD, 0.85)))
    d.material("frame_side", dm.tile_wood(shade(FRAME, 0.9)))
    d.material("iron_side", dm.tile_metal(IRON), 32, 32)
    d.material("ring_side", dm.tile_metal(shade(IRON, 0.62)), 16, 16)
    d.material("strap2", lambda c: c.strap_h(0, c.w, 0, 2, IRON, every=6, light=IRON_L), 64, 2)
    d.material("batten", lambda c: c.planks_h(0, 0, c.w, c.h, [c.h], shade(BACK, 1.05), joints=0), 64, 3)
    d.material("lantern", dm.tile_lantern, 16, 16)
    d.material("iron", dm.tile_metal(shade(IRON, 0.8)), 16, 16)
    d.material("gold", dm.tile_gold, 16, 16)
    d.material("chain_side", dm.tile_metal(shade(IRON, 0.75)), 16, 16)

    # ------------------------------------------------------------ pictures: frame
    for P, k in ((F, 1.0), (B, 0.85)):
        # posts: vertical planks, a lighter plinth block at the bottom
        for x0 in (-16, 12):
            P.planks_v(x0, 6, x0 + 4, 54, [2, 2], shade(FRAME, k), knots=0.08, joints=0.5)
            P.planks_h(x0, 0, x0 + 4, 6, [3, 3], shade(PLINTH, k), joints=0)
        # header beam above the leaves, lintel planks (top row of blocks, end brackets + centre block)
        P.planks_h(-12, 50, 12, 54, [2, 2], shade(FRAME, 0.8 * k), joints=0.8)
        P.planks_h(-16, 58, 16, 64, [3, 3], shade(FRAME_L, k), joints=0)
        for jx in (-8, 1, 9):
            for y in range(58, 64):
                P.put(jx, y, shade(FRAME, 0.45 * k))
        P.planks_h(-16, 54, -11, 58, [2, 2], shade(FRAME, 1.05 * k), joints=0)
        P.planks_h(11, 54, 16, 58, [2, 2], shade(FRAME, 1.05 * k), joints=0)
        P.planks_h(-3, 54, 3, 58, [2, 2], shade(FRAME_L, 0.95 * k), joints=0)
        P.planks_h(-11, 54, -3, 58, [4], shade(FRAME, 0.62 * k), joints=0)
        P.planks_h(3, 54, 11, 58, [4], shade(FRAME, 0.62 * k), joints=0)

    # ------------------------------------------------------------ pictures: leaves
    for x0 in (-12, 0):
        F.planks_v(x0, 0, x0 + 12, LEAF_TOP, [3, 3, 3, 3], WOOD, WOOD_D, knots=0.06, joints=0.25)
        B.planks_v(x0, 0, x0 + 12, LEAF_TOP, [3, 3, 3, 3], BACK, shade(BACK, 0.5), knots=0.06, joints=0.25)
        # iron frame of the leaf: border straps + middle rail (front)
        F.strap_v(x0, 0, LEAF_TOP, 2, IRON, light=IRON_L)
        F.strap_v(x0 + 10, 0, LEAF_TOP, 2, IRON, light=IRON_L)
        F.strap_h(x0 + 2, x0 + 10, 0, 2, IRON, light=IRON_L)
        F.strap_h(x0 + 2, x0 + 10, LEAF_TOP - 2, 2, IRON, light=IRON_L)
        F.strap_h(x0 + 2, x0 + 10, 23, 2, IRON, light=IRON_L)
        # seam shadow
    for y in range(0, LEAF_TOP):
        F.put(-1, y, shade(F.get(-1, y), 0.7))
        F.put(0, y, shade(F.get(0, y), 0.8))

    # ------------------------------------------------------------ frame cubes
    # posts: full depth only outside X = +-14.5 (the rebate behind the 2.5 px door stop takes the turned leaves)
    fr = d.frame
    for s in (-1, 1):
        xo, xs, xi = 16 * s, 14.5 * s, 12 * s
        d.box(fr, "post_%d" % s, xo, xs, 6, 54, -8, 4, side="frame_side")
        d.box(fr, "post_stop_%d" % s, xs, xi, 6, 50, 2.75, 4, side="frame_side")
        d.box(fr, "plinth_%d" % s, xo, xs, 0, 6, -8, 5, side="frame_side")
        d.box(fr, "plinth_stop_%d" % s, xs, xi, 0, 6, 2.75, 5, side="frame_side")
        d.box(fr, "bracket_%d" % s, xo, 11 * s, 54, 58, -6, 8, side="frame_side")
    d.box(fr, "header", -14.5, 14.5, 50, 54, -4, 4, side="frame_side")
    d.head_stop(2.75, 4, "frame_side", Y0=49)
    d.box(fr, "lintel_back", -11, 11, 54, 58, -5, 5, side="frame_side")
    d.box(fr, "lintel_mid", -3, 3, 54, 58, 5, 7, side="frame_side", back=None)
    for k, (a, b, z1) in enumerate(((-16, -8, 8), (-8, 1, 7.5), (1, 9, 8), (9, 16, 7.5))):
        d.box(fr, "lintel_%d" % k, a, b, 58, 64, -6, z1, side="frame_side")
    # lanterns on chains under the end brackets, in front of the posts (clear of the posts by 0.5 px)
    for s in (-1, 1):
        k = 0 if s < 0 else 1
        ytop = d.lantern(fr, "lantern_%d" % k, 13.6 * s, 44.2, 6.15, size=3.4, metal="iron")
        d.chain(fr, "chain_%d" % k, 13.6 * s, ytop, 54.5, 6.15)

    # ------------------------------------------------------------ leaves
    for leaf, x0, s in ((d.leaf_l, -12, -1), (d.leaf_r, 0, 1)):
        d.box(leaf, "core", x0, x0 + 12, 0, LEAF_TOP, -1, 1, side="wood_side")
        # front iron frame (1.5 px relief) and X braces (1 px, under the frame where they cross it)
        d.box(leaf, "strap_o", x0, x0 + 2, 0, LEAF_TOP, 1, 2.5, side="iron_side", back=None)
        d.box(leaf, "strap_i", x0 + 10, x0 + 12, 0, LEAF_TOP, 1, 2.5, side="iron_side", back=None)
        d.box(leaf, "strap_b", x0 + 2, x0 + 10, 0, 2, 1, 2.5, side="iron_side", back=None)
        d.box(leaf, "strap_t", x0 + 2, x0 + 10, LEAF_TOP - 2, LEAF_TOP, 1, 2.5, side="iron_side", back=None)
        d.box(leaf, "strap_m", x0 + 2, x0 + 10, 23, 25, 1, 2.5, side="iron_side", back=None)
        xo, xi = (x0 + 2.6, x0 + 9.4) if s < 0 else (x0 + 9.4, x0 + 2.6)
        d.strap(leaf, "brace_0", (xo, LEAF_TOP - 2.6), (xi, 25.6), 2, 1, 2, "strap2")
        d.strap(leaf, "brace_1", (xi, 22.4), (xo, 2.6), 2, 1, 2, "strap2")
        # forged hinge straps from the hinge edge, on the frame of the leaf
        for k, y in enumerate((5, 21.5, 42)):
            xa, xb = (x0 + 0.25, x0 + 6) if s < 0 else (x0 + 6, x0 + 11.75)
            d.box(leaf, "hinge_strap_%d" % k, xa, xb, y, y + 2.5, 1, 3, side="iron_side", back=None)
        # ring handle near the seam, on the middle rail (its own bone: handle_0 / handle_1)
        hx = -5 if s < 0 else 4
        dm.ring_handle(d, leaf, "ring", hx, 24, "ring_side", shade(IRON, 0.7), shade(IRON, 1.25), Z=2.5, size=5,
                       handle="handle_%d" % (0 if s < 0 else 1))
        # hinge barrels round the pivot
        px = -12 if s < 0 else 12
        for k, y in enumerate((5, 21.5, 42)):
            d.knuckle(leaf, "hinge_%d" % k, px, y - 0.5, y + 3, "iron_side")
        # back: horizontal battens and a diagonal wooden brace in each half ("Z")
        for k, y in enumerate((3, 22, 44)):
            d.box(leaf, "batten_%d" % k, x0 + 0.5, x0 + 11.5, y, y + 3, -2.25, -1, front=None, back="batten", side="wood_side")
        if s < 0:
            d.strap(leaf, "zbrace_0", (x0 + 2, 6), (x0 + 10, 22), 2.5, -2, -1, "batten")
            d.strap(leaf, "zbrace_1", (x0 + 2, 25), (x0 + 10, 44), 2.5, -2, -1, "batten")
        else:
            d.strap(leaf, "zbrace_0", (x0 + 10, 6), (x0 + 2, 22), 2.5, -2, -1, "batten")
            d.strap(leaf, "zbrace_1", (x0 + 10, 25), (x0 + 2, 44), 2.5, -2, -1, "batten")
        # back pull handle (far enough from the hinge to clear the post when the leaf is open)
        d.box(leaf, "pull", (x0 + 8.5) if s < 0 else (x0 + 2.5), (x0 + 9.5) if s < 0 else (x0 + 3.5), 28, 34, -2.75, -2,
              front="iron_side", back="iron_side", side="iron_side")
    d.material("seam_dark", dm.tile_flat(shade(WOOD_D, 0.7), 4), 16, 16)
    d.finalize(top_gap=True, cover_side="wood_side", seam_mat="seam_dark")
    d.icon_map = (ICON, ICON_PAL)
    return d


REFS = [(dm.REF_DIR + "/ref1.png", (365, 115, 675, 440)), (dm.REF_DIR + "/ref4.png", (1225, 50, 1630, 375)),
        (dm.REF_DIR + "/ref2.png", (578, 35, 890, 410))]

if __name__ == "__main__":
    d = build()
    d.export()
    for line in d.bones():
        print(line)
    if "--preview" in sys.argv:
        d.preview(dm.SCRATCH + "/doors_out2/medium_porte_grange.png", refs=REFS)
