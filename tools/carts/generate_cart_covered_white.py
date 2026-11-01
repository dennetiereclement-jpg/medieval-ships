#!/usr/bin/env python3
"""cart_covered_white — Charrette couverte blanche / White Covered Wagon (reference: scratchpad/ref/cart_covered_white_ref.png).

a four-wheeled wagon, low sides, a rounded white canvas cover on hoops, two lanterns at the front opening, a drawbar.

Usage:  python3 tools/carts/generate_cart_covered_white.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_covered_white.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_covered_white.png,
        carts/cart_covered_white.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_covered_white"
HW = 1.0                    # the bed is 2.0 wide
Z0, Z1 = -2.5, 1.35         # back and front of the bed (3.85 long)
BED_Y = 1.05                # top of the floor
REAR, FRONT = (-1.6, 0.82), (0.62, 0.64)   # (axle z, wheel radius): big wheels behind, smaller in front
TRACK = 2 * (HW + 0.2)
WALL_H = 0.62               # the plank sides under the cover
COVER_Y0, COVER_RISE = BED_Y + 0.55, 1.65
UP = cl.UP


def gear(root, detail):
    g = cl.Bone("gear", parent=root)
    cl.bed(g, "bed", HW, Z0, Z1, BED_Y, region="plank", sill="wood_dark", cross=4)
    sill_bottom = BED_Y - 0.08 - 0.18
    for k, (z, r) in enumerate((REAR, FRONT)):
        cl.wheel_pair(g, "wheel_%d" % k, z, r, TRACK, width=0.22, detail=detail, spokes=12 if k == 0 else 10,
                      segs=16 if k == 0 else 14, hub_d=0.32, hub_len=0.46)
        top = r + 0.07
        cl.add_cube(g, "bolster_%d" % k, (0, (top + sill_bottom) / 2 + 0.02, z), cl.EYE,
                    (2 * HW - 0.1, max(0.1, sill_bottom - top + 0.04), 0.22), {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
        for s in (1, -1):   # iron stays from the bolster to the axle ends
            cl.beam(detail, "stay_%d_%d" % (k, s), (s * (HW - 0.3), sill_bottom, z), (s * (TRACK / 2 - 0.2), r, z), 0.04, "iron", up=cl.X)
    # the reach pole joining the two axles under the bed
    cl.add_cube(g, "reach", (0, sill_bottom - 0.06, (REAR[0] + FRONT[0]) / 2), cl.EYE, (0.16, 0.14, FRONT[0] - REAR[0] + 0.3), "wood_dark")
    cl.drawbar(g, "drawbar", Z1 - 0.3, BED_Y - 0.25, length=1.9, x_start=0.4, x_tip=0.2, tip_y=0.45, d=0.15)
    return g


def walls(body, detail):
    """Plank sides (dark boards) between heavy posts, a top rail, iron corner straps; a low tailboard."""
    zs = [Z0 + 0.06, Z0 + 0.06 + (Z1 - Z0 - 0.12) * 0.33, Z0 + 0.06 + (Z1 - Z0 - 0.12) * 0.66, Z1 - 0.06]
    for s in (1, -1):
        x = s * (HW - 0.04)
        cl.add_cube(body, "side_%d" % s, (x, BED_Y + WALL_H / 2, (Z0 + Z1) / 2), cl.EYE, (0.07, WALL_H, Z1 - Z0 - 0.04),
                    {"all": "plank_dark", "+1": "plank_dark", "-1": "plank"})
        cl.beam(body, "rail_%d" % s, (x + s * 0.03, BED_Y + WALL_H, Z0), (x + s * 0.03, BED_Y + WALL_H, Z1), 0.1, "wood", width=0.14, up=UP)
        cl.beam(body, "rub_%d" % s, (x + s * 0.06, BED_Y + 0.12, Z0), (x + s * 0.06, BED_Y + 0.12, Z1), 0.12, "wood_dark", width=0.08, up=UP)
        for k, z in enumerate(zs):
            cl.post(body, "stake_%d_%d" % (s, k), (x + s * 0.07, BED_Y - 0.28, z), (x + s * 0.07, BED_Y + WALL_H + 0.08, z), d=0.12,
                    region="wood_dark", solid=False)
            for j, y in enumerate((BED_Y + 0.05, BED_Y + WALL_H - 0.1)):
                cl.add_cube(detail, "strap_%d_%d_%d" % (s, k, j), (x + s * 0.135, y, z), cl.EYE, (0.02, 0.07, 0.2), "iron")
        cl.collide((min(x, x + s * 0.12) - 0.02, BED_Y, Z0, max(x, x + s * 0.12) + 0.02, BED_Y + WALL_H, Z1))
    cl.add_cube(body, "tailboard", (0, BED_Y + 0.25, Z0 + 0.04), cl.EYE, (2 * HW - 0.1, 0.5, 0.07), {"all": "plank_dark"})
    cl.beam(body, "tail_rail", (-HW, BED_Y + 0.5, Z0 + 0.02), (HW, BED_Y + 0.5, Z0 + 0.02), 0.1, "wood", width=0.12, up=UP)
    cl.collide((-HW, BED_Y, Z0, HW, BED_Y + 0.5, Z0 + 0.12))
    # the front board under the driver's seat
    cl.add_cube(body, "dashboard", (0, BED_Y + 0.22, Z1 - 0.05), cl.EYE, (2 * HW - 0.1, 0.44, 0.07), "plank_dark")


def cover(body, detail):
    P = cl.hoop_cover(body, "cover", Z0 - 0.05, Z1 - 0.45, HW + 0.13, COVER_Y0, COVER_RISE, hoops=6, region="canvas",
                      trim="trim_white", flare=0.32, sag=0.07, flat=0.42, nx=8, detail=detail)
    span = 5
    for j in range(1, span):           # raised seams over the hoops
        t = j / span

        def T(sv, u, t=t):
            p = P(sv, t - 0.012 + 0.024 * u)
            out = cl.norm(cl.v3(p[0], p[1] - COVER_Y0, 0))
            return p + out * 0.04
        cl.loft(body, "seam_%d" % j, T, 8, 1, "trim_white", th=0.04)
    # the cloth hangs a little over the sides: a skirt along both lower edges, cut in tabs
    for s, sv in ((1, 0.0), (-1, 1.0)):
        for k in range(10):
            t0, t1 = 0.03 + k * 0.094, 0.03 + k * 0.094 + 0.08
            a, b = P(sv, t0), P(sv, t1)
            cl.add_cube(detail, "skirt_%d_%d" % (s, k), (a + b) / 2 - UP * 0.1 + cl.X * s * 0.01, cl.EYE,
                        (0.03, 0.2 - 0.06 * (k % 2), abs(b[2] - a[2])), "canvas", stretch=True)
    return P


def inside(body, detail, P):
    # driver's bench at the front opening, on two side brackets
    zb = Z1 - 0.55
    cl.add_cube(body, "bench", (0, BED_Y + 0.5, zb), cl.EYE, (2 * HW - 0.2, 0.09, 0.42), {"all": "plank", "+2": "plank"})
    cl.add_cube(body, "bench_back", (0, BED_Y + 0.82, zb - 0.22), cl.gg.rx(-0.15), (2 * HW - 0.2, 0.42, 0.07), "plank_dark")
    for s in (1, -1):
        cl.add_cube(body, "bench_leg_%d" % s, (s * (HW - 0.25), BED_Y + 0.23, zb), cl.EYE, (0.1, 0.46, 0.34), "wood_dark")
    cl.collide((-HW, BED_Y, zb - 0.25, HW, BED_Y + 0.55, zb + 0.21))
    # cargo under the cover: crates, a barrel, sacks
    cargo = cl.Bone("cargo", parent=body)
    cl.crate_box(cargo, "crate_0", (0.45, BED_Y, -1.9), s=0.6, yaw=0.1)
    cl.crate_box(cargo, "crate_1", (0.42, BED_Y + 0.6, -1.85), s=0.48, yaw=-0.15, solid=False)
    cl.crate_box(cargo, "crate_2", (-0.4, BED_Y, -2.0), s=0.55, yaw=-0.08)
    cl.barrel(cargo, "barrel", (-0.45, BED_Y, -1.2), r=0.3, h=0.78)
    cl.add_cube(detail, "sack_0", (0.45, BED_Y + 0.2, -1.2), cl.gg.ry(0.4), (0.42, 0.4, 0.36), "sack", stretch=True)
    cl.add_cube(detail, "sack_1", (0.2, BED_Y + 0.17, -0.6), cl.gg.ry(-0.3), (0.4, 0.34, 0.34), "sack", stretch=True)
    # crates on the front footboard, at the near side (as in the reference)
    cl.crate_box(cargo, "front_crate_0", (0.55, BED_Y, Z1 - 0.2), s=0.42, yaw=0.05, solid=False)
    cl.crate_box(cargo, "front_crate_1", (0.12, BED_Y, Z1 - 0.2), s=0.36, yaw=-0.1, solid=False)
    # two lanterns hanging at the front opening, on iron brackets from the front hoop
    for s, sv in ((1, 0.16), (-1, 0.84)):
        h = P(sv, 1.0)
        tip = h + cl.v3(-s * 0.18, -0.02, 0.1)
        cl.beam(detail, "lamp_bracket_%d" % s, h, tip, 0.05, "iron", up=UP)
        cl.lantern(body, "lamp_%d" % s, tip - UP * 0.3, size=0.24, chain_to=tip)


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    gear(root, detail)
    body = cl.Bone("body", parent=root)
    walls(body, detail)
    P = cover(body, detail)
    inside(body, detail, P)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, cover=(232, 224, 204), cover_dark=(176, 166, 146), trim=(206, 196, 176), lantern=True,
                 body=(120, 84, 48), dark=(70, 46, 24))


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
