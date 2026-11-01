#!/usr/bin/env python3
"""cart_market — Charrette de marché / Market Cart (reference: scratchpad/ref/cart_market_ref.png).

a merchant flatbed with a red and white striped awning on four posts, crates of produce, a lantern, a barrel beside it.

Usage:  python3 tools/carts/generate_cart_market.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_market.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_market.png,
        carts/cart_market.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_market"
HW = 0.88                   # the bed is 1.76 wide
Z0, Z1 = -2.0, 1.35         # back and front of the bed (3.35 long)
BED_Y = 0.88
AXLES = (-1.3, 0.62)        # two axles, wheels of the same size
R = 0.62
TRACK = 2 * (HW + 0.19)
SIDE_H = 0.42               # the low slatted sides
AW_Y = BED_Y + 1.95         # the awning's height (front edge a little lower)
UP = cl.UP


def gear(root, detail):
    g = cl.Bone("gear", parent=root)
    cl.bed(g, "bed", HW, Z0, Z1, BED_Y, region="plank", sill="wood_dark", cross=4)
    sill_bottom = BED_Y - 0.08 - 0.18
    for k, z in enumerate(AXLES):
        cl.wheel_pair(g, "wheel_%d" % k, z, R, TRACK, width=0.21, detail=detail, spokes=10, segs=14, hub_d=0.3, hub_len=0.44)
        top = R + 0.07
        cl.add_cube(g, "bolster_%d" % k, (0, (top + sill_bottom) / 2 + 0.02, z), cl.EYE,
                    (2 * HW - 0.1, max(0.1, sill_bottom - top + 0.04), 0.22), {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    cl.add_cube(g, "reach", (0, sill_bottom - 0.06, sum(AXLES) / 2), cl.EYE, (0.15, 0.13, AXLES[1] - AXLES[0] + 0.3), "wood_dark")
    cl.drawbar(g, "drawbar", Z1 - 0.3, BED_Y - 0.25, length=1.7, x_start=0.38, x_tip=0.2, tip_y=0.42, d=0.14)
    # a thick rubbing strake along both sides of the bed
    for s in (1, -1):
        cl.beam(g, "strake_%d" % s, (s * (HW + 0.03), BED_Y - 0.1, Z0 - 0.04), (s * (HW + 0.03), BED_Y - 0.1, Z1 + 0.04), 0.16, "wood",
                width=0.08, up=UP)


def awning(body, detail):
    """Posts (three a side) carrying a flat striped awning (red and white stripes across the cart, i.e. alternating
    along its length) with a straight striped valance on all four sides."""
    xs = HW - 0.07
    zp = (Z0 + 0.07, (Z0 + Z1) / 2 - 0.1, Z1 - 0.07)
    for s in (1, -1):
        for k, z in enumerate(zp):
            top = AW_Y - 0.08 * (z - Z0) / (Z1 - Z0)
            cl.post(body, "aw_post_%d_%d" % (s, k), (s * xs, BED_Y - 0.2, z), (s * xs, top, z), d=0.12, region="wood", solid=True)
        cl.beam(body, "aw_rail_%d" % s, (s * xs, AW_Y - 0.06, Z0 - 0.05), (s * xs, AW_Y - 0.14, Z1 + 0.05), 0.1, "wood_dark", width=0.12, up=UP)
    for k, z in enumerate((Z0 + 0.07, Z1 - 0.07)):
        y = AW_Y - 0.06 - 0.08 * k
        cl.beam(body, "aw_cross_%d" % k, (-xs - 0.06, y, z), (xs + 0.06, y, z), 0.1, "wood_dark", up=UP)
    x0, x1, za, zb = -HW - 0.22, HW + 0.22, Z0 - 0.18, Z1 + 0.3

    def P(sv, t):                      # sv along the cart (stripes alternate along it), t across
        z = za + (zb - za) * sv
        x = x1 + (x0 - x1) * t
        y = AW_Y + 0.04 - 0.1 * sv - 0.05 * math.sin(math.pi * t) * math.sin(math.pi * (sv * 5 % 1.0)) * 0.0
        y -= 0.06 * math.sin(math.pi * t)
        return cl.v3(x, y, z)
    cl.loft(body, "awning", P, 10, 3, "stripes", th=0.04)
    # valance: along both sides and across both ends
    for e, t in (("r", 0.0), ("l", 1.0)):
        def V(sv, u, t=t):
            return P(sv, t) - UP * (0.26 * u)
        cl.loft(body, "valance_" + e, V, 10, 1, "stripes", th=0.035)
    for e, sv in (("b", 0.0), ("f", 1.0)):
        def W(t, u, sv=sv):
            return P(sv, t) - UP * (0.26 * u)
        cl.loft(body, "valance_" + e, W, 4, 1, "stripes", th=0.035)
    cl.collide((x0, AW_Y - 0.2, za, x1, AW_Y + 0.08, zb))
    # the lantern hanging from an iron arm on the front near-side post
    base = cl.v3(xs, AW_Y - 0.45, Z1 - 0.07)
    tip = base + cl.v3(0.12, 0.0, 0.32)
    cl.beam(detail, "lamp_arm", base, tip, 0.05, "iron", up=UP)
    cl.beam(detail, "lamp_brace", base - UP * 0.25, tip - cl.v3(0.06, 0, 0.16), 0.04, "iron", up=UP)
    cl.lantern(body, "lamp", tip - UP * 0.3, size=0.26, chain_to=tip)


def cargo(root, detail):
    c = cl.Bone("cargo", parent=root)
    y = BED_Y
    # crates of produce in two rows, some stacked, a heap of apples in the middle
    layout = ((0.42, -1.55, "apples", 0.05), (-0.42, -1.55, "carrots", -0.06), (0.42, -0.95, "apples", -0.03),
              (-0.42, -0.95, "cabbage", 0.04), (0.42, 0.75, "apples", 0.0), (-0.42, 0.75, "apples", 0.06))
    for k, (x, z, prod, yaw) in enumerate(layout):
        cl.produce_crate(c, "crate_%d" % k, (x, y, z), size=(0.62, 0.36, 0.5), produce=prod, yaw=yaw)
    cl.produce_crate(c, "crate_top_0", (0.4, y + 0.36, -1.5), size=(0.5, 0.3, 0.42), produce="apples", yaw=0.15)
    cl.produce_crate(c, "crate_top_1", (-0.38, y + 0.36, 0.72), size=(0.5, 0.3, 0.42), produce="apples", yaw=-0.12)
    # the middle: a low open bin heaped with apples
    cl.add_cube(c, "bin", (0, y + 0.15, -0.1), cl.EYE, (1.4, 0.3, 0.9), {"all": "crate", "+2": "apples"}, stretch=True)
    cl.add_cube(c, "bin_heap", (0, y + 0.36, -0.1), cl.EYE, (1.15, 0.16, 0.7), "apples", stretch=True)
    cl.add_cube(detail, "bin_heap_top", (0.05, y + 0.48, -0.12), cl.gg.ry(0.3), (0.6, 0.1, 0.4), "apples", stretch=True)
    for k in range(5):
        cl.add_cube(detail, "apple_%d" % k, (-0.5 + 0.25 * k, y + 0.47 + 0.03 * (k % 2), 0.2 - 0.12 * (k % 3)), cl.gg.ry(0.5 * k),
                    (0.1, 0.1, 0.1), "cloth_red")
    cl.collide((-0.7, y, -0.55, 0.7, y + 0.45, 0.35))
    cl.add_cube(detail, "sack", (0.5, y + 0.18, 0.15), cl.gg.ry(0.4), (0.34, 0.36, 0.3), "sack", stretch=True)
    # the barrel standing beside the cart at the front near side, an empty crate by it
    cl.barrel(c, "barrel_side", (HW + 0.85, 0.0, Z1 + 0.35), r=0.36, h=0.92)
    cl.crate_box(c, "side_crate", (HW + 0.7, 0.0, Z1 - 0.45), s=0.48, yaw=0.3)


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    gear(root, detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", HW, Z0, Z1, BED_Y, h=SIDE_H, posts=6, boards=(0.45, 1.0), post_region="wood", region="plank")
    awning(body, detail)
    cargo(root, detail)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, stripes=((176, 38, 30), (236, 228, 212)), cargo=(184, 38, 28), cargo_dark=(110, 160, 60), sides=False,
                 lantern=True)


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
