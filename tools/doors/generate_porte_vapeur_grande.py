#!/usr/bin/env python3
"""porte_vapeur_grande (1.32.0): the great steam gate, 6 high x 4 wide, two dark steel leaves.

References: ref5 row 3 4th (dark riveted steel plates in panels, glowing grilles, big copper gears and a wheel on
the seam, steel truss header, thick copper pipes up the sides and over the top), ref1 top 5th (gears in the
header, lanterns fed by pipes), ref4 "6x4" 2nd (copper pipes, gauges, glowing top windows).
Everything inside the 4 x 6 x 1 box. 1.32.0 rules (see doorlib_large.LargeDoor): the posts cover the leaf edges in
front and leave a rear rebate for the hinges, the header covers the leaf tops in front and stays above them behind,
the astragal of the right leaf covers the seam, no coplanar faces (resolve() + audit on export).

Bones: frame (+ gear_a_4, gear_b_5, gear_b_6 in the header), leaf_l (gear_a_0, gear_b_1, bolt_0, bolt_1, piston_0),
leaf_r (gear_b_2, gear_a_3, bolt_2, bolt_3, piston_1), glow_* (grilles, lanterns, gauge glass).

Run: python3 tools/doors/generate_porte_vapeur_grande.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_large as dl  # noqa: E402
from doorlib_large import rgb, mix, shade, P, STOP_Z  # noqa: E402

NAME = "porte_vapeur_grande"
J = 6
TOP = 78                         # underside of the header (the leaf tops stop GAP under it)
PLATE, PLATE_D = rgb("342d31"), rgb("1a1618")
STEEL, STEEL_L = rgb("6b6064"), rgb("948789")
STONE = rgb("7d7476")
COP, COP_L, COP_D = rgb("b86a38"), rgb("f4a45a"), rgb("5a2610")
WIN = (-20, -7, 58, 71)          # grille of the left leaf (mirrored on the right)
RAILS = ((0.25, 4), (24, 28), (50, 54), (74, 77.5))
POST_Z = 4.0                     # front of the posts (the pipes stand on them)
PIPE_W, PIPE_X = 4.5, 28.25      # pipe width and centre |x|
SEAL = (1.125, 39, 8)            # the wheel on the seam: centre on the astragal, radius
GEARS = [("gear_a_0", "l", -14.5, 39, 12, 10), ("gear_b_1", "l", -16, 14, 10, 8),
         ("gear_b_2", "r", 15.5, 39, 12, 10), ("gear_a_3", "r", 16, 14, 10, 8),
         ("gear_a_4", "f", 0, 86, 16, 12), ("gear_b_5", "f", -12.5, 85, 10, 8), ("gear_b_6", "f", 12.5, 85, 10, 8)]
NOTCHES = []


def paint_post(Pc, X0, X1):
    """Steel lattice column: two rails and X bracing over dark gaps; a stone plinth."""
    Pc.rect(*Pc.R(X0, X1, 6, TOP), rgb("191517"))
    i0, i1, _, _ = Pc.R(X0, X1, 0, 0)
    for Y in range(6, TOP, 8):
        Pc.line(i0 + 0.5, Pc.J(Y) + 0.5, i1 - 0.5, Pc.J(Y + 8) + 0.5, 1.3, STEEL, 4)
        Pc.line(i1 - 0.5, Pc.J(Y) + 0.5, i0 + 0.5, Pc.J(Y + 8) + 0.5, 1.3, STEEL, 4)
        Pc.metal(*Pc.R(X0, X1, Y, Y + 1), STEEL, bevel=False)
    Pc.metal(*Pc.R(X0, X0 + 1, 6, TOP), STEEL_L, bevel=False)
    Pc.metal(*Pc.R(X1 - 1, X1, 6, TOP), shade(STEEL, 0.8), bevel=False)
    Pc.stone(*Pc.R(X0, X1, 0, 6), base=STONE)


def paint_header(Pc):
    Pc.rect(*Pc.R(-32, 32, TOP - 1, 90), rgb("191517"))
    for X in range(-32, 32, 8):
        i0, i1, j0, j1 = Pc.R(X, X + 8, 80, 90)
        Pc.line(i0 + 0.5, j0 + 0.5, i1 - 0.5, j1 - 0.5, 1.4, STEEL, 4)
        Pc.line(i1 - 0.5, j0 + 0.5, i0 + 0.5, j1 - 0.5, 1.4, STEEL, 4)
        Pc.metal(*Pc.R(X, X + 1, 80, 90), STEEL, bevel=False)
    Pc.metal(*Pc.R(-32, 32, TOP - 1, 80), shade(STEEL, 0.9))
    Pc.metal(*Pc.R(-32, 32, 90, 96), STEEL)
    i0, i1, j0, j1 = Pc.R(-32, 32, 90, 96)
    Pc.rivets_h(i0 + 1, i1 - 1, j0 + 1, 4)
    Pc.rivets_h(i0 + 1, i1 - 1, j0 + 4, 4)
    i0, i1, j0, j1 = Pc.R(-32, 32, TOP - 1, 80)
    Pc.rivets_h(i0 + 1, i1 - 1, j0 + 1, 4)
    Pc.metal(*Pc.R(-18, 18, 80, 90), shade(PLATE, 1.1))
    i0, i1, j0, j1 = Pc.R(-18, 18, 80, 90)
    for (ii, jj) in ((i0 + 1, j0 + 1), (i1 - 3, j0 + 1), (i0 + 1, j1 - 3), (i1 - 3, j1 - 3)):
        Pc.rivet(ii, jj, big=True)


def paint_leaf(Pc, X0, X1, back=False):
    s = -1 if X0 < 0 else 1
    Pc.metal(*Pc.R(X0, X1, 0, TOP), PLATE if not back else shade(PLATE, 0.9), noise=4, rust=0.03)
    if back:
        for (y0, y1) in RAILS:
            Pc.metal(*Pc.R(X0, X1, y0, y1), STEEL)
            i0, i1, j0, j1 = Pc.R(X0, X1, y0, y1)
            Pc.rivets_h(i0 + 2, i1 - 2, j0 + 1, 5)
        Pc.rect(*Pc.R(-1, 1, 0, TOP), rgb("120e10"))
        return
    # raised panels (lighter, bevelled) inside the strap frame
    xa, xb = (X0 + 4, X1 - 4)
    for (y0, y1) in ((4, 24), (28, 50), (54, 74)):
        Pc.metal(*Pc.R(xa + 1, xb - 1, y0 + 1, y1 - 1), shade(PLATE, 1.18), noise=4, rust=0.02)
    # straps: stiles and rails, riveted
    straps = [(X0, X1, y0, y1) for (y0, y1) in RAILS] + [(X0, X0 + 4, 0, TOP), (X1 - 4, X1, 0, TOP)]
    for (a, b, y0, y1) in straps:
        Pc.metal(*Pc.R(a, b, y0, y1), STEEL)
    for (a, b, y0, y1) in straps:
        i0, i1, j0, j1 = Pc.R(a, b, y0, y1)
        if i1 - i0 > j1 - j0:
            Pc.rivets_h(i0 + 2, i1 - 2, j0 + 1, 5)
        else:
            Pc.rivets_v(i0 + 1, j0 + 2, j1 - 2, 5)
    wx0, wx1 = (WIN[0], WIN[1]) if s < 0 else (-WIN[1], -WIN[0])
    Pc.metal(*Pc.R(wx0 - 1, wx1 + 1, WIN[2] - 1, WIN[3] + 1), STEEL_L)
    # the round seat of the seam wheel
    cx, cy, rr = SEAL
    Pc.disc(Pc.pt(cx, cy)[0], Pc.pt(cx, cy)[1], rr + 0.5, shade(PLATE, 0.62))


def paint_astragal(F):
    """The astragal (right leaf, X -0.75 .. 3) shows the middle of the seam wheel."""
    F.metal(*F.R(-1, 3, 0, TOP), shade(STEEL, 1.05))
    F.rect(*F.R(-1, 0, 0, TOP), rgb("1a1517"))
    i0, i1, j0, j1 = F.R(0, 3, 0, TOP)
    F.rivets_v(i0 + 1, j0 + 2, j1 - 2, 5, big=True)
    cx, cy, rr = SEAL
    tmp = dl.np.zeros((2 * rr, 2 * rr, 4))
    dl.sprite_gear(16, base=rgb("c07a38"), light=rgb("f6b868"), dark=rgb("4e260c"), spokes=6)(
        dl.Px(tmp, 0, 0, 2 * rr, 2 * rr, 5))
    for j in range(2 * rr):
        for i in range(2 * rr):
            X = cx - rr + i + 0.5
            Y = cy + rr - j - 0.5
            if -1 <= X < 3 and tmp[j, i, 3] > 0:
                F.put(F.I(math.floor(X)), F.J(math.floor(Y)), tuple(int(v) for v in tmp[j, i, :3]))
    F.disc(F.pt(cx, cy)[0], F.pt(cx, cy)[1], 2.2, dl.BRASS_L, ring=dl.BRASS_D)


def paint_grille(px):
    px.glow(0, px.w, 0, px.h, hot=(255, 232, 140), warm=(246, 156, 40), edge=(190, 90, 20))
    for i in range(0, px.w, 3):
        px.rect(i, i + 1, 0, px.h, rgb("2a2225"))
    for j in range(0, px.h, 3):
        px.rect(0, px.w, j, j + 1, rgb("2a2225"))
    px.outline(0, px.w, 0, px.h, rgb("1c1719"))


def pipe_tile(vertical=True):
    """A thick round copper pipe: highlight a third in, dark rim, faint bands."""
    def paint(px):
        n = px.w if vertical else px.h
        L = px.h if vertical else px.w
        for a in range(n):
            t = (a + 0.5) / n
            if t < 0.14:
                c = mix(COP_D, COP, t / 0.14)
            elif t < 0.38:
                c = mix(COP, COP_L, (t - 0.14) / 0.24)
            elif t < 0.55:
                c = mix(COP_L, COP, (t - 0.38) / 0.17)
            else:
                c = mix(COP, COP_D, (t - 0.55) / 0.45)
            for b in range(L):
                cc = shade(c, 0.86) if b % 12 == 0 else c
                i, j = (a, b) if vertical else (b, a)
                px.put(i, j, px.jit(cc, 3))
    return paint


# ------------------------------------------------------------------ geometry
def build_leaves(d):
    for bone, tag in ((d.leaf_l, "l"), (d.leaf_r, "r")):
        X0, X1 = d.leaf_x(tag)
        s = -1 if tag == "l" else 1
        wx0, wx1 = (WIN[0], WIN[1]) if s < 0 else (-WIN[1], -WIN[0])
        wy0, wy1 = WIN[2], WIN[3]
        d.box(bone, "body_" + tag, X0, X1, dl.GAP, TOP - dl.GAP, -dl.BODY, dl.BODY, side="steel_side")
        d.box(bone, "glow_grille_" + tag, wx0, wx1, wy0, wy1, -1.75, 1.75, side="grille", front="grille",
              back=("grille", True), glow=True)
        for k, (a, b, c0, c1) in enumerate(((wx0 - 1, wx1 + 1, wy0 - 1, wy0), (wx0 - 1, wx1 + 1, wy1, wy1 + 1),
                                            (wx0 - 1, wx0, wy0, wy1), (wx1, wx1 + 1, wy0, wy1))):
            d.box(bone, "grille_frame_%s_%d" % (tag, k), a, b, c0, c1, 1.25, 2.0, back=None, side="steel_side")
        # stiles (front 2.0): the outer one under the post's stop, the inner one stops at the seam wheel
        so0, so1 = (X0 + 0.25, X0 + 4) if s < 0 else (X1 - 4, X1 - 0.25)
        d.box(bone, "stile_out_" + tag, so0, so1, 0.25, TOP - 0.5, 1.25, 2.0, back=None)
        si0, si1 = (-4, -1) if s < 0 else (3.25, 4.25)
        cx, cy, rr = SEAL
        for k, (y0, y1) in enumerate(((0.25, cy - rr - 0.5), (cy + rr + 0.5, TOP - 0.5))):
            if s < 0:
                d.box(bone, "stile_in_%s_%d" % (tag, k), si0, si1, y0, y1, 1.25, 2.0, back=None)
        if s > 0:
            d.box(bone, "seam_strap_r", 0.5, 3, 0.25, TOP - 0.5, 1.25, 1.75, back=None, front=None)
            d.box(bone, "astragal", -0.75, 3, 0.25, TOP - 0.5, 1.75, 2.0, back="steel_side")
        # rails between the stiles (front 1.75) and raised panels (front 1.75 too, never overlapping the rails)
        ra, rb = (X0 + 4.25, -4.25) if s < 0 else (4.5, X1 - 4.25)
        for (y0, y1) in RAILS:
            d.box(bone, "rail_%s_%d" % (tag, int(y0)), ra, rb, max(0.5, y0), min(TOP - 0.75, y1), 1.25, 1.75,
                  back=None)
        # back: straps and diagonal braces
        for (y0, y1) in RAILS:
            d.box(bone, "bstrap_%s_%d" % (tag, int(y0)), X0 + (3.5 if s < 0 else 0.5), X1 - (0.5 if s < 0 else 3.5),
                  max(0.5, y0), min(TOP - 0.75, y1), -2.0, -1.25, front=None)
        d.rbox(bone, "bbrace_" + tag, (X0 + 5, 6) if s < 0 else (X1 - 5, 6), (X1 - 3, 23) if s < 0 else (X0 + 3, 23),
               3, -1.75, -1.25, "steel_bar", side="steel_side")
        d.rbox(bone, "bbrace2_" + tag, (X0 + 5, 30) if s < 0 else (X1 - 5, 30),
               (X1 - 3, 49) if s < 0 else (X0 + 3, 49), 3, -1.75, -1.25, "steel_bar", side="steel_side")
        # the half wheels on the seam (the astragal carries its middle) and their hub caps
        if s < 0:
            d.sprite_box(bone, "seal_l", (cx - rr + -1.0) / 2, cy, -1.0 - (cx - rr), 2 * rr, 1.75, 2.0, "seal_l")
        else:
            d.sprite_box(bone, "seal_r", (3.25 + cx + rr) / 2, cy, cx + rr - 3.25, 2 * rr, 1.75, 2.0, "seal_r")
        # gears
        for name, where, gx, gy, D, teeth in GEARS:
            if where != tag:
                continue
            g = dl.Bone(name, origin=(gx * P, gy * P, 1.875 * P), parent=bone)
            d.sprite_box(g, name + "_wheel", gx, gy, D, D, 1.75, 2.0, "gear%d" % D)
            d.box(bone, name + "_axle", gx - 1.25, gx + 1.25, gy - 1.25, gy + 1.25, 1.25, 1.75, side="brass",
                  front="brass", back=None)
        # piston (housing on the leaf, rod slides up)
        hx = -8.5 if s < 0 else 8.5
        d.box(bone, "piston_cyl_" + tag, hx - 1.75, hx + 1.75, 5, 12, 1.25, 2.0, side="brass", front="cylinder",
              back=None)
        pist = dl.Bone("piston_%d" % (0 if s < 0 else 1), origin=(hx * P, 12 * P, 1.75 * P), parent=bone)
        d.box(pist, "rod_" + tag, hx - 0.75, hx + 0.75, 12, 19.5, 1.25, 1.75, side="rod", front="rod", back=None)
        d.box(pist, "rod_head_" + tag, hx - 1.5, hx + 1.5, 19.5, 21, 1.25, 2.0, side="brass", front="brass",
              back=None)
        # bolts riding on the rails near the meeting edge (slide along x)
        for k, by in enumerate((24.75, 50.75)):
            bx0, bx1 = (-12, -5) if s < 0 else (5.25, 12)
            bolt = dl.Bone("bolt_%d" % ((0 if s < 0 else 2) + k), origin=((bx0 + bx1) / 2 * P, (by + 1.25) * P,
                                                                         1.875 * P), parent=bone)
            d.box(bolt, "bolt_bar_%s_%d" % (tag, k), bx0, bx1, by, by + 2.5, 1.25, 2.0, side="steel_side",
                  front="bolt", back=None)
        # hinge knuckles on the hinge edge (both faces), inside the leaf envelope
        hx0, hx1 = (X0, X0 + 2.5) if s < 0 else (X1 - 2.5, X1)
        for y in (10, 38, 66):
            d.box(bone, "knuckle_%s_%d" % (tag, y), hx0, hx1, y, y + 4, -2.0, -1.25, front=None, side="steel_side")


def build_frame(d, sw):
    fr = d.frame
    det = d.detail(fr)
    for side in (-1, 1):
        tg = "l" if side < 0 else "r"
        d.jamb_courses(side, [(0, 6)], front_z=(8.0,), back_z=(8.0,), mat="stone_side", name="plinth")
        d.jamb_courses(side, [(6, 30), (30, 54), (54, TOP - 1)], front_z=(POST_Z,), back_z=(6.0,),
                       mat="steel_side", name="post")
        a, b = (-26 - dl.REBATE, -26) if side < 0 else (26, 26 + dl.REBATE)
        y0 = max(0, int(math.ceil(sw.top(a, b, -8, 0) + 0.5)))
        if y0 < TOP - 1:
            d.box(fr, "rebate_fill_" + tg, a, b, y0, TOP - 1, -6.0, 0, side="steel_side")
    # header: front part covers the leaf tops (from TOP - 1), back part above the swept leaves (TOP)
    d.sill(mat="steel_side", front="steel_side")
    d.box(fr, "header_low", -32, 32, TOP - 1, 80, STOP_Z, 6.0, side="steel_side")
    d.box(fr, "header_low_b", -32, 32, TOP, 80, -6.0, STOP_Z, side="steel_side")
    d.box(fr, "header_truss", -32, 32, 80, 90, -5.0, 4.5, side="steel_side")
    d.box(fr, "header_top", -32, 32, 90, 96, -6.5, 5.5, side="steel_side")
    d.box(fr, "gear_housing", -18, 18, 80, 90, 4.0, 5.0, side="steel_side", back=None)
    # pipes: plinth -> feed pipe -> valve -> gas lantern -> return pipe -> elbow -> header pipe -> junction
    pv = dict(front="pipe_v", back="pipe_v", left="pipe_v", right="pipe_v", top="copper", bottom="copper")
    ph = dict(front="pipe_h", back="pipe_h", top="pipe_h", bottom="pipe_h", left="copper", right="copper")
    pz0, pz1 = POST_Z - 0.25, 8.0
    for side in (-1, 1):
        tg = "l" if side < 0 else "r"
        cx = PIPE_X * side
        x0, x1 = cx - PIPE_W / 2, cx + PIPE_W / 2
        d.box(fr, "pipe_feed_" + tg, x0, x1, 6, 55, pz0, pz1, **pv)
        d.box(fr, "flange_low_" + tg, x0 - 0.75, x1 + 0.75, 6, 8, pz0 - 0.25, 8.0, side="brass", front="brass",
              back="brass")
        d.box(fr, "flange_mid_" + tg, x0 - 0.75, x1 + 0.75, 30, 32, pz0 - 0.25, 8.0, side="brass", front="brass",
              back="brass")
        d.box(fr, "valve_body_" + tg, x0 - 0.5, x1 + 0.5, 55, 58, pz0 - 0.5, 7.75, side="brass", front="brass",
              back="brass")
        d.lantern(fr, "lantern_" + tg, cx, 62.0, 5.2, w=5.2, h=7.5, metal="iron")
        d.box(fr, "pipe_ret_" + tg, x0, x1, 67.5, 90.75, pz0, pz1, **pv)
        d.box(fr, "flange_top_" + tg, x0 - 0.75, x1 + 0.75, 67.5, 69.5, pz0 - 0.25, 8.0, side="brass",
              front="brass", back="brass")
        d.box(fr, "elbow_" + tg, x0 - 0.5, x1 + 0.5, 90.75, 95.75, pz0 - 0.25, 8.0, side="copper",
              front="elbow", back="copper")
        hx0, hx1 = sorted((x1 if side < 0 else x0, -2.5 * side))
        d.box(fr, "pipe_top_" + tg, hx0, hx1, 91, 95.5, pz0, pz1 - 0.25, **ph)
        # valve wheel on the left pipe, gauge on the right
        if side < 0:
            d.sprite_box(det, "valve_wheel_l", cx, 44, 7, 7, 8.0 - 0.5, 8.0 - 0.25, "vwheel")
        else:
            d.box(fr, "gauge_r", x0 - 0.75, x1 + 0.75, 42, 47.5, pz0, 7.75, side="brass", front="gauge",
                  back="brass")
    d.box(fr, "pipe_junction", -2.5, 2.5, 90.5, 96, pz0 - 0.5, 8.0, side="brass", front="junction", back="brass")
    # header gears (turn while the door moves)
    for name, where, gx, gy, D, teeth in GEARS:
        if where != "f":
            continue
        g = dl.Bone(name, origin=(gx * P, gy * P, 5.375 * P), parent=fr)
        d.sprite_box(g, name + "_wheel", gx, gy, D, D, 5.25, 5.5, "gear%d" % D)
        d.box(fr, name + "_axle", gx - 1.5, gx + 1.5, gy - 1.5, gy + 1.5, 5.0, 6.0, side="brass", front="hub",
              back="brass")


def icon(px, im):
    p = im.load()
    for y in range(16):
        for x in range(16):
            p[x, y] = (0, 0, 0, 0)
    ST, PL, CO, GL, GE = rgb("6a6064"), rgb("3b3337"), rgb("d07e44"), rgb("ffc860"), rgb("d08a3a")
    for y in range(0, 16):
        for x in range(1, 15):
            p[x, y] = (ST if (x in (1, 2, 13, 14) or y < 3) else PL) + (255,)
    for x in range(0, 16):
        p[x, 0] = CO + (255,)
    for y in range(0, 16):
        for x in (0, 1, 14, 15):
            p[x, y] = CO + (255,)
    for y in range(3, 16):
        p[7, y] = rgb("141012") + (255,)
        p[8, y] = rgb("8a7c80") + (255,)
    for (x0, x1) in ((4, 6), (9, 11)):
        for y in (4, 5):
            for x in range(x0, x1 + 1):
                p[x, y] = GL + (255,)
    for cx in (4.5, 11):
        for y in range(7, 13):
            for x in range(16):
                r = math.hypot(x - cx, y - 9.5)
                if 0.9 < r < 2.1 or (2.1 <= r < 2.7 and (x + y) % 2 == 0):
                    if 2 < x < 14:
                        p[x, y] = GE + (255,)
    for x in range(3, 13):
        p[x, 14] = ST + (255,)
    p[7, 1] = GE + (255,)
    p[8, 1] = GE + (255,)
    p[1, 7] = GL + (255,)
    p[14, 7] = GL + (255,)


def main():
    d = dl.LargeDoor(NAME, jamb=J, size=256, seed=23)
    d.notches = NOTCHES
    dl.standard_materials(d, wood=rgb("6a4228"), wood_dark=rgb("2e1c10"), iron=STEEL, stone=STONE)
    d.material("steel_side", dl.tile_metal(shade(STEEL, 0.9), noise=5), 64, 32)
    d.material("copper", dl.tile_metal(COP, noise=6), 16, 16)
    d.material("brass", dl.tile_metal(dl.BRASS, noise=6), 16, 16)
    d.sprite("pipe_v", 5, 16, pipe_tile(True))
    d.sprite("pipe_h", 16, 5, pipe_tile(False))
    d.sprite("grille", 13, 13, paint_grille)
    gc = dict(base=rgb("c07a38"), light=rgb("f6b868"), dark=rgb("4e260c"))
    for D, teeth in ((12, 10), (10, 8), (16, 12)):
        d.sprite("gear%d" % D, D, D, dl.sprite_gear(teeth, spokes=4 if D > 9 else 3, **gc))
    cx, cy, rr = SEAL
    full = dl.sprite_gear(16, spokes=6, **gc)

    def seal_part(x0, x1):
        def paint(px):
            tmp = dl.np.zeros((2 * rr, 2 * rr, 4))
            full(dl.Px(tmp, 0, 0, 2 * rr, 2 * rr, 5))
            i0 = int(round(x0 - (cx - rr)))
            sub = tmp[:, i0:i0 + px.w]
            px.a[px.v0:px.v0 + px.h, px.u0:px.u0 + sub.shape[1]] = sub
        return paint
    wl = int(round(-1.0 - (cx - rr)))
    wr = int(round(cx + rr - 3.25))
    d.sprite("seal_l", wl, 2 * rr, seal_part(cx - rr, -1.0))
    d.sprite("seal_r", wr, 2 * rr, seal_part(3.25, cx + rr))

    def hub(px):
        px.metal(0, px.w, 0, px.h, dl.BRASS_L)
        px.put(1, 1, (40, 30, 20))
    d.sprite("hub", 3, 3, hub)

    def gauge(px):
        px.metal(0, px.w, 0, px.h, dl.BRASS)
        px.disc(px.w / 2, px.h / 2, 2.4, rgb("efe6cf"), ring=dl.BRASS_D)
        px.line(px.w / 2, px.h / 2, px.w / 2 + 1.5, px.h / 2 - 1.2, 0.8, rgb("a01810"))
        px.put(int(px.w / 2), int(px.h / 2), (20, 20, 20))
    d.sprite("gauge", 6, 6, gauge)

    def elbow(px):
        pipe_tile(True)(px)
        px.rect(0, px.w, 0, 1, COP_D)
        px.rect(0, px.w, px.h - 1, px.h, COP_D)
    d.sprite("elbow", 6, 5, elbow)

    def junction(px):
        px.metal(0, px.w, 0, px.h, dl.BRASS)
        px.disc(px.w / 2, px.h / 2, 1.6, rgb("a02018"))
        px.outline(0, px.w, 0, px.h, dl.BRASS_D)
    d.sprite("junction", 5, 5, junction)

    d.sprite("vwheel", 7, 7, dl.sprite_gear(6, base=rgb("b02a1e"), light=rgb("e45a40"), dark=rgb("4a0e08"),
                                             spokes=4))

    def cylinder(px):
        for i in range(px.w):
            c = mix(dl.BRASS_L, dl.BRASS_D, i / max(1, px.w - 1))
            px.rect(i, i + 1, 0, px.h, c, 3)
        px.rect(0, px.w, 0, 1, dl.BRASS_D)
        px.rect(0, px.w, px.h - 1, px.h, dl.BRASS_D)
    d.sprite("cylinder", 4, 7, cylinder)

    def rod(px):
        for i in range(px.w):
            px.rect(i, i + 1, 0, px.h, (210, 210, 214) if i == 0 else (130, 130, 138), 2)
    d.sprite("rod", 2, 8, rod)

    def bolt(px):
        px.metal(0, px.w, 0, px.h, STEEL_L)
        px.rect(px.w - 2, px.w, 0, px.h, dl.BRASS)
    d.sprite("bolt", 7, 3, bolt)

    def steel_bar(px):
        px.metal(0, px.w, 0, px.h, STEEL)
        px.rivets_h(1, px.w - 1, 0, 4)
    d.sprite("steel_bar", 24, 3, steel_bar)
    F, B = d.F, d.B
    for Pc, back in ((F, False), (B, True)):
        paint_post(Pc, -32, -25)
        paint_post(Pc, 25, 32)
        paint_header(Pc)
        paint_leaf(Pc, -26, 0, back)
        paint_leaf(Pc, 0, 26, back)
        if back:
            Pc.rect(*Pc.R(-32, -26, 6, TOP), rgb("2a2427"))
            Pc.rect(*Pc.R(26, 32, 6, TOP), rgb("2a2427"))
            paint_post(Pc, -32, -28)
            paint_post(Pc, 28, 32)
    # the posts' stops cover column -26 / 25 in front: lattice there too
    paint_astragal(F)
    build_leaves(d)
    sw = dl.Sweep(d)
    build_frame(d, sw)
    d.export(icon=icon)
    if "--preview" in sys.argv:
        C = os.path.join(dl.SCRATCH, "doors_out/crops")
        d.preview(os.path.join(dl.SCRATCH, "doors_out2/large_%s.png" % NAME),
                  [os.path.join(C, "vapeur_r5.png"), os.path.join(C, "vapeur_r1.png"), os.path.join(C, "vapeur_r4.png")])


if __name__ == "__main__":
    main()
