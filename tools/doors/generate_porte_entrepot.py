#!/usr/bin/env python3
"""porte_entrepot (1.32.0): the warehouse / shipyard gate, 6 high x 4 wide, two reinforced plank leaves.

References: ref4 "6x4" 3rd (timber frame: posts on stone footings, heavy lintel with end blocks and a central
block, knee braces, a big Saint Andrew's cross over both leaves meeting on riveted iron plates, iron bands, hinge
plates wrapping the posts), ref5 row 3 2nd (big lanterns, timber framing), ref1 bottom 5th (riveted straps, lamps in
iron cages on the posts).
Everything inside the 4 x 6 x 1 box. 1.32.0 rules (see doorlib_large.LargeDoor): the posts cover the leaf edges in
front and leave a rear rebate for the hinges, the lintel covers the leaf tops in front and stays above them behind,
the knee braces and lanterns stand in front of the leaves (a backwards swing never reaches them), the astragal of
the right leaf covers the seam, no coplanar faces (resolve() + audit on export).

Bones: frame (posts, footings, lintel, braces, hinge plates, lanterns), leaf_l / leaf_r (pivots on the hinge edges
X = -/+26 px), bolt_0 / bolt_1 (the halves of the timber drop bar on the back, slide along x), glow_* (lantern
glass).

Run: python3 tools/doors/generate_porte_entrepot.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_large as dl  # noqa: E402
from doorlib_large import rgb, mix, shade, P, STOP_Z  # noqa: E402

NAME = "porte_entrepot"
J = 6
TOP = 84
WOOD, WOOD_D = rgb("7c4524"), rgb("2d1a0e")
TIMBER = rgb("8a5530")
IRON, IRON_L = rgb("47404a"), rgb("6e6470")
STONE = rgb("7f7678")
POST_Z = 3.0
BR0, BR1 = (-25.0, 70.0), (-12.0, 83.5)      # knee brace centre line (left; mirrored on the right)
BR_T = 4.0
BANDS = ((64, 68), (8, 12))
PLATES_Y = (32, 44)
HINGES = ((64, 68), (37, 41), (8, 12))
NOTCHES = []


def paint(Pc, back=False):
    # footings, posts
    for X0, X1 in ((-32, -25), (25, 32)):
        Pc.stone(*Pc.R(X0, X1, 0, 6), base=STONE)
        Pc.planks_v(*Pc.R(X0, X1, 6, TOP), [7], TIMBER, WOOD_D, grain=0.14, knots=0.8)
        Pc.outline(*Pc.R(X0, X1, 6, TOP), shade(WOOD_D, 1.2))
    # leaves
    for X0 in (-26, 0):
        Pc.planks_v(*Pc.R(X0, X0 + 26, 0, TOP), [5, 4, 4, 4, 4, 5], WOOD if not back else shade(WOOD, 0.88), WOOD_D,
                    grain=0.12, knots=0.5, joints=True)
    snap = Pc.snapshot()
    # lintel, end blocks, centre block, cap board
    Pc.planks_h(*Pc.R(-32, 32, TOP - 1, 94), [6, 5], TIMBER, WOOD_D, grain=0.13, outline=WOOD_D)
    Pc.planks_h(*Pc.R(-32, 32, 94, 96), [2], shade(TIMBER, 0.85), WOOD_D)
    for X0, X1 in ((-32, -24), (24, 32), (-4, 4)):
        Pc.planks_v(*Pc.R(X0, X1, TOP - 1, 96), [X1 - X0], shade(TIMBER, 1.08), WOOD_D, grain=0.1, knots=0)
        Pc.rect(*Pc.R(X0, X1, 95, 96), shade(TIMBER, 1.2))
        Pc.outline(*Pc.R(X0, X1, TOP - 1, 96), WOOD_D)
    Pc.metal(*Pc.R(-4, 4, 87, 90), IRON)
    i0, i1, j0, j1 = Pc.R(-4, 4, 87, 90)
    Pc.rivet(i0 + 1, j0 + 1)
    Pc.rivet(i1 - 3, j0 + 1)
    for X0, X1 in ((-32, -24), (24, 32)):
        Pc.metal(*Pc.R(X0 + 1, X1 - 1, 89, 92), IRON)
        i0, i1, j0, j1 = Pc.R(X0 + 1, X1 - 1, 89, 92)
        Pc.rivet(i0 + 1, j0 + 1, big=True)
        Pc.rivet(i1 - 3, j0 + 1, big=True)
    if not back:
        # knee braces (front only: painted where the cubes show them)
        for sg in (-1, 1):
            p0 = Pc.pt(BR0[0] * -sg, BR0[1])
            p1 = Pc.pt(BR1[0] * -sg, BR1[1])
            Pc.line(p0[0], p0[1], p1[0], p1[1], BR_T, shade(TIMBER, 0.98), noise=6)
    Pc.restore(snap, lambda X, Y: -25 <= X < 25 and Y < TOP - 1 and not back or (back and -26 <= X < 26 and Y < TOP))
    if back:
        for X0 in (-26, 0):
            for (y0, y1) in ((10, 16), (38, 44), (66, 72)):
                Pc.planks_h(*Pc.R(X0 + 1, X0 + 25, y0, y1), [6], shade(TIMBER, 0.95), WOOD_D, outline=WOOD_D)
        Pc.rect(*Pc.R(-1, 1, 0, TOP), rgb("140c08"))
        for X0, X1 in ((-32, -28), (28, 32)):
            Pc.planks_v(*Pc.R(X0, X1, 6, TOP), [4], shade(TIMBER, 0.9), WOOD_D, grain=0.14, knots=0.8)
        for X0, X1 in ((-28, -26), (26, 28)):
            Pc.rect(*Pc.R(X0, X1, 6, TOP), shade(WOOD_D, 1.1))
        return
    # leaf top shadow under the lintel
    for X in range(-25, 25):
        Pc.put(Pc.I(X), Pc.J(TOP - 2), shade(Pc.get(Pc.I(X), Pc.J(TOP - 2)), 0.6))
    # iron bands (front), seam straps / astragal, centre plates, hinge straps, hinge plates on the posts
    for X0, X1 in ((-26, 0), (0, 26)):
        for (y0, y1) in BANDS:
            Pc.metal(*Pc.R(X0, X1, y0, y1), IRON)
            i0, i1, j0, j1 = Pc.R(X0, X1, y0, y1)
            Pc.rivets_h(i0 + 1, i1 - 1, j0 + 1, 6.2, big=True, light=rgb("d6b48a"))
        Pc.metal(*Pc.R(X0, X1, 0, 3), shade(IRON, 0.85))
    Pc.metal(*Pc.R(-3, -1, 0, TOP), IRON)
    Pc.metal(*Pc.R(-1, 3, 0, TOP), shade(IRON, 1.1))
    Pc.rect(*Pc.R(-1, 0, 0, TOP), rgb("140c08"))
    i0, i1, j0, j1 = Pc.R(0, 3, 0, TOP)
    Pc.rivets_v(i0 + 1, j0 + 2, j1 - 2, 7, light=rgb("a89ca4"))
    for X0, X1 in ((-9, -1), (3, 9)):
        Pc.metal(*Pc.R(X0, X1, PLATES_Y[0], PLATES_Y[1]), shade(IRON, 1.1))
        i0, i1, j0, j1 = Pc.R(X0, X1, PLATES_Y[0], PLATES_Y[1])
        for ii, jj in ((i0 + 1, j0 + 1), (i1 - 2, j0 + 1), (i0 + 1, j1 - 2), (i1 - 2, j1 - 2)):
            Pc.rivet(ii, jj)
        cxp = (i0 + i1) / 2
        Pc.disc(cxp, (j0 + j1) / 2 + 1, 2.6, rgb("8a8090"), ring=rgb("2a2428"), r_in=1.3)
        Pc.rect(cxp - 1, cxp + 1, j0 + 2, j0 + 4, rgb("2a2428"))
    for (y0, y1) in HINGES:
        for X0, X1 in ((-26, -14), (14, 26)):
            Pc.metal(*Pc.R(X0, X1, y0, y1), shade(IRON, 0.92))
            i0, i1, j0, j1 = Pc.R(X0, X1, y0, y1)
            Pc.rivets_h(i0 + 2, i1 - 2, j0 + 1, 4.5, big=False, light=rgb("c8b8a8"))
        for X0, X1 in ((-32, -25), (25, 32)):
            Pc.metal(*Pc.R(X0, X1, y0 - 1, y1 + 1), IRON)
            i0, i1, j0, j1 = Pc.R(X0, X1, y0 - 1, y1 + 1)
            Pc.rivet(i0 + 1, j0 + 1, big=True)
            Pc.rivet(i1 - 3, j1 - 3, big=True)


def build_leaves(d):
    for bone, tag in ((d.leaf_l, "l"), (d.leaf_r, "r")):
        X0, X1 = d.leaf_x(tag)
        s = -1 if tag == "l" else 1
        d.box(bone, "body_" + tag, X0, X1, dl.GAP, TOP - dl.GAP, -dl.BODY, dl.BODY, side="wood_side", top="wood_end")
        bx0, bx1 = (X0 + 0.25, -3.25) if s < 0 else (3.25, X1 - 0.25)
        for (y0, y1) in BANDS:
            d.box(bone, "band_%s_%d" % (tag, y0), bx0, bx1, y0, y1, 1.25, 1.75, back=None)
        d.box(bone, "foot_" + tag, bx0, bx1, 0.25, 3, 1.25, 1.75, back=None)
        if s < 0:
            d.box(bone, "seam_strap_l", -3, -1, 0.25, TOP - 0.5, 1.25, 2.0, back=None)
        else:
            d.box(bone, "seam_strap_r", 0.5, 3, 0.25, TOP - 0.5, 1.25, 1.75, back=None, front=None)
            d.box(bone, "astragal", -0.75, 3, 0.25, TOP - 0.5, 1.75, 2.0, back="iron_side")
        px0, px1 = (-9, -1.25) if s < 0 else (3.25, 9)
        d.box(bone, "centre_plate_" + tag, px0, px1, PLATES_Y[0], PLATES_Y[1], 1.25, 2.0, back=None)
        # the Saint Andrew's cross: two battens per leaf meeting on the centre plate (front 1.75)
        oxe = X0 + 3.5 if s < 0 else X1 - 3.5
        cxe = -8 if s < 0 else 8
        d.rbox(bone, "cross_up_" + tag, (oxe, 59.5), (cxe, 44.5), 5, 1.25, 1.75, "batten", side="wood_h")
        d.rbox(bone, "cross_low_" + tag, (cxe, 31.5), (oxe, 15.5), 5, 1.25, 1.75, "batten", side="wood_h")
        # hinge straps from the hinge edge (front 2.0) and knuckles behind (in the rebate)
        hs0, hs1 = (X0 + 0.25, -14) if s < 0 else (14, X1 - 0.25)
        for (y0, y1) in HINGES:
            d.box(bone, "hstrap_%s_%d" % (tag, y0), hs0, hs1, y0 + 0.25, y1 - 0.25, 1.5, 2.0, back=None)
            kx0, kx1 = (X0, X0 + 2.5) if s < 0 else (X1 - 2.5, X1)
            d.box(bone, "knuckle_%s_%d" % (tag, y0), kx0, kx1, y0, y1, -2.0, -1.25, front=None, side="iron")
        # back: ledges and braces, the drop bar halves (bolts) in iron brackets
        lx0, lx1 = (X0 + 3, X1 - 1) if s < 0 else (X0 + 1, X1 - 3)
        for (y0, y1) in ((10, 16), (38, 44), (66, 72)):
            d.box(bone, "ledge_%s_%d" % (tag, y0), lx0, lx1, y0, y1, -2.0, -1.25, front=None, side="wood_h")
        bxa, bxb = (-15, -0.5) if s < 0 else (0.5, 15)
        bolt = dl.Bone("bolt_%d" % (0 if s < 0 else 1), origin=((bxa + bxb) / 2 * P, 52 * P, -1.625 * P), parent=bone)
        d.box(bolt, "bar_" + tag, bxa, bxb, 50, 54, -2.0, -1.25, front=None, back="bar", side="wood_h")
        for k, sx in enumerate((bxa + 3, bxb - 3)):
            for j, (y0, y1) in enumerate(((48.75, 50), (54, 55.25))):
                d.box(bone, "bracket_%s_%d_%d" % (tag, k, j), sx - 1, sx + 1, y0, y1, -2.0, -1.25, front=None,
                      back="iron", side="iron")
        d.rbox(bone, "bbrace_low_" + tag, (X0 + 5, 16) if s < 0 else (X1 - 5, 16),
               (X1 - 4, 38) if s < 0 else (X0 + 4, 38), 4, -1.75, -1.25, "batten_back", side="wood_h")
        d.rbox(bone, "bbrace_up_" + tag, (X0 + 5, 44) if s < 0 else (X1 - 5, 44),
               (X1 - 4, 66) if s < 0 else (X0 + 4, 66), 4, -1.75, -1.25, "batten_back", side="wood_h")


def build_frame(d, sw):
    fr = d.frame
    det = d.detail(fr)
    for side in (-1, 1):
        tg = "l" if side < 0 else "r"
        d.jamb_courses(side, [(0, 6)], front_z=(8.0,), back_z=(8.0,), mat="stone_side", name="footing")
        d.jamb_courses(side, [(6, TOP - 1)], front_z=(POST_Z,), back_z=(6.0,), mat="wood_side", name="post")
        a, b = (-26 - dl.REBATE, -26) if side < 0 else (26, 26 + dl.REBATE)
        y0 = max(0, int(math.ceil(sw.top(a, b, -8, 0) + 0.5)))
        if y0 < TOP - 1:
            d.box(fr, "rebate_fill_" + tg, a, b, y0, TOP - 1, -6.0, 0, side="wood_side")
    d.sill(mat="stone_side", front="stone_side")
    d.box(fr, "lintel", -32, 32, TOP - 1, 94, STOP_Z, 7.0, side="wood_h")
    d.box(fr, "lintel_b", -32, 32, TOP, 94, -7.0, STOP_Z, side="wood_h")
    for k, (X0, X1) in enumerate(((-24, -4), (4, 24))):
        for j, (z0, z1) in enumerate(((STOP_Z, 6.5), (-6.5, STOP_Z))):
            d.box(fr, "cap_board_%d_%d" % (k, j), X0, X1, 94, 96, z0, z1, side="wood_h",
                  front="F" if j == 0 else None, back="B" if j == 1 else None)
    for tag, (X0, X1) in (("l", (-32, -24)), ("r", (24, 32)), ("c", (-4, 4))):
        d.box(fr, "block_" + tag, X0, X1, TOP - 1 + (0.5 if tag == "c" else 0), 96, STOP_Z, 8,
              side="wood_end" if tag != "c" else "wood_side", top="wood_end")
        d.box(fr, "block_b_" + tag, X0, X1, TOP + 0.5, 96, -8, STOP_Z, side="wood_end", top="wood_end",
              front=None)
    # knee braces (rotated about z) in front of the leaves' upper corners
    for sg in (-1, 1):
        p0, p1 = (BR0[0] * -sg, BR0[1]), (BR1[0] * -sg, BR1[1])
        d.rbox(fr, "knee_%d" % (sg > 0), p0, p1, BR_T, 2.5, 5.75, "brace_face", side="wood_h")
    # hinge plates wrapping the posts' front
    for (y0, y1) in HINGES:
        for tag, (X0, X1) in (("l", (-32, -25)), ("r", (25, 32))):
            d.box(fr, "hinge_plate_%s_%d" % (tag, y0), X0 + 0.25, X1 - 0.25, y0 - 1, y1 + 1, POST_Z - 0.5, POST_Z + 0.5,
                  back=None, side="iron")
    # big lanterns on iron arms (lit glass, drawn full bright)
    for tag, x in (("l", -28.75), ("r", 28.75)):
        d.box(det, "lantern_arm_" + tag, x - 0.5, x + 0.5, 65.5, 75, POST_Z - 0.25, 6.5, side="iron", front="iron",
              back="iron")
        d.box(det, "lantern_hook_" + tag, x - 1.25, x + 1.25, 74, 75.5, POST_Z - 0.25, 7.25, side="iron",
              front="iron", back="iron")
        # the lantern stands just in front of the post (every part >= 1/64 block from its front face)
        d.lantern(fr, "lantern_" + tag, x, 58.0, 5.62, w=4.4, h=8.5, metal="iron")


def icon(px, im):
    p = im.load()
    for y in range(16):
        for x in range(16):
            p[x, y] = (0, 0, 0, 0)
    T, W, Wd, IR, ST, GL = rgb("9a6034"), rgb("7c4524"), rgb("4a2812"), rgb("3e3842"), rgb("7f7678"), rgb("ffc860")
    for y in range(2, 16):
        for x in range(2, 14):
            p[x, y] = (W if x % 3 else Wd) + (255,)
    for x in range(0, 16):
        for y in range(0, 3):
            p[x, y] = T + (255,)
        p[x, 2] = Wd + (255,)
    for y in range(3, 16):
        for x in (0, 1, 14, 15):
            p[x, y] = (T if y < 14 else ST) + (255,)
    for k in range(10):            # Saint Andrew's cross
        for (x, y) in ((3 + k, 4 + k * 10 // 9), (12 - k, 4 + k * 10 // 9)):
            if 0 <= y < 16:
                p[x, y] = rgb("d09a62") + (255,)
    for x in range(2, 14):
        p[x, 4] = IR + (255,)
        p[x, 13] = IR + (255,)
    for y in range(3, 16):
        p[7, y] = rgb("140c08") + (255,)
    for (x, y) in ((6, 8), (8, 8), (6, 9), (8, 9)):
        p[x, y] = IR + (255,)
    for (x, y) in ((1, 6), (1, 7), (14, 6), (14, 7)):
        p[x, y] = GL + (255,)
    p[1, 5] = IR + (255,)
    p[14, 5] = IR + (255,)


def main():
    d = dl.LargeDoor(NAME, jamb=J, size=256, seed=31)
    d.notches = NOTCHES
    dl.standard_materials(d, wood=TIMBER, wood_dark=WOOD_D, iron=IRON, stone=STONE)

    def batten(px, base=shade(TIMBER, 1.12)):
        px.planks_h(0, px.w, 0, px.h, [px.h], base, WOOD_D, grain=0.12, outline=WOOD_D)
        px.rivets_h(2, px.w - 2, px.h // 2 - 1, 7, big=False, light=rgb("c8b8a8"))
    d.sprite("batten", 36, 5, batten)
    d.sprite("batten_back", 28, 4, lambda px: batten(px, shade(TIMBER, 0.98)))
    d.sprite("brace_face", 20, 4, lambda px: px.planks_h(0, px.w, 0, px.h, [px.h], shade(TIMBER, 0.98), WOOD_D,
                                                         outline=WOOD_D))

    def bar(px):
        px.planks_h(0, px.w, 0, px.h, [px.h], shade(TIMBER, 1.05), WOOD_D, outline=WOOD_D)
    d.sprite("bar", 15, 4, bar)
    paint(d.F, back=False)
    paint(d.B, back=True)
    build_leaves(d)
    sw = dl.Sweep(d)
    build_frame(d, sw)
    d.export(icon=icon)
    if "--preview" in sys.argv:
        C = os.path.join(dl.SCRATCH, "doors_out/crops")
        d.preview(os.path.join(dl.SCRATCH, "doors_out2/large_%s.png" % NAME),
                  [os.path.join(C, "entrepot_r4.png"), os.path.join(C, "entrepot_r5.png"),
                   os.path.join(C, "entrepot_r1.png")])


if __name__ == "__main__":
    main()
