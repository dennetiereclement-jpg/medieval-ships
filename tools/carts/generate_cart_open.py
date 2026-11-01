#!/usr/bin/env python3
"""cart_open — the open transport cart (reference: scratchpad/ref/cart_open_ref.png); the worked example of cartlib.

A two-wheeled open cart: a plank floor on two sills, slatted wooden fence sides (posts, two boards, a top rail)
on all four sides, two big spoked wheels (12 spokes, iron tyres) on an axle a little behind the middle, the drawbar
(two shafts converging forward, a crossbar) resting on a small prop at its tip.

Usage:  python3 tools/carts/generate_cart_open.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_open.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_open.png,
        carts/cart_open.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_open"
HALF_W = 0.85          # the bed is 1.7 wide
Z0, Z1 = -1.55, 1.05   # back and front of the bed (2.6 long)
BED_Y = 0.98           # top of the floor
R = 0.78               # wheel radius (1.56 across)
AXLE_Z = -0.25
FENCE_H = 0.72


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    cl.running_gear(root, HALF_W, Z0, Z1, BED_Y, [AXLE_Z], R, wheel_w=0.22, spokes=12, segs=16, drawbar_len=2.0, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", HALF_W, Z0, Z1, BED_Y, h=FENCE_H, posts=4, boards=(0.3, 0.62, 1.0))
    # a loose plank and a sack in the bed, a rope coil on the floor
    cl.add_cube(detail, "loose_plank", (0.25, BED_Y + 0.04, -0.7), cl.gg.ry(0.3), (0.28, 0.06, 1.3), "plank")
    cl.add_cube(detail, "sack", (-0.4, BED_Y + 0.2, -1.1), cl.gg.ry(-0.4), (0.45, 0.4, 0.36), "sack", stretch=True)
    return root


def icon(path):
    cl.icon_cart(path, wheels=2)


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(6, 3, 0))


if __name__ == "__main__":
    main()
