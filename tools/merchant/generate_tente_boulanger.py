#!/usr/bin/env python3
"""tente_boulanger — Tente du boulanger / Baker's Stall (reference: scratchpad/ref/tente_boulanger_ref.png).

The gabled market stall of merchantlib.stall in brown and beige: stripes running down the two roof slopes, the
dagged brown and beige valance edged in gold, four squared posts with gold caps, lanterns on the two front posts, two
brown banners with the golden wheat ear over a loaf (one hanging from each front post); dressed by
tools/merchant/props_m8.py: the stone bread oven at the back (arched mouth glowing with loaves inside, the stepped
chimney hood), the shelves full of round and long loaves at the back right, a string of garlic and a wheat sheaf
hanging from the rail, the wooden bread peel, two jars on a stand, the long counter with big round loaves, buns and
brioches, a berry tart and a cake (mod blocks when installed), the cream cloth with the wheat emblem and gold dags
hanging at its front; on the left a low table with a sack of wheat ears and a tray of buns, two open flour sacks with
the wheat emblem before it, barrels outside the left post (a basket of baguettes, a basket of buns) and crates; a
barrel, crates and a sack outside the right post. No flags, no rug (as on the picture); a rare wisp of smoke from the
oven mouth.

Usage:  python3 tools/merchant/generate_tente_boulanger.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_boulanger.json, models/entity + blockbench/tente_boulanger.bbmodel,
textures/entity/tente_boulanger.png, textures/item/tente_boulanger.png, interiors/tente_boulanger_decor.json.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m8 as p8  # noqa: E402

NAME = "tente_boulanger"
v3, UP = ml.v3, ml.UP
OVEN_X = 0.0


def counter_goods(props, det, L, rng, decor):
    """On the long counter: big round loaves at the left, a heap of buns and brioches, a long loaf, the berry tart on a
    board and the cake at the right (mod blocks when installed); the cream cloth with the wheat emblem hanging at its
    front."""
    (x0, y, z0, x1, _, z1), = L.counter_boxes
    p8.p7.runner(props, "cloth", 0.05, 1.45, z0, z1, y, hang=0.78, region="m8_cloth", top_region="m8_cloth_top")
    yt = y + 0.016
    zc = (z0 + z1) / 2
    for k, (x, z, r) in enumerate(((-0.12, zc + 0.12, 0.2), (0.34, zc + 0.16, 0.21), (0.1, zc - 0.2, 0.19), (0.58, zc - 0.18, 0.17))):
        p8.loaf_round(props, "loaf_%d" % k, (x, yt, z), r=r, h=0.2, yaw=0.3 * k)
    # the heap of buns and brioches in the middle (two layers)
    for k in range(7):
        j = k % 4
        layer = 0 if k < 4 else 1
        x = 0.82 + j * 0.15 + 0.07 * layer
        z = zc + (0.12 if (k % 2) else -0.1) - 0.02 * layer
        p8.bun(props, "bun_%d" % k, (x, yt + 0.07 * layer, z), r=0.085, h=0.085, yaw=rng.uniform(-0.5, 0.5))
    p8.loaf_long(props, "loaf_long_c", (1.12, yt, z0 + 0.14), l=0.44, w=0.2, h=0.15, yaw=0.15)
    # the tart on its board and the cake (mod), with stand-ins drawn when the mods are missing
    p8.box(props, "tart_board", (1.48, yt, zc - 0.22), (1.86, yt + 0.03, zc + 0.2), "plank")
    decor.block("farmersdelight:sweet_berry_cheesecake", 1.67, yt + 0.03, zc, facing="front", scale=0.5, solid=False, fallback="m8_tart",
                bounds=(0.125, 0.875, 0.0, 0.25, 0.125, 0.875))
    p8.box(props, "cake_stand", (1.9, yt, zc - 0.25), (2.3, yt + 0.05, zc + 0.23), "wood_dark")
    decor.block("landsoficaria:strawberry_cake", 2.1, yt + 0.05, zc - 0.01, facing="front", scale=0.48, solid=False,
                fallback="m8_icing", bounds=(0.0625, 0.9375, 0.0, 0.5, 0.0625, 0.9375))
    p8.bun(props, "bun_r", (2.05, yt, z1 - 0.06), r=0.07, h=0.07)


def left_table(props, det, L, rng):
    """The low table between the left post and the counter: the sack of wheat ears and a tray of buns; the two open
    flour sacks before it."""
    hd = L.half_d
    top = ml.counter(props, "table_left", -2.25, -1.2, hd - 1.0, hd - 0.38, h=0.82, detail=det)
    y = top[1]
    p8.wheat_sack(props, "wheat_sack", (-1.92, y, hd - 0.7), s=0.42)
    p8.bun_tray(props, "tray_buns", -1.62, -1.26, hd - 0.92, hd - 0.48, y, rng, r=0.075, rows=3)
    p8.loaf_round(props, "table_loaf", (-1.45, y, hd - 0.42), r=0.12, h=0.12)
    p8.flour_sack(props, "flour_0", (-1.78, 0.0, hd + 0.5), s=0.56, yaw=0.12)
    p8.flour_sack(props, "flour_1", (-1.15, 0.0, hd + 0.62), s=0.52, yaw=-0.18)


def back(props, det, L, rng, decor):
    """The stone oven at the back, the shelves full of loaves at the back right, the jars on a stand, the bread peel,
    the garlic and the wheat sheaf hanging from the rail; a sack of flour against the wall at the back left."""
    hw, hd = L.half_w, L.half_d
    mouth = p8.oven(props, det, OVEN_X, -hd + 0.02, rng, w=1.9, d=1.25, hood_top=3.72)
    # the shelves
    levels = ml.shelf_unit(props, "shelves", 1.05, hw - 0.36, -hd + 0.06, -hd + 0.58, levels=(0.55, 1.1, 1.65, 2.2), h=2.5, back=False,
                           uprights=3, detail=det)
    for i, (sx0, sx1, y, zf, zb) in enumerate(levels):
        n = 5 if i % 2 == 0 else 4
        for k in range(n):
            x = sx0 + 0.08 + (sx1 - sx0 - 0.16) * (k + 0.5) / n
            z = (zf + zb) / 2 + rng.uniform(-0.04, 0.04)
            if (i + k) % 3 == 2:
                p8.loaf_long(det, "shelf_long_%d_%d" % (i, k), (x, y, z), l=0.3, w=0.15, h=0.12, yaw=1.57 + rng.uniform(-0.2, 0.2))
            else:
                p8.loaf_round(det, "shelf_loaf_%d_%d" % (i, k), (x, y, z), r=0.12, h=0.13, yaw=rng.uniform(0, 1))
        if i == 0:
            p8.bun(det, "shelf_bun_a", (sx0 + 0.3, y + 0.13, (zf + zb) / 2), r=0.07, h=0.07)
    # the stand with two jars between the oven and the shelves, the peel leaning on it
    top = ml.counter(props, "jar_stand", 1.04, 1.58, -1.62, -1.15, h=0.92, detail=det)
    p8.jar(props, "jar_0", (1.19, top[1], -1.4), r=0.12, h=0.26)
    p8.jar(props, "jar_1", (1.44, top[1], -1.36), r=0.11, h=0.22)
    p8.peel(props, "peel", (1.12, 0.0, -0.93), (1.17, 1.72, -1.2))
    # hanging from the rail: garlic left of the hood, the wheat sheaf right of it
    hy, hz = L.hang_y, L.hang_z
    p8.garlic_string(props, "garlic", (OVEN_X - 0.75, hy, hz), length=0.85, width=0.3)
    p8.wheat_sheaf(props, "sheaf", (OVEN_X + 0.95, hy, hz), length=0.95, width=0.5)
    p8.garlic_string(props, "garlic_b", (1.75, hy, hz), length=0.7, width=0.26)
    decor.block("farmersdelight:rice_bag", -hw + 0.55, 0.0, -hd + 0.5, facing="front", scale=0.75, fallback="m8_burlap")
    return mouth


def outside(props, det, L, rng, decor):
    """Barrels and crates outside the posts: the barrel with the basket of baguettes and the barrel with a basket of
    buns at the left, crates behind them; the barrel, the crate with a tray of buns and a crate with a sack at the
    right."""
    hw, hd = L.half_w, L.half_d
    # left
    fl = (-hw - 0.62, 0.0, hd - 0.05)
    ml.barrel(props, "barrel_l0", fl, r=0.4, h=0.92)
    ml.basket(props, "basket_bag", (fl[0], 0.92, fl[2]), r=0.28, h=0.26, handle=False)
    for k, (dx, dz, lx, lz) in enumerate(((-0.1, -0.06, -0.12, -0.05), (0.0, 0.04, 0.02, 0.08), (0.1, -0.04, 0.14, -0.02),
                                          (-0.04, 0.1, -0.06, 0.16))):
        a = v3(fl[0] + dx, 1.0, fl[2] + dz)
        p8.baguette(props, "baguette_%d" % k, a, a + v3(lx, 0.62 - 0.05 * (k % 2), lz), r=0.055)
    fl2 = (-hw - 0.66, 0.0, hd - 0.95)
    ml.barrel(props, "barrel_l1", fl2, r=0.36, h=0.84)
    ml.basket(props, "basket_buns", (fl2[0], 0.84, fl2[2]), r=0.25, h=0.16, content="m8_bun_top", handle=True)
    for k in range(3):
        p8.bun(props, "basket_bun_%d" % k, (fl2[0] - 0.09 + 0.09 * k, 1.0, fl2[2] + 0.03 * (k % 2)), r=0.07, h=0.07)
    decor.block("furnish:spruce_crate", -hw - 0.62, 0.0, -0.45, facing="front", scale=0.75, fallback="crate")
    decor.block("furnish:spruce_crate", -hw - 0.62, 0.75, -0.45, facing="front", scale=0.55, fallback="crate")
    # right
    fr = (hw + 0.62, 0.0, hd - 0.2)
    ml.barrel(props, "barrel_r0", fr, r=0.4, h=0.92)
    p8.bun_tray(props, "barrel_buns", fr[0] - 0.22, fr[0] + 0.22, fr[2] - 0.18, fr[2] + 0.18, 0.92, rng, r=0.07, rows=2)
    decor.block("furnish:spruce_crate", hw - 0.2, 0.0, hd + 0.62, facing="front", scale=0.62, fallback="crate")
    p8.bun_tray(props, "crate_buns", hw - 0.46, hw + 0.06, hd + 0.4, hd + 0.84, 0.62, rng, r=0.07, rows=2)
    decor.block("furnish:spruce_crate", hw + 0.62, 0.0, 0.85, facing="front", scale=0.72, fallback="crate")
    decor.block("farmersdelight:rice_bag", hw + 0.62, 0.72, 0.85, facing="front", scale=0.5, solid=False, fallback="m8_burlap")


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="brown")
    p8.add_regions(atlas)
    root = ml.Bone(NAME)
    L = ml.stall(root, atlas, emblem="bread", lanterns=2, front_counter=True, counter_x=(-0.35, 2.3), back_shelves=False,
                 banner_side="both", hang_z=-0.55)
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1701)
    decor = ml.Decor()
    counter_goods(props, det, L, rng, decor)
    left_table(props, det, L, rng)
    mouth = back(props, det, L, rng, decor)
    outside(props, det, L, rng, decor)
    particles = [ml.particle("smoke", (mouth[0], mouth[1] + 0.45, mouth[2] + 0.12), chance=0.08, count=1)]
    return root, atlas, L, decor, particles


def main():
    root, atlas, L, decor, particles = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="brown", emblem="bread", shape="stall", banners=2), particles=particles)


if __name__ == "__main__":
    main()
