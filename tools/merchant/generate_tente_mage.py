#!/usr/bin/env python3
"""tente_mage — Tente du vendeur de mage / Mage Merchant Tent (reference: scratchpad/ref/tente_mage_ref.png).

The shared merchant pavilion (tools/merchant/merchantlib.py) in purple and beige with gold trim and a lower roof
(roof_rise 2.3), the purple banner with the gold eight-pointed star hanging at the front left, the purple flag at the
back left; dressed by agent M5 (tools/merchant/props_m5.py): the back shelves with a big glowing blue crystal
cluster, purple and blue crystals and rows of glowing potions; the central counter under a purple cloth with a
gold-starred flap, a propped purple grimoire with its gold sigil and an open book on a little lectern; the glowing
orb in its gold ring on a turned stand; four mage staffs with crystal heads (purple, violet, blue) in their rack at
the right; crates topped with a glowing amethyst cluster at the left, an iron-banded chest, a barrel of wands; potions
and a crystal hanging from the front eave; lanterns on the front posts, the purple rug. Crystals, orb and potions
are lit (full bright), no particles.

Usage:  python3 tools/merchant/generate_tente_mage.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_mage.json, models/entity + blockbench/tente_mage.bbmodel,
textures/entity/tente_mage.png, textures/item/tente_mage.png, interiors/tente_mage_decor.json.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m5 as pm  # noqa: E402

NAME = "tente_mage"
v3, UP, X, Z = ml.v3, ml.UP, ml.X, ml.Z
BANNER_X = -1.85     # the front banner hangs at the left of the front (as pictured)
POTIONS = ("purple", "blue", "pink", "purple", "cyan", "blue", "red", "purple", "green", "blue")


def shift_banner(L, dx, dy=0.3):
    """Moves the shell's front banner (and its rod) sideways and up (it hangs from the roof edge, as pictured), two
    dark straps holding its rod ends to the roof."""
    for c in L.shell.cubes:
        if c.name.startswith("banner_front"):
            c.center = c.center + v3(dx, dy, 0)
    zr = L.half_d + 0.34 + 0.1 + 0.02
    for k, sx in enumerate((-1, 1)):
        x = dx + sx * (1.35 / 2 + 0.06)
        ml.beam(L.detail, "banner_strap_%d" % k, (x, L.eave_y + 0.17 + dy, zr), (x, L.eave_y + 0.22, L.half_d + 0.1), 0.04, "leather_dark")


def bottle_row(det, name, x0, x1, y, z, rng, colours, rmin=0.08, rmax=0.12, gap=0.05):
    """Lit potion bottles side by side along x (round, tall and flat flasks mixed)."""
    x, k = x0, 0
    shapes = ("round", "round", "tall", "flask")
    while True:
        r = rng.uniform(rmin, rmax)
        if x + 2 * r > x1:
            break
        sh = shapes[k % len(shapes)] if k % 3 else "round"
        ml.bottle(det, "%s_%d" % (name, k), (x + r, y, z + rng.uniform(-0.04, 0.04)), colour=colours[k % len(colours)], r=r,
                  h=r * rng.uniform(1.7, 2.3), neck_h=r * 0.7, shape=sh, glow=True)
        x += 2 * r + gap
        k += 1


def shelves(props, det, L, rng):
    """The back shelves: the big blue crystal cluster and purple potions on the top board, rows of potions, books,
    a small purple cluster."""
    lv = sorted(L.shelf_levels, key=lambda s: s[2])
    (ax0, ax1, ya, zfa, zba), (bx0, bx1, yb, zfb, zbb), (cx0, cx1, yc, zfc, zbc), (dx0, dx1, yd, zfd, zbd) = lv
    z = (zfd + zbd) / 2
    p1 = pm.p1
    p1.wb.crystal_cluster(props, "crys_top", (dx0 + 0.7, yd, z), "blue", rng, n=6, h=0.62, w=0.16, spread=0.15)
    bottle_row(det, "pot_top_a", dx0 + 1.15, dx0 + 2.6, yd, z, rng, ("purple", "blue", "purple", "cyan"), rmin=0.12, rmax=0.15, gap=0.08)
    p1.wb.crystal_cluster(props, "crys_top2", (dx1 - 1.95, yd, z), "purple", rng, n=4, h=0.38, w=0.11, spread=0.1)
    bottle_row(det, "pot_top_b", dx1 - 1.6, dx1 - 0.1, yd, z, rng, ("blue", "purple", "pink", "purple"), rmin=0.11, rmax=0.14, gap=0.08)
    z = (zfc + zbc) / 2
    bottle_row(det, "pot_mid", cx0 + 0.15, cx1 - 0.1, yc, z, rng, POTIONS, rmin=0.11, rmax=0.15, gap=0.12)
    z = (zfb + zbb) / 2
    p1.wb.book_row(det, "books_b", bx0 + 0.1, bx0 + 1.1, yb, zfb - 0.02, 0.34, rng, colors=("purple", "blue", "red", "brown"))
    p1.wb.crystal_cluster(props, "crys_low", (bx0 + 1.5, yb, z), "violet", rng, n=4, h=0.34, w=0.1, spread=0.09)
    bottle_row(det, "pot_low", bx0 + 1.9, bx1 - 0.1, yb, z, rng, POTIONS[3:], rmin=0.11, rmax=0.14, gap=0.14)


def counter(props, det, L, rng):
    """The central counter: purple cloth, the gold-starred flap (the tent's banner region), the grimoire propped up,
    the open book on its lectern, a candle and a small crystal."""
    hd = L.half_d
    x0, x1, z0, z1 = -1.55, 0.85, hd - 1.38, hd - 0.68
    top = ml.counter(props, "counter_main", x0, x1, z0, z1, h=1.0, detail=det)
    y = top[1]
    ml.table_cloth(props, "cloth_main", x0 - 0.02, x1 + 0.02, z0 - 0.02, z1 + 0.06, y, hang=0.22, sides=("front", "left", "right"))
    ml.banner(props, "counter_flap", (-0.32, y + 0.005, z1 + 0.09), 0.95, 0.86, normal=(0, 0, 1), rod=False, wave=0.015)
    y += 0.015
    pm.grimoire(props, "grimoire", (-1.05, y, (z0 + z1) / 2 + 0.05), yaw=0.18, w=0.5, h=0.62, th=0.12, lean=0.42)
    pm.lectern_book(props, "open_book", (-0.12, y, (z0 + z1) / 2 + 0.02), yaw=-0.12, w=0.66, d=0.44)
    pm.p1.wb.candle(det, "candle", (0.6, y, z0 + 0.2), h=0.26, r=0.05, holder="brass")
    pm.p1.wb.crystal_cluster(det, "counter_crys", (0.55, y, z1 - 0.2), "purple", rng, n=3, h=0.24, w=0.08, spread=0.07)
    ml.bottle(det, "counter_pot", (-1.42, y, z0 + 0.15), colour="blue", r=0.08, h=0.17, glow=True)
    return (x0, x1, z0, z1)


def staffs(props, det, L, rng):
    """Four staffs in a rack at the right: crystal heads purple, violet, purple, blue."""
    hw, hd = L.half_w, L.half_d
    x0, x1, z = 1.98, 2.86, hd - 1.0
    ml.box(props, "staff_rack_base", (x0, 0.0, z - 0.2), (x1, 0.28, z + 0.2), {"all": "crate", "+2": "plank_dark"}, solid=True)
    for k, x in enumerate((x0, x1)):
        ml.box(props, "staff_rack_up_%d" % k, (x - 0.05, 0.0, z - 0.28), (x + 0.05, 1.7, z - 0.18), "wood_dark")
    ml.box(props, "staff_rack_rail", (x0 - 0.06, 1.6, z - 0.29), (x1 + 0.06, 1.7, z - 0.17), "wood", u_dir=X)
    heads = (("purple", 2.38), ("violet", 2.2), ("purple", 2.48), ("blue", 2.28))
    for k, (hc, ht) in enumerate(heads):
        x = x0 + 0.13 + (x1 - x0 - 0.26) * k / 3
        lean = (k - 1.5) * 0.035
        pm.staff(det if k % 2 else props, "staff_%d" % k, (x, 0.2, z), (x + lean, ht, z - 0.2), head=hc,
                 crystal_h=0.44 if k % 2 == 0 else 0.36, crystal_w=0.17 if k % 2 == 0 else 0.15)
    ml.collide((x0 - 0.06, 0.0, z - 0.3, x1 + 0.06, 1.7, z + 0.2))


def left_side(props, det, L, rng, decor):
    """Left: crates topped with a glowing amethyst cluster; a chest and a crate stack before the post; a barrel of
    wands outside."""
    hw, hd = L.half_w, L.half_d
    ml.crate(props, "crate_l0", (-2.42, 0.0, hd - 1.05), size=(0.78, 0.72, 0.7), yaw=0.04)
    ml.crate(props, "crate_l1", (-2.4, 0.72, hd - 1.08), size=(0.58, 0.48, 0.55), yaw=-0.08)
    pm.p1.wb.crystal_cluster(props, "crys_left", (-2.4, 1.2, hd - 1.08), "purple", rng, n=6, h=0.58, w=0.14, spread=0.13)
    pm.chest(props, "chest", (-2.2, 0.0, hd + 0.5), w=0.86, h=0.62, d=0.56, yaw=0.12)
    ml.crate(props, "crate_f0", (-1.45, 0.0, hd + 0.22), size=(0.7, 0.62, 0.62), yaw=-0.06)
    ml.crate(props, "crate_f1", (-1.49, 0.62, hd + 0.22), size=(0.46, 0.4, 0.44), yaw=0.15)
    ml.bottle(det, "crate_pot", (-1.49, 1.02, hd + 0.22), colour="purple", r=0.09, h=0.18, shape="round", glow=True)
    decor.block("landsoficaria:cypress_barrel", -hw - 0.42, 0.0, hd - 0.85, facing="pos_x", scale=0.82, alt="minecraft:barrel",
                fallback="barrel")
    pm.wands(det, "wands", (-hw - 0.42, 0.66, hd - 0.85), n=6, h=0.62, spread=0.15, seed=3)


def hanging(det, L, rng):
    """Potions and a crystal hanging from the front eave beam."""
    hd, by = L.half_d, L.eave_y - 0.17 - 0.16
    pm.hanging_flask(det, "hang_0", (-0.55, by, hd - 0.05), colour="purple", drop=0.32, r=0.09, h=0.18)
    pm.hanging_flask(det, "hang_1", (0.45, by, hd - 0.05), colour="red", drop=0.22, r=0.07, h=0.15, shape="flask")
    pm.crystal_pendant(det, "hang_2", (1.0, by, hd - 0.05), colour="purple", drop=0.4)
    pm.hanging_flask(det, "hang_3", (1.75, by, hd - 0.05), colour="blue", drop=0.28, r=0.07, h=0.15)


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="purple")
    pm.add_regions(atlas, pm.MAGE_REGIONS)
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="star", flag_corner="back_left", side_banners=0, rug=False, lanterns=2,
                    front_counter=False, back_shelves=True, roof_rise=2.3)
    shift_banner(L, BANNER_X)
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1502)
    hw, hd = L.half_w, L.half_d
    ml.rug(L.shell, "rug", -0.75, 2.05, hd + 0.45, hd + 2.2)
    L.rug_box = (-0.75, hd + 0.45, 2.05, hd + 2.2)
    shelves(props, det, L, rng)
    counter(props, det, L, rng)
    pm.orb_stand(props, det, "orb", (1.42, 0.0, hd - 1.3), h=1.42, r=0.24)
    staffs(props, det, L, rng)
    decor = ml.Decor()
    left_side(props, det, L, rng, decor)
    hanging(det, L, rng)
    ml.crate(props, "crate_fr", (2.45, 0.0, hd + 0.3), size=(0.66, 0.6, 0.6), yaw=-0.05)
    # mod furniture (drawn when the mod is installed; stand-ins otherwise)
    decor.block("furnish:spruce_crate", hw + 0.42, 0.0, hd - 0.9, facing="neg_x", scale=0.7, fallback="crate")
    decor.block("landsoficaria:purple_storage_vase", -hw + 0.55, 0.0, -0.9, facing="pos_x", scale=0.62, fallback="cloth")
    decor.block("furnish:book_pile", 0.62, 1.0, -hd + 0.48, facing="front", scale=0.7, fallback="book_purple", solid=False)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="purple", emblem="star"))


if __name__ == "__main__":
    main()
