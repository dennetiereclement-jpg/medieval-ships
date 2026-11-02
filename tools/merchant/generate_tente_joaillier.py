#!/usr/bin/env python3
"""tente_joaillier — Tente du joaillier / Jeweller's Tent (1.21.0; reference picture described in the brief).

A rectangular merchant tent, wider than deep (about 8 x 5.5 blocks, the open front at +z), on the gabled stall of
merchantlib.stall in purple and beige: four thick dark posts with iron bands and gold caps, the heavy front beam with
iron straps, the roof striped down its two slopes with, in its centre, a raised pointed pavilion peak (purple and beige
gores, a wooden finial with a gold knob and spire), the left end of the roof sloping down further over the left wall,
the dagged beige and purple valance edged in gold; dressed by tools/merchant/props_m10.py: draped curtain walls in big
harlequin quarters on the sides and the back (purple drapes inside at the back), the side curtains tied back near the
front posts, two tie beams and an angled brace inside on the left, two purple banners with dagged gold edges and the
gold diamond (the big one from the front-left post's bracket, one on the front-right post), a lantern under the front
beam by the left post, one on the right post, a small chained lantern inside (mod block when installed); the left
counter under a purple cloth with gold dags (three black velvet busts with gold necklaces set with a ruby, a sapphire,
an emerald, two ring trays, drawers with iron latches); the shelves at the back (jewellery coffers, one open with a
necklace, gem crystals, a bust with a necklace on top); the right counter at the back right (a tray of cut gems, a
bust, the glass vitrine with the golden crown set with rubies, drawers), the gold balance hanging above it (an
amethyst and an emerald on its pans); outside the crate of crystal clusters (amethyst clusters, green and red
crystals) at the front left and the iron-banded treasure chest at the front right; the purple rug with the gold
diamond in the open middle. The anchor block gives light 12. No flags.

Usage:  python3 tools/merchant/generate_tente_joaillier.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_joaillier.json, models/entity + blockbench/tente_joaillier.bbmodel,
textures/entity/tente_joaillier.png, textures/item/tente_joaillier.png, interiors/tente_joaillier_decor.json.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m10 as p10  # noqa: E402

NAME = "tente_joaillier"
v3, UP = ml.v3, ml.UP
HW, HD, EAVE, RISE = 3.6, 2.35, 3.45, 1.35
BY = EAVE - 0.18              # the eave beams' axis
TIE_X = (-2.3, 2.2)           # the two tie beams across the tent (along z)
LEFT_COUNTER = (-3.15, -1.2, 1.0, 1.7)     # x0, x1, z0, z1
RIGHT_COUNTER = (1.25, 3.2, -1.05, -0.4)
NPC_SPOT = (1.6, -2.2, 2.6, -1.2)          # x0, z0, x1, z1: the merchant's free place behind the right counter
RUG = (-1.2, 1.2, 0.4, 2.0)


def frame(L):
    """The tie beams across the tent under the eaves and the angled brace inside on the left."""
    sh, det = L.shell, L.detail
    for k, x in enumerate(TIE_X):
        ml.beam(sh, "tie_beam_%d" % k, (x, BY - 0.02, -HD), (x, BY - 0.02, HD), 0.26, {"all": "wood", "+1": "end_grain", "-1": "end_grain"},
                width=0.22)
        for j, z in enumerate((-HD + 0.35, HD - 0.35)):
            ml.box(det, "tie_strap_%d_%d" % (k, j), (x - 0.13, BY - 0.17, z - 0.05), (x + 0.13, BY + 0.13, z + 0.05), "iron")
    ml.beam(sh, "brace_inside", (-HW + 0.18, 1.85, -0.85), (TIE_X[0], BY - 0.12, -0.85), 0.16, "wood_dark", extend=0.05)
    ml.beam(sh, "brace_inside_b", (-HW + 0.18, 2.1, -HD + 0.25), (-HW + 0.95, BY - 0.12, -HD + 0.25), 0.14, "wood_dark", extend=0.04)


def lights(L, decor):
    """The lantern under the front beam by the left post, the one on an iron arm of the right post, the small chained
    lantern inside hanging from the left tie beam (mod block, a lantern stand-in otherwise)."""
    sh, det = L.shell, L.detail
    xl = -HW + 0.55
    ml.lantern(sh, "lamp_left", (xl, EAVE - 0.82, HD + 0.02), size=0.38, metal="iron", chain_to=(xl, BY - 0.17, HD))
    x = HW
    mount, tip = v3(x - 0.2, 2.95, HD), v3(x - 0.58, 2.95, HD)
    ml.beam(det, "lamp_right_arm", mount, tip, 0.05, "iron", extend=0.02)
    ml.beam(det, "lamp_right_brace", v3(x - 0.2, 2.55, HD), tip - UP * 0.02, 0.04, "iron")
    ml.lantern(sh, "lamp_right", (tip[0], 2.45, HD), size=0.38, metal="iron", chain_to=tip)
    decor.block("farmhouse_decorations:chained_kerosene_lantern", TIE_X[0], BY - 0.13 - 1.0, 0.45, facing="front", scale=1.0, glow=True,
                solid=False, fallback="lantern")


def banners(L):
    det = L.detail
    D = HD + 0.42
    p10.jeweller_banner(L.shell, det, "banner_left", (-HW, EAVE - 0.12, D + 0.14), 0.92, 2.05, arm_from=(-HW, EAVE - 0.12, HD + 0.2))
    p10.jeweller_banner(L.shell, det, "banner_right", (HW + 0.02, EAVE - 0.3, D + 0.14), 0.72, 1.6, arm_from=(HW, EAVE - 0.3, HD + 0.2))


def left_counter(props, det, L, rng):
    """The left counter under the purple cloth with gold dags: three black busts with gold necklaces (ruby, sapphire,
    emerald), two ring trays before them, drawers with iron latches below."""
    x0, x1, z0, z1 = LEFT_COUNTER
    top = ml.counter(props, "counter_left", x0, x1, z0, z1, h=1.0, detail=det)
    y = top[1]
    ml.plate(det, "counter_left_drawers", ((x0 + x1) / 2, 0.34, z1 - 0.04), x1 - x0 - 0.16, 0.44, "m10_drawers", th=0.012)
    p10.p7.runner(props, "runner_left", top[0] + 0.02, top[3] - 0.02, top[2], top[5], y, hang=0.42)
    yt = y + 0.016
    zb = z0 + 0.28
    for k, (x, gem, sides) in enumerate(((-2.75, "ruby", ("emerald", "sapphire")), (-2.17, "sapphire", ("ruby", "ruby")),
                                         (-1.59, "emerald", ("sapphire", "amethyst")))):
        p10.bust(props, det, "bust_l%d" % k, (x, yt, zb), gem=gem, yaw=0.12 * (1 - k), s=1.35, side_gems=sides)
    p10.ring_tray(props, "rings_l0", (-2.46, yt, z1 - 0.2), yaw=0.15)
    p10.ring_tray(props, "rings_l1", (-1.88, yt, z1 - 0.18), yaw=-0.1)
    p10.coffer(props, det, "coffer_l", (-3.0, yt, z1 - 0.2), w=0.2, h=0.12, d=0.15, yaw=0.3)


def back_shelves(props, det, L, rng):
    """The wooden shelf unit at the back middle: coffers (one open with a necklace), gem crystals, the black bust with a
    gold necklace on top."""
    levels = ml.shelf_unit(props, "shelves", -1.05, 1.05, -HD + 0.1, -HD + 0.56, levels=(0.42, 0.9, 1.38), h=1.9, back=False, uprights=3,
                           detail=det)
    (a0, a1, y0, zf0, zb0), (b0, b1, y1, zf1, zb1), (c0, c1, y2, zf2, zb2) = levels
    z = (zf0 + zb0) / 2
    p10.coffer(det, det, "coffer_s0", (-0.6, y0, z), w=0.3, h=0.18, d=0.22)
    p10.coffer(det, det, "coffer_s1", (0.55, y0, z), w=0.26, h=0.16, d=0.2, yaw=-0.2)
    p10.crystals(det, "crys_s0", (0.0, y0, z), "blue", rng, n=3, h=0.24)
    p10.coffer(props, det, "coffer_open", (0.0, y1, z + 0.03), w=0.36, h=0.14, d=0.24, open_=True)
    p10.crystals(det, "crys_s1", (-0.68, y1, z), "purple", rng, n=4, h=0.3)
    p10.crystals(det, "crys_s2", (0.66, y1, z), "green", rng, n=3, h=0.26)
    p10.crystals(det, "crys_s3", (-0.55, y2, z), "red", rng, n=3, h=0.26)
    p10.coffer(det, det, "coffer_s2", (0.05, y2, z), w=0.28, h=0.16, d=0.2, yaw=0.15)
    p10.crystals(det, "crys_s4", (0.62, y2, z), "purple", rng, n=3, h=0.24)
    p10.bust(props, det, "bust_top", (0.0, 2.0, z), gem="ruby", s=1.1, side_gems=("emerald", "emerald"))


def right_counter(props, det, L, rng):
    """The right counter at the back right under its purple cloth: the tray of cut gems, a black bust with a necklace,
    the glass vitrine with the golden crown; drawers below; the gold balance hanging above from the tie beam."""
    x0, x1, z0, z1 = RIGHT_COUNTER
    top = ml.counter(props, "counter_right", x0, x1, z0, z1, h=1.0, detail=det)
    y = top[1]
    ml.plate(det, "counter_right_drawers", ((x0 + x1) / 2, 0.34, z1 - 0.04), x1 - x0 - 0.16, 0.44, "m10_drawers", th=0.012)
    p10.p7.runner(props, "runner_right", top[0] + 0.02, top[3] - 0.02, top[2], top[5], y, hang=0.42)
    yt = y + 0.016
    zc = (z0 + z1) / 2
    p10.gem_tray(props, det, "gemtray", (1.66, yt, zc + 0.05), yaw=0.08, rng=rng)
    p10.bust(props, det, "bust_r", (2.2, yt, zc - 0.05), gem="sapphire", s=1.25, side_gems=("ruby", "ruby"))
    p10.vitrine_crown(props, det, "vitrine", (2.82, yt, zc), w=0.62, d=0.5, h=0.5)
    p10.balance(props, det, "balance", (TIE_X[1], BY - 0.13, -0.72), span=0.62, drop=0.55, pan_drop=0.32)


def outside(props, det, L, rng, decor):
    """The crate of crystal clusters at the front left (amethyst clusters and green and red crystals), the big
    iron-banded treasure chest at the front right."""
    cx, cz, cs = -HW + 0.45, HD + 0.78, 0.7
    decor.block("furnish:spruce_crate", cx, 0.0, cz, facing="front", scale=cs, fallback="crate")
    for k, (dx, dz) in enumerate(((-0.14, -0.1), (0.12, 0.08))):
        decor.block("minecraft:amethyst_cluster", cx + dx, cs, cz + dz, facing="front", scale=0.42, glow=True, solid=False,
                    fallback="crystal_purple", bounds=(0.1875, 0.8125, 0.0, 0.4375, 0.1875, 0.8125))
    p10.crystals(props, "crate_green", (cx + 0.15, cs, cz - 0.14), "green", rng, n=5, h=0.36, w=0.08, spread=0.08)
    p10.crystals(props, "crate_purple", (cx - 0.12, cs, cz + 0.14), "purple", rng, n=4, h=0.3, w=0.07)
    p10.crystals(props, "crate_red", (cx + 0.02, cs, cz + 0.02), "red", rng, n=3, h=0.26, w=0.07)
    p10.treasure_chest(props, det, "treasure", (HW - 0.4, 0.0, HD + 0.78), size=(1.0, 0.74, 0.64), yaw=-0.18)


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="purple")
    p10.add_regions(atlas)
    root = ml.Bone(NAME)
    L = ml.stall(root, atlas, emblem="diamond", lanterns=0, front_counter=False, back_shelves=False, banner_side=None, rug=False,
                 half_w=HW, half_d=HD, eave_y=EAVE, roof_rise=RISE, walls=False, hang_rail=False, stripes=11, end_stripes=5)
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(2101)
    decor = ml.Decor()
    p10.peak(L)
    p10.hip_left(L)
    p10.walls(L)
    frame(L)
    lights(L, decor)
    banners(L)
    ml.rug(L.shell, "rug", RUG[0], RUG[1], RUG[2], RUG[3], y=0.0)
    left_counter(props, det, L, rng)
    back_shelves(props, det, L, rng)
    right_counter(props, det, L, rng)
    outside(props, det, L, rng, decor)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="purple", emblem="diamond", shape="stall", banners=2), light=12)


if __name__ == "__main__":
    main()
