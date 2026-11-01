#!/usr/bin/env python3
"""cart_market — Charrette de marché / Market Cart (reference: scratchpad/ref/cart_market_ref.png).

PLACEHOLDER built with cartlib (carts-core): a merchant flatbed with a red and white striped awning on four posts, crates of produce, a lantern, a barrel beside it.
Replace build() / icon() with the detailed model; keep NAME, main() and the cartlib.export call.

Usage:  python3 tools/carts/generate_cart_market.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_market.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_market.png,
        carts/cart_market.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_market"

def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    hw, z0, z1, y = 0.95, -1.6, 1.2, 0.9
    cl.running_gear(root, hw, z0, z1, y, [-0.3], 0.7, spokes=12, segs=16, drawbar_len=1.8, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", hw, z0, z1, y, h=0.3, posts=3, boards=(1.0,))
    for sx in (1, -1):
        for zz, top in ((z0 + 0.08, y + 1.55), (z1 - 0.08, y + 1.35)):
            cl.post(body, "awning_post_%d_%.1f" % (sx, zz), (sx * (hw - 0.08), y, zz), (sx * (hw - 0.08), top, zz), d=0.1, solid=True)
    cl.awning(body, "awning", -hw - 0.15, hw + 0.15, z0 - 0.1, z1 + 0.35, y + 1.6, y + 1.32)
    cargo = cl.Bone("cargo", parent=root)
    for k, (x, z, p) in enumerate(((-0.42, -1.1, "apples"), (0.42, -1.1, "carrots"), (-0.42, -0.35, "cabbage"), (0.42, -0.35, "apples"),
                                   (-0.42, 0.45, "carrots"), (0.42, 0.45, "cabbage"))):
        cl.produce_crate(cargo, "crate_%d" % k, (x, y, z), produce=p)
    cl.lantern(detail, "lamp", (hw - 0.2, y + 1.05, z1 + 0.1), size=0.22, chain_to=(hw - 0.2, y + 1.3, z1 + 0.1))
    cl.barrel(cargo, "barrel_side", (hw + 0.75, 0.0, 0.6), r=0.33, h=0.85)
    return root


def icon(path):
    cl.icon_cart(path, wheels=2, stripes=((176, 38, 30), (236, 228, 212)), cargo=(184, 38, 28), cargo_dark=(224, 122, 28), sides=False)


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
