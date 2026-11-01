#!/usr/bin/env python3
"""cart_covered_white — Charrette couverte blanche / White Covered Wagon (reference: scratchpad/ref/cart_covered_white_ref.png).

PLACEHOLDER built with cartlib (carts-core): a four-wheeled wagon, low sides, a rounded white canvas cover on hoops, two lanterns at the front opening, a drawbar.
Replace build() / icon() with the detailed model; keep NAME, main() and the cartlib.export call.

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

def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    g = cl.running_gear(root, 0.95, -2.3, 1.5, 0.92, [-1.5, 0.75], 0.6, spokes=10, drawbar_len=1.8, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", 0.95, -2.3, 1.5, 0.92, h=0.4, posts=4, boards=(0.45, 1.0), front=False)
    cl.hoop_cover(body, "cover", -2.35, 1.4, 1.02, 1.3, 1.45, hoops=5, region="canvas", trim="trim_white", detail=detail)
    for s in (1, -1):
        cl.lantern_post(detail, "lamp_%d" % s, (s * 0.88, 1.3, 1.45), height=0.75, arm=(s * 0.25, 0, 0.18), size=0.22)
    cl.add_cube(detail, "bench", (0, 1.15, 1.0), cl.EYE, (1.6, 0.1, 0.4), "plank")
    cl.crate_box(detail, "crate", (0.35, 0.92, -1.6), s=0.6, solid=False)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, cover=(232, 224, 204), cover_dark=(190, 180, 160))


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
