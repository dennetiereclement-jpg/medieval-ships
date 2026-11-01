#!/usr/bin/env python3
"""tente_nourriture — Tente du marchand de nourriture / Food Merchant Tent (reference:
scratchpad/ref/tente_nourriture_ref.png).

The shared merchant pavilion (merchantlib.pavilion) in ochre yellow and beige with the cheese banner, dressed as a
food stall: a presentation table under a yellow cloth with a pyramid of cheese blocks, shelves of cheese wheels and
bread along the left wall and the back, the right counter heaped with tomatoes, apples, bread rolls and greens,
cured hams and sausages hanging from the front beam, a small banner, ivy at the left post, barrels, baskets, sacks
and the Farmer's Delight crates by the front posts.

Usage:  python3 tools/merchant/generate_tente_nourriture.py      (MERCHANT_OUT=<file.bbmodel>: only the model)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merchantlib as ml  # noqa: E402
import props_m2 as pm  # noqa: E402

NAME = "tente_nourriture"
v3, UP = pm.v3, pm.UP


def left_shelf(bone, det, x0, x1, z_back, z_front, levels=(0.55, 1.15, 1.75), h=2.15):
    """The front-facing cheese shelves in the left part of the stall (shell shelf unit); returns its levels."""
    return ml.shelf_unit(bone, "lshelf", x0, x1, z_back, z_front, levels=levels, h=h, uprights=3, detail=det)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="yellow")
    pm.add_regions(atlas, "food")
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="cheese", flag_corner="back_left", side_banners=0, rug=True, lanterns=2,
                    front_counter="right", back_shelves=True, ivy=False)
    det = L.detail
    stall = ml.Bone("stall", parent=root)
    decor = ml.Decor()
    hw, hd = L.half_w, L.half_d

    # ---- the presentation table under the yellow cloth, a pyramid of cheese blocks, wheels and a wedge
    tx0, tx1, tz0, tz1, ty = -2.05, -0.35, 1.25, 2.05, 0.95
    ml.counter(stall, "table", tx0, tx1, tz0, tz1, h=ty, detail=det)
    pm.table_cloth(stall, "table_cloth", tx0, tx1, tz0, tz1, ty, drop=0.7)
    y = ty + 0.025
    s = 0.36
    for k, x in enumerate((-1.62, -1.2, -0.78)):
        pm.cheese_block(stall, "cheese_a_%d" % k, (x, y, 1.55), s=s, yaw=0.06 * (k - 1))
    for k, x in enumerate((-1.41, -0.99)):
        pm.cheese_block(stall, "cheese_b_%d" % k, (x, y + s * 0.9, 1.53), s=s * 0.95, yaw=-0.05 + 0.1 * k)
    pm.cheese_block(stall, "cheese_c", (-1.2, y + s * 1.75, 1.53), s=s * 0.9, yaw=0.12)
    pm.cheese_block(stall, "cheese_front_0", (-1.55, y, 1.88), s=0.26, yaw=0.3)
    pm.cheese_block(stall, "cheese_front_1", (-0.95, y, 1.9), s=0.24, yaw=-0.2)
    pm.cheese_wedge(det, "cheese_wedge_0", (-1.25, y, 1.92), l=0.3, h=0.15, yaw=-0.4)
    pm.cheese_wheel(stall, "cheese_wheel_t0", (-0.58, y, 1.5), r=0.15, h=0.12)
    pm.cheese_wheel(stall, "cheese_wheel_t1", (-0.58, y + 0.12, 1.5), r=0.13, h=0.11, yaw=0.3)
    pm.cheese_cut_wheel(det, "cheese_cut_t", (-0.58, y, 1.85), r=0.12, h=0.1, yaw=0.6)

    # ---- the shelves along the left wall: cheese wheels, wedges, bread loaves
    ls = left_shelf(stall, det, -hw + 0.25, -1.3, -0.6, -0.08)
    for j, (x0, x1, yl, zf, zb) in enumerate(ls):
        zm = (zf + zb) / 2
        n = 4
        for k in range(n):
            x = x0 + 0.22 + k * (x1 - x0 - 0.44) / (n - 1)
            kind = (j + k) % 3
            if kind == 0:
                pm.cheese_wheel(stall if k % 2 else det, "lw_%d_%d" % (j, k), (x, yl, zm), r=0.19, h=0.13)
                pm.cheese_wheel(det, "lw2_%d_%d" % (j, k), (x, yl + 0.13, zm), r=0.16, h=0.12, yaw=0.4)
            elif kind == 1:
                pm.bread(det, "lb_%d_%d" % (j, k), (x - 0.04, yl, zm - 0.08), yaw=0.2, l=0.32)
                pm.bread(det, "lb2_%d_%d" % (j, k), (x + 0.03, yl, zm + 0.1), yaw=-0.15, l=0.28)
            else:
                pm.cheese_wedge(det, "lwedge_%d_%d" % (j, k), (x, yl, zm), l=0.32, h=0.17, yaw=0.5 + k)
                pm.bread_round(det, "lroll_%d_%d" % (j, k), (x + 0.12, yl, zm + 0.08), r=0.1, h=0.09)
    # dried herbs and garlic hanging over the left shelves
    for k, z in enumerate((0.3, 0.9, 1.5)):
        ml.hanging_bunch(det, "lherbs_%d" % k, (-hw + 0.05, L.eave_y - 0.33, z), kind="herbs" if k % 2 else "herbs_dry", length=0.5,
                         width=0.28, string=0.2)

    # ---- the back shelves (shell): cheese on the left half, jars and loaves on the right, baskets on top
    for j, (x0, x1, yl, zf, zb) in enumerate(L.shelf_levels):
        zm = (zf + zb) / 2
        n = 9
        for k in range(n):
            x = x0 + 0.25 + k * (x1 - x0 - 0.5) / (n - 1)
            b = det if k % 3 else stall
            if j == 3:
                if k % 3 == 0:
                    ml.basket(b, "bs_basket_%d" % k, (x, yl, zm), r=0.18, h=0.16, content="m2_bread_top" if k % 2 else "apples", handle=False)
                continue
            left = x < -0.3
            if left:
                if (k + j) % 2 == 0:
                    pm.cheese_wheel(b, "bs_w_%d_%d" % (j, k), (x, yl, zm), r=0.18, h=0.13)
                    pm.cheese_wheel(det, "bs_w2_%d_%d" % (j, k), (x, yl + 0.13, zm), r=0.15, h=0.12, yaw=0.4)
                else:
                    pm.bread(det, "bs_b_%d_%d" % (j, k), (x, yl, zm), yaw=0.2 * (k - 4), l=0.3)
            else:
                if (k + j) % 3 == 0:
                    pm.bread_round(det, "bs_r_%d_%d" % (j, k), (x, yl, zm), r=0.12, h=0.1)
                else:
                    pm.jar(det, "bs_j_%d_%d" % (j, k), (x, yl, zm), r=0.08 + 0.02 * ((k + j) % 2), h=0.2 + 0.06 * (k % 2))

    # ---- the right counter (shell): tomatoes, apples, bread rolls, a planter of greens; the return: cabbages, oranges
    (fx0, fy, fz0, fx1, _, fz1) = L.counter_boxes[0]
    (sx0, sy, sz0, sx1, _, sz1) = L.counter_boxes[1]
    fzm = (fz0 + fz1) / 2
    pm.produce_heap(stall, "crate_tomatoes", (fx0 + 0.38, fy, fzm), size=(0.6, 0.22, 0.5), produce="m2_tomatoes", fruits=5, fruit_r=0.065)
    pm.produce_heap(stall, "crate_apples", (fx0 + 1.0, fy, fzm), size=(0.55, 0.22, 0.5), produce="m2_apples", fruits=5, fruit_r=0.065)
    pm.basket(stall, "basket_rolls", (fx0 + 1.52, fy, fzm), r=0.2, h=0.15, content="m2_bread_top", handle=True)
    for k in range(3):
        pm.bread_round(det, "roll_%d" % k, (fx0 + 1.45 + 0.1 * k, fy + 0.15, fzm - 0.06 + 0.07 * (k % 2)), r=0.08, h=0.08)
    pm.box(stall, "planter", (fx1 - 0.48, fy, fzm - 0.24), (fx1 - 0.06, fy + 0.26, fzm + 0.24), {"all": "m2_terracotta", "+2": "m2_greens"},
           stretch=True)
    for k in range(3):
        pm.cabbage(det, "planter_greens_%d" % k, (fx1 - 0.38 + 0.13 * k, fy + 0.24, fzm - 0.1 + 0.1 * (k % 2)), r=0.09)
    szm = (sx0 + sx1) / 2
    for k, z in enumerate((sz0 + 0.3, sz0 + 0.6, sz0 + 0.9)):
        pm.cabbage(det if k else stall, "cabbage_%d" % k, (szm - 0.1 + 0.12 * (k % 2), sy, z), r=0.13)
    pm.produce_heap(stall, "crate_oranges", (szm, sy, sz0 + 1.55), size=(0.5, 0.2, 0.55), produce="m2_oranges", yaw=math.pi / 2, fruits=4)

    # ---- hams and sausages hanging from the front beam (right half), a small banner by the right post
    beam_y = L.eave_y - 0.17 - 0.16
    for k, x in enumerate((0.85, 1.45, 2.05)):
        ml.beam(det, "ham_hook_%d" % k, v3(x, beam_y + 0.02, hd), v3(x, beam_y - 0.1, hd), 0.03, "iron")
        pm.ham(stall, "ham_%d" % k, (x, beam_y - 0.1, hd), length=0.72 - 0.08 * (k % 2), w=0.42, yaw=0.3 * (k - 1), string=0.4 + 0.1 * (k % 2))
    pm.sausages(det, "sausages_0", v3(0.55, beam_y - 0.05, hd - 0.05), v3(1.15, beam_y - 0.05, hd - 0.05), n=4, sag=0.22)
    pm.sausages(det, "sausages_1", v3(1.15, beam_y - 0.05, hd - 0.05), v3(1.75, beam_y - 0.05, hd - 0.05), n=4, sag=0.18)
    ml.banner(stall, "banner_small", (2.55, beam_y + 0.05, hd + 0.05), 0.55, 0.95, normal=(0, 0, 1), wave=0.03)

    # ---- ivy down the left front post and a vine at the left valance
    px, pz = -hw, hd
    ml.vine(det, "ivy_post_0", (px + 0.2, L.eave_y - 0.25, pz), 1.6, 0.36, normal=(1, 0, 0))
    ml.vine(det, "ivy_post_1", (px, L.eave_y - 0.3, pz + 0.2), 1.1, 0.34, normal=(0, 0, 1))
    ml.vine(det, "ivy_side_0", (px - 0.25, L.eave_y - 0.15, pz - 0.7), 1.3, 0.4, normal=(-1, 0, 0))
    ml.vine(det, "ivy_side_1", (px - 0.25, L.eave_y - 0.15, pz - 1.6), 0.9, 0.4, normal=(-1, 0, 0))

    # ---- by the front left post: a barrel with apples, a crate heaped with bread rolls, sacks
    flx, _, flz = L.front_left
    frx, _, frz = L.front_right
    ml.barrel(stall, "barrel_front", (flx + 0.8, 0.0, flz - 0.1), r=0.42, h=1.0, content="apples")
    ml.crate(stall, "crate_bread", (flx - 0.3, 0.0, flz - 0.35), size=(0.72, 0.5, 0.6), yaw=0.1, content="m2_bread_top")
    for k, (dx, dz) in enumerate(((-0.2, -0.15), (0.05, -0.1), (0.2, 0.05), (-0.1, 0.12), (0.0, -0.02))):
        pm.bread_round(det, "crate_roll_%d" % k, (flx - 0.3 + dx, 0.5 + (0.08 if k == 4 else 0.0), flz - 0.35 + dz), r=0.1, h=0.1)
    ml.sack(stall, "sack_front_0", (flx - 0.55, 0.0, flz + 0.4), s=0.5, yaw=0.3)
    pm.sack(stall, "sack_front_1", (flx + 0.05, 0.0, flz + 0.55), s=0.42, yaw=-0.2, open_top="m2_oranges")

    # ---- mod furniture (Farmer's Delight crates and basket, Icaria barrel, rice bag), stand-ins without the mods
    decor.block("farmersdelight:tomato_crate", frx + 0.15, 0.0, frz - 0.15, facing="front", scale=0.7, fallback="crate")
    decor.block("farmersdelight:cabbage_crate", frx - 0.6, 0.0, frz + 0.05, facing="front", scale=0.6, fallback="crate")
    decor.block("farmersdelight:potato_crate", frx + 0.15, 0.7, frz - 0.15, facing="front", scale=0.55, fallback="crate")
    decor.block("farmersdelight:wooden_basket", 0.55, 0.0, 2.55, facing="front", scale=0.5, fallback="basket")
    decor.block("landsoficaria:cypress_barrel", -hw + 0.6, 0.0, 0.55, facing="pos_x", scale=0.8, alt="minecraft:barrel", fallback="barrel")
    decor.block("farmersdelight:rice_bag", -1.9, 0.0, -1.55, facing="front", scale=0.6, fallback="sack")

    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="yellow", emblem="cheese"))


if __name__ == "__main__":
    main()
