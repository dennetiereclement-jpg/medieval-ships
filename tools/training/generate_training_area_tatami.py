#!/usr/bin/env python3
"""training_area_tatami — Aire d'entraînement aux tatamis / Tatami Training Area (reference:
scratchpad/ref/training_area_tatami_ref.png).

A square martial-arts yard (~7 x 7) of traininglib (agent K) dressed by props_l.py (agent L): the floor entirely of
beige tatami mats (woven, staggered, dark edges) with a red border all round and the red flower knot in the middle,
framed by a square of dark mat seams; the post-and-rail fence with iron-capped posts and stone corner bases, the
entrance in the middle of the front; at the back the small stall with the red-and-beige striped awning over a plank
back wall, a wooden bench with rolled mats and cushions, two shelf units of training gear (jars, folded cloths), wooden
swords hung on the back wall and a lantern under the awning; two stools with jars by its left post; on the left a rack
of staves and wooden swords and wooden swords leaning on the front-left fence, on the right staves leaning on the fence;
the tall red banner with the gold lotus at the back right on its gallows post, a barrel and a lying log-barrel beside
it, a second lotus banner on the front-right corner post; two lanterns hung from tall posts at the back corners; the
pot of pink flowers on its stone pedestal at the front-left corner (in place of the corner post).

Usage:  python3 tools/training/generate_training_area_tatami.py      (TRAINING_OUT=<file.bbmodel>: preview model only)
Writes (traininglib.export): training/training_area_tatami.json, models/entity + blockbench/training_area_tatami.bbmodel,
textures/entity/training_area_tatami.png, textures/item/training_area_tatami.png,
interiors/training_area_tatami_decor.json.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import traininglib as tr  # noqa: E402
import props_l as pl  # noqa: E402

NAME = "training_area_tatami"
v3, UP = tr.v3, tr.UP
HW, HD = 3.4, 3.4                 # the fence ring (posts' centres)
FX0, FX1, FZ0, FZ1 = -3.15, 3.15, -2.2, 3.15   # the tatami floor
STALL = (-2.0, 1.05, -3.12, -2.25)             # x0, x1, z_back, z_front of the stall's posts


def drop_post(A, prefix, at):
    """Removes a fence post made by fence_ring (its cubes named prefix..., and its collision box round `at`), so that
    something else stands at that corner."""
    for b in (A.shell, A.detail):
        b.cubes[:] = [c for c in b.cubes if not c.name.startswith(prefix)]
    x, z = at
    tr.COLLIDERS[:] = [c for c in tr.COLLIDERS if not (c[0] <= x <= c[3] and c[2] <= z <= c[5] and c[3] - c[0] < 0.8 and c[5] - c[2] < 0.8)]


def stall(A, atlas, rng, decor):
    """The striped stall at the back: plank back wall, bench with rolled mats, two shelf units of gear, wooden swords
    on the wall, a lantern under the awning."""
    sh, det = A.shell, A.detail
    x0, x1, zb, zf = STALL
    roof, val = tr.awning_regions(atlas, "red", stripe="beige", n=4)
    S = tr.awning(A, "stall", x0, x1, zb, zf, roof, val, h_front=2.05, h_back=2.4, overhang=0.2, sag=0.06, valance=0.26)
    # the plank back wall between the back posts
    tr.box(sh, "stall_wall", (x0 + 0.08, 0.0, zb - 0.06), (x1 - 0.08, 2.32, zb - 0.01), {"all": "plank_dark"}, stretch=True, u_dir=UP)
    # the shelf units at the two ends (jars, folded cloths, a bowl)
    for k, (sx0, sx1) in enumerate(((x0 + 0.12, x0 + 0.86), (x1 - 0.86, x1 - 0.12))):
        levels = tr.shelf_unit(sh, "shelf_%d" % k, sx0, sx1, zb + 0.02, zb + 0.4, levels=(0.5, 1.0, 1.5), h=1.78, back=False,
                               uprights=2, detail=det)
        for i, (lx0, lx1, y, zfr, zbk) in enumerate(levels):
            zc = (zfr + zbk) / 2
            if (i + k) % 2 == 0:
                pl.jar(det, "shelf_%d_jar_%d_a" % (k, i), (lx0 + 0.13, y, zc), r=0.085, h=0.19)
                pl.jar(det, "shelf_%d_jar_%d_b" % (k, i), (lx0 + 0.34, y, zc + 0.02), r=0.07, h=0.15)
                pl.folded_stack(det, "shelf_%d_cloth_%d" % (k, i), (lx1 - 0.18, y, zc), ["cloth_white", "cloth_red"], w=0.26, d=0.24)
            else:
                pl.folded_stack(det, "shelf_%d_cloth_%d" % (k, i), (lx0 + 0.18, y, zc), ["cloth_beige", "cloth_white", "cloth_red"],
                                w=0.28, d=0.24)
                pl.jar(det, "shelf_%d_jar_%d_a" % (k, i), (lx1 - 0.16, y, zc), r=0.09, h=0.21)
    # the bench in the middle, rolled mats and cushions on it
    bx = (x0 + x1) / 2
    tr.bench(A, "bench", (bx, 0.0, zb + 0.42), length=1.25, h=0.46, depth=0.38)
    pl.mat_roll(det, "bench_roll_0", (bx - 0.36, 0.46 + 0.11, zb + 0.42), 0.36, r=0.11, direction=(0, 0, 1), region="t_straw",
                ends="t_straw_end")
    pl.mat_roll(det, "bench_roll_1", (bx - 0.08, 0.46 + 0.11, zb + 0.42), 0.36, r=0.11, direction=(0, 0, 1), region="cloth_beige",
                ends="cloth_red")
    tr.box(det, "bench_cushion", (bx + 0.12, 0.46, zb + 0.28), (bx + 0.52, 0.56, zb + 0.56), {"all": "cloth_red"}, stretch=True)
    pl.folded_stack(det, "bench_cloth", (bx + 0.32, 0.56, zb + 0.42), ["cloth_white"], w=0.3, d=0.22)
    # wooden swords and a staff hung on the back wall above the bench (pegs)
    for k in range(4):
        x = bx - 0.45 + 0.3 * k
        tr.box(det, "wall_peg_%d" % k, (x - 0.03, 1.86, zb - 0.01), (x + 0.03, 1.92, zb + 0.08), "wood_dark")
        pl.wooden_sword(det, "wall_sword_%d" % k, (x, 1.98, zb + 0.06), up=(0, -1, 0), facing=(0, 0, 1), length=0.86)
    pl.staff(det, "wall_staff", (bx - 0.62, 1.75, zb + 0.08), (bx + 0.62, 1.75, zb + 0.08), d=0.055)
    tr.hanging_lantern(A, "stall_lamp", (x1 - 0.32, 2.0, zf + 0.02), drop=0.22, size=0.26)
    # two stools with jars by the left post (furnish crates when installed)
    for k, (x, z) in enumerate(((x0 - 0.45, zf - 0.05), (x0 - 0.45, zf + 0.5))):
        decor.block("furnish:spruce_crate", x, 0.0, z, facing="front", scale=0.42, fallback="crate")
        pl.jar(det, "stool_jar_%d" % k, (x, 0.42, z), r=0.09, h=0.2 - 0.03 * k)
    return S


def back_right(A, atlas, decor, ban):
    """The tall lotus banner on its gallows post, a barrel and the lying log-barrel beside it."""
    sh, det = A.shell, A.detail
    top = tr.tall_post(A, "banner_post", (2.45, 0.0, -2.95), h=2.95, d=0.22)
    tr.post_banner(A, "banner_back", top, ban, normal=(0, 0, 1), w=0.72, h=1.5, arm=(-0.8, 0.0))
    tr.box(det, "banner_post_brace", (2.31, 2.45, -3.0), (2.35, 2.78, -2.9), "wood_dark")
    decor.block("landsoficaria:cypress_barrel", 2.85, 0.0, -2.4, facing="front", scale=0.8, alt="minecraft:barrel", fallback="barrel")
    tr.barrel(sh, "log_barrel", (1.45, 0.3, -2.6), r=0.3, h=0.85, axis="x")
    tr.box(det, "log_chock_0", (1.5, 0.0, -2.85), (1.62, 0.1, -2.35), "wood_dark")
    tr.box(det, "log_chock_1", (2.12, 0.0, -2.85), (2.24, 0.1, -2.35), "wood_dark")


def weapons(A):
    """The rack of staves and wooden swords on the left, wooden swords leaning on the front-left fence, staves on the
    right fence (both sides, as on the picture)."""
    sh, det = A.shell, A.detail
    rail = tr.FENCE_H * 0.86 + 0.1
    pl.practice_rack(sh, det, "rack_left", (-HW + 0.32, 0.0, -1.75), (-HW + 0.32, 0.0, -0.55), normal=(1, 0, 0),
                     items=("staff", "wsword", "staff", "wsword", "staff"), h=1.2)
    pl.lean_on_fence(det, "lean_left", ["wsword", "staff", "wsword"], (-HW, 0.0, 0.55), (-HW, 0.0, 1.55), rail, (1, 0, 0),
                     lengths=[0.9, 1.7, 0.9])
    pl.lean_on_fence(det, "lean_right", ["staff", "staff", "wsword", "staff"], (HW, 0.0, -1.85), (HW, 0.0, -0.45), rail, (-1, 0, 0),
                     lengths=[1.75, 1.65, 0.92, 1.8])


def build():
    tr.setup(NAME)
    atlas = tr.Atlas(NAME, colour="red")
    pl.add_regions(atlas)
    A = tr.area(NAME, atlas)
    sh, det = A.shell, A.detail
    rng = random.Random(1802)
    decor = tr.Decor()
    # the tatami floor and the square of seams round the motif
    fl = tr.floor_region(atlas, "t_floor_tatami", FX1 - FX0, FZ1 - FZ0, kind="tatami", border=0.55, border_colour="red",
                         motif="flower_knot")
    tr.floor(sh, "floor", FX0, FX1, FZ0, FZ1, fl)
    pl.floor_knot(det, "floor_seams", ((FX0 + FX1) / 2, 0.042, (FZ0 + FZ1) / 2), size=0.0, frame=2.5, seam=0.08)
    # the fence: entrance in the middle of the front, stone bases at the corners; the front-left corner post gives
    # way to the flower pot on its stone pedestal
    F = tr.fence_ring(A, -HW, HW, -HD, HD, entrance=("front", 0.0, 1.6), stone="corners", post_every=0.95)
    drop_post(A, "post_front_left", (-HW, HD))
    pl.flower_pot(sh, det, "flower_pot", (-HW, 0.0, HD), pedestal=1.02, w=0.6, r=0.25, ph=0.78)
    ban = tr.banner_region(atlas, "red", "lotus", w=48, h=96)
    tr.post_banner(A, "banner_front", F.posts["front_right"], ban, normal=(0, 0, 1), w=0.5, h=0.95, offset=0.2)
    # lanterns on tall posts at the two back corners (the corner posts grow into lantern posts)
    pl.lantern_gallows(sh, det, "lamp_left", (-HW, 0.0, -HD), h=3.0, arm=(0.62, 0.0, 0.12))
    pl.lantern_gallows(sh, det, "lamp_right", (HW, 0.0, -HD), h=3.0, arm=(-0.62, 0.0, 0.12))
    stall(A, atlas, rng, decor)
    back_right(A, atlas, decor, ban)
    weapons(A)
    tr.export(A.root, NAME, atlas, decor=decor, icon=pl.icon_tatami)


if __name__ == "__main__":
    build()
