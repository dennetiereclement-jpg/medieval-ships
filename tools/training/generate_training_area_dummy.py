#!/usr/bin/env python3
"""training_area_dummy — Aire d'entraînement aux frappes / Strike Training Area
(reference: scratchpad/ref/training_area_dummy_ref.png).

A square yard of about 7 x 7 blocks: a floor of trodden earth mixed with stones, a post-and-rail fence on four sides
(squared posts with iron caps and bands, two plank rails, stone-brick bases under the four corner posts) with an
entrance in the front fence; THREE straw-and-wood training dummies of different heights (cross-shaped: post, straw
body bound with rope, arms, head); a heavy punching bag hanging on a chain from a wooden gallows at the back right
(a coil of rope on its post); a small red canvas awning on four posts at the back left over a sword rack of training
swords, barrels and crates; four small red banners with crossed swords (two hung from arms on the tall back posts, two
on the front corner posts); two lanterns (under the awning, at the end of the gallows beam).

Usage:  python3 tools/training/generate_training_area_dummy.py   (TRAINING_OUT=<file.bbmodel>: preview model only)
Writes (traininglib.export): training/training_area_dummy.json, models/entity + blockbench/training_area_dummy.bbmodel,
textures/entity/training_area_dummy.png, textures/item/training_area_dummy.png,
interiors/training_area_dummy_decor.json.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import traininglib as tr  # noqa: E402

NAME = "training_area_dummy"
v3, UP = tr.v3, tr.UP
HW = 3.3                      # half width of the fence ring (posts' centres)
ENTRANCE = ("front", 1.45, 1.7)   # front fence, centred at x = 1.45, 1.7 wide


def build():
    tr.setup(NAME)
    atlas = tr.Atlas(NAME, colour="red")
    A = tr.area(NAME, atlas)
    floor = tr.floor_region(atlas, "t_floor_earth", 2 * HW + 0.2, 2 * HW + 0.2, kind="earth")
    banner = tr.banner_region(atlas, "red", "crossed_swords")
    roof, valance = tr.awning_regions(atlas, "red")

    # the yard: floor and fence
    tr.floor(A.shell, "floor", -HW - 0.1, HW + 0.1, -HW - 0.1, HW + 0.1, floor)
    F = tr.fence_ring(A, -HW, HW, -HW, HW, entrance=ENTRANCE, post_every=1.4, stone="corners")

    # the red awning at the back left over the sword rack (between the two tall banner posts, as on the picture)
    tr.awning(A, "awning", -2.12, -0.02, -3.0, -1.55, roof, valance, h_front=2.0, h_back=2.4, overhang=0.16, sag=0.07, valance=0.26)
    tr.sword_rack(A, "sword_rack", (-1.6, 0, -2.68), (-0.45, 0, -2.68), normal=(0, 0, 1), h=0.95, swords=5)
    tr.hanging_lantern(A, "awning_lamp", (-0.32, 2.0 - 0.06, -1.55), drop=0.2, size=0.26)

    # two tall banner posts on the back fence line, each with a banner hanging from an arm on its right
    t0 = tr.tall_post(A, "banner_post_l", (-2.84, 0, -HW), h=2.95, d=0.24)
    tr.post_banner(A, "banner_back_l", t0, banner, normal=(0, 0, 1), w=0.6, h=1.2, arm=(0.64, 0.0))
    t1 = tr.tall_post(A, "banner_post_c", (0.22, 0, -HW), h=2.95, d=0.24)
    tr.post_banner(A, "banner_back_c", t1, banner, normal=(0, 0, 1), w=0.6, h=1.2, arm=(0.64, 0.0))

    # front corner posts: banners hung on their front faces
    tr.post_banner(A, "banner_front_l", F.posts["front_left"], banner, normal=(0, 0, 1), w=0.56, h=1.0, offset=0.2)
    tr.post_banner(A, "banner_front_r", F.posts["front_right"], banner, normal=(0, 0, 1), w=0.56, h=1.0, offset=0.2)

    # the punching bag on its gallows, back right
    tr.punching_bag(A, "bag", (2.12, 0, -2.4), span=1.62, h=2.6, bag_h=1.12, bag_r=0.35)
    tr.hanging_lantern(A, "gallows_lamp", (2.12 + 0.81 + 0.2, 2.6 - 0.02, -2.4), drop=0.1, size=0.24)

    # three straw dummies of different heights
    tr.dummy(A, "dummy_l", (-1.75, 0, -0.55), height=1.72, yaw=0.25)
    tr.dummy(A, "dummy_r", (0.95, 0, -1.25), height=1.58, yaw=-0.2)
    tr.dummy(A, "dummy_f", (-0.3, 0, 1.05), height=1.86, yaw=0.08)

    # barrels and crates: under the awning, along the left fence, at the foot of the centre banner post
    tr.barrel(A.shell, "barrel_awning", (-1.88, 0, -2.62), r=0.27, h=0.74)
    tr.crate(A.shell, "crate_awning", (-1.85, 0, -2.02), size=0.46, yaw=0.15)
    tr.barrel(A.shell, "barrel_post", (0.62, 0, -2.85), r=0.27, h=0.72)
    tr.crate(A.shell, "crate_left", (-2.78, 0, -0.95), size=(0.55, 0.45, 0.6), yaw=0.05)
    decor = tr.Decor()
    decor.block("landsoficaria:cypress_barrel", -2.8, 0.0, 0.0, facing="front", scale=0.72, alt="minecraft:barrel", fallback="barrel")
    decor.block("furnish:spruce_crate", -2.8, 0.45, -0.95, facing="front", scale=0.42, solid=False, fallback="crate")
    decor.block("farmersdelight:straw_bale", -2.75, 0.0, -2.0, facing="front", scale=0.55, fallback="straw")
    return A, atlas, decor


def main():
    A, atlas, decor = build()
    tr.export(A.root, NAME, atlas, decor=decor, icon=dict(kind="dummy", colour="red", floor="earth"))


if __name__ == "__main__":
    main()
