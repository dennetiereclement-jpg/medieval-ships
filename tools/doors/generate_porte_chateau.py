#!/usr/bin/env python3
"""porte_chateau (1.32.0): the monumental castle gate, 6 high x 4 wide, two massive oak leaves.

References: ref4 "6x4" 1st (round stone arch of big voussoirs with a keystone, orange oak leaves, riveted iron
bands, studded lower plate, iron straps on the meeting edges), ref5 row 3 1st (corner turrets and crenellated
parapet, blue banners, braziers), ref1 top 5th.
Everything inside the 4 x 6 x 1 box. 1.32.0 rules (see doorlib_large.LargeDoor): no air gap anywhere (jointed
voussoir columns 1 px wide, the arch ring overlaps the leaf tops by 1 px in front, the jambs cover the leaf edges
in front and leave a rear rebate for the hinges, the rear arch / soffit is cut exactly above the swept leaves),
no coplanar faces (resolve() + audit on export).

Bones: frame (jambs, arch, soffit, cornice, turrets, banners, braziers), leaf_l / leaf_r (pivots on the hinge edges
X = -/+26 px), handle_0 / handle_1 (the ring pulls, turn about z on their centre), bolt_0 / bolt_1 (the heavy bars on
the back, slide along x), glow_* (brazier flames).

Run: python3 tools/doors/generate_porte_chateau.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_large as dl  # noqa: E402
from doorlib_large import rgb, mix, shade, P, STOP_Z, BODY  # noqa: E402

NAME = "porte_chateau"
J = 6                        # jamb width (px)
YS, RISE = 54, 22            # arch springing line and rise of the intrados (px)
R_IN = (26 ** 2 + RISE ** 2) / (2 * RISE)
YC = YS + RISE - R_IN        # centre of the arch circles
RING = 9                     # voussoir depth (px)
CORNICE = (85, 88)
STEP = 2                     # leaf strips (px)
Z_JAMB = (7.0, 6.25)         # quoins: alternate courses stand out
Z_RING, Z_SPAN, Z_KEY = 7.5, 6.5, 8.0
TURRETS = ((-32, -21), (21, 32))
MERLONS_T = ((-32, -28.5), (-24.5, -21), (21, 24.5), (28.5, 32))   # turret merlons (Y 93 - 96)
MERLONS_C = ((-16, -10), (-3, 3), (10, 16))                        # parapet merlons (Y 90 - 94)
NOTCHES = [(-28.5, -24.5, 93, 96), (24.5, 28.5, 93, 96),           # crenels: silhouette notches open to the top
           (-21, 21, 94, 96),                                      # the parapet stands lower than the turrets
           (-21, -16, 90, 94), (-10, -3, 90, 94), (3, 10, 90, 94), (16, 21, 90, 94)]
COURSES = [(0, 9), (9, 18), (18, 27), (27, 36), (36, 45), (45, 54)]
SHAFT = [(54, 62), (62, 70), (70, 78), (78, 85)]

WOOD = rgb("9a5522")
WOOD_D = rgb("3a1c0c")
IRON = rgb("4a4246")
STONE = rgb("8e8384")
MORTAR = rgb("3a3334")


def strip_top(X):
    """Leaf top of the 2 px strip containing X (strips start at the hinge edge, 26 - GAP)."""
    a = abs(X)
    if a >= 26:
        return YS
    s = math.floor((25.75 - a) / STEP)
    xc = 25.75 - (s + 0.5) * STEP
    if 25.75 - (s + 1) * STEP < 0.25 + 0.6:          # the last strip is narrower (to the seam)
        xc = (25.75 - s * STEP + 0.25) / 2
    return int(round(YC + math.sqrt(max(0.0, R_IN ** 2 - xc ** 2))))


def col_bottom(X):
    """Bottom of the front arch column [X, X+1]: 1 px under the lowest leaf top it covers."""
    return min(strip_top(X + 0.05), strip_top(X + 0.95)) - 1


def front_bottom(X):
    """Bottom of the arch front over column X (the keystone takes the lowest of its columns)."""
    if -4 <= X < 4:
        return min(col_bottom(x) for x in range(-4, 4))
    return col_bottom(X)


def extrados(X):
    xc = X + 0.5
    return int(round(min(CORNICE[0], YC + math.sqrt(max(0.0, (R_IN + RING) ** 2 - xc ** 2)))))


def in_leaf(X, Y):
    """Door pixel (X, Y) shows the leaf (front picture)."""
    return -25 <= X < 25 and Y < front_bottom(X)


# ------------------------------------------------------------------ painting
def paint_masonry(Pc, back=False, sweep_bottom=None):
    st = shade(STONE, 0.94 if back else 1.0)
    # wall courses behind everything (spandrels, turret shafts, soffit)
    for r in range(12):
        y0 = 50 + r * 4
        off = (r % 2) * 3
        X = -32 - off
        while X < 32:
            w = 6 if (X // 6) % 2 else 7
            Pc.stone(*Pc.R(max(-32, X), min(32, X + w), y0, min(96, y0 + 4)), base=shade(st, 0.9), mortar=MORTAR)
            X += w
    # jamb quoins and shaft stones
    for X0, X1 in ((-32, -25), (25, 32)):
        for k, (y0, y1) in enumerate(COURSES + SHAFT):
            Pc.stone(*Pc.R(X0, X1, y0, y1), base=st if k % 2 else shade(st, 1.08), mortar=MORTAR)
    # voussoirs with radial joints (front) / a plainer rear arch (back)
    n_v = 11
    a0, a1 = math.atan2(YS - YC, -26.0), math.atan2(YS - YC, 26.0)
    tones = [shade(st, 1.0 + 0.08 * ((k * 3) % 4 - 1.5) / 1.5) for k in range(n_v)]
    for Y in range(YS - 2, CORNICE[0]):
        for X in range(-25, 25):
            if Y < front_bottom(X) or Y >= extrados(X):
                continue
            xc, yc = X + 0.5, Y + 0.5
            dd = math.hypot(xc, yc - YC)
            ang = math.atan2(yc - YC, xc)
            t = (a0 - ang) / (a0 - a1)
            k = int(min(n_v - 1, max(0, t * n_v)))
            frac = t * n_v - k
            c = tones[k]
            if frac < 0.08 or Y == extrados(X) - 1:
                c = MORTAR
            elif dd < R_IN + 0.3 or frac < 0.18 or Y == front_bottom(X):
                c = mix(c, (232, 226, 222), 0.30)
            elif frac > 0.86:
                c = shade(c, 0.80)
            else:
                rr = Pc.rng.random()
                c = shade(c, 0.88) if rr < 0.16 else mix(c, (225, 218, 215), 0.18) if rr < 0.28 else c
            if back:
                c = shade(c, 0.9)
            Pc.put(Pc.I(X), Pc.J(Y), Pc.jit(c, 4))
    # keystone
    Pc.stone(*Pc.R(-4, 4, front_bottom(0), CORNICE[1] + 1), base=shade(st, 1.14), mortar=MORTAR)
    # cornice (corbel row), turrets, parapet, merlons
    Pc.rect(*Pc.R(-32, 32, CORNICE[0], CORNICE[1]), shade(st, 0.82), noise=4)
    for X in range(-32, 32):
        Pc.put(Pc.I(X), Pc.J(CORNICE[1] - 1), mix(st, (235, 230, 226), 0.35))
        Pc.put(Pc.I(X), Pc.J(CORNICE[0]), rgb("2c2627"))
        if X % 4 == 0:
            Pc.put(Pc.I(X), Pc.J(CORNICE[0] + 1), rgb("2c2627"))
    for X0, X1 in TURRETS:
        for k, (y0, y1) in enumerate(((88, 92), (92, 96))):
            for j, (a, b) in enumerate(((X0, (X0 + X1) // 2), ((X0 + X1) // 2, X1))):
                Pc.stone(*Pc.R(a, b, y0, y1), base=shade(st, 1.05 if (j + k) % 2 else 0.97), mortar=MORTAR)
    Pc.planks_h(*Pc.R(-21, 21, 88, 90), [2], shade(st, 0.95), MORTAR, grain=0.02, knots=0)
    for X0, X1 in MERLONS_C:
        Pc.stone(*Pc.R(X0, X1, 90, 94), base=shade(st, 1.04), mortar=MORTAR)
    for X0, X1, Y0, Y1 in NOTCHES:
        Pc.rect(*Pc.R(X0, X1, Y0, Y1), rgb("2a2526"))
    # slit windows in the turrets
    for X0, X1 in TURRETS:
        cx = (X0 + X1) / 2
        Pc.rect(*Pc.R(cx - 0.5, cx + 0.5, 88, 91), rgb("15100f"))
    if back and sweep_bottom is not None:
        # between the leaf tops and the rear arch the back of the front ring shows: deep shadow
        for X in range(-26, 26):
            for Y in range(front_bottom(X) if -25 <= X < 25 else YS, min(CORNICE[0], sweep_bottom(X))):
                Pc.put(Pc.I(X), Pc.J(Y), shade(Pc.get(Pc.I(X), Pc.J(Y)), 0.55))


def paint_leaves_front(F):
    for X0 in (-26, 0):
        F.planks_v(*F.R(X0, X0 + 26, 0, 80), [5, 4, 4, 4, 4, 5], WOOD, WOOD_D, grain=0.12, knots=0.6, joints=True)
    # iron: bands, studded plate, foot, seam straps / astragal
    for X0, X1 in ((-26, 0), (0, 26)):
        for (y0, y1) in ((50, 55), (31, 36)):
            F.metal(*F.R(X0, X1, y0, y1), IRON)
            i0, i1, j0, j1 = F.R(X0, X1, y0, y1)
            F.rivets_h(i0 + 1, i1 - 1, j0 + 1, 4.4, big=True, light=rgb("e2c890") if y0 == 50 else dl.RIVET_L)
            F.rivets_h(i0 + 1, i1 - 1, j0 + 3, 4.4)
        F.metal(*F.R(X0, X1, 3, 21), shade(IRON, 0.95))
        F.metal(*F.R(X0, X1, 0, 3), shade(IRON, 0.8))
    F.metal(*F.R(-3, -1, 0, 80), shade(IRON, 1.05))
    F.metal(*F.R(-1, 3, 0, 80), shade(IRON, 1.12))
    F.rect(*F.R(-1, 0, 0, 80), rgb("201a1b"))
    i0, i1, j0, j1 = F.R(-3, -1, 0, 76)
    F.rivets_v(i0, j0 + 4, j1 - 2, 6)
    i0, i1, j0, j1 = F.R(0, 3, 0, 76)
    F.rivets_v(i0 + 1, j0 + 4, j1 - 2, 6, big=True)
    for X0 in (-26, 0):
        for yy in (18, 13, 8):
            for k in range(5):
                cxp = int(round(X0 + (k + 0.5) * 26 / 5))
                if abs(cxp) >= 4:
                    F.rivet(F.I(cxp - 1), F.J(yy), big=True)
    for cx in (-8, 8):           # ring plates
        F.metal(*F.R(cx - 1, cx + 1, 44.5, 47), shade(IRON, 0.85))
        F.rivet(F.I(cx - 1), F.J(46), big=False)
    for y in (51, 32, 11):       # hinge straps ends on the hinge edges
        for X0, X1 in ((-26, -23), (23, 26)):
            F.metal(*F.R(X0, X1, y - 1, y + 4), rgb("2e292b"))


def paint_leaves_back(B):
    for X0 in (-26, 0):
        B.planks_v(*B.R(X0, X0 + 26, 0, 80), [5, 4, 4, 4, 4, 5], shade(WOOD, 0.85), WOOD_D, grain=0.1, knots=0.4)
        for (y0, y1) in ((8, 14), (30, 36), (50, 56)):
            B.planks_h(*B.R(X0 + 1, X0 + 25, y0, y1), [6], shade(WOOD, 1.0), WOOD_D, outline=WOOD_D)
    B.rect(*B.R(-1, 1, 0, 80), rgb("1c1718"))


# ------------------------------------------------------------------ geometry
def build_leaves(d):
    L, Rr = d.leaf_l, d.leaf_r
    for bone, tag in ((L, "l"), (Rr, "r")):
        X0, X1 = d.leaf_x(tag)
        sgn = -1 if tag == "l" else 1
        d.leaf_strips(bone, "body_" + tag, X0, X1, strip_top, STEP)
        # front iron, embedded in the body, front at 1.75 (bands / plate) and 2.0 (straps, studs)
        bx0, bx1 = (X0, -3.25) if tag == "l" else (3.25, X1)
        for (y0, y1) in ((50, 55), (31, 36)):
            d.box(bone, "band_%s_%d" % (tag, y0), bx0, bx1, y0, y1, 1.25, 1.75, back=None)
        d.box(bone, "plate_" + tag, bx0, bx1, 3, 21, 1.25, 1.75, back=None)
        d.box(bone, "foot_" + tag, bx0, bx1, 0.25, 3, 1.25, 1.75, back=None)
        if tag == "l":
            d.box(bone, "seam_strap_l", -3, -1, 0.25, strip_top(-2) - 0.5, 1.25, 2.0, back=None)
        else:
            d.box(bone, "seam_strap_r", 0.5, 3, 0.25, strip_top(2) - 0.5, 1.25, 1.75, back=None, front=None)
            d.box(bone, "astragal", -0.75, 3, 0.25, strip_top(1) - 0.5, 1.75, 2.0, back="iron_side")
        dt = d.detail(bone)
        for row, yy in enumerate((18, 13, 8)):
            for k in range(5):
                cxp = int(round(-26 * (tag == "l") + (k + 0.5) * 26 / 5))
                if abs(cxp) < 4:
                    continue
                d.box(dt, "stud_%s_%d_%d" % (tag, row, k), cxp - 1, cxp + 1, yy - 1, yy + 1, 1.5, 2.0, back=None,
                      side="iron")
        # ring pull: its plate on the leaf, the ring on its own bone (turns while unlocking)
        cx = 8 * sgn
        d.box(bone, "ring_plate_" + tag, cx - 1, cx + 1, 44.5, 47, 1.25, 2.0, back=None)
        h = dl.Bone("handle_%d" % (0 if tag == "l" else 1), origin=(cx * P, 41.5 * P, 1.875 * P), parent=bone)
        d.sprite_box(h, "ring_" + tag, cx, 41.5, 5, 5, 1.75, 2.0, "ring")
        # hinge straps / knuckles on the hinge edge (both faces), within the leaf envelope
        hx0, hx1 = (X0, X0 + 3) if tag == "l" else (X1 - 3, X1)
        for y in (51, 32, 11):
            d.box(bone, "knuckle_%s_%d" % (tag, y), hx0, hx1, y - 1, y + 4, -2.0, 2.0, side="iron", front="F",
                  back="iron")
        # back: battens and diagonal braces, the bar (bolt) near the meeting edge
        for (y0, y1) in ((8, 14), (30, 36), (50, 56)):
            d.box(bone, "batten_%s_%d" % (tag, y0), X0 + 3.25 * (tag == "l") + 1, X1 - 1 - 3.25 * (tag == "r"),
                  y0, y1, -2.0, -1.25, front=None, side="wood_h")
        # diagonal braces butting against the battens (never overlapping them)
        p0 = (X0 + 6, 16.75) if tag == "l" else (X1 - 6, 16.75)
        p1 = (X1 - 5, 27.25) if tag == "l" else (X0 + 5, 27.25)
        d.rbox(bone, "brace_low_" + tag, p0, p1, 4, -1.75, -1.25, "brace", side="wood_h")
        p0 = (X0 + 6, 38.75) if tag == "l" else (X1 - 6, 38.75)
        p1 = (X1 - 5, 47.25) if tag == "l" else (X0 + 5, 47.25)
        d.rbox(bone, "brace_up_" + tag, p0, p1, 4, -1.75, -1.25, "brace", side="wood_h")
        bxa, bxb = (-12, -0.5) if tag == "l" else (0.5, 12)
        bolt = dl.Bone("bolt_%d" % (0 if tag == "l" else 1), origin=((bxa + bxb) / 2 * P, 41.5 * P, -1.6 * P),
                       parent=bone)
        d.box(bolt, "bar_" + tag, bxa, bxb, 40, 43, -2.0, -1.25, front=None, back="bar", side="iron")
        for k, sx in enumerate((bxa + 3, bxb - 3)):
            for j, (y0, y1) in enumerate(((38.75, 40), (43, 44.25))):
                d.box(bone, "staple_%s_%d_%d" % (tag, k, j), sx - 1, sx + 1, y0, y1, -2.0, -1.25, front=None,
                      back="iron", side="iron")


def build_frame(d, sw):
    fr = d.frame
    det = d.detail(fr)
    # ---------------- jambs (quoins) + turret shafts, with the stop in front and the rebate behind
    for side in (-1, 1):
        d.jamb_courses(side, COURSES + SHAFT, front_z=Z_JAMB, back_z=Z_JAMB, mat="stone_side")
        # the rear rebate is filled where the swept leaf never goes (above the hinge-side leaf tops)
        a, b = (-26 - dl.REBATE, -26) if side < 0 else (26, 26 + dl.REBATE)
        top = sw.top(a, b, -8, 0)
        y0 = max(0, int(math.ceil(top + 0.5)))
        if y0 < CORNICE[0]:
            d.box(fr, "rebate_fill_%s" % ("l" if side < 0 else "r"), a, b, y0, CORNICE[0], -7.0, 0, side="stone_side")
    # ---------------- arch: front columns 1 px (voussoir ring + spandrel), keystone
    for X in range(-25, 25):
        if -4 <= X < 4:
            continue
        yb, ye = col_bottom(X), extrados(X)
        d.box(fr, "ring_%d" % (X + 25), X, X + 1, yb, ye, STOP_Z, Z_RING, side="stone_side")
        if ye < CORNICE[0]:
            d.box(fr, "span_%d" % (X + 25), X, X + 1, ye, CORNICE[0], STOP_Z, Z_SPAN, side="stone_side")
    d.box(fr, "keystone", -4, 4, front_bottom(0), CORNICE[1] + 1, STOP_Z, Z_KEY, side="stone_side")
    d.sill(mat="stone_side", front="stone_side")
    # ---------------- rear arch (soffit), three depths, cut above the swept leaves, merged columns
    layers = ((0, STOP_Z, -0.0), (-4, 0, 0), (-7.25, -4, 0))
    for li, (z0, z1, _) in enumerate(layers):
        cols = []
        for X in range(-26, 26):
            t = sw.top(X, X + 1, z0, z1)
            yb = max(col_bottom(X) + (0 if li == 0 else 0), int(math.ceil(t + 0.5)) if t >= 0 else col_bottom(X))
            if li == 0:
                yb = max(yb, col_bottom(X) + 1)
            cols.append(min(yb, CORNICE[0] - 1))
        X = -26
        while X < 26:
            Xn = X + 1
            while Xn < 26 and cols[Xn + 26] == cols[X + 26]:
                Xn += 1
            d.box(fr, "soffit_%d_%d" % (li, X + 26), X, Xn, cols[X + 26], CORNICE[0], z0, z1, side="stone_side")
            X = Xn
    # ---------------- cornice, turrets, parapet, merlons
    d.box(fr, "cornice", -32, 32, CORNICE[0], CORNICE[1], -8, 7.75, side="stone_side")
    for k, (X0, X1) in enumerate(TURRETS):
        d.box(fr, "turret_%d" % k, X0, X1, CORNICE[1], 93, -7.75, 8.0, side="stone_side")
    for k, (X0, X1) in enumerate(MERLONS_T):
        d.box(fr, "merlon_t%d" % k, X0, X1, 93, 96, -7.25, 7.5, side="stone_side")
    d.box(fr, "parapet", -21, 21, CORNICE[1], 90, -6, 6, side="stone_side")
    for k, (X0, X1) in enumerate(MERLONS_C):
        d.box(fr, "merlon_c%d" % k, X0, X1, 90, 94, -5.5, 5.5, side="stone_side")
    # corbels under the turrets
    for k, (X0, X1) in enumerate(TURRETS):
        for j, cx in enumerate((X0 + 2, X1 - 2)):
            d.box(det, "corbel_%d_%d" % (k, j), cx - 1, cx + 1, CORNICE[0] - 2, CORNICE[0], 6.0, 7.5,
                  side="stone_side")
    # ---------------- banners on the turret shafts, braziers on the jambs
    for side in (-1, 1):
        cx = 28.5 * side
        tg = "r" if side > 0 else "l"
        d.box(det, "banner_rod_" + tg, cx - 3, cx + 2.75, 82, 83, 7.25, 8.0, side="iron", front="iron", back="iron")
        d.sprite_box(fr, "banner_" + tg, cx, 70.5, 5, 23, 7.5, 7.75, "banner")
        bx = 28.75 * side
        d.box(fr, "brazier_arm_" + tg, bx - 0.75, bx + 0.75, 19, 25.5, 5.5, 7.5, side="iron", front="iron",
              back="iron")
        d.box(fr, "brazier_bowl_" + tg, bx - 3, bx + 3, 25.5, 29, 5.25, 8.0, side="iron_dark",
              front="bowl", back="iron")
        d.box(fr, "glow_embers_" + tg, bx - 2, bx + 2, 29, 30.25, 5.5, 7.5, side="flame", front="flame",
              back="flame", top="flame")
        d.sprite_box(fr, "flame_" + tg, bx, 34.0, 6, 10, 6.75, 7.0, "flame_cut", glow=True)


def icon(px, im):
    p = im.load()
    S, SD, SL = rgb("8e8384"), rgb("4a4244"), rgb("b5aaa8")
    W1, W2, IR = rgb("9a5522"), rgb("5a2c12"), rgb("3a3438")
    for y in range(16):
        for x in range(16):
            p[x, y] = (0, 0, 0, 0)
    for x in range(0, 16):        # turrets + parapet
        for y in range(0, 3):
            tur = x < 4 or x > 11
            if (tur and (y > 0 or x in (0, 1, 3, 12, 14, 15))) or (not tur and (y == 2 or x in (5, 6, 9, 10))):
                p[x, y] = S + (255,)
    for y in range(3, 16):
        for x in range(1, 15):
            p[x, y] = (S if (x + y) % 5 else SL) + (255,)
    for y in range(5, 16):
        for x in range(3, 13):
            r = math.hypot(x - 7.5, (y - 9.5) * 1.0)
            if y >= 9 or r < 5.6:
                p[x, y] = (W1 if x % 3 else W2) + (255,)
    for x in range(3, 13):
        for y in (10, 13):
            p[x, y] = IR + (255,)
        p[x, 15] = IR + (255,)
    for y in range(5, 16):
        p[7, y] = rgb("221c1c") + (255,)
        p[8, y] = IR + (255,)
    p[7, 3] = SL + (255,)
    p[8, 3] = SL + (255,)
    p[1, 5] = rgb("2a3478") + (255,)
    p[1, 6] = rgb("2a3478") + (255,)
    p[14, 5] = rgb("2a3478") + (255,)
    p[14, 6] = rgb("2a3478") + (255,)
    p[1, 9] = rgb("ffc040") + (255,)
    p[14, 9] = rgb("ffc040") + (255,)


def main():
    d = dl.LargeDoor(NAME, jamb=J, size=256, seed=11)
    d.notches = NOTCHES
    dl.standard_materials(d, wood=WOOD, wood_dark=WOOD_D, iron=IRON, stone=STONE)
    d.material("iron_dark", dl.tile_metal(shade(IRON, 0.6)), 16, 16)
    d.material("flame", lambda px: px.glow(0, px.w, 0, px.h, hot=(255, 244, 170), warm=(250, 170, 40),
                                           edge=(214, 84, 18)), 16, 16)
    d.sprite("banner", 5, 23, dl.sprite_banner())
    d.sprite("ring", 5, 5, dl.sprite_ring())

    def bowl(px):
        px.metal(0, px.w, 0, px.h, shade(IRON, 0.9))
        for i in range(0, px.w, 2):
            px.put(i, 0, rgb("8a7a70"))
        px.rect(0, px.w, px.h - 1, px.h, rgb("1e1a1b"))
    d.sprite("bowl", 6, 4, bowl)

    def flame_cut(px):
        px.clear(0, px.w, 0, px.h)
        for j in range(px.h):
            for i in range(px.w):
                t = j / (px.h - 1)                 # 0 top .. 1 bottom
                half = (px.w / 2) * (0.25 + 0.75 * t ** 0.7) * (1 + 0.15 * math.sin(j * 1.9 + i))
                dx = abs(i + 0.5 - px.w / 2 - 0.6 * math.sin(j * 0.9))
                if dx > half or (j < 2 and dx > 0.6):
                    continue
                k = dx / max(0.5, half)
                c = mix((255, 248, 190), (255, 196, 60), min(1, k * 1.3 + (1 - t) * 0.3))
                if k > 0.7 or t < 0.25:
                    c = mix(c, (232, 98, 24), 0.6)
                px.put(i, j, c)
    d.sprite("flame_cut", 6, 10, flame_cut)

    def brace(px):
        px.planks_h(0, px.w, 0, px.h, [px.h], shade(WOOD, 1.05), WOOD_D, outline=WOOD_D)
    d.sprite("brace", 24, 4, brace)

    def bar(px):
        px.metal(0, px.w, 0, px.h, shade(IRON, 1.1))
        px.rivet(1, 0)
        px.rivet(px.w - 3, 0)
    d.sprite("bar", 12, 3, bar)
    build_leaves(d)
    sw = dl.Sweep(d)

    def sweep_bottom(X):
        return int(math.ceil(sw.top(X, X + 1, -8, STOP_Z) + 0.5))
    # pictures: masonry first, the leaves over it where the front shows them
    F, B = d.F, d.B
    paint_masonry(F)
    snap = F.snapshot()
    paint_leaves_front(F)
    leaf_pic = F.snapshot()
    F.restore(snap, lambda X, Y: True)
    F.restore(leaf_pic, lambda X, Y: in_leaf(X, Y) or (-25 <= X < 25 and Y < 3))
    paint_masonry(B, back=True, sweep_bottom=sweep_bottom)
    snapb = B.snapshot()
    paint_leaves_back(B)
    leaf_b = B.snapshot()
    B.restore(snapb, lambda X, Y: True)
    B.restore(leaf_b, lambda X, Y: -26 <= X < 26 and Y < strip_top(X + 0.5))
    build_frame(d, sw)
    d.export(icon=icon)
    if "--preview" in sys.argv:
        C = os.path.join(dl.SCRATCH, "doors_out/crops")
        d.preview(os.path.join(dl.SCRATCH, "doors_out2/large_%s.png" % NAME),
                  [os.path.join(C, "chateau_r4.png"), os.path.join(C, "chateau_r5.png")])


if __name__ == "__main__":
    main()
