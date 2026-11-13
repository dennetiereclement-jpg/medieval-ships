#!/usr/bin/env python3
"""porte_vapeur_grande (1.31.0): the great steam gate, 6 high x 4 wide, two dark steel leaves.

References: ref5 row 3 4th (dark riveted steel plates, glowing grilles, big copper gears, steel truss header,
copper pipes up the sides), ref1 top 5th (gears in the header, lanterns fed by pipes), ref4 "6x4" 2nd (copper pipes,
small gears on the jambs, glowing top windows).
Everything inside the 4 x 6 x 1 box: steel lattice posts 6 px wide on stone plinths, a truss header (Y 78-96) with
three meshing gears, copper pipes (feed pipe -> valve -> gas lantern -> return pipe -> header pipe) on both posts.

Bones: frame (+ gear_a_4, gear_b_5, gear_b_6 in the header), leaf_l (gear_a_0, gear_b_1, bolt_0, bolt_1, piston_0, seal_l half wheel),
leaf_r (gear_b_2, gear_a_3, bolt_2, bolt_3, piston_1, seal_r half wheel), glow_* (grilles, lanterns).

Run: python3 tools/doors/generate_porte_vapeur_grande.py [--preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_large as dl  # noqa: E402
from doorlib_large import rgb, mix, shade, P  # noqa: E402

NAME = "porte_vapeur_grande"
J = 6
TOP = 78                         # underside of the header
PLATE, PLATE_D = rgb("342d31"), rgb("1a1618")
STEEL, STEEL_L = rgb("6b6064"), rgb("948789")
STONE = rgb("7d7476")
COP, COP_L, COP_D = rgb("b4693a"), rgb("ee9a52"), rgb("5e2812")
WIN = (-20, -8, 58, 71)          # grille of the left leaf (mirrored on the right)

# gears: (bone name, leaf, cx, cy, diameter px, teeth)
GEARS = [("gear_a_0", "l", -16, 27, 16, 12), ("gear_b_1", "l", -18, 39.5, 10, 8),
         ("gear_b_2", "r", 16, 27, 16, 12), ("gear_a_3", "r", 18, 39.5, 10, 8),
         ("gear_a_4", "f", 0, 85, 14, 12), ("gear_b_5", "f", -11, 84, 9, 8), ("gear_b_6", "f", 11, 84, 9, 8)]
SEAL = (0, 41, 10)               # the big wheel on the seam (two static halves, one per leaf)
STRAP_Y = ((0, 4), (24, 28), (52, 56), (TOP - 4, TOP))


def paint_post(Pc, X0, X1):
    """Steel lattice column: two rails and X bracing over dark gaps; a stone plinth."""
    Pc.rect(*Pc.R(X0, X1, 6, TOP), rgb("191517"))
    for Y in range(6, TOP, 8):
        Pc.line(Pc.R(X0, X1, 0, 0)[0] + 0.5, Pc.J(Y) + 0.5, Pc.R(X0, X1, 0, 0)[1] - 0.5, Pc.J(Y + 8) + 0.5, 1.3, STEEL, 4)
        Pc.line(Pc.R(X0, X1, 0, 0)[1] - 0.5, Pc.J(Y) + 0.5, Pc.R(X0, X1, 0, 0)[0] + 0.5, Pc.J(Y + 8) + 0.5, 1.3, STEEL, 4)
        Pc.metal(*Pc.R(X0, X1, Y, Y + 1), STEEL, bevel=False)
    Pc.metal(*Pc.R(X0, X0 + 1, 6, TOP), STEEL_L, bevel=False)
    Pc.metal(*Pc.R(X1 - 1, X1, 6, TOP), shade(STEEL, 0.8), bevel=False)
    Pc.stone(*Pc.R(X0, X1, 0, 6), base=STONE)


def paint_header(Pc):
    Pc.rect(*Pc.R(-32, 32, TOP, 90), rgb("191517"))
    for X in range(-32, 32, 8):
        i0, i1, j0, j1 = Pc.R(X, X + 8, 80, 90)
        Pc.line(i0 + 0.5, j0 + 0.5, i1 - 0.5, j1 - 0.5, 1.4, STEEL, 4)
        Pc.line(i1 - 0.5, j0 + 0.5, i0 + 0.5, j1 - 0.5, 1.4, STEEL, 4)
        Pc.metal(*Pc.R(X, X + 1, 80, 90), STEEL, bevel=False)
    Pc.metal(*Pc.R(-32, 32, TOP, 80), shade(STEEL, 0.9))
    Pc.metal(*Pc.R(-32, 32, 90, 96), STEEL)
    i0, i1, j0, j1 = Pc.R(-32, 32, 90, 96)
    Pc.rivets_h(i0 + 1, i1 - 1, j0 + 1, 4, big=False)
    Pc.rivets_h(i0 + 1, i1 - 1, j0 + 4, 4, big=False)
    i0, i1, j0, j1 = Pc.R(-32, 32, TOP, 80)
    Pc.rivets_h(i0 + 1, i1 - 1, j0, 4, big=False)
    # gear housing plate behind the header gears
    Pc.metal(*Pc.R(-9, 9, 80, 90), shade(PLATE, 1.1))
    i0, i1, j0, j1 = Pc.R(-9, 9, 80, 90)
    for (ii, jj) in ((i0 + 1, j0 + 1), (i1 - 3, j0 + 1), (i0 + 1, j1 - 3), (i1 - 3, j1 - 3)):
        Pc.rivet(ii, jj, big=True)


def paint_leaf(Pc, X0, X1, back=False):
    s = -1 if X0 < 0 else 1
    Pc.metal(*Pc.R(X0, X1, 0, TOP), PLATE if not back else shade(PLATE, 0.9), noise=4, rust=0.03)
    for y in (14, 40, 66):
        Pc.rect(*Pc.R(X0, X1, y, y + 1), PLATE_D)
    for x in ((X0 + 13,) if True else ()):
        Pc.rect(*Pc.R(x, x + 1, 0, TOP), PLATE_D)
    straps = [(X0, X1, y0, y1) for (y0, y1) in STRAP_Y]
    straps += [(X0, X0 + 4, 0, TOP), (X1 - 4, X1, 0, TOP)]
    for (a, b, y0, y1) in straps:
        Pc.metal(*Pc.R(a, b, y0, y1), STEEL)
    for (a, b, y0, y1) in straps:
        i0, i1, j0, j1 = Pc.R(a, b, y0, y1)
        if i1 - i0 > j1 - j0:
            Pc.rivets_h(i0 + 2, i1 - 2, j0 + 1, 5)
        else:
            Pc.rivets_v(i0 + 1, j0 + 2, j1 - 2, 5)
    Pc.rect(*Pc.R(-1, 1, 0, TOP), rgb("120e10"))
    if back:
        return
    wx0, wx1 = (WIN[0], WIN[1]) if s < 0 else (-WIN[1], -WIN[0])
    Pc.metal(*Pc.R(wx0 - 1, wx1 + 1, WIN[2] - 1, WIN[3] + 1), STEEL_L)
    # dark round seat behind the seam wheel
    Pc.disc(Pc.I(0) + (0 if s > 0 else 1), Pc.J(SEAL[1]) + 0.5, SEAL[2] - 1, shade(PLATE, 0.7))


def paint_grille(px):
    px.glow(0, px.w, 0, px.h, hot=(255, 232, 140), warm=(246, 156, 40), edge=(190, 90, 20))
    for i in range(0, px.w, 3):
        px.rect(i, i + 1, 0, px.h, rgb("2a2225"))
    for j in range(0, px.h, 3):
        px.rect(0, px.w, j, j + 1, rgb("2a2225"))
    px.outline(0, px.w, 0, px.h, rgb("1c1719"))


def build(d):
    fr, L, Rr = d.frame, d.leaf_l, d.leaf_r
    det = d.detail(fr)
    # ---------------- posts, plinths, header
    for side, (X0, X1) in (("l", (-32, -26)), ("r", (26, 32))):
        d.box(fr, "plinth_" + side, X0, X1, 0, 6, -8, 8, side="stone_side")
        d.box(fr, "post_" + side, X0, X1, 6, TOP, -6, 5, side="steel_side")
    d.box(fr, "header_low", -32, 32, TOP, 80, -6, 5, side="steel_side")
    d.box(fr, "header_truss", -32, 32, 80, 90, -5, 4, side="steel_side")
    d.box(fr, "header_top", -32, 32, 90, 96, -6, 5, side="steel_side")
    d.box(fr, "gear_housing", -9, 9, 80, 90, 4, 5, side="steel_side", back=None)
    # ---------------- pipes: feed -> valve -> lantern -> return -> header pipe
    for side in ("l", "r"):
        sg = -1 if side == "l" else 1
        px0, px1 = (-31.75, -28.75) if side == "l" else (28.75, 31.75)
        pz0, pz1 = 5, 8
        pipe = dict(front="pipe_v", back="pipe_v", left="pipe_v", right="pipe_v", top="copper", bottom="copper")
        d.box(fr, "pipe_feed_" + side, px0, px1, 6, 56, pz0, pz1, **pipe)
        d.box(fr, "valve_" + side, px0 - 0.5, px1 + 0.5, 56, 59, 5, 8, side="brass", front="valve", back="brass")
        d.lantern(fr, "lantern_" + side, (px0 + px1) / 2 - 0.25 * sg, 62, 6.1, w=3.6, h=5.2, metal="iron")
        d.box(fr, "pipe_ret_" + side, px0, px1, 68, 92, pz0, pz1, **pipe)
        d.box(det, "flange_ret_" + side, px0 - 0.4, px1 + 0.4, 68, 69.5, 5.2, 8, side="brass", front="brass", back="brass")
        d.box(det, "flange_feed_" + side, px0 - 0.4, px1 + 0.4, 30, 31.5, 5.2, 8, side="brass", front="brass", back="brass")
        d.box(fr, "elbow_" + side, px0 - 0.5 if side == "l" else px0, px1 if side == "l" else px1 + 0.5, 92, 95, 5.2, 8,
              side="copper", front="copper", back="copper")
        hx0, hx1 = (px1, -2) if side == "l" else (2, px0)
        d.box(fr, "pipe_top_" + side, hx0, hx1, 92, 95, pz0, pz1, front="pipe_h", back="pipe_h", top="pipe_h",
              bottom="pipe_h", left="copper", right="copper")
        # gauge on the right post, wheel valve on the left
        if side == "r":
            d.box(det, "gauge", 28.5, 31.5, 44, 47, 5, 6.5, side="brass", front="gauge", back="brass")
    d.box(fr, "pipe_junction", -2, 2, 91.5, 95.5, 5, 8, side="brass", front="brass", back="brass")
    # ---------------- header gears (turn while the door moves)
    for name, where, cx, cy, D, teeth in GEARS:
        if where != "f":
            continue
        g = dl.Bone(name, origin=(cx * P, cy * P, 5.6 * P), parent=fr)
        d.sprite_box(g, name + "_wheel", cx, cy, D, D, 5.0, 5.6, "gear%d" % D)
        d.box(g, name + "_hub", cx - 1.5, cx + 1.5, cy - 1.5, cy + 1.5, 5.0, 6.4, side="brass", front="hub", back="brass")
    # ---------------- leaves
    for bone, X0, X1, tag in ((L, -26, 0, "l"), (Rr, 0, 26, "r")):
        s = -1 if tag == "l" else 1
        wx0, wx1 = (WIN[0], WIN[1]) if s < 0 else (-WIN[1], -WIN[0])
        wy0, wy1 = WIN[2], WIN[3]
        z0, z1 = -1.25, 1.25
        side = "steel_side"
        d.box(bone, "body_low_" + tag, X0, X1, 0, wy0, z0, z1, side=side)
        d.box(bone, "body_up_" + tag, X0, X1, wy1, TOP, z0, z1, side=side)
        d.box(bone, "body_a_" + tag, X0, wx0, wy0, wy1, z0, z1, side=side)
        d.box(bone, "body_b_" + tag, wx1, X1, wy0, wy1, z0, z1, side=side)
        d.box(bone, "glow_grille_" + tag, wx0, wx1, wy0, wy1, -0.75, 0.75, side="grille", front="grille",
              back=("grille", True), glow=True)
        for k, (a, b, c0, c1) in enumerate(((wx0 - 1, wx1 + 1, wy0 - 1, wy0), (wx0 - 1, wx1 + 1, wy1, wy1 + 1),
                                            (wx0 - 1, wx0, wy0, wy1), (wx1, wx1 + 1, wy0, wy1))):
            d.box(bone, "grille_frame_%s_%d" % (tag, k), a, b, c0, c1, 1.25, 1.75, back=None, side="steel_side")
        # straps (front, raised), back straps
        d.box(bone, "strap_out_" + tag, X0, X0 + 4, 0, TOP, 1.25, 1.7, back=None)
        d.box(bone, "strap_in_" + tag, X1 - 4, X1, 0, TOP, 1.25, 1.7, back=None)
        for (y0, y1) in STRAP_Y:
            d.box(bone, "strap_%s_%d" % (tag, y0), X0 + 4, X1 - 4, y0, y1, 1.25, 1.6, back=None)
            d.box(bone, "bstrap_%s_%d" % (tag, y0), X0, X1, y0, y1, -1.7, -1.25, front=None)
        # half of the seam wheel (static) with its hub quarter
        cx, cy, rr = SEAL
        d.box(bone, "seal_" + tag, 0 if s > 0 else -rr, rr if s > 0 else 0, cy - rr, cy + rr, 1.7, 1.95, side=None,
              front="seal_" + tag, back=("seal_" + tag, True))
        d.box(bone, "seal_hub_" + tag, -2 if s < 0 else 0, 0 if s < 0 else 2, cy - 2, cy + 2, 1.6, 2.0, side="brass",
              front="brass", back=None)
        d.rbox(bone, "bbrace_" + tag, (X0 + 3, 4) if s < 0 else (X1 - 3, 4), (X1 - 3, 25) if s < 0 else (X0 + 3, 25),
               3, -1.7, -1.25, "steel_bar", side="steel_side")
        d.rbox(bone, "bbrace2_" + tag, (X0 + 3, 30) if s < 0 else (X1 - 3, 30), (X1 - 3, 51) if s < 0 else (X0 + 3, 51),
               3, -1.7, -1.25, "steel_bar", side="steel_side")
        # gears
        for name, where, cx, cy, D, teeth in GEARS:
            if where != tag:
                continue
            g = dl.Bone(name, origin=(cx * P, cy * P, 1.85 * P), parent=bone)
            d.sprite_box(g, name + "_wheel", cx, cy, D, D, 1.7, 1.95, "gear%d" % D)
            hs = 1.5 if D > 10 else 1.0
            d.box(g, name + "_hub", cx - hs, cx + hs, cy - hs, cy + hs, 1.7, 2.0, side="brass", front="hub",
                  back="brass")
        # piston (housing on the leaf, rod slides up)
        hx = -22 if s < 0 else 22
        d.box(bone, "piston_cyl_" + tag, hx - 2, hx + 2, 4, 11, 1.6, 2.0, side="brass", front="cylinder", back=None)
        pist = dl.Bone("piston_%d" % (0 if s < 0 else 1), origin=(hx * P, 11 * P, 1.75 * P), parent=bone)
        d.box(pist, "rod_" + tag, hx - 0.75, hx + 0.75, 11, 15, 1.6, 1.9, side="rod", front="rod", back=None)
        d.box(pist, "rod_head_" + tag, hx - 1.5, hx + 1.5, 15, 16.5, 1.6, 2.0, side="brass", front="brass", back=None)
        # bolts at the meeting edge (slide along x), staples
        for k, by in enumerate((10, 62)):
            bx0, bx1 = (-9, -0.5) if s < 0 else (0.5, 9)
            bolt = dl.Bone("bolt_%d" % ((0 if s < 0 else 2) + k), origin=((bx0 + bx1) / 2 * P, (by + 1.5) * P, 1.85 * P),
                           parent=bone)
            d.box(bolt, "bolt_bar_%s_%d" % (tag, k), bx0, bx1, by, by + 3, 1.7, 2.0, side="steel_side", front="bolt",
                  back=None)
            sx0 = -8 if s < 0 else 6
            d.box(bone, "keeper_%s_%d" % (tag, k), sx0, sx0 + 2, by - 1, by + 4, 1.25, 1.65, back=None, side="steel_side")


def icon(px, im):
    p = im.load()
    for y in range(16):
        for x in range(16):
            p[x, y] = (0, 0, 0, 0)
    ST, PL, CO, GL, GE = rgb("6a6064"), rgb("3b3337"), rgb("c87a40"), rgb("ffc860"), rgb("d08a3a")
    for y in range(0, 16):
        for x in range(1, 15):
            p[x, y] = (ST if (x in (1, 2, 13, 14) or y < 3) else PL) + (255,)
    for x in range(1, 15):
        p[x, 0] = CO + (255,)
    for y in range(0, 15):
        p[1, y] = CO + (255,)
        p[14, y] = CO + (255,)
    for y in range(3, 16):
        p[7, y] = rgb("141012") + (255,)
        p[8, y] = rgb("141012") + (255,)
    for (x0, x1) in ((4, 6), (9, 11)):
        for y in (4, 5):
            for x in range(x0, x1 + 1):
                p[x, y] = GL + (255,)
    for cx in (4.5, 10.5):
        for y in range(7, 13):
            for x in range(16):
                r = math.hypot(x - cx, y - 9.5)
                if 0.9 < r < 2.1 or (2.1 <= r < 2.7 and (x + y) % 2 == 0):
                    p[x, y] = GE + (255,)
    for x in range(3, 13):
        p[x, 14] = ST + (255,)
    p[7, 1] = GE + (255,)
    p[8, 1] = GE + (255,)
    p[2, 6] = GL + (255,)
    p[13, 6] = GL + (255,)


def main():
    d = dl.LargeDoor(NAME, jamb=J, size=256, seed=23)
    dl.standard_materials(d, wood=rgb("6a4228"), wood_dark=rgb("2e1c10"), iron=STEEL, stone=STONE)
    d.material("steel_side", dl.tile_metal(shade(STEEL, 0.9), noise=5), 64, 32)
    d.material("copper", dl.tile_metal(COP, noise=6), 16, 16)
    d.material("brass", dl.tile_metal(dl.BRASS, noise=6), 16, 16)
    d.sprite("pipe_v", 3, 16, dl.tile_copper(COP, COP_L, COP_D, vertical=True))
    d.sprite("pipe_h", 16, 3, dl.tile_copper(COP, COP_L, COP_D, vertical=False))
    d.sprite("grille", 12, 13, paint_grille)
    gc = dict(base=rgb("c07a38"), light=rgb("f6b868"), dark=rgb("4e260c"))
    for D, teeth in ((16, 12), (10, 8), (9, 8), (14, 12)):
        d.sprite("gear%d" % D, D, D, dl.sprite_gear(teeth, spokes=4 if D > 9 else 3, **gc))
    d.sprite("seal_l", SEAL[2], 2 * SEAL[2], dl.sprite_half_wheel(-1, 16, spokes=6, **gc))
    d.sprite("seal_r", SEAL[2], 2 * SEAL[2], dl.sprite_half_wheel(1, 16, spokes=6, **gc))

    def hub(px):
        px.metal(0, px.w, 0, px.h, dl.BRASS_L)
        px.put(1, 1, (40, 30, 20))
    d.sprite("hub", 3, 3, hub)

    def valve(px):
        px.metal(0, px.w, 0, px.h, dl.BRASS)
        px.disc(px.w / 2, px.h / 2, 1.4, rgb("a02018"))
    d.sprite("valve", 4, 3, valve)

    def gauge(px):
        px.disc(1.5, 1.5, 1.6, rgb("efe6cf"), ring=dl.BRASS_D)
        px.put(1, 1, (20, 20, 20))
        px.put(2, 0, (160, 20, 20))
    d.sprite("gauge", 3, 3, gauge)

    def cylinder(px):
        for i in range(px.w):
            c = mix(dl.BRASS_L, dl.BRASS_D, i / max(1, px.w - 1))
            px.rect(i, i + 1, 0, px.h, c, 3)
        px.rect(0, px.w, 0, 1, dl.BRASS_D)
        px.rect(0, px.w, px.h - 1, px.h, dl.BRASS_D)
    d.sprite("cylinder", 4, 9, cylinder)

    def rod(px):
        for i in range(px.w):
            px.rect(i, i + 1, 0, px.h, (210, 210, 214) if i == 0 else (130, 130, 138), 2)
    d.sprite("rod", 2, 8, rod)

    def bolt(px):
        px.metal(0, px.w, 0, px.h, STEEL_L)
        px.rect(px.w - 2, px.w, 0, px.h, dl.BRASS)
    d.sprite("bolt", 9, 3, bolt)

    def steel_bar(px):
        px.metal(0, px.w, 0, px.h, STEEL)
        px.rivets_h(1, px.w - 1, 0, 4)
    d.sprite("steel_bar", 24, 3, steel_bar)
    F, B = d.F, d.B
    for Pc, back in ((F, False), (B, True)):
        paint_post(Pc, -32, -26)
        paint_post(Pc, 26, 32)
        paint_header(Pc)
        paint_leaf(Pc, -26, 0, back)
        paint_leaf(Pc, 0, 26, back)
    build(d)
    d.export(icon=icon)
    if "--preview" in sys.argv:
        C = os.path.join(dl.SCRATCH, "doors_out/crops")
        d.preview(os.path.join(dl.SCRATCH, "doors_out/large_%s.png" % NAME),
                  [os.path.join(C, "vapeur_r5.png"), os.path.join(C, "vapeur_r1.png"), os.path.join(C, "vapeur_r4.png")])


if __name__ == "__main__":
    main()
