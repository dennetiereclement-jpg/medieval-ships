#!/usr/bin/env python3
"""cart_barrels — Charrette à tonneaux / Barrel Cart (reference: scratchpad/ref/cart_barrels_ref.png).

PLACEHOLDER built with cartlib (carts-core): a two-wheeled transport cart carrying big wooden barrels with iron hoops, a lantern on a post, a drawbar.
Replace build() / icon() with the detailed model; keep NAME, main() and the cartlib.export call.

Usage:  python3 tools/carts/generate_cart_barrels.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_barrels.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_barrels.png,
        carts/cart_barrels.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_barrels"

def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    hw, z0, z1, y = 0.9, -1.5, 1.1, 0.95
    cl.running_gear(root, hw, z0, z1, y, [-0.2], 0.76, spokes=12, segs=16, drawbar_len=1.9, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", hw, z0, z1, y, h=0.4, posts=3, boards=(0.5, 1.0))
    cargo = cl.Bone("cargo", parent=root)
    for k, (x, z) in enumerate(((-0.4, -0.95), (0.4, -0.95), (-0.4, -0.1))):
        cl.barrel(cargo, "barrel_%d" % k, (x, y, z), r=0.36, h=0.95, solid=False)
    cl.barrel(cargo, "barrel_lying", (-0.35, y + 0.36, 0.55), r=0.34, h=0.85, axis="x", solid=False)
    cl.collide((-hw, y, z0, hw, y + 0.95, 0.95))
    cl.lantern_post(detail, "lamp", (hw - 0.1, y, z1 - 0.1), height=1.5, arm=(0, 0, 0.3), size=0.24)
    return root


def icon(path):
    cl.icon_cart(path, wheels=2, cargo=(148, 100, 58), cargo_dark=(60, 60, 64), lantern=True)


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
