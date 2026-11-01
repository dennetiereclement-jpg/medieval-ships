#!/usr/bin/env python3
"""tente_boucher — Tente du boucher / Butcher's Tent (reference: scratchpad/ref/tente_boucher_ref.png).

The gabled market stall of merchantlib.stall in red and beige: stripes running down the two roof slopes, the dagged
red and beige valance edged in gold, four squared posts with gold caps, lanterns on the two front posts, the big red
banner with the two crossed cleavers hanging from a rod on the front-left post; dressed by
tools/merchant/props_m7.py: big pieces of meat hanging on chains from the rail under the eaves (a ham, three strings
of sausages, a side of pork with its ribs), more on the left side and along the back wall, the long counter covered
with raw steaks and cuts, a cream cloth with red dags hanging at its front, the big round chopping block with a
cleaver stuck in it at the front left, a barrel heaped with meat outside the left post, a crate of steaks before the
counter, shelves of crocks and salt at the back, a knife board, barrels and crates (mod furniture when installed).
No flags, no rug (as on the picture).

Usage:  python3 tools/merchant/generate_tente_boucher.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_boucher.json, models/entity + blockbench/tente_boucher.bbmodel,
textures/entity/tente_boucher.png, textures/item/tente_boucher.png, interiors/tente_boucher_decor.json.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m7 as p7  # noqa: E402

NAME = "tente_boucher"
v3, UP = ml.v3, ml.UP


def counter_goods(props, det, L, rng, decor):
    """Raw steaks and cuts all along the counter, the cream cloth with red dags at its front, a cutting board (mod)."""
    (x0, y, z0, x1, _, z1), = L.counter_boxes
    p7.runner(props, "cloth", 0.85, 1.95, z0, z1, y, hang=0.86, region="m7_cloth_cream", top_region="m7_cloth_cream_top")
    yt = y + 0.016
    zc = (z0 + z1) / 2
    decor.block("farmersdelight:cutting_board", -0.22, y, zc, facing="front", scale=0.62, solid=False, fallback="plank")
    p7.steak(props, "board_steak", (-0.25, y + 0.04, zc + 0.02), w=0.36, d=0.24, th=0.09, yaw=0.2)
    p7.steak_pile(props, "pile_l", (0.4, y, zc), rng, n=3, w=0.4, d=0.26, th=0.1)
    for k, (x, yaw) in enumerate(((1.05, -0.15), (1.5, 0.12), (1.92, -0.08))):
        p7.steak(props, "steak_%d" % k, (x, yt, zc + 0.05 * (k % 2)), w=0.46, d=0.28, th=0.12, yaw=yaw)
    p7.steak(props, "steak_back", (1.3, yt, z0 + 0.12), w=0.34, d=0.2, th=0.08, yaw=0.3)
    p7.steak(props, "steak_r", (2.1, y, z0 + 0.14), w=0.3, d=0.22, th=0.08, yaw=0.6)
    # a cleaver lying flat on the counter
    p7.box(props, "flat_cleaver_blade", (0.62, yt, z0 + 0.06), (0.92, yt + 0.02, z0 + 0.24), {"all": "steel", "+2": "m7_blade"})
    p7.box(props, "flat_cleaver_handle", (0.92, yt, z0 + 0.12), (1.18, yt + 0.04, z0 + 0.17), "wood_dark")


def hanging(props, det, L, rng):
    """The ham, three strings of sausages and the side of pork on chains from the rail; a ham and a string on the left
    side beam."""
    hy, hz = L.hang_y, L.hang_z
    t = p7.hook(det, "hook_ham", (-0.6, hy, hz), drop=0.42)
    p7.ham(props, "ham_front", t, length=1.1, w=0.74, yaw=0.3)
    for k, x in enumerate((0.12, 0.58, 1.04)):
        t = p7.hook(det, "hook_saus_%d" % k, (x, hy, hz), drop=0.3 + 0.06 * (k % 2))
        p7.sausage_string(props, "sausages_%d" % k, t, n=5, link=0.22, r=0.17, seed=k)
    t = p7.hook(det, "hook_side", (1.78, hy, hz), drop=0.3)
    p7.carcass(props, "pork_side", t, w=0.95, h=1.35, yaw=0.0)
    # the left side: a smaller ham and a string from the side beam
    hw = L.half_w
    by = L.eave_y - 0.18 - 0.17
    t = p7.hook(det, "hook_side_ham", (-hw + 0.08, by, 0.9), drop=0.3)
    p7.ham(props, "ham_side", t, length=0.9, w=0.6, yaw=1.2)
    t = p7.hook(det, "hook_side_saus", (-hw + 0.08, by, 0.25), drop=0.25)
    p7.sausage_string(props, "sausages_side", t, n=5, link=0.2, r=0.14, seed=7)


def back(props, det, L, rng, decor):
    """Along the back wall: a rail of hams and sausages over the left half, the knife board, a lying barrel and crates
    (mod furniture when installed); shelves of crocks, salt and bowls on the right half."""
    hw, hd = L.half_w, L.half_d
    zb = -hd + 0.4
    ml.beam(props, "back_rail", (-hw + 0.1, 3.05, zb), (0.2, 3.05, zb), 0.12, "wood_dark")
    for k, x in enumerate((-1.95, -1.2, -0.45)):
        t = p7.hook(det, "back_hook_%d" % k, (x, 2.98, zb), drop=0.18)
        if k == 1:
            p7.sausage_string(props, "back_sausages", t, n=5, link=0.2, r=0.14, seed=11)
        else:
            p7.ham(props, "back_ham_%d" % k, t, length=0.85, w=0.56, yaw=0.5 * k)
    p7.knife_rack(props, "knives", -1.9, -0.6, 1.95, -hd - 0.02, n=5)
    decor.block("landsoficaria:cypress_barrel", -1.55, 0.0, -hd + 0.55, facing="pos_x", scale=0.85, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("furnish:spruce_crate", -hw + 0.5, 0.0, -hd + 0.5, facing="front", scale=0.7, fallback="crate")
    decor.block("furnish:spruce_crate", -hw + 0.5, 0.7, -hd + 0.5, facing="front", scale=0.55, fallback="crate")
    levels = ml.shelf_unit(props, "shelves", 0.35, hw - 0.35, -hd + 0.12, -hd + 0.6, levels=(0.55, 1.15, 1.75), h=2.15, back=False,
                           uprights=3, detail=det)
    for i, (x0, x1, y, zf, zbk) in enumerate(levels):
        z = (zf + zbk) / 2
        xs = [x0 + 0.2 + k * (x1 - x0 - 0.4) / 3 for k in range(4)]
        for k, x in enumerate(xs):
            kind = (i + k) % 3
            if kind == 0:
                p7.wb.jar(det, "crock_%d_%d" % (i, k), (x, y, z), r=0.11 + 0.02 * (k % 2), h=0.26)
            elif kind == 1:
                p7.wb.octo(det, "salt_%d_%d" % (i, k), (x, y, z), 0.14, 0.14, {"all": "wood_dark", "+2": "m7_salt"}, stretch=True)
            else:
                p7.steak_pile(props, "shelf_meat_%d_%d" % (i, k), (x, y, z), rng, n=2, w=0.3, d=0.2, th=0.07)
    ml.sack(props, "salt_sack", (1.2, 0.0, -hd + 0.95), s=0.45, yaw=0.4)


def front(props, det, L, rng):
    """The chopping block at the front left, the barrel heaped with meat outside the left post, the crate of steaks
    before the counter, a second barrel beside the first."""
    hw, hd = L.half_w, L.half_d
    p7.chopping_block(props, det, (-1.8, 0.0, hd - 0.5), rng, r=0.55, h=1.0)
    fl = (-hw - 0.58, 0.0, hd - 0.12)
    ml.barrel(props, "barrel_fl", fl, r=0.37, h=0.9, content="m7_steak_heap")
    p7.steak_pile(props, "barrel_meat", (fl[0], 0.9, fl[2]), rng, n=4, w=0.34, d=0.22, th=0.1)
    ml.barrel(props, "barrel_fl2", (-hw - 0.62, 0.0, hd - 0.92), r=0.33, h=0.8)
    cx, cz, cs = -0.62, hd + 0.62, 0.56
    ml.crate(props, "crate_meat", (cx, 0.0, cz), size=cs, yaw=0.0, solid=True)
    p7.steak_pile(props, "crate_steaks", (cx, cs, cz), rng, n=3, w=0.3, d=0.2, th=0.09)


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    p7.add_regions(atlas, p7.BUTCHER_REGIONS)
    root = ml.Bone(NAME)
    L = ml.stall(root, atlas, emblem="cleavers", lanterns=2, front_counter=True, back_shelves=False, banner_side="left")
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1602)
    decor = ml.Decor()
    counter_goods(props, det, L, rng, decor)
    hanging(props, det, L, rng)
    back(props, det, L, rng, decor)
    front(props, det, L, rng)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="red", emblem="cleavers", shape="stall"))


if __name__ == "__main__":
    main()
