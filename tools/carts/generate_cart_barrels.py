#!/usr/bin/env python3
"""cart_barrels — Charrette à tonneaux / Barrel Cart (reference: scratchpad/ref/cart_barrels_ref.png).

a two-wheeled transport cart carrying big wooden barrels with iron hoops, a lantern on a post, a drawbar.

Usage:  python3 tools/carts/generate_cart_barrels.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_barrels.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_barrels.png,
        carts/cart_barrels.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402
import cart_frame as cf  # noqa: E402

NAME = "cart_barrels"

HALF_W, Z0, Z1, BED_Y = 0.85, -1.3, 1.05, 1.0
AXLE = (-0.15, 0.82)       # one axle: two big wheels
FENCE_H, POSTS = 0.38, 3


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    cf.gear(root, HALF_W, Z0, Z1, BED_Y, [AXLE], wheel_w=0.24, spokes=8, segs=16, felloe=0.2, hub_d=0.36, drawbar_len=2.0, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", HALF_W, Z0, Z1, BED_Y, h=FENCE_H, posts=POSTS, boards=(0.5, 1.0), d=0.15, board_h=0.15,
                 region="plank_dark", post_region="wood_dark")
    cf.side_bolts(detail, "bolt", HALF_W, Z0, Z1, BED_Y, POSTS, (FENCE_H * 0.5, FENCE_H))
    # tall back corner posts with a top rail (the tailboard frame)
    i = 0.06
    for s in (1, -1):
        cl.post(body, "back_post_%d" % ((s + 1) // 2), (s * (HALF_W - i), BED_Y - 0.1, Z0 + i), (s * (HALF_W - i), BED_Y + 0.82, Z0 + i),
                d=0.15, region="wood_dark", solid=False)
    cl.beam(body, "back_rail", (-HALF_W + i, BED_Y + 0.75, Z0 + i), (HALF_W - i, BED_Y + 0.75, Z0 + i), 0.12, "wood_dark", width=0.16, extend=0.08)
    cl.collide((-HALF_W, BED_Y, Z0 - 0.04, HALF_W, BED_Y + 0.82, Z0 + 0.16))
    cargo = cl.Bone("cargo", parent=root)
    # two big iron-hooped barrels standing along the cart
    for k, z in enumerate((-0.74, 0.3)):
        cf.hooped_barrel(cargo, detail, "barrel_%d" % k, (0.02 * (1 - 2 * k), BED_Y, z), r=0.45, h=1.12, staves=12, bulge=0.06,
                         hoops=(0.08, 0.3, 0.7, 0.92))
    # the lantern on a post at the front corner
    cl.lantern_post(detail, "lamp", (-HALF_W + 0.08, BED_Y - 0.05, Z1 - 0.08), height=1.05, arm=(0.0, 0.0, 0.26), size=0.36, d=0.11)
    cl.collide((-HALF_W, BED_Y, Z1 - 0.18, -HALF_W + 0.18, BED_Y + 1.0, Z1 + 0.02))
    # a coil of rope on the floor behind the barrels and wedges against the barrels
    cl.add_cube(detail, "wedge_0", (0.0, BED_Y + 0.06, -0.15), cl.EYE, (0.5, 0.12, 0.12), "wood")
    return root


def icon(path):
    from PIL import Image
    cl.icon_cart(path, wheels=2, cargo=(156, 104, 56), cargo_dark=(64, 64, 70), lantern=True, dark=(78, 52, 28))
    im = Image.open(path)
    p = im.load()
    for x in range(2, 12):                       # the barrels' iron hoops
        for y in (5, 7):
            p[x, y] = (60, 60, 66, 255)
    im.save(path)

def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
