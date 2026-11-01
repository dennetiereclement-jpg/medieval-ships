#!/usr/bin/env python3
"""tente_poissonnier — Tente du poissonnier / Fishmonger's Stall (reference: scratchpad/ref/tente_poissonnier_ref.png).

The gabled market stall of merchantlib.stall, LONGER than the other stalls (6.6 blocks between the posts), in sea blue
and white: stripes running down the two roof slopes, the dagged blue and white valance edged in gold, four squared
posts with gold caps and rope wound round them, lanterns high on the two front posts, TWO blue banners with the white
fish over a hook (one on each front post); dressed by tools/merchant/props_m9.py: a fishing net hung in festoons under
the eave, fish of several sizes and colours (grey-blue, blue, silver, red) hanging on chains from the rail, the ice
display on the counter (crushed ice, salmon and cod, little price boards), the cutting board with a salmon fillet, a
steak and a cleaver on the right of the counter, crates of fish on ice, a crate of red lobsters and one of crabs,
barrels of fish, the lobster trap at the front right, the anchor leaning on a barrel at the front left, seaweed
hanging from the crates, the posts and the left side, shelves of green jars, pots and fish at the back, barrels and
crates (mod furniture when installed). No flags, no rug (as on the picture).

Usage:  python3 tools/merchant/generate_tente_poissonnier.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_poissonnier.json, models/entity + blockbench/tente_poissonnier.bbmodel,
textures/entity/tente_poissonnier.png, textures/item/tente_poissonnier.png, interiors/tente_poissonnier_decor.json.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m9 as p9  # noqa: E402

NAME = "tente_poissonnier"
v3, UP = ml.v3, ml.UP
HALF_W, HALF_D, EAVE = 3.3, 2.4, 3.65
COUNTER_X = (-2.4, 2.45)


def lanterns(L):
    """The two lanterns high on the front posts (on an iron arm, as on the picture: at about 3/4 of the post)."""
    for k, sx in enumerate((-1, 1)):
        x, z = sx * L.half_w, L.half_d
        y = 2.72
        mount, tip = v3(x, y + 0.48, z + 0.2), v3(x, y + 0.48, z + 0.5)
        ml.beam(L.detail, "lamp_arm_%d" % k, mount, tip, 0.05, "iron", extend=0.02)
        ml.beam(L.detail, "lamp_brace_%d" % k, v3(x, y + 0.05, z + 0.2), tip - UP * 0.02, 0.04, "iron")
        ml.lantern(L.shell, "lamp_%d" % k, (x, y, z + 0.5), size=0.5, metal="iron", chain_to=tip)


def posts_dress(props, det, L):
    """Rope wound round the four posts above the roof and round the front posts under the eave; seaweed down the
    front posts."""
    hw, hd = L.half_w, L.half_d
    for k, (x, z) in enumerate(((-hw, hd), (hw, hd), (hw, -hd), (-hw, -hd))):
        p9.rope_wrap(det, "post_rope_%d" % k, x, z, L.eave_y + 0.3, side=0.4, h=0.16)
        if z > 0:
            p9.rope_wrap(det, "post_rope_low_%d" % k, x, z, L.eave_y - 0.95, side=0.4, h=0.12)
    p9.seaweed(props, "kelp_post_l", (-hw + 0.21, L.eave_y - 0.4, hd + 0.05), length=1.1, width=0.3, normal=(1, 0, 0))
    p9.seaweed(props, "kelp_post_l2", (-hw - 0.12, L.eave_y - 0.5, hd + 0.21), length=0.9, width=0.28, normal=(0, 0, 1))
    p9.seaweed(props, "kelp_post_r", (hw - 0.21, L.eave_y - 0.45, hd + 0.05), length=0.95, width=0.28, normal=(-1, 0, 0))
    # seaweed hanging thick from the front-left corner of the eave (as on the picture)
    for k, (dx, ln) in enumerate(((-0.25, 1.4), (0.3, 1.0), (0.6, 1.25))):
        p9.seaweed(props, "kelp_corner_%d" % k, (-hw + dx, L.eave_y - 0.32, hd + 0.18), length=ln, width=0.34)


def hanging(props, det, L, rng):
    """The fishing net in festoons under the front eave (behind the fish), the fish hanging on chains from the rail:
    a group of four in the middle, three on the right, one half hidden behind the left banner; nets and seaweed down
    the left side."""
    hy, hz = L.hang_y, L.hang_z
    hw, hd = L.half_w, L.half_d
    zn = hz - 0.12
    for k, (xa, xb, dp) in enumerate(((-1.65, -0.1, 0.72), (-0.1, 1.45, 0.7), (1.45, 2.95, 0.55))):
        p9.net_swag(props, "net_%d" % k, (xa, hy + 0.04, zn), (xb, hy + 0.04, zn), depth=dp, top_sag=0.06)
    for k, (x, kind, ln, dr) in enumerate(((-1.25, "silver", 1.0, 0.32), (-0.82, "blue", 1.05, 0.26), (-0.45, "cod", 0.9, 0.36),
                                           (-0.05, "red", 1.0, 0.3), (1.12, "blue", 0.92, 0.36), (1.58, "red", 0.82, 0.28),
                                           (2.0, "silver", 0.95, 0.32), (-2.05, "cod", 0.75, 0.3))):
        p9.hanging_fish(props, det, "hfish_%d" % k, (x, hy, hz + 0.02), kind, length=ln, drop=dr + 0.22, yaw=rng.uniform(-0.2, 0.2))
    # the left side: a net and seaweed hanging from the side eave beam
    by = L.eave_y - 0.18 - 0.17
    p9.hanging_net(props, "net_side_l", (-hw - 0.06, by, 1.05), 1.0, 0.9, normal=(-1, 0, 0))
    for k, (z, ln) in enumerate(((0.1, 1.1), (0.55, 1.5), (1.45, 1.3), (1.85, 1.7), (2.15, 1.2))):
        p9.seaweed(props, "kelp_side_%d" % k, (-hw - 0.1, by, z), length=ln, width=0.32, normal=(-1, 0, 0))
    # the right front: a net draped beside the post
    p9.hanging_net(props, "net_post_r", (hw - 0.45, L.eave_y - 0.6, hd + 0.3), 0.55, 1.1)


def ice_display(props, det, L, rng):
    """The ice display on the left of the counter: a raised wooden tray sloping down to the front, filled with crushed
    ice and loose ice blocks, two big salmon and three silver fish / cod on it, three little price boards at its
    back."""
    (x0, y, z0, x1, _, z1), = L.counter_boxes
    xa, xb = x0 + 0.04, 0.32
    za, zb = z0 + 0.02, z1 + 0.06
    lo, tilt = 0.16, 0.36
    p9.box(props, "tray_front", (xa, y, zb - 0.06), (xb, y + lo + 0.05, zb), "plank")
    p9.box(props, "tray_back", (xa, y, za), (xb, y + lo + tilt + 0.1, za + 0.07), {"all": "plank", "+2": "wood_dark"})
    for k, x in enumerate((xa, xb)):
        p9.box(props, "tray_end_%d" % k, (x - 0.045, y, za), (x + 0.045, y + lo + tilt * 0.55, zb), "wood_dark")
        p9.box(det, "tray_end_top_%d" % k, (x - 0.045, y + lo + tilt * 0.55, za), (x + 0.045, y + lo + tilt + 0.06, za + 0.25), "wood_dark")
    surf = p9.ice_bed(props, det, "ice", xa + 0.045, xb - 0.045, za + 0.07, zb - 0.06, y + lo, rng, chunks=11, tilt=tilt, size=(0.14, 0.2),
                      front=0.75)
    for k, (x, z, ln, yaw) in enumerate(((-1.98, 1.7, 0.86, 0.32), (-1.42, 1.62, 0.82, 0.18))):
        p9.lying_fish(props, "ice_salmon_%d" % k, (x, surf(z) + 0.02, z), "salmon", length=ln, yaw=yaw, tilt=0.45)
    for k, (x, z, kind) in enumerate(((-0.86, 1.72, "silver"), (-0.46, 1.6, "cod"), (-0.08, 1.76, "silver"))):
        p9.lying_fish(props, "ice_fish_%d" % k, (x, surf(z) + 0.02, z), kind, length=0.8, yaw=0.45 + 0.12 * k, tilt=0.45)
    for k, x in enumerate((-2.0, -1.55, -0.85)):
        p9.price_sign(det, "sign_%d" % k, (x, y + lo + tilt + 0.06, za + 0.04), h=0.24 + 0.05 * (k % 2), w=0.28, yaw=0.05 * (k - 1))


def cutting(props, det, L, rng, decor):
    """On the right of the counter: the cutting board (Farmer's Delight when installed) with a salmon fillet and a
    steak, a cleaver standing on it, a knife."""
    (x0, y, z0, x1, _, z1), = L.counter_boxes
    zc = (z0 + z1) / 2
    decor.block("farmersdelight:cutting_board", 1.25, y, zc, facing="front", scale=0.9, solid=False, fallback="plank")
    yb = y + 0.06
    p9.salmon_steak(props, "fillet", (1.1, yb, zc + 0.04), w=0.62, d=0.26, th=0.09, yaw=0.08)
    p9.salmon_steak(props, "steak", (1.55, yb, zc - 0.12), w=0.24, d=0.2, th=0.07, yaw=-0.3)
    p9.lying_fish(props, "board_fish", (2.05, y, zc + 0.08), "salmon", length=0.55, yaw=-0.3)
    # the cleaver standing on its edge, its handle up to the right
    c = v3(1.78, yb + 0.14, zc + 0.12)
    p9.add_cube(props, "cleaver_blade", c, p9.rz(-0.25), (0.26, 0.24, 0.025), {"all": "steel"}, stretch=True)
    ml.beam(det, "cleaver_handle", c + v3(0.1, 0.1, 0), c + v3(0.28, 0.3, 0), 0.05, "wood_dark", extend=0.01)
    ml.beam(det, "knife_blade", v3(0.62, y + 0.012, z1 - 0.12), v3(0.84, y + 0.012, z1 - 0.18), 0.04, "steel", width=0.012)
    ml.beam(det, "knife_handle", v3(0.84, y + 0.02, z1 - 0.18), v3(0.98, y + 0.02, z1 - 0.22), 0.035, "wood_dark")


def front(props, det, L, rng, decor):
    """Before the stall: the big crate of fish on ice at the front left, a crate of fish before the counter, the crate
    of lobsters on a crate stack at the left, the crate of red crabs before the right of the counter, the lobster trap
    at the front right, a crate of fish at the right post; seaweed hanging from the crates."""
    hw, hd = L.half_w, L.half_d
    # the big low crate of fish at the very front left
    p9.fish_crate(props, "crate_fl", (-2.62, 0.0, hd + 1.05), (1.15, 0.46, 0.62), content="m9_fish_heap")
    for k, (dx, dz, kind, yaw) in enumerate(((-0.25, 0.0, "silver", 0.2), (0.12, 0.08, "cod", -0.15), (0.32, -0.12, "blue", 0.3))):
        p9.lying_fish(props, "crate_fl_fish_%d" % k, (-2.62 + dx, 0.47, hd + 1.05 + dz), kind, length=0.55, yaw=yaw)
    p9.seaweed(props, "kelp_crate_fl", (-2.2, 0.44, hd + 1.37), length=0.42, width=0.3)
    # the crate before the counter (fish on ice)
    p9.fish_crate(props, "crate_fc", (-1.3, 0.0, hd + 0.38), (0.72, 0.62, 0.62), content="m9_fish_heap", yaw=0.05)
    for k, (dx, kind) in enumerate(((-0.14, "silver"), (0.12, "cod"))):
        p9.lying_fish(props, "crate_fc_fish_%d" % k, (-1.3 + dx, 0.63, hd + 0.38 + 0.05 * k), kind, length=0.5, yaw=0.4 - 0.7 * k)
    p9.seaweed(props, "kelp_crate_fc", (-1.05, 0.6, hd + 0.71), length=0.6, width=0.28)
    # the crate of lobsters on a crate at the left end of the counter
    decor.block("furnish:spruce_crate", -2.68, 0.0, hd + 0.12, facing="front", scale=0.62, fallback="crate")
    p9.fish_crate(props, "crate_lob", (-2.68, 0.62, hd + 0.12), (0.66, 0.32, 0.56), content="m9_crab_heap")
    for k, (dx, dz, yaw) in enumerate(((-0.12, 0.06, 0.4), (0.14, -0.06, 2.7))):
        p9.lobster(props, "lob_%d" % k, (-2.68 + dx, 0.95, hd + 0.12 + dz), L=0.42, yaw=yaw)
    p9.seaweed(props, "kelp_crate_lob", (-2.45, 0.92, hd + 0.42), length=0.55, width=0.26)
    # the crate of crabs before the right of the counter
    cx, cz = 2.35, hd + 0.42
    p9.fish_crate(props, "crate_crabs", (cx, 0.0, cz), (0.78, 0.55, 0.62), content="m9_crab_heap")
    for k, (dx, dz, yaw) in enumerate(((-0.2, 0.08, 0.3), (0.05, -0.1, -0.4), (0.22, 0.1, 1.2), (-0.02, 0.15, 2.0))):
        p9.crab(props, "crab_%d" % k, (cx + dx, 0.55, cz + dz), s=0.2, yaw=yaw)
    p9.seaweed(props, "kelp_crate_crabs", (cx - 0.32, 0.54, cz + 0.32), length=0.4, width=0.24)
    # the lobster trap at the front right
    p9.lobster_trap(props, det, "trap", (hw + 0.38, 0.0, hd + 0.7), w=1.22, d=0.92, h=1.0, yaw=-0.25)
    p9.seaweed(props, "kelp_trap", (hw + 0.1, 0.62, hd + 1.05), length=0.5, width=0.3)
    # a crate of fish at the right post, between the counter and the post
    p9.fish_crate(props, "crate_post_r", (hw - 0.55, 0.0, hd - 0.55), (0.5, 0.9, 0.5), content="m9_fish_heap")
    p9.lying_fish(props, "crate_post_r_fish", (hw - 0.55, 0.91, hd - 0.55), "blue", length=0.46, yaw=1.2)


def left(props, det, L, rng, decor):
    """Outside the left post: a barrel heaped with fish, a barrel behind it with two potted plants, the anchor leaning
    on the front barrel, two more barrels of fish along the left side at the back; the way in on the left side stays
    free (z -0.3 .. 1.5)."""
    hw, hd = L.half_w, L.half_d
    bx, bz = -hw - 0.62, hd + 0.35
    ml.barrel(props, "barrel_fl", (bx, 0.0, bz), r=0.36, h=0.92, staves=6, content="m9_fish_heap")
    for k, (dx, kind, yaw) in enumerate(((-0.1, "silver", 0.6), (0.1, "blue", -0.4))):
        p9.lying_fish(props, "barrel_fl_fish_%d" % k, (bx + dx, 0.93, bz + 0.05 * k), kind, length=0.48, yaw=yaw)
    p9.seaweed(props, "kelp_barrel_fl", (bx + 0.2, 0.9, bz + 0.33), length=0.5, width=0.26)
    ml.barrel(props, "barrel_fl2", (bx - 0.05, 0.0, hd - 0.48), r=0.36, h=1.05, staves=6)
    p9.potted_plant(props, "pot_0", (bx - 0.15, 1.05, hd - 0.52), r=0.1, h=0.15)
    p9.potted_plant(props, "pot_1", (bx + 0.13, 1.05, hd - 0.42), r=0.09, h=0.13, plant="vines")
    p9.anchor(props, det, "anchor", (bx - 0.62, 0.0, bz + 0.45), (bx - 0.36, 1.82, bz + 0.12), s=1.25, region="iron")
    for k, (z, h) in enumerate(((-0.95, 0.9), (-1.75, 0.85))):
        ml.barrel(props, "barrel_side_%d" % k, (-hw - 0.5, 0.0, z), r=0.34, h=h, staves=6, content="m9_fish_heap" if k == 0 else "m9_salmon_heap")
    p9.lying_fish(props, "barrel_side_fish", (-hw - 0.5, 0.91, -0.95), "cod", length=0.48, yaw=0.9)


def back(props, det, L, rng, decor):
    """The back shelves: green jars, clay pots, fish lying on the boards, small crates; barrels and a crate inside
    (mod furniture when installed); the merchant's place stays free (x 0.6 .. 1.6, z 0.3 .. 1.3)."""
    hw, hd = L.half_w, L.half_d
    levels = sorted(L.shelf_levels, key=lambda s: s[2])
    for i, (x0, x1, y, zf, zb) in enumerate(levels):
        z = (zf + zb) / 2
        n = 9 if i else 4
        xa = x0 + 0.25 if i else 0.0
        xb = x1 - 0.25 if i else 1.9
        for k in range(n):
            x = xa + k * (xb - xa) / (n - 1)
            kind = (i * 3 + k) % 5
            if kind in (0, 3):
                p9.green_jar(det, "jar_%d_%d" % (i, k), (x, y, z), r=0.1 + 0.025 * (k % 2), h=0.24 + 0.06 * (i % 2))
            elif kind == 1:
                p9.lying_fish(det, "shelf_fish_%d_%d" % (i, k), (x - 0.12, y, z + 0.04), ("silver", "cod", "blue", "red")[k % 4], length=0.46,
                              yaw=0.15 * (k % 3 - 1), tilt=0.5)
            elif kind == 2:
                p9.wb.octo(det, "crock_%d_%d" % (i, k), (x, y, z), 0.12, 0.22, {"all": "pot_clay", "+2": "jar_top"}, stretch=True)
            else:
                p9.fish_crate(det, "shelf_box_%d_%d" % (i, k), (x, y, z), (0.36, 0.2, 0.32), content="m9_fish_heap", solid=False)
    decor.block("landsoficaria:cypress_barrel", -hw + 0.7, 0.0, -hd + 0.95, facing="pos_x", scale=0.85, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("furnish:spruce_crate", hw - 0.7, 0.0, -hd + 0.95, facing="front", scale=0.75, fallback="crate")
    decor.block("furnish:spruce_crate", hw - 0.7, 0.75, -hd + 0.95, facing="front", scale=0.55, fallback="crate")
    decor.block("landsoficaria:loaded_cypress_barrel", -0.6, 0.0, -hd + 0.98, facing="front", scale=0.8, alt="minecraft:barrel",
                fallback="barrel")
    p9.rope_coil(props, "rope_coil", (-hw + 0.75, 0.0, -0.3), r=0.24, h=0.12)
    ml.sack(props, "salt_sack", (-hw + 0.7, 0.0, 0.45), s=0.42, yaw=0.3)


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="seablue")
    p9.add_regions(atlas, p9.FISH_REGIONS)
    root = ml.Bone(NAME)
    L = ml.stall(root, atlas, emblem="fish", lanterns=0, front_counter=True, back_shelves=True, banner_side="both",
                 half_w=HALF_W, half_d=HALF_D, eave_y=EAVE, roof_rise=1.8, stripes=9, end_stripes=5, counter_x=COUNTER_X,
                 banner_size=(1.25, 1.95))
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1701)
    decor = ml.Decor()
    lanterns(L)
    posts_dress(props, det, L)
    hanging(props, det, L, rng)
    ice_display(props, det, L, rng)
    cutting(props, det, L, rng, decor)
    front(props, det, L, rng, decor)
    left(props, det, L, rng, decor)
    back(props, det, L, rng, decor)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="seablue", emblem="fish", shape="stall", banners=2))


if __name__ == "__main__":
    main()
