#!/usr/bin/env python3
"""porte_entrepot (1.31.0): the warehouse / shipyard gate, 6 high x 4 wide, two reinforced plank leaves.

References: ref4 "6x4" 3rd (timber frame: posts on stone footings, heavy lintel with end blocks and a central
block, knee braces, a big Saint Andrew's cross over both leaves meeting on riveted iron plates, iron bands, hinge
plates wrapping the posts), ref5 row 3 2nd (lanterns, timber framing), ref1 bottom 5th (riveted straps).
Everything inside the 4 x 6 x 1 box: posts 6 px wide, lintel Y 84-94, the leaves (26 px each) up to the lintel, the
knee braces in front of their upper corners (z 2-5 px: clear of a leaf swinging backwards, the default).

Bones: frame (posts, footings, lintel, braces, hinge plates, lanterns), leaf_l / leaf_r (pivots on the hinge edges
X = -/+26 px), bolt_0 / bolt_1 (the halves of the timber drop bar on the back, slide along x).

Run: python3 tools/doors/generate_porte_entrepot.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_large as dl  # noqa: E402
from doorlib_large import rgb, mix, shade, P  # noqa: E402

NAME = "porte_entrepot"
J = 6
TOP = 84
WOOD, WOOD_D = rgb("7c4524"), rgb("2d1a0e")
TIMBER = rgb("8a5530")
IRON, IRON_L = rgb("47404a"), rgb("6e6470")
STONE = rgb("7f7678")
BR0, BR1 = (-27.0, 70.0), (-13.0, 85.0)      # knee brace centre line (left; mirrored on the right)
BR_T = 4.0
BANDS = ((64, 68), (8, 12))
PLATES_Y = (32, 44)
HINGES = ((64, 68), (37, 41), (8, 12))


def brace_low(X):
    """Lower edge of the left knee brace at X (door px)."""
    ang = math.atan2(BR1[1] - BR0[1], BR1[0] - BR0[0])
    off = (BR_T / 2) / math.cos(ang)
    return BR0[1] + (X - BR0[0]) * math.tan(ang) - off


def leaf_top(X):
    """Top of the leaves: right under the lintel (the knee braces stand in front of the leaves' upper corners, so a
    leaf swinging backwards, the default, never meets them)."""
    return TOP


def paint(Pc, back=False):
    # footings, posts
    for X0, X1 in ((-32, -26), (26, 32)):
        Pc.stone(*Pc.R(X0, X1, 0, 6), base=STONE)
        Pc.planks_v(*Pc.R(X0, X1, 6, TOP), [6], TIMBER, WOOD_D, grain=0.14, knots=0.8)
        Pc.outline(*Pc.R(X0, X1, 6, TOP), shade(WOOD_D, 1.2))
    # leaves
    for X0 in (-26, 0):
        Pc.planks_v(*Pc.R(X0, X0 + 26, 0, TOP), [5, 4, 4, 4, 4, 5] if X0 < 0 else [5, 4, 4, 4, 4, 5],
                    WOOD if not back else shade(WOOD, 0.88), WOOD_D, grain=0.12, knots=0.5, joints=True)
    snap = Pc.snapshot()
    # lintel, end blocks, centre block, cap board
    Pc.planks_h(*Pc.R(-32, 32, TOP, 94), [5, 5], TIMBER, WOOD_D, grain=0.13, outline=WOOD_D)
    Pc.planks_h(*Pc.R(-32, 32, 94, 96), [2], shade(TIMBER, 0.85), WOOD_D)
    for X0, X1 in ((-32, -24), (24, 32), (-4, 4)):
        y0 = TOP
        Pc.planks_v(*Pc.R(X0, X1, y0, 96), [X1 - X0], shade(TIMBER, 1.08), WOOD_D, grain=0.1, knots=0)
        Pc.outline(*Pc.R(X0, X1, y0, 96), WOOD_D)
    Pc.metal(*Pc.R(-4, 4, 86, 89), IRON)
    i0, i1, j0, j1 = Pc.R(-4, 4, 86, 89)
    Pc.rivet(i0 + 1, j0 + 1, big=False)
    Pc.rivet(i1 - 3, j0 + 1, big=False)
    # knee braces (painted where the cube shows them)
    for sg in (-1, 1):
        p0 = Pc.pt(BR0[0] * -sg if sg > 0 else BR0[0], BR0[1])
        p1 = Pc.pt(BR1[0] * -sg if sg > 0 else BR1[0], BR1[1])
        Pc.line(p0[0], p0[1], p1[0], p1[1], BR_T, shade(TIMBER, 0.95), noise=6)
    Pc.restore(snap, lambda X, Y: abs(X + 0.5) < 26 and Y < leaf_top(X))
    # leaf top shadow under the lintel / braces
    for X in range(-26, 26):
        Pc.put(Pc.I(X), Pc.J(leaf_top(X) - 1), shade(Pc.get(Pc.I(X), Pc.J(leaf_top(X) - 1)), 0.6))
    if back:
        for X0 in (-26, 0):
            for (y0, y1) in ((10, 16), (38, 44), (66, 72)):
                Pc.planks_h(*Pc.R(X0 + 1, X0 + 25, y0, y1), [6], shade(TIMBER, 0.95), WOOD_D, outline=WOOD_D)
        Pc.rect(*Pc.R(-1, 1, 0, TOP), rgb("140c08"))
        return
    # iron bands (front), seam straps, centre plates, hinge plates on the posts
    for X0, X1 in ((-26, 0), (0, 26)):
        for (y0, y1) in BANDS:
            Pc.metal(*Pc.R(X0, X1, y0, y1), IRON)
            i0, i1, j0, j1 = Pc.R(X0, X1, y0, y1)
            Pc.rivets_h(i0 + 1, i1 - 1, j0 + 1, 6.2, big=True, light=rgb("d6b48a"))
        Pc.metal(*Pc.R(X0, X1, 0, 3), shade(IRON, 0.85))
    for X0, X1 in ((-3, 0), (0, 3)):
        Pc.metal(*Pc.R(X0, X1, 0, TOP), IRON)
        i0, i1, j0, j1 = Pc.R(X0, X1, 0, TOP)
        Pc.rivets_v(i0 + (1 if X0 < 0 else 0), j0 + 2, j1 - 2, 7, light=rgb("a89ca4"))
    for X0, X1 in ((-8, 0), (0, 8)):
        Pc.metal(*Pc.R(X0, X1, PLATES_Y[0], PLATES_Y[1]), shade(IRON, 1.1))
        i0, i1, j0, j1 = Pc.R(X0, X1, PLATES_Y[0], PLATES_Y[1])
        for ii, jj in ((i0, j0), (i1 - 1, j0), (i0, j1 - 1), (i1 - 1, j1 - 1)):
            Pc.put(ii, jj, (0, 0, 0), 0)
        cx = (i0 + i1) // 2
        Pc.disc(cx + (0.5 if X0 < 0 else -0.5) + 0.0, (j0 + j1) / 2, 2.0, rgb("8a8090"), ring=rgb("2a2428"))
    Pc.rect(*Pc.R(-1, 1, 0, TOP), rgb("140c08"))
    for (y0, y1) in HINGES:
        for X0, X1 in ((-32, -26), (26, 32)):
            Pc.metal(*Pc.R(X0, X1, y0 - 1, y1 + 1), IRON)
            i0, i1, j0, j1 = Pc.R(X0, X1, y0 - 1, y1 + 1)
            Pc.rivet(i0 + 1, j0 + 1, big=True)
            Pc.rivet(i1 - 3, j1 - 3, big=True)


def build(d):
    fr, L, Rr = d.frame, d.leaf_l, d.leaf_r
    det = d.detail(fr)
    for tag, (X0, X1) in (("l", (-32, -26)), ("r", (26, 32))):
        d.box(fr, "footing_" + tag, X0, X1, 0, 6, -8, 8, side="stone_side")
        d.box(fr, "post_" + tag, X0, X1, 6, TOP, -6, 4.5, side="wood_side")
    d.box(fr, "lintel", -24, 24, TOP, 94, -7.5, 7.5, side="wood_h")
    d.box(fr, "cap_board", -24, 24, 94, 96, -6, 6, side="wood_h")
    for tag, (X0, X1, y0) in (("l", (-32, -24, TOP)), ("r", (24, 32, TOP)), ("c", (-4, 4, TOP))):
        d.box(fr, "block_" + tag, X0, X1, y0, 96, -8, 8, side="wood_end" if tag != "c" else "wood_side",
              top="wood_end")
    # knee braces (rotated about z) in front of the leaves' upper corners
    for sg in (-1, 1):
        p0 = (BR0[0] * -sg if sg > 0 else BR0[0], BR0[1])
        p1 = (BR1[0] * -sg if sg > 0 else BR1[0], BR1[1])
        if sg > 0:
            p0, p1 = (-BR0[0], BR0[1]), (-BR1[0], BR1[1])
        d.rbox(fr, "knee_%d" % (sg > 0), p0, p1, BR_T, 2.1, 5.0, "brace_face", side="wood_h")
    # hinge plates wrapping the posts (the pintles of the leaves)
    for (y0, y1) in HINGES:
        for tag, (X0, X1) in (("l", (-32, -26)), ("r", (26, 32))):
            d.box(fr, "hinge_plate_%s_%d" % (tag, y0), X0, X1, y0 - 1, y1 + 1, 4.5, 5.25, back=None, side="iron")
    # lanterns on iron arms
    for tag, x in (("l", -29.4), ("r", 29.4)):
        d.box(det, "lantern_arm_" + tag, x - 0.5, x + 0.5, 56, 62, 4.5, 6.5, side="iron", front="iron", back="iron")
        d.lantern(fr, "lantern_" + tag, x, 52.5, 6.4, w=3.2, h=5.0, metal="iron")
    # ---------------- leaves
    for bone, X0, X1, tag in ((L, -26, 0, "l"), (Rr, 0, 26, "r")):
        s = -1 if tag == "l" else 1
        d.box(bone, "body_" + tag, X0, X1, 0, TOP, -1.25, 1.25, side="wood_side", top="wood_end")
        for (y0, y1) in BANDS:
            bx0, bx1 = (X0, X1 - 3) if s < 0 else (X0 + 3, X1)
            d.box(bone, "band_%s_%d" % (tag, y0), bx0, bx1, y0, y1, 1.25, 1.75, back=None)
        d.box(bone, "foot_" + tag, X0 + (0 if s < 0 else 3), X1 - (3 if s < 0 else 0), 0, 3, 1.25, 1.6, back=None)
        sx0, sx1 = (-3, 0) if s < 0 else (0, 3)
        d.box(bone, "seam_strap_" + tag, sx0, sx1, 0, TOP, 1.25, 1.85, back=None)
        px0, px1 = (-8, 0) if s < 0 else (0, 8)
        d.box(bone, "centre_plate_" + tag, px0, px1, PLATES_Y[0], PLATES_Y[1], 1.25, 2.0, back=None)
        # the Saint Andrew's cross: two wooden battens per leaf meeting on the centre plate
        oxe = X0 + 3 if s < 0 else X1 - 3
        cxe = -7 if s < 0 else 7
        d.rbox(bone, "cross_up_" + tag, (oxe, 62.5), (cxe, 42), 5, 1.25, 1.85, "batten", side="wood_h")
        d.rbox(bone, "cross_low_" + tag, (cxe, 34), (oxe, 13.5), 5, 1.25, 1.85, "batten", side="wood_h")
        # hinge straps reaching the hinge edge (knuckles both faces)
        hx = X0 if s < 0 else X1
        for (y0, y1) in HINGES:
            d.box(bone, "knuckle_%s_%d" % (tag, y0), hx if s < 0 else hx - 1.5, hx + 1.5 if s < 0 else hx, y0, y1,
                  -2.0, 2.0, side="iron", front="iron", back="iron")
        # back: ledges and braces, the drop bar halves (bolts) in iron brackets
        for (y0, y1) in ((10, 16), (38, 44), (66, 72)):
            d.box(bone, "ledge_%s_%d" % (tag, y0), X0 + 1, X1 - 1, y0, y1, -2.0, -1.25, front=None, side="wood_h")
        bxa, bxb = (-15, 0) if s < 0 else (0, 15)
        bolt = dl.Bone("bolt_%d" % (0 if s < 0 else 1), origin=((bxa + bxb) / 2 * P, 52 * P, -1.6 * P), parent=bone)
        d.box(bolt, "bar_" + tag, bxa, bxb, 50, 54, -2.0, -1.25, front=None, back="bar", side="wood_h")
        for k, sx in enumerate((bxa + 3, bxb - 3)):
            d.box(bone, "bracket_%s_%d" % (tag, k), sx - 1, sx + 1, 49, 55, -1.9, -1.25, front=None, back="iron",
                  side="iron")
        d.rbox(bone, "bbrace_low_" + tag, (X0 + 3, 16) if s < 0 else (X1 - 3, 16), (X1 - 4, 38) if s < 0 else (X0 + 4, 38),
               4, -2.0, -1.3, "batten_back", side="wood_h")
        d.rbox(bone, "bbrace_up_" + tag, (X0 + 3, 44) if s < 0 else (X1 - 3, 44), (X1 - 4, 66) if s < 0 else (X0 + 4, 66),
               4, -2.0, -1.3, "batten_back", side="wood_h")


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
    p[1, 7] = GL + (255,)
    p[14, 7] = GL + (255,)


def main():
    d = dl.LargeDoor(NAME, jamb=J, size=256, seed=31)
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
    build(d)
    d.export(icon=icon)
    if "--preview" in sys.argv:
        C = os.path.join(dl.SCRATCH, "doors_out/crops")
        d.preview(os.path.join(dl.SCRATCH, "doors_out/large_%s.png" % NAME),
                  [os.path.join(C, "entrepot_r4.png"), os.path.join(C, "entrepot_r5.png"), os.path.join(C, "entrepot_r1.png")])


if __name__ == "__main__":
    main()
