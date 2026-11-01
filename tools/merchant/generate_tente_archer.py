#!/usr/bin/env python3
"""tente_archer — Tente du vendeur d'archerie / Archery Merchant Tent (reference: scratchpad/ref/tente_archer_ref.png).

The shared merchant pavilion (tools/merchant/merchantlib.py) in green and beige with a lower roof (roof_rise 2.0),
the green banner with the gold bow and arrow hanging at the front left, the green flag at the back left; dressed by
agent M5 (tools/merchant/props_m5.py): a dark wooden display wall at the back with recurve bows and a crossbow on its
rails, a tall box of white-fletched arrows by the left front post and a small crate of arrows before it, the green
clothed main counter (crossbows, a bundle of arrows, a quiver), the right counter with its green runner, a box of
arrows, gold arrowhead boxes and a crossbow, a crossbow leaning in front, barrels and crates (mod furniture when
installed), lanterns on the front posts, the green rug, and in front at the left the ROUND STRAW TRAINING TARGET
(red and cream rings) on its wooden easel.

Usage:  python3 tools/merchant/generate_tente_archer.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_archer.json, models/entity + blockbench/tente_archer.bbmodel,
textures/entity/tente_archer.png, textures/item/tente_archer.png, interiors/tente_archer_decor.json.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m5 as pm  # noqa: E402

NAME = "tente_archer"
v3, UP, X, Z = ml.v3, ml.UP, ml.X, ml.Z
BANNER_X = -1.85     # the front banner hangs at the left of the front (as pictured), not in the middle
WALL_Z = -0.95       # the bow wall stands a third of the way in (a shallow shop, as pictured); the canvas behind it


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


def back_wall(props, det, L, rng):
    """The wooden display wall at the back: recurve bows on its rails, a crossbow, two quivers."""
    hw, hd = L.half_w, L.half_d
    z = WALL_Z
    zf = pm.bow_wall(props, det, "bow_wall", -hw + 0.18, hw - 0.18, z, y1=L.eave_y - 0.3)
    zb = zf + 0.06
    bows = ((-2.15, 1.5, -1), (-1.15, 1.62, 1), (-0.52, 1.55, -1), (0.58, 1.66, 1), (1.2, 1.55, -1), (2.15, 1.5, 1))
    for k, (x, L_, f) in enumerate(bows):
        cy = 1.82 + 0.05 * ((k * 3) % 2)
        pm.bow(det, "wall_bow_%d" % k, (x, cy, zb + 0.02), up=(0, 1, 0), facing=(f, 0, 0), length=L_, th=0.1)
        pm.peg(det, "wall_peg_%d" % k, (x, cy + 0.72, zb), zf - 0.02)
    # a crossbow hung upright in the middle bay, its stirrup down
    pm.crossbow(det, "wall_xbow", (0.02, 2.42, zb + 0.02), (0, -1, 0), up=(0, 0, 1), length=0.72, prod=0.62)
    pm.peg(det, "wall_peg_x", (0.02, 2.45, zb), zf - 0.02)
    # quivers hung at the two ends, leaning a little
    pm.quiver(det, "wall_quiver_l", (-2.62, 1.0, zb + 0.08), h=0.66, r=0.11, up=(0.12, 1, 0.05), arrows=0.36)
    pm.quiver(det, "wall_quiver_r", (2.62, 1.0, zb + 0.08), h=0.66, r=0.11, up=(-0.12, 1, 0.05), arrows=0.36)
    return zf


def left_counter(props, det, L, rng):
    """The main counter (front left): the green gold-fringed cloth, two crossbows, a bundle of arrows, a quiver."""
    hd = L.half_d
    x0, x1, z0, z1 = -1.95, -0.38, hd - 1.35, hd - 0.65
    top = ml.counter(props, "counter_main", x0, x1, z0, z1, h=0.98, detail=det)
    y = top[1]
    ml.table_cloth(props, "cloth_main", x0 + 0.12, x1 - 0.12, z0 - 0.02, z1 + 0.02, y, hang=0.46, sides=("front",))
    y += 0.015
    pm.crossbow(det, "xbow_c0", (-1.72, y + 0.05, z1 - 0.28), (1, 0, -0.18), up=(0, 1, 0), length=0.7, prod=0.6)
    pm.crossbow(det, "xbow_c1", (-0.72, y + 0.05, z0 + 0.18), (-0.35, 0, 1), up=(0, 1, 0), length=0.62, prod=0.56)
    pm.arrow_bundle(det, "bundle_c", (-1.25, y, z0 + 0.2), (1, 0, 0.08), length=0.85, w=0.18)
    pm.quiver(det, "quiver_c", (-0.62, 0.0, z1 + 0.2), h=0.72, r=0.12, up=(0.06, 1, 0.22), arrows=0.4)
    return (x0, x1, z0, z1)


def right_counter(props, det, L, rng):
    """The right counter: a green runner, a box of arrows, small gold boxes of arrowheads, a crossbow; a crossbow
    leaning against its front."""
    hd, hw = L.half_d, L.half_w
    x0, x1, z0, z1 = 0.95, hw - 0.42, hd - 1.4, hd - 0.68
    top = ml.counter(props, "counter_right", x0, x1, z0, z1, h=1.0, detail=det)
    y = top[1]
    ml.table_cloth(props, "runner_right", 1.2, 2.0, z0 - 0.02, z1 + 0.02, y, hang=0.5, sides=("front",))
    pm.arrow_box(props, det, "box_r", (x1 - 0.34, y, (z0 + z1) / 2 - 0.05), size=(0.56, 0.66, 0.5), arrows=0.72, yaw=0.08, solid=False)
    ml.box(det, "box_r_band", (x1 - 0.64, y + 0.5, (z0 + z1) / 2 - 0.32), (x1 - 0.04, y + 0.56, (z0 + z1) / 2 + 0.22), "iron")
    for k, (dx, dz, dy) in enumerate(((0.0, 0.0, 0.0), (0.2, 0.06, 0.0), (0.08, 0.02, 0.13))):
        ml.rbox(det, "gold_box_%d" % k, (1.32 + dx, y + 0.015 + dy, z0 + 0.3 + dz), (0.18, 0.13, 0.26), 0.1 * k, "gold_ingot")
    pm.crossbow(det, "xbow_r", (1.45, y + 0.065, z1 - 0.12), (1, 0, -0.3), up=(0, 1, 0), length=0.62, prod=0.55)
    pm.crossbow(det, "xbow_lean", (2.2, 0.02, z1 + 0.32), (0.05, 1, -0.3), up=(0, 0.3, 1), length=0.66, prod=0.58)
    return (x0, x1, z0, z1)


def front_left(props, det, L, rng, decor):
    """By the left front post: the tall box of arrows, a small crate of arrows before it."""
    hw, hd = L.half_w, L.half_d
    pm.arrow_box(props, det, "tall_box", (-2.42, 0.0, hd - 0.42), size=(0.6, 1.12, 0.52), arrows=0.95, yaw=0.04)
    ml.box(det, "tall_box_band", (-2.74, 0.82, hd - 0.7), (-2.1, 0.9, hd - 0.14), "iron")
    pm.arrow_box(props, det, "small_crate", (-2.1, 0.0, hd + 0.62), size=(0.62, 0.5, 0.52), arrows=0.42, yaw=-0.12, planes=2)


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="green")
    pm.add_regions(atlas, pm.ARCHER_REGIONS)
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="bow", flag_corner="back_left", side_banners=0, rug=False, lanterns=2,
                    front_counter=False, back_shelves=False, roof_rise=2.0)
    shift_banner(L, BANNER_X)
    det = L.detail
    props = ml.Bone("props", parent=root)
    rng = random.Random(1501)
    hw, hd = L.half_w, L.half_d
    # the green rug lies before the right counter (as pictured)
    ml.rug(L.shell, "rug", -0.3, 2.45, hd + 0.45, hd + 2.15)
    L.rug_box = (-0.3, hd + 0.45, 2.45, hd + 2.15)
    back_wall(props, det, L, rng)
    left_counter(props, det, L, rng)
    right_counter(props, det, L, rng)
    decor = ml.Decor()
    front_left(props, det, L, rng, decor)
    # the round training target on its easel, in front at the left, turned towards the passers-by
    pm.target_easel(props, det, "target", (-hw - 0.5, 0.0, hd + 1.25), yaw=-0.32, r=0.72, h=1.26)
    # mod furniture (drawn when the mod is installed; vanilla barrel / stand-in otherwise)
    decor.block("landsoficaria:cypress_barrel", hw + 0.48, 0.0, 1.05, facing="neg_x", scale=0.85, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("furnish:spruce_crate", hw - 0.28, 0.0, hd + 0.62, facing="front", scale=0.72, fallback="crate")
    decor.block("furnish:spruce_crate", 2.2, 0.0, WALL_Z + 0.55, facing="front", scale=0.62, fallback="crate")
    decor.block("landsoficaria:cypress_barrel", -2.3, 0.0, WALL_Z + 0.55, facing="front", scale=0.72, alt="minecraft:barrel",
                fallback="barrel")
    # arrows standing in that barrel against the wall (above its lid whichever block is drawn)
    pm.arrow_bunch(det, "barrel_arrows", (-2.3, 0.56, WALL_Z + 0.55), h=0.72, w=0.5, planes=3, yaw=0.3)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="green", emblem="bow"))


if __name__ == "__main__":
    main()
