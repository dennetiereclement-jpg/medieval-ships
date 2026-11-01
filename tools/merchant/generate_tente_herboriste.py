#!/usr/bin/env python3
"""tente_herboriste — Tente de l'herboriste / Herbalist Tent (reference: scratchpad/ref/tente_herboriste_ref.png).

The shared merchant pavilion (tools/merchant/merchantlib.py) in green and beige with its ivy option (ivy on the
valance and the posts), the leaf banner, the green flag at the back left; dressed by agent M1
(tools/merchant/props_m1.py): ivy creeping over the roof, bunches of dried herbs and lavender hanging under the front
eave and from two ropes across the tent, terracotta flower pots (white, purple and red flowers, green sprouts) on
the two front counters, their side returns and the back shelves, mossy crates with pots of lavender by the front
posts, crates of the harvest, baskets and barrels (mod furniture when installed).

Usage:  python3 tools/merchant/generate_tente_herboriste.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_herboriste.json, models/entity + blockbench/tente_herboriste.bbmodel,
textures/entity/tente_herboriste.png, textures/item/tente_herboriste.png, interiors/tente_herboriste_decor.json.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m1 as pm  # noqa: E402

NAME = "tente_herboriste"
v3, UP = ml.v3, ml.UP
BUNCHES = ("herbs_dry", "lavender", "herbs", "herbs_dry", "herbs_red", "lavender")


def counters(props, det, L, rng):
    """Flower pots on the two front counters (white / purple / red flowers on the right one, sprouts and lavender on
    the left one), baskets and pots on the side returns."""
    boxes = L.counter_boxes          # right front, right side, left front, left side
    (rx0, y, rz0, rx1, _, rz1), rs, (lx0, _, lz0, lx1, _, lz1), ls = boxes
    # right front counter: two rows of flowering pots
    pm.pot_row(det, "pots_rf_back", rx0 + 0.05, rx1 - 0.05, y, rz0 + 0.22, rng, plants=("flowers_white", "flowers_purple", "flowers_white"),
               rmin=0.1, rmax=0.13)
    pm.pot_row(det, "pots_rf_front", rx0 + 0.15, rx1 - 0.1, y, rz1 - 0.2, rng, plants=("flowers_red", "flowers_white", "sprout"),
               rmin=0.09, rmax=0.12, gap=0.1)
    # left front counter: lavender and sprouts, a jar
    pm.pot_row(det, "pots_lf", lx0 + 0.1, lx1 - 0.35, y, (lz0 + lz1) / 2 + 0.05, rng, plants=("flowers_purple", "sprout", "flowers_purple"),
               rmin=0.1, rmax=0.13, gap=0.08)
    pm.wb.jar(det, "lf_jar", (lx1 - 0.2, y, lz0 + 0.25), r=0.09, h=0.22)
    # side returns: a basket of herbs and pots
    for nm, (sx0, _, sz0, sx1, _, sz1) in (("rs", rs), ("ls", ls)):
        cx = (sx0 + sx1) / 2
        ml.basket(det, nm + "_basket", (cx, y, sz0 + 0.4), r=0.25, h=0.2, content="herbs_box")
        pm.pot(det, nm + "_pot0", (cx - 0.1, y, sz0 + 1.0), r=0.11, h=0.16, plant="sprout")
        pm.pot(det, nm + "_pot1", (cx + 0.12, y, sz0 + 1.35), r=0.1, h=0.15, plant="flowers_red" if nm == "rs" else "flowers_purple")


def shelves(props, det, L, rng):
    """Pots, jars and baskets on the back shelves."""
    lv = sorted(L.shelf_levels, key=lambda s: s[2])
    for i, (x0, x1, y, zf, zb) in enumerate(lv[1:]):
        z = (zf + zb) / 2
        pm.pot_row(det, "shelf_%d" % i, x0 + 0.05, x1 - 0.05, y, z, rng, plants=("sprout", "flowers_white", "flowers_purple", "sprout", "flowers_red"),
                   rmin=0.1, rmax=0.13, gap=0.32)
    x0, x1, y, zf, zb = lv[0]
    z = (zf + zb) / 2
    ml.basket(det, "low_basket0", (x0 + 0.5, y, z), r=0.22, h=0.18, content="herbs_box", handle=False)
    pm.wb.jar(det, "low_jar0", (x0 + 1.2, y, z), r=0.12, h=0.28)
    pm.wb.jar(det, "low_jar1", (x1 - 1.4, y, z), r=0.1, h=0.24)
    ml.basket(det, "low_basket1", (x1 - 0.6, y, z), r=0.22, h=0.18, content="herbs_box", handle=False)


def hanging(det, L, rng):
    """Dried herbs and lavender under the front eave beam and from two ropes strung across the tent."""
    hw, hd, by = L.half_w, L.half_d, L.eave_y - 0.17 - 0.16
    pm.herb_line(det, "herbs_front_l", (-hw + 0.4, by, hd - 0.02), (-0.8, by, hd - 0.02), 4, BUNCHES, rng)
    pm.herb_line(det, "herbs_front_r", (0.8, by, hd - 0.02), (hw - 0.4, by, hd - 0.02), 4, BUNCHES[::-1], rng)
    for k, z in enumerate((1.0, -0.7)):
        pm.herb_rope(det, "herb_rope_%d" % k, (-hw + 0.12, by + 0.04, z), (hw - 0.12, by + 0.04, z), 7, BUNCHES[k:] + BUNCHES[:k], rng)


def outside(props, det, L, rng, decor):
    """Mossy crates with lavender pots by the front posts, a crate of sprouts, barrels and harvest crates."""
    hw, hd = L.half_w, L.half_d
    fl, fr = L.front_left, L.front_right
    pm.mossy_crate(props, det, "crate_fl", (fl[0] - 0.55, 0.0, fl[2] + 0.05), s=0.85, yaw=0.04,
                   pots=((-0.2, -0.15, "flowers_purple", 0.13), (0.18, 0.1, "flowers_purple", 0.12)))
    pm.mossy_crate(props, det, "crate_fl2", (fl[0] + 0.75, 0.0, fl[2] - 0.15), s=0.7, yaw=-0.05,
                   pots=((0.0, 0.0, "flowers_red", 0.12),))
    pm.mossy_crate(props, det, "crate_fr", (fr[0] - 0.7, 0.0, fr[2] + 0.02), s=0.8, yaw=0.03,
                   pots=((-0.2, -0.15, "sprout", 0.11), (0.2, -0.1, "sprout", 0.1), (0.0, 0.18, "flowers_white", 0.11)))
    decor.block("landsoficaria:cypress_barrel", -hw - 0.35, 0.0, hd - 1.2, facing="pos_x", scale=0.85, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("farmersdelight:cabbage_crate", -1.1, 0.0, -1.62, facing="front", scale=0.7, fallback="crate")
    decor.block("farmersdelight:carrot_crate", hw - 0.5, 0.0, -1.65, facing="neg_x", scale=0.7, fallback="crate")
    decor.block("farmersdelight:onion_crate", -hw + 0.5, 0.0, -1.65, facing="pos_x", scale=0.7, fallback="crate")
    decor.block("farmersdelight:wooden_basket", hw + 0.45, 0.0, hd + 0.9, facing="front", scale=0.6, fallback="basket")


def herbs_box_painter(img):
    """Basket / crate filling: a heap of green herbs with a few flowers."""
    rng = random.Random(77)
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            c = rng.choice([(74, 122, 36), (90, 138, 42), (58, 106, 30), (106, 154, 48)])
            if rng.random() < 0.06:
                c = rng.choice([(150, 104, 200), (240, 240, 232), (200, 60, 50)])
            px[x, y] = tuple(max(0, min(255, v + rng.randint(-8, 8))) for v in c) + (255,)


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="green")
    pm.add_regions(atlas, pm.HERB_REGIONS)
    atlas.add("herbs_box", 16, 16, herbs_box_painter)
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="leaf", flag_corner="back_left", side_banners=0, rug=True, lanterns=2,
                    front_counter="both", back_shelves=True, ivy=True)
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1402)
    counters(props, det, L, rng)
    shelves(props, det, L, rng)
    hanging(det, L, rng)
    pm.roof_ivy(det, L, rng, sides=(0, 1, 3), per_side=5)
    decor = ml.Decor()
    outside(props, det, L, rng, decor)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="green", emblem="leaf"))


if __name__ == "__main__":
    main()
