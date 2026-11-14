#!/usr/bin/env python3
"""porte_marchande (1.31.0): merchant double door, 4 high x 2 wide. References: ref3 bottom 1st (wooden frame with
a stepped plank arch, lanterns on the posts, small lit arched windows, wooden X battens, ring handles, stone
plinths), ref1 bottom 4th (lit gridded windows in the upper part, brass pull handles), ref3 bottom 4th (brass bands
and fittings, lanterns).

    python3 tools/doors/generate_porte_marchande.py [--preview]
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_medium as dm  # noqa: E402
from doorlib_medium import rgb, shade, mix  # noqa: E402

WOOD = rgb("87481f")
WOOD_D = rgb("4a2810")
BACK = rgb("85491f")
FRAME = rgb("a8622c")
FRAME_L = rgb("c27b3c")
BATTEN = rgb("bf7a3c")
BRASS = rgb("c99a3c")
BRASS_L = rgb("f2d27a")
BRASS_D = rgb("7a571b")
STONE = rgb("8e8c88")
MUNTIN = rgb("5a3416")

SPRING, RISE = 50.0, 4.0       # segmental arch of the leaves: 50 at the posts, 54 in the middle


def leaf_top(x):
    t = min(1.0, abs(x) / 12.0)
    return SPRING + RISE * (1 - t * t)

ICON = [
    "LLLLLLLLLLLLLLLL",
    "lLLLLLBBBLLLLLLl",
    ".PPddddBddddPPP.",
    ".PPdWWWWWWWWdPP.",
    "yPPWBBBWWBBBWPPy",
    "YPPWBYYWWYYBWPPY",
    "YPPWBYYWWYYBWPPY",
    "yPPWBBBWWBBBWPPy",
    ".PPWWWWWWWWWWPP.",
    ".PPWWWRWWRWWWPP.",
    ".PPBBBBBBBBBBPP.",
    ".PPWXWWXXWWXWPP.",
    ".PPWWXXWWXXWWPP.",
    ".PPWXWWXXWWXWPP.",
    ".ssBBBBBBBBBBss.",
    ".ssBBBBBBBBBBss.",
]
ICON_PAL = {"L": rgb("c27b3c"), "l": rgb("8e5124"), "B": rgb("c99a3c"), "P": rgb("a8622c"), "d": rgb("5e5650"), "W": rgb("87481f"), "Y": rgb("ffc35a"), "y": rgb("7a571b"), "R": rgb("f2d27a"), "X": rgb("bf7a3c"), "s": rgb("8e8c88")}


def build():
    d = dm.Door("porte_marchande", post=4, top=int(SPRING), seed=41)
    F, B = d.F, d.B
    d.material("wood_side", dm.tile_wood(shade(WOOD, 0.85)))
    d.material("frame_side", dm.tile_wood(shade(FRAME, 0.95)))
    d.material("brass_side", lambda c: [c.put(x, y, mix(BRASS_D, BRASS_L, 0.5 + 0.5 * math.sin(x * 0.9 + y * 0.3)))
                                        for x in range(c.w) for y in range(c.h)], 16, 16)
    d.material("stone_side", dm.tile_stone(STONE), 32, 32)
    d.material("batten3", lambda c: c.planks_h(0, 0, c.w, c.h, [c.h], BATTEN, joints=0), 64, 3)
    d.material("muntin_side", dm.tile_flat(MUNTIN, 5), 16, 16)
    d.material("glow_side", lambda c: c.glow_pane(0, 0, c.w, c.h), 16, 16)
    d.material("lantern", dm.tile_lantern, 16, 16)
    d.material("brass", lambda c: [c.put(x, y, mix(BRASS_D, BRASS_L, 0.5 + 0.5 * math.sin(x * 0.9 + y * 0.4)))
                                   for x in range(c.w) for y in range(c.h)], 16, 16)
    d.material("gold", dm.tile_gold, 16, 16)
    d.material("chain_side", lambda c: [c.put(x, y, mix(BRASS_D, BRASS, 0.5 + 0.5 * math.sin(x * 1.3 + y)))
                                        for x in range(c.w) for y in range(c.h)], 16, 16)

    # opening mask (both leaves) and lintel mask
    open_m = np.zeros((64, 32), bool)
    for j in range(64):
        Y = 63 - j
        for i in range(32):
            X = i - 16
            if abs(X + 0.5) < 12 and Y + 0.5 < leaf_top(X + 0.5):
                open_m[j, i] = True

    # ------------------------------------------------------------ pictures: frame
    for P, k in ((F, 1.0), (B, 0.85)):
        for x0 in (-16, 12):
            P.planks_v(x0, 6, x0 + 4, 58, [2, 2], shade(FRAME, k), knots=0.08, joints=0.4)
            P.stone_wall(dm.label_rows(["AAAA", "AAAA", "####", "BB#C", "BB#C", "BB#C"]), x0, 0, shade(STONE, k))
            P.metal(x0, 6, x0 + 4, 7, shade(BRASS, k), noise=3)
            P.metal(x0, 36, x0 + 4, 38, shade(BRASS, k), noise=3)
            P.rivet(x0 + 1, 37, light=BRASS_L)
            P.rivet(x0 + 2, 37, light=BRASS_L)
        # lintel: horizontal planks above the arch, stepped like ref3
        P.planks_h(-16, 58, 16, 64, [3, 3], shade(FRAME_L, k), joints=0.5)
        for x in range(-16, 16):
            P.put(x, 58, shade(FRAME, 0.5 * k))
        # dark brick infill of the arch (ref3 bottom 1st), between the leaves and the lintel planks
        lab = -np.ones((8, 24), int)
        for jj in range(8):
            Y = 57 - jj
            for ii in range(24):
                X = ii - 12
                if open_m[63 - Y, X + 16]:
                    continue
                course = (Y - 50) // 2
                off = 2 if course % 2 else 0
                if (Y - 50) % 2 == 1 and False:
                    lab[jj, ii] = 0
                elif (X + 12 + off) % 5 == 4:
                    lab[jj, ii] = 0
                else:
                    lab[jj, ii] = 1 + course * 10 + (X + 12 + off) // 5
        P.stone_wall(lab, -12, 50, shade(rgb("5e5650"), k), seed_k=0.03)
        for X in range(-12, 12):
            for Y in range(50, 58):
                if open_m[63 - Y, X + 16]:
                    continue
                if (Y - 50) % 2 == 0 and lab[57 - Y, X + 12] > 0:
                    P.scale_px(X, Y, 0.8)
        # brass-framed keystone plaque
        P.metal(-3, 55, 3, 63, shade(BRASS, k), noise=3)
        P.metal(-2, 56, 2, 62, shade(FRAME, 1.05 * k), noise=4)
        P.rivet(-1, 59, light=BRASS_L)
        P.rivet(0, 59, light=BRASS_L)
        for x in (-15, 14):
            P.rivet(x, 61, light=BRASS_L)

    # ------------------------------------------------------------ pictures: leaves
    for x0, s in ((-12, -1), (0, 1)):
        for P, base, dark in ((F, WOOD, WOOD_D), (B, BACK, shade(BACK, 0.45))):
            sub = P.a.copy()
            P.planks_v(x0, 0, x0 + 12, 55, [3, 3, 3, 3], base, dark, knots=0.05, joints=0.2)
            # keep the lintel pixels above the arch
            for j in range(64):
                for i in range(x0 + 16, x0 + 28):
                    if not open_m[j, i]:
                        P.a[j, i] = sub[j, i]
        # stiles (lighter boards) and wooden rails
        F.planks_v(x0, 0, x0 + 2, 55, [2], BATTEN, knots=0)
        F.planks_v(x0 + 10, 0, x0 + 12, 55, [2], BATTEN, knots=0)
        F.planks_h(x0 + 2, 3, x0 + 10, 5, [2], BATTEN, joints=0)
        F.planks_h(x0 + 2, 33, x0 + 10, 35, [2], BATTEN, joints=0)
        # brass: kick plate, middle band, short hinge straps
        F.metal(x0, 0, x0 + 12, 3, BRASS, noise=4)
        F.strap_h(x0, x0 + 12, 21, 2, BRASS, light=BRASS_L, every=4)
        for x in range(x0 + 1, x0 + 12, 4):
            F.rivet(x, 1, light=BRASS_L)
        for y in (12, 29):
            for X in range(5):
                xx = x0 + X if s < 0 else x0 + 11 - X
                F.put(xx, y, BRASS)
                F.put(xx, y + 1, shade(BRASS, 0.85))
            F.rivet(x0 + 1 if s < 0 else x0 + 10, y + 1, light=BRASS_L)
        # the window: lit, 3 x 3 panes (8 x 11 px), brass rim (both faces lit)
        for P in (F, B):
            P.glow_pane(x0 + 2, 37, x0 + 10, 48)
            for y in range(37, 48):
                P.put(x0 + 4, y, MUNTIN)
                P.put(x0 + 7, y, MUNTIN)
            for x in range(x0 + 2, x0 + 10):
                P.put(x, 40, MUNTIN)
                P.put(x, 44, MUNTIN)
        for X in range(x0 + 1, x0 + 11):
            F.put(X, 36, BRASS)
            F.put(X, 48, BRASS_L)
        for Y in range(36, 49):
            F.put(x0 + 1, Y, BRASS)
            F.put(x0 + 10, Y, shade(BRASS, 0.8))
        # brass keyhole plate on the left leaf
        if s < 0:
            F.metal(-4, 24, -2, 27, BRASS, noise=3)
            F.put(-3, 25, rgb("1a1208"))

    # ------------------------------------------------------------ frame cubes
    fr = d.frame
    for s in (-1, 1):
        xo, xs, xi = 16 * s, 14.5 * s, 12 * s
        d.box(fr, "post_%d" % s, xo, xs, 6, 58, -8, 4, side="frame_side")
        d.box(fr, "post_stop_%d" % s, xs, xi, 6, 55, 2.75, 4, side="frame_side")
        d.box(fr, "post_head_%d" % s, xs, xi, 55, 58, -8, 4, side="frame_side")
        d.box(fr, "plinth_%d" % s, xo, xs, 0, 6, -8, 5.5, side="stone_side")
        d.box(fr, "plinth_stop_%d" % s, xs, xi, 0, 6, 2.75, 5.5, side="stone_side")
        d.box(fr, "band_%d" % s, xo, xi, 36, 38, 4, 4.75, side="brass_side", back=None)
        # lantern hanging from a brass bracket in front of the post
        d.box(fr, "arm_%d" % s, 14 * s - 0.75, 14 * s + 0.75, 49.5, 50.5, 4, 7, front="brass_side", side="brass_side")
        ytop = d.lantern(fr, "lantern_%d" % (0 if s < 0 else 1), 14 * s, 43.6, 6.15, size=3.4, metal="brass")
        d.chain(fr, "chain_%d" % (0 if s < 0 else 1), 14 * s, ytop, 50, 6.15)
    # lintel: the stepped plank arch above the leaves, the projecting cap, the keystone plaque
    lint = ~open_m.copy()
    lint[:, :4] = False
    lint[:, 28:] = False
    lint[:6, :] = False                       # Y 58..64 is the cap
    lint[64 - 50:, :] = False                 # below the springing: posts
    low = lint.copy()
    low[:64 - 55, :] = False                  # under Y 55 the turned leaves pass behind: front only
    lint[64 - 55:, :] = False
    d.mask_boxes(fr, "lintel_low", low, -16, 0, 2.75, 4.5, side="frame_side")
    d.mask_boxes(fr, "lintel", lint, -16, 0, -6, 4.5, side="frame_side")
    # a 0.5 px lip in front of the top of the leaves (no grazing line of sight between the steps)
    tops = [64 - np.nonzero(open_m[:, i + 4])[0][0] for i in range(24)]
    for i in range(24):
        low_ = min(tops[max(0, i - 1)], tops[i], tops[min(23, i + 1)])     # down to the lower neighbour's top
        d.box(fr, "lip_%d" % i, i - 12, i - 11, low_ - 0.5, tops[i], 2.75, 3.5, front="front", back="back", side="frame_side")
    d.box(fr, "cap", -16, 16, 58, 64, -7, 7.5, side="frame_side")
    d.box(fr, "plaque", -3, 3, 58, 63, 7.5, 8, front="front", back=None, side="brass_side")
    d.box(fr, "plaque_low", -3, 3, 55, 58, 4.5, 8, front="front", back=None, side="brass_side")
    for s in (-1, 1):
        x = 15 if s > 0 else -15
        d.box(fr, "stud_%d" % s, min(x, x - s), max(x, x - s), 60.5, 61.5, 7.5, 8, front="brass_side", back=None, side="brass_side")

    # ------------------------------------------------------------ leaves
    for leaf, x0, s in ((d.leaf_l, -12, -1), (d.leaf_r, 0, 1)):
        m = open_m[:, x0 + 16:x0 + 28].copy()
        win = np.zeros_like(m)
        win[64 - 48:64 - 37, 2:10] = True
        core = m & ~win
        d.mask_boxes(leaf, "core", core, x0, 0, -1, 1, side="wood_side")
        d.box(leaf, "glow_window", x0 + 2, x0 + 10, 37, 48, -1, 1, side="glow_side")
        for k, x in enumerate((x0 + 4, x0 + 7)):
            d.box(leaf, "muntin_v%d" % k, x, x + 1, 37, 48, 1, 2, back=None, side="muntin_side")
            d.box(leaf, "muntin_vb%d" % k, x, x + 1, 37, 48, -2, -1, front=None, side="muntin_side")
        for k, y in enumerate((40, 44)):
            d.box(leaf, "muntin_h%d" % k, x0 + 2, x0 + 10, y, y + 1, 1, 2.25, back=None, side="muntin_side")
            d.box(leaf, "muntin_hb%d" % k, x0 + 2, x0 + 10, y, y + 1, -2.25, -1, front=None, side="muntin_side")
        d.box(leaf, "rim_b", x0 + 1.25, x0 + 10.75, 36, 37, 1, 2.75, back=None, side="brass_side")
        d.box(leaf, "rim_t", x0 + 1.25, x0 + 10.75, 48, 49, 1, 2.75, back=None, side="brass_side")
        d.box(leaf, "rim_l", x0 + 1.25, x0 + 2.25, 37, 48, 1, 2.75, back=None, side="brass_side")
        d.box(leaf, "rim_r", x0 + 9.75, x0 + 10.75, 37, 48, 1, 2.75, back=None, side="brass_side")
        # arched top rail: the top 2 px of the leaf between the stiles (lighter batten, 1.5 px relief)
        band = np.zeros_like(m)
        for i in range(2, 10):
            col = np.nonzero(m[:, i])[0]
            band[col[0]:col[0] + 2, i] = True
            for j in range(col[0], col[0] + 2):
                F.put(x0 + i, 63 - j, shade(BATTEN, 1.05 if j == col[0] else 0.85) + F.rng.normal(0, 4))
        d.mask_boxes(leaf, "arch_rail", band, x0, 0, 1, 2.5, back=None, side="wood_side")
        # stiles: follow the arch on the top
        for k, (a, b) in enumerate(((x0, x0 + 2), (x0 + 10, x0 + 12))):
            top = int(math.floor(min(leaf_top(a + 0.5), leaf_top(b - 0.5))))
            d.box(leaf, "stile_%d" % k, a, b, 3, top, 1, 2.5, back=None, side="wood_side")
        d.box(leaf, "rail_b", x0 + 2, x0 + 10, 3, 5, 1, 2.5, back=None, side="wood_side")
        d.box(leaf, "rail_t", x0 + 2, x0 + 10, 33, 35, 1, 2.5, back=None, side="wood_side")
        d.box(leaf, "kick", x0, x0 + 12, 0, 3, 1, 2.5, back=None, side="brass_side")
        d.box(leaf, "band", x0 + (0.25 if s < 0 else 0.75), x0 + (11.25 if s < 0 else 11.75), 21, 23, 1, 2.75, back=None,
              side="brass_side")
        # wooden X battens of the lower panel
        d.strap(leaf, "x_a", (x0 + 2.8, 5.8), (x0 + 9.2, 20.2), 2, 1, 2, "batten3")
        d.strap(leaf, "x_b", (x0 + 9.2, 5.8), (x0 + 2.8, 20.2), 2, 1, 2.25, "batten3")
        # brass hinge straps and barrels
        px = -12 if s < 0 else 12
        for k, y in enumerate((12, 29.5)):
            xa, xb = (x0 + 0.25, x0 + 5) if s < 0 else (x0 + 7, x0 + 11.75)
            d.box(leaf, "hinge_strap_%d" % k, xa, xb, y, y + 2, 1, 3, back=None, side="brass_side")
            d.knuckle(leaf, "knuckle_%d" % k, px, y - 1, y + 3, "brass_side")
        # brass ring handle near the seam (handle_0 / handle_1)
        hx = -5 if s < 0 else 4
        dm.ring_handle(d, leaf, "ring", hx, 29, "brass_side", BRASS, BRASS_L, Z=2.5, size=5, handle="handle_%d" % (0 if s < 0 else 1))
        # back: battens and a pull bar
        for k, y in enumerate((4, 20, 33)):
            d.box(leaf, "batten_%d" % k, x0 + 0.5, x0 + 11.5, y, y + 3, -2, -1, front=None, back="batten3", side="wood_side")
        d.box(leaf, "pull", (x0 + 8.5) if s < 0 else (x0 + 2.5), (x0 + 9.5) if s < 0 else (x0 + 3.5), 25, 31, -2.75, -1,
              front="brass_side", back="brass_side", side="brass_side")
    d.material("seam_dark", dm.tile_flat(shade(WOOD_D, 0.7), 4), 16, 16)
    d.finalize(top_gap=False, seam_top=54, cover_side="wood_side", seam_mat="seam_dark")
    d.icon_map = (ICON, ICON_PAL)
    return d


REFS = [(dm.REF_DIR + "/ref3.png", (10, 430, 275, 870)), (dm.REF_DIR + "/ref1.png", (690, 565, 1000, 880)),
        (dm.REF_DIR + "/ref3.png", (955, 425, 1325, 870))]

if __name__ == "__main__":
    d = build()
    d.export()
    for line in d.bones():
        print(line)
    if "--preview" in sys.argv:
        d.preview(dm.SCRATCH + "/doors_out2/medium_porte_marchande.png", refs=REFS)
