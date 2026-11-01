#!/usr/bin/env python3
"""tente_alchimiste — Tente du marchand d'alchimie / Alchemy Merchant Tent (reference: scratchpad/ref/tente_alchimiste_ref.png).

The shared merchant pavilion (tools/merchant/merchantlib.py) in purple and beige with gold trim, the potion-flask
banner at the front, the purple flag at the back left; dressed by agent M1 (tools/merchant/props_m1.py): the back
shelves full of coloured potion bottles, the bubbling purple cauldron with its glowing amethyst cluster at the left
front, big orange / green / red flasks on the left counter, an open book on a purple gold-fringed cloth on the right
counter, candles, jars, a scroll, bunches of herbs hanging under the eaves, iron-banded crates and barrels by the
front posts (mod furniture when installed).

Usage:  python3 tools/merchant/generate_tente_alchimiste.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_alchimiste.json, models/entity + blockbench/tente_alchimiste.bbmodel,
textures/entity/tente_alchimiste.png, textures/item/tente_alchimiste.png, interiors/tente_alchimiste_decor.json.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m1 as pm  # noqa: E402

NAME = "tente_alchimiste"
v3, UP = ml.v3, ml.UP
COLOURS = ("purple", "blue", "green", "red", "pink", "orange", "cyan", "violet", "purple", "blue", "violet")


def left_counter(props, det, L, rng):
    """The left front counter (mirror of the shell's right one): big flasks, small bottles, a glowing crystal, a jar."""
    hd = L.half_d
    z0, z1 = hd - 1.35, hd - 0.65
    top = ml.counter(props, "counter_left", -1.95, -0.6, z0, z1, h=1.0, detail=det)
    y = top[1]
    pm.big_flasks(props, det, [(-1.62, y, z1 - 0.3), (-1.2, y, z1 - 0.22), (-0.86, y, z0 + 0.3)], ["orange", "green", "red"])
    pm.bottle(det, "lc_b0", (-1.42, y, z0 + 0.22), "purple", r=0.06, h=0.18, shape="tall")
    pm.bottle(det, "lc_b1", (-0.82, y, z1 - 0.18), "cyan", r=0.065, h=0.14)
    pm.wb.jar(det, "lc_jar", (-1.8, y, z0 + 0.2), r=0.08, h=0.18)
    pm.wb.crystal_cluster(det, "lc_crystal", (-1.05, y, z0 + 0.18), "purple", rng, n=4, h=0.3, w=0.08, spread=0.07)
    return top


def right_counters(props, det, L, rng):
    """The shell's right L counter: the purple gold-fringed cloth and the open book on the front piece, candles, bottles
    and a scroll; jars, books and bottles on the side return."""
    (fx0, y, fz0, fx1, _, fz1), (sx0, _, sz0, sx1, _, sz1) = L.counter_boxes[0], L.counter_boxes[1]
    cx0 = fx0 + 0.75
    ml.table_cloth(props, "book_cloth", cx0, fx1 + 0.02, fz0, fz1 + 0.02, y, hang=0.5, sides=("front",))
    pm.wb.open_book(props, "book", ((cx0 + fx1) / 2, y + 0.015, (fz0 + fz1) / 2 + 0.03), w=0.78, d=0.5, yaw=-0.12, cover="book_red",
                    glow=False, tilt=0.18, lift=0.04)
    pm.wb.candle(det, "candle_a", (fx0 + 0.18, y, fz0 + 0.22), h=0.34, r=0.06, holder="brass")
    pm.wb.candle(det, "candle_b", (fx0 + 0.42, y, fz0 + 0.14), h=0.2, r=0.05, holder="brass")
    pm.bottle(det, "rc_b0", (fx0 + 0.3, y, fz1 - 0.18), "blue", r=0.07, h=0.16)
    pm.bottle(det, "rc_b1", (fx0 + 0.55, y, fz1 - 0.2), "pink", r=0.055, h=0.18, shape="tall")
    # the side return: books, jars, bottles
    pm.wb.book_stack(det, "rs_books", ((sx0 + sx1) / 2, y, sz1 - 0.35), 3, rng, w=0.36, d=0.26, colors=("purple", "red", "brown"),
                     yaw=1.57)
    pm.wb.jar(det, "rs_jar0", ((sx0 + sx1) / 2 - 0.12, y, sz0 + 0.3), r=0.09, h=0.22)
    pm.wb.jar(det, "rs_jar1", ((sx0 + sx1) / 2 + 0.14, y, sz0 + 0.55), r=0.07, h=0.17)

    for k, (dz, c) in enumerate(((0.95, "green"), (1.15, "purple"), (1.32, "orange"))):
        pm.bottle(det, "rs_b%d" % k, ((sx0 + sx1) / 2 + 0.1 * (k % 2), y, sz0 + dz), c, r=0.065, h=0.16)
    pm.wb.parchment(det, "rs_scroll", ((sx0 + sx1) / 2, y + 0.005, sz1 - 0.95), w=0.26, d=0.34, yaw=0.5)


def shelves(props, det, L, rng):
    """Potions on the three upper boards, jars, big bottles and two glowing crystal clusters on the lowest one."""
    lv = sorted(L.shelf_levels, key=lambda s: s[2])
    low, upper = lv[0], lv[1:]
    for i, (x0, x1, y, zf, zb) in enumerate(upper):
        z = (zf + zb) / 2
        pm.bottle_row(det, "shelf_%d" % i, x0 + 0.05, x1 - 0.05, y, z, rng, COLOURS, rmin=0.115, rmax=0.155, gap=0.1)
    x0, x1, y, zf, zb = low
    z = (zf + zb) / 2
    xs = [x0 + 0.3, x0 + 0.85, x0 + 1.5, x1 - 1.6, x1 - 0.95, x1 - 0.35]
    pm.wb.jar(det, "low_jar0", (xs[0], y, z), r=0.13, h=0.3)
    pm.wb.crystal_cluster(props, "low_crystal0", (xs[1], y, z), "purple", rng, n=5, h=0.42, w=0.11, spread=0.1)
    pm.bottle(det, "low_big0", (xs[2], y, z), "green", r=0.13, h=0.26, neck_h=0.1)
    pm.wb.book_row(det, "low_books", xs[3] - 0.25, xs[3] + 0.35, y, zf - 0.02, 0.36, rng, colors=("purple", "red", "brown", "blue"))
    pm.wb.crystal_cluster(props, "low_crystal1", (xs[4], y, z), "purple", rng, n=4, h=0.36, w=0.1, spread=0.09)
    pm.wb.jar(det, "low_jar1", (xs[5], y, z), r=0.11, h=0.26)


def herbs(det, L, rng):
    """Bunches of dried herbs hanging under the front and side eave beams."""
    hw, hd, by = L.half_w, L.half_d, L.eave_y - 0.17 - 0.16
    kinds = ("herbs", "herbs_dry", "herbs_red", "lavender")
    pm.herb_line(det, "herbs_front_l", (-hw + 0.45, by, hd - 0.02), (-0.75, by, hd - 0.02), 4, kinds, rng)
    pm.herb_line(det, "herbs_front_r", (0.75, by, hd - 0.02), (hw - 0.45, by, hd - 0.02), 4, kinds[::-1], rng)
    pm.herb_line(det, "herbs_left", (-hw + 0.02, by, -hd + 0.9), (-hw + 0.02, by, hd - 0.6), 4, kinds, rng)
    pm.herb_line(det, "herbs_right", (hw - 0.02, by, -hd + 0.9), (hw - 0.02, by, hd - 0.6), 4, kinds[1:], rng)


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="purple")
    pm.add_regions(atlas, pm.ALCH_REGIONS)
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="flask", flag_corner="back_left", side_banners=0, rug=True, lanterns=2,
                    front_counter="right", back_shelves=True)
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1401)
    hw, hd = L.half_w, L.half_d
    # the cauldron with the glowing amethyst cluster at the left front
    pm.cauldron_crystal(props, det, (-hw - 0.1, 0.0, hd - 1.35), rng, r=0.5, h=0.58)
    left_counter(props, det, L, rng)
    right_counters(props, det, L, rng)
    shelves(props, det, L, rng)
    herbs(det, L, rng)
    # iron-banded crates by the front posts (ours, the pictured ones), a small chest on the right one
    fl, fr = L.front_left, L.front_right
    ml.crate(props, "crate_fl", (fl[0] - 0.6, 0.0, fl[2] + 0.03), size=0.85, yaw=0.05, solid=True)
    ml.crate(props, "crate_fl2", (fl[0] + 0.75, 0.0, fl[2] - 0.2), size=(0.75, 0.75, 0.7), yaw=-0.04, solid=True)
    ml.crate(props, "crate_fl_small", (fl[0] + 1.32, 0.0, fl[2] - 0.05), size=0.42, yaw=-0.25, solid=True)
    pm.bottle(det, "crate_bottle", (fl[0] - 0.45, 0.85, fl[2] + 0.1), "orange", r=0.09, h=0.2)
    ml.crate(props, "crate_fr", (fr[0] - 0.75, 0.0, fr[2] - 0.02), size=0.8, yaw=-0.06, solid=True)
    # mod furniture (drawn when the mod is installed; vanilla barrel / stand-in otherwise)
    decor = ml.Decor()
    decor.block("landsoficaria:cypress_barrel", -hw - 0.25, 0.0, 0.35, facing="pos_x", scale=0.85, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("landsoficaria:cypress_barrel", hw + 0.4, 0.0, hd + 0.95, facing="front", scale=0.8, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("furnish:spruce_crate", hw - 0.55, 0.0, -0.95, facing="neg_x", scale=0.7, fallback="crate")
    sx = (L.counter_boxes[1][0] + L.counter_boxes[1][3]) / 2
    decor.block("farmhouse_decorations:pile_of_books", sx - 0.45, L.counter_top_y, 0.15, facing="neg_x", scale=0.9,
                fallback="book_purple", solid=False)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="purple", emblem="flask"))


if __name__ == "__main__":
    main()
