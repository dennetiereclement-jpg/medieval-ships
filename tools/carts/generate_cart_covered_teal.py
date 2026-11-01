#!/usr/bin/env python3
"""cart_covered_teal — Charrette couverte turquoise / Teal Covered Wagon (reference: scratchpad/ref/cart_covered_teal_ref.png).

PLACEHOLDER built with cartlib (carts-core): a small wagon with a rounded teal canvas cover with gold trim edges, a lantern at the front opening, four wheels, a drawbar.
Replace build() / icon() with the detailed model; keep NAME, main() and the cartlib.export call.

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

def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    hw, z0, z1, y = 0.8, -1.7, 1.1, 0.82
    cl.running_gear(root, hw, z0, z1, y, [-1.1, 0.5], 0.5, spokes=10, drawbar_len=1.6, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", hw, z0, z1, y, h=0.35, posts=3, boards=(0.45, 1.0), front=False)
    cl.hoop_cover(body, "cover", -1.75, 1.0, 0.86, 1.15, 1.2, hoops=4, region="canvas_teal", trim="trim_gold", detail=detail)
    cl.lantern_post(detail, "lamp", (0.72, 1.15, 1.08), height=0.7, arm=(0.2, 0, 0.18), size=0.22)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, cover=(47, 143, 138), cover_dark=(30, 100, 96), trim=(216, 170, 56), lantern=True)


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
