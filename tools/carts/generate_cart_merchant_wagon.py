#!/usr/bin/env python3
"""cart_merchant_wagon — Roulotte de marchand / Merchant Wagon (reference: scratchpad/ref/cart_merchant_wagon_ref.png).

a small house on four wheels: dark red plank walls with gold trim, a curved red roof, lit windows, a door and steps at the back, lanterns, a drawbar.

Usage:  python3 tools/carts/generate_cart_merchant_wagon.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_merchant_wagon.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_merchant_wagon.png,
        carts/cart_merchant_wagon.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_merchant_wagon"
HW = 0.95                   # the house is 1.9 wide
Z0, Z1 = -1.85, 1.2         # back and front walls (3.05 long); the door and its steps at the front (+z)
BED_Y = 1.0                 # floor of the house
REAR, FRONT = (-1.15, 0.74), (0.62, 0.56)  # (axle z, wheel radius)
TRACK = 2 * (HW + 0.2)
WALL_H = 1.5
EAVE = BED_Y + WALL_H
UP = cl.UP
WIN_Z, WIN_W, WIN_H, WIN_Y = -0.45, 0.72, 0.58, BED_Y + 0.62   # side windows (centre z, width, height, sill)


def gear(root, detail):
    g = cl.Bone("gear", parent=root)
    cl.bed(g, "bed", HW + 0.06, Z0 - 0.08, Z1 + 0.38, BED_Y, region="plank_dark", sill="wood_dark", cross=4)
    sill_bottom = BED_Y - 0.08 - 0.18
    for k, (z, r) in enumerate((REAR, FRONT)):
        cl.wheel_pair(g, "wheel_%d" % k, z, r, TRACK, width=0.22, detail=detail, spokes=12 if k == 0 else 10,
                      segs=16 if k == 0 else 14, hub_d=0.3, hub_len=0.44, region="wood", spoke_region="wood")
        top = r + 0.07
        cl.add_cube(g, "bolster_%d" % k, (0, (top + sill_bottom) / 2 + 0.02, z), cl.EYE,
                    (2 * HW - 0.1, max(0.1, sill_bottom - top + 0.04), 0.22), {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    cl.add_cube(g, "reach", (0, sill_bottom - 0.06, (REAR[0] + FRONT[0]) / 2), cl.EYE, (0.16, 0.14, FRONT[0] - REAR[0] + 0.3), "wood_dark")
    # a gold-painted skirting board round the floor
    for s in (1, -1):
        cl.add_cube(g, "skirt_%d" % s, (s * (HW + 0.07), BED_Y - 0.1, (Z0 + Z1) / 2 + 0.15), cl.EYE, (0.04, 0.14, Z1 - Z0 + 0.46), "gold")


def frame_rect(bone, name, x, zc, w, yb, h, s, region="gold", d=0.07):
    """A flat rectangular frame on the wall at x (facing s), centred on zc, from yb to yb + h."""
    xo = x + s * 0.04
    for k, (a, b) in enumerate((((zc - w / 2, yb), (zc + w / 2, yb)), ((zc - w / 2, yb + h), (zc + w / 2, yb + h)),
                                ((zc - w / 2, yb), (zc - w / 2, yb + h)), ((zc + w / 2, yb), (zc + w / 2, yb + h)))):
        cl.beam(bone, "%s_%d" % (name, k), (xo, a[1], a[0]), (xo, b[1], b[0]), d, region, width=0.05, up=cl.X * s, extend=d / 2)


def house(body, detail):
    """Dark-red plank walls framed with gold-painted pilasters and bands; windows with open red shutters and
    flower boxes on both sides; a door at the front between two lanterns; a small window at the back."""
    zc, L = (Z0 + Z1) / 2, Z1 - Z0
    for s in (1, -1):
        x = s * HW
        # wall around the window: below, above, and the two side parts
        za, zb = WIN_Z - WIN_W / 2, WIN_Z + WIN_W / 2
        cl.add_cube(body, "wall_low_%d" % s, (x, (BED_Y + WIN_Y) / 2, zc), cl.EYE, (0.08, WIN_Y - BED_Y, L), "red_plank")
        cl.add_cube(body, "wall_high_%d" % s, (x, (WIN_Y + WIN_H + EAVE) / 2, zc), cl.EYE, (0.08, EAVE - WIN_Y - WIN_H, L), "red_plank")
        cl.add_cube(body, "wall_back_%d" % s, (x, WIN_Y + WIN_H / 2, (Z0 + za) / 2), cl.EYE, (0.08, WIN_H, za - Z0), "red_plank")
        cl.add_cube(body, "wall_front_%d" % s, (x, WIN_Y + WIN_H / 2, (zb + Z1) / 2), cl.EYE, (0.08, WIN_H, Z1 - zb), "red_plank")
        cl.add_cube(body, "glow_window_%d" % s, (x - s * 0.01, WIN_Y + WIN_H / 2, WIN_Z), cl.EYE, (0.04, WIN_H, WIN_W), "glass")
        frame_rect(body, "win_frame_%d" % s, x, WIN_Z, WIN_W + 0.06, WIN_Y - 0.03, WIN_H + 0.06, s)
        cl.beam(detail, "win_mullion_%d" % s, (x + s * 0.03, WIN_Y, WIN_Z), (x + s * 0.03, WIN_Y + WIN_H, WIN_Z), 0.04, "wood_dark", width=0.04, up=cl.X)
        cl.beam(detail, "win_bar_%d" % s, (x + s * 0.03, WIN_Y + WIN_H / 2, za), (x + s * 0.03, WIN_Y + WIN_H / 2, zb), 0.04, "wood_dark", width=0.04, up=UP)
        # shutters, opened out a little
        for e, z_h in ((-1, za - 0.04), (1, zb + 0.04)):
            ang = 0.35 * e * s
            R = cl.gg.ry(ang)
            c = cl.v3(x + s * 0.1, WIN_Y + WIN_H / 2, z_h + e * WIN_W / 4 + e * 0.03)
            cl.add_cube(body, "shutter_%d_%d" % (s, e), c, R, (0.05, WIN_H + 0.08, WIN_W / 2), {"all": "gold", "+1": "red_paint", "-1": "red_paint"})
            for j, dy in enumerate((-0.18, 0.18)):
                cl.add_cube(detail, "shutter_trim_%d_%d_%d" % (s, e, j), c + cl.X * s * 0.03 + UP * dy, R, (0.02, 0.05, WIN_W / 2 - 0.04), "gold")
            cl.add_cube(detail, "shutter_edge_%d_%d" % (s, e), c + cl.X * s * 0.03, R, (0.02, WIN_H + 0.08, 0.05), "gold")
        # flower box under the window
        fb = cl.v3(x + s * 0.16, WIN_Y - 0.14, WIN_Z)
        cl.add_cube(body, "flower_box_%d" % s, fb, cl.EYE, (0.2, 0.18, WIN_W + 0.3), {"all": "plank", "+2": "flowers"})
        cl.add_cube(detail, "flowers_%d" % s, fb + UP * 0.13, cl.EYE, (0.16, 0.1, WIN_W + 0.2), "flowers", stretch=True)
        for k in range(4):
            cl.add_cube(detail, "bloom_%d_%d" % (s, k), fb + UP * 0.2 + cl.v3(0, 0.02 * (k % 2), -0.36 + k * 0.24), cl.gg.ry(0.4 * k),
                        (0.1, 0.08, 0.1), "cloth_red")
        for k in range(2):
            cl.beam(detail, "fb_bracket_%d_%d" % (s, k), (x, WIN_Y - 0.45, WIN_Z - 0.3 + 0.6 * k), fb + cl.v3(-s * 0.05, -0.08, -0.3 + 0.6 * k),
                    0.05, "wood_dark", up=UP)
        # gold pilasters at the corners and a band at the eaves and the floor
        for z in (Z0, Z1):
            cl.add_cube(body, "pilaster_%d_%.1f" % (s, z), (x + s * 0.02, BED_Y + WALL_H / 2, z), cl.EYE, (0.13, WALL_H + 0.04, 0.13),
                        {"all": "gold", "+2": "end_grain", "-2": "end_grain"})
        cl.add_cube(body, "band_top_%d" % s, (x + s * 0.045, EAVE - 0.06, zc), cl.EYE, (0.05, 0.12, L), "gold")
        cl.add_cube(body, "band_low_%d" % s, (x + s * 0.045, BED_Y + 0.06, zc), cl.EYE, (0.05, 0.12, L), "gold")
        # a gold-framed painted sign between the window and the door
        cl.add_cube(body, "sign_%d" % s, (x + s * 0.06, WIN_Y + 0.32, 0.55), cl.EYE, (0.04, 0.5, 0.36), {"all": "gold", "+1": "cloth_red", "-1": "cloth_red"})
        cl.add_cube(detail, "sign_crest_%d" % s, (x + s * 0.085, WIN_Y + 0.34, 0.55), cl.gg.rx(math.pi / 4), (0.02, 0.16, 0.16), "gold")
        cl.add_cube(body, "band_mid_%d" % s, (x + s * 0.045, WIN_Y - 0.03, zc), cl.EYE, (0.03, 0.05, L), "wood")
    # front wall: the door between two lanterns, gold door frame and pediment
    zf = Z1
    door_w, door_h = 0.62, 1.25
    for s in (1, -1):
        cl.add_cube(body, "front_wall_%d" % s, (s * (door_w / 2 + (HW - door_w / 2) / 2), BED_Y + WALL_H / 2, zf), cl.EYE,
                    (HW - door_w / 2, WALL_H, 0.08), "red_plank")
        cl.add_cube(body, "door_post_%d" % s, (s * (door_w / 2 + 0.05), BED_Y + door_h / 2 + 0.02, zf + 0.05), cl.EYE,
                    (0.1, door_h + 0.06, 0.06), "gold")
        # lanterns on brackets beside the door
        b0 = cl.v3(s * 0.62, BED_Y + 1.3, zf + 0.04)
        tip = b0 + cl.v3(0, 0.02, 0.24)
        cl.beam(detail, "lamp_bracket_%d" % s, b0, tip, 0.05, "iron", up=UP)
        cl.add_cube(detail, "lamp_plate_%d" % s, b0 + cl.v3(0, -0.05, 0.01), cl.EYE, (0.1, 0.2, 0.03), "gold")
        cl.lantern(body, "lamp_%d" % s, tip - UP * 0.28, size=0.22, chain_to=tip)
    cl.add_cube(body, "front_over_door", (0, (BED_Y + door_h + EAVE) / 2, zf), cl.EYE, (door_w, EAVE - BED_Y - door_h, 0.08), "red_plank")
    cl.add_cube(body, "door", (0, BED_Y + door_h / 2, zf - 0.02), cl.EYE, (door_w, door_h, 0.06), {"all": "plank_dark", "+3": "plank_dark"})
    cl.add_cube(detail, "door_window", (0, BED_Y + door_h - 0.3, zf + 0.015), cl.EYE, (0.26, 0.26, 0.02), "glass")
    cl.add_cube(detail, "door_knob", (0.2, BED_Y + 0.6, zf + 0.03), cl.EYE, (0.05, 0.05, 0.04), "gold")
    cl.add_cube(body, "door_lintel", (0, BED_Y + door_h + 0.08, zf + 0.06), cl.EYE, (door_w + 0.3, 0.1, 0.08), "gold")
    cl.add_cube(detail, "door_crest", (0, BED_Y + door_h + 0.22, zf + 0.06), cl.gg.rz(math.pi / 4), (0.14, 0.14, 0.05), "gold")
    for s in (1, -1):
        cl.add_cube(body, "front_band_%d" % s, (s * (HW + door_w / 2) / 2, EAVE - 0.06, zf + 0.045), cl.EYE, (HW - door_w / 2, 0.12, 0.05), "gold")
    # back wall with a small window
    cl.add_cube(body, "back_wall", (0, BED_Y + WALL_H / 2, Z0), cl.EYE, (2 * HW, WALL_H, 0.08), "red_plank")
    cl.add_cube(body, "glow_back_window", (0, BED_Y + 0.95, Z0 - 0.045), cl.EYE, (0.5, 0.45, 0.02), "glass")
    for k, (a, b) in enumerate((((-0.28, 0.7), (0.28, 0.7)), ((-0.28, 1.2), (0.28, 1.2)), ((-0.28, 0.7), (-0.28, 1.2)), ((0.28, 0.7), (0.28, 1.2)))):
        cl.beam(body, "back_frame_%d" % k, (a[0], BED_Y + a[1], Z0 - 0.06), (b[0], BED_Y + b[1], Z0 - 0.06), 0.06, "gold", width=0.04,
                up=cl.v3(0, 0, -1), extend=0.03)
    cl.collide((-HW - 0.05, BED_Y, Z0 - 0.05, HW + 0.05, EAVE, Z1 + 0.05))


def roof_and_porch(body, detail):
    # curved red roof, overhanging the porch at the front, gold bargeboards
    cl.roof(body, "roof", HW, Z0, Z1 + 0.32, EAVE, 0.55, region="red_roof", trim="gold", th=0.08, nx=8, overhang=0.16)
    # gables (red planks filling the arch at both ends) as a few stacked boards
    for e, z in (("front", Z1), ("back", Z0)):
        for k in range(3):
            y = EAVE + 0.09 + k * 0.15
            f = (1 - ((y - EAVE) / 0.6) ** 2) ** 0.5
            cl.add_cube(body, "gable_%s_%d" % (e, k), (0, y, z), cl.EYE, (2 * HW * f, 0.16, 0.08), "red_plank")
    cl.add_cube(body, "ridge", (0, EAVE + 0.6, (Z0 + Z1) / 2 + 0.16), cl.EYE, (0.12, 0.08, Z1 - Z0 + 0.66), "gold")
    # carved brackets under the porch overhang
    for s in (1, -1):
        cl.beam(detail, "porch_bracket_%d" % s, (s * (HW - 0.05), EAVE - 0.45, Z1 + 0.04), (s * (HW - 0.05), EAVE - 0.02, Z1 + 0.4),
                0.08, "gold", up=cl.X)
        cl.post(body, "porch_post_%d" % s, (s * (HW - 0.05), BED_Y, Z1 + 0.32), (s * (HW - 0.05), EAVE, Z1 + 0.32), d=0.09,
                region="wood", solid=False)
    # steps from the porch down to the ground, between two stringers
    zs = Z1 + 0.38
    for k in range(3):
        top = BED_Y - 0.25 * (k + 1)
        z = zs + 0.27 * k
        cl.add_cube(body, "step_%d" % k, (0, top - 0.04, z + 0.135), cl.EYE, (0.78, 0.08, 0.3), {"all": "plank", "+2": "plank"})
        cl.add_cube(body, "riser_%d" % k, (0, top - 0.17, z + 0.02), cl.EYE, (0.76, 0.18, 0.04), "plank_dark")
        cl.collide((-0.4, 0.0, z, 0.4, top, z + 0.27))
    for s in (1, -1):
        cl.beam(body, "stringer_%d" % s, (s * 0.43, BED_Y, zs - 0.02), (s * 0.43, 0.0, zs + 0.86), 0.07, "wood_dark", width=0.16, up=cl.X)


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    gear(root, detail)
    body = cl.Bone("body", parent=root)
    house(body, detail)
    roof_and_porch(body, detail)
    # a small barrel and a crate beside the steps
    cargo = cl.Bone("cargo", parent=root)
    cl.barrel(cargo, "barrel", (-0.9, 0.0, Z1 + 0.85), r=0.26, h=0.66)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, body=(122, 36, 30), dark=(70, 46, 24), roof=(168, 44, 34), trim=(222, 178, 52), lantern=True)


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
