#!/usr/bin/env python3
"""training_area_shield — Aire d'entraînement épée et bouclier / Sword & Shield Training Area (reference:
scratchpad/ref/training_area_shield_ref.png).

A compact fenced yard (~8 x 6.5) of traininglib (agent K) dressed by props_l.py (agent L): the floor of trodden earth
and stones; the post-and-rail fence with iron-capped posts and grey stone pillars at the corners and on both sides of
the entrance (middle of the front); THREE wooden dummies on small plinths, each wearing an iron helmet, holding a steel
sword in its right hand and carrying a round wooden shield (red and white rings, iron rim, iron boss) strapped on its
left forearm, set in a diagonal across the yard; at the back left the small stall with the BLUE-and-beige striped
awning over a plank back wall: a low rack of three round shields with swords between them, two more shields hung on the
wall above a sword rack, a blue banner with the gold heraldic shield on a tall post at its right; barrels before its
left post, a bucket by the back fence; a sword rack by the right fence; two blue banners with the gold shield on tall
posts in the front fence; tall lantern posts standing on the stone pillars at the two back corners.

1.19.0: the three dummies are interactive training targets (kind "shield_dummy": bones target_0..2 with their head,
arms, sword and shield; JSON "targets", see traininglib.Target).

Usage:  python3 tools/training/generate_training_area_shield.py      (TRAINING_OUT=<file.bbmodel>: preview model only)
Writes (traininglib.export): training/training_area_shield.json, models/entity + blockbench/training_area_shield.bbmodel,
textures/entity/training_area_shield.png, textures/item/training_area_shield.png,
interiors/training_area_shield_decor.json.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import traininglib as tr  # noqa: E402
import props_l as pl  # noqa: E402

NAME = "training_area_shield"
v3, UP = tr.v3, tr.UP
HW, HD = 4.0, 3.15                 # the fence ring (posts' centres)
STALL = (-3.7, -1.05, -2.95, -1.95)  # x0, x1, z_back, z_front of the stall's posts
PILLAR_TOP = tr.FENCE_H + 0.35       # top of a stone pillar's cap (fence_post(pillar=True))
DUMMIES = (  # foot (x, z), yaw, sword pose
    ((-1.35, 0.85), 0.12, "low"),
    ((0.55, -0.15), -0.08, "up"),
    ((2.35, -1.2), -0.22, "up"),
)


def stall(A, atlas, decor, ban):
    """The blue-and-beige striped stall at the back left: plank back wall, the low rack of three round shields with
    swords, two shields hung on the wall over a sword rack, the banner on its tall post at the right."""
    sh, det = A.shell, A.detail
    x0, x1, zb, zf = STALL
    roof, val = tr.awning_regions(atlas, "blue", stripe="beige", n=6)
    tr.awning(A, "stall", x0, x1, zb, zf, roof, val, h_front=2.1, h_back=2.45, overhang=0.2, sag=0.06, valance=0.26)
    tr.box(sh, "stall_wall", (x0 + 0.08, 0.0, zb - 0.06), (x1 - 0.08, 2.38, zb - 0.01), {"all": "plank_dark"}, stretch=True, u_dir=UP)
    # left: the low rack of round shields leaning back, swords standing between them
    pl.shield_rack(sh, det, "shield_rack", (x0 + 0.25, 0.0, zb + 0.32), (x0 + 1.5, 0.0, zb + 0.32), normal=(0, 0, 1), n=3, h=0.9,
                   r=0.3, faces=["l_shield", "l_shield", "l_shield"])
    # right: two shields hung on the wall, the sword rack under them
    rx0, rx1 = x0 + 1.72, x1 - 0.18
    for k in range(2):
        cx = rx0 + (rx1 - rx0) * (k + 0.5) / 2
        tr.box(det, "wall_peg_%d" % k, (cx - 0.03, 1.72, zb - 0.01), (cx + 0.03, 1.78, zb + 0.07), "wood_dark")
        pl.round_shield(det, "wall_shield_%d" % k, (cx, 1.48, zb + 0.04), normal=(0, 0, 1), r=0.28)
    tr.sword_rack(A, "stall_swords", (rx0, 0.0, zb + 0.3), (rx1, 0.0, zb + 0.3), normal=(0, 0, 1), h=0.95, swords=4)
    # the banner on its tall post at the right of the stall
    top = tr.tall_post(A, "stall_banner_post", (x1 + 0.32, 0.0, zb + 0.05), h=2.75, d=0.2)
    tr.post_banner(A, "banner_stall", top, ban, normal=(0, 0, 1), w=0.58, h=1.15, offset=0.16)
    # barrels before the left post (landsoficaria when installed), a small one, a bucket by the back fence
    decor.block("landsoficaria:cypress_barrel", x0 + 0.33, 0.0, zf + 0.62, facing="front", scale=0.85, alt="minecraft:barrel",
                fallback="barrel")
    tr.barrel(sh, "barrel_small", (x0 + 0.26, 0.0, zf + 1.36), r=0.26, h=0.58)
    tr.barrel(sh, "bucket", (x1 + 0.95, 0.0, zb + 0.12), r=0.21, h=0.36)
    tr.beam(det, "bucket_handle", (x1 + 0.76, 0.36, zb + 0.12), (x1 + 1.14, 0.36, zb + 0.12), 0.025, "black_iron")


def build():
    tr.setup(NAME)
    atlas = tr.Atlas(NAME, colour="blue")
    pl.add_regions(atlas)
    A = tr.area(NAME, atlas)
    sh, det = A.shell, A.detail
    decor = tr.Decor()
    # the earth-and-stone floor
    fl = tr.floor_region(atlas, "t_floor_earth", 2 * HW - 0.3, 2 * HD - 0.3, kind="earth")
    tr.floor(sh, "floor", -HW + 0.15, HW - 0.15, -HD + 0.15, HD - 0.15, fl)
    # the fence: stone pillars at the corners and on both sides of the entrance (middle of the front)
    tr.fence_ring(A, -HW, HW, -HD, HD, entrance=("front", 0.0, 1.6), stone="pillars", post_every=1.0)
    ban = tr.banner_region(atlas, "blue", "heraldic_shield", w=48, h=96)
    # two banners with the heraldic shield on tall posts in the front fence
    for k, x in enumerate((-2.45, 2.45)):
        top = tr.tall_post(A, "front_banner_post_%d" % k, (x, 0.0, HD), h=1.95, d=0.24)
        tr.post_banner(A, "banner_front_%d" % k, top, ban, normal=(0, 0, 1), w=0.56, h=1.3, offset=0.17)
    # lantern posts standing on the stone pillars of the two back corners
    pl.lantern_gallows(sh, det, "lamp_left", (-HW, PILLAR_TOP, -HD), h=1.75, arm=(0.6, 0.0, 0.15), d=0.28)
    pl.lantern_gallows(sh, det, "lamp_right", (HW, PILLAR_TOP, -HD), h=1.75, arm=(-0.6, 0.0, 0.15), d=0.28)
    stall(A, atlas, decor, ban)
    # the sword rack by the right fence
    tr.sword_rack(A, "rack_right", (HW - 0.38, 0.0, -2.35), (HW - 0.38, 0.0, -1.15), normal=(-1, 0, 0), h=1.0, swords=4)
    # the three wooden dummies: helmet, sword in the right hand, round shield on the left forearm
    for k, ((x, z), yaw, pose) in enumerate(DUMMIES):
        pl.wooden_dummy(sh, det, "dummy_%d" % k, (x, 0.0, z), yaw=yaw, sword_pose=pose, target=tr.target(A, "shield_dummy", yaw=yaw))
    tr.export(A.root, NAME, atlas, decor=decor, icon=dict(kind="shield", colour="blue", floor="earth"))


if __name__ == "__main__":
    build()
