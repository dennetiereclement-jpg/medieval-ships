#!/usr/bin/env python3
"""porte_industrielle (1.31.0): industrial double door, 4 high x 2 wide. References: ref4 "4x2" 2nd (copper
pipes round the frame, gears at the top), ref2 top row 4th (riveted metal, lit barred windows, lit vent in the
lintel), ref5 row 2 4th (lit grilles, X-braced lower panels, hazard stripes, copper tanks and pipes), ref3 bottom 2nd
(dark metal leaves, meshing gears in the middle).

    python3 tools/doors/generate_porte_industrielle.py [--preview]

Animated bones: gear_a_0 / gear_b_1 (lintel), gear_a_2 (leaf_l) / gear_b_3 (leaf_r) meshing across the seam,
bolt_0 (leaf_l) / bolt_1 (leaf_r) sliding latch bars, piston_0 / piston_1 (rods of the copper tanks of the posts).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_medium as dm  # noqa: E402
from doorlib_medium import rgb, shade, mix  # noqa: E402

STEEL = rgb("4c4c52")
STEEL_D = rgb("333337")
STEEL_L = rgb("6c6c73")
RIVET = rgb("a2a2a8")
FRAME = rgb("5a5a60")
COPPER = rgb("b5652f")
COPPER_L = rgb("e39a57")
COPPER_D = rgb("74391a")
BRASS = rgb("d29a38")
YELLOW = rgb("e0b024")
BLACK = rgb("26262a")
LEAF_TOP = 52

ICON = [
    "CCCCCCCCCCCCCCCC",
    "FFbbFFGGFFFFbbFF",
    "FCFFFFGGFFFFFCFF",
    "FCFTTTTTTTTTTCFF",
    "FCFTYYTTTTYYTCFF",
    "FCFTYYTTTTYYTCFF",
    "FCFTTTTTTTTTTCFF",
    "FCFTTbbTTbbTTCFF",
    "FCFTbBBbbBBbTCFF",
    "FCFTTbbTTbbTTCFF",
    "FCFTTTTTTTTTTCFF",
    "FCFTXTXTTXTXTCFF",
    "FCFTTXTTTTXTTCFF",
    "CCCTXTXTTXTXTCCC",
    "CCCKkKkKKkKkKCCC",
    "CCCkKkKkkKkKkCCC",
]
ICON_PAL = {"C": rgb("b5652f"), "F": rgb("5a5a60"), "b": rgb("8a6a2a"), "B": rgb("d29a38"), "G": rgb("ffc35a"), "T": rgb("4c4c52"), "Y": rgb("ffbf55"), "X": rgb("8a8a92"), "K": rgb("e0b024"), "k": rgb("26262a")}


def build():
    d = dm.Door("porte_industrielle", post=4, top=LEAF_TOP, seed=31)
    F, B = d.F, d.B
    d.picture("pic_gears")
    d.material("steel_side", dm.tile_metal(shade(STEEL, 0.9)), 32, 32)
    d.material("frame_side", dm.tile_metal(FRAME), 32, 32)
    d.material("copper_side", lambda c: [c.put(x, y, mix(COPPER_D, COPPER_L, 0.5 + 0.5 * np.sin(x * 0.8)) + c.rng.normal(0, 4))
                                         for x in range(c.w) for y in range(c.h)], 16, 16)
    d.material("gear_side", dm.tile_flat(shade(BRASS, 0.8)), 16, 16)
    d.material("strap2", lambda c: c.strap_h(0, c.w, 0, 2, STEEL_L, every=6, light=RIVET), 64, 2)
    d.material("rod_side", dm.tile_flat(rgb("b8b8be"), 5), 16, 16)
    d.material("glow_side", lambda c: c.glow_pane(0, 0, c.w, c.h), 16, 16)

    # ------------------------------------------------------------ pictures: frame
    for P, k in ((F, 1.0), (B, 0.85)):
        for x0 in (-16, 12):
            P.metal(x0, 0, x0 + 4, 52, shade(FRAME, k), noise=5)
            for y in range(3, 52, 6):
                P.rivet(x0 + 1, y, light=RIVET)
                P.rivet(x0 + 3, y + 3, light=RIVET)
            # square bosses (ref2)
            for y in (4, 26, 46):
                P.metal(x0, y, x0 + 4, y + 4, shade(FRAME, 1.15 * k), noise=3)
                P.rivet(x0 + 2, y + 2, light=RIVET)
        P.metal(-16, 52, 16, 64, shade(FRAME, 0.95 * k), noise=5)
        for x in range(-15, 16, 3):
            P.rivet(x, 53, light=RIVET)
        P.strap_h(-16, 16, 60, 2, shade(STEEL_L, k), light=RIVET)
        # lit vent in the middle of the lintel
        P.glow_pane(-4, 55, 4, 61)
        for x in (-2, 0, 2):
            for y in range(55, 61):
                P.put(x, y, STEEL_D)
        P.metal(-5, 54, 5, 55, shade(STEEL_L, k), noise=3)
        P.metal(-5, 61, 5, 62, shade(STEEL_L, k), noise=3)
    # copper: tanks at the bottom of the posts, pipes up the posts and over the lintel (front only)
    for s in (-1, 1):
        xa = -16 if s < 0 else 12
        for x in range(xa, xa + 4):
            for y in range(0, 11):
                t = (x - xa) / 3
                c = mix(COPPER_L, COPPER_D, t) if y not in (2, 8) else shade(COPPER_D, 0.9)
                F.put(x, y, c + F.rng.normal(0, 4))
        px = -15 if s < 0 else 13
        for y in range(17, 64):
            F.put(px, y, COPPER_L)
            F.put(px + 1, y, COPPER)
        for y in (24, 40, 54):
            F.put(px, y, COPPER_D)
            F.put(px + 1, y, COPPER_D)
        F.metal(px - 1, 15, px + 3, 17, STEEL_L, noise=3)
    for x in range(-15, 15):
        F.put(x, 63, COPPER_L)
        F.put(x, 62, COPPER)
    for x in (-8, 8):
        F.put(x, 63, COPPER_D)
        F.put(x, 62, COPPER_D)

    # ------------------------------------------------------------ pictures: leaves
    for x0, s in ((-12, -1), (0, 1)):
        for P, k in ((F, 1.0), (B, 0.88)):
            P.metal(x0, 0, x0 + 12, LEAF_TOP, shade(STEEL, k), bevel=False, noise=5, rust=rgb("6a4a32"), rust_p=0.03)
            # plate seams
            for y in (18, 34):
                for x in range(x0, x0 + 12):
                    P.put(x, y, shade(STEEL_D, k))
            P.strap_v(x0, 0, LEAF_TOP, 2, shade(STEEL_L, k), light=RIVET)
            P.strap_v(x0 + 10, 0, LEAF_TOP, 2, shade(STEEL_L, k), light=RIVET)
            P.strap_h(x0 + 2, x0 + 10, LEAF_TOP - 2, 2, shade(STEEL_L, k), light=RIVET)
            P.strap_h(x0 + 2, x0 + 10, 18, 2, shade(STEEL_L, k), light=RIVET)
            P.strap_h(x0 + 2, x0 + 10, 34, 2, shade(STEEL_L, k), light=RIVET)
            P.strap_h(x0 + 2, x0 + 10, 46, 2, shade(STEEL_L, k), light=RIVET)
            # the lit barred window (both faces)
            P.glow_pane(x0 + 2, 36, x0 + 10, 46)
            for y in range(36, 46):
                P.put(x0 + 4, y, STEEL_D)
                P.put(x0 + 7, y, STEEL_D)
            for x in range(x0 + 2, x0 + 10):
                P.put(x, 41, STEEL_D)
        # hazard kick plate (front)
        for x in range(x0, x0 + 12):
            for y in range(0, 4):
                F.put(x, y, YELLOW if ((x + y) // 2) % 2 == 0 else BLACK)
        for x in range(x0, x0 + 12):
            F.put(x, 4, STEEL_L)
        # back: two horizontal stiffeners
        for y in (10, 26):
            B.strap_h(x0 + 1, x0 + 11, y, 3, shade(STEEL_L, 0.9), light=RIVET)

    # ------------------------------------------------------------ frame cubes
    fr = d.frame
    for s in (-1, 1):
        xo, xs, xi = 16 * s, 14 * s, 12 * s
        d.box(fr, "post_%d" % s, xo, xs, 0, 52, -8, 4, side="frame_side")
        d.box(fr, "post_stop_%d" % s, xs, xi, 0, 52, 2, 4, side="frame_side")
        d.box(fr, "tank_%d" % s, xo, xi, 0, 11, 4, 8, side="copper_side")
        d.box(fr, "tank_cap_%d" % s, xo + 0.5 * -s, xi - 0.5 * -s, 11, 12, 4.5, 7.5, side="frame_side", front="frame_side")
        px = -15 if s < 0 else 13
        d.box(fr, "bracket_%d" % s, px - 1, px + 3, 15, 17, 4, 7.5, side="frame_side")
        d.box(fr, "pipe_v_%d" % s, px, px + 2, 17, 62, 4.5, 6.5, side="copper_side")
        for k, y in enumerate((24, 40, 54)):
            d.box(fr, "flange_%d_%d" % (s, k), px - 0.5, px + 2.5, y, y + 1, 4.2, 6.8, side="copper_side", front="copper_side")
        pist = dm.Bone("piston_%d" % (0 if s < 0 else 1), origin=((px + 1) / 16, 10.5 / 16, 5.5 / 16), parent=fr)
        d.box(pist, "rod", px + 0.5, px + 1.5, 7, 15.5, 5, 6, front="rod_side", back="rod_side", side="rod_side")
    d.box(fr, "pipe_h", -15, 15, 62, 64, 4.5, 6.5, side="copper_side")
    # lintel round the lit vent
    d.box(fr, "lintel_l", -16, -5, 52, 64, -6, 4.5, side="frame_side")
    d.box(fr, "lintel_r", 5, 16, 52, 64, -6, 4.5, side="frame_side")
    d.box(fr, "lintel_b", -5, 5, 52, 55, -6, 4.5, side="frame_side")
    d.box(fr, "lintel_t", -5, 5, 61, 64, -6, 4.5, side="frame_side")
    d.box(fr, "vent_rim_b", -5, 5, 54, 55, 4.5, 5.5, side="frame_side", back=None)
    d.box(fr, "vent_rim_t", -5, 5, 61, 62, 4.5, 5.5, side="frame_side", back=None)
    d.box(fr, "glow_vent", -4, 4, 55, 61, -5, 3.5, side="glow_side")
    for k, x in enumerate((-2, 0, 2)):
        d.box(fr, "vent_bar_%d" % k, x, x + 1, 55, 61, 3.5, 4.5, side="steel_side")
        d.box(fr, "vent_bar_b_%d" % k, x, x + 1, 55, 61, -6, -5, side="steel_side")
    # gears on the lintel
    d.gear(fr, "gear_a_0", -10, 57.5, 5.0, 3.8, 8, 4.5, 5.5, BRASS, hub=1.0, pic="pic_gears")
    d.gear(fr, "gear_b_1", 10, 57.5, 5.0, 3.8, 8, 4.5, 5.5, shade(BRASS, 0.9), hub=1.0, pic="pic_gears")

    # ------------------------------------------------------------ leaves
    for leaf, x0, s in ((d.leaf_l, -12, -1), (d.leaf_r, 0, 1)):
        m = np.ones((LEAF_TOP, 12), bool)
        m[LEAF_TOP - 46:LEAF_TOP - 36, 2:10] = False          # the window (rows from the top)
        d.mask_boxes(leaf, "core", m, x0, 0, -1, 1, side="steel_side")
        d.box(leaf, "glow_window", x0 + 2, x0 + 10, 36, 46, -1, 1, side="glow_side")
        for k, x in enumerate((x0 + 4, x0 + 7)):
            d.box(leaf, "bar_%d" % k, x, x + 1, 36, 46, 1, 2, back=None, side="steel_side")
            d.box(leaf, "bar_b_%d" % k, x, x + 1, 36, 46, -2, -1, front=None, side="steel_side")
        d.box(leaf, "bar_h", x0 + 2, x0 + 10, 41, 42, 1, 2, back=None, side="steel_side")
        d.box(leaf, "bar_hb", x0 + 2, x0 + 10, 41, 42, -2, -1, front=None, side="steel_side")
        # raised riveted frame
        d.box(leaf, "frame_o", x0, x0 + 2, 4, LEAF_TOP, 1, 2, back=None, side="steel_side")
        d.box(leaf, "frame_i", x0 + 10, x0 + 12, 4, LEAF_TOP, 1, 2, back=None, side="steel_side")
        for k, y in enumerate((18, 34, 46, LEAF_TOP - 2)):
            d.box(leaf, "rail_%d" % k, x0 + 2, x0 + 10, y, y + 2, 1, 2, back=None, side="steel_side")
        d.box(leaf, "kick", x0, x0 + 12, 0, 4, 1, 2, back=None, side="steel_side")
        # X braces of the lower panel
        d.strap(leaf, "brace_a", (x0 + 2.6, 4.6), (x0 + 9.4, 17.4), 2, 1, 2, "strap2")
        d.strap(leaf, "brace_b", (x0 + 9.4, 4.6), (x0 + 2.6, 17.4), 2, 1.05, 2.05, "strap2")
        # back stiffeners
        for k, y in enumerate((10, 26)):
            d.box(leaf, "stiff_%d" % k, x0 + 1, x0 + 11, y, y + 3, -2, -1, front=None, side="steel_side")
        # gears meshing across the seam, in the middle zone
        gx = -4.6 if s < 0 else 4.6
        if s < 0:
            d.gear(leaf, "gear_a_2", gx, 27.5, 4.6, 3.5, 8, 1, 2.2, BRASS, hub=1.0, pic="pic_gears")
        else:
            d.gear(leaf, "gear_b_3", gx, 27.5, 4.6, 3.5, 8, 1, 2.2, shade(BRASS, 0.9), hub=1.0, pic="pic_gears")
        # sliding latch bar (bolt) in two guides, under the gear
        bx0, bx1 = (x0 + 3, x0 + 9) if s < 0 else (x0 + 3, x0 + 9)
        bolt = dm.Bone("bolt_%d" % (0 if s < 0 else 1), origin=((bx0 + bx1) / 32, 21.5 / 16, 2.5 / 16), parent=leaf)
        d.box(bolt, "bar", bx0, bx1, 21, 22, 2, 3, front="rod_side", back="rod_side", side="rod_side")
        for k, gxx in enumerate((bx0 + 1, bx1 - 2)):
            d.box(leaf, "guide_%d" % k, gxx, gxx + 1, 20, 23, 1, 3.4, back=None, side="steel_side", front="steel_side")
        # hinge knuckles
        px = -12 if s < 0 else 12
        for k, y in enumerate((6, 26, 44)):
            d.box(leaf, "knuckle_%d" % k, px - 2, px + 2, y, y + 3, -2, 2, front="steel_side", back="steel_side", side="steel_side")
    d.icon_map = (ICON, ICON_PAL)
    return d


REFS = [(dm.REF_DIR + "/ref4.png", (855, 50, 1200, 375)), (dm.REF_DIR + "/ref2.png", (940, 35, 1280, 410)),
        (dm.REF_DIR + "/ref5.png", (1070, 255, 1370, 490)), (dm.REF_DIR + "/ref3.png", (295, 470, 560, 870))]

if __name__ == "__main__":
    d = build()
    d.export()
    for line in d.bones():
        print(line)
    if "--preview" in sys.argv:
        d.preview(dm.SCRATCH + "/doors_out/medium_porte_industrielle.png", refs=REFS)
