#!/usr/bin/env python3
"""cart_logs — Charrette de bûcheron / Log Cart (reference: scratchpad/ref/cart_logs_ref.png).

PLACEHOLDER built with cartlib (carts-core): a robust flatbed on four wheels with side stakes, carrying stacked round logs (bark + rings) tied with ropes, a drawbar.
Replace build() / icon() with the detailed model; keep NAME, main() and the cartlib.export call.

Usage:  python3 tools/carts/generate_cart_logs.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_logs.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_logs.png,
        carts/cart_logs.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402

NAME = "cart_logs"

def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    hw, z0, z1, y = 0.9, -2.2, 1.4, 0.85
    cl.running_gear(root, hw, z0, z1, y, [-1.45, 0.65], 0.55, spokes=10, wheel_w=0.24, drawbar_len=1.8, detail=detail)
    body = cl.Bone("body", parent=root)
    for s in (1, -1):
        for k, z in enumerate((-1.8, -0.4, 1.0)):
            cl.post(body, "stake_%d_%d" % (s, k), (s * (hw - 0.06), y - 0.2, z), (s * (hw - 0.02), y + 0.95, z), d=0.12, solid=False)
    cargo = cl.Bone("cargo", parent=root)
    r = 0.26
    rows = [(-0.56, 0.0, 2.0), (0.0, 0.0, 1.9), (0.56, 0.0, 2.1), (-0.28, 0.46, 1.7), (0.28, 0.46, 1.8), (0.0, 0.92, 1.5)]
    for k, (x, dy, L) in enumerate(rows):
        zc = -0.4 + 0.08 * (k % 3 - 1)
        cl.log(cargo, "log_%d" % k, (x, y + r + dy, zc - L), (x, y + r + dy, zc + L * 0.8), r=r)
    cl.collide((-hw, y, -2.4, hw, y + 1.45, 1.1))
    for k, z in enumerate((-1.5, 0.5)):
        cl.rope(detail, "tie_%d" % k, (-hw, y + 0.6, z), (0, y + 1.5, z), d=0.05, segs=2, sag=-0.1)
        cl.rope(detail, "tie_b_%d" % k, (0, y + 1.5, z), (hw, y + 0.6, z), d=0.05, segs=2, sag=-0.1)
    return root


def icon(path):
    cl.icon_cart(path, wheels=4, cargo=(90, 64, 38), cargo_dark=(207, 166, 106), sides=False)


def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
