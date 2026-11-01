#!/usr/bin/env python3
"""tente_poison — Tente du vendeur de poisons / Poison Merchant Tent (reference: scratchpad/ref/tente_poison_ref.png).

The gabled market stall of merchantlib.stall in purple and beige: stripes running down the two roof slopes, the dagged
purple and beige valance edged in gold, four squared posts with gold caps, lanterns on the two front posts, the big
purple banner with the skull above the orange flask hanging from a rod on the front-left post; dressed by
tools/merchant/props_m7.py: the black cauldron of glowing green poison on its crate at the front left, the long
counter under a purple runner with gold dags (small bottles, jars, a skull, mushrooms, a bowl of green powder, a
book), the back shelves full of round flasks (purple, green, red, orange), toxic plants and dried herbs hanging from
the rail under the eaves, barrels and crates (mod furniture when installed). No flags, no rug (as on the picture).

Usage:  python3 tools/merchant/generate_tente_poison.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_poison.json, models/entity + blockbench/tente_poison.bbmodel,
textures/entity/tente_poison.png, textures/item/tente_poison.png, interiors/tente_poison_decor.json.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m7 as p7  # noqa: E402

NAME = "tente_poison"
v3, UP = ml.v3, ml.UP
FLASKS = ("purple", "green", "red", "orange", "purple", "green", "purple", "red", "yellow", "orange", "green", "purple")


def counter_goods(props, det, L, rng):
    """The purple runner with gold dags across the middle, small bottles, jars, a skull, mushrooms, a bowl of green
    powder, a closed book on the counter."""
    (x0, y, z0, x1, _, z1), = L.counter_boxes
    p7.runner(props, "runner", 0.45, 1.45, z0, z1, y, hang=0.8)
    yt = y + 0.016
    zc = (z0 + z1) / 2
    # left part: small bottles and a jar, a skull
    for k, (x, c, s) in enumerate(((-0.4, "green", "round"), (-0.18, "purple", "tall"), (0.02, "orange", "round"), (0.25, "red", "flask"))):
        p7.p1.bottle(det, "cb_%d" % k, (x, y, zc + 0.12 * (k % 2 - 0.5)), c, r=0.06 + 0.012 * (k % 2), h=0.15, shape=s, neck_h=0.06)
    p7.wb.jar(det, "c_jar0", (-0.35, y, z0 + 0.15), r=0.08, h=0.18)
    p7.skull(props, "c_skull", (0.78, yt, zc - 0.08), s=0.22, yaw=-0.25)
    p7.bowl(det, "c_bowl", (1.18, yt, zc + 0.06), r=0.11, h=0.06)
    # right part: mushrooms, small boxes, more bottles, a book
    p7.mushrooms(det, "c_mush0", (1.62, y, zc + 0.14), rng, n=4, cap="m7_mush_red")
    p7.mushrooms(det, "c_mush1", (1.66, y, zc - 0.16), rng, n=3, cap="m7_mush_purple")
    ml.crate(props, "c_box0", (1.98, y, zc - 0.06), size=(0.3, 0.2, 0.26), yaw=0.2, solid=False)
    ml.crate(props, "c_box1", (2.0, y + 0.2, zc - 0.04), size=(0.22, 0.14, 0.2), yaw=-0.15, solid=False)
    for k, (x, c) in enumerate(((2.12, "purple"), (2.22, "green"), (1.86, "red"))):
        p7.p1.bottle(det, "cr_%d" % k, (x, y, zc + 0.16 - 0.1 * k), c, r=0.055, h=0.14, shape="tall" if k == 1 else "round", neck_h=0.05)
    p7.wb.book_flat(det, "c_book", (2.0, y, z1 - 0.12), 0.28, 0.07, 0.2, "purple", yaw=0.3)


def shelf_goods(props, det, L, rng):
    """Round flasks on the three upper boards; jars, a skull, books and a glowing vial rack on the lowest one."""
    lv = sorted(L.shelf_levels, key=lambda s: s[2])
    low, upper = lv[0], lv[1:]
    p7.bottle_rows(det, upper, rng, FLASKS, rmin=0.11, rmax=0.15, gap=0.08)
    x0, x1, y, zf, zb = low
    z = (zf + zb) / 2
    p7.wb.jar(det, "low_jar0", (x0 + 0.25, y, z), r=0.12, h=0.28)
    p7.wb.jar(det, "low_jar1", (x0 + 0.6, y, z), r=0.09, h=0.22)
    p7.skull(props, "low_skull", (x0 + 1.05, y, z + 0.02), s=0.24, yaw=0.15)
    p7.wb.book_row(det, "low_books", x0 + 1.4, x0 + 2.0, y, zf - 0.02, 0.36, rng, colors=("purple", "green", "brown"))
    p7.p1.bottle_row(det, "low_vials", x0 + 2.15, x1 - 1.0, y, z, rng, ("green", "purple", "green", "orange"), rmin=0.05, rmax=0.07,
                     gap=0.03)
    p7.mushrooms(det, "low_mush", (x1 - 0.75, y, z), rng, n=5, cap="m7_mush_purple", spread=0.15, s=1.2)
    p7.wb.jar(det, "low_jar2", (x1 - 0.3, y, z), r=0.11, h=0.25)


def herbs(det, L, rng):
    """Toxic plants and dried herbs hanging from the rail under the eaves and from the left side beam."""
    hy, hz = L.hang_y, L.hang_z
    kinds = ("lavender", "m7_toxic", "m7_nightshade", "herbs", "m7_toxic", "m7_nightshade", "herbs_dry")
    p7.herb_row(det, "herbs_rail", -L.half_w + 0.15, L.half_w - 0.15, hy, hz, kinds, rng, n=8, length=(0.8, 1.15), width=0.5)
    hw, hd = L.half_w, L.half_d
    by = L.eave_y - 0.18 - 0.17
    p7.herb_row(det, "herbs_back", -1.6, 1.6, by, -0.6, ("m7_nightshade", "lavender", "m7_toxic", "herbs_dry"), rng, n=4,
                length=(0.6, 0.8))
    for k, z in enumerate((-0.1, 0.55, 1.2)):
        p7.wb.hanging_bunch(det, "herbs_side_%d" % k, (-hw + 0.05, by, z), ("m7_nightshade", "lavender", "m7_toxic")[k],
                            length=0.7 + 0.15 * (k % 2), width=0.4, string=0.08)


def outside(props, det, L, rng, decor):
    """The cauldron on its crate at the front left, a barrel with a small chest outside the front-left post, a crate
    with small boxes at the front right (mod furniture when installed)."""
    hw, hd = L.half_w, L.half_d
    p7.cauldron_on_crate(props, det, (-1.88, 0.0, hd - 0.4), rng, crate=0.76, r=0.46, h=0.52)
    fl = (-hw - 0.58, 0.0, hd - 0.12)
    ml.barrel(props, "barrel_fl", fl, r=0.36, h=0.9)
    ml.crate(props, "barrel_fl_box", (fl[0], 0.9, fl[2]), size=(0.42, 0.18, 0.32), yaw=0.25, solid=False)
    ml.crate(props, "barrel_fl_box2", (fl[0] + 0.03, 1.08, fl[2] + 0.02), size=(0.3, 0.12, 0.24), yaw=-0.2, solid=False)
    ml.barrel(props, "barrel_fl2", (-hw - 0.62, 0.0, hd - 0.92), r=0.32, h=0.8)
    # the crate at the front right with small boxes on it (furnish crate when installed)
    cx, cz, cs = hw - 0.42, hd + 0.62, 0.62
    decor.block("furnish:spruce_crate", cx, 0.0, cz, facing="front", scale=cs, fallback="crate")
    ml.crate(props, "fr_box0", (cx - 0.05, cs, cz + 0.02), size=(0.36, 0.16, 0.28), yaw=0.15, solid=False)
    ml.crate(props, "fr_box1", (cx + 0.02, cs + 0.16, cz), size=(0.24, 0.12, 0.2), yaw=-0.25, solid=False)
    p7.p1.bottle(det, "fr_bottle", (cx + 0.2, cs, cz - 0.16), "purple", r=0.05, h=0.13)


def inside(props, det, L, rng, decor):
    """Behind the counter: a lying barrel and a crate stack in the back corners, a sack; the merchant's place stays
    free (x 0.6 .. 1.6, z 0.3 .. 1.3)."""
    hw, hd = L.half_w, L.half_d
    decor.block("landsoficaria:loaded_cypress_barrel", hw - 0.55, 0.0, -0.95, facing="neg_x", scale=0.8, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("furnish:spruce_crate", -hw + 0.6, 0.0, -1.2, facing="front", scale=0.7, fallback="crate")
    ml.crate(props, "in_box", (-hw + 0.6, 0.7, -1.2), size=(0.44, 0.3, 0.4), yaw=0.2, solid=False)
    ml.sack(props, "in_sack", (-hw + 0.65, 0.0, -0.3), s=0.45, yaw=0.3)
    decor.block("farmhouse_decorations:wine_bottle", -0.5, L.counter_top_y, L.half_d - 0.48, facing="front", solid=False,
                fallback="potion_green")
    decor.block("farmhouse_decorations:red_wine_bottle", 2.12, L.counter_top_y, L.half_d - 0.98, facing="front", solid=False,
                fallback="potion_red")


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="purple")
    p7.add_regions(atlas, p7.POISON_REGIONS)
    root = ml.Bone(NAME)
    L = ml.stall(root, atlas, emblem="poison", lanterns=2, front_counter=True, back_shelves=True, banner_side="left")
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1601)
    decor = ml.Decor()
    counter_goods(props, det, L, rng)
    shelf_goods(props, det, L, rng)
    herbs(det, L, rng)
    outside(props, det, L, rng, decor)
    inside(props, det, L, rng, decor)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="purple", emblem="poison", shape="stall"))


if __name__ == "__main__":
    main()
