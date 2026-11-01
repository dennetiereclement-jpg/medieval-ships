#!/usr/bin/env python3
"""cart_hay — Charrette de foin / Hay Cart (reference: scratchpad/ref/cart_hay_ref.png).

a four-wheeled bed with low slatted sides, stacked hay bales and a barrel, a drawbar.

Usage:  python3 tools/carts/generate_cart_hay.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_hay.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_hay.png,
        carts/cart_hay.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402
import cart_frame as cf  # noqa: E402

NAME = "cart_hay"

HALF_W, Z0, Z1, BED_Y = 1.0, -2.05, 1.5, 0.95
REAR, FRONT = (-1.3, 0.6), (0.8, 0.52)     # axle z, wheel radius (smaller front wheels)
FENCE_H, POSTS = 0.55, 5


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    cf.gear(root, HALF_W, Z0, Z1, BED_Y, [REAR, FRONT], wheel_w=0.22, spokes=8, segs=14, drawbar_len=1.8, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", HALF_W, Z0, Z1, BED_Y, h=FENCE_H, posts=POSTS, boards=(0.42, 1.0), d=0.14, board_h=0.15,
                 region="plank_dark", post_region="wood_dark")
    cf.side_bolts(detail, "bolt", HALF_W, Z0, Z1, BED_Y, POSTS, (FENCE_H * 0.42, FENCE_H))
    cargo = cl.Bone("cargo", parent=root)
    y = BED_Y
    # bottom layer: 2 x 3 big bales filling the back two thirds of the bed
    for i, z in enumerate((-1.55, -0.74, 0.07)):
        for j, x in enumerate((-0.45, 0.45)):
            yaw = 0.03 * ((i + j) % 3 - 1)
            cl.hay_bale(cargo, "bale_%d_%d" % (i, j), (x, y, z), size=(0.86, 0.55, 0.8), yaw=yaw, solid=False)
            cf.bale_strings(detail, "string_%d_%d" % (i, j), (x, y, z), (0.86, 0.55, 0.8), yaw)
    # second layer: 2 x 2 bales, set back a little
    for i, z in enumerate((-1.3, -0.45)):
        for j, x in enumerate((-0.43, 0.43)):
            yaw = 0.04 * ((i * 2 + j) % 3 - 1)
            cl.hay_bale(cargo, "bale_top_%d_%d" % (i, j), (x, y + 0.55, z), size=(0.82, 0.52, 0.8), yaw=yaw, solid=False)
            cf.bale_strings(detail, "string_top_%d_%d" % (i, j), (x, y + 0.55, z), (0.82, 0.52, 0.8), yaw)
    cl.collide((-HALF_W + 0.08, y, -1.97, HALF_W - 0.08, y + 1.07, 0.47))
    # the barrel at the front corner and a sack
    cf.hooped_barrel(cargo, detail, "barrel", (-0.5, y, 1.0), r=0.38, h=0.95, staves=10, bulge=0.05, hoops=(0.1, 0.3, 0.7, 0.9))
    cl.add_cube(detail, "sack", (0.45, y + 0.2, 1.05), cl.gg.ry(-0.35), (0.45, 0.4, 0.36), "sack", stretch=True)
    # loose hay on the floor at the front
    cl.add_cube(detail, "loose_hay", (0.15, y + 0.04, 0.75), cl.gg.ry(0.4), (0.7, 0.08, 0.5), "hay_top", stretch=True)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, cargo=(214, 178, 74), cargo_dark=(160, 124, 48), dark=(78, 52, 28))

def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
