#!/usr/bin/env python3
"""cart_hay — Charrette de foin / Hay Cart (reference: scratchpad/ref/cart_hay_ref.png).

PLACEHOLDER built with cartlib (carts-core): a four-wheeled bed with low slatted sides, stacked hay bales and a barrel, a drawbar.
Replace build() / icon() with the detailed model; keep NAME, main() and the cartlib.export call.

Usage:  python3 tools/carts/generate_cart_hay.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_hay.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_hay.png,
        carts/cart_hay.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_hay"

def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    cl.running_gear(root, 0.95, -2.1, 1.5, 0.88, [-1.35, 0.75], 0.56, spokes=10, drawbar_len=1.8, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", 0.95, -2.1, 1.5, 0.88, h=0.5, posts=4, boards=(0.45, 1.0))
    cargo = cl.Bone("cargo", parent=root)
    for i, z in enumerate((-1.55, -0.65, 0.25)):
        for j, x in enumerate((-0.45, 0.45)):
            cl.hay_bale(cargo, "bale_%d_%d" % (i, j), (x, 0.88, z), size=(0.85, 0.5, 0.85), yaw=0.04 * (i - j))
    for i, z in enumerate((-1.1, -0.2)):
        cl.hay_bale(cargo, "bale_top_%d" % i, (0, 1.38, z), size=(0.85, 0.5, 0.85), yaw=1.57 + 0.05 * i)
    cl.barrel(cargo, "barrel", (0.45, 0.88, 1.05), r=0.3, h=0.7)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, cargo=(200, 167, 72), cargo_dark=(150, 120, 50))


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
