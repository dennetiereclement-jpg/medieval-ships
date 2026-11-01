#!/usr/bin/env python3
"""cart_covered_teal — Charrette couverte turquoise / Teal Covered Wagon (reference: scratchpad/ref/cart_covered_teal_ref.png).

a small wagon with a rounded teal canvas cover with gold trim edges, a lantern at the front opening, four wheels, a drawbar.

Usage:  python3 tools/carts/generate_cart_covered_teal.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_covered_teal.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_covered_teal.png,
        carts/cart_covered_teal.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_covered_teal"
HW = 0.82                   # the bed is 1.64 wide
Z0, Z1 = -1.6, 0.95         # back and front of the bed (2.55 long)
BED_Y = 0.92
REAR, FRONT = (-1.0, 0.68), (0.42, 0.52)   # (axle z, wheel radius): big wheels behind, small in front
TRACK = 2 * (HW + 0.19)
WALL_H = 0.42
COVER_Y0, COVER_RISE = BED_Y + 0.3, 1.55
UP = cl.UP


def gear(root, detail):
    g = cl.Bone("gear", parent=root)
    cl.bed(g, "bed", HW, Z0, Z1, BED_Y, region="plank", sill="wood_dark", cross=3)
    sill_bottom = BED_Y - 0.08 - 0.18
    for k, (z, r) in enumerate((REAR, FRONT)):
        cl.wheel_pair(g, "wheel_%d" % k, z, r, TRACK, width=0.2, detail=detail, spokes=10 if k == 0 else 8,
                      segs=14 if k == 0 else 12, hub_d=0.28, hub_len=0.4)
        top = r + 0.07
        cl.add_cube(g, "bolster_%d" % k, (0, (top + sill_bottom) / 2 + 0.02, z), cl.EYE,
                    (2 * HW - 0.1, max(0.1, sill_bottom - top + 0.04), 0.2), {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    cl.add_cube(g, "reach", (0, sill_bottom - 0.06, (REAR[0] + FRONT[0]) / 2), cl.EYE, (0.14, 0.12, FRONT[0] - REAR[0] + 0.3), "wood_dark")
    cl.drawbar(g, "drawbar", Z1 - 0.25, BED_Y - 0.25, length=1.55, x_start=0.36, x_tip=0.2, tip_y=0.42, d=0.13)
    return g


def body_box(body, detail):
    """Low dark plank sides with corner posts, a front wall with a little door under the lantern."""
    for s in (1, -1):
        x = s * (HW - 0.04)
        cl.add_cube(body, "side_%d" % s, (x, BED_Y + WALL_H / 2, (Z0 + Z1) / 2), cl.EYE, (0.07, WALL_H, Z1 - Z0 - 0.04), "plank_dark")
        cl.beam(body, "rail_%d" % s, (x + s * 0.03, BED_Y + WALL_H, Z0), (x + s * 0.03, BED_Y + WALL_H, Z1), 0.09, "wood_dark", width=0.12, up=UP)
        for k, z in enumerate((Z0 + 0.06, (Z0 + Z1) / 2, Z1 - 0.06)):
            cl.post(body, "stake_%d_%d" % (s, k), (x + s * 0.06, BED_Y - 0.25, z), (x + s * 0.06, BED_Y + WALL_H + 0.06, z), d=0.11,
                    region="wood_dark", solid=False)
            cl.add_cube(detail, "strap_%d_%d" % (s, k), (x + s * 0.12, BED_Y + 0.08, z), cl.EYE, (0.02, 0.07, 0.18), "iron")
        cl.collide((min(x, x + s * 0.1) - 0.02, BED_Y, Z0, max(x, x + s * 0.1) + 0.02, BED_Y + WALL_H, Z1))
    cl.add_cube(body, "tailboard", (0, BED_Y + 0.2, Z0 + 0.04), cl.EYE, (2 * HW - 0.1, 0.4, 0.07), "plank_dark")
    cl.collide((-HW, BED_Y, Z0, HW, BED_Y + 0.4, Z0 + 0.12))
    # the front wall inside the opening: planks with a narrow door, framed posts
    zf = Z1 - 0.32
    cl.add_cube(body, "front_wall", (0, BED_Y + 0.55, zf), cl.EYE, (2 * HW - 0.12, 1.1, 0.07), {"all": "plank_dark", "+3": "plank"})
    cl.add_cube(body, "front_door", (-0.18, BED_Y + 0.5, zf + 0.045), cl.EYE, (0.5, 0.95, 0.03), "wood_dark")
    cl.add_cube(detail, "door_ring", (0.0, BED_Y + 0.5, zf + 0.07), cl.EYE, (0.06, 0.06, 0.02), "iron")
    for s in (1, -1):
        cl.post(body, "front_post_%d" % s, (s * (HW - 0.1), BED_Y, zf + 0.05), (s * (HW - 0.1), BED_Y + 1.15, zf + 0.05), d=0.1,
                region="wood_dark", solid=False)
    cl.collide((-HW, BED_Y, zf - 0.05, HW, BED_Y + 1.1, zf + 0.05))
    # footboard and seat plank in front of the wall
    cl.add_cube(body, "seat", (0, BED_Y + 0.38, Z1 - 0.12), cl.EYE, (2 * HW - 0.3, 0.07, 0.3), "plank")
    for s in (1, -1):
        cl.add_cube(body, "seat_leg_%d" % s, (s * (HW - 0.3), BED_Y + 0.18, Z1 - 0.12), cl.EYE, (0.08, 0.36, 0.22), "wood_dark")


def cover(body, detail):
    P = cl.hoop_cover(body, "cover", Z0 - 0.05, Z1 - 0.35, HW + 0.1, COVER_Y0, COVER_RISE, hoops=5, region="canvas_teal",
                      trim="trim_gold", flare=0.22, sag=0.08, flat=0.62, nx=8, detail=detail)
    span = 4
    for j in range(1, span):           # raised panels' seams over the hoops (darker teal bands)
        t = j / span

        def T(sv, u, t=t):
            p = P(sv, t - 0.015 + 0.03 * u)
            out = cl.norm(cl.v3(p[0], p[1] - COVER_Y0, 0))
            return p + out * 0.035
        cl.loft(body, "seam_%d" % j, T, 8, 1, "canvas_teal", th=0.035)
    # gold trim along both lower edges of the cover, with a scalloped fringe of gold tabs
    for s, sv in ((1, 0.0), (-1, 1.0)):
        n = 8
        pts = [P(sv, k / n) + cl.X * s * 0.03 for k in range(n + 1)]
        for k in range(n):
            cl.beam(body, "hem_%d_%d" % (s, k), pts[k], pts[k + 1], 0.12, "trim_gold", width=0.04, up=UP, extend=0.02)
        for k in range(10):
            p = P(sv, 0.05 + k * 0.1) + cl.X * s * 0.035 - UP * 0.1
            cl.add_cube(detail, "tab_%d_%d" % (s, k), p, cl.EYE, (0.03, 0.1 + 0.05 * (k % 2), 0.1), "gold")
    # a wide gold band round the front opening (the bonnet's hem)
    def F(sv, u):
        p = P(sv, 1.0 - 0.07 * u)
        out = cl.norm(cl.v3(p[0], p[1] - COVER_Y0, 0))
        return p + out * 0.045
    cl.loft(body, "front_band", F, 8, 1, "trim_gold", th=0.04)
    return P


def cargo(body, detail):
    c = cl.Bone("cargo", parent=body)
    cl.crate_box(c, "crate_0", (0.35, BED_Y, -1.2), s=0.5, yaw=0.1)
    cl.barrel(c, "barrel", (-0.35, BED_Y, -1.15), r=0.27, h=0.7)
    cl.add_cube(detail, "sack", (0.3, BED_Y + 0.17, -0.55), cl.gg.ry(0.3), (0.38, 0.34, 0.32), "sack", stretch=True)


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    gear(root, detail)
    body = cl.Bone("body", parent=root)
    body_box(body, detail)
    P = cover(body, detail)
    cargo(body, detail)
    # the lantern hanging at the top of the front opening, near side, on an iron bracket from the front hoop
    h = P(0.3, 1.0)
    tip = h + cl.v3(-0.15, -0.05, 0.12)
    cl.beam(detail, "lamp_bracket", h, tip, 0.05, "iron", up=UP)
    cl.lantern(body, "lamp", tip - UP * 0.32, size=0.26, chain_to=tip)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, cover=(47, 143, 138), cover_dark=(30, 98, 94), trim=(222, 178, 52), lantern=True,
                 body=(120, 84, 48), dark=(70, 46, 24))


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
