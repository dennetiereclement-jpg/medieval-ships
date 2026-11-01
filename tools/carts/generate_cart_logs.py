#!/usr/bin/env python3
"""cart_logs — Charrette de bûcheron / Log Cart (reference: scratchpad/ref/cart_logs_ref.png).

a robust flatbed on four wheels with side stakes, carrying stacked round logs (bark + rings) tied with ropes, a drawbar.

Usage:  python3 tools/carts/generate_cart_logs.py      (CART_OUT=<file>: write only the model there, for previews)
Writes: blockbench/cart_logs.bbmodel, the assets copy, textures/entity/carts.png, textures/item/cart_logs.png,
        carts/cart_logs.json (extent + collision boxes for TentType).
Cart-local coordinates: y up, +z = front (the drawbar, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartlib as cl  # noqa: E402
import cart_frame as cf  # noqa: E402

NAME = "cart_logs"

HALF_W, Z0, Z1, BED_Y = 0.95, -2.1, 1.3, 0.95
REAR, FRONT = (-1.35, 0.62), (0.65, 0.52)
FENCE_H, POSTS = 0.48, 4
LZ0, LZ1 = -2.25, 1.22     # the logs' back and front ends (about)


def stack():
    """(x, y, r) of the logs, a pyramid of 4 / 3 / 2 resting on the bed."""
    y0 = BED_Y
    logs = []
    for k, x in enumerate((-0.66, -0.22, 0.22, 0.66)):
        logs.append((x, y0 + 0.21, 0.205 - 0.012 * (k % 2)))
    for k, x in enumerate((-0.44, 0.0, 0.44)):
        logs.append((x + 0.01 * (k - 1), y0 + 0.21 + 0.38, 0.215 - 0.012 * (k % 2)))
    for k, x in enumerate((-0.23, 0.23)):
        logs.append((x, y0 + 0.21 + 0.76, 0.225 - 0.01 * k))
    return logs


def hull_pts(logs, side_y, n=9, pad=0.035):
    """A rope round the stack: from the left fence top over the logs to the right fence top."""
    pts = [(-HALF_W - 0.01, side_y)]
    for i in range(n + 1):
        a = math.pi * (1 - i / n)
        nx, ny = math.cos(a), math.sin(a)
        best = max(logs, key=lambda l: l[0] * nx + l[1] * ny + l[2])
        pts.append((best[0] + (best[2] + pad) * nx, best[1] + (best[2] + pad) * ny))
    pts.append((HALF_W + 0.01, side_y))
    return [p for p in pts if p[1] >= side_y - 0.01 or abs(p[0]) > HALF_W - 0.02]


def build():
    root = cl.Bone(NAME)
    detail = cl.Bone("detail", parent=root)
    cf.gear(root, HALF_W, Z0, Z1, BED_Y, [REAR, FRONT], wheel_w=0.24, spokes=8, segs=14, felloe=0.19, drawbar_len=1.8, detail=detail)
    body = cl.Bone("body", parent=root)
    cl.box_sides(body, "side", HALF_W, Z0, Z1, BED_Y, h=FENCE_H, posts=POSTS, boards=(0.45, 1.0), d=0.15, board_h=0.17,
                 region="plank_dark", post_region="wood_dark")
    cf.side_bolts(detail, "bolt", HALF_W, Z0, Z1, BED_Y, POSTS, (FENCE_H * 0.45, FENCE_H))
    cargo = cl.Bone("cargo", parent=root)
    logs = stack()
    for k, (x, y, r) in enumerate(logs):
        dz0, dz1 = 0.07 * ((k * 3) % 4 - 1.5), 0.06 * ((k * 5) % 3 - 1)
        cf.log12(cargo, "log_%d" % k, (x, y, LZ0 + dz0), (x, y, LZ1 + dz1), r=r, cap_bone=cargo)
    top = max(y + r for x, y, r in logs)
    cl.collide((-HALF_W + 0.08, BED_Y, LZ0 - 0.1, HALF_W - 0.08, top, LZ1 + 0.08))
    # two rope lashings over the stack down to the fence rails, knotted on the near side
    pts = hull_pts(logs, BED_Y + FENCE_H * 0.5)
    for k, z in enumerate((-1.35, 0.35)):
        cf.strap(detail, "lash_%d" % k, [(x, y, z) for x, y in pts], d=0.08, region="hay")
        cl.add_cube(detail, "knot_%d" % k, (HALF_W + 0.03, BED_Y + FENCE_H * 0.5, z), cl.EYE, (0.1, 0.14, 0.14), "hay")
        cf.strap(detail, "lash_end_%d" % k, [(HALF_W + 0.05, BED_Y + FENCE_H * 0.5, z), (HALF_W + 0.07, BED_Y + 0.05, z + 0.08)], d=0.05, region="hay")
    # an axe stuck in the top log, a wedge at the back
    lx, ly, lr = logs[-1]
    cl.beam(detail, "axe_handle", (lx + 0.05, ly + lr - 0.02, -1.9), (lx + 0.35, ly + lr + 0.45, -1.75), 0.05, "wood", up=cl.UP)
    cl.add_cube(detail, "axe_head", (lx + 0.05, ly + lr + 0.02, -1.9), cl.gg.rz(0.6), (0.06, 0.2, 0.22), "iron")
    return root


def icon(path):
    from PIL import Image
    cl.icon_cart(path, wheels=4, cargo=(92, 62, 36), cargo_dark=(70, 46, 26), sides=False, dark=(78, 52, 28))
    im = Image.open(path)
    p = im.load()
    for cx, cy in ((2, 7), (4, 7), (3, 5), (2, 5), (4, 5)):      # the ring ends of the logs at the front
        p[cx, cy] = (214, 176, 116, 255)
    im.save(path)

def main():
    cl.setup(NAME)
    root = build()
    cl.export(root, NAME, None, icon=icon, visible_box=(8, 4, 0))


if __name__ == "__main__":
    main()
