#!/usr/bin/env python3
"""cart_merchant_wagon — Roulotte de marchand / Merchant Wagon (reference: scratchpad/ref/cart_merchant_wagon_ref.png).

PLACEHOLDER built with cartlib (carts-core): a small house on four wheels: dark red plank walls with gold trim, a curved red roof, lit windows, a door and steps at the back, lanterns, a drawbar.
Replace build() / icon() with the detailed model; keep NAME, main() and the cartlib.export call.

Usage:  python3 tools/carts/generate_cart_merchant_wagon.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_merchant_wagon.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_merchant_wagon.png,
        carts/cart_merchant_wagon.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_merchant_wagon"

def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    hw, z0, z1, y = 1.0, -2.5, 1.5, 0.88
    cl.running_gear(root, hw, z0, z1, y, [-1.7, 0.7], 0.58, spokes=10, drawbar_len=1.8, detail=detail)
    body = cl.Bone("body", parent=root)
    H = 1.55
    for s in (1, -1):
        cl.add_cube(body, "wall_%d" % s, (s * (hw - 0.05), y + H / 2, (z0 + z1) / 2), cl.EYE, (0.1, H, z1 - z0 - 0.1), "red_plank", u_dir=(0, 0, 1))
        for z in (z0 + 0.05, z1 - 0.05, (z0 + z1) / 2):
            cl.add_cube(body, "corner_%d_%.1f" % (s, z), (s * (hw - 0.02), y + H / 2, z), cl.EYE, (0.12, H + 0.04, 0.12), "gold")
        for k, z in enumerate((-1.6, -0.2)):
            cl.add_cube(body, "glow_window_%d_%d" % (s, k), (s * (hw + 0.01), y + 0.95, z), cl.EYE, (0.04, 0.5, 0.55), "glass")
            cl.add_cube(detail, "shutter_%d_%d" % (s, k), (s * (hw + 0.03), y + 0.95, z - 0.42), cl.EYE, (0.04, 0.55, 0.28), "red_paint")
            cl.add_cube(detail, "flowers_%d_%d" % (s, k), (s * (hw + 0.12), y + 0.62, z), cl.EYE, (0.2, 0.16, 0.6), {"all": "plank", "+2": "flowers"})
    for e, z in (("back", z0 + 0.05), ("front", z1 - 0.05)):
        cl.add_cube(body, "end_" + e, (0, y + H / 2, z), cl.EYE, (2 * hw - 0.1, H, 0.1), "red_plank")
    cl.add_cube(body, "door", (0, y + 0.7, z0 - 0.01), cl.EYE, (0.6, 1.25, 0.06), "plank_dark")
    for k in range(2):
        cl.add_cube(detail, "step_%d" % k, (0, y - 0.3 - k * 0.28, z0 - 0.25 - k * 0.22), cl.EYE, (0.6, 0.06, 0.24), "plank")
    cl.roof(body, "roof", hw, z0, z1, y + H, 0.45, region="red_roof", trim="gold")
    cl.collide((-hw, y, z0, hw, y + H, z1))
    for s in (1, -1):
        cl.lantern_post(detail, "lamp_%d" % s, (s * (hw + 0.05), y + 1.1, z1 + 0.05), height=0.35, arm=(s * 0.2, 0, 0.15), size=0.2)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, body=(126, 42, 34), dark=(70, 20, 16), roof=(142, 46, 36), trim=(216, 170, 56))


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
