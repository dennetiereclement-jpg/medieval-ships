#!/usr/bin/env python3
"""porte_chateau (1.31.0): the monumental castle gate, 6 high x 4 wide, two massive oak leaves.

References: ref4 "6x4" 1st (stone arch with keystone, orange oak leaves, riveted iron bands, studded lower plate,
iron straps on the meeting edges), ref5 row 3 1st (crenellated parapet, blue banners, braziers), ref1 top 5th.
Everything inside the 4 x 6 x 1 box: stone jambs 6 px wide, a segmental arch whose ring and spandrel walls fill the
upper corners, a cornice and five merlons on top; the leaves (26 px wide each) follow the arch.

Bones: frame (jambs, arch, parapet, banners, braziers), leaf_l / leaf_r (pivots on the hinge edges X = -/+26 px),
bolt_0 / bolt_1 (the heavy bars on the back, slide along x), glow_* (brazier flames).

Run: python3 tools/doors/generate_porte_chateau.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_large as dl  # noqa: E402
from doorlib_large import rgb, mix, shade  # noqa: E402

NAME = "porte_chateau"
J = 6                        # jamb width (px)
YS, RISE = 58, 20            # arch springing line and rise of the intrados (px)
R_IN = (26 ** 2 + RISE ** 2) / (2 * RISE)
YC = YS + RISE - R_IN        # centre of the arch circles
RING = 8                     # voussoir depth (px)
CORNICE = (86, 89)
STEP = 2
BACK_Y = 79                  # the back half of the arch (z < -2 px) starts above the highest leaf top (78)

WOOD = rgb("93511f")
WOOD_D = rgb("3a1c0c")
IRON = rgb("4a4246")
STONE = rgb("8e8384")


def top_q(X):
    """Leaf top / intrados height of the 2 px strip containing X (quantised like the cubes)."""
    s = math.floor((X + 26) / STEP)
    xc = -26 + (s + 0.5) * STEP
    return int(round(YC + math.sqrt(max(0.0, R_IN ** 2 - xc ** 2))))


def extrados(X):
    return YC + math.sqrt(max(0.0, (R_IN + RING) ** 2 - X ** 2))


COURSES = [(0, 9), (9, 18), (18, 27), (27, 36), (36, 44), (44, 52), (52, 60)]
MERLONS = ((-32, -24), (-18, -10), (-4, 4), (10, 18), (24, 32))


def leaf_px(X, Y):
    return abs(X + 0.5) < 26 and Y < top_q(X)


def paint_masonry(Pc, k_tone=1.0):
    """Jambs, spandrel walls, voussoirs, keystone, cornice and merlons on a picture (front or back)."""
    st = shade(STONE, k_tone)
    # spandrel walls: small coursed stones
    for r in range(10):
        y0 = 56 + r * 4
        off = (r % 2) * 3
        X = -32 - off
        while X < 32:
            w = 6 if (X // 6) % 2 else 7
            Pc.stone(*Pc.R(max(-32, X), min(32, X + w), y0, min(96, y0 + 4)), base=shade(st, 0.9), mortar=rgb("3a3334"))
            X += w
    # jamb quoins
    for X0, X1 in ((-32, -26), (26, 32)):
        for k, (y0, y1) in enumerate(COURSES):
            Pc.stone(*Pc.R(X0, X1, y0, y1), base=st if k % 2 else shade(st, 1.07))
    # voussoirs with radial joints
    n_v = 10
    a0, a1 = math.atan2(YS - YC, -26.0), math.atan2(YS - YC, 26.0)
    tones = [shade(st, 1.0 + 0.07 * ((k * 3) % 4 - 1.5) / 1.5) for k in range(n_v)]
    for Y in range(YS - 4, 90):
        for X in range(-32, 32):
            xc, yc = X + 0.5, Y + 0.5
            dd = math.hypot(xc, yc - YC)
            if leaf_px(X, Y) or not (R_IN - 1.0 <= dd <= R_IN + RING) or Y < YS - 1:
                continue
            ang = math.atan2(yc - YC, xc)
            t = (a0 - ang) / (a0 - a1)
            if t < -0.06 or t > 1.06:
                continue
            k = int(min(n_v - 1, max(0, t * n_v)))
            frac = t * n_v - k
            c = tones[k]
            if frac < 0.09 or dd > R_IN + RING - 1:
                c = rgb("3a3334")
            elif dd < R_IN + 0.6 or frac < 0.2:
                c = mix(c, (232, 226, 222), 0.32)
            elif frac > 0.85 or dd > R_IN + RING - 2:
                c = shade(c, 0.82)
            else:
                rr = Pc.rng.random()
                c = shade(c, 0.88) if rr < 0.16 else mix(c, (225, 218, 215), 0.18) if rr < 0.28 else c
            Pc.put(Pc.I(X), Pc.J(Y), Pc.jit(c, 4))
    # cornice, keystone, merlons
    Pc.rect(*Pc.R(-32, 32, CORNICE[0], CORNICE[1]), shade(st, 0.82), noise=4)
    for X in range(-32, 32):
        Pc.put(Pc.I(X), Pc.J(CORNICE[1] - 1), mix(st, (235, 230, 226), 0.35))
        Pc.put(Pc.I(X), Pc.J(CORNICE[0]), rgb("332c2d"))
    Pc.stone(*Pc.R(-5, 5, top_q(0) - 1, 91), base=shade(st, 1.12))
    Pc.clear(*Pc.R(-32, 32, 89, 96))
    for X0, X1 in MERLONS:
        Pc.stone(*Pc.R(X0, X1, 91 if abs(X0) < 5 else 89, 96), base=shade(st, 1.04))
    # shadow line under the intrados, on the leaf side
    for X in range(-26, 26):
        Y = top_q(X) - 1
        Pc.put(Pc.I(X), Pc.J(Y), shade(Pc.get(Pc.I(X), Pc.J(Y)), 0.6))


def paint_front(d):
    F = d.F
    for X0 in (-26, 0):
        F.planks_v(*F.R(X0, X0 + 26, 0, 80), [5, 4, 4, 4, 4, 5], WOOD, WOOD_D, grain=0.12, knots=0.6)
    snap = F.snapshot()
    paint_masonry(F)
    F.restore(snap, lambda X, Y: leaf_px(X, Y) and Y < top_q(X) - 1)
    # ---- iron: bands, studded plate, seam straps
    for X0, X1 in ((-26, 0), (0, 26)):
        for (y0, y1) in ((49, 54), (30, 35)):
            F.metal(*F.R(X0, X1, y0, y1), IRON)
            i0, i1, j0, j1 = F.R(X0, X1, y0, y1)
            F.rivets_h(i0 + 1, i1 - 1, j0 + 1, 4.4, big=True, light=rgb("e2c890") if y0 == 49 else dl.RIVET_L)
            F.rivets_h(i0 + 1, i1 - 1, j0 + 3, 4.4, big=False)
        F.metal(*F.R(X0, X1, 3, 20), shade(IRON, 0.95))
        F.metal(*F.R(X0, X1, 0, 3), shade(IRON, 0.8))
    for X0, X1 in ((-3, 0), (0, 3)):
        F.metal(*F.R(X0, X1, 0, top_q(X0) - 1), shade(IRON, 1.05))
        i0, i1, j0, j1 = F.R(X0, X1, 0, top_q(X0) - 1)
        F.rivets_v(i0 + 1 if X0 < 0 else i0, j0 + 4, j1 - 2, 6, big=False)
    F.rect(*F.R(-1, 1, 0, top_q(0) - 1), rgb("1c1718"))          # the gap between the leaves
    for X0 in (-26, 0):
        for yy in (17, 12, 7):
            for k in range(5):
                cxp = int(round(X0 + (k + 0.5) * 26 / 5))
                if abs(cxp) >= 3:
                    F.rivet(F.I(cxp - 1), F.J(yy), big=True)
    # ring pulls
    for cx in (-8, 8):
        F.metal(*F.R(cx - 1, cx + 1, 43, 45), shade(IRON, 0.8))
    # hinge pintles on the jambs
    for y in (50, 31, 10):
        F.metal(*F.R(-27, -26, y - 1, y + 4), rgb("2e292b"))
        F.metal(*F.R(26, 27, y - 1, y + 4), rgb("2e292b"))


def paint_back(d):
    B = d.B
    for X0 in (-26, 0):
        B.planks_v(*B.R(X0, X0 + 26, 0, 80), [5, 4, 4, 4, 4, 5], shade(WOOD, 0.85), WOOD_D, grain=0.1, knots=0.4)
        for (y0, y1) in ((8, 14), (30, 36), (50, 56)):
            B.planks_h(*B.R(X0 + 1, X0 + 25, y0, y1), [6], shade(WOOD, 1.0), WOOD_D, outline=WOOD_D)
    B.rect(*B.R(-1, 1, 0, 79), rgb("1c1718"))
    snap = B.snapshot()
    paint_masonry(B, 0.94)
    B.restore(snap, lambda X, Y: leaf_px(X, Y) and Y < top_q(X) - 1)


def build(d):
    fr, L, Rr = d.frame, d.leaf_l, d.leaf_r
    det = d.detail(fr)
    # ---------------- jambs: stacked stones, alternate courses stand out by 1 px (quoins)
    courses = [(0, 9), (9, 18), (18, 27), (27, 36), (36, 44), (44, 52), (52, 60)]
    for side in (-1, 1):
        X0, X1 = (-32, -26) if side < 0 else (26, 32)
        for k, (y0, y1) in enumerate(courses):
            z = 8 if k % 2 == 0 else 7
            zf = min(z, 7.5) if y1 > 56 else z
            d.box(fr, "jamb_%s_%d" % ("l" if side < 0 else "r", k), X0, X1, y0, y1, -z, zf, side="stone_side")
    # ---------------- arch ring + spandrels, 2 px strips over the whole width
    for s in range(-16, 16):
        X0, X1 = s * STEP, s * STEP + STEP
        xc = (X0 + X1) / 2
        if abs(xc) < 26:
            yin = top_q(xc)
        else:
            yin = 60
        yex = int(round(extrados(xc))) if abs(xc) < R_IN + RING else yin
        yex = max(yin + 2, min(CORNICE[0], yex))
        if abs(xc) <= 5:
            continue   # keystone
        outer = abs(xc) > 26
        zf = 7.5 if outer else 8
        if abs(xc) < 26 and yex > BACK_Y:
            # the back of the arch starts above every leaf top: a leaf swinging backwards (the default) clears it
            d.box(fr, "ring_%d" % (s + 16), X0, X1, yin, yex, -2, zf, side="stone_side")
            d.box(fr, "ring_back_%d" % (s + 16), X0, X1, BACK_Y, yex, -8, -2, side="stone_side")
        elif abs(xc) < 26:
            d.box(fr, "ring_%d" % (s + 16), X0, X1, yin, yex, -2, zf, side="stone_side")
        else:
            d.box(fr, "ring_%d" % (s + 16), X0, X1, yin, yex, -8, zf, side="stone_side")
        if yex < CORNICE[0]:
            if abs(xc) < 26 and yex < BACK_Y:
                d.box(fr, "spandrel_%d" % (s + 16), X0, X1, yex, CORNICE[0], -2, 7, side="stone_side")
                d.box(fr, "spandrel_back_%d" % (s + 16), X0, X1, BACK_Y, CORNICE[0], -7, -2, side="stone_side")
            else:
                d.box(fr, "spandrel_%d" % (s + 16), X0, X1, yex, CORNICE[0], -7, 7, side="stone_side")
    d.box(fr, "keystone", -5, 5, top_q(0) - 1, 91, -2, 8, side="stone_side")
    d.box(fr, "keystone_back", -5, 5, BACK_Y, 91, -8, -2, side="stone_side")
    d.box(fr, "cornice", -32, 32, CORNICE[0], CORNICE[1], -7.5, 7.5, side="stone_side")
    for k, (X0, X1) in enumerate(((-32, -24), (-18, -10), (10, 18), (24, 32))):
        d.box(fr, "merlon_%d" % k, X0, X1, CORNICE[1], 96, -6, 6, side="stone_side")
    d.box(fr, "merlon_c", -4, 4, 91, 96, -6, 6, side="stone_side")
    # ---------------- banners hanging from the cornice in front of the spandrels, braziers on the jambs
    for side in (-1, 1):
        cx = -29.5 * -side if False else (-29.5 if side < 0 else 29.5)
        d.box(det, "banner_rod_%d" % (side > 0), cx - 2.5, cx + 2.5, 83, 84, 7.5, 8.0, side="iron", front="iron", back="iron")
        d.sprite_box(fr, "banner_%d" % (side > 0), cx, 72.5, 5, 21, 7.6, 7.9, "banner")
        # brazier: iron bowl on a bracket, flame drawn full bright
        bx = -30 if side < 0 else 30
        d.box(det, "brazier_arm_%d" % (side > 0), bx - 0.5, bx + 0.5, 22, 26, 6, 8, side="iron", front="iron", back="iron")
        d.box(fr, "brazier_bowl_%d" % (side > 0), bx - 2, bx + 2, 26, 29, 5, 8, side="iron", front="iron", back="iron",
              top="iron_dark")
        d.box(fr, "glow_flame_%d" % (side > 0), bx - 1.5, bx + 1.5, 29, 33, 5.5, 7.5, side="flame", front="flame",
              back="flame", top="flame", glow=True)
    # ---------------- leaves
    for bone, X0, X1, tag in ((L, -26, 0, "l"), (Rr, 0, 26, "r")):
        sgn = -1 if tag == "l" else 1
        d.leaf_strips(bone, "body_" + tag, X0, X1, top_q, STEP, Z0=-1.25, Z1=1.25)
        # front iron (raised to z = 2 px)
        bx0, bx1 = (X0, X1 - 3) if tag == "l" else (X0 + 3, X1)
        for (y0, y1) in ((49, 54), (30, 35)):
            d.box(bone, "band_%s_%d" % (tag, y0), bx0, bx1, y0, y1, 1.25, 1.9, back=None)
        d.box(bone, "plate_" + tag, bx0, bx1, 3, 20, 1.25, 1.75, back=None)
        d.box(bone, "foot_" + tag, bx0, bx1, 0, 3, 1.25, 1.9, back=None)
        sx0, sx1 = (-3, -0.0) if tag == "l" else (0.0, 3)
        d.box(bone, "seam_strap_" + tag, sx0, sx1, 0, top_q(sx0 + 1) - 1, 1.25, 2.0, back=None)
        # studs of the lower plate
        dt = d.detail(bone)
        for row, yy in enumerate((17, 12, 7)):
            for k in range(5):
                cxp = int(round(X0 + (k + 0.5) * 26 / 5))
                if abs(cxp) < 3:
                    continue
                d.box(dt, "stud_%s_%d_%d" % (tag, row, k), cxp - 1, cxp + 1, yy - 1, yy + 1, 1.75, 2.0, back=None,
                      side="iron")
        # ring pull and its plate
        cx = 8 * sgn
        d.box(bone, "ring_plate_" + tag, cx - 1, cx + 1, 43, 45, 1.25, 1.75, back=None)
        d.sprite_box(dt, "ring_" + tag, cx, 40, 6, 6, 1.75, 2.0, "ring")
        # hinge knuckles on the hinge edge, both faces
        hx = X0 if tag == "l" else X1
        for y in (50, 31, 10):
            d.box(bone, "knuckle_%s_%d" % (tag, y), hx - 0.0 if tag == "l" else hx - 1.5, hx + 1.5 if tag == "l" else hx,
                  y - 1, y + 3, -2.0, 2.0, side="iron", front="F", back="iron")
        # back: battens and a diagonal brace, the bolt (heavy bar) near the meeting edge
        for (y0, y1) in ((8, 14), (30, 36), (50, 56)):
            d.box(bone, "batten_%s_%d" % (tag, y0), X0 + 1, X1 - 1, y0, y1, -2.0, -1.25, front=None, side="wood_h")
        p0 = (X0 + 3, 14) if tag == "l" else (X1 - 3, 14)
        p1 = (X1 - 4, 30) if tag == "l" else (X0 + 4, 30)
        d.rbox(bone, "brace_low_" + tag, p0, p1, 4, -2.0, -1.3, "brace", side="wood_h")
        p0 = (X0 + 3, 36) if tag == "l" else (X1 - 3, 36)
        p1 = (X1 - 4, 50) if tag == "l" else (X0 + 4, 50)
        d.rbox(bone, "brace_up_" + tag, p0, p1, 4, -2.0, -1.3, "brace", side="wood_h")
        # the bar slides in two staples
        bxa, bxb = (-12, 0) if tag == "l" else (0, 12)
        bolt = dl.Bone("bolt_%d" % (0 if tag == "l" else 1), origin=((bxa + bxb) / 2 * dl.P, 41.5 * dl.P, -1.6 * dl.P),
                       parent=bone)
        d.box(bolt, "bar_" + tag, bxa + (0.0 if tag == "l" else 0.0), bxb, 40, 43, -2.0, -1.25, front=None,
              back="bar", side="iron")
        for k, sx in enumerate((bxa + 3, bxb - 3) if tag == "l" else (bxa + 3, bxb - 3)):
            d.box(bone, "staple_%s_%d" % (tag, k), sx - 1, sx + 1, 39, 44, -2.0, -1.25, front=None, back="iron",
                  side="iron")


def icon(px, im):
    p = im.load()
    S, SD, SL = rgb("8e8384"), rgb("4a4244"), rgb("b5aaa8")
    W1, W2, IR = rgb("8a4a20"), rgb("5a2c12"), rgb("3a3438")
    for y in range(16):
        for x in range(16):
            p[x, y] = (0, 0, 0, 0)
    for x in range(1, 15):        # parapet
        for y in range(0, 3):
            if y == 2 or x % 4 in (1, 2):
                p[x, y] = S + (255,)
    for y in range(3, 16):         # jambs + arch
        for x in range(1, 15):
            p[x, y] = (S if (x + y) % 5 else SL) + (255,)
    for y in range(5, 16):
        for x in range(3, 13):
            cx = 7.5
            r = math.hypot(x - cx, (y - 9.5) * 1.0)
            if y >= 8 or r < 5.2:
                p[x, y] = (W1 if x % 3 else W2) + (255,)
    for x in range(3, 13):
        for y in (9, 13):
            p[x, y] = IR + (255,)
        p[x, 15] = IR + (255,)
    for y in range(6, 16):
        p[7, y] = rgb("221c1c") + (255,)
        p[8, y] = IR + (255,)
    p[7, 3] = SL + (255,)
    p[8, 3] = SL + (255,)
    for y in range(3, 16):
        p[1, y] = SD + (255,)
        p[14, y] = SD + (255,)
    p[2, 6] = rgb("2a3478") + (255,)
    p[2, 7] = rgb("2a3478") + (255,)
    p[13, 6] = rgb("2a3478") + (255,)
    p[13, 7] = rgb("2a3478") + (255,)


def main():
    d = dl.LargeDoor(NAME, jamb=J, size=256, seed=11)
    dl.standard_materials(d, wood=WOOD, wood_dark=WOOD_D, iron=IRON, stone=STONE)
    d.material("iron_dark", dl.tile_metal(shade(IRON, 0.6)), 16, 16)
    d.material("flame", lambda px: px.glow(0, px.w, 0, px.h, hot=(255, 244, 170), warm=(250, 170, 40), edge=(214, 84, 18)), 16, 16)
    d.sprite("banner", 5, 21, dl.sprite_banner())
    d.sprite("ring", 6, 6, dl.sprite_ring())

    def brace(px):
        px.planks_h(0, px.w, 0, px.h, [px.h], shade(WOOD, 1.05), WOOD_D, outline=WOOD_D)
    d.sprite("brace", 24, 4, brace)

    def bar(px):
        px.metal(0, px.w, 0, px.h, shade(IRON, 1.1))
        px.rivet(1, 0)
        px.rivet(px.w - 3, 0)
    d.sprite("bar", 12, 3, bar)
    paint_front(d)
    paint_back(d)
    build(d)
    d.export(icon=icon)
    if "--preview" in sys.argv:
        C = os.path.join(dl.SCRATCH, "doors_out/crops")
        d.preview(os.path.join(dl.SCRATCH, "doors_out/large_%s.png" % NAME),
                  [os.path.join(C, "chateau_r4.png"), os.path.join(C, "chateau_r5.png")])


if __name__ == "__main__":
    main()
